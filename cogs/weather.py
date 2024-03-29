import discord
import logging
import json
import math
import pycountry
import datetime
import pytz
from discord.ext import commands
from discord.ext.commands import BucketType
from os import path

from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from internal.databasemanager import dbm
from internal.logs import logger
from bot import current_settings

class Weather(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.db_folder = "./internal/data/databases/"

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)
        
    def CheckAndCreateDatabase(self, ctx):
        """Check if a meme database has been made for each server the bot is connected to, and create it if not.
        """
        try:
            filename = f"weather{ctx.guild.id}"
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

    def GetWetBulb(self, t, h):
        #Tw = T * arctan[0.151977 * (rh% + 8.313659)^(1/2)] + arctan(T + rh%) - arctan(rh% - 1.676331) + 0.00391838 (rh%)^(3/2) arctan(0.023101 * rh%) - 4.686035
        result = t * math.atan(0.151977 * math.pow((h + 8.313659),(1.0/2.0))) + math.atan(t + h) - math.atan(h - 1.676331) + 0.00391838 * math.pow(h, 3.0/2.0) * math.atan(0.023101*h) - 4.686035
        result = round(result, 2)
        return result


    def CountryCodeToName(self, ccode):
        return pycountry.countries.lookup(ccode).name

    def GetLocalTime(self, timezone):
        utc_time = datetime.datetime.utcnow()
        converted = utc_time + datetime.timedelta(seconds=timezone)
        return converted.strftime("%H:%M")

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

    @commands.command(aliases=["tc", "TC"], help="Convert from C to F or vice versa")    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def TempConvert(self, ctx):
        split_message = Helpers.CommandStrip(self, ctx.message.content).split(' ')
        t_in = Helpers.FuzzyIntegerSearch(self, split_message[0])
        if len(split_message) > 1:  
            unit = split_message[1].lower().strip()
        else:
            if "f" in split_message[0].lower():
                unit = "f"
            else:
                unit = "c"
        if unit is not "f":
            unit = "c"
        if t_in == None:
            await ctx.reply("Please provide a value.")
            return
        if unit == "f":
            t_out = (t_in - 32) * 5.0/9.0
            t_out = round(t_out,1)
            await ctx.reply(f'{t_in}°F = {t_out}°C')
        if unit == "c":
            t_out = 9.0/5.0*t_in+32
            t_out = round(t_out,1)
            await ctx.reply(f'{t_in}°C = {t_out}°F')
        
        
        


    @commands.command(aliases=["weather", "w"], help="Get the current weather for a specific location.\nUsage: !weather location. For example !weather London or !weather London,uk")    
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def Weather(self, ctx):
        self.CheckAndCreateDatabase(ctx)

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
                wet_bulb_c = self.GetWetBulb(tempC,humidity)
                wet_bulb_f = self.ConvertCtoF(wet_bulb_c)
                wind_speed = round(float(api_results["wind"]["speed"]) * 3.6, 2)
                current_time = self.GetLocalTime(api_results["timezone"])
                data_collected_time = datetime.datetime.fromtimestamp(api_results["dt"], tz=pytz.utc)
                data_collected_time = data_collected_time + datetime.timedelta(seconds=api_results["timezone"])
                data_collected_time = data_collected_time.strftime("%H:%M")

                weather_embed = discord.Embed()
                weather_embed.title = f'Current Weather in {name}, {country}'
                weather_embed.set_thumbnail(url=icon)
                weather_embed.add_field(name=f'Temperature', value=f'{tempC}°C ({self.ConvertCtoF(tempC)}°F)', inline=False)
                weather_embed.add_field(name=f'Wet Bulb Temperature', value=f'{wet_bulb_c}°C ({wet_bulb_f}°F)', inline=False)
                weather_embed.add_field(name='Weather Type', value=f'{weather}', inline=True)
                weather_embed.add_field(name='Humidity', value=f"{humidity}%", inline=True)
                weather_embed.add_field(name='Wind Speed', value=f"{wind_speed} km/h", inline=True)
                weather_embed.set_footer(text=f'Local Time: {current_time}  |  Data collected at {data_collected_time}.')
                await ctx.reply(embed=weather_embed)
            else:
                logger.LogPrint(f"Error contacting OpenWeather API. - API Results:{api_results}", logging.ERROR)
                await ctx.reply(f'API Error.\nCould not find weather for \'{city}\'.')
        else:
            await ctx.reply(f'Please specify a City. Eg `!weather London` or `!weather London,UK`.\nAlternatively, set your default location with `!setweatherlocation city`.')

    @commands.command(aliases=["forecast", "weatherforecast", "wf"], help="Get the 4 day forecast for a location.")
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def WeatherForecast(self, ctx):
        self.CheckAndCreateDatabase(ctx)

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
            api_results = Helpers.GetWebPage(self, api_url)
            if api_results:
                api_results = api_results.json()
                data_list = api_results["list"]
                days_unformatted = []
                day_periods = []
                days_formatted = []
                today = datetime.date.today()
                for t_period in data_list:
                    date = datetime.datetime.strptime(t_period["dt_txt"].split(" ")[0], '%Y-%m-%d').date()
                    if date >= today:
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
                weather_embed.title = f'{len(days_formatted)}-Day Forecast for {name}, {country}'
                for day in days_formatted:
                    weather_embed.add_field(name=f'__{day["date"].strftime("%d/%m")}__', value=f'**{day["weather_type"]}** {self.IconToEmoji(day["weather_icon"])}\n**Min:** {day["min"]}°C ({self.ConvertCtoF(day["min"])}°F)\n**Max:** {day["max"]}°C ({self.ConvertCtoF(day["max"])}°F)\n**Wind:** {day["wind"]} km/h\n**Humidity:** {day["humidity"]}%', inline=True)
                await ctx.reply(embed=weather_embed)
            else:
                logger.LogPrint(f"Error contacting OpenWeather API. - API Results:{api_results}", logging.ERROR)
                await ctx.reply(f'API Error.\nCould not find forecast for \'{city}\'.')
        else:
            await ctx.reply(f'Please specify a City. Eg `!forecast London` or `!forecast London,UK`.\nAlternatively, set your default location with `!setweatherlocation city`.')


    @commands.command(aliases=["setweatherlocation"], help="Set your location for the !weather command.\nDO NOT USE IF YOU DO NOT WANT YOUR LOCATION TIED TO YOUR DISCORD ID\nUsage: !setweatherlocation location. For example !setweatherlocation London or !setweatherlocation London,uk")    
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def SetWeatherLocation(self, ctx):
        self.CheckAndCreateDatabase(ctx)

        filename = f"weather{ctx.guild.id}"
        location = Helpers.CommandStrip(self, ctx.message.content)
        data = {"uid": ctx.message.author.id, "location": location}
        try:
            dbm.Delete(filename, "w_locs", where={"uid": ctx.message.author.id})
            dbm.Insert(filename, "w_locs", data)
            await ctx.reply(f'Set your default location to {location}')
        except Exception as ex:
            logger.LogPrint(f'ERROR - Couldn\'t execute SetWeatherLocation command: {ex}',logging.ERROR)     


def setup(client):
    client.add_cog(Weather(client))