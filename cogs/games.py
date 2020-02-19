import discord
import logging
import random
import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helper
from internal.data.adjectives import adjectives

class Games(commands.Cog):

    def __init__(self, client):
        self.client = client

    # This command is very server specific. 
    # It will basically only run for the server I'm building the bot for.
    @commands.command(aliases=["tb", "TB", "Tb"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.guild_only()
    async def trollbox(self, ctx):
        fftrolled = Helper.FindEmoji(ctx, "fftrolled")
        left_side = Helper.FindEmoji(ctx, "longtroll3")
        right_side = Helper.FindEmoji(ctx, "longtroll1")
        try:
            if fftrolled is not None and left_side is not None and right_side is not None:
                prize = random.choice(ctx.guild.emojis)
                while(prize.animated == True):
                    prize = random.choice(ctx.guild.emojis)
                message_one = f'<:{left_side.name}:{left_side.id}><:{right_side.name}:{right_side.id}>'
                message_two = f'<:{left_side.name}:{left_side.id}>    <:{right_side.name}:{right_side.id}>'
                message_three = f'<:{left_side.name}:{left_side.id}> :sparkles: <:{right_side.name}:{right_side.id}>'
                message_four = f'<:{left_side.name}:{left_side.id}> <:{prize.name}:{prize.id}> <:{right_side.name}:{right_side.id}>'
                task_one = asyncio.create_task(ctx.send(message_one))
                await task_one
                await asyncio.sleep(1)
                task_two = asyncio.create_task(task_one.result().edit(content=message_two))
                await task_two
                await asyncio.sleep(0.2)
                task_three = asyncio.create_task(task_one.result().edit(content=message_three))
                await task_three
                await asyncio.sleep(1.2)
                task_four = asyncio.create_task(task_one.result().edit(content=message_four))
                await task_four
            else:
                await ctx.send(f'{ctx.message.author.mention}: Could not find the required emoji.')
        except Exception as ex:
            logger.LogPrint(ex, logging.ERROR)

    @commands.command(help="Randomly describe whaver you put in.", aliases=["a", "A"])
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.guild_only()
    async def adjective(self, ctx):
        adjs = []
        response = ''
        split_message = Helper.CommandStrip(ctx.message.content).split(' ')
        amount = Helper.FuzzyNumberSearch(split_message[0])
        if amount == None:
            amount = 2
        else:
            split_message = split_message[1:]
        if len(split_message) == 0:
            split_message.append(ctx.message.author.display_name)
        elif split_message[0] == '':
            split_message = [f"{ctx.message.author.display_name}"]
        if amount > 0:
            if amount > 5:
                amount = 5
            for i in range(0,amount):
                selected_adj = random.choice(adjectives)
                if selected_adj in adjs:
                    selected_adj = random.choice(adjectives)
                    i -= 1
                    continue
                adjs.append(selected_adj)
            for i in range(len(adjs)):
                response += f'{adjs[i]}'
                if amount != 1:
                    if i == (len(adjs)-2):
                        response += ' and '
                    else:
                        response += ', '
            if amount != 1:
                response = f'{response[:-2]} '
            else:
                response = f'{response} '
            response = response.capitalize()
            for word in split_message:
                response += f'{word} '
        else:
            response = f'{ctx.message.author.mention}: Invalid number of adjectives requested.'        
        await ctx.send(f'{ctx.message.author.mention}: ``{response}``')


def setup(client):
    client.add_cog(Games(client))