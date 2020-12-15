import discord
import logging
from discord.ext import commands
from discord.ext.commands import BucketType
from os import path

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from internal.enums import WhereType
from internal.databasemanager import dbm

class Tags(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db_folder = "./internal/data/databases/"

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)
        
    def CheckAndCreateDatabase(self, ctx):
        try:
            filename = f"tags{ctx.guild.id}"
            if not path.exists(f'{self.db_folder}{filename}.db'):
                # Create the required tables
                columns = {"tag_name": "text PRIMARY KEY", "tag_content": "text NOT NULL", "author_id": "integer NOT NULL"}
                dbm.CreateTable(filename, "tags", columns)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t create database: {ex}',logging.ERROR)

    @commands.command(help="Get a tag specified by name.", aliases=["t", "T", "Tag"])    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def tag(self, ctx):
        try:
            self.CheckAndCreateDatabase(ctx)

            to_delete = ctx.message
            where = ("tag_name", Helpers.CommandStrip(self, ctx.message.content))
            tag = dbm.Retrieve(f"tags{ctx.guild.id}", "tags", [where])
            if len(tag) > 0:
                await ctx.send(f'{ctx.message.author.mention}: Tag - {Helpers.CommandStrip(self, ctx.message.content)}\n{tag[0][1]}')
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No tag with that name.', delete_after=6)
            await to_delete.delete(delay=3)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute tag command: {ex}',logging.ERROR)

    @commands.command(help="Create a tag.", aliases=["ct", "CT", "Ct", "Createtag", "addtag"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def createtag(self, ctx):
        try:
            self.CheckAndCreateDatabase(ctx)

            to_delete = ctx.message
            split_message = Helpers.CommandStrip(self, ctx.message.content).split(' ')
            if len(split_message) > 1 and len(split_message) < 400:
                tag_name = split_message[0]
                tag_content = ' '.join(split_message[1:])
                where = ("tag_name", tag_name)
                existing = dbm.Retrieve(f"tags{ctx.guild.id}", "tags", [where])
                if len(existing) == 0:
                    new_tag = {"tag_name": tag_name, "tag_content": tag_content, "author_id": ctx.message.author.id}
                    if dbm.Insert(f"tags{ctx.guild.id}", "tags", new_tag):
                        await ctx.send(f'{ctx.message.author.mention}: Created tag \'{tag_name}\'.')
                else:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: That tag already exists.', delete_after=5)
            else:
                await ctx.send(f'{ctx.message.author.mention}: Tag too long or too short.')
            await to_delete.delete(delay=5)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t create tag: {ex}',logging.ERROR)

    @commands.command(help="Delete a tag.", aliases=["removetag"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def deletetag(self, ctx):
        try:
            self.CheckAndCreateDatabase(ctx)

            to_delete = ctx.message
            tag_name = Helpers.CommandStrip(self, ctx.message.content)
            where = ("tag_name", tag_name)
            where_dict = {"tag_name": tag_name}
            existing = dbm.Retrieve(f"tags{ctx.guild.id}", "tags", [where])
            if len(existing) > 0:
                user_is_admin = ctx.message.author.permissions_in(ctx.message.channel).administrator
                if user_is_admin or ctx.message.author.id == existing[0][2]:
                    if dbm.Delete(f"tags{ctx.guild.id}", "tags", where_dict) > 0:
                        await ctx.send(f'{ctx.message.author.mention}: Tag \'{tag_name}\' deleted.')
                else:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: You do not have permissions to delete that tag.\nYou must either be an Administrator or the original tag creator.', delete_after=5)
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: That tag does not exist.', delete_after=5)
            await to_delete.delete(delay=5)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t delete tag: {ex}',logging.ERROR)

    @commands.command(help="Get a list of all tags.", aliases=["tl"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def taglist(self, ctx):
        try:
            self.CheckAndCreateDatabase(ctx)

            filename = f"{self.db_folder}taglist-{ctx.guild.id}.txt"
            tags = dbm.Retrieve(f"tags{ctx.guild.id}", "tags", rows_required=100000, order_by=("tag_name", "asc"))
            if len(tags) > 0:
                tag_details_list = []
                for tag in tags:                    
                    tag_details_list.append(f"Tag Name: {tag[0]}\nAuthor ID: <@{tag[2]}>\nContent: {tag[1]}")
                with open(filename, 'w', encoding="utf-8") as list_file:
                    for item in tag_details_list:
                        list_file.write('%s\n\n' % item)
                with open(f'{self.db_folder}taglist-{ctx.guild.id}.txt', 'rb') as fp:
                    await ctx.send(f'{ctx.message.author.mention}', file=discord.File(fp, f'taglist-{ctx.guild.id}.txt'))
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No tags in the database.', delete_after=5)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t get tag list: {ex}',logging.ERROR)


def setup(client):
    client.add_cog(Tags(client))