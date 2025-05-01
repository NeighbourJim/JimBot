import discord
import asyncio
import random
import logging
import functools
from discord.ext import commands
from discord.ext.commands import BucketType
import googletrans
import httpx==0.13.3
from googletrans import Translator

# Internal Imports
from internal.logs import logger
from internal.data.trans_languages import language_dictionary, bad_trans_languages, bad_trans_languages_old
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from bot import current_settings


# This cog is for Google Translate commands as well as Bad Translate. 
# Made this a separate cog to Google.py just to keep things a little cleaner.

class Translate(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.btr_char_limit = 600
        self.translator = Translator()

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)
        
    async def GetTranslation(self, message, target_lang='en'):
        if target_lang in language_dictionary:
            fn = functools.partial(
                self.translator.translate,
                message,
                src='auto',
                dest=target_lang
            )
            result = await asyncio.get_event_loop().run_in_executor(None, fn)
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
            message_to_translate = Helpers.DiscordEmoteConvert(self, message_to_translate)
            target = None
            if len(message_to_translate) < 1:
                task = asyncio.create_task(Helpers.GetLastTextMessage(self, ctx))
                await task            
                message_to_translate = task.result()
                if message_to_translate == None:
                    await ctx.reply(f'Invalid message.')
                    return
                message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
                message_to_translate = Helpers.DiscordEmoteConvert(self, message_to_translate)
            if len(split_message) > 1:
                target = split_message[1].strip()
            if target != None:
                task = asyncio.create_task(self.GetTranslation(message=message_to_translate, target_lang=target))
            else:
                task = asyncio.create_task(self.GetTranslation(message_to_translate))
            await task
            if task.result() != None:
                await ctx.reply(f'{task.result()}')
            else:
                await ctx.reply(f'Translation failed, for some reason.')
        except Exception as ex:
            logger.LogPrint("TRANSLATE ERROR", logging.ERROR, ex)
            await self.client.close()

    @commands.command(aliases=["btrw"], help="Translates a message into many other languages in succession.\nUsage: !BadTranslate funny dog")    
    @commands.cooldown(rate=1, per=30, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def badtranslate_wip(self,ctx):
        random_lang = None  
        messages = []
        target_message = ctx.message

        message_to_translate = Helpers.CommandStrip(self, target_message.content)
        message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
        message_to_translate = Helpers.DiscordEmoteConvert(self, message_to_translate)
        message_to_translate = message_to_translate[0:self.btr_char_limit]
        if len(message_to_translate) < 1:
            task = asyncio.create_task(Helpers.GetLastTextMessage(self, ctx))
            await task            
            target_message = task.result()
            message_to_translate = Helpers.CommandStrip(self, target_message.content)
            message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
            message_to_translate = Helpers.DiscordEmoteConvert(self, message_to_translate)
            message_to_translate = Helpers.StripMentions(self, message_to_translate)
            message_to_translate = message_to_translate[0:self.btr_char_limit]
            if message_to_translate == None:
                await ctx.reply(f'Invalid message.')
                return
        try:
            current_message = message_to_translate
            logger.LogPrint(f'BTR: Beginning BadTranslate.', logging.DEBUG)
            j = 1
            for i in range(0, 15):
                if i % 3 == 0:
                    await ctx.trigger_typing()
                previous_lang = random_lang
                while previous_lang == random_lang:
                    random_lang = random.choice(bad_trans_languages_old)
                logger.LogPrint(f'BTR: Translating to {random_lang}.', logging.DEBUG)
                logger.LogPrint(f'BTR: Pre:{current_message}', logging.DEBUG)
                task = asyncio.create_task(self.GetTranslation(message=current_message, target_lang=random_lang))
                await task
                current_message = task.result()
                
                if i % 2 == 0 and i != 0:
                    eng_task = asyncio.create_task(self.GetTranslation(message=current_message, target_lang='en'))
                    await eng_task
                    messages.append(f'{j}: {eng_task.result()}')
                    j += 1
                
                logger.LogPrint(f'BTR: Post:{current_message}', logging.DEBUG)
            task = asyncio.create_task(self.GetTranslation(current_message))
            await task
            messages.append(task.result())
            if target_message.content == ctx.message.content:
                task = asyncio.create_task(ctx.reply(f'{messages.pop(0)}'))
            else:
                try:
                    await ctx.message.delete()
                except discord.errors.HTTPException:
                    logger.LogPrint(f'Message was already deleted.', logging.WARNING)
                task = asyncio.create_task(target_message.reply(f'{messages.pop(0)}', mention_author=False))
            await task
            await asyncio.sleep(2)
            for i in range(0, len(messages)):
                await ctx.trigger_typing()
                result = f'{messages[i]}'
                task_two = asyncio.create_task(task.result().edit(content=result))
                await task_two
                await asyncio.sleep(4)
            ctx.command.reset_cooldown(ctx)
            logger.LogPrint(f'BTR: BadTranslate complete.', logging.DEBUG)
        except Exception as ex:
            logger.LogPrint("BAD TRANSLATE ERROR", logging.CRITICAL, ex)
            await ctx.reply(f'ERROR: {ex}.\nThis means Google didnt respond properly, or you provided no message and the last message in the channel could not be retrieved.')

    @commands.command(aliases=["btr", "Btr", "BTR"], help="Translates a message into many other languages in succession.\nUsage: !BadTranslate funny dog")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def badtranslate(self,ctx):
        random_lang = None  
        target_message = ctx.message
        message_to_translate = Helpers.CommandStrip(self, target_message.content)
        message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
        message_to_translate = Helpers.DiscordEmoteConvert(self, message_to_translate)
        message_to_translate = message_to_translate[0:self.btr_char_limit]
        if len(message_to_translate) < 1:
            task = asyncio.create_task(Helpers.GetLastTextMessage(self, ctx))
            await task            
            target_message = task.result()
            message_to_translate = Helpers.CommandStrip(self, target_message.content)
            message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
            message_to_translate = Helpers.DiscordEmoteConvert(self, message_to_translate)
            message_to_translate = Helpers.StripMentions(self, message_to_translate)
            message_to_translate = message_to_translate[0:self.btr_char_limit]
            if message_to_translate == None:
                await ctx.reply(f'Invalid message.')
                return
        try:
            current_message = message_to_translate
            print(current_message)
            logger.LogPrint(f'BTR: Beginning BadTranslate.', logging.DEBUG)
            for i in range(0, 7):
                previous_lang = random_lang
                if i % 2 == 0 and i != 0 and True == False:
                    random_lang = 'en'
                else:
                    while previous_lang == random_lang:
                        random_lang = random.choice(bad_trans_languages_old)
                logger.LogPrint(f'BTR: Translating to {random_lang}.', logging.DEBUG)
                logger.LogPrint(f'BTR: Pre:{current_message}', logging.DEBUG)
                if i % 3 == 0:
                    await ctx.trigger_typing()
                task = asyncio.create_task(self.GetTranslation(message=current_message, target_lang=random_lang))
                await task
                current_message = task.result()
                logger.LogPrint(f'BTR: Post:{current_message}', logging.DEBUG)
            await ctx.trigger_typing()
            task = asyncio.create_task(self.GetTranslation(current_message))
            await task
            if target_message.content == ctx.message.content:
                await ctx.reply(f'{task.result()}')
            else:
                try:
                    await ctx.message.delete()
                except discord.errors.HTTPException:
                    logger.LogPrint(f'Message was already deleted.', logging.WARNING)
                await target_message.reply(f'{task.result()}', mention_author=False)
            logger.LogPrint(f'BTR: BadTranslate complete.', logging.DEBUG)
        except Exception as ex:
            logger.LogPrint("BAD TRANSLATE ERROR", logging.CRITICAL, ex)
            await ctx.reply(f'ERROR: {ex}.\nThis means Google didnt respond properly, or you provided no message and the last message in the channel could not be retrieved.')

def setup(client):
    client.add_cog(Translate(client))