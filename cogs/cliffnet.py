import discord
import logging
import random
import requests
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helper

class cliffnet(commands.Cog):

    def __init__(self, client):
        self.client = client
              
    @commands.command(aliases=["Scramble", "s"], help="scrambles word order")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def scramble(self, ctx):
        if ctx.guild.id == 107847342006226944:
            split_message = Helper.CommandStrip(ctx.message.content).split(' ')
            if len(split_message) > 0:
                result = random.sample(split_message, len(split_message))
                stringResult= " "
                stringResult = stringResult.join(result)
                await ctx.send(f'{ctx.message.author.mention}: {stringResult}')
            else:
                await ctx.send(f'{ctx.message.author.mention}: call tech support on Jims PM')


    @commands.command(aliases=["News", "n"], help="Search the recent news via a keyword! Powered by newsapi.org")  
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def command2(self, ctx):
        if ctx.guild.id == 107847342006226944:

            try:
                input = ctx.message.content
                source = (f'http://newsapi.org/v2/everything?q={input}&sortBy=popularity&apiKey=fec0d23dd26549a9a6d58a29a675e764')
                
                pull = requests.get(source)
                articles = pull.json()["totalResults"]

                if articles == 0:
                    await ctx.send(f'{ctx.message.author.mention}: No results.')
                elif articles < 19:
                    randomId = random.randint(0,articles)
                else:
                    randomId = random.randint(0,19)
                    
                content = pull.json()["articles"][randomId]
                responseUrl = content["url"]
                if content:
                    await ctx.send(f'Result: {responseUrl}')
                else: 
                    await ctx.send(f'{ctx.message.author.mention}: No results.')

            except Exception as ex:
                logger.LogPrint(f'Couldn\'t get the news! - {ex}', logging.ERROR)


def setup(client):
    client.add_cog(cliffnet(client))