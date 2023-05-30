import discord
import logging
import pickle
from discord.ext import commands
from discord.ext.commands import BucketType
from os import path

from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from internal.databasemanager import dbm
from internal.logs import logger
from bot import current_settings

class joinleave(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db_folder = "./internal/data/databases/"
        self.base_dict = dict()
        self.settings_cache = dict()

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)
        
    def pickle_settings(self, settings, id):
        with open(f'{self.db_folder}jl-settings-{id}.pickle', 'wb') as handle:
            pickle.dump(settings, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_settings(self, id):
        with open(f'{self.db_folder}jl-settings-{id}.pickle', 'rb') as handle:
            return pickle.load(handle)

    @commands.command(help="Change join leave message settings.", aliases=["jls"])
    @commands.cooldown(rate=1, per=15, type=BucketType.channel)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def join_leave_settings(self, ctx):
        if ctx.author.id == 107847100150091776:
            settings = command_to_toggle = Helpers.CommandStrip(self, ctx.message.content).lower().split(',')
            if len(settings) == 5:
                channel = ctx.message.raw_channel_mentions[0]
                joins = settings[1]
                leaves = settings[2]
                join_message = settings[3]
                leave_message = settings[4]
    
                settings_d = dict()
                settings_d["channel"] = channel
                settings_d["joins"] = joins == "true"
                settings_d["leaves"] = leaves == "true"
                settings_d["join_message"] = join_message
                settings_d["leave_message"] = leave_message
    
                self.settings_cache[ctx.guild.id] = settings_d
                self.pickle_settings(settings_d, ctx.guild.id)
                await ctx.reply("Settings saved.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id not in self.settings_cache:
            if path.isfile(f"{self.db_folder}jl-settings-{member.guild.id}.pickle"):
                self.settings_cache[member.guild.id] = self.load_settings(member.guild.id)
            else:
                return
        active_settings = self.settings_cache[member.guild.id]        
        if active_settings["joins"] == True:            
            channel = member.guild.get_channel(active_settings["channel"])
            msg = active_settings["join_message"].replace("usr_name", member.mention)
            await channel.send(msg)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id not in self.settings_cache:
            if path.isfile(f"{self.db_folder}jl-settings-{member.guild.id}.pickle"):
                self.settings_cache[member.guild.id] = self.load_settings(member.guild.id)
            else:
                return
        active_settings = self.settings_cache[member.guild.id]        
        print(active_settings)
        if active_settings["leaves"] == True:            
            channel = member.guild.get_channel(active_settings["channel"])
            msg = active_settings["leave_message"].replace("usr_name", f'**{member.name}**')
            await channel.send(msg)


def setup(client):
    client.add_cog(joinleave(client))