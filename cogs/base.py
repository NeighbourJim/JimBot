import discord
import random
import logging
import re
import d20
import json
from discord.ext import commands, tasks
from discord.ext.commands import BucketType
from discord.ext.commands import EmojiConverter
from datetime import datetime

from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from internal.logs import logger
from bot import current_settings


class Base(commands.Cog):

    def __init__(self, client):
        self.client = client    
        #self.eldencd.start()

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)

    def cog_unload(self):
        #self.eldencd.cancel()
        return super().cog_unload()

    #@tasks.loop(seconds=600)
    #async def eldencd(self):
    #    game = discord.Game("OOOHHH ELDEN RING")
    #    await self.client.change_presence(status=discord.Status.online, activity=game)

    #@eldencd.before_loop
    #async def before_eldencd(self):
    #    await self.client.wait_until_ready()

    @commands.command(help="Ping!")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.reply(':sparkles:')

    @commands.command(aliases=["8ball", "8b"], help="Roll the Magic 8-Ball!\nUsage: !magic8ball question?")
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def magic8ball(self, ctx):
        answers = [
					'Signs point to yes.',
					'Yes.',
					'No.',
					'Without a doubt.',
					'My sources say no.',
					'As I see it, yes.',
					'You may rely on it.',
					'Probably not.',
					'It is decidedly so.',
					'Very doubtful.',
					'Yes - definitely.',
					'Absolutely not.',
					'Never ever ever.',
					'Of course not.',
					'Negative.',
					'It is certain.',
					'Most likely.',
					'My reply is no.',
					'Outlook good.',
					'Don\'t count on it.',
					'Who cares?',
					'Never, ever, ever.'
				]
        if len(Helpers.CommandStrip(self, ctx.message.content)) > 0:
            await ctx.reply(f'**{random.choice(answers)}**')
        else:
            await ctx.reply(f'What are you asking?')

    @commands.command(aliases=["r", "R"], help="Rolls a random number between 2 other numbers.\nIf provided with 1 number, will roll between 0 and that number.\nIf provided with 2 separated by a comma, will take the first as the min and the second as the max.\nUsage: !roll 100 / !roll 10,20.")
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def roll(self, ctx):
        # Split the message at comma, for custom roll range
        split_message = Helpers.CommandStrip(self, ctx.message.content).split(',')
        number = None
        min = None
        max = None
        if len(split_message) > 1:            
            # If there was a comma, attempt to parse the first 2 parts as numbers
            min = Helpers.FuzzyIntegerSearch(self, split_message[0])
            max = Helpers.FuzzyIntegerSearch(self, split_message[1])
        else:
            # If the user provided only one value, set min to 0 and parse their value for max
            min = 0
            max = Helpers.FuzzyIntegerSearch(self, split_message[0])
        try:
            if min != None and max != None:                
                if max < min:
                    # If max is less than min because the user specified a negative number, or did something strange, swap them so the randint() call will still function
                    tmp = max
                    max = min
                    min = tmp
                # Generate the number and form the response
                if max > 100000000:
                    max = 100000000
                if min < -100000000:
                    min = -100000000
                number = random.randint(min, max)
                response = f'Your number between {min} and {max} was: **{number}**.'
                # If 2 or more of the trailing digits are the same, and the server has an appropriate emoji, append it to the message - An in-joke on our server
                if len(str(number)) >= 2:
                    if str(number)[-1] == str(number)[-2]:
                        digits_emoji = Helpers.FindEmoji(self, ctx, "checkEm")
                        if digits_emoji != None:
                            response += f'<:{digits_emoji.name}:{digits_emoji.id}>'
                # If the number is 7, append the zap emoji - Another in-joke
                if number == 7:
                    response += ' :zap:'
                await ctx.reply(response)
            else:
                await ctx.reply(f'That\'s not a number.')
        except Exception as ex:
            logger.LogPrint(f'ROLL command failed. - {ex}', logging.ERROR)

    @commands.command(aliases=["Pick", "p"], help="Selects a random item out of provided choices.\nUsage: !pick cat,dog.")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def pick(self, ctx):
        # Split the message into a list at commas
        split_message = Helpers.CommandStrip(self, ctx.message.content).split(',')
        if len(split_message) > 1:
            # Select a random element and respond with it
            result = random.choice(split_message)
            await ctx.reply(f'{result}')
        else:
            await ctx.reply(f'You only gave one option.')



    @commands.command(aliases=["Dice"], help="Rolls a die of specified size a specified numer of times.\nUsage: !dice 2d20")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def dice(self, ctx):
        try:
            result = d20.roll(Helpers.CommandStrip(self, ctx.message.content))
            await ctx.reply(f'{result}')
        except d20.RollSyntaxError as e:
            await ctx.reply(f'Invalid input.', delete_after=6.0)
            await ctx.message.delete(delay=7)
        

    @commands.command(aliases=["ru", "RU", "Ru"], help="Gives up to 10 random ONLINE users on the server.")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randuser(self, ctx):
        await ctx.trigger_typing()
        selected_members = []
        response = ''
        members = ctx.guild.members
        # Get the amount of requested users
        amount = Helpers.FuzzyIntegerSearch(self, Helpers.CommandStrip(self, ctx.message.content).split(' ')[0])
        # Set the amount to 1 if the user did not specify, and 10 if they requested more than 10
        if amount == None:
            amount = 1
        if amount > 10:
            amount = 10
        # Shuffle the list
        random.shuffle(members)
        i = 0
        # Loop through the shuffled list, pop a member off the list, and append it to the selected members list, provided they aren't a bot OR offline
        while i < amount:
            if len(members) > 0:
                r_member = members.pop()
                if r_member.status != discord.Status.offline and r_member.bot == False: 
            
                    selected_members.append(r_member)
                    i += 1
            else:
                # If there are no more members to add (ie someone asks for 5 people in a server with only 4 members), end the loop
                break
        # Loop through the selected members, format their names, and append them to the response
        for member in selected_members:
            if member.display_name == member.name:
                name = f'{member.display_name}'
            else:
                name = f'{member.display_name} ({member.name})'
            response += f'{name}\n'
        await ctx.reply(f'{response}')

    @commands.command(aliases=["rua", "RUA", "Rua"], help="Gives up to 10 random users on the server, both online and offline.")    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randuserall(self, ctx):
        await ctx.trigger_typing()
        selected_members = []
        response = ''
        members = ctx.guild.members
        # Get the amount of requested users
        amount = Helpers.FuzzyIntegerSearch(self, Helpers.CommandStrip(self, ctx.message.content).split(' ')[0])
        # Set the amount to 1 if the user did not specify, and 10 if they requested more than 10
        if amount == None:
            amount = 1
        if amount > 10:
            amount = 10
        # Shuffle the list
        random.shuffle(members)
        i = 0
        # Loop through the shuffled list, pop a member off the list, and append it to the selected members list, provided they aren't a bot
        while i < amount:
            if len(members) > 0:
                r_member = members.pop()
                if r_member.bot == False:                 
                    selected_members.append(r_member)
                    i += 1
            else:
                # If there are no more members to add (ie someone asks for 5 people in a server with only 4 members), end the loop
                break
        # Loop through the selected members, format their names, and append them to the response
        for member in selected_members:
            if member.display_name == member.name:
                name = f'{member.display_name}'
            else:
                name = f'{member.display_name} ({member.name})'
            response += f'{name}\n'
        await ctx.reply(f'{response}')

    @commands.command(aliases=["e", "E"], help="Get the image link for an emote.")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def emote(self, ctx):
        # Get the ID of the first emoji in the user's message - If there is one, provide a link to the full image as stored on discord's servers.
        e_id = Helpers.GetFirstEmojiID(self, Helpers.CommandStrip(self, ctx.message.content))
        if e_id:
            await ctx.reply(f'https://cdn.discordapp.com/emojis/{e_id.group()}.png')
        else:            
            await ctx.reply(f'You didn\'t provide an emoji.')


    @commands.command(help="Print some info about the bot.")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def info(self, ctx):
        fields = [
            {"name": "Development Info", "value": "I am a bot created by NeighbourJim#4976.\nI am written in Python 3.8, using Discord.py.", "inline": False},
            {"name": "Servers", "value": f'I am currently in {len(self.client.guilds)} server(s).', "inline": False},
            {"name": "GitHub Repo", "value": "https://github.com/NeighbourJim/JimBot", "inline": False}
            ]
        embed_dict = {
                    "author": {"name": f'I am {self.client.user.display_name}!'}, 
                    "fields": fields,
                    "thumbnail": {"url": f'{self.client.user.avatar_url}'}
                    }
        info_embed = discord.Embed.from_dict(embed_dict)
        await ctx.reply(embed=info_embed)

    @commands.command(aliases=["cc", "Cc"], help="Convert a value between two currencies.")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def currencyconvert(self, ctx):
        split_message = Helpers.CommandStrip(self, ctx.message.content).split(' ')
        if len(split_message) >= 3:
            input_value = Helpers.FuzzyNumberSearch_OLD(self, split_message[0])
            input_value = float(input_value)
            if input_value and input_value > 0 and input_value < 1000000000000:
                currency_one = split_message[1].strip(',')
                currency_two = split_message[2].strip(',')
                url = f'https://free.currconv.com/api/v7/convert?q={currency_one}_{currency_two}&compact=ultra&apiKey={current_settings["keys"]["currencyconverter_key"]}'
                response = Helpers.GetWebPage(self, url).json()
                if len(response) > 0:
                    result = input_value * list(response.values())[0]
                    formatted_value = "{:,.2f}".format(input_value)
                    formatted_result = "{:,.2f}".format(result)
                    await ctx.reply(f'`{formatted_value} {currency_one.upper()} = {formatted_result} {currency_two.upper()}.`')
                    return
        await ctx.reply(f'Invalid input. Correct input eg. `!cc 2.5, USD, EUR`\n You must provide the 3 letter currency codes: <https://www.iban.com/currency-codes>')

    @commands.command(aliases=["dc"], help="Convert a distance into another distance")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def distanceconvert(self, ctx):
        split_message = Helpers.CommandStrip(self, ctx.message.content).split(',')
        units = ['mm', 'cm', 'm', 'km', 'in', 'ft', 'yd', 'mi']
        if len(split_message) >= 3:
            input_value = Helpers.FuzzyNumberSearch_OLD(self, split_message[0])
            try:
                input_value = float(input_value)
            except:
                await ctx.reply(f'Invalid input. Correct input eg. `!dc 2.5, m, ft`\n You must provide the unit codes: mm, cm, m, km, in, ft, yd, mi')
                return            
            unit_one = split_message[1].strip().lower()
            unit_two = split_message[2].strip().lower()
            if input_value and input_value > 0 and unit_one in units and unit_two in units:
                conversions = {
                    'mm': 1,
                    'cm': 10,
                    'm': 1000,
                    'km': 1000000,
                    'in': 25.4,
                    'ft': 304.8,
                    'yd': 914.4,
                    'mi': 1609344
                }
                result = input_value * conversions[unit_one] / conversions[unit_two]
                formatted_value = "{:,.2f}".format(input_value)
                formatted_result = "{:,.2f}".format(result)
                await ctx.reply(f'`{formatted_value} {unit_one} = {formatted_result} {unit_two}.`')
                return
            else:
                await ctx.reply(f'Invalid input. Correct input eg. `!dc 2.5, m, ft`\n You must provide the unit codes: mm, cm, m, km, in, ft, yd, mi')
        else:
            await ctx.reply(f'Invalid input. Correct input eg. `!dc 2.5, m, ft`\n You must provide the unit codes: mm, cm, m, km, in, ft, yd, mi')
            
        


def setup(client):
    client.add_cog(Base(client))