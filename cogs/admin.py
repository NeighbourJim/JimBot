import re
import discord
import logging
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.command_blacklist_manager import BLM
from internal.logs import logger
from internal.helpers import Helpers



class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client
        
    #region ---------------- Extension Loaders ----------------
    # Loads extensions
    @commands.command(help="Loads a command module.", hidden=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def load(self, ctx: discord.ext.commands.Context, extension: str):
        self.client.load_extension(f'cogs.{extension}')
        logger.LogPrint(f'Loaded extension {extension}')
        await ctx.reply(f'Loaded extension {extension}')

    # Unload extensions - Obviously!
    @commands.command(help="Unloads a command module.", hidden=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def unload(self, ctx: discord.ext.commands.Context, extension: str):
        self.client.unload_extension(f'cogs.{extension}')
        logger.LogPrint(f'Unloaded extension {extension}')
        await ctx.reply(f'Unloaded extension {extension}')

    # Reload a cog - Useful for working on cogs without having to restart the bot constantly
    @commands.command(help="Reloads a command module.", hidden=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def reload(self, ctx: discord.ext.commands.Context, extension: str):
        self.client.unload_extension(f'cogs.{extension}')
        self.client.load_extension(f'cogs.{extension}')
        logger.LogPrint(f'Reloaded extension {extension}')
        await ctx.reply(f'Reloaded extension {extension}')
    
    #endregion
    
    # Shuts down the bot
    @commands.command(aliases=["q"], help="Causes the bot to shut down. Owner command only.")
    @commands.is_owner()
    async def quit(self, ctx):
        logger.LogPrint(f'Bot forced to shut down via command.')
        await ctx.reply("Bot shutting down...")
        await self.client.close()

    # Toggle whether a command is blacklisted in the current channel
    @commands.command(aliases=["toggle"], help="Toggle whether a command is blacklisted in the current channel.", hidden=True)
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def togglecommand(self, ctx):
        command_to_toggle = Helpers.CommandStrip(self, ctx.message.content).lower().strip().split(' ')[0]
        if len(ctx.message.channel_mentions) > 0:
            channel = ctx.message.channel_mentions[0]
        else:
            channel = ctx.channel
        print(channel)
        valid_command = False
        for command in self.client.commands:
            if command.name.lower() == command_to_toggle:
                valid_command = True
        if valid_command:
            result = await BLM.ToggleCommandInChannelAsync(command_to_toggle, ctx.guild.id, channel.id)
            if result == True:
                await ctx.reply(f'Command `{command_to_toggle}` enabled in channel `{channel.name}`.')
            else:
                await ctx.reply(f'Command `{command_to_toggle}` disabled in channel `{channel.name}`.')
        else:
            await ctx.reply(f'The command `{command_to_toggle}` does not exist.')
        await ctx.message.delete()

    # Deletes a specified number of messages.
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
            msg = Helpers.CommandStrip(self, ctx.message.clean_content)
            print(msg)
            amount = Helpers.FuzzyIntegerSearch(self, msg)
            print(amount)
            if amount > 0 and amount <= 50:
                if len(mentions) == 0:
                    deleted = await ctx.channel.purge(limit=amount)
                    await ctx.reply(f'Deleted {len(deleted)} messages.')                    
                elif len(mentions) == 1:
                    deleted = await ctx.channel.purge(limit=amount, check=compare_users)                
                    await ctx.reply(f'Deleted {len(deleted)} messages.') 
                else:
                    await ctx.reply(f'Can only delete messages from 1 user at a time.')
            else:
                    await ctx.reply(f'Can only delete between 1 and 50 messages.')
        except Exception as ex:
            logger.LogPrint(f'ERROR - {ctx.command}:{ex}',logging.ERROR)  
            await ctx.reply(f'You didn\'t enter a number of messages.')      


def setup(client):
    client.add_cog(Admin(client))