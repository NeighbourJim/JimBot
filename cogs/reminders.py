import discord
import logging
import re
from dateparser import search
import datetime
from discord.ext import commands, tasks
from discord.ext.commands import BucketType
from os import path

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
import internal.reminders_db as reminders_db

class Reminders(commands.Cog):

    def __init__(self, client):
        self.client = client
        reminders_db.setup()

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)

    @commands.command(aliases=["remind"], help="Set a reminder.\nUsage: !remindme to do the thing in 10 minutes.")
    @commands.cooldown(rate=1, per=10, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def remindme(self, ctx):
        full_message = Helpers.CommandStrip(self, ctx.message.content)

        if not full_message:
            await ctx.reply("You need to provide a reminder message and a time.")
            return

        # Use dateparser's search function to find time strings
        found_dates = search.search_dates(full_message, settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': True})

        if not found_dates:
            await ctx.reply("I couldn't understand the time for the reminder. Try something like 'in 10 minutes' or 'tomorrow at 2pm'.")
            return

        # Take the first found date
        time_string, due_time = found_dates[0]
        
        # The reminder message is the original message with the time string removed
        reminder_message = full_message.replace(time_string, "").strip()

        if not reminder_message:
            await ctx.reply("You need to provide a message for the reminder.")
            return

        if not due_time:
            await ctx.reply(f"I couldn't understand the time string '{time_string}'.")
            return
        
        # Ensure due_time is timezone-aware and in UTC for database storage
        if due_time.tzinfo is None:
            # If dateparser returns a naive datetime, assume it's in the bot's local timezone and convert to UTC
            # A better approach might be to assume user's local time, but that's much more complex.
            # For now, we'll make it UTC if it's naive.
            due_time = due_time.replace(tzinfo=datetime.timezone.utc)
        else:
            due_time = due_time.astimezone(datetime.timezone.utc)


        if due_time < datetime.datetime.now(datetime.timezone.utc):
            await ctx.reply("You can't set a reminder in the past!")
            return

        try:
            reminders_db.add_reminder(ctx.author.id, ctx.channel.id, due_time.strftime('%Y-%m-%d %H:%M:%S'), reminder_message)
            await ctx.reply(f"Okay, I will remind you on {due_time.strftime('%Y-%m-%d at %H:%M:%S UTC')} to: `{reminder_message}`")
        except Exception as e:
            logger.LogPrint(f"ERROR - Could not insert reminder into database: {e}", logging.ERROR)
            await ctx.reply("Sorry, there was an error saving your reminder.")

    @tasks.loop(seconds=15)
    async def check_reminders(self):
        reminders_to_send = reminders_db.get_due_reminders()

        if reminders_to_send:
            for r in reminders_to_send:
                reminder_id = r[0]
                user_id = r[1]
                channel_id = r[2]
                message = r[4]

                channel = self.client.get_channel(channel_id)
                if channel:
                    user = channel.guild.get_member(user_id)
                    if user:
                        try:
                            await channel.send(f"{user.mention}, you asked me to remind you: `{message}`")
                        except Exception as e:
                            logger.LogPrint(f"ERROR - Could not send reminder {reminder_id}: {e}", logging.ERROR)
                
                reminders_db.delete_reminder(reminder_id)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.client.wait_until_ready()

def setup(client):
    client.add_cog(Reminders(client))
