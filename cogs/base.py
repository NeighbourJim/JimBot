import discord
import random
import re
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.helpers import Helper

class Base(commands.Cog):

    def __init__(self, client):
        self.client = client    

    @commands.command()    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def ping(self, ctx):
        await ctx.send('Pong!')

    @commands.command(aliases=["8ball", "8b"])
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def _8ball(self, ctx):
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

    @commands.command(aliases=["r", "R"])
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
            
        


def setup(client):
    client.add_cog(Base(client))