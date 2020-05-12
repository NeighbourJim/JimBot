import discord
import logging
import random
import requests
import pickle
import datetime
import re
import os.path
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
    async def news(self, ctx):
        if ctx.guild.id == 107847342006226944:
            await ctx.trigger_typing()
            try:
                input = Helper.CommandStrip(ctx.message.content)
                if input=="":
                    return await ctx.send(f'Enter a keyword to search')
                    
                source = (f'http://newsapi.org/v2/everything?q={input}&sortBy=top&apiKey=fec0d23dd26549a9a6d58a29a675e764')
                
                pull = requests.get(source)

                articles = pull.json()["totalResults"]

                if articles == 0:
                   return await ctx.send(f'{ctx.message.author.mention}: No results.')
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
                await ctx.send(f'Couldn\'t get the news! - {ex}')
                logger.LogPrint(f'Couldn\'t get the news! - {ex}', logging.ERROR)


    @commands.command(aliases=["Movie"], help="find a random movie based on avg score from bromovies")  
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def movie(self, ctx):
        if ctx.guild.id == 107847342006226944:
            await ctx.trigger_typing()
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            credentials = ServiceAccountCredentials.from_json_keyfile_name('./internal/data/bromoviessearch.json', scope) # Your json file here
            
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

    @commands.command(aliases=["Days"], help="View or add long term timers.")  
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def days(self, ctx):
        def timeDeltaFormat(td: datetime.timedelta):
            tdHours = td.seconds/60/60
            if tdHours > 24:
                tdDaysHours = [tdHours // 24, float("{:.1f}".format(tdHours % 24))]
                return tdDaysHours
            else:
                tdDaysHours = [0, float("{:.1f}".format(tdHours))]
                return tdDaysHours

        try:
            try:
                keyWords = ["ZERO","DELETE"]
                #daysDict dictionary format = {"Entry1": ["StartTime1","LastLength1","LongestLength1"],}
                daysDict = {}
                daysFile = f"./internal/data/databases/days{ctx.guild.id}.pk"
                fileExists = os.path.isfile(daysFile)
                contentExists = os.path.getsize(daysFile) > 0

                if contentExists:
                    with open(daysFile,"rb") as daysFileReader:           
                        daysDict = pickle.load(daysFileReader)

            except IOError as ex:
                with open(daysFile,"ab+") as daysFileWriter:
                    pickle.dump(daysDict,daysFileWriter)
            except Exception as ex:
                logger.LogPrint(f'Error during initial file read / creation: {ex}',logging.ERROR)
        
            #return all entries
            input = Helper.CommandStrip(ctx.message.content).upper()
            if input == "": 
                response = f">>> Days since last reset: "
                for x in daysDict:
                    timeDeltaDif = datetime.datetime.utcnow() - daysDict[x][0]
                    response += f"\n\"{x}\" - {timeDeltaFormat(timeDeltaDif)[0]} days and {timeDeltaFormat(timeDeltaDif)[1]} hours"
                await ctx.send(response)
            
            #add new timer
            elif input.split(' ')[0].upper() not in keyWords: 
                
                if input in daysDict:
                    timeDeltaDif = datetime.datetime.utcnow() - daysDict[input][0]
                    return await ctx.send(f">>> \"{input}\" - {timeDeltaFormat(timeDeltaDif)[0]} days and {timeDeltaFormat(timeDeltaDif)[1]} hours since last reset")
                else:
                    daysDict[input.upper()] = [datetime.datetime.utcnow(),0,0]
                    with open(daysFile,"wb") as daysFileWriter:
                        pickle.dump(daysDict, daysFileWriter)
                        return await ctx.send(f">>> Successfully added to the list!")
            
            #reset an existing timer
            elif input.startswith("ZERO"): 

                pattern = "ZERO "
                input = input.upper()
                input = re.split(pattern, input, 1)[1]
                if input in daysDict:
                    lastDate=daysDict[input][0]
                    recordLength=daysDict[input][2]
                    currentDate=datetime.datetime.utcnow()
                    lastLength=currentDate-lastDate

                    if daysDict[input][2] == None or daysDict[input][2] == 0 or daysDict[input][2] < lastLength: 
                        recordLength = lastLength
                    daysDict[input]=[currentDate,lastLength,recordLength]
                    await ctx.send(f">>> \"{input}\" lasted {timeDeltaFormat(lastLength)[0]} days and {timeDeltaFormat(lastLength)[1]} hours. Longest record {timeDeltaFormat(recordLength)[0]} days and {timeDeltaFormat(recordLength)[1]} hours.")
                    with open(daysFile,"wb") as daysFileWriter:
                        pickle.dump(daysDict, daysFileWriter)
                else:
                    return await ctx.send(f">>> Entry for timer reset not found.")

            elif input.startswith("DELETE"): #delete an existing timer
                pattern = "DELETE "
                input = re.split(pattern, input, 1)[1]

                if input in daysDict:
                    daysDict.pop(input)
                    with open(daysFile,"wb") as daysFileWriter:
                        pickle.dump(daysDict, daysFileWriter)
                        return await ctx.send(f">>> \"{input}\" Deleted from list")
                else:
                    return await ctx.send(f">>> \"{input}\" - was not found for deletion.")        

        except FileNotFoundError as ex:
            logger.LogPrint(f'ERROR - Days file not found - {ex}', logging.ERROR)
        except EOFError as ex:
            logger.LogPrint(f"ERROR - File's empty, this shouldn't happen haha :) - {ex}", logging.ERROR)
        except Exception as ex:
            logger.LogPrint(f"ERROR - {ex}", logging.ERROR)


def setup(client):
    client.add_cog(cliffnet(client))
