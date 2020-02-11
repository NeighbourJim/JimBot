import re
import discord
from discord.ext import commands
from discord.ext.commands import BucketType

class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client
        
    @commands.command()
    @commands.is_owner()
    async def quit(self, ctx):
        await ctx.send("Bot shutting down...")
        await self.client.close()

    @commands.command(help="Deletes a specified number of messages from the channel.")
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx):
        mentions = ctx.message.mentions
        def compare_users(message):
            return message.author == mentions[0]
        try:            
            # Get the amount by using regex to strip all mentions out 
            amount = int(re.sub(r'<.*>', '', ctx.message.content[6:].strip()))
            if amount > 0 and amount < 50:
                if len(mentions) == 0:
                    deleted = await ctx.channel.purge(limit=amount)
                    await ctx.send(f'{ctx.message.author.mention}: Deleted {len(deleted)} messages.')                    
                elif len(mentions) == 1:
                    deleted = await ctx.channel.purge(limit=amount, check=compare_users)                
                    await ctx.send(f'{ctx.message.author.mention}: Deleted {len(deleted)} messages.') 
                else:
                    await ctx.send(f'{ctx.message.author.mention}: Can only delete messages from 1 user at a time.')
            else:
                    await ctx.send(f'{ctx.message.author.mention}: Can only delete between 1 and 50 messages.')
        except:
            await ctx.send(f'{ctx.message.author.mention}: You didn\'t enter a number of messages.')      


def setup(client):
    client.add_cog(Admin(client))