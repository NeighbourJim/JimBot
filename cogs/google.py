import discord
import random
import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Internal Imports
from internal.helpers import Helper
from bot import current_settings



class Google(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.cse_service = build('customsearch', 'v1', developerKey=current_settings["keys"]["google"])
        self.yt_service = build('youtube', 'v3', developerKey=current_settings["keys"]["google"])

    #region --------------- Google Search ---------------
    async def GetSearchResult(self, message):
        query = Helper.CommandStrip(message)
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
        query = Helper.CommandStrip(message)
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

    @commands.command(aliases=["g", "gs", "G", "Gs", "google"])    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.guild_only()
    async def Google(self,ctx):
        if ctx.message.channel.is_nsfw():
            task = asyncio.create_task(self.GetSearchResult(ctx.message.content))
        else:
            task = asyncio.create_task(self.GetSafeSearchResult(ctx.message.content))
        await task
        if(task.result() != None):
            fields = [  {"name": task.result()[0]['title'], "value": task.result()[0]['link'], "inline": False }, 
                        {"name": task.result()[1]['title'], "value": task.result()[1]['link'], "inline": False }, 
                        {"name": task.result()[2]['title'], "value": task.result()[2]['link'], "inline": False }, ]
            result_dict = {
                "author": {"name": "Search Results for '{}'".format(Helper.CommandStrip(ctx.message.content))}, 
                "footer": {"text": "Searched for by {}".format(ctx.message.author)}, 
                "fields": fields,
                "colour": discord.colour.Colour.blurple(),
                "thumbnail": {"url": "https://cdn.discordapp.com/attachments/144073497939935232/677385165462568970/500px-Google_G_Logo.svg.png"}
                }
            result_embed = discord.Embed.from_dict(result_dict)
            await ctx.send(embed=result_embed)
        else:
            await ctx.send(f'{ctx.message.author.mention}: No results found for that query.')

            
            
    #endregion

    #region --------------- Image Search ---------------
    async def GetImageResult(self, message):
        query = Helper.CommandStrip(message)
        results = self.cse_service.cse().list(q=query, cx=current_settings["keys"]["cse"], searchType="image").execute()
        if "items" in results:
            return random.choice(list(results["items"]))
        else:
            return None

    async def GetSafeImageResult(self, message):
        query = Helper.CommandStrip(message)
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
            await ctx.send(f'{ctx.message.author.mention}: No results found for that query. Note that Safe Search is on if the channel is not marked as NSFW!')
    #endregion

    #region --------------- Youtube Search ---------------
    async def GetYoutubeVideo(self, message):
        query = Helper.CommandStrip(message)
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