import json

class ConfigManager():
    def __init__(self):
        self.__config_data = ''

    def __ReadConfigFile(self):
        """Attempt to read config.json.

        Returns:
            bool: True if config file successfully read. False if not.
        """
        with open('config.json') as file:
            self.__config_data = json.load(file)
            return True
        return False
    
    def __SaveConfigFile(self):
        """Dump the current config data to config.json."""
        with open('config.json', 'w') as json_file:
            json.dump(self.__config_data, json_file)

    def GetConfig(self):
        """Read and return the config data.

        Returns:
            object: Python object containing config data read from config.json.
        """
        if self.__ReadConfigFile():
            return self.__config_data

cm = ConfigManager()
    