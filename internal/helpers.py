# General use helper methods used throughout various commands
import discord
import re
import logging
import emoji

import internal.configmanager as configmanager
from internal.logs import logger


class Helpers(): 
    def __init__(self):
        # NOTE: This regex pattern courtesy of top answer here: https://stackoverflow.com/questions/20157375/fuzzy-smart-number-parsing-in-python
        self.__fuzzy_number_pattern = r"""(?x)       # enable verbose mode (which ignores whitespace and comments)
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

    def CommandStrip(self, message):
        regex = r'^(\{}\w*)'.format(configmanager.cm.GetConfig()["settings"]["prefix"])
        return re.sub(r'{}'.format(regex), '', f'{message}').lstrip()

    def FindEmoji(self, context, name_to_find):
        try:
            emoji_list = context.guild.emojis
            for emoji in emoji_list:
                if emoji.name.lower() == name_to_find.lower():
                    return emoji
            return None
        except Exception as ex:
            print(ex)

    def EmojiConvert(self, message):
        return emoji.demojize(message)

    def FuzzyNumberSearch(self, message):
        match = re.match(self.__fuzzy_number_pattern, message)
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


Helper = Helpers()

