import discord
import random
import logging
import re
from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ext.commands import EmojiConverter

from internal.helpers import Helpers
from internal.logs import logger


class Base(commands.Cog):

    def __init__(self, client):
        self.client = client    

    @commands.command(help="Ping!")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.send(':sparkles:')

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
            await ctx.send(f'{ctx.message.author.mention}: **{random.choice(answers)}**')
        else:
            await ctx.send(f'{ctx.message.author.mention}: What are you asking?')

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
                response = f'{ctx.message.author.mention}: Your number between {min} and {max} was: **{number}**.'
                # If 2 or more of the trailing digits are the same, and the server has an appropriate emoji, append it to the message - An in-joke on our server
                if len(str(number)) >= 2:
                    if str(number)[-1] == str(number)[-2]:
                        digits_emoji = Helpers.FindEmoji(self, ctx, "checkEm")
                        if digits_emoji != None:
                            response += f'<:{digits_emoji.name}:{digits_emoji.id}>'
                # If the number is 7, append the zap emoji - Another in-joke
                if number == 7:
                    response += ' :zap:'
                await ctx.send(response)
            else:
                await ctx.send(f'{ctx.message.author.mention}: That\'s not a number.')
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
            await ctx.send(f'{ctx.message.author.mention}: {result}')
        else:
            await ctx.send(f'{ctx.message.author.mention}: You only gave one option.')

    @commands.command(aliases=["Dice"], help="Rolls a die of specified size a specified numer of times.\nUsage: !dice 2d20")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def dice(self, ctx):
        # Split the message at 'd' to get both number of dice and dice size
        max_count = 50
        max_size = 100000
        split_message = Helpers.CommandStrip(self, ctx.message.content).lower().split('d')
        if len(split_message) > 1:
            dice_amount = Helpers.FuzzyIntegerSearch(self, split_message[0])
            dice_size = Helpers.FuzzyIntegerSearch(self, split_message[1])
            if dice_amount != None and dice_size != None:
                if dice_amount > 0 and dice_size > 0:
                    if dice_amount > max_count or dice_size > max_size:
                        await ctx.send(f'{ctx.message.author.mention}: Invalid dice size. Max amount {max_count}, max size {max_size}.')
                        return
                    # If both variables have appropriate values, roll the dice the specified number of times
                    # Append each roll to the rolls list, then provide them + the total
                    rolls = []
                    for i in range(dice_amount):
                        rolls.append(random.randint(1, dice_size))
                    await ctx.send(f'{ctx.message.author.mention}: Your rolls: **{", ".join(str(roll) for roll in rolls)}**.\n**Total:** {sum(rolls)}.')
                else:
                    await ctx.send(f'{ctx.message.author.mention}: Invalid dice. Correct usage eg: ``!dice 2d20``')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Invalid dice. Correct usage eg: ``!dice 2d20``')

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
        await ctx.send(f'{ctx.message.author.mention}: {response}')

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
        await ctx.send(f'{ctx.message.author.mention}: {response}')

    @commands.command(aliases=["e", "E"], help="Get the image link for an emote.")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def emote(self, ctx):
        # Get the ID of the first emoji in the user's message - If there is one, provide a link to the full image as stored on discord's servers.
        e_id = Helpers.GetFirstEmojiID(self, Helpers.CommandStrip(self, ctx.message.content))
        if e_id:
            await ctx.send(f'{ctx.message.author.mention}: https://cdn.discordapp.com/emojis/{e_id.group()}.png')
        else:            
            await ctx.send(f'{ctx.message.author.mention}: You didn\'t provide an emoji.')


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
        await ctx.send(embed=info_embed)

def setup(client):
    client.add_cog(Base(client))