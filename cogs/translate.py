import discord
import asyncio
import random
from discord.ext import commands
from discord.ext.commands import BucketType
from googletrans import Translator

# Internal Imports
from internal.data.trans_languages import language_dictionary, bad_trans_languages
from internal.helpers import Helper
from bot import current_settings


# This cog is for Google Translate commands as well as Bad Translate. 
# Made this a separate cog to Google.py just to keep things a little cleaner.

class Translate(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.translator = Translator()

    async def GetTranslation(self, message, target_lang='en'):
        if target_lang in language_dictionary:
            result = self.translator.translate(message, src='auto', dest=target_lang)
            return result.text
        else:
            return None
        

    @commands.command(aliases=["tr"], help="Translates a message into another language.\nThe language can be specified with lang:code, otherwise will default to translating into English.\nUsage: !translate Hola")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.guild_only()
    async def translate(self, ctx):
        await ctx.trigger_typing()
        try:
            split_message = Helper.CommandStrip(ctx.message.content).split('lang:')
            message_to_translate = split_message[0]
            target = None
            if len(split_message) > 1:
                target = split_message[1].strip()
            if target != None:
                task = asyncio.create_task(self.GetTranslation(message=message_to_translate, target_lang=target))
            else:
                task = asyncio.create_task(self.GetTranslation(message_to_translate))
            await task
            if task.result() != None:
                await ctx.send(f'{ctx.message.author.mention}: {task.result()}')
            else:
                await ctx.send(f'{ctx.message.author.mention}: Translation failed, for some reason.')
        except Exception as ex:
            print(ex)
            await self.client.close()

    @commands.command(aliases=["btr"], help="Translates a message into many other languages in succession.\nUsage: !BadTranslate funny dog")    
    @commands.cooldown(rate=1, per=30, type=BucketType.channel)
    @commands.guild_only()
    async def badtranslate(self,ctx):
        await ctx.trigger_typing()
        try:
            message_to_translate = Helper.CommandStrip(ctx.message.content)
            current_message = message_to_translate
            for i in range(0, 10):
                random_lang = random.choice(bad_trans_languages)
                task = asyncio.create_task(self.GetTranslation(message=current_message, target_lang=random_lang))
                await task
                current_message = task.result()
                if current_message == 'invalid destination language':
                    i -= 1
            task = asyncio.create_task(self.GetTranslation(current_message))
            await task
            await ctx.send(f'{ctx.message.author.mention}: {task.result()}')
        except Exception as ex:
            print(ex)
            await self.client.close()

        





def setup(client):
    client.add_cog(Translate(client))