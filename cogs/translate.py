import discord
import asyncio
import random
import logging
from discord.ext import commands
from discord.ext.commands import BucketType
from googletrans import Translator

# Internal Imports
from internal.logs import logger
from internal.data.trans_languages import language_dictionary, bad_trans_languages, bad_trans_languages_old
from internal.helpers import Helpers
from bot import current_settings


# This cog is for Google Translate commands as well as Bad Translate. 
# Made this a separate cog to Google.py just to keep things a little cleaner.

class Translate(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.btr_char_limit = 400
        self.translator = Translator()

    async def GetTranslation(self, message, target_lang='en'):
        if target_lang in language_dictionary:
            result = self.translator.translate(message, src='auto', dest=target_lang)
            return result.text
        else:
            return None
        

    @commands.command(aliases=["tr"], help="Translates a message into another language.\nThe language can be specified with lang:code, otherwise will default to translating into English.\nUsage: !translate Hola")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def translate(self, ctx):
        await ctx.trigger_typing()
        try:
            split_message = Helpers.CommandStrip(self, ctx.message.content).split('lang:')
            message_to_translate = split_message[0]
            message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
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
            logger.LogPrint("TRANSLATE ERROR", logging.ERROR, ex)
            await self.client.close()

    @commands.command(aliases=["btr", "Btr", "BTR"], help="Translates a message into many other languages in succession.\nUsage: !BadTranslate funny dog")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def badtranslate(self,ctx):
        random_lang = None        
        message_to_translate = Helpers.CommandStrip(self, ctx.message.content)
        message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
        if len(message_to_translate) <= self.btr_char_limit:
            if len(message_to_translate) < 1:
                task = asyncio.create_task(Helpers.GetLastTextMessage(self, ctx))
                await task
                message_to_translate = task.result()
                if message_to_translate == None:
                    await ctx.send(f'{ctx.message.author.mention}: Invalid message.')
                    return
            await ctx.trigger_typing()
            try:
                current_message = message_to_translate
                logger.LogPrint(f'BTR: Beginning BadTranslate.', logging.DEBUG)
                for i in range(0, 15):
                    previous_lang = random_lang
                    if i % 2 == 0 and i != 0 and True == False:
                        random_lang = 'en'
                    else:
                        while previous_lang == random_lang:
                            random_lang = random.choice(bad_trans_languages_old)
                    logger.LogPrint(f'BTR: Translating to {random_lang}.', logging.DEBUG)
                    logger.LogPrint(f'BTR: Pre:{current_message}', logging.DEBUG)
                    task = asyncio.create_task(self.GetTranslation(message=current_message, target_lang=random_lang))
                    await task
                    current_message = task.result()
                    logger.LogPrint(f'BTR: Post:{current_message}', logging.DEBUG)
                task = asyncio.create_task(self.GetTranslation(current_message))
                await task
                await ctx.send(f'{ctx.message.author.mention}: {task.result()}')
                logger.LogPrint(f'BTR: BadTranslate complete.', logging.DEBUG)
            except Exception as ex:
                logger.LogPrint("BAD TRANSLATE ERROR", logging.CRITICAL, ex)
                await ctx.send(f'ERROR: {ex}.\nThis means Google didnt respond properly, or you provided no message and the last message in the channel could not be retrieved.')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Message too long. Maximum length for BTR is {self.btr_char_limit} characters.', delete_after=10)

def setup(client):
    client.add_cog(Translate(client))