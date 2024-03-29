import discord
from discord.utils import escape_markdown, escape_mentions
import re
import requests
import html
import logging
import emoji
import datetime
import asyncio

from os import path

import internal.command_blacklist_manager as blm
from internal.databasemanager import dbm
import internal.configmanager as configmanager
from internal.logs import logger



class Helpers(): 
    """Contains simple helper functions reused throughout the bot."""
     
    @staticmethod
    def CommandStrip(self, message: str):
        """Remove command evocation message from a string.

        Args:
            message (str): Message to remove command evocation from. Pass in the raw discord message content.

        Returns:
            str: Message entered without the command evocation. Performs strip() on the message so leading and trailing whitespace is removed.
        """
        regex = r'^(\{}\w*)'.format(configmanager.cm.GetConfig()["settings"]["prefix"])
        return re.sub(r'{}'.format(regex), '', f'{message}').strip()

    @staticmethod
    def StripMentions(self, message:str):
        regex = r'<@[0-9]*>'
        message = re.sub(r'{}'.format(regex), '', f'{message}').strip()
        regex = r'<@![0-9]*>'
        message = re.sub(r'{}'.format(regex), '', f'{message}').strip()
        return message

    @staticmethod
    async def GetLastTextMessage(self, ctx, search_limit=10):
        last_message_id = ctx.channel.last_message_id
        if last_message_id != None:
            task = asyncio.create_task(ctx.channel.history(limit=search_limit).flatten())
            await task
            message_list = task.result()
            for message in message_list:
                stripped = Helpers.CommandStrip(self, message.content)
                stripped = Helpers.StripMentions(self, stripped)
                if len(stripped) > 1:
                    return message
        return None

    

    @staticmethod
    def GetFirstEmojiID(self, message: str):
        """Find the ID of the first Discord emoji in a given string.

        Args:
            message (str): Message to search for emoji.

        Returns:
            str: Discord ID of first emoji found.
            None: If no emoji ID is found.
        """
        try:
            return re.search(r'[^:]+(?=\>)', message)
        except Exception as ex:
            print(ex)

    @staticmethod
    def FindEmoji(self, context: discord.ext.commands.Context, name_to_find: str):
        """Find an emoji on server with a given name. Searches using lower(), so is not case sensitive.

        Args:
            context (discord.ext.commands.Context): The context in which to search. Should generally be the context of the message which evoked the command. 
            name_to_find (str): Name of the emoji to find.

        Returns:
            discord.Emoji: Emoji object found with the specified name.
            None: If no Emoji is found.
        """
        try:
            emoji_list = context.guild.emojis
            for emoji in emoji_list:
                if emoji.name.lower() == name_to_find.lower():
                    return emoji
            return None
        except Exception as ex:
            print(ex)

    # Remove??? Basically pointless
    @staticmethod
    def EmojiConvert(self, message: str):
        """Demojize a given string using the emoji package. Not really necessary but avoids importing emoji package I guess..

        Args:
            message (str): Message to demojize.

        Returns:
            str: The message paramater but demojized.
        """
        return emoji.demojize(message)

    @staticmethod
    def DiscordEmoteConvert(self, message:str):
        emotes = re.findall(r'<:.*?>', message)
        if emotes:
            for emote in emotes:
                name = re.search(r':(.*?):', emote).group(0)
                name = name.replace(':','')
                message = message.replace(emote,f' {name} ')

        emotes = re.findall(r'<:(.*?)>', message)
        if emotes:
            for emote in emotes:
                name = re.search(r'a:(.*?):', emote).group(0)
                name = name.replace(':','')
                message = message.replace(emote,f' {name} ')
        return message



    @staticmethod
    def FuzzyIntegerSearch(self, message: str):
        """Search for whole numbers inside a string and returns the first one found.

        Args:
            message (str): Message to search.

        Returns:
            int: The first integer found.
            None: If the string contains no numbers.
        """
        result = re.findall(r'-?\d+', message)
        if len(result) > 0:
            return int(result[0])
        else:
            return None

    @staticmethod
    def FuzzyNumberSearch_OLD(self, message: str):
        """Search for a number inside a string and convert to numeric data type using regex. 
        No longer actively used because it doesn't work if there are multiple numbers in a message, but may still have some use since it can find floats.

        Args:
            message (str): Message to search for a number.

        Returns:
            int: If a whole number is found.
            float: If a real number is found.
        """
        # NOTE: This regex pattern courtesy of top answer here: https://stackoverflow.com/questions/20157375/fuzzy-smart-number-parsing-in-python
        __fuzzy_number_pattern = r"""(?x)       # enable verbose mode (which ignores whitespace and comments)
        ^                     # start of the input
        [^\d+-\.]*            # prefixed junk
        (?P<number>           # capturing group for the whole number
            (?P<sign>[+-])?       # sign group (optional)
            (?P<integer_part>         # capturing group for the integer part
                \d{1,3}               # leading digits in an int with a thousands separator
                (?P<sep>              # capturing group for the thousands separator
                    [ ,.]                 # the allowed separator characters
                )
                \d{3}                 # exactly three digits after the separator
                (?:                   # non-capturing group
                    (?P=sep)              # the same separator again (a backreference)
                    \d{3}                 # exactly three more digits
                )*                    # repeated 0 or more times
            |                     # or
                \d+                   # simple integer (just digits with no separator)
            )?                    # integer part is optional, to allow numbers like ".5"
            (?P<decimal_part>     # capturing group for the decimal part of the number
                (?P<point>            # capturing group for the decimal point
                    (?(sep)               # conditional pattern, only tested if sep matched
                        (?!                   # a negative lookahead
                            (?P=sep)              # backreference to the separator
                        )
                    )
                    [.,]                  # the accepted decimal point characters
                )
                \d+                   # one or more digits after the decimal point
            )?                    # the whole decimal part is optional
        )
        [^\d]*                # suffixed junk
        $                     # end of the input
        """
        match = re.match(__fuzzy_number_pattern, message)
        if match is None or not (match.group("integer_part") or match.group("decimal_part")):    # failed to match
            return None                      # consider raising an exception instead
        num_str = match.group("number")      # get all of the number, without the junk
        sep = match.group("sep")
        if sep:
            num_str = num_str.replace(sep, "")     # remove thousands separators
        if match.group("decimal_part"):
            point = match.group("point")
            if point != ".":
                num_str = num_str.replace(point, ".")  # regularize the decimal point
            return float(num_str)

        return int(num_str)

    @staticmethod
    def CheckIfMemberHasRole(self, member: discord.Member, role_name: str):
        """Check if a given Discord member has a given role.

        Args:
            member (discord.Member): Discord member to search.
            role_name (str): Role name to search for.

        Returns:
            bool: True if role is found, False if not.
        """
        for role in member.roles:
            if role.name == role_name:
                return True
        return False


    @staticmethod
    def GetWebPage(self, url: str, params=None):
        """Pass a url and optional parameters to requests.get().

        Args:
            url (str): URL of the webpage.
            params (dict, optional): Parameters to pass through to webpage. Defaults to None.

        Returns:
            requests.Response: If Status Code 200 return the result of .get()
            None: If any other Status Code
        """
        try:
            logger.LogPrint(f"Initiating request...")
            if params:
                result = requests.get(url, params)
            else:
                result = requests.get(url)
            logger.LogPrint(f"Response: {result}")
            if result.status_code == 200:
                return result
            else:
                return None
        except Exception as ex:
            print(ex)

    @staticmethod
    def CleanHTML(self, input):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', input)
        cleantext = html.unescape(cleantext)
        return cleantext

    @staticmethod
    def timeDeltaFormat(self, td: datetime.timedelta):
            """Convert a timedelta objects into days and hours.

            Args:
                td (datetime.timedelta): timedelta object from datetime module.

            Returns:
                list(int,float): list with days and hours. Hours rounded to the first decimal.
            """
            tdHours = td.seconds/60/60
            tdDaysHours = [td.days, float("{:.1f}".format(tdHours % 24))]
            return tdDaysHours


Helper = Helpers()