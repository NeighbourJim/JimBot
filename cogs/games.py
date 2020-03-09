import discord
import logging
import random
import asyncio
import json
import urllib.parse
from lxml import html
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helper
from internal.data.adjectives import adjectives
from internal.stand_image_generator import stand_gen

class Games(commands.Cog):

    def __init__(self, client):
        self.client = client

    def GetStandStats(self):
        stats = []
        for i in range(6):
            rand = random.randint(0,1000)
            if rand >= 990:
                stats.append("∞")
            elif rand >= 950:
                stats.append("S")
            elif rand >= 750:
                stats.append("A")
            elif rand >= 500:
                stats.append("B")
            elif rand >= 300:
                stats.append("C")
            elif rand >= 100:
                stats.append("D")
            else:
                stats.append("E")
        return stats

    # This command is very server specific. 
    # It will basically only run for the server I'm building the bot for.
    @commands.command(aliases=["tb", "TB", "Tb"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
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
                await ctx.send(f'{ctx.message.author.mention}: Could not find the required emoji.', delete_after=6)
        except Exception as ex:
            logger.LogPrint(ex, logging.ERROR)

    @commands.command(help="Randomly describe whaver you put in.", aliases=["a", "A"])
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def adjective(self, ctx):
        adjs = []
        response = ''
        split_message = Helper.CommandStrip(ctx.message.content).split(' ')
        amount = Helper.FuzzyNumberSearch(split_message[0])
        if amount == None:
            amount = 1
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
                    if amount == 2 and i == (len(adjs)-2):
                        response += ' and '
                    elif i == (len(adjs)-2):
                        response += ', and '
                    else:
                        response += ', '
            if amount != 1:
                response = f'{response[:-2]} '
            else:
                response = f'{response} '
            response = response.capitalize()
            for word in split_message:
                response += f'{word} '
            response = f'{response.strip()}.'
        else:
            ctx.command.reset_cooldown(ctx)
            response = f'Invalid number of adjectives requested.'        
        await ctx.send(f'{ctx.message.author.mention}: ``{response}``')

    @commands.command(aliases=["Power"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def power(self, ctx):
        try:
            await ctx.trigger_typing()
            api_url = 'https://powerlisting.fandom.com/api.php'
            params = {
                "action": "query",
                "list": "random",
                "rnnamespace": "0",
                "rnlimit": "1",
                "format": "json"
            }
            random_power = Helper.GetWebPage(api_url, params)
            if random_power:
                power = random_power.json()["query"]["random"][0]
                name = power["title"]
                encoded_url = f'https://powerlisting.fandom.com/wiki/{urllib.parse.quote(name)}'
                power_data = Helper.GetWebPage(encoded_url)
                if power_data:
                    page_tree = html.fromstring(power_data.text)
                    desc = page_tree.xpath('//meta[@name="description"]/@content')
                    if len(desc) > 0:
                        response = f'{ctx.message.author.mention}: **Power:** {name}\n**Description:** {desc[0].strip()}\n<{encoded_url}>'
                    else:
                        response = f'{ctx.message.author.mention}: **Power:**{name}\n<{encoded_url}>'
                else:
                    response = f'{ctx.message.author.mention}: Couldn\'t get Power info.'
            else:
                response = f'{ctx.message.author.mention}: Couldn\'t get Power info.'
            await ctx.send(response)
        except Exception as ex:
            logger.LogPrint(ex, logging.ERROR)

    @commands.command(aliases=["Stand"])
    @commands.cooldown(rate=1, per=7, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def stand(self, ctx):
        await ctx.trigger_typing()
        stats = self.GetStandStats()
        power_api_url = 'https://powerlisting.fandom.com/api.php'
        music_api_url = 'https://music.fandom.com/api.php'
        params = {
            "action": "query",
            "list": "random",
            "rnnamespace": "0",
            "rnlimit": "1",
            "format": "json"
        }
        random_power = Helper.GetWebPage(power_api_url, params)            
        random_music = Helper.GetWebPage(music_api_url, params)
        if random_power and random_music:
            power = random_power.json()["query"]["random"][0]
            pow_name = power["title"]
            pow_url = f'https://powerlisting.fandom.com/wiki/{urllib.parse.quote(pow_name)}'
            music = random_music.json()["query"]["random"][0]
            music_name = music["title"].split(',')[0]
            music_name = music_name.split('List of ')[0]
            music_name = music_name.split('(')[0]
            if len(music_name.split(':')) > 1:
                print(music_name.split(':'))
                r = random.randint(0,10)
                if r >= 3:
                    music_name = music_name.split(':')[1]
                else:
                    music_name = music_name.split(':')[0]
            else:
                music_name = music_name.split(':')[0]
            if music_name == "Lyrics":
                music_name = music["title"].split(':')[1]
            power_data = Helper.GetWebPage(pow_url)
            if power_data:
                page_tree = html.fromstring(power_data.text)
                desc = page_tree.xpath('//meta[@name="description"]/@content')
                stats_dict = {"power": stats[0],"speed": stats[1],"range": stats[2],"durability": stats[3],"precision": stats[4],"potential": stats[5]}
                r = ctx.message.author.colour.r
                g = ctx.message.author.colour.g
                b = ctx.message.author.colour.b
                if r > 230:
                    r = r-30
                elif r < 50:
                    r = r+50
                if g > 230:
                    g = g-30
                elif g < 50:
                    g = g+50
                if b > 230:
                    b = b-30
                elif b < 50:
                    b = b+50
                user_colour = (r,g,b,200)
                if stand_gen.GenerateImage(stats_dict,user_colour) == True:
                    image_file = discord.File('./internal/data/images/stand.png', filename='stand.png')
                    stand_embed = discord.Embed()
                    if len(ctx.guild.members) > 75:
                        stand_embed.set_thumbnail(url="attachment://stand.png")
                    else:
                        stand_embed.set_image(url="attachment://stand.png")
                    stand_embed.set_author(name=f'{ctx.message.author.display_name}\'s Stand')
                    stand_embed.title = f'**「{music_name}」**'
                    if len(desc) > 0:
                        stand_embed.description = f"It has the ability: **[{pow_name}]({pow_url})**\n{'.'.join(desc[0].split('.')[0:2])}"
                    else:
                        stand_embed.description = f"It has the ability: **[{pow_name}]({pow_url})**"
                    sent = await ctx.send(file=image_file, embed=stand_embed)
                    if len(ctx.guild.members) <= 75:
                        await asyncio.sleep(7)
                        stand_embed.set_thumbnail(url="attachment://stand.png")
                        stand_embed.set_image(url='')
                        await sent.edit(embed=stand_embed)
                else:
                    response = f"Couldn't generate Stand."
                    await ctx.send(response)
            else:
                response = f"Couldn't generate Stand."
                await ctx.send(response)
        else:
            response = f"Couldn't generate Stand."
            await ctx.send(response)



def setup(client):
    client.add_cog(Games(client))