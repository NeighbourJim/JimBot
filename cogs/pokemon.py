import discord
import json
import logging
import random
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from internal.data.pokemon_names import pokemon_names

class Pokemon(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(help="Get a random Pokemon.", aliases=["rmon", "RMon", "Rmon", "RMON"])
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randompokemon(self, ctx):
        pokemon_count = 890
        shiny_rarity = 1365
        poke_num = random.randint(1, pokemon_count)
        shiny = random.randint(1,shiny_rarity)
        poke_name = pokemon_names[poke_num]
        if poke_num < 10:
            poke_num_string = f'00{poke_num}'
        elif poke_num < 100:
            poke_num_string = f'0{poke_num}'
        else:
            poke_num_string = str(poke_num)
        if shiny == shiny_rarity:
            if poke_num < 810:
                url = f'https://www.serebii.net/Shiny/SWSH/{poke_num_string}.png'
            else:
                url = f'https://www.serebii.net/Shiny/SWSH/{poke_num_string}.png'
            message = f'**{poke_num} - :sparkles:{poke_name}:sparkles:**\n{url}'
        else:
            if poke_num < 810:
                url = f'https://www.serebii.net/swordshield/pokemon/{poke_num_string}.png'
            else:
                url = f'https://www.serebii.net/swordshield/pokemon/{poke_num_string}.png'
            message = f'**{poke_num_string} - {poke_name}**\n{url}'
        await ctx.send(f'{ctx.message.author.mention}: {message}')

    @commands.command(help="Get a random Pokemon move.", aliases=['rmove', 'Rmove', 'RMove', 'RMOVE'])
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randommove(self, ctx):
        api_results = Helpers.GetWebPage(self, 'https://pokeapi.co/api/v2/move/?offset=0&limit=20000')
        if api_results:
            move = random.choice(api_results.json()['results'])['name']
            move = move.title().replace("-", " ")
            await ctx.send(f'{ctx.message.author.mention}: {move}')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Something went wrong when contacting the API.')

    @commands.command(help="Get a random Pokemon ability.", aliases=['rability', 'Rability', 'RAbility', 'RABILITY'])
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomability(self, ctx):
        api_results = Helpers.GetWebPage(self, 'https://pokeapi.co/api/v2/ability/?offset=0&limit=20000')
        if api_results:
            ability = random.choice(api_results.json()['results'])['name']
            ability = ability.title().replace("-", " ")
            await ctx.send(f'{ctx.message.author.mention}: {ability}')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Something went wrong when contacting the API.')

    @commands.command(help="Get a random Pokemon item.", aliases=['ritem', 'Ritem', 'RItem', 'RITEM'])
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomitem(self, ctx):
        api_results = Helpers.GetWebPage(self, 'https://pokeapi.co/api/v2/item/?offset=0&limit=485')
        if api_results:
            item = random.choice(api_results.json()['results'])['name']
            item = item.title().replace("-", " ")
            await ctx.send(f'{ctx.message.author.mention}: {item}')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Something went wrong when contacting the API.')

    @commands.command(help="Get information about a Pokemon (Gen 1 - 7).", aliases=['pdt', 'Pdt', 'PDT', 'pdata', 'pd'])
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def pokedata(self, ctx):
        poke = Helpers.CommandStrip(self, ctx.message.content).replace(' ', '-')
        api_results = Helpers.GetWebPage(self, f'https://pokeapi.co/api/v2/pokemon/{poke}/')
        if api_results:
            results_json = api_results.json()
            name = results_json['name'].title()
            number = results_json['id']
            if number < 100:
                number_string = f'0{number}'
            else:
                number_string = str(number)
            sprite = results_json['sprites']['front_default']

            abilities = results_json['abilities']
            abilities_formatted = []
            for a in reversed(abilities):
                ab_str = ''
                ab_str += f"{a['ability']['name'].title().replace('-', ' ')}"
                if a['is_hidden']:
                    ab_str += ' (Hidden)'
                abilities_formatted.append(ab_str)                
            
            typing = results_json['types']
            typing_formatted = []
            for t in reversed(typing):
                typing_formatted.append(t['type']['name'].title())
            
            stats = results_json['stats']                     # API stat order is Spe, SpD, SpA, Def, Atk, HP
            poke_embed = discord.Embed()
            poke_embed.title = f'{name.title()} - #{number}'
            if sprite != None:
                poke_embed.set_thumbnail(url=sprite)
            poke_embed.add_field(name='Type', value=' / '.join(typing_formatted), inline=True)
            poke_embed.add_field(name='Abilities', value=', '.join(abilities_formatted), inline=False)
            poke_embed.add_field(name='Base', value=(
                f"**HP:** {stats[5]['base_stat']}\n"
                f"**ATK:** {stats[4]['base_stat']}\n"
                f"**DEF:** {stats[3]['base_stat']}\n"
                ), inline=True)
            poke_embed.add_field(name='Stats', value=(
                f"**SP.ATK:** {stats[2]['base_stat']}\n"
                f"**SP.DEF:** {stats[1]['base_stat']}\n"
                f"**SPE:** {stats[0]['base_stat']}\n"
            ), inline=True)
            poke_embed.set_footer(text=f'More info: https://pokemondb.net/pokedex/{poke}')
            await ctx.send(embed=poke_embed)
            
        else:
            await ctx.send(f'{ctx.message.author.mention}: No pokemon with that name or number found.')
    
    @commands.command(help="Generate a Pokemon name.", aliases=['rname', 'RName', 'Rname'])
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomname(self, ctx):
        # Generate Name
        name1 = random.choice(pokemon_names).lower()
        name2 = random.choice(pokemon_names).lower()

        roll = random.randint(0,3)
        if roll == 0:
            name = name1[:len(name1)//2] + name2[len(name2)//2:]
        elif roll == 1:
            name = name1[len(name1)//2:] + name2[:len(name2)//2]
        elif roll == 2:
            name = name2[len(name2)//2:] + name1[:len(name1)//2]
        elif roll == 3:
            name = name2[:len(name2)//2] + name1[len(name1)//2:]
        name = name.title()

        await ctx.send(f'{ctx.message.author.mention}: {name}')

    @commands.command(help="Generate an entirely random new Pokemon.", aliases=['gpoke', 'genpoke', 'GPoke', 'Genpoke', 'gmon'])
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def generatepokemon(self, ctx):
        types = ['normal','fire','water','grass','fighting','flying','poison','electric','ground','psychic','rock','ice','bug','dragon','ghost','dark','steel','fairy']
        stats = []

        await ctx.trigger_typing()

        # Generate Name
        name1 = random.choice(pokemon_names).lower()
        while True:
            name2 = random.choice(pokemon_names).lower()
            if name1 != name2:
                break

        roll = random.randint(0,3)
        if roll == 0:
            name = name1[:len(name1)//2] + name2[len(name2)//2:]
        elif roll == 1:
            name = name1[len(name1)//2:] + name2[:len(name2)//2]
        elif roll == 2:
            name = name2[len(name2)//2:] + name1[:len(name1)//2]
        elif roll == 3:
            name = name2[:len(name2)//2] + name1[len(name1)//2:]
        name = name.title()


        # Generate Typing
        if random.randint(0,100) <= 40:
            # single typed
            typing = random.choice(types).title()
        else:
            # dual typed
            t1 = random.choice(types).title()
            while True:
                t2 = random.choice(types).title()
                if t1 != t2:
                    break
            typing = f'{t1}/{t2}'

        # Generate Stats 
        stats = []
        min_base_bst = 300
        max_base_bst = 720
        # get a random base total to use
        base_bst = random.randint(min_base_bst,max_base_bst)
        # decide the stat weight
        # clamped float value between 0.8 and 1.0, varying based on the base total
        # higher base totals will tend to have higher stat weight
        # On average (over 10000 runs) this process should result in an average BST of about 460, min 180, max 725.
        stat_weight = round(max(min((base_bst / max_base_bst) * 1.5, 1.0), 0.8), 2)
        for i in range(6):
            stat = random.randint(100,200) + random.randint(-50, 55)
            if stat > 255:
                stat = 255
            if stat < 5:
                stat = 5
            # subtract the stat from the remaining stat total, multiplying by stat weight
            # doing this should get more relatively accurate stat spreads ON AVERAGE (you can still end up with absolutely pathetic stats)
            base_bst -= round(stat * stat_weight)
            if base_bst < 50:
                stat = random.randint(25,50)
            stats.append(stat)
        random.shuffle(stats)
        stat_total = sum(stats)

        # Generate Abilities
        api_results = Helpers.GetWebPage(self, 'https://pokeapi.co/api/v2/ability/?offset=0&limit=233')
        if api_results:
            ability1 = random.choice(api_results.json()['results'])['name']
            ability1 = ability1.title().replace("-", " ")
            while True:
                ability2 = random.choice(api_results.json()['results'])['name']
                ability2 = ability2.title().replace("-", " ")

                ability3 = random.choice(api_results.json()['results'])['name']
                ability3 = ability3.title().replace("-", " ")

                if ability1 != ability2 != ability3:
                    break
        else:
            await ctx.send(f'{ctx.message.author.mention}: Something went wrong when contacting the API.')
            return

        poke_embed = discord.Embed()
        poke_embed.title = f'{name}'
        poke_embed.add_field(name='Type', value=typing, inline=True)
        poke_embed.add_field(name='Abilities', value=f'{ability1}, {ability2}, {ability3} (Hidden)', inline=False)
        poke_embed.add_field(name=f'BST: {stat_total}', value=(
            f"**HP:** {stats[0]}\n"
            f"**ATK:** {stats[1]}\n"
            f"**DEF:** {stats[2]}\n"
            ), inline=True)
        poke_embed.add_field(name=f'Stats', value=(
            f"**SP.ATK:** {stats[3]}\n"
            f"**SP.DEF:** {stats[4]}\n"
            f"**SPE:** {stats[5]}\n"
        ), inline=True)
        poke_embed.set_footer(text=f'Generated for {ctx.message.author.name}')
        await ctx.send(embed=poke_embed)
        

        


def setup(client):
    client.add_cog(Pokemon(client))