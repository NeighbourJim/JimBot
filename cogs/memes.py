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

    def GetMemeScore(self, ctx, m_id):
        try: 
            return self.GetUpvoteCount(ctx, m_id) - self.GetDownvoteCount(ctx, m_id)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not get meme score: {ex}',logging.ERROR)  

    def GetUpvoteCount(self, ctx, m_id):
        try:
            ups = dbm.ExecuteRawQuery(f'memes{ctx.guild.id}',f'SELECT COUNT(DISTINCT author_id) as C FROM upvotes WHERE m_id = {m_id}')
            return ups[0]
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not get meme upvote count: {ex}',logging.ERROR) 

    def GetDownvoteCount(self, ctx, m_id):
        try:
            downs = dbm.ExecuteRawQuery(f'memes{ctx.guild.id}',f'SELECT COUNT(DISTINCT author_id) as C FROM downvotes WHERE m_id = {m_id}')
            return downs[0]
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not get meme downvote count: {ex}',logging.ERROR) 

    def GetGradeSmallServer(self, score):
        if score >= 10:
            return "https://i.imgur.com/UfxLyJd.png"
        elif score >= 7:
            return "https://i.imgur.com/yTorwDL.png"
        elif score >= 5:
            return "https://i.imgur.com/BKkfn06.png"
        elif score >= 3:
            return "https://i.imgur.com/8EygCxU.png"
        elif score >= 1:
            return "https://i.imgur.com/4UNoKdG.png"
        elif score == 0:
            return "https://i.imgur.com/czp3Bt8.png"
        elif score < 0 and score >= -2:
            return "https://i.imgur.com/xLflJAw.png"
        elif score < -2 and score >= -5:
            return "https://cdn.discordapp.com/attachments/131374467476750336/680053237549891609/emote.png"
        elif score <= -10:
            return "https://cdn.discordapp.com/attachments/131374467476750336/680038565404868661/winkvomit.png"
        else:
            return "https://cdn.discordapp.com/attachments/131374467476750336/680053237549891609/emote.png"

    def GetGradeLargeServer(self, score):
        if score >= 25:
            return "https://i.imgur.com/UfxLyJd.png"
        elif score >= 20:
            return "https://i.imgur.com/yTorwDL.png"
        elif score >= 15:
            return "https://i.imgur.com/BKkfn06.png"
        elif score >= 10:
            return "https://i.imgur.com/8EygCxU.png"
        elif score == 7:
            return "https://cdn.discordapp.com/attachments/131374467476750336/680037715659849756/emote.png"
        elif score >= 5:
            return "https://i.imgur.com/4UNoKdG.png"
        elif score > 0:
            return "https://i.imgur.com/czp3Bt8.png"
        elif score == 0:
            return "https://cdn.discordapp.com/attachments/355351184514744320/680042617257721869/emote.png"
        elif score < 0 and score >= -5:
            return "https://cdn.discordapp.com/attachments/131374467476750336/680038225443946496/emote.png"
        elif score < -5 and score >= -10:
            return "https://cdn.discordapp.com/attachments/131374467476750336/680038639257911307/emote.png"
        elif score < -20:
            return "https://cdn.discordapp.com/attachments/131374467476750336/680053237549891609/emote.png"
        else:
            return "https://cdn.discordapp.com/attachments/131374467476750336/680036401613635610/emote.png"

    def GetGradeUrl(self, ctx, score):
        if len(ctx.guild.members) > 75:
            return self.GetGradeLargeServer(score)
        else:
            return self.GetGradeSmallServer(score)
        

    @commands.command(help="Get a meme.", aliases=["m", "M"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.guild_only()
    async def meme(self, ctx):
        try:
            to_delete = ctx.message
            message = Helper.CommandStrip(ctx.message.content)
            values_to_find = []
            if len(message) > 0:
                if Helper.FuzzyNumberSearch(message):
                    t = ("m_id", int(Helper.FuzzyNumberSearch(message)))
                    values_to_find.append(t)
                else:
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
            if len(meme) > 0:
                self.last_meme_roll = meme[0][0]
                await ctx.send(f'{ctx.message.author.mention}: **ID:{meme[0][0]}**\n {meme[0][1]}')
                await to_delete.delete()
            else:
                await ctx.send((f'{ctx.message.author.mention}: No memes found.'))
                await to_delete.delete()
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute meme command: {ex}',logging.ERROR)             

    @commands.command(help="Get a meme added within the last 30 days.", aliases=["nm", "NM", "Nm"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.guild_only()
    async def newmeme(self, ctx):
        try:
            to_delete = ctx.message
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
                meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_meme_all_new", values_to_find, WhereType.OR)
            else:
                meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_meme_all_new", None)
            if len(meme) > 0:
                self.last_meme_roll = meme[0][0]
                await ctx.send(f'{ctx.message.author.mention}: **ID:{meme[0][0]}**\n {meme[0][1]}')
                await to_delete.delete()
            else:
                await ctx.send((f'{ctx.message.author.mention}: No memes found that were added in the last 30 days.'))
                await to_delete.delete()
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute meme command: {ex}',logging.ERROR)     

    @commands.command(help="Get a meme that has not yet been voted on.", aliases=["ur", "UR", "Ur"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.guild_only()
    async def unratedmeme(self, ctx):
        try:
            to_delete = ctx.message
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
                meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_unrated_all", values_to_find, WhereType.OR)
            else:
                meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_unrated_all", None)
            if len(meme) > 0:
                self.last_meme_roll = meme[0][0]
                await ctx.send(f'{ctx.message.author.mention}: **ID:{meme[0][0]}**\n {meme[0][1]}')
                await to_delete.delete()
            else:
                await ctx.send(f'{ctx.message.author.mention}: No unrated memes found.')
                await to_delete.delete()
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute meme command: {ex}',logging.ERROR)     

    @commands.command(help="Rate a meme as good.", aliases=["gm", "GM", "Gm", "Godmersham"])
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.guild_only()
    async def goodmeme(self, ctx):
        m_id = None
        values_to_find = []
        try:
            to_delete = ctx.message
            message = Helper.CommandStrip(ctx.message.content)
            m_id = self.last_meme_roll
            if len(message) > 0 and Helper.FuzzyNumberSearch(message) is not None:
                m_id = int(Helper.FuzzyNumberSearch(message))
            t = ("m_id", m_id)
            values_to_find.append(t)
            meme = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', values_to_find)
            if len(meme) > 0:
                vote = dbm.Retrieve(f'memes{ctx.guild.id}', 'upvotes', [("author_id", f'<@{ctx.message.author.id}>'), ("m_id", m_id)])
                if len(vote) == 0:
                    d = {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>', "author_username": ctx.message.author.name}
                    dbm.Insert(f'memes{ctx.guild.id}', "upvotes", d)
                    dbm.Delete(f'memes{ctx.guild.id}', "downvotes", {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>'})
                    await ctx.send(f'{ctx.message.author.mention}: :arrow_up: **{self.GetMemeScore(ctx, m_id)}**')
                    await to_delete.delete()
                else:
                    await ctx.send(f'{ctx.message.author.mention}: You already upvoted that meme.')
                    await to_delete.delete()
            else:
                await ctx.send(f'{ctx.message.author.mention}: No meme to vote on. Either you specified a meme ID that doesn\'t exist or no meme was rolled since the last bot restart.')
                await to_delete.delete()

        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute goodmeme command: {ex}', logging.ERROR)

    @commands.command(help="Rate a meme as bad.", aliases=["bm", "BM", "Bm"])
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.guild_only()
    async def badmeme(self, ctx):
        m_id = None
        values_to_find = []
        try:
            to_delete = ctx.message
            message = Helper.CommandStrip(ctx.message.content)
            m_id = self.last_meme_roll
            if len(message) > 0 and Helper.FuzzyNumberSearch(message) is not None:
                m_id = int(Helper.FuzzyNumberSearch(message))
            t = ("m_id", m_id)
            values_to_find.append(t)
            meme = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', values_to_find)
            if len(meme) > 0:
                vote = dbm.Retrieve(f'memes{ctx.guild.id}', 'downvotes', [("author_id", f'<@{ctx.message.author.id}>'), ("m_id", m_id)])
                if len(vote) == 0:
                    d = {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>', "author_username": ctx.message.author.name}
                    dbm.Insert(f'memes{ctx.guild.id}', "downvotes", d)
                    dbm.Delete(f'memes{ctx.guild.id}', "upvotes", {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>'})
                    await ctx.send(f'{ctx.message.author.mention}: :arrow_down: **{self.GetMemeScore(ctx, m_id)}**')
                    await to_delete.delete()
                else:
                    await ctx.send(f'{ctx.message.author.mention}: You already downvoted that meme.')
                    await to_delete.delete()
            else:
                await ctx.send(f'{ctx.message.author.mention}: No meme to vote on.\nEither you specified a meme ID that doesn\'t exist or no meme was rolled since the last bot restart.')
                await to_delete.delete()

        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute goodmeme command: {ex}', logging.ERROR)

    @commands.command(help="Get a meme's information.", aliases=["mi", "MI", "Mi"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.guild_only()
    async def memeinfo(self, ctx):
        m_id = None
        values_to_find = []
        try:
            to_delete = ctx.message
            message = Helper.CommandStrip(ctx.message.content)
            m_id = self.last_meme_roll
            if len(message) > 0 and Helper.FuzzyNumberSearch(message) is not None:
                m_id = int(Helper.FuzzyNumberSearch(message))
            t = ("m_id", m_id)
            values_to_find.append(t)
            meme = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', values_to_find)
            if len(meme) > 0:
                fields = []
                fields.append({"name": f'Requested by {ctx.message.author.display_name}', "value": f'Created by {meme[0][3]} on {meme[0][6]}\nScore: **{meme[0][2]}** (+{self.GetUpvoteCount(ctx, m_id)} / -{self.GetDownvoteCount(ctx, m_id)})', "inline": False})
                meme_dict = {
                    "author": {"name": f'Meme #{m_id} Info'},
                    "fields": fields,
                    "thumbnail": {"url": f'{self.GetGradeUrl(ctx, meme[0][2])}'} 
                }
                result_embed = discord.Embed.from_dict(meme_dict)
                await ctx.send(embed=result_embed)
                await to_delete.delete()
            else:
                await ctx.send(f'{ctx.message.author.mention}: No meme info to get.\nEither you specified a meme ID that doesn\'t exist or no meme was rolled since the last bot restart.')
                await to_delete.delete()
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute memeinfo command: {ex}', logging.ERROR)
    
    @commands.command(hidden=True)    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def TESTDB(self, ctx):
        print()
        



def setup(client):
    client.add_cog(Memes(client))