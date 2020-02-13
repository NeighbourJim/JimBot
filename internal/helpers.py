# General use helper methods used throughout various commands
import discord
import re
import internal.configmanager as configmanager

class Helpers(): 

    def CommandStrip(self, message):
        regex = r'^(\{}\w*)'.format(configmanager.cm.GetConfig()["settings"]["prefix"])
        print(regex)
        return re.sub(r'{}'.format(regex), '', message).lstrip()

Helper = Helpers()