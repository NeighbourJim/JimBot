import discord
import logging
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helper

class cliffnet(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def is_neverchat(ctx):
        return ctx.guild.id == 107847342006226944

    @commands.command()    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    @commands.check(is_neverchat)
    async def COMMAND(self, ctx):
        await ctx.send('Pong!')



def setup(client):
    client.add_cog(cliffnet(client))