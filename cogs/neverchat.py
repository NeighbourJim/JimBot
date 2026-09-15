import discord
import logging
import random
import re
import asyncio
import aiohttp
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from bot import current_settings


# ---------------------------------------------------------------- config

OLLAMA_BASE = "http://10.0.0.1:11434"
OLLAMA_CHAT = f"{OLLAMA_BASE}/v1/chat/completions"
OLLAMA_GENERATE = f"{OLLAMA_BASE}/api/generate"   # used only to unload models

# The multi-speaker model. Used for anyone without a solo model below.
MODEL_NAME = "neverchat-5532"

# Solo models, one per speaker. Only list ones that actually exist in
# Ollama -- anything missing here falls back to MODEL_NAME.
SOLO_MODELS = {
    "Nemesis": "nemesis-780",
    "Noet" : "noet-480",
    "NeighbourJim" : "jim-final"
    # "Noet":      "neverchat-noet",
    # "Oryon":     "neverchat-oryon",
}

SPEAKERS = [
    "Nemesis", "NeighbourJim", "Noet", "Oryon",
    "Knite", "Machio", "Zerod", "Cliffracer",
]

# Discord username (the @handle, lowercase) -> trained name.
# Used when the ID isn't listed.
USERNAMES = {
    "nemnem": "Nemesis",
    "neighbourjim": "NeighbourJim",
    "machio": "Machio",
    "zerod1": "Zerod",
    "cloffracer": "Cliffracer",
    "kniteknite": "Knite",
    "taugames": "Oryon",
    "zudrag": "Zudrag",
    "noise1508": "Noise",
    "violet2644": "Violet"
}

# Same mapping used when building the training data, so nicknames that
# drifted still resolve to the name the model knows.
PSEUDONYMS = {
    "Noet, He Who Speaks Motion": "Noet",
    "Nemer a Muirebe": "Nemesis",
    "Merry little Machio": "Machio",
}

ALIASES = {
    "jim": "NeighbourJim",
    "nem": "Nemesis",
    "cliff": "Cliffracer",
}

CONTEXT_MESSAGES = 10       # history lines when no message is supplied
CONTEXT_WITH_MESSAGE = 5    # history lines when a message IS supplied
HISTORY_FETCH = 40          # how many to pull before filtering down
BURST_DELIMITER = "<|split|>"
BURST_DELAY = 1.2           # seconds between one speaker's own messages
SPEAKER_DELAY = 1.8         # seconds between different speakers
MAX_RESPONSES = 3           # cap on the "generate N replies" argument
COUNT_CEILING = 10          # digits above this are message text, not a count
MAX_TOKENS = 140
TEMPERATURE = 1.0
KEEP_ALIVE = "5m"          # how long a model stays resident after use
# Invoking the command under one of these names skips channel context.
NO_CONTEXT_ALIASES = {"ncs"}

BLOCKED_AUTHOR_IDS = {
    676693645155631124,
    170903342199865344,
    439205512425504771,
}

COMMAND_PREFIXES = ("!", ".")

# ---------------------------------------------------------------- cleaning
# These mirror the training-data converter. If the prompt the model sees at
# runtime doesn't look like what it trained on, quality drops.

URL_RE = re.compile(r"https?://\S+")
CUSTOM_EMOJI_RE = re.compile(r"<a?(:\w+:)\d+>")
MENTION_RE = re.compile(r"<@!?(\d+)>")
CHANNEL_RE = re.compile(r"<#\d+>")
ROLE_RE = re.compile(r"<@&\d+>")
COMMAND_RE = re.compile(r"^[" + "".join(re.escape(p) for p in COMMAND_PREFIXES) + r"]\w")
CUSTOM_EMOJI_TEXT_RE = re.compile(r":(\w+):")
# Tolerant: the model generates this token, so it sometimes malforms it.
SPLIT_RE = re.compile(r"<\s*\|?\s*split\s*\|?\s*>")

# lowercase name -> canonical speaker, covering both real names and aliases
SPEAKER_LOOKUP = {s.lower(): s for s in SPEAKERS}
SPEAKER_LOOKUP.update({a.lower(): s for a, s in ALIASES.items()})


