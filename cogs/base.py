import discord
from discord.ext import commands
from discord.ext.commands import BucketType

class Base(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):        
        print('Logged in as {}'.format(self.client.user))
        print('Connected to {} server(s).'.format(len(self.client.guilds)))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if(type(error) != discord.ext.commands.errors.CommandNotFound):
            print(f'**ERROR:** ``{error}``')
            ctx.send(f'**ERROR:** ``{error}``')    

    @commands.command()    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.send('Pong!')



def setup(client):
    client.add_cog(Base(client))