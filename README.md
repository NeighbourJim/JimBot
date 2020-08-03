# JimBot (Working title.)
 Multifunction Discord bot written in Python, using Discord.py
 
 Built from the ground up to replace a bot I run for a private discord server that was using a very outdated Javascript wrapper.
 
 Has several cogs with a multitude of functions ranging from memes/tags, searching Google's APIs, games, and more.
 All of these cogs were written by me, with the one exception of the cog 'cliffnet.py', which was written by friends of mine for coding practice. The commands in that cog are set up only to work on one specific server for them to test.
 
 The bot is not specifically set up for public use on a large amount of servers, though theoretically it should support that - mostly.  
 If you want to run an instance of JimBot for yourself, then you need only to clone this repository and fill in the appropriate keys into config.json. An example file is provided, simply plug in your keys and remove EXAMPLE from the filename.  
 
 You will require a Discord bot token, placed in the "token" field in config.json  
 Certain Cogs also require API keys, placed in their appropriate fields in config.json.  
 These are:
 * Google Cog - Requires a Google API key, and a Google Custom Search Engine key.
 * Weather Cog - Requires an OpenWeatherMap.org API key.
 * Food Cog - Requires a Spoonacular.com API key.  
 
 You need not provide these keys if you plan on disabling the above cogs.
 
 Once that is configured you need only run bot.py in the root directory.
 
## Dependencies
Several python packages outside of those included with Python are required for this to run. Install these with ``pip install packagename``.
* discord.py
* requests
* gspread
* oauth2client
* pandas
* lxml
* google-api-python-client
* googletrans
* emoji
* Pillow
* pycountry
* beautifulsoup4


## Made With
<p align="center">
<a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Made%20With-Python%203.8-blue.svg?style=for-the-badge" alt="Made with Python 3.8">
</a>
<br>
<a href="https://github.com/Rapptz/discord.py/">
   <img src="https://img.shields.io/badge/discord-py-blue.svg" alt="discord.py">
</a>
</p>