class NeverChat(commands.Cog):

    def __init__(self, client):
        self.client = client
        # message_id -> speaker name, so the bot's own replies can be fed
        # back into context attributed to the persona rather than the bot.
        self.persona_messages = {}

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)

    # ------------------------------------------------------------ helpers

    def display_name(self, member):
        """Resolve to the name the model was trained on.

        Username first (stable), then nickname.
        """
        username = (getattr(member, "name", "") or "").lower()
        if username in USERNAMES:
            return USERNAMES[username]

        name = getattr(member, "nick", None) or getattr(member, "name", "") or "unknown"
        return PSEUDONYMS.get(name, name)

    def clean_content(self, message):
        text = (message.content or "").strip()
        if not text:
            return ""

        lookup = {str(u.id): self.display_name(u) for u in message.mentions}
        text = MENTION_RE.sub(
            lambda m: "@" + lookup.get(m.group(1), "someone"), text)
        text = ROLE_RE.sub("@role", text)
        text = CHANNEL_RE.sub("#channel", text)
        text = CUSTOM_EMOJI_RE.sub(r"\1", text)
        text = URL_RE.sub("[link]", text)
        return text.strip()

    def restore_emoji(self, text, guild):
        """Turn ':knite:' back into '<:knite:123>' so Discord renders it."""
        lookup = {}
        for emoji in self.client.emojis:
            lookup[emoji.name.lower()] = str(emoji)
        if guild:
            for emoji in guild.emojis:   # this server wins on name clashes
                lookup[emoji.name.lower()] = str(emoji)

        return CUSTOM_EMOJI_TEXT_RE.sub(
            lambda m: lookup.get(m.group(1).lower(), m.group(0)), text)

    def is_usable(self, text):
        if not text:
            return False
        if COMMAND_RE.match(text):
            return False
        # Only reject when the message IS a link -- emoji-only messages,
        # '?' and '...' have no word characters but are real messages.
        if URL_RE.search(text) and not re.search(r"\w", URL_RE.sub("", text)):
            return False
        return True

    async def build_context(self, ctx, limit):
        """Pull recent channel messages and format them as training did."""
        lines = []
        async for message in ctx.channel.history(limit=HISTORY_FETCH):
            if message.id == ctx.message.id:
                continue

            # Our own persona replies get re-attributed to the persona.
            if message.author.id == self.client.user.id:
                speaker = self.persona_messages.get(message.id)
                if not speaker:
                    continue
            else:
                if message.author.bot:
                    continue
                if message.author.id in BLOCKED_AUTHOR_IDS:
                    continue
                speaker = self.display_name(message.author)

            text = self.clean_content(message)
            if not self.is_usable(text):
                continue

            lines.append(f"{speaker}: {text}")
            if len(lines) >= limit:
                break

        lines.reverse()   # history returns newest first
        return lines

    def parse_args(self, split_message):
        """Pull an optional speaker and an optional count off the front.

        Accepts either order: '!nc zerod 3 msg' and '!nc 3 zerod msg'.
        Stops at the first token that is neither, so '!nc hey 3 people'
        keeps the whole thing as the message.
        """
        speaker, count = None, 1
        count_set = False

        for _ in range(2):
            if not split_message:
                break
            first, _, rest = split_message.partition(" ")
            low = first.lower()

            if speaker is None and low in SPEAKER_LOOKUP:
                speaker = SPEAKER_LOOKUP[low]
                split_message = rest.strip()
                continue

            if not count_set and low.isdigit():
                n = int(low)
                if 1 <= n <= COUNT_CEILING:
                    count = min(n, MAX_RESPONSES)
                    count_set = True
                    split_message = rest.strip()
                    continue
            break

        return speaker, count, split_message

    def pick_order(self, speaker, count):
        """Who replies, in order.

        A named speaker means every reply is theirs, so their model stays
        loaded. No name means N different random speakers.
        """
        if speaker:
            return [speaker] * count
        pool = list(SPEAKERS)
        random.shuffle(pool)
        return pool[:count]

    def model_for(self, speaker):
        return SOLO_MODELS.get(speaker, MODEL_NAME)

    async def unload_model(self, model):
        """Ask Ollama to drop a model from VRAM immediately.

        Called before switching models so two 4GB models don't fight over
        a 16GB card during a multi-speaker batch.
        """
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                        OLLAMA_GENERATE,
                        json={"model": model, "keep_alive": 0}) as resp:
                    await resp.read()
        except Exception as ex:
            print(f"unload {model}: {ex}")

    async def get_response(self, prompt, model):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "keep_alive": KEEP_ALIVE,
        }
        try:
            timeout = aiohttp.ClientTimeout(total=90)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(OLLAMA_CHAT, json=payload) as resp:
                    if resp.status != 200:
                        print(f"Ollama returned {resp.status} for {model}")
                        return None
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as ex:
            print(ex)
            return None

    # ------------------------------------------------------------ command

    @commands.command(aliases=["nc", "ncs"], help="Respond as someone from the chat.")
    @commands.cooldown(rate=1, per=20, type=BucketType.guild)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def neverchat(self, ctx):
        loaded_model = None
        try:
            split_message = Helpers.CommandStrip(self, ctx.message.content)
            split_message = Helpers.EmojiConvert(self, split_message)
            split_message = Helpers.DiscordEmoteConvert(self, split_message)
            split_message = (split_message or "").strip()

            speaker, count, split_message = self.parse_args(split_message)
            order = self.pick_order(speaker, count)

            # A supplied message goes last, in the slot the model conditions
            # on most strongly, with a shorter history window behind it.
            cleaned = ""
            if split_message:
                cleaned = URL_RE.sub("[link]", split_message).strip()

            use_context = (ctx.invoked_with.lower() not in NO_CONTEXT_ALIASES
                           or not cleaned)

            limit = CONTEXT_WITH_MESSAGE if cleaned else CONTEXT_MESSAGES
            context_lines = await self.build_context(ctx, limit) if use_context else []

            if cleaned:
                author = self.display_name(ctx.message.author)
                context_lines.append(f"{author}: {cleaned}")

            if not context_lines:
                await ctx.reply("Not enough chat history to work with.")
                ctx.command.reset_cooldown(ctx)
                return

            window = limit + (1 if cleaned else 0)
            first_message = True

            for index, who in enumerate(order):
                model = self.model_for(who)

                # Switching models: drop the old one before loading the new,
                # so they don't compete for VRAM.
                if loaded_model and model != loaded_model:
                    await self.unload_model(loaded_model)
                loaded_model = model

                context_lines = context_lines[-window:]
                now = datetime.now().strftime("%H:%M")
                prompt = (f"[{now}]\n" + "\n".join(context_lines)
                          + f"\n{who}:")

                await ctx.trigger_typing()
                response = await self.get_response(prompt, model)
                if response is None:
                    await ctx.trigger_typing()
                    response = await self.get_response(prompt, model)

                if response is None:
                    if first_message:
                        await ctx.reply("Local model did not respond. Cooldown has been reset, if you want to try again.")
                        ctx.command.reset_cooldown(ctx)
                    return

                raw_parts = [p.strip() for p in SPLIT_RE.split(response)]
                raw_parts = [p for p in raw_parts if p]
                if not raw_parts:
                    continue

                # Context keeps the RAW text so ':knite:' stays in the form
                # the model trained on rather than the rendered emoji.
                context_lines.append(
                    f"{who}: " + f"\n{BURST_DELIMITER}\n".join(raw_parts))

                parts = [self.restore_emoji(p, ctx.guild) for p in raw_parts]
                parts = [SPLIT_RE.sub(" ", p).strip()[:1750] for p in parts]
                parts = [p for p in parts if p]

                for i, part in enumerate(parts):
                    if i > 0:
                        await asyncio.sleep(BURST_DELAY)
                        await ctx.trigger_typing()

                    # Label a speaker only when they start talking.
                    label = i == 0 and (index == 0 or order[index - 1] != who)
                    body = f"**{who}:** {part}" if label else part

                    if first_message:
                        sent = await ctx.reply(body)
                        first_message = False
                    else:
                        sent = await ctx.send(body)
                    self.persona_messages[sent.id] = who

                if index < len(order) - 1:
                    same = order[index + 1] == who
                    await asyncio.sleep(BURST_DELAY if same else SPEAKER_DELAY)

            # Keep the cache from growing forever.
            if len(self.persona_messages) > 500:
                for key in list(self.persona_messages)[:250]:
                    del self.persona_messages[key]

        except Exception as ex:
            logger.LogPrint("NEVERCHAT ERROR", logging.ERROR, ex)
            await self.client.close()

    @commands.command(aliases=["ncwho"], help="List who the bot can imitate.")
    @commands.cooldown(rate=1, per=10, type=BucketType.guild)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def neverchatwho(self, ctx):
        lines = []
        for s in SPEAKERS:
            lines.append(f"{s} (own model)" if s in SOLO_MODELS else s)
        await ctx.reply("Can respond as: " + ", ".join(lines))


def setup(client):
    client.add_cog(NeverChat(client))