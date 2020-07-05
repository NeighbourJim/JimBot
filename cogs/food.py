import discord
import logging
import random
import json
import html
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from bot import current_settings

class Food(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["rrecipe", "Randomrecipe", "rfood", "rr"], help="Get a random recipe.")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomrecipe(self, ctx):
        await ctx.trigger_typing()
        url = f'https://api.spoonacular.com/recipes/random?apiKey={current_settings["keys"]["spoonacular_key"]}'
        api_results = Helpers.GetWebPage(self, url)
        if api_results:
            api_results = api_results.json()
            food_embed = discord.Embed()
            food_embed.title = html.unescape(f'{api_results["recipes"][0]["title"]}')
            if "image" in api_results["recipes"][0].keys():
                food_embed.set_thumbnail(url=api_results["recipes"][0]["image"])
            food_embed.description = f'[Full Recipe]({api_results["recipes"][0]["sourceUrl"]})'
            if "dishTypes" in api_results["recipes"][0].keys():
                    if len(api_results["recipes"][0]["dishTypes"]) > 0:
                        food_embed.add_field(name="__Dish Type(s)__", value=f'{" / ".join(api_results["recipes"][0]["dishTypes"]).title()}', inline=False)  
            if "cuisines" in api_results["recipes"][0].keys():
                        if len(api_results["recipes"][0]["cuisines"]) > 0:
                            food_embed.add_field(name="__Cuisine(s)__", value=f'{" / ".join(api_results["recipes"][0]["cuisines"]).title()}', inline=False) 
            if "readyInMinutes" in api_results["recipes"][0].keys():
                    food_embed.add_field(name="__Ready In__", value=f'{api_results["recipes"][0]["readyInMinutes"]} min(s).', inline=True)
            if "servings" in api_results["recipes"][0].keys():
                    food_embed.add_field(name="__Servings__", value=f'{api_results["recipes"][0]["servings"]}', inline=True)
            food_embed.set_footer(text=f'Random Recipe retrieved from Spoonacular API for {ctx.message.author.name}.')
            await ctx.send(embed=food_embed)
        else:
            await ctx.send(f'{ctx.message.author.mention}: API Error.\nCould not contact Spoonacular API.\nLikely exceeded the free daily quota, which resets at Midnight UTC.')

    @commands.command(aliases=["rs", "Recipesearch", "sfood", "rsearch"], help="Search for a recipe with a keyword.\nKeywords: ``cuisine, ingredient, diet``.\nUsage: Specify a keyword and then search query, or a search query on its own.\nFor Example: ``!recipesearch Burger``, ``!recipesearch cuisine spanish``, ``!recipesearch ingredient beef``.")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def recipesearch(self, ctx):
        await ctx.trigger_typing()
        keywords = ["cuisine", "ingredient", "diet"]
        split_message = Helpers.CommandStrip(self, ctx.message.content).split(' ')
        if split_message[0].lower() in keywords and len(split_message) > 1:
            user_kw = split_message.pop(0).lower()
            if user_kw == "ingredient":
                user_kw = "includeIngredients"
            query = " ".join(split_message)
        else:
            user_kw = "query"
            query = Helpers.CommandStrip(self, ctx.message.content)
        if len(query.strip()) > 0:
            url = f'https://api.spoonacular.com/recipes/complexSearch?{user_kw}={query}&number=1&offset={random.randint(0,10)}&addRecipeInformation=true&apiKey={current_settings["keys"]["spoonacular_key"]}'
            api_results = Helpers.GetWebPage(self, url)
            if api_results:
                api_results = api_results.json()
                if len(api_results["results"]) > 0:
                    recipe = random.choice(api_results["results"])
                    food_embed = discord.Embed()
                    food_embed.title = html.unescape(f'{recipe["title"]}')
                    if "image" in recipe.keys():
                        food_embed.set_thumbnail(url=recipe["image"])
                    food_embed.description = f'[Full Recipe]({recipe["sourceUrl"]})'
                    if "dishTypes" in recipe.keys():
                        if len(recipe["dishTypes"]) > 0:
                            food_embed.add_field(name="__Dish Type(s)__", value=f'{" / ".join(recipe["dishTypes"]).title()}', inline=False)
                    if "cuisines" in recipe.keys():
                        if len(recipe["cuisines"]) > 0:
                            food_embed.add_field(name="__Cuisine(s)__", value=f'{" / ".join(recipe["cuisines"]).title()}', inline=False)  
                    if "readyInMinutes" in recipe.keys():
                        food_embed.add_field(name="__Ready In__", value=f'{recipe["readyInMinutes"]} min(s).', inline=True)
                    if "servings" in recipe.keys():
                        food_embed.add_field(name="__Servings__", value=f'{recipe["servings"]}', inline=True)
                    food_embed.set_footer(text=f'Recipe including \'{query}\' retrieved from Spoonacular API for {ctx.message.author.name}.')
                    await ctx.send(embed=food_embed)
                else:
                    await ctx.send(f'{ctx.message.author.mention}: No results for \'{query}\'.')
            else:
                await ctx.send(f'{ctx.message.author.mention}: API Error.\nCould not contact Spoonacular API.\nLikely exceeded the free daily quota, which resets at Midnight UTC.')
        else:
            await ctx.send(f'{ctx.message.author.mention}: You didn\'t specify a query.')
        



def setup(client):
    client.add_cog(Food(client))