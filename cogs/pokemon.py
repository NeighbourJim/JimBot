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
        if poke_num < 100:
            poke_num_string = f'0{poke_num}'
        elif poke_num < 10:
            poke_num_string = f'00{poke_num}'
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
            message = f'**{poke_num} - {poke_name}**\n{url}'
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



def setup(client):
    client.add_cog(Pokemon(client))