import discord
import asyncio
import random
import logging
import functools
from discord.ext import commands
from discord.ext.commands import BucketType
from deep_translator import GoogleTranslator
from deep_translator.exceptions import RequestError

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
        self.translator = GoogleTranslator(source='auto', target='en')
        langs_dict = self.translator.get_supported_languages(as_dict=True)
        supported_codes = langs_dict.values()
        for lang in bad_trans_languages_old:
            if lang not in supported_codes:
                logger.LogPrint(f'Language code {lang} from bad_trans_languages_old is not supported by the translator.', logging.WARNING)


    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)
        
    async def GetTranslation(self, message, target_lang='en', retries=3, delay=2):
        if target_lang not in language_dictionary:
            # Check if the language is in the bad_trans_languages_old list, if so, allow it.
            if target_lang not in bad_trans_languages_old:
                return None

        self.translator.target = target_lang
        
        for i in range(retries):
            try:
                fn = functools.partial(
                    self.translator.translate,
                    message
                )
                result = await asyncio.get_event_loop().run_in_executor(None, fn)
                return result
            except RequestError as e:
                logger.LogPrint(f"Translation failed with RequestError (attempt {i+1}/{retries}): {e}", logging.WARNING)
                if i < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    logger.LogPrint(f"Translation failed after {retries} retries.", logging.ERROR)
                    return None
            except Exception as e:
                logger.LogPrint(f"An unexpected error occurred during translation (attempt {i+1}/{retries}): {e}", logging.ERROR)
                # For unexpected errors, maybe we don't retry. Let's fail fast.
                return None
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

    @commands.command(aliases=["btr", "Btr", "BTR"], help="Translates a message into many other languages and back to English in succession.\nUsage: !badtranslate funny dog")
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def badtranslate(self, ctx):
        target_message = ctx.message
        message_to_translate = Helpers.CommandStrip(self, target_message.content)
        message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
        message_to_translate = Helpers.DiscordEmoteConvert(self, message_to_translate)
        message_to_translate = message_to_translate[0:self.btr_char_limit]
        if len(message_to_translate) < 1:
            task = asyncio.create_task(Helpers.GetLastTextMessage(self, ctx))
            await task
            target_message = task.result()
            if target_message is None:
                await ctx.reply(f'Invalid message.')
                return
            message_to_translate = Helpers.CommandStrip(self, target_message.content)
            message_to_translate = Helpers.EmojiConvert(self, message_to_translate)
            message_to_translate = Helpers.DiscordEmoteConvert(self, message_to_translate)
            message_to_translate = Helpers.StripMentions(self, message_to_translate)
            message_to_translate = message_to_translate[0:self.btr_char_limit]
            if message_to_translate is None:
                await ctx.reply(f'Invalid message.')
                return
        try:
            await ctx.trigger_typing()
            current_message = message_to_translate
            for i in range(15):
                if i % 3 == 0 and i != 0:
                    await ctx.trigger_typing()

                # 1. To random language
                random_lang_code = random.choice(bad_trans_languages_old)
                translated_to_random = await self.GetTranslation(current_message, target_lang=random_lang_code)
                if not translated_to_random:
                    await ctx.reply(f"Translation failed. Aborting.")
                    return
                current_message = translated_to_random
                await asyncio.sleep(0.5)

            # 2. Back to English
            translated_back_to_english = await self.GetTranslation(current_message, target_lang='en')
            if not translated_back_to_english:
                await ctx.reply(f"Translation back to English failed. Aborting.")
                return
            current_message = translated_back_to_english

            # Send the final result
            DISCORD_CHAR_LIMIT = 2000
            TRUNCATION_MESSAGE = "\n... (message truncated as it exceeded Discord's character limit)"
            if len(current_message) > DISCORD_CHAR_LIMIT:
                current_message = current_message[:DISCORD_CHAR_LIMIT - len(TRUNCATION_MESSAGE)] + TRUNCATION_MESSAGE
                
            if target_message.content == ctx.message.content:
                await ctx.reply(f'{current_message}')
            else:
                try:
                    await ctx.message.delete()
                except discord.errors.HTTPException:
                    logger.LogPrint(f'Message was already deleted.', logging.WARNING)
                await target_message.reply(f'{current_message}', mention_author=False)
            ctx.command.reset_cooldown(ctx)

        except Exception as ex:
            logger.LogPrint("BAD TRANSLATE ERROR", logging.CRITICAL, ex)
            await ctx.reply(f'ERROR: {ex}.\nSomething went wrong during the bad translation process.')

def setup(client):
    client.add_cog(Translate(client))