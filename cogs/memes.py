import io
import sqlite3
import random
import discord
import logging
from discord.ext import commands
from discord.ext.commands import BucketType
from os import path
from datetime import datetime

from internal.logs import logger
from internal.helpers import Helpers
from internal.enums import WhereType, CompareType
from internal.databasemanager import dbm
from internal.data.meme_views import meme_views

class Memes(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db_folder = "./internal/data/databases/"
        self.last_meme_roll = {}
        self.CheckAndCreateDatabase()

#region Non-Command Methods - General Helpers Methods specific to this cog
    def CheckAndCreateDatabase(self):
        """Check if a meme database has been made for each server the bot is connected to, and create it if not.
        """
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
        """Get the score of a specific meme. Calls GetUpvoteCount() and GetDownvoteCount().

        Args:
            ctx (discord.ext.commands.context): Context in which to search. Should be the context of the evocation message.
            m_id (int): The meme ID to look up.

        Returns:
            int: The score of the meme. Calculated by subtracting upvotes from downvotes.
        """
        try: 
            return self.GetUpvoteCount(ctx, m_id) - self.GetDownvoteCount(ctx, m_id)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not get meme score: {ex}',logging.ERROR)  

    def GetUpvoteCount(self, ctx, m_id):
        """Get the total number of 'goodmeme' votes for a given meme.

        Args:
            ctx (discord.ext.commands.context): Context in which to search. Should be the context of the evocation message.
            m_id (int): The meme ID to look up.

        Returns:
            int: The number of upvotes on requested meme.
        """
        try:
            ups = dbm.ExecuteRawQuery(f'memes{ctx.guild.id}',f'SELECT COUNT(DISTINCT author_id) as C FROM upvotes WHERE m_id = {m_id}')
            return ups[0]
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not get meme upvote count: {ex}',logging.ERROR) 

    def GetDownvoteCount(self, ctx, m_id):
        """Get the total number of 'badmeme' votes for a given meme.

        Args:
            ctx (discord.ext.commands.context): Context in which to search. Should be the context of the evocation message.
            m_id (int): The meme ID to look up.

        Returns:
            int: The number of downvotes on requested meme.
        """
        try:
            downs = dbm.ExecuteRawQuery(f'memes{ctx.guild.id}',f'SELECT COUNT(DISTINCT author_id) as C FROM downvotes WHERE m_id = {m_id}')
            return downs[0]
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not get meme downvote count: {ex}',logging.ERROR) 

    def GetVoters(self, ctx, m_id):
        """Get all of the votes for a meme, both good and bad.

        Args:
            ctx (discord.ext.commands.context): Context in which to search. Should be the context of the evocation message.
            m_id (int): The meme ID to look up.

        Returns:
            dict: Dictionary with 2 keys. dict["ups"] holds a list of upvotes. dict["downs"] holds a list of downvotes.
        """
        try:
            w = [("m_id", m_id)]
            ups = dbm.Retrieve(f'memes{ctx.guild.id}', 'upvotes', w, WhereType.AND, ["author_id", "author_username"], 10000)
            downs = dbm.Retrieve(f'memes{ctx.guild.id}', 'downvotes', w, WhereType.AND, ["author_id", "author_username"], 10000)
            return {"ups": ups, "downs": downs}
        except Exception as ex:
            logger.LogPrint(f'ERROR: Could not get meme votes. - {ex}', logging.ERROR)

    def GetGradeSmallServer(self, score):
        """Get the Grade image for a given score for a smaller server.

        Args:
            score (int): Score to get Grade for.

        Returns:
            str: URL of appropriate Grade image.
        """
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
        """Get the Grade image for a given score for a larger server.

        Args:
            score (int): Score to get Grade for.

        Returns:
            str: URL of appropriate Grade image.
        """
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

#endregion

    @commands.command(help="Get a meme.", aliases=["m", "M"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def meme(self, ctx):
        try:
            to_delete = ctx.message
            message = Helpers.CommandStrip(self, ctx.message.content)
            values_to_find = []
            if len(message) > 0:
                split_message = message.split(',')
                for name in split_message:
                    member = ctx.guild.get_member_named(name)
                    if member is not None:
                        t = ("author_id", f'<@{member.id}>')
                    else:
                        if Helpers.FuzzyNumberSearch(self, message):
                            t = ("m_id", int(Helpers.FuzzyNumberSearch(self, message)))
                        else:
                            t = ("author_username", name)
                    values_to_find.append(t)
            if len(values_to_find) != 0:
                meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_meme_all", values_to_find, WhereType.OR, ["*"], 1, CompareType.LIKE)
            else:
                meme = dbm.Retrieve(f'memes{ctx.guild.id}', "random_meme_all")
            if len(meme) > 0:
                self.last_meme_roll[f"{ctx.guild.id}"] = meme[0][0]
                await ctx.send(f'{ctx.message.author.mention}: **ID:{meme[0][0]}**\n {meme[0][1]}')
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No memes found.', delete_after=10)
            await to_delete.delete(delay=6)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute meme command: {ex}',logging.ERROR)             

    @commands.command(help="Get a meme added within the last 30 days.", aliases=["nm", "NM", "Nm"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def newmeme(self, ctx):
        try:
            to_delete = ctx.message
            message = Helpers.CommandStrip(self, ctx.message.content)
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
                self.last_meme_roll[f"{ctx.guild.id}"] = meme[0][0]
                await ctx.send(f'{ctx.message.author.mention}: **ID:{meme[0][0]}**\n {meme[0][1]}')
                await to_delete.delete(delay=3)
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No memes found that were added in the last 30 days.', delete_after=6)
                await to_delete.delete(delay=3)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute meme command: {ex}',logging.ERROR)     

    @commands.command(help="Get a meme that has not yet been voted on.", aliases=["ur", "UR", "Ur"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def unratedmeme(self, ctx):
        try:
            to_delete = ctx.message
            message = Helpers.CommandStrip(self, ctx.message.content)
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
                self.last_meme_roll[f"{ctx.guild.id}"] = meme[0][0]
                await ctx.send(f'{ctx.message.author.mention}: **ID:{meme[0][0]}**\n {meme[0][1]}')
                await to_delete.delete(delay=3)
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No unrated memes found.', delete_after=6)
                await to_delete.delete(delay=3)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute meme command: {ex}',logging.ERROR)     

    @commands.command(help="Rate a meme as good.", aliases=["gm", "GM", "Gm", "Godmersham", "godmersham"])
    @commands.cooldown(rate=1, per=1, type=BucketType.member)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def goodmeme(self, ctx):
        m_id = None
        values_to_find = []
        try:
            to_delete = ctx.message
            message = Helpers.CommandStrip(self, ctx.message.content)
            if f"{ctx.guild.id}" in self.last_meme_roll:
                m_id = self.last_meme_roll[f"{ctx.guild.id}"]
            else:
                m_id = None
            if len(message) > 0 and Helpers.FuzzyNumberSearch(self, message) is not None:
                m_id = int(Helpers.FuzzyNumberSearch(self, message))
            t = ("m_id", m_id)
            values_to_find.append(t)
            meme = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', values_to_find)
            if len(meme) > 0:
                vote = dbm.Retrieve(f'memes{ctx.guild.id}', 'upvotes', [("author_id", f'<@{ctx.message.author.id}>'), ("m_id", m_id)])
                if len(vote) == 0:
                    d = {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>', "author_username": ctx.message.author.name}
                    dbm.Insert(f'memes{ctx.guild.id}', "upvotes", d)
                    dbm.Delete(f'memes{ctx.guild.id}', "downvotes", {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>'})
                    dbm.Update(f'memes{ctx.guild.id}', 'memes', {"score": self.GetMemeScore(ctx, m_id)}, {"m_id": m_id})
                    await ctx.send(f'{ctx.message.author.mention}: **ID:{m_id}** - :arrow_up: **{self.GetMemeScore(ctx, m_id)}**')
                    await to_delete.delete(delay=3)
                else:
                    await ctx.send(f'{ctx.message.author.mention}: You already upvoted **ID:{m_id}**.')
                    await to_delete.delete(delay=3)
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No meme to vote on. Either you specified a meme ID that doesn\'t exist or no meme was rolled since the last bot restart.', delete_after=6)
                await to_delete.delete(delay=3)

        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute goodmeme command: {ex}', logging.ERROR)

    @commands.command(help="Rate a meme as bad.", aliases=["bm", "BM", "Bm", "Bandmaster", "bandmaster"])
    @commands.cooldown(rate=1, per=1, type=BucketType.member)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def badmeme(self, ctx):
        m_id = None
        values_to_find = []
        try:
            to_delete = ctx.message
            message = Helpers.CommandStrip(self, ctx.message.content)
            if f"{ctx.guild.id}" in self.last_meme_roll:
                m_id = self.last_meme_roll[f"{ctx.guild.id}"]
            else:
                m_id = None
            if len(message) > 0 and Helpers.FuzzyNumberSearch(self, message) is not None:
                m_id = int(Helpers.FuzzyNumberSearch(self, message))
            t = ("m_id", m_id)
            values_to_find.append(t)
            meme = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', values_to_find)
            if len(meme) > 0:
                vote = dbm.Retrieve(f'memes{ctx.guild.id}', 'downvotes', [("author_id", f'<@{ctx.message.author.id}>'), ("m_id", m_id)])
                if len(vote) == 0:
                    d = {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>', "author_username": ctx.message.author.name}
                    dbm.Insert(f'memes{ctx.guild.id}', "downvotes", d)
                    dbm.Delete(f'memes{ctx.guild.id}', "upvotes", {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>'})
                    dbm.Update(f'memes{ctx.guild.id}', 'memes', {"score": self.GetMemeScore(ctx, m_id)}, {"m_id": m_id})
                    await ctx.send(f'{ctx.message.author.mention}: **ID:{m_id}** - :arrow_down: **{self.GetMemeScore(ctx, m_id)}**')
                else:
                    await ctx.send(f'{ctx.message.author.mention}: You already downvoted **ID:{m_id}**.')
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No meme to vote on.\nEither you specified a meme ID that doesn\'t exist or no meme was rolled since the last bot restart.', delete_after=6)
            await to_delete.delete(delay=3)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute goodmeme command: {ex}', logging.ERROR)

    @commands.command(help="Get a meme's information.", aliases=["mi", "MI", "Mi"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def memeinfo(self, ctx):
        m_id = None
        values_to_find = []
        try:
            to_delete = ctx.message
            message = Helpers.CommandStrip(self, ctx.message.content)
            if f"{ctx.guild.id}" in self.last_meme_roll:
                m_id = self.last_meme_roll[f"{ctx.guild.id}"]
            else:
                m_id = None
            if len(message) > 0 and Helpers.FuzzyNumberSearch(self, message) is not None:
                m_id = int(Helpers.FuzzyNumberSearch(self, message))
            t = ("m_id", m_id)
            values_to_find.append(t)
            meme = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', values_to_find)
            if len(meme) > 0:
                meme_dict = {
                    "author": {"name": f'Meme #{m_id} Info'},
                    "description": f'Created by {meme[0][3]} on {meme[0][6]}\nScore: **{meme[0][2]}** (+{self.GetUpvoteCount(ctx, m_id)} / -{self.GetDownvoteCount(ctx, m_id)})',
                    "thumbnail": {"url": f'{self.GetGradeUrl(ctx, meme[0][2])}'},
                    "footer": {"text": f'Requested by {ctx.message.author.display_name}'}
                }
                result_embed = discord.Embed.from_dict(meme_dict)
                await ctx.send(embed=result_embed)
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No meme info to get.\nEither you specified a meme ID that doesn\'t exist or no meme was rolled since the last bot restart.', delete_after=10)
            await to_delete.delete(delay=3)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute memeinfo command: {ex}', logging.ERROR)

    @commands.command(help="Show who voted on a meme.", aliases=["v", "V", "Voters"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def voters(self, ctx):
        try:
            upvoters = []
            upvoter_message = ""
            downvoters = []
            downvoter_message = ""
            to_delete = ctx.message
            message = Helpers.CommandStrip(self, ctx.message.content)
            if f"{ctx.guild.id}" in self.last_meme_roll:
                m_id = self.last_meme_roll[f"{ctx.guild.id}"]
            else:
                m_id = None
            if len(message) > 0 and Helpers.FuzzyNumberSearch(self, message) is not None:
                m_id = int(Helpers.FuzzyNumberSearch(self, message))
            if m_id != None:
                voter_dict = self.GetVoters(ctx, m_id)
                for a_id, name in voter_dict["ups"]:
                    print(f'{a_id}, {name}')
                    member_id = int(Helpers.FuzzyNumberSearch(self, a_id))
                    member = ctx.guild.get_member(member_id)
                    if member != None:
                        upvoters.append(member.name)
                    else:
                        upvoters.append(name)
                for a_id, name in voter_dict["downs"]:
                    member_id = int(Helpers.FuzzyNumberSearch(self, a_id))
                    member = ctx.guild.get_member(member_id)
                    if member != None:
                        downvoters.append(member.name)
                    else:
                        downvoters.append(name)
                if len(upvoters) > 0:
                    i = 0
                    print(upvoters)
                    for member in upvoters:
                        if member != None:
                            upvoter_message += f'{member}, '
                        else:
                            upvoter_message += f'``Unknown User``, '
                        if i == 4:
                            upvoter_message += '\n'
                            i = 0
                        else:
                            i += 1
                        
                    upvoter_message = upvoter_message[:-2]                    
                else:
                    upvoter_message = "None!"
                if len(downvoters) > 0:
                    i = 0
                    for member in downvoters:
                        if member != None:
                            downvoter_message += f'{member}, '
                        else:
                            downvoter_message += f'``Unknown User``, '
                        if i == 4:
                            downvoter_message += '\n'
                            i = 0
                        else:
                            i += 1                       
                    downvoter_message = downvoter_message[:-2]                      
                else:
                    downvoter_message = "None!"
                final_message = f'**Voters for Meme #{m_id}:**\n**Upvotes:** {upvoter_message}\n**Downvotes:** {downvoter_message}'
                await ctx.send(f'{ctx.message.author.mention}: {final_message}')
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: No meme info to get.\nEither you specified a meme ID that doesn\'t exist or no meme was rolled since the last bot restart.', delete_after=10)
            await to_delete.delete(delay=3)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t get meme voters: {ex}', logging.ERROR)

    @commands.command(help="Add a meme.", aliases=["am", "AM", "Am"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def addmeme(self, ctx):
        try:
            to_delete = ctx.message
            forbidden = ["@everyone", "@here", "puu.sh", "twimg.com", "i.4cdn.org", "4chan.org", "mixtape.moe"]
            message = Helpers.CommandStrip(self, ctx.message.content)
            mentions = ctx.message.mentions
            valid = True
            if len(message) > 0:
                for term in forbidden:
                    if message.find(term) != -1:
                        valid = False
                if len(mentions) > 0:
                    valid = False
                if valid:
                    existing = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', [("meme", message)])
                    if len(existing) == 0:
                        today = datetime.today().strftime('%Y-%m-%d')
                        d = {"meme": message, "score": 0, "author_username": ctx.message.author.name, "author_nickname": ctx.message.author.nick, "author_id": f'<@{ctx.message.author.id}>', "date_added": today}
                        dbm.Insert(f'memes{ctx.guild.id}', 'memes', d)
                        nm = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', [("meme", message)], where_type=WhereType.AND, column_data=["m_id"])
                        await ctx.send(f'{ctx.message.author.mention}: Meme added. (ID:{nm[0][0]})')
                    else:
                        ctx.command.reset_cooldown(ctx)
                        await ctx.send(f'{ctx.message.author.mention}: That\'s already a meme, you dip.', delete_after=10)
                else:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: That meme contains a forbidden term. Memes cannot highlight people or contain links that expire quickly.', delete_after=10)
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: Can\'t add a blank meme.', delete_after=10)
            await to_delete.delete(delay=25)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t add meme: {ex}', logging.ERROR)

    @commands.command(help="Delete a meme.", aliases=["dm", "DM", "Dm"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def deletememe(self, ctx):
        try:
            to_delete = ctx.message
            m_id = int(Helpers.FuzzyNumberSearch(self, Helpers.CommandStrip(self, ctx.message.content)))
            if m_id != None:
                where = {"m_id": m_id}
                affected = dbm.Delete(f'memes{ctx.guild.id}', 'memes', where)
                if affected == 1:
                    dbm.Delete(f'memes{ctx.guild.id}', 'upvotes', where)
                    dbm.Delete(f'memes{ctx.guild.id}', 'downvotes', where)
                    await ctx.send(f'{ctx.message.author.mention}: Meme #{m_id} deleted.')
                else:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: Couldn\'t delete Meme #{m_id}.\nProbably because there is no meme with that ID.', delete_after=6)
            else:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: Specify a meme to delete.', delete_after=6)
            await to_delete.delete(delay=3)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t delete meme: {ex}', logging.ERROR)

    @commands.command(help="Delete a meme that you added.", aliases=["sdm", "SDM", "Sdm", "selfdelete"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def selfdeletememe(self, ctx):
        try:
            to_delete = ctx.message
            m_id = int(Helpers.FuzzyNumberSearch(self, Helpers.CommandStrip(self, ctx.message.content)))
            if m_id != None:
                where = {"m_id": m_id, "author_id": f'<@{ctx.message.author.id}>'}
                affected = dbm.Delete(f'memes{ctx.guild.id}', 'memes', where)
                if affected == 1:
                    where = {"m_id": m_id}
                    dbm.Delete(f'memes{ctx.guild.id}', 'upvotes', where)
                    dbm.Delete(f'memes{ctx.guild.id}', 'downvotes', where)
                    await ctx.send(f'{ctx.message.author.mention}: Meme #{m_id} deleted.', delete_after=6)
                else:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: Couldn\'t delete Meme #{m_id}.\nEither because there is no meme with that ID or you didn\'t add that meme.', delete_after=6)
            else: 
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f'{ctx.message.author.mention}: Specify a meme to delete.', delete_after=6)
            await to_delete.delete(delay=3)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t delete meme: {ex}', logging.ERROR)

    @commands.command(help="Get the best meme either overall or for a specific user.", aliases=["best", "Best"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def bestmeme(self, ctx):
        try:
            name = Helpers.CommandStrip(self, ctx.message.content)
            where = None
            if len(name) > 0:
                where = [("author_username", name)]

            meme = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', where=where, compare_type=CompareType.LIKE, order_by=("score", "desc"))
            if len(meme) > 0:
                self.last_meme_roll[f"{ctx.guild.id}"] = meme[0][0]
                if len(name) > 0:
                    response = f'Best Meme by **{meme[0][3]}** is **#{meme[0][0]}** with Score **{meme[0][2]}**\n{meme[0][1]}\n'
                else:    
                    response = f'Best Meme is **#{meme[0][0]}** by **{meme[0][3]}** with Score **{meme[0][2]}**\n{meme[0][1]}\n'
                await ctx.send(f'{ctx.message.author.mention}: {response}')
            else:
                if len(name) > 0:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: No memes found for user {name}.', delete_after=6)
                else:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: No memes found.', delete_after=6)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t get best meme: {ex}', logging.ERROR)

    @commands.command(help="Get the worst meme either overall or for a specific user.", aliases=["worst", "Worst"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def worstmeme(self, ctx):
        try:
            name = Helpers.CommandStrip(self, ctx.message.content)
            where = None
            if len(name) > 0:
                where = [("author_username", name)]

            meme = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', where=where, compare_type=CompareType.LIKE, order_by=("score", "asc"))
            if len(meme) > 0:
                self.last_meme_roll[f"{ctx.guild.id}"] = meme[0][0]
                if len(name) > 0:
                    response = f'Worst Meme by **{meme[0][3]}** is **#{meme[0][0]}** with Score **{meme[0][2]}**\n{meme[0][1]}\n'
                else:    
                    response = f'Worst Meme is **#{meme[0][0]}** by **{meme[0][3]}** with Score **{meme[0][2]}**\n{meme[0][1]}\n'
                await ctx.send(f'{ctx.message.author.mention}: {response}')
            else:
                if len(name) > 0:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: No memes found for user {name}.', delete_after=6)
                else:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send(f'{ctx.message.author.mention}: No memes found.', delete_after=6)
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t get worst meme: {ex}', logging.ERROR)

    @commands.command(help="Get the meme list either in total or for a specific user.", aliases=["ml", "Ml", "ML", "Memelist"])
    @commands.cooldown(rate=1, per=20, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def memelist(self, ctx):
        msg = Helpers.CommandStrip(self, ctx.message.content)
        if len(msg) > 0:
            names = msg.split(',')
        else:
            names = []
        where = None
        meme_list = ''

        await ctx.trigger_typing()
        if len(names) > 0:
            where = []
            for name in names:
                where.append(("author_username", name.strip()))
            memes = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', where=where, where_type=WhereType.OR, compare_type=CompareType.LIKE, rows_required=99999)
        else:
            memes = dbm.Retrieve(f'memes{ctx.guild.id}', 'memes', rows_required=99999)
        if len(memes) > 0:
            for meme in memes:
                meme_string = f'ID: {meme[0]}\nAuthor: {meme[3]}\nDate Added: {meme[6]}\nScore: {meme[2]}\nMeme: {meme[1]}\n\n'
                meme_list += meme_string
            list_file = open('./internal/data/memelist.txt', 'wb')
            meme_list = meme_list.encode('utf-8-sig')
            list_file.write(meme_list)
            list_file.close()
            await ctx.send(content=f'{ctx.message.author.mention}', file=discord.File('./internal/data/memelist.txt'))
        else:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f'{ctx.message.author.mention}: No memes found.', delete_after=6)

    
    @commands.command(help="Get the meme stats for a specific user, or yourself.", aliases=["tms", "Tms", "TMS", "Totalmemestats"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def totalmemestats(self, ctx):
        total_memes = 0
        good_count = 0
        neutral_count = 0
        bad_count = 0
        voted_count = 0
        average = 0

        query = '''SELECT * FROM 
			(SELECT COUNT(DISTINCT m_id) as totalcount FROM memes),
			(SELECT COUNT(DISTINCT m_id) as good FROM memes WHERE score > 0), 
			(SELECT COUNT(DISTINCT m_id) as bad FROM memes WHERE score < 0), 
			(SELECT COUNT(DISTINCT memes.m_id) as neutral FROM memes INNER JOIN upvotes ON memes.m_id LIKE upvotes.m_id WHERE memes.score = 0 AND memes.m_id IN (SELECT m_id FROM upvotes)),
			(SELECT AVG(score) as average FROM memes)'''
        results = dbm.ExecuteRawQuery(f'memes{ctx.guild.id}', query)
        
        if results != None:
            print(results)
            total_memes = results[0]
            good_count = results[1]
            bad_count = results[2]
            neutral_count = results[3]
            average = results[4]

            voted_count = good_count + bad_count + neutral_count
            good_percent = round((good_count/voted_count)*100, 2)
            bad_percent = round((bad_count/voted_count)*100, 2)
            neutral_percent = round((neutral_count/voted_count)*100, 2)
            average = round(average, 2)

            response = f'There are **{total_memes}** memes in the database.\n**{voted_count}** have been rated.\n**{good_count}** ({good_percent}%) are Good, **{neutral_count}** ({neutral_percent}%) are Neutral, and **{bad_count}** ({bad_percent}%) are Bad.\nThe average memescore is **{average}**.'
            await ctx.send(f'{ctx.message.author.mention}: {response}')
        else:
            await ctx.send(f'{ctx.message.author.mention}: No memes found.', delete_after=6)

    @commands.command(help="Get the top or bottom of the rankings for average meme score. A threshold", aliases=["mb", "Mb", "MB", "Memerboard"])
    @commands.cooldown(rate=1, per=15, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def memerboard(self, ctx):
        msg = Helpers.CommandStrip(self, ctx.message.content)
        if len(msg) > 0:
            msg = msg.split()[0].lower()
        if msg == 'bottom' or msg == 'bot':
            if len(ctx.guild.members) > 75:
                table = 'bottom_five_above_ten'
            else:
                table = 'bottom_five'
        else:
            if len(ctx.guild.members) > 75:
                table = 'top_ten_above_ten'
            else:
                table = 'top_five'
        results = dbm.Retrieve(f'memes{ctx.guild.id}', table, rows_required=10)
        if results != None:
            print(results)
            if msg == 'bottom' or msg == 'bot':
                response = 'The bottom 10 average memescore holders are:\n'
            else:
                response = 'The top 10 average memescore holders are:\n'
            for i in range(0, len(results)):
                if results[i][1] == None or results[i][1] == 'None':
                    user = self.client.get_user(Helpers.FuzzyNumberSearch(self, results[i][0]))
                    if user != None:
                        name = user.name
                    else:
                        name = 'None'
                else:
                    name = results[i][1]
                response += f'**#{i+1}** - {name}: **{round(results[i][2],2)}**.\n'
            await ctx.send(f'{ctx.message.author.mention}: {response}')
        else:
            await ctx.send(f'{ctx.message.author.mention}: No memes found.', delete_after=6)
        

    @commands.command(help="Get the meme stats for a specific user, or yourself.", aliases=["ms", "Ms", "MS", "Memestats"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def memestats(self, ctx):
        total_memes = 0
        user_count = 0
        good_count = 0
        neutral_count = 0
        bad_count = 0
        voted_count = 0
        average = 0

        msg = Helpers.CommandStrip(self, ctx.message.content)
        if len(msg) > 0:
            name = msg 
        else:
            name = ctx.message.author.name
        query = '''SELECT * FROM 
			(SELECT COUNT(DISTINCT m_id) as totalcount FROM memes),
			(SELECT COUNT(DISTINCT m_id) as memecount FROM memes WHERE author_username LIKE ?1),
			(SELECT COUNT(DISTINCT m_id) as good FROM memes WHERE author_username LIKE ?1 AND score > 0), 
			(SELECT COUNT(DISTINCT m_id) as bad FROM memes WHERE author_username LIKE ?1 AND score < 0), 
			(SELECT COUNT(DISTINCT memes.m_id) as neutral FROM memes INNER JOIN upvotes ON memes.m_id LIKE upvotes.m_id WHERE memes.author_username LIKE ?1 AND memes.score = 0 AND memes.m_id IN (SELECT m_id FROM upvotes)),
			(SELECT AVG(score) as average FROM memes WHERE author_username LIKE ?1)'''
        params = [name]
        results = dbm.ExecuteParamQuery(f'memes{ctx.guild.id}', query, params)
        if results != None:
            if results[0][1] > 0:
                total_memes = results[0][0]
                user_count = results[0][1]
                good_count = results[0][2]
                bad_count = results[0][3]
                neutral_count = results[0][4]
                average = results[0][5]
    
                voted_count = good_count + bad_count + neutral_count
                total_percent = round((user_count/total_memes)*100, 2) if total_memes > 0 else 0
                good_percent = round((good_count/voted_count)*100, 2)  if voted_count > 0 else 0
                bad_percent = round((bad_count/voted_count)*100, 2)  if voted_count > 0 else 0
                neutral_percent = round((neutral_count/voted_count)*100, 2)  if voted_count > 0 else 0
                average = round(average, 2) if average != None else 0
    
                response = f'**{name}** has added **{user_count}** memes which is **{total_percent}%** of the total **{total_memes}** memes.\nOf their {voted_count} rated memes, **{good_count}** ({good_percent}%) are Good, **{neutral_count}** ({neutral_percent}%) are Neutral, and **{bad_count}** ({bad_percent}%) are Bad.\nTheir average memescore is **{average}**.'
                await ctx.send(f'{ctx.message.author.mention}: {response}')
            else:
                await ctx.send(f'{ctx.message.author.mention}: No memes found for {name}', delete_after=6)
        else:
                await ctx.send(f'{ctx.message.author.mention}: Something went wrong connecting to the database.', delete_after=6)



def setup(client):
    client.add_cog(Memes(client))