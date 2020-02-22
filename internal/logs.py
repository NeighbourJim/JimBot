import logging
import os
import errno
from datetime import date

class Logger():
    def __init__(self, logLevel):
        self.__loglevel = logLevel
        self.__path = './logs/'
        self.__filename = f'{self.__path}discord-{logLevel}-{date.today()}.log'
        self.logger = None

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
            self.logger = logging.getLogger('discord')
            self.logger.setLevel(self.__loglevel)
            handler = logging.FileHandler(filename=self.__filename, encoding='utf-8', mode='a')
            handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
            self.logger.addHandler(handler)
        else:
            print("ERROR: Failed to create logs folder.")

    def LogPrint(self, message, level=logging.INFO, err=None):
        if level == logging.CRITICAL:
            if level >= self.__loglevel:
                print(f'{message}:{err}')
            self.logger.critical(message,exc_info=err)
        if level == logging.ERROR:
            if level >= self.__loglevel:
                print(f'{message}:{err}')
            self.logger.error(message,exc_info=err)
        if level == logging.WARNING:
            if level >= self.__loglevel:
                print(f'{message}:{err}')
            self.logger.warning(message,exc_info=err)
        if level == logging.INFO:
            if level >= self.__loglevel:
                print(f'{message}:{err}')
            self.logger.info(message,exc_info=err)
        if level == logging.DEBUG:
            if level >= self.__loglevel:
                print(f'{message}:{err}')
            self.logger.debug(message,exc_info=err)
            
logger = Logger(logging.INFO)