import sys
import os
import logging
import discord
from discord.ext import commands


#region Internal Imports
from internal.helpers import Helper
from internal.logs import logger
import internal.configmanager as configmanager
#endregion

# Start the logger, load the current settings, create the client
logger.StartLogging()
current_settings = configmanager.cm.GetConfig()
client = commands.Bot(
    command_prefix = current_settings["settings"]["prefix"], 
    owner_id = current_settings["settings"]["owner"])

#region ---------------- Event Listeners ----------------
@client.event
async def on_ready():        
    logger.LogPrint('Logged in as {}'.format(client.user))
    logger.LogPrint('Connected to {} server(s).'.format(len(client.guilds)))

@client.event
async def on_command_error(ctx, error):
    if type(error) != discord.ext.commands.errors.CommandNotFound:
        to_delete = ctx.message    
        await ctx.send(content=f'{ctx.message.author.mention}: **ERROR:** ``{error}``', delete_after=6.0)
        await to_delete.delete(delay=5)
        if type(error) != discord.ext.commands.errors.CommandOnCooldown and type(error) != discord.ext.commands.errors.MissingRole:
            logger.LogPrint(f'!!!ERROR!!!: CMD:{ctx.command.name} ERR:{error}', logging.ERROR)

@client.event
async def on_command(ctx):
    logger.LogPrint(f'Executing command {ctx.command.name} for user {ctx.message.author}')

@client.event
async def on_error(ctx, error):
    logger.LogPrint(f'!!!ERROR!!!:',logging.ERROR, sys.exc_info())
#endregion

# Load the Cog files from ./cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Loaded cog: {filename}')

client.run(current_settings["bot"]["token"])
