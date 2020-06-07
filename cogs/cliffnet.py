### THIS COG IS FOR MACHIO AND KNITE TO PRACTICE AND MAKE THEIR OWN COMMANDS

import discord
import logging
import random
import requests
import pickle
import datetime
import asyncio
import time
import re
import os.path
from discord.ext import commands
from discord.ext.commands import BucketType
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

from internal.logs import logger
from internal.helpers import Helpers

class cliffnet(commands.Cog):

    def __init__(self, client):
        self.client = client
              
    @commands.command(aliases=["Scramble"], help="scrambles word order")
    @commands.cooldown(rate=1, per=1, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def scramble(self, ctx):
        if ctx.guild.id == 107847342006226944:
            userInput = Helpers.CommandStrip(self, ctx.message.content)
            split_message = userInput.split(' ')
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
                userInput = Helpers.CommandStrip(self, ctx.message.content)
                if userInput=="":
                    return await ctx.send(f'Enter a keyword to search')
                    
                source = (f'http://newsapi.org/v2/everything?q={userInput}&sortBy=top&apiKey=fec0d23dd26549a9a6d58a29a675e764')
                
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
                
    @commands.command(aliases=["Roulette", "rr"], help="Prove your barevery/ commit suicide. between 1-6 bullets")  
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()

    async def russianroulette(self, ctx):
        if ctx.guild.id == 107847342006226944:
            await ctx.trigger_typing()
        try:
            #get_message_task = ctx.channel.fetch_message(ctx.channel.last_message_id)   
            bullets = Helpers.FuzzyNumberSearch(self, ctx.message.content)
            if bullets != None:
                bullets = int(bullets)
            else:
                bullets = 0
            pick = 1 
            y= 6 #chambers left
            tension = 0 
            
            if bullets <7 and bullets > 0:
            
                while bullets !=0:
                    pick = random.randint(1, int(y))
                    y-=1
                    tension += 1
                    await asyncio.sleep(1.5)
                    if tension > 3 and tension <5:
                        await ctx.send("AAAH AAH AAH", delete_after=1)
                        await asyncio.sleep(1)
                    if tension == 6: 
                        await ctx.send("... ... .... ...", delete_after=1)
                        await asyncio.sleep(3)
                    if pick == 1:
                        await ctx.send("*BANG*")
                        break
                    else: await ctx.send("*click*", delete_after=1)
                    bullets-=1
                    
                if pick != 1:
                    await asyncio.sleep(0.2)
                    await ctx.send("You made it!")
                    
            else:await ctx.send("Incorrect bullets.")
        
        except Exception as ex:
                        await ctx.send(f'gun failure. {ex}')
                        logger.LogPrint(f'wrong bullets bad! bad! {ex}', logging.ERROR)



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
                goal = Helpers.CommandStrip(self, ctx.message.content)
                goal = float(goal)
                results=df.loc[(df['avg'] >= goal) & (df['avg'] < goal+1)]['Title'].values #prints whole row where avg == goal
                if len(results) > 0:
                   await ctx.send(f'{ctx.message.author.mention}:', random.choice(results))
                else:
                    await ctx.send(f'{ctx.message.author.mention}:No results, do not try again')
            except ValueError:
                await ctx.send('{ctx.message.author.mention}:You have to enter a number, for example: 5')

    @commands.command(aliases=["Days"], help="View or add long term timers. To add a timer it is !days [entry]. To reset is !days zero [entry]. To delete is !days delete [entry].")  
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def days(self, ctx):
        try:
            try:
                keyWords = ["ZERO","DELETE","RESET"]
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
            userInput = Helpers.CommandStrip(self, ctx.message.content).upper()
            if userInput == "": 
                response = f"**Days Since:**\n>>> "
                for x in daysDict:
                    timeDeltaDif = datetime.datetime.utcnow() - daysDict[x][0]
                    recordLength = daysDict[x][2]
                    if recordLength == datetime.timedelta(0):
                        response += f"**{x.title()}** - {Helpers.timeDeltaFormat(self, timeDeltaDif)[0]} days and {Helpers.timeDeltaFormat(self, timeDeltaDif)[1]} hours.\n"
                    else:
                        response += (f"**{x.title()}** - {Helpers.timeDeltaFormat(self, timeDeltaDif)[0]} days and {Helpers.timeDeltaFormat(self, timeDeltaDif)[1]} hours." 
                        f" Record: {Helpers.timeDeltaFormat(self, recordLength)[0]} days and {Helpers.timeDeltaFormat(self, recordLength)[1]} hours.\n")
                await ctx.send(response)
            
            #add new timer
            elif userInput.split(' ')[0].upper() not in keyWords: 
                
                if userInput in daysDict:
                    timeDeltaDif = datetime.datetime.utcnow() - daysDict[userInput][0]
                    return await ctx.send(f">>> It has been {Helpers.timeDeltaFormat(self, timeDeltaDif)[0]} days and {Helpers.timeDeltaFormat(self, timeDeltaDif)[1]} hours since the last **{userInput}**.")
                else:
                    daysDict[userInput.upper()] = [datetime.datetime.utcnow(),datetime.timedelta(0),datetime.timedelta(0)]
                    with open(daysFile,"wb") as daysFileWriter:
                        pickle.dump(daysDict, daysFileWriter)
                        return await ctx.send(f">>> Successfully added to the list!")
            
            #reset an existing timer
            elif userInput.startswith("ZERO") or userInput.startswith("RESET"): 
                if userInput.startswith("ZERO"):
                    pattern = "ZERO "
                else:
                    pattern = "RESET "
                userInput = userInput.upper()
                userInput = re.split(pattern, userInput, 1)[1]
                if userInput in daysDict:
                    lastDate=daysDict[userInput][0]
                    recordLength=daysDict[userInput][2]
                    currentDate=datetime.datetime.utcnow()
                    lastLength=currentDate-lastDate

                    if daysDict[userInput][2] == None or daysDict[userInput][2] == 0 or daysDict[userInput][2] < lastLength: 
                        recordLength = lastLength
                    daysDict[userInput]=[currentDate,lastLength,recordLength]
                    await ctx.send(f">>> Clock reset on **{userInput}**. Time was: {Helpers.timeDeltaFormat(self, lastLength)[0]} days and {Helpers.timeDeltaFormat(self, lastLength)[1]} hours." 
                    f"\nLongest record {Helpers.timeDeltaFormat(self, recordLength)[0]} days and {Helpers.timeDeltaFormat(self, recordLength)[1]} hours.")
                    
                    with open(daysFile,"wb") as daysFileWriter:
                        pickle.dump(daysDict, daysFileWriter)
                else:
                    return await ctx.send(f">>> Entry for timer reset not found.")

            elif userInput.startswith("DELETE"): #delete an existing timer
                pattern = "DELETE "
                userInput = re.split(pattern, userInput, 1)[1]

                if userInput in daysDict:
                    daysDict.pop(userInput)
                    with open(daysFile,"wb") as daysFileWriter:
                        pickle.dump(daysDict, daysFileWriter)
                        return await ctx.send(f">>> **{userInput}** - Deleted from list")
                else:
                    return await ctx.send(f">>> **{userInput}** - Not found for deletion.")        

        except FileNotFoundError as ex:
            logger.LogPrint(f'ERROR - Days file not found - {ex}', logging.ERROR)
        except EOFError as ex:
            logger.LogPrint(f"ERROR - File's empty, this shouldn't happen haha :) - {ex}", logging.ERROR)
        except Exception as ex:
            logger.LogPrint(f"ERROR - {ex}", logging.ERROR)


def setup(client):
    client.add_cog(cliffnet(client))
