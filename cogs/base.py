import discord
from discord.ext import commands
from discord.ext.commands import BucketType

class Base(commands.Cog):

    def __init__(self, client):
        self.client = client    

    @commands.command()    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.send('Pong!')



def setup(client):
    client.add_cog(Base(client))