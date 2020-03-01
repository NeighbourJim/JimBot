import re
import discord
import logging
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helper


class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client
        
    #region ---------------- Extension Loaders ----------------
    # Loads extensions
    @commands.command(help="Loads a command module.", hidden=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def load(self, ctx, extension):
        self.client.load_extension(f'cogs.{extension}')
        logger.LogPrint(f'Loaded extension {extension}')
        await ctx.send(f'Loaded extension {extension}')

    # Unload extensions - Obviously!
    @commands.command(help="Unloads a command module.", hidden=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def unload(self, ctx, extension):
        self.client.unload_extension(f'cogs.{extension}')
        logger.LogPrint(f'Unloaded extension {extension}')
        await ctx.send(f'Unloaded extension {extension}')

    # Reload a cog - Useful for working on cogs without having to restart the bot constantly
    @commands.command(help="Reloads a command module.", hidden=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def reload(self, ctx, extension):
        self.client.unload_extension(f'cogs.{extension}')
        self.client.load_extension(f'cogs.{extension}')
        logger.LogPrint(f'Reloaded extension {extension}')
        await ctx.send(f'Reloaded extension {extension}')
    
    #endregion
    
    @commands.command(aliases=["q"], help="Causes the bot to shut down. Owner command only.")
    @commands.is_owner()
    async def quit(self, ctx):
        logger.LogPrint(f'Bot forced to shut down via command.')
        await ctx.send("Bot shutting down...")
        await self.client.close()

    @commands.command(help="Deletes a specified number of messages from the channel.\nCan be used to target only one specific user.\nUsage: !purge 5 / !purge @user 5")
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx):
        mentions = ctx.message.mentions
        def compare_users(message):
            return message.author == mentions[0]
        try:            
            # Get the amount by using regex to strip all mentions out 
            msg = Helper.CommandStrip(ctx.message.clean_content)
            print(msg)
            amount = Helper.FuzzyNumberSearch(msg)
            print(amount)
            if amount > 0 and amount <= 50:
                if len(mentions) == 0:
                    deleted = await ctx.channel.purge(limit=amount)
                    await ctx.send(f'{ctx.message.author.mention}: Deleted {len(deleted)} messages.')                    
                elif len(mentions) == 1:
                    deleted = await ctx.channel.purge(limit=amount, check=compare_users)                
                    await ctx.send(f'{ctx.message.author.mention}: Deleted {len(deleted)} messages.') 
                else:
                    await ctx.send(f'{ctx.message.author.mention}: Can only delete messages from 1 user at a time.')
            else:
                    await ctx.send(f'{ctx.message.author.mention}: Can only delete between 1 and 50 messages.')
        except Exception as ex:
            logger.LogPrint(f'ERROR - {ctx.command}:{ex}',logging.ERROR)  
            await ctx.send(f'{ctx.message.author.mention}: You didn\'t enter a number of messages.')      


def setup(client):
    client.add_cog(Admin(client))