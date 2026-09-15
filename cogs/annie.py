import discord
import logging
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

OLLAMA_URL = "http://10.0.0.1:11434/v1/chat/completions"
MODEL_NAME = "mouse2-final"
SPEAKER = "Annie"           # the prompt cue -- MUST match training data
DISPLAY_NAME = "MouseBot"   # what shows in Discord

# Nickname variants of the target, matching the training data.
PSEUDONYMS = {
    "mouse, evil doubter": "Annie",
    "anniep": "Annie",
    "mousebot" : "Annie",
}

CONTEXT_MESSAGES = 8        # history lines when no message is supplied
CONTEXT_WITH_MESSAGE = 4    # history lines when a message IS supplied
HISTORY_FETCH = 40          # how many to pull before filtering down
BURST_DELIMITER = "<|split|>"
BURST_DELAY = 1.2           # seconds between one reply's own messages
REPLY_DELAY = 1.8           # seconds between separate replies
MAX_RESPONSES = 3           # cap on the "generate N replies" argument
MAX_TOKENS = 120
TEMPERATURE = 1
KEEP_ALIVE = "5m"
# Must match the system prompt used when building the training data.
SYSTEM_PROMPT = "You are a member of this group chat. Continue the conversation. You are responding as Annie. Annie uses they/them pronouns. Annie has two cats - Iggy and Dusty. Annie lives in the UK."
# Invoking the command under one of these names skips channel context.
NO_CONTEXT_ALIASES = {"ans"}

BLOCKED_AUTHOR_IDS = set()

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
LABEL_RE = re.compile(r"^\*\*[^*]{1,40}:\*\*\s*")
SELF_LABEL_RE = re.compile(
    rf"^\s*(?:\*\*)?(?:{re.escape(SPEAKER)}|{re.escape(DISPLAY_NAME)})\s*:(?:\*\*)?\s*",
    re.IGNORECASE)


class Annie(commands.Cog):

    def __init__(self, client):
        self.client = client
        # message_id -> True, so the bot's own replies can be fed back into
        # context attributed to Annie rather than to the bot account.
        self.persona_messages = {}

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)

    # ------------------------------------------------------------ helpers

    def display_name(self, member):
        name = getattr(member, "nick", None) or member.name
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
        """Turn ':sob:' back into '<:sob:123>' so Discord renders it."""
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

            # Our own replies get re-attributed to Annie.
            if message.author.id == self.client.user.id:
                if message.id not in self.persona_messages:
                    continue
                speaker = SPEAKER
            else:
                if message.author.bot:
                    continue
                if message.author.id in BLOCKED_AUTHOR_IDS:
                    continue
                speaker = self.display_name(message.author)

            text = self.clean_content(message)
            if message.author.id == self.client.user.id:
                text = LABEL_RE.sub("", text)
            if not self.is_usable(text):
                continue

            lines.append(f"{speaker}: {text}")
            if len(lines) >= limit:
                break

        lines.reverse()   # history returns newest first
        return lines

    def parse_args(self, split_message):
        """Pull an optional count off the front: '!annie 3 hey there'."""
        count = 1
        if split_message:
            first, _, rest = split_message.partition(" ")
            if first.isdigit():
                n = int(first)
                if 1 <= n <= MAX_RESPONSES:
                    count = n
                    split_message = rest.strip()
        return count, split_message

    async def get_response(self, prompt):
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "keep_alive": KEEP_ALIVE,
        }
        try:
            timeout = aiohttp.ClientTimeout(total=90)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(OLLAMA_URL, json=payload) as resp:
                    if resp.status != 200:
                        print(f"Ollama returned {resp.status}")
                        return None
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as ex:
            print(ex)
            return None

    # ------------------------------------------------------------ command

    @commands.command(aliases=["an", "ans"], help="Say something as Annie.")
    @commands.cooldown(rate=1, per=10, type=BucketType.guild)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def annie(self, ctx):
        try:
            split_message = Helpers.CommandStrip(self, ctx.message.content)
            split_message = Helpers.EmojiConvert(self, split_message)
            split_message = Helpers.DiscordEmoteConvert(self, split_message)
            split_message = (split_message or "").strip()

            count, split_message = self.parse_args(split_message)

            # A supplied message goes last, in the slot the model conditions
            # on most strongly, with a shorter history window behind it.
            cleaned = ""
            if split_message:
                cleaned = URL_RE.sub("[link]", split_message).strip()

            # !ans skips channel context, but only when there's a message to
            # work from -- a bare prompt is off-distribution for this model.
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

            for index in range(count):
                context_lines = context_lines[-window:]
                now = datetime.now().strftime("%H:%M")
                prompt = (f"[{now}]\n" + "\n".join(context_lines)
                          + f"\n{SPEAKER}:")

                await ctx.trigger_typing()
                response = await self.get_response(prompt)
                if response is None:
                    await ctx.trigger_typing()
                    response = await self.get_response(prompt)

                if response is None:
                    if first_message:
                        await ctx.reply("Local model did not respond. Cooldown has been reset, if you want to try again.")
                        ctx.command.reset_cooldown(ctx)
                    return

                raw_parts = [SELF_LABEL_RE.sub("", p).strip()
                             for p in SPLIT_RE.split(response)]
                raw_parts = [p for p in raw_parts if p]

                if not raw_parts:
                    # Everything got filtered -- try once more before moving on.
                    response = await self.get_response(prompt)
                    if response:
                        raw_parts = [SELF_LABEL_RE.sub("", p).strip()
                                     for p in SPLIT_RE.split(response)]
                        raw_parts = [p for p in raw_parts if p]
                if not raw_parts:
                    continue

                # Context keeps the RAW text so ':sob:' stays in the form
                # the model trained on rather than the rendered emoji.
                context_lines.append(
                    f"{SPEAKER}: " + f"\n{BURST_DELIMITER}\n".join(raw_parts))

                parts = [self.restore_emoji(p, ctx.guild) for p in raw_parts]
                parts = [SPLIT_RE.sub(" ", p).strip()[:1750] for p in parts]
                parts = [p for p in parts if p]

                for i, part in enumerate(parts):
                    if i > 0:
                        await asyncio.sleep(BURST_DELAY)
                        await ctx.trigger_typing()

                    # Label only on the very first message of the batch.
                    body = f"**{DISPLAY_NAME}:** {part}" if first_message else part

                    if first_message:
                        sent = await ctx.reply(body)
                        first_message = False
                    else:
                        sent = await ctx.send(body)
                    self.persona_messages[sent.id] = True

                if index < count - 1:
                    await asyncio.sleep(REPLY_DELAY)

            if first_message:
                await ctx.reply("Model returned nothing usable.")
                ctx.command.reset_cooldown(ctx)
                return

            # Keep the cache from growing forever.
            if len(self.persona_messages) > 500:
                for key in list(self.persona_messages)[:250]:
                    del self.persona_messages[key]

        except Exception as ex:
            logger.LogPrint("ANNIE ERROR", logging.ERROR, ex)
            await self.client.close()


def setup(client):
    client.add_cog(Annie(client))