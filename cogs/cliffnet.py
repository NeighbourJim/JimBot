import discord
import logging
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helper

class cliffnet(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def COMMAND(self, ctx):
        if ctx.guild.id == 107847342006226944:
            #
            #   COMMAND GOES HERE
            #
            await ctx.send("PONG")


def setup(client):
    client.add_cog(cliffnet(client))