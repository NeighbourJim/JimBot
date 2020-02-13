# General use helper methods used throughout various commands
import discord
import re
import internal.configmanager as configmanager


class Helpers(): 

    def CommandStrip(self, message):
        regex = r'^(\{}\w*)'.format(configmanager.cm.GetConfig()["settings"]["prefix"])
        return re.sub(r'{}'.format(regex), '', message).lstrip()

    def FindEmoji(self, context, name_to_find):
        print("hello")
        try:
            emoji_list = context.guild.emojis
            for emoji in emoji_list:
                if emoji.name.lower() == name_to_find.lower():
                    return emoji
            return None
        except Exception as ex:
            print(ex)


Helper = Helpers()