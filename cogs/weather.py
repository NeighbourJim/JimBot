import discord
import logging
import json
import pycountry
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.helpers import Helpers
from internal.logs import logger
from bot import current_settings

class Weather(commands.Cog):

    def __init__(self, client):
        self.client = client

    def ConvertCtoF(self, value):
        return round(((value * 9/5) + 32))

    def ConvertKtoC(self, value):
        return round(value - 273.15)

    def CountryCodeToName(self, ccode):
        return pycountry.countries.lookup(ccode).name

    @commands.command(aliases=["weather", "w"], help="Get the current weather for a specific location.\nUsage: !weather location. For example !weather London or !weather London,uk")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def Weather(self, ctx):
        await ctx.trigger_typing()
        city = Helpers.CommandStrip(self, ctx.message.content)
        if len(city.strip()) > 0:
            api_url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={current_settings["keys"]["open_weather_key"]}'
            api_results = Helpers.GetWebPage(self, api_url)
            if api_results:
                api_results = api_results.json()
                if api_results["cod"] == 200:
                    name = api_results["name"]
                    country = self.CountryCodeToName(api_results["sys"]["country"])
                    weather = api_results["weather"][0]["description"].title()
                    icon = f'http://openweathermap.org/img/wn/{api_results["weather"][0]["icon"]}@2x.png'
                    tempC = self.ConvertKtoC(api_results["main"]["temp"])
                    minC = self.ConvertKtoC(api_results["main"]["temp_min"])
                    maxC = self.ConvertKtoC(api_results["main"]["temp_max"])
                    humidity = api_results["main"]["humidity"]
                    wind_speed = round(float(api_results["wind"]["speed"]) * 3.6, 2)

                    weather_embed = discord.Embed()
                    weather_embed.title = f'Current Weather in {name}, {country}'
                    weather_embed.set_thumbnail(url=icon)
                    weather_embed.add_field(name='Temperature', value=f'**Current:** {tempC}°C ({self.ConvertCtoF(tempC)}°F)\n**Min:** {minC}°C ({self.ConvertCtoF(minC)}°F)\n**Max:** {maxC}°C ({self.ConvertCtoF(maxC)}°F)', inline=False)
                    weather_embed.add_field(name='Weather Type', value=f'{weather}', inline=True)
                    weather_embed.add_field(name='Humidity', value=f"{humidity}%", inline=True)
                    weather_embed.add_field(name='Wind Speed', value=f"{wind_speed} km/h", inline=True)
                    weather_embed.set_footer(text=f'Retrieved from OpenWeatherMap.org for {ctx.message.author.name}')
                    await ctx.send(embed=weather_embed)
                elif api_results["cod"] == 404:
                    await ctx.send(f'{ctx.message.author.mention}: ERROR {api_results["cod"]}\nWeather for City \'{city}\' does not exist.')
                else:
                    await ctx.send(f'{ctx.message.author.mention}: ERROR {api_results["cod"]}\nWeather could not be retrieved.')
            else:
                logger.LogPrint(f"Error contacting OpenWeather API. - API Results:{api_results}", logging.ERROR)
                await ctx.send(f'{ctx.message.author.mention}: API Error.\nPlease specify a City. Eg ``!weather London`` or ``!weather London,UK``')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Please specify a City. Eg ``!weather London`` or ``!weather London,UK``.')


def setup(client):
    client.add_cog(Weather(client))