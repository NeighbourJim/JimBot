import discord
import logging
import random
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helper
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
        shiny = (random.randint(1,shiny_rarity) == shiny_rarity)
        poke_name = pokemon_names[poke_num]
        if poke_num < 100:
            poke_num_string = f'0{poke_num}'
        else:
            poke_num_string = str(poke_num)
        if shiny:
            if poke_num < 810:
                url = f'https://www.serebii.net/Shiny/SM/{poke_num_string}.png'
            else:
                url = f'https://www.serebii.net/Shiny/SWSH/{poke_num_string}.png'
            message = f'**{poke_num} - :sparkles:{poke_name}:sparkles:**\n{url}'
        else:
            if poke_num < 810:
                url = f'https://www.serebii.net/sunmoon/pokemon/{poke_num_string}.png'
            else:
                url = f'https://www.serebii.net/swordshield/pokemon/{poke_num_string}.png'
            message = f'**{poke_num} - {poke_name}**\n{url}'
        await ctx.send(f'{ctx.message.author.mention}: {message}')



def setup(client):
    client.add_cog(Pokemon(client))