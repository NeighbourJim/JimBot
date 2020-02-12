import discord
import random
import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Internal Imports
from bot import current_settings
from internal.commandstrip import CommandStrip


class Google(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.cse_service = build('customsearch', 'v1', developerKey=current_settings["keys"]["google"])
        self.yt_service = build('youtube', 'v3', developerKey=current_settings["keys"]["google"])

    #region --------------- Image Search ---------------
    async def GetImageResult(self, message):
        query = CommandStrip(message)
        results = self.cse_service.cse().list(q=query, cx=current_settings["keys"]["cse"], searchType="image").execute()
        if "items" in results:
            return random.choice(list(results["items"]))
        else:
            return None

    async def GetSafeImageResult(self, message):
        query = CommandStrip(message)
        results = self.cse_service.cse().list(q=query, cx=current_settings["keys"]["cse"], searchType="image", safe="active").execute()
        if "items" in results:
            return random.choice(list(results["items"]))
        else:
            return None

    @commands.command(aliases=["i", "gi", "I", "GI", "image", "IMAGE"])    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.guild_only()
    async def ImageSearch(self, ctx):
        if ctx.message.channel.is_nsfw():
            task = asyncio.create_task(self.GetImageResult(ctx.message.content))
        else:
            task = asyncio.create_task(self.GetSafeImageResult(ctx.message.content))
        await task
        if(task.result() != None):
            await ctx.send(f'{ctx.message.author.mention}: **{task.result()["title"]}**\n{task.result()["link"]}')
        else:
            await ctx.send(f'No results found for that query. Note that Safe Search is on if the channel is not marked as NSFW!')
    #endregion

    #region --------------- Youtube Search ---------------
    async def GetYoutubeVideo(self, message):
        query = CommandStrip(message)
        results = self.yt_service.search().list(q=query, part='id,snippet', maxResults=10).execute()
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

    @commands.command(aliases=["yt", "YT"])
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.guild_only()
    async def Youtube(self, ctx):
        task = asyncio.create_task(self.GetYoutubeVideo(ctx.message.content))
        await task
        if task.result() != None:
            await ctx.send(f'{ctx.message.author.mention}: http://youtu.be/{task.result()["id"]["videoId"]}')
        else:
            await ctx.send(f'{ctx.message.author.mention}: No results found.')
    #endregion

def setup(client):
    client.add_cog(Google(client))