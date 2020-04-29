import discord
import logging
import random
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

#hi knite! this is a change 
    @commands.command(aliases=["Thing", "t"], help="scrambles word order")  
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def command2(self, ctx):
        if ctx.guild.id == 107847342006226944:
            #different stuff

def setup(client):
    client.add_cog(cliffnet(client))