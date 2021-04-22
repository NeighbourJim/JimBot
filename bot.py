import sys
import random
import os
import logging
import discord
from cleverwrap import CleverWrap
from discord.ext import commands


#region Internal Imports
from internal.helpers import Helpers
from internal.logs import logger
import internal.configmanager as configmanager
#endregion

# Start the logger, load the current settings, create the client
logger.StartLogging()
current_settings = configmanager.cm.GetConfig()
cw = CleverWrap(f'{current_settings["keys"]["cleverbot_key"]}')
convo = cw.new_conversation()
hitroll = 2000
intents = discord.Intents(messages=True, guilds=True, members=True, bans=True, emojis=True, reactions=True, typing=True, presences=True)

client = commands.Bot(
    command_prefix = current_settings["settings"]["prefix"], 
    owner_id = current_settings["settings"]["owner"],
    help_command=discord.ext.commands.DefaultHelpCommand(dm_help=True),
    allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True),
    intents=intents)


#region ---------------- Event Listeners ----------------
@client.event
async def on_ready():        
    logger.LogPrint(f'Logged in as {client.user}')
    logger.LogPrint(f'Connected to {len(client.guilds)} server(s).')


@client.event
async def on_command_error(ctx, error):
    # Ignore CommandNotFound error, as it fires every time any message beginning with the prefix is posted
    # Otherwise, post the error message to the chat and log it, then restart the bot.
    if type(error) == discord.ext.commands.errors.CommandNotFound:
        return 
    if type(error) == discord.ext.commands.errors.CheckFailure:
        return

    to_delete = ctx.message    
    await ctx.reply(content=f'**ERROR:** `{error}`', delete_after=6.0)
    await to_delete.delete(delay=7)

    if type(error) == discord.ext.commands.errors.CommandOnCooldown or type(error) == discord.ext.commands.errors.MissingRole:
        return

@client.event
async def on_command_completion(ctx):
    # Log Command evocations to the console at INFO level
    logger.LogPrint(f'Executing command {ctx.command.name} for user {ctx.message.author}', logging.INFO)

@client.event
async def on_message(ctx):
    global hitroll
    if ctx.guild.id == 107847342006226944 and ctx.author.bot == False and not ctx.content.startswith(current_settings["settings"]["prefix"]):
        if 'chatbot' in ctx.content.lower() or random.randint(0,hitroll) == hitroll:
            await ctx.channel.trigger_typing()            
            if len(ctx.content) > 0:
                truemessage = ctx.content
                if truemessage.lower().startswith('chatbot'):
                    truemessage = truemessage.replace("chatbot", " ")
                    truemessage = truemessage.replace("Chatbot", " ")
                response = convo.say(truemessage)
                hitroll = 2000
                await ctx.reply(content=f'`{response}`', mention_author=False)
    hitroll -= 1
    if hitroll <1:
        hitroll = 1
    await client.process_commands(ctx)
    

#@client.event
#async def on_error(ctx, error):
#    logger.LogPrint(f'!!!ERROR!!!: {error}',logging.ERROR, sys.exc_info())
#endregion

# Load the Cog files from ./cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Loaded cog: {filename}')

client.run(current_settings["bot"]["token"])
