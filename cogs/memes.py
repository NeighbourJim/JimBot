import io
import sqlite3
import discord
import logging
from discord.ext import commands
from discord.ext.commands import BucketType
from os import path

from internal.logs import logger
from internal.databasemanager import dbm
from internal.data.meme_views import *

class Memes(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db_folder = "./internal/data/databases/"

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
                    dbm.ExecuteRawQuery(filename, view_b_five)
                    dbm.ExecuteRawQuery(filename, view_b_five_ab_ten)
                    dbm.ExecuteRawQuery(filename, view_get_meme_num)
                    dbm.ExecuteRawQuery(filename, view_random_meme)
                    dbm.ExecuteRawQuery(filename, view_random_new_meme)
                    dbm.ExecuteRawQuery(filename, view_random_unrated)
                    dbm.ExecuteRawQuery(filename, view_t_five)
                    dbm.ExecuteRawQuery(filename, view_t_five_above_ten)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not create table or view: {ex}',logging.ERROR)                

    @commands.command(help="Get a meme.", aliases=["m", "M"])
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def meme(self, ctx):
        meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_meme")
        await ctx.send(f'{ctx.message.author.mention}: **ID:{meme[0][1]}**\n {meme[0][2]}')


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