import discord
import logging
import asyncio
import functools
from os import path

from internal.logs import logger
from internal.databasemanager import dbm
from internal.enums import WhereType, CompareType

import internal.configmanager as configmanager


class Blacklist_Manager():
    
    def __init__(self):
        self.current_settings = configmanager.cm.GetConfig()

    async def CheckAndCreateDatabaseAsync(self, db_filename, starting_table_name, columns):
        """Check if a database has been made, and create it if not.
        """
        try:
            loop = asyncio.get_event_loop()
            db_exists = await loop.run_in_executor(None, path.exists, f'./internal/data/databases/{db_filename}.db')
            if not db_exists:
                await loop.run_in_executor(None, functools.partial(dbm.CreateTable, db_filename, starting_table_name, columns))
            return True

        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not create {db_filename}: {ex}',logging.ERROR)     
            return False

    async def CheckIfCommandAllowed(self, ctx):
        if ctx.message.author.id == self.current_settings["settings"]["owner"]:
            return True
        await self.CheckAndCreateDatabaseAsync(f'blacklist-{ctx.guild.id}', 'blacklist', {"channel_id": "integer NOT NULL", "command_name": "text NOT NULL"})
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, functools.partial(dbm.Retrieve, db_name=f'blacklist-{ctx.guild.id}', table_name='blacklist', where=[("channel_id", f"{ctx.message.channel.id}"),("command_name", f"{ctx.command.name.lower()}")]))
        if len(results) > 0:
            return False
        else:
            return True

    async def AddCommandToBlacklistAsync(self, command_name, guild_id, channel_id):
        await self.CheckAndCreateDatabaseAsync(f'blacklist-{guild_id}', 'blacklist', {"channel_id": "integer NOT NULL", "command_name": "text NOT NULL"})
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(dbm.Insert, f'blacklist-{guild_id}', 'blacklist', {"channel_id": channel_id, "command_name": command_name}))

    async def DeleteCommandFromBlacklistAsync(self, command_name, guild_id, channel_id):
        await self.CheckAndCreateDatabaseAsync(f'blacklist-{guild_id}', 'blacklist', {"channel_id": "integer NOT NULL", "command_name": "text NOT NULL"})
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(dbm.Delete, f'blacklist-{guild_id}', 'blacklist', {"channel_id": channel_id, "command_name": command_name}))

    async def ToggleCommandInChannelAsync(self, command_name, guild_id, channel_id):
        """Toggles a command's blacklist state - Adds it to blacklist if it isn't in there, or removes it if it is.

        Args:
            command_name (str): The name of the command to toggle.
            guild_id (int): The Discord Guild ID where the command was executed
            channel_id (int): The Discord Channel ID where the command was executed

        Returns:
            bool: True if the command was removed from the blacklist, False if it was added.
        """
        await self.CheckAndCreateDatabaseAsync(f'blacklist-{guild_id}', 'blacklist', {"channel_id": "integer NOT NULL", "command_name": "text NOT NULL"})
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, functools.partial(dbm.Retrieve, db_name=f'blacklist-{guild_id}', table_name='blacklist', where=[("channel_id", f"{channel_id}"),("command_name", f"{command_name}")], where_type=WhereType.AND))
        if len(results) > 0:
            await self.DeleteCommandFromBlacklistAsync(command_name, guild_id, channel_id)
            return True
        else:
            await self.AddCommandToBlacklistAsync(command_name, guild_id, channel_id)
            return False
        

BLM = Blacklist_Manager()