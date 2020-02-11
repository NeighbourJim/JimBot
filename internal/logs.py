import logging
import os
import errno
from datetime import date

class Logger():
    def __init__(self, logLevel):
        self.__loglevel = logLevel
        self.__path = './logs'
        self.__filename = '{0}discord-{1}.log'.format(self.__path, date.today())

    def CreateLogDirectory(self):
        try:
            os.mkdir(self.__path)
        except OSError as ex:
            if ex.errno == errno.EEXIST and os.path.isdir(self.__path):
                return True
            else:
                return False 

    def StartLogging(self):
        if self.CreateLogDirectory():
            logger = logging.getLogger('discord')
            logger.setLevel(self.__loglevel)
            handler = logging.FileHandler(filename=self.__filename, encoding='utf-8', mode='a')
            handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
            logger.addHandler(handler)
        else:
            print("ERROR: Failed to create logs folder.")
            
logger = Logger(logging.DEBUG)