import discord
import logging
import random
import asyncio
import json
import html as base_html
import urllib.parse
from bs4 import BeautifulSoup as BS
from lxml import html
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from internal.data.adjectives import adjectives
from internal.stand_image_generator import stand_gen

class Games(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)
        
    # Generate Stats for the Stand command
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
    # It will play an animation of an emoji splitting apart to reveal a random other emoji
    # Provided a server has appropriately named emoji it will work.
    @commands.command(aliases=["tb", "TB", "Tb"])
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def trollbox(self, ctx):
        left_side = Helpers.FindEmoji(self,ctx, "longtroll3")
        right_side = Helpers.FindEmoji(self,ctx, "longtroll1")
        try:
            # If the server has appropriately named emoji
            if left_side is not None and right_side is not None:
                # Select a prize
                prize = random.choice(ctx.guild.emojis)
                # Prepare the formatted emoji strings
                left_side_string = f'<:{left_side.name}:{left_side.id}>'
                right_side_string = f'<:{right_side.name}:{right_side.id}>'                                
                if prize.animated == True:
                    prize_string = f'<a:{prize.name}:{prize.id}>'
                else:
                    prize_string = f'<:{prize.name}:{prize.id}>'
                # Prepare each of the messages - The first will be sent, and then the message will be edited to each subsequent message in order
                message_one = f'{left_side_string}{right_side_string}'
                message_two = f'{left_side_string}    {right_side_string}'
                message_three = f'{left_side_string} :sparkles: {right_side_string}'
                message_four = f'{left_side_string} {prize_string} {right_side_string}'
                # Create a task to send the first message
                task_one = asyncio.create_task(ctx.send(message_one))
                # Await the message send completion, and then sleep for 1 second
                await task_one
                await asyncio.sleep(1)
                # Create a new task to edit the result of the first task with the content of message two
                task_two = asyncio.create_task(task_one.result().edit(content=message_two))
                # Await and then sleep for 0.2 seconds
                await task_two
                await asyncio.sleep(0.2)
                # Repeat as above for messages three and four
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
        split_message = Helpers.CommandStrip(self, ctx.message.content).split(' ')
        amount = Helpers.FuzzyIntegerSearch(self, split_message[0])
        if amount == None:
            amount = 1
        else:
            split_message = split_message[1:]
        if len(split_message) == 0:
            split_message.append(ctx.message.author.display_name)
        elif split_message[0] == '':
            split_message = [f"{ctx.message.author.display_name}"]
        if amount > 0:
            if amount > 10:
                amount = 10
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
            random_power = Helpers.GetWebPage(self, api_url, params)
            if random_power:
                power = random_power.json()["query"]["random"][0]
                name = power["title"]
                encoded_url = f'https://powerlisting.fandom.com/wiki/{urllib.parse.quote(name)}'
                power_data = Helpers.GetWebPage(self, encoded_url)
                if power_data:
                    page_tree = html.fromstring(power_data.text)
                    desc = page_tree.xpath('//meta[@name="description"]/@content')
                    readable_url = urllib.parse.unquote(encoded_url).replace(" ", "_")
                    if len(desc) > 0:
                        response = f'{ctx.message.author.mention}: **Power:** {name}\n**Description:** {base_html.unescape(desc[0].strip())}\n<{readable_url}>'
                    else:
                        response = f'{ctx.message.author.mention}: **Power:**{name}\n<{readable_url}>'
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
        random_power = Helpers.GetWebPage(self, power_api_url, params)            
        random_music = Helpers.GetWebPage(self, music_api_url, params)
        if random_power and random_music:
            power = random_power.json()["query"]["random"][0]
            pow_name = power["title"]
            pow_url = f'https://powerlisting.fandom.com/wiki/{urllib.parse.quote(pow_name)}'
            music = random_music.json()["query"]["random"][0]
            music_name = music["title"].split(',')[0]
            music_name = music_name.split('List of ')[0]
            music_name = music_name.split('(')[0]
            if len(music_name.split(':')) > 1:
                r = random.randint(0,10)
                if r >= 3:
                    music_name = music_name.split(':')[1]
                else:
                    music_name = music_name.split(':')[0]
            else:
                music_name = music_name.split(':')[0]
            if music_name == "Lyrics":
                music_name = music["title"].split(':')[1]
            power_data = Helpers.GetWebPage(self, pow_url)
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
                    if len(ctx.guild.members) >= 200:
                        stand_embed.set_thumbnail(url="attachment://stand.png")
                    else:
                        stand_embed.set_image(url="attachment://stand.png")
                    stand_embed.set_author(name=f'{ctx.message.author.display_name}\'s Stand')
                    stand_embed.title = f'**「{music_name}」**'
                    if len(desc) > 0:
                        stand_embed.description = f"It has the ability: **[{pow_name}]({pow_url})**\n{base_html.unescape('.'.join(desc[0].split('.')[0:2]))}"
                    else:
                        stand_embed.description = f"It has the ability: **[{pow_name}]({pow_url})**"
                    sent = await ctx.send(file=image_file, embed=stand_embed)
                    if len(ctx.guild.members) <= 200: # temporarily disabled as it isnt necessary
                        await asyncio.sleep(10)
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

    @commands.command(help="Fuse two user's names.", aliases=['nf', 'NF', 'Nf'])
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def namefuse(self, ctx):
        members = ctx.guild.members
        if len(members) > 1:
            if Helpers.CommandStrip(self, ctx.message.content).split(' ')[0].lower() == 'online':
                depth = 0
                while True:                
                    name1 = random.choice(members)
                    if name1.status != discord.Status.offline:
                        depth = 0
                        break
                    depth += 1
                    if depth > 100:
                        await ctx.send(f'{ctx.message.author.mention}: Could not find enough valid members.')
                        return
                while True:
                    name2 = random.choice(members)
                    if name1 != name2 and name2.status != discord.Status.offline:
                        depth = 0
                        break
                    depth += 1
                    if depth > 100:
                        await ctx.send(f'{ctx.message.author.mention}: Could not find enough valid members.')
                        return
            else:            
                name1 = random.choice(members)
                while True:
                    name2 = random.choice(members)
                    if name1 != name2:
                        depth = 0
                        break
                    depth += 1
                    if depth > 100:
                        await ctx.send(f'{ctx.message.author.mention}: Could not find enough valid members.')
                        return
                    
            if random.randint(0,1) == 0:
                name1 = name1.name.lower()
            else:
                name1 = name1.display_name.lower()

            if random.randint(0,1) == 0:
                name2 = name2.name.lower()
            else:
                name2 = name2.display_name.lower()
            
            name1parts = [name1[:len(name1)//2],name1[len(name1)//2:]]
            name2parts = [name2[:len(name2)//2],name2[len(name2)//2:]]
            roll = random.randint(0,1)
            if roll == 0:

                name = name1parts[0] + name2parts[1]
            else:
                name = name2parts[0] + name1parts[1]

            await ctx.send(f'{ctx.message.author.mention}: {name.title()}')

    @commands.command(aliases=["tvt", "TVT"], help="Get a random TVTropes page.")    
    @commands.cooldown(rate=1, per=7, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def tvtropes(self, ctx):
        try:            
            await ctx.trigger_typing()
            page = Helpers.GetWebPage(self, "https://tvtropes.org/pmwiki/randomitem.php?p=1")
            if page:
                soup = BS(page.content, "lxml")
                url = soup.find('meta', {"property":"og:url"})['content']
                response = f'{ctx.message.author.mention}: {url}'
            else:
                response = f'{ctx.message.author.mention}: Couldn\'t get TVTropes page.'
            await ctx.send(response)
        except Exception as ex:
            logger.LogPrint("IMAGE ERROR", logging.CRITICAL, ex)
            await ctx.send(f'{ctx.message.author.mention}: Something went wrong getting TVTropes page.')

    
    @commands.command(aliases=["ae", "aes", "Aesthetic"], help="By request - Get a random aesthetic wiki page.")    
    @commands.cooldown(rate=1, per=7, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def aesthetic(self, ctx):
        try:
            await ctx.trigger_typing()
            api_url = 'https://aesthetics.fandom.com/api.php'
            params = {
                "action": "query",
                "list": "random",
                "rnnamespace": "0",
                "rnlimit": "1",
                "format": "json"
            }
            random_aesthetic = Helpers.GetWebPage(self, api_url, params)
            if random_aesthetic:
                aesthetic = random_aesthetic.json()["query"]["random"][0]
                name = aesthetic["title"]
                encoded_url = f'https://aesthetics.fandom.com/wiki/{urllib.parse.quote(name)}'
                aesthetic_data = Helpers.GetWebPage(self, encoded_url)
                if aesthetic_data:
                    page_tree = html.fromstring(aesthetic_data.text)
                    desc = page_tree.xpath('//meta[@name="description"]/@content')
                    readable_url = urllib.parse.unquote(encoded_url).replace(" ", "_")
                    if len(desc) > 0:
                        response = f'{ctx.message.author.mention}: **Aesthetic:** {name}\n**Description:** {base_html.unescape(desc[0].strip())}\n<{readable_url}>'
                    else:
                        response = f'{ctx.message.author.mention}: **Aesthetic:**{name}\n<{readable_url}>'
                else:
                    response = f'{ctx.message.author.mention}: Couldn\'t get Aesthetic info.'
            else:
                response = f'{ctx.message.author.mention}: Couldn\'t get Aesthetic info.'
            await ctx.send(response)
        except Exception as ex:
            logger.LogPrint(ex, logging.ERROR)

    @commands.command(aliases=["rwiki", "rfandom"], help="By request - Get a random wiki page on any specified fandom wiki.")    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomfandom(self, ctx):
        try:
            await ctx.trigger_typing()
            query = Helpers.CommandStrip(self, ctx.message.content).split(' ')[0]
            if len(query) <= 0:
                response = f'{ctx.message.author.mention}: Please specify a fandom wiki.'
            else:
                api_url = f'https://{query}.fandom.com/api.php'
                params = {
                    "action": "query",
                    "list": "random",
                    "rnnamespace": "0",
                    "rnlimit": "1",
                    "format": "json"
                }
                random_aesthetic = Helpers.GetWebPage(self, api_url, params)
                if random_aesthetic:
                    try:
                        power = random_aesthetic.json()["query"]["random"][0]
                        name = power["title"]
                        encoded_url = f'https://{query}.fandom.com/wiki/{urllib.parse.quote(name)}'
                        power_data = Helpers.GetWebPage(self, encoded_url)
                        if power_data:
                            page_tree = html.fromstring(power_data.text)
                            desc = page_tree.xpath('//meta[@name="description"]/@content')
                            readable_url = urllib.parse.unquote(encoded_url).replace(" ", "_")
                            if len(desc) > 0:
                                response = f'{ctx.message.author.mention}: **Title:** {name}\n**Description:** {base_html.unescape(urllib.parse.unquote(desc[0].strip()))}\n<{readable_url}>'
                            else:
                                response = f'{ctx.message.author.mention}: **Title:**{name}\n<{readable_url}>'
                        else:
                            response = f'{ctx.message.author.mention}: Couldn\'t get info.'
                    except Exception as ex:
                        response = f'{ctx.message.author.mention}: Couldn\'t contact {query} wiki.\nCheck you entered a fandom wiki that actually exists!\nIf you\'re sure it exists, then they likely have the API turned off.'
                else:
                    response = f'{ctx.message.author.mention}: Couldn\'t contact {query} wiki.\nCheck you entered a fandom wiki that actually exists!'
            await ctx.send(response)
        except Exception as ex:
            logger.LogPrint(ex, logging.ERROR)

def setup(client):
    client.add_cog(Games(client))