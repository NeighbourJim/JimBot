import os
import discord
from discord.ext import commands

#region Internal Imports
import internal.logs as logs
import internal.configmanager as configmanager
#endregion

# Start the logger, load the current settings, create the client
logs.logger.StartLogging()
current_settings = configmanager.cm.GetConfig()
client = commands.Bot(
    command_prefix = current_settings["settings"]["prefix"], 
    owner_id = current_settings["settings"]["owner"])

#region ---------------- Event Listeners ----------------
@client.event
async def on_ready():        
    print('Logged in as {}'.format(client.user))
    print('Connected to {} server(s).'.format(len(client.guilds)))

@client.event
async def on_command_error(ctx, error):
    if type(error) == discord.ext.commands.errors.CommandOnCooldown:
        await ctx.send(content=f'{ctx.message.author.mention}: **ERROR:** ``{error}``', delete_after=5.0)

@client.event
async def on_error(ctx, error):
    print(error)
#endregion

# Load the Cog files from ./cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Loaded cog: {filename}')

client.run(current_settings["bot"]["token"])
