import discord
import random
import asyncio
import logging
from discord.ext import commands
from discord.ext.commands import BucketType
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Internal Imports
from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from bot import current_settings



class Google(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.cse_service = build('customsearch', 'v1', developerKey=current_settings["keys"]["google"])
        self.yt_service = build('youtube', 'v3', developerKey=current_settings["keys"]["google"])

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)

    #region --------------- Google Search ---------------
    async def GetSearchResult(self, message):
        query = Helpers.CommandStrip(self, message)
        results = self.cse_service.cse().list(q=query, cx=current_settings["keys"]["cse"]).execute()
        if "items" in results:
            final_results = []
            i = 0
            for item in results["items"]:
                if(i < 3):
                    final_results.append(item)
                    i += 1
                else:
                    break
            return final_results
        else:
            return None

    async def GetSafeSearchResult(self, message):
        query = Helpers.CommandStrip(self, message)
        results = self.cse_service.cse().list(q=query, cx=current_settings["keys"]["cse"], safe="active").execute()
        if "items" in results:
            final_results = []
            i = 0
            for item in results["items"]:
                if(i < 3):
                    final_results.append(item)
                    i += 1
                else:
                    break
            return final_results
        else:
            return None

    @commands.command(aliases=["g", "gs", "G", "Gs", "Google"], help="Searches Google and returns up to the first 3 results.\nUsage: !google funny dog.")    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def google(self,ctx):
        try:
            if ctx.message.channel.is_nsfw():
                task = asyncio.create_task(self.GetSearchResult(ctx.message.content))
            else:
                task = asyncio.create_task(self.GetSafeSearchResult(ctx.message.content))
            await task
            if(task.result() != None):
                fields = []
                for item in task.result():
                    fields.append({"name": item['title'], "value": item['link'], "inline": False })        
                result_dict = {
                    "author": {"name": "Search Results for '{}'".format(Helpers.CommandStrip(self, ctx.message.content))}, 
                    "fields": fields,
                    "thumbnail": {"url": "https://cdn.discordapp.com/attachments/144073497939935232/677385165462568970/500px-Google_G_Logo.svg.png"}
                    }
                result_embed = discord.Embed.from_dict(result_dict)
                await ctx.reply(embed=result_embed)
            else:
                await ctx.reply(f'No results found for that query.')
        except Exception as ex:
            await self.client.close()

            
            
    #endregion

    #region --------------- Image Search ---------------
    async def GetImageResult(self, message):
        forbidden = ["fbsbx.com", "i.kym-cdn.com", "x-raw-image"]
        query = Helpers.CommandStrip(self, message)
        results = self.cse_service.cse().list(q=query, cx=current_settings["keys"]["cse"], searchType="image").execute()
        if "items" in results:
            for i in range(0,100):
                result = random.choice(list(results["items"]))
                valid = True
                for term in forbidden:
                    if result["link"].find(term) > -1:
                        valid = False
                if valid:
                    break
            if valid:
                return result
            else:
                return None
        else:
            return None

    async def GetSafeImageResult(self, message):
        query = Helpers.CommandStrip(self, message)
        forbidden = ["fbsbx.com", "i.kym-cdn.com"]
        results = self.cse_service.cse().list(q=query, cx=current_settings["keys"]["cse"], searchType="image", safe="active").execute()
        if "items" in results:
            for i in range(0,100):
                result = random.choice(list(results["items"]))
                valid = True
                for term in forbidden:
                    if result["link"].find(term) > -1:
                        valid = False
                if valid:
                    break
            if valid:
                return result
            else:
                return None
        else:
            return None

    @commands.command(aliases=["i", "gi", "I", "GI", "Image", "IMAGE"], help="Searches Google for an image from a query.\nGives a random result from the front page. Safe-Search is enabled for SFW channels, and disabled for NSFW ones.\nUsage: !image funny dog\n")    
    @commands.cooldown(rate=1, per=60, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def image(self, ctx):
        try:
            if ctx.message.channel.is_nsfw():
                task = asyncio.create_task(self.GetImageResult(ctx.message.content))
            else:
                task = asyncio.create_task(self.GetSafeImageResult(ctx.message.content))
            await task
            if(task.result() != None):
                image_embed = discord.Embed()
                image_embed.title = task.result()["title"]
                if len(task.result()["link"]) <= 200:
                    image_embed.description = task.result()["link"]
                if len(ctx.guild.members) < 300:
                    image_embed.set_image(url=task.result()["link"])
                    ctx.command.reset_cooldown(ctx)
                else:
                    image_embed.set_thumbnail(url=task.result()["link"])
                await ctx.reply(embed=image_embed)
            else:
                await ctx.reply(f'No results found for \'{Helpers.CommandStrip(self, ctx.message.content)}\'. Note that Safe Search is on if the channel is not marked as NSFW!', delete_after=10)
        except Exception as ex:
            logger.LogPrint("IMAGE ERROR", logging.CRITICAL, ex)
            if str(ex).find('Invalid Form Body') != -1:
                await ctx.reply(f'{task.result()["link"]}')
            if str(ex).find('HttpError 429') != -1:
                await ctx.reply(f'ERROR: Quota exceeded. Resets at Midnight PST.')
            if str(ex).find('HttpError 503') != -1:
                await ctx.reply(f'ERROR: The service is currently unavailable.')
            else:
                await ctx.reply(f'ERROR: Something went wrong.')
    #endregion

    #region --------------- Youtube Search ---------------
    async def GetYoutubeVideo(self, message):
        query = Helpers.CommandStrip(self, message) # removes the command invocation from the message ie '!yt funny dog' becomes 'funny dog'
        results = self.yt_service.search().list(q=query, part='id,snippet', type="video", maxResults=1).execute()
        videos = []
        if "items" in results:
            for item in results.get('items', []):
                if item['id']['kind'] == 'youtube#video':
                    videos.append(item)
            if len(videos) > 0:
                return videos[0]
            else:
                return None
        else:
            return None

    @commands.command(aliases=["yt", "YT", "Youtube", "YouTube"], help="Searches Youtube for a query and returns the first video result.\nUsage: !yt funny dog.")
    @commands.cooldown(rate=1, per=15, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def youtube(self, ctx):
        try:
            task = asyncio.create_task(self.GetYoutubeVideo(ctx.message.content))
            await task
            if task.result() != None:
                await ctx.reply(f'http://youtu.be/{task.result()["id"]["videoId"]}')
            else:
                await ctx.reply(f'No results found.')
        except Exception as ex:
            logger.LogPrint(f"ERROR: {ctx.command} - {ex}", logging.CRITICAL, ex)
            if str(ex).find('Daily Limit Exceeded'):
                await ctx.reply(f'ERROR: Daily Search Limit Exceeded. The limit resets at midnight Pacific Time.')
            else:
                await ctx.reply(f'ERROR: Something went wrong.')
            
    #endregion

def setup(client):
    client.add_cog(Google(client))