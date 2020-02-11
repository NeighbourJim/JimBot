import json

class ConfigManager():
    def __init__(self):
        self.__config_data = ''

    def __ReadConfigFile(self):
        with open('config.json') as file:
            self.__config_data = json.load(file)
            return True
        return False
    
    def __SaveConfigFile(self):
        with open('config.json', 'w') as json_file:
            json.dump(self.__config_data, json_file)

    def GetConfig(self):
        if self.__ReadConfigFile():
            return self.__config_data

cm = ConfigManager()
    