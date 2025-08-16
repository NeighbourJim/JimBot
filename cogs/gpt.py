import discord
import logging
import random
import json
import html
import freeGPT
import requests
import asyncio
import functools
from PIL import Image
from io import BytesIO
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from internal.databasemanager import dbm
from bot import current_settings


class GPT(commands.Cog):    

    def __init__(self, client):
        self.client = client
        self.server_url = "http://10.0.0.1:7881/v1/chat/completions"
        self.headers = {"Content-Type": "application/json"}
        self.banned_terms = ["tits","titty", "titties","phallus","butthole", "breasts", "breast", "boobs", "boob", "pussy", "cock", "penis", "sex ", "sex,", "nude", "asshole", "genitalia", "semen", "masturbate", "masturbating", "masturbation", "dildo", "dick", "naked", "nipple", "areola", "vagina", "labia", "titties", "cunny", "coochie"]

    async def cog_check(self, ctx):
        return await BLM.CheckIfCommandAllowed(ctx)

    async def get_gpt_text(self, prompt):
        try:
            response = await getattr(freeGPT, "gpt4").Completion().create(prompt)
            return response
        except Exception as e:
            print(f"ERROR: {e}")
            return None
        
    async def get_ai_image(self, prompt, id):
        try:
            if random.randint(1,3) == 0:
                model = "pollinations"
            else:
                model = "prodia"
            response = await getattr(freeGPT, model).Generation().create(prompt)
            im = Image.open(BytesIO(response))
            im.save(f'./internal/data/images/ai{id}.jpg')
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return None
        
    async def get_text_local(self, prompt, character):
        try:
            history = []
            history.append({"role": "user", "content": prompt})
            data = {
                "mode": "chat-instruct",
                "instruction_template": "Llama-v3",
                "character": character,
                "messages": history,
                "max_tokens": 200,
                "temperature": 0.8,
            }
            fn = functools.partial(requests.post, self.server_url, headers=self.headers, json=data, verify=False)
            response = await asyncio.get_event_loop().run_in_executor(None, fn)
            assistant_message = response.json()['choices'][0]['message']['content']
            return assistant_message
        except Exception as e:
            print(f"ERROR: {e}")
            return None

    @commands.command(aliases=["evil2"], help="")    
    @commands.cooldown(rate=1, per=15, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def gptlocal_evil(self, ctx):
        split_message = Helpers.CommandStrip(self, ctx.message.content)
        split_message = Helpers.EmojiConvert(self, split_message)
        split_message = Helpers.DiscordEmoteConvert(self, split_message)
        split_message = split_message[:2000]
        if len(split_message) < 1:
            await ctx.reply(f'You didn\'t enter a message.')
            return
        await ctx.trigger_typing()
        task = asyncio.create_task(self.get_text_local(split_message, "EvilTroll2"))
        await task            
        gpt_response = task.result()
        if gpt_response is None:
            await ctx.reply("GPT did not respond.")
        else:
            gpt_response = gpt_response[:1750].encode('utf-8')
            await ctx.reply(f"{gpt_response.decode('utf-8')}")

    @commands.command(aliases=["chat2"], help="")    
    @commands.cooldown(rate=1, per=15, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def gptlocal(self, ctx):
        split_message = Helpers.CommandStrip(self, ctx.message.content)
        split_message = Helpers.EmojiConvert(self, split_message)
        split_message = Helpers.DiscordEmoteConvert(self, split_message)
        split_message = split_message[:2000]
        if len(split_message) < 1:
            await ctx.reply(f'You didn\'t enter a message.')
            return
        await ctx.trigger_typing()
        task = asyncio.create_task(self.get_text_local(split_message, "Assistant"))
        await task            
        gpt_response = task.result()
        if gpt_response is None:
            await ctx.reply("GPT did not respond.")
        else:
            gpt_response = gpt_response[:1750].encode('utf-8')
            await ctx.reply(f"{gpt_response.decode('utf-8')}")

    @commands.command(aliases=["ig", "igen"], help="Generate an image")    
    @commands.cooldown(rate=1, per=15, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def imagegen(self, ctx):
        split_message = Helpers.CommandStrip(self, ctx.message.content)
        split_message = Helpers.EmojiConvert(self, split_message)
        split_message = Helpers.DiscordEmoteConvert(self, split_message)
        split_message = split_message[:400]
        split_message = split_message.lower()
        if len(split_message) < 1:
            await ctx.reply(f'You didn\'t enter a prompt.')
            return
        if not ctx.message.channel.is_nsfw():
            for word in self.banned_terms:
                split_message = split_message.replace(word, "something")
        await ctx.trigger_typing()
        task = asyncio.create_task(self.get_ai_image(split_message, ctx.guild.id))
        await task            
        response = task.result()
        if response == None:
            await ctx.reply(f'Failed to generate image.')
            return
        else:
            if not ctx.message.channel.is_nsfw():
                image_file = discord.File(f'./internal/data/images/ai{ctx.guild.id}.jpg', filename='SPOILER_ai.jpg')
                sent = await ctx.reply(f"**May be NSFW. Click at own risk.**\nPrompt:``{split_message}``", file=image_file)
            else:
                image_file = discord.File(f'./internal/data/images/ai{ctx.guild.id}.jpg', filename='ai.jpg')
                sent = await ctx.reply(f"Prompt:``{split_message}``", file=image_file)

        



def setup(client):
    client.add_cog(GPT(client))