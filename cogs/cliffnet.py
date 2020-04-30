import discord
import logging
import random
import requests
from discord.ext import commands
from discord.ext.commands import BucketType
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

from internal.logs import logger
from internal.helpers import Helper

class cliffnet(commands.Cog):

    def __init__(self, client):
        self.client = client
              
    @commands.command(aliases=["Scramble"], help="scrambles word order")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def scramble(self, ctx):
        if ctx.guild.id == 107847342006226944:
            get_message_task = asyncio.create_task(ctx.channel.fetch_message(ctx.channel.last_message_id))
            await get_message_task
            input = get_message_task.result()
            split_message = input.split(' ')
            if len(split_message) > 0:
                result = random.sample(split_message, len(split_message))
                stringResult= " "
                stringResult = stringResult.join(result)
                await ctx.send(f'{ctx.message.author.mention}: {stringResult}')
            else:
                await ctx.send(f'{ctx.message.author.mention}: Call tech support on Jims PM')


    @commands.command(aliases=["News", "n"], help="Search the recent news via a keyword! Powered by newsapi.org")  
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def command2(self, ctx):
        if ctx.guild.id == 107847342006226944:

            try:
                input = Helper.CommandStrip(ctx.message.content)
                if input=="":
                    return await ctx.send(f'Enter a keyword to search')
                    
                source = (f'http://newsapi.org/v2/everything?q={input}&sortBy=popularity&apiKey=fec0d23dd26549a9a6d58a29a675e764')
                
                pull = requests.get(source)
                articles = pull.json()["totalResults"]

                if articles == 0:
                    await ctx.send(f'{ctx.message.author.mention}: No results.')
                elif articles < 19:
                    randomId = random.randint(0,articles)
                else:
                    randomId = random.randint(0,19)
                    
                content = pull.json()["articles"][randomId]
                responseUrl = content["url"]
                if content:
                    await ctx.send(f'Result: {responseUrl}')
                else: 
                    await ctx.send(f'{ctx.message.author.mention}: No results.')
 
            except Exception as ex:
                logger.LogPrint(f'Couldn\'t get the news! - {ex}', logging.ERROR)


    @commands.command(aliases=["Movie"], help="find a random movie based on avg score from bromovies")  
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def movie(self, ctx):
        if ctx.guild.id == 107847342006226944:
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                     'bromoviessearch-08cd123a16ed.json', scope) # Your json file here
            
            gc = gspread.authorize(credentials)
            
            wks = gc.open_by_key("1MJivigtIomBZSWpTpYSCjyOuVq8XpScZ-CKdv1OOIM4") #opens sheetsfile
            worksheet = wks.worksheet("movies") #selects worksheet
            data = worksheet.get_all_values()
            headers = data.pop(0)
            
            df = pd.DataFrame(data, columns=headers)
            #all set up now the querry
            
            
            #print(df['avg'])
            #print(df.loc[8])
            df["avg"] = pd.to_numeric(df["avg"])

            try:
                goal = Helper.CommandStrip(ctx.message.content)
                goal = float(goal)
                results=df.loc[(df['avg'] >= goal) & (df['avg'] < goal+1)]['Title'].values #prints whole row where avg == goal
                if len(results) > 0:
                   await ctx.send(f'{ctx.message.author.mention}:', random.choice(results))
                else:
                    await ctx.send(f'{ctx.message.author.mention}:No results, do not try again')
            except ValueError:
                await ctx.send('{ctx.message.author.mention}:You have to enter a number, for example: 5')





    def setup(client):
        client.add_cog(cliffnet(client))