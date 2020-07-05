import discord
import logging
import json
import pycountry
import datetime
from discord.ext import commands
from discord.ext.commands import BucketType
from os import path

from internal.helpers import Helpers
from internal.databasemanager import dbm
from internal.logs import logger
from bot import current_settings

class Weather(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db_folder = "./internal/data/databases/"
        self.CheckAndCreateDatabase()

    def CheckAndCreateDatabase(self):
        """Check if a meme database has been made for each server the bot is connected to, and create it if not.
        """
        try:
            guilds = self.client.guilds
            for g in guilds:
                filename = f"weather{g.id}"
                if not path.exists(f'{self.db_folder}{filename}.db'):
                    # Create the required tables
                    columns = {"uid": "integer", "location": "text NOT NULL"}
                    dbm.CreateTable(filename, "w_locs", columns)
                    
        except Exception as ex:
            logger.LogPrint(f'ERROR - Could not create table or view: {ex}',logging.ERROR)    

    def ConvertCtoF(self, value):
        return round(((value * 9/5) + 32))

    def ConvertKtoC(self, value):
        return round(value - 273.15)

    def CountryCodeToName(self, ccode):
        return pycountry.countries.lookup(ccode).name

    def IconToEmoji(self, icon_code):
        if icon_code.startswith('01'):
            return ":sunny:"
        if icon_code.startswith('02'):
            return ":partly_sunny:"
        if icon_code.startswith('03'):
            return ":cloud:"
        if icon_code.startswith('04'):
            return ":cloud:"
        if icon_code.startswith('09'):
            return ":cloud_rain:"
        if icon_code.startswith('10'):
            return ":cloud_rain:"
        if icon_code.startswith('11'):
            return ":thunder_cloud_rain:"
        if icon_code.startswith('13'):
            return ":cloud_snow:"
        if icon_code.startswith('50'):
            return ":fog:"
        else:
            return ":person_shrugging:"

    @commands.command(aliases=["weather", "w"], help="Get the current weather for a specific location.\nUsage: !weather location. For example !weather London or !weather London,uk")    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def Weather(self, ctx):
        filename = f"weather{ctx.guild.id}"        

        await ctx.trigger_typing()
        city = Helpers.CommandStrip(self, ctx.message.content)
        if len(city.strip()) == 0:
            user_location = dbm.Retrieve(filename, "w_locs", where=[("uid", ctx.message.author.id)], column_data=["location"])
            if len(user_location) > 0:
                city = user_location[0][0]
            else:
                city = None
        if city != None:            
            api_url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={current_settings["keys"]["open_weather_key"]}'
            api_results = Helpers.GetWebPage(self, api_url)
            if api_results:
                api_results = api_results.json()
                name = api_results["name"]
                country = self.CountryCodeToName(api_results["sys"]["country"])
                weather = api_results["weather"][0]["description"].title()
                icon = f'http://openweathermap.org/img/wn/{api_results["weather"][0]["icon"]}@4x.png'
                tempC = self.ConvertKtoC(api_results["main"]["temp"])
                minC = self.ConvertKtoC(api_results["main"]["temp_min"])
                maxC = self.ConvertKtoC(api_results["main"]["temp_max"])
                humidity = api_results["main"]["humidity"]
                wind_speed = round(float(api_results["wind"]["speed"]) * 3.6, 2)

                weather_embed = discord.Embed()
                weather_embed.title = f'Current Weather in {name}, {country}'
                weather_embed.set_thumbnail(url=icon)
                weather_embed.add_field(name='Temperature', value=f'{tempC}°C ({self.ConvertCtoF(tempC)}°F)', inline=False)
                weather_embed.add_field(name='Weather Type', value=f'{weather}', inline=True)
                weather_embed.add_field(name='Humidity', value=f"{humidity}%", inline=True)
                weather_embed.add_field(name='Wind Speed', value=f"{wind_speed} km/h", inline=True)
                weather_embed.set_footer(text=f'Retrieved from OpenWeatherMap.org for {ctx.message.author.name}')
                await ctx.send(embed=weather_embed)
            else:
                logger.LogPrint(f"Error contacting OpenWeather API. - API Results:{api_results}", logging.ERROR)
                await ctx.send(f'{ctx.message.author.mention}: API Error.\nCould not find weather for \'{city}\'.')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Please specify a City. Eg ``!weather London`` or ``!weather London,UK``.\nAlternatively, set your default location with ``!setweatherlocation city``.')

    @commands.command(aliases=["forecast", "weatherforecast", "wf"], help="Get the 4 day forecast for a location.")
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def WeatherForecast(self, ctx):
        filename = f"weather{ctx.guild.id}"       

        await ctx.trigger_typing()
        city = Helpers.CommandStrip(self, ctx.message.content)
        if len(city.strip()) == 0:
            user_location = dbm.Retrieve(filename, "w_locs", where=[("uid", ctx.message.author.id)], column_data=["location"])
            if len(user_location) > 0:
                city = user_location[0][0]
            else:
                city = None
        if city != None:
            api_url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={current_settings["keys"]["open_weather_key"]}'
            api_results = Helpers.GetWebPage(self, api_url).json()
            if api_results:
                data_list = api_results["list"]
                days_unformatted = []
                day_periods = []
                days_formatted = []
                today = datetime.date.today()
                for t_period in data_list:
                    date = datetime.datetime.strptime(t_period["dt_txt"].split(" ")[0], '%Y-%m-%d').date()
                    if date > today:
                        if len(day_periods) > 0:
                            if date == datetime.datetime.strptime(day_periods[0]["dt_txt"].split(" ")[0], '%Y-%m-%d').date():
                                day_periods.append(t_period)
                            else:
                                days_unformatted.append(day_periods)
                                day_periods = []
                                day_periods.append(t_period)
                        else:
                            day_periods.append(t_period)
                name = api_results["city"]["name"]
                country = self.CountryCodeToName(api_results["city"]["country"])
                for day in days_unformatted:
                    minC = 10000
                    maxC = -10000
                    weather_icon = day[len(day)//2]["weather"][0]["icon"]
                    weather_type = day[len(day)//2]["weather"][0]["description"].title()
                    humidity = day[len(day)//2]["main"]["humidity"]
                    wind = round(day[len(day)//2]["wind"]["speed"] * 3.6,1)
                    date = datetime.datetime.strptime(day[0]["dt_txt"].split(" ")[0], '%Y-%m-%d').date()
                    for t_period in day:
                        if self.ConvertKtoC(t_period["main"]["temp"]) < minC:
                            minC = self.ConvertKtoC(t_period["main"]["temp"])
                        if self.ConvertKtoC(t_period["main"]["temp"]) > maxC:
                            maxC = self.ConvertKtoC(t_period["main"]["temp"])
                    day_data = {"min": minC, "max": maxC, "weather_icon": weather_icon, "weather_type": weather_type, "date": date, "humidity": humidity, "wind": wind}
                    days_formatted.append(day_data)
                weather_embed = discord.Embed()
                weather_embed.title = f'4-Day Forecast for {name}, {country}'
                for day in days_formatted:
                    weather_embed.add_field(name=f'__{day["date"].strftime("%d/%m")}__', value=f'**{day["weather_type"]}** {self.IconToEmoji(day["weather_icon"])}\n**Min:** {day["min"]}°C ({self.ConvertCtoF(day["min"])}°F)\n**Max:** {day["max"]}°C ({self.ConvertCtoF(day["max"])}°F)\n**Wind:** {day["wind"]} km/h\n**Humidity:** {day["humidity"]}%', inline=True)
                weather_embed.set_footer(text=f'Retrieved from OpenWeatherMap.org for {ctx.message.author.name}')
                await ctx.send(embed=weather_embed)
            else:
                logger.LogPrint(f"Error contacting OpenWeather API. - API Results:{api_results}", logging.ERROR)
                await ctx.send(f'{ctx.message.author.mention}: API Error.\nCould not find forecast for \'{city}\'.')
        else:
            await ctx.send(f'{ctx.message.author.mention}: Please specify a City. Eg ``!forecast London`` or ``!forecast London,UK``.\nAlternatively, set your default location with ``!setweatherlocation city``.')


    @commands.command(aliases=["setweatherlocation"], help="Set your location for the !weather command.\nDO NOT USE IF YOU DO NOT WANT YOUR LOCATION TIED TO YOUR DISCORD ID\nUsage: !setweatherlocation location. For example !setweatherlocation London or !setweatherlocation London,uk")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def SetWeatherLocation(self, ctx):
        filename = f"weather{ctx.guild.id}"
        location = Helpers.CommandStrip(self, ctx.message.content)
        data = {"uid": ctx.message.author.id, "location": location}
        try:
            dbm.Delete(filename, "w_locs", where={"uid": ctx.message.author.id})
            dbm.Insert(filename, "w_locs", data)
            await ctx.send(f'{ctx.message.author.mention}: Set your default location to {location}')
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute SetWeatherLocation command: {ex}',logging.ERROR)     


def setup(client):
    client.add_cog(Weather(client))