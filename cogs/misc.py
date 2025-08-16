import asyncio
import discord
import html2text
import logging
import json
import random
import re
import requests
import functools
from discord.ext import commands
from discord.ext.commands import BucketType
from os import path
import datetime

from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from internal.logs import logger
from bot import current_settings

class Misc(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.deep_ai_key = current_settings["keys"]["deep_ai"]

    async def cog_check(self, ctx):
        return await BLM.CheckIfCommandAllowed(ctx)
        
    #@commands.command(aliases=["tti"], help="Get an image generated from text.")    
    #@commands.cooldown(rate=1, per=20, type=BucketType.channel)
    #@commands.has_role("Bot Use")
    #@commands.guild_only()
    #async def texttoimage(self, ctx):
    #    await ctx.trigger_typing()
    #    max_length = 100
#
    #    input_message = ctx.message
    #    input_message = Helpers.CommandStrip(self, input_message.content)
    #    input_message = Helpers.EmojiConvert(self, input_message)
    #    input_message = Helpers.DiscordEmoteConvert(self, input_message)
    #    input_message = input_message[0:max_length]
#
    #    if len(input_message) > 0:
    #        r =  requests.post(
    #            "https://api.deepai.org/api/text2img",
    #            data={'text': input_message,},
    #            headers={'api-key': self.deep_ai_key})
    #        url = r.json()['output_url']
    #        await ctx.reply(f'{url}')
    #    else:
    #        await ctx.reply(f'Please enter a message.')

    @commands.command(aliases=["hobbes"], help="Get a random Calvin and Hobbes comic.")    
    @commands.cooldown(rate=1, per=20, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def calvin(self, ctx):
        def get_random_date():
            start_date = datetime.date(1985,11,18)
            end_date = datetime.date(1995,12,31)
            time_between_dates = end_date - start_date
            days_between_dates = time_between_dates.days
            random_number_of_days = random.randrange(days_between_dates)
            random_date = start_date + datetime.timedelta(days=random_number_of_days)
            return random_date
        
        valid = False
        await ctx.trigger_typing() 
        while not valid:
            comic_date = get_random_date()
            url = f'https://www.gocomics.com/calvinandhobbes/{comic_date.year}/{comic_date.month}/{comic_date.day}'
            loop = asyncio.get_event_loop()
            fn = functools.partial(requests.get, url)
            result = await loop.run_in_executor(None, fn)
            if result is not None and result.url != 'https://www.gocomics.com/calvinandhobbes':
                    valid = True
        await ctx.reply(url)
        
    @commands.command(aliases=["peanus"], help="Get a random Peanuts comic.")    
    @commands.cooldown(rate=1, per=20, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def peanuts(self, ctx):
        def get_random_date():
            start_date = datetime.date(1950,10,2)
            end_date = datetime.date(2000,2,12)
            time_between_dates = end_date - start_date
            days_between_dates = time_between_dates.days
            random_number_of_days = random.randrange(days_between_dates)
            random_date = start_date + datetime.timedelta(days=random_number_of_days)
            return random_date
        
        valid = False
        await ctx.trigger_typing() 
        while not valid:
            comic_date = get_random_date()
            url = f'https://www.gocomics.com/peanuts/{comic_date.year}/{comic_date.month}/{comic_date.day}'
            loop = asyncio.get_event_loop()
            fn = functools.partial(requests.get, url)
            result = await loop.run_in_executor(None, fn)
            if result is not None and result.url != 'https://www.gocomics.com/peanuts':
                valid = True
        await ctx.reply(url)
        



    @commands.command(aliases=["4chan"], help="Get a random post from the front page of a 4chan board.")    
    @commands.cooldown(rate=1, per=30, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def chan(self, ctx):

        async def GetRandomPost(board):
            valid = False
            loop = asyncio.get_event_loop()
            fn = functools.partial(requests.get, f'https://a.4cdn.org/{board}/threads.json')
            results = await loop.run_in_executor(None, fn)
            h = html2text.HTML2Text()
            h.ignore_links = True
            if results and results.status_code == 200:
                page = random.randint(0,3)
                data = results.json()
                thread_list = data[page]["threads"]
                while not valid:
                    random_thread_id = random.choice(thread_list)["no"]
                    await asyncio.sleep(1)
                    fn = functools.partial(requests.get, f'https://a.4cdn.org/{board}/thread/{random_thread_id}.json')
                    results = await loop.run_in_executor(None, fn)
                    if results and results.status_code == 200:
                        post_list = results.json()
                        random_post = random.choice(post_list["posts"])
                        if "sticky" in random_post:
                            continue
                        if "com" in random_post:
                            random_post = random_post["com"][0:1500]
                            clean_post = h.handle(random_post)
                            quotes = re.findall('>>[\d]*', clean_post)
                            if len(quotes) > 0:
                                for quote in quotes:
                                    clean_post = clean_post.replace(quote, '')
                            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', clean_post)
                            if len(urls) > 0:
                                for url in urls:
                                    clean_post = clean_post.replace(url, f'<{url}>')
                            if "bump" in clean_post.lower():
                                continue
                            if len(clean_post) > 0:
                                valid = True
                                return clean_post
                            
            return None

        valid_boards = ["a", "b", "c", "d", "e", "g", "gif", "h", "hr", "k", "m", "o", "p", "r", "s", "t", "u", "v", "vg", "vm", "vmg", "vr", "vrpg", "vst", "w", "wg", 
                        "i", "ic", "r9k", "s4s", "qa", "cm", "hm", "lgbt", "y", "3", "aco", "adv", "an", "bant", "biz", "cgl", "ck", "co", "diy", "fa", "fit", "gd", "hc", 
                        "his", "int", "jp", "lit", "mlp", "mu", "n", "news", "out", "po", "pol", "pw", "qst", "sci", "soc", "sp", "tg", "toy", "trv", "tv", "vp", "vt", 
                        "wsg", "wsr", "x", "xs", "trash"]
        board = Helpers.CommandStrip(self, ctx.message.content).split(' ')[0].lower()
        if board in valid_boards:
            await ctx.trigger_typing()          
            valid = False
            i = 0
            while not valid:
                post = await GetRandomPost(board)
                i += 1
                if i > 100:
                    await ctx.reply("Something went wrong when getting a post.")
                    break
                if post is None:
                    continue
                elif re.search('[a-zA-Z]', post):
                    valid = True
            await ctx.reply(post)
        else:
            await ctx.reply(f'Invalid board.')




def setup(client):
    client.add_cog(Misc(client))