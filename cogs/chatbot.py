import discord
import logging
import os.path
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from bot import current_settings
from bot import convo


class Chatbot(commands.Cog):    

    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        if ctx.guild.id == 107847342006226944:
            return BLM.CheckIfCommandAllowed(ctx)
        return False

    @commands.command(aliases=["cb", "chatbot", "Chatbot"], help="Talk to Chatbot.")    
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def cleverbot(self, ctx):
        await ctx.trigger_typing()
        msg = Helpers.CommandStrip(self,ctx.message.content)
        if len(msg) > 1:
            response = convo.say(msg)
        else:
            response = f'You didn\'t enter a message.'
        await ctx.reply(f'`{response}`')

    @commands.command(aliases=["cbreset", "chatbotreset", "Chatbotreset"], help="Talk to Chatbot.")    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def cleverbotreset(self, ctx):
        convo.reset()
        await ctx.reply(f'Conversation reset.')


def setup(client):
    client.add_cog(Chatbot(client))