import io
import sqlite3
import discord
import logging
from discord.ext import commands
from discord.ext.commands import BucketType
from os import path

from internal.logs import logger
from internal.helpers import Helper
from internal.enums import WhereType
from internal.databasemanager import dbm
from internal.data.meme_views import meme_views

class Memes(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db_folder = "./internal/data/databases/"
        self.last_meme_roll = None

    def CheckAndCreateDatabase(self):
        try:
            guilds = self.client.guilds
            for g in guilds:
                filename = f"memes{g.id}"
                if not path.exists(f'{self.db_folder}{filename}.db'):
                    # Create the required tables
                    columns = {"id": "integer PRIMARY KEY AUTOINCREMENT", "meme": "text NOT NULL", "score": "integer NOT NULL", "author_username": "varchar(255) NOT NULL", "author_nickname": "varchar(255) NOT NULL", "date_added": "text NOT NULL"}
                    dbm.CreateTable(filename, "memes", columns)
                    columns = {"m_id": "integer NOT NULL", "author_id": "varchar(255) NOT NULL", "author_username": "varchar(255)"}
                    dbm.CreateTable(filename, "downvotes", columns)
                    dbm.CreateTable(filename, "upvotes", columns)

                    # Create the required views
                    for view in meme_views:
                        dbm.ExecuteRawQuery(filename, view)
                    
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not create table or view: {ex}',logging.ERROR)                

    @commands.command(help="Get a meme.", aliases=["m", "M"])
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def meme(self, ctx):
        try:
            message = Helper.CommandStrip(ctx.message.content)
            values_to_find = []
            if len(message) > 0:
                split_message = message.split(',')
                for name in split_message:
                    member = ctx.guild.get_member_named(name)
                    if member is not None:
                        t = ("author_id", f'<@{member.id}>')
                    else:
                        t = ("author_username", name)
                    values_to_find.append(t)
            if len(values_to_find) != 0:
                meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_meme_all", values_to_find, WhereType.OR)
            else:
                meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_meme_all", None)
            if meme is not None:
                print(f'FUCK {meme}')
                self.last_meme_roll = meme[0][0]
                await ctx.send(f'{ctx.message.author.mention}: **ID:{meme[0][0]}**\n {meme[0][1]}')
            else:
                self.last_meme_roll = None
                await ctx.send((f'{ctx.message.author.mention}: No memes found.'))
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute meme command: {ex}',logging.ERROR)             



    @commands.command(hidden=True)    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def TESTDB(self, ctx):
        columns = {"id": "integer PRIMARY KEY AUTOINCREMENT", "name": "text", "number": "integer", "some_other_value": "varchar(255)"}
        data = {"name": "john scum", "number": 55, "some_other_value": "cock and ball torture"}
        dbm.CreateTable("test", "test_table", columns)
        dbm.Insert("test","test_table", data)

        ud = {"name": "jane scum", "number": 69}
        uw = {"id": 1}
        dbm.Update("test","test_table",ud,uw)

        data = {"name": "fucker", "number": 69, "some_other_value": "cock and ball torture"}
        dbm.Insert("test", "test_table", data)
        dw = {"name": "fucker"}
        dbm.Delete("test", "test_table", dw)

        rw = {"id": 1}
        r = dbm.Retrieve("test", "test_table", rw)
        print(r)

        rw = {"id": 1}
        r = dbm.Retrieve("test", "test_table", rw, ["name", "number"])
        print(r)



def setup(client):
    client.add_cog(Memes(client))