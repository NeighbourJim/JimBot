import discord
import random
import re
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.helpers import Helper

class Base(commands.Cog):

    def __init__(self, client):
        self.client = client    

    @commands.command(help="Ping!")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.send('Pong!')

    @commands.command(aliases=["8ball", "8b"], help="Roll the Magic 8-Ball!\nUsage: !magic8ball question?")
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
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
        if len(Helper.CommandStrip(ctx.message.content)) > 0:
            await ctx.send(f'{ctx.message.author.mention}: **{random.choice(answers)}**')
        else:
            await ctx.send(f'{ctx.message.author.mention}: What are you asking?')

    @commands.command(aliases=["r", "R"], help="Rolls a random number between 2 other numbers.\nIf provided with 1 number, will roll between 0 and that number.\nIf provided with 2 separated by a comma, will take the first as the min and the second as the max.\nUsage: !roll 100 / !roll 10,20.")
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def roll(self, ctx):
        split_message = Helper.CommandStrip(ctx.message.content).split(',')
        number = None
        min = None
        max = None
        if len(split_message) > 1:            
            try:
                min = int(split_message[0])
                max = int(split_message[1])
            except:
                await ctx.send(f'{ctx.message.author.mention}: One of your numbers wasn\'t a number.')
        else:
            try:
                min = 0
                max = int(split_message[0])
            except Exception as ex:
                print(ex)
                await ctx.send(f'{ctx.message.author.mention}: That\'s not a number.')
        if min != None and max != None:
            number = random.randint(min, max)
            response = f'{ctx.message.author.mention}: Your number between {min} and {max} was: **{number}**.'
            digits_regex = re.compile('(\d)(\1){1,}$')
            if str(number)[-1] == str(number)[-2]:
                digits_emoji = Helper.FindEmoji(ctx, "checkEm")
                if digits_emoji != None:
                    response += f'<:{digits_emoji.name}:{digits_emoji.id}>'
            await ctx.send(response)

    @commands.command(aliases=["Pick", "p"], help="Selects a random item out of provided choices.\nUsage: !pick cat,dog.")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.guild_only()
    async def pick(self, ctx):
        split_message = Helper.CommandStrip(ctx.message.content).split(',')
        if len(split_message) > 1:
            result = random.choice(split_message)
            await ctx.send(f'{ctx.message.author.mention}: {result}')
        else:
            await ctx.send(f'{ctx.message.author.mention}: You only gave one option.')

    # DICE COMMAND
    # Rolls a die of the specified type a specified number of times.
    # Usage: [prefix]dice 2d10
    @commands.command(aliases=["Dice"], help="Rolls a die of specified size a specified numer of times.\nUsage: !dice 2d20")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.guild_only()
    async def dice(self, ctx):
        split_message = Helper.CommandStrip(ctx.message.content).lower().split('d')
        if len(split_message) > 1:
            try:
                dice_amount = int(split_message[0])
                dice_size = int(split_message[1])
                rolls = []
                if dice_amount > 0 and dice_size > 0:
                    for i in range(dice_amount):
                        rolls.append(random.randint(1, dice_size))
                    await ctx.send(f'{ctx.message.author.mention}: Your rolls: **{rolls}**.\n**Total:** {sum(rolls)}.')
                else:
                    await ctx.send(f'{ctx.message.author.mention}: Invalid dice. Correct usage eg: ``!dice 2d20``')
            except:
                await ctx.send(f'{ctx.message.author.mention}: Invalid dice. Correct usage eg: ``!dice 2d20``')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Invalid dice. Correct usage eg: ``!dice 2d20``')

def setup(client):
    client.add_cog(Base(client))