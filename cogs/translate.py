import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType
from googletrans import Translator

# Internal Imports
from internal.trans_languages import language_dictionary, bad_trans_languages
from internal.helpers import Helper
from bot import current_settings


# This cog is for Google Translate commands as well as Bad Translate. 
# Made a separate cog to Google.py just to keep things a little cleaner.

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
        

    @commands.command(aliases=["tr"])    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def translate(self, ctx):
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



def setup(client):
    client.add_cog(Translate(client))