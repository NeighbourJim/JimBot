import discord
import json
import logging
import random
import asyncio
import requests
import glob
import re
import os
import io
from PIL import Image
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from internal.data.pokemon_names import pokemon_names, pokemon_names_fusion
from internal.data.pokemon_names_split import split_names, pokemon_names_split_fusion

class Pokemon(commands.Cog):

    

    def __init__(self, client):
        self.client = client
        self.fusion_cache = dict()
        self.triplechance = 500
        self.head_fusions, self.body_fusions, self.fusion_files = self._build_fusion_maps()
        self.fusable_pokemon = list(self.head_fusions.keys() | self.body_fusions.keys())
        
        triples_path = f'./internal/data/images/fusions/CustomBattlers/indexed/triples/'
        if os.path.isdir(triples_path):
            self.triple_fusions = [os.path.join(triples_path, f) for f in os.listdir(triples_path) if f.endswith('.png')]
        else:
            self.triple_fusions = []

    def _build_fusion_maps(self):
        head_fusions = {}
        body_fusions = {}
        fusion_files = {}
        root_dir = './internal/data/images/fusions/CustomBattlers/indexed2/CustomBattlers'
        if not os.path.isdir(root_dir):
            logger.error("Custom fusions directory not found.")
            return {}, {}, {}
            
        for head_dir in os.listdir(root_dir):
            if not head_dir.isdigit():
                continue
            head_id = int(head_dir)
            path = os.path.join(root_dir, head_dir)
            if not os.path.isdir(path):
                continue
                
            for fusion_file in os.listdir(path):
                match = re.match(rf'^{head_id}\.(\d+)([a-zA-Z])?\.png$', fusion_file)
                if match:
                    body_id = int(match.group(1))

                    if head_id not in head_fusions:
                        head_fusions[head_id] = []
                    if body_id not in head_fusions[head_id]:
                        head_fusions[head_id].append(body_id)

                    if body_id not in body_fusions:
                        body_fusions[body_id] = []
                    if head_id not in body_fusions[body_id]:
                        body_fusions[body_id].append(head_id)
                    
                    if (head_id, body_id) not in fusion_files:
                        fusion_files[(head_id, body_id)] = []
                    fusion_files[(head_id, body_id)].append(fusion_file)
                    
        return head_fusions, body_fusions, fusion_files

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)
        
    def AddToFusionCache(self, key,value):
        max_dict_size = 1000
        if len(self.fusion_cache) >= max_dict_size:
            self.fusion_cache.pop(next(iter(self.fusion_cache)))
        self.fusion_cache[key] = value

    def GenerateFusedName(self, id1, id2):
        prefix_only = ['mr. ', 'regi', 'type: ', 'tapu ', 'iron ', "wo-", "ting-", "chi-", "chien-", "mimi", "ultra necro"]
        suffix_only = [' jr.', 'ese', 'mo-o', 'pedo']      
        n2_prefix_found = False
        n1_suffix_found = False



        name1pre = pokemon_names_split_fusion[id1][0].lower()
        name1suf = pokemon_names_split_fusion[id1][1].lower()
        name2pre = pokemon_names_split_fusion[id2][0].lower()
        name2suf = pokemon_names_split_fusion[id2][1].lower()
        
        for i in prefix_only:
            if i == name2pre:
                n2_prefix_found = True
        for i in suffix_only:
            if i == name1suf:
                n1_suffix_found = True

        if n2_prefix_found or n1_suffix_found:
            name = name2pre + name1suf
        else:
            if name1pre[-1].lower() == name2suf[0].lower():
                name2suf = name2suf[1:]
            name = name1pre + name2suf

        return name.title().strip()

    def GetCustomFusionNew(self, id):
        count = 1        
        tripleroll = random.randint(0, self.triplechance)
        if random.randint(1,6) == 1 and self.triplechance > 0:
            self.triplechance = self.triplechance - 1
            
        if (tripleroll == self.triplechance or not self.fusable_pokemon) and self.triple_fusions:
            self.triplechance = 500
            fusion = random.choice(self.triple_fusions)
            return [fusion,count,None,None]

        search_pokemon_id = id
        
        if search_pokemon_id != -1:
            if search_pokemon_id not in self.fusable_pokemon:
                search_pokemon_id = -1 
        
        if search_pokemon_id == -1:
            search_pokemon_id = random.choice(self.fusable_pokemon)
        
        choice = []
        if search_pokemon_id in self.head_fusions:
            choice.append('head')
        if search_pokemon_id in self.body_fusions:
            choice.append('body')
        
        if not choice:
            if self.triple_fusions:
                self.triplechance = 500
                fusion = random.choice(self.triple_fusions)
                return [fusion, 51, None, None]
            else: # Catastrophic failure
                return [None, 51, None, None]

        if random.choice(choice) == 'head':
            id1 = search_pokemon_id
            id2 = random.choice(self.head_fusions[id1])
        else:
            id2 = search_pokemon_id
            id1 = random.choice(self.body_fusions[id2])

        filename = random.choice(self.fusion_files[(id1, id2)])
        path = f"./internal/data/images/fusions/CustomBattlers/indexed2/CustomBattlers/{id1}/{filename}"
        return [path, count, id1, id2]
            
    def GetFusion(self, id1, id2):
        max_id = 473
        if id1 == -1:
            id1 = random.randint(1,max_id)
        if id2 == -1:
            id2 = random.randint(1,max_id)
        path = f'./internal/data/images/fusions/CustomBattlers/indexed2/CustomBattlers/{id1}/{id1}.{id2}'
        path_prefix = f"./internal/data/images/fusions/CustomBattlers/indexed2/CustomBattlers/{id1}\\"
        pattern = re.compile(rf'{re.escape(path_prefix)}{id1}\.{id2}[a-zA-Z]?\.png')
        fusions =  glob.glob(f'{path}*.png')
        matching = []
        for fusion in fusions:
            if pattern.match(fusion):
                matching.append(fusion)
        if len(matching) > 0:
                return [random.choice(matching),id1,id2]
        if os.path.isfile(path):
            print('returning custom')
            return [path,id1,id2]
        print('returning auto')
        return [f'./internal/data/images/fusions/Battlers/{id1}/{id1}.{id2}.png',id1,id2]


    def GetRandomFusion(self):
        max_id = 420
        p1 = random.randint(1,max_id)
        p2 = random.randint(1,max_id)
        #custom_url = f"https://raw.githubusercontent.com/infinitefusion/sprites/main/CustomBattlers/{p1}.{p2}.png"
        #fallback_url = f"https://raw.githubusercontent.com/infinitefusion/autogen-fusion-sprites/master/Battlers/{p1}/{p1}.{p2}.png"
        custom_url = f"https://gitlab.com/infinitefusion/sprites/-/raw/master/CustomBattlers/{p1}/{p1}.{p2}.png"
        fallback_url = f"https://gitlab.com/infinitefusion/sprites/-/raw/master/Battlers/{p1}/{p1}.{p2}.png"
        if p1 == p2:
            custom_request = requests.get(custom_url)
            if custom_request.status_code == 404:
                p2 = random.randint(1,max_id)
                custom_url = f"https://gitlab.com/infinitefusion/sprites/-/raw/master/CustomBattlers/{p1}/{p1}.{p2}.png"
                fallback_url = f"https://gitlab.com/infinitefusion/sprites/-/raw/master/Battlers/{p1}/{p1}.{p2}.png"
        if (p1,p2) in self.fusion_cache:
            image_url = self.fusion_cache[(p1,p2)]
        else:
            #custom_url = f"https://raw.githubusercontent.com/Aegide/custom-fusion-sprites/main/CustomBattlers/{p1}.{p2}.png"
            
            custom_request = requests.get(custom_url)
            if custom_request.status_code != 404:
                image_url = custom_url
            else:
                image_url = fallback_url
            self.AddToFusionCache((p1,p2), image_url)
        return (image_url, (p1,p2))

    def GetCustomFusion(self, id):
        max_id = 420
        if random.randint(0,1) == 1:
            p1 = id
            p2 = random.randint(1, max_id)
        else:
            p1 = random.randint(1, max_id)
            p2 = id
        if (p1,p2) in self.fusion_cache:
            image_url = self.fusion_cache[(p1,p2)]
            if "CustomBattlers" in image_url:
                return image_url
        image_url = None
        custom_url = f"https://gitlab.com/infinitefusion/sprites/-/raw/master/CustomBattlers/{p1}/{p1}.{p2}.png"
        custom_request = requests.get(custom_url)
        if custom_request.status_code != 404:
            image_url = custom_url
            self.AddToFusionCache((p1,p2), image_url)
        else:
            custom_url = f"https://gitlab.com/infinitefusion/sprites/-/raw/master/CustomBattlers/{p1}/{p1}.{p2}.png"
            custom_request = requests.get(custom_url)
            if custom_request.status_code != 404:
                image_url = custom_url
                self.AddToFusionCache((p1,p2), image_url)
        return (image_url, (p1,p2))
        
    def GetTripleFusion(self):
        #https://raw.githubusercontent.com/infinitefusion/autogen-fusion-sprites/master/Battlers/special/1.4.7.png
        
        triples = [("1.4.7","Bulbmantle"),("144.145.146","Zapmolticuno"),("150.348.380","Deoxese Two"),("151.251.381","Celemewchi"),("152.155.158","Totoritaquil"),("153.156.159","Baylavanaw"),("154.157.160","Megaligasion"),("2.5.8","Ivymelortle"),("243.244.245","Enraicune"),("276.279.282","Torkipcko"),("277.280.283","Gromarshken"),("278.281.284","Swamptiliken"),("3.6.9","Venustoizard"),("316.319.322","Turcharlup"),("317.320.323","Prinfernotle"),("318.321.324","Torterneon"),("340.341.342","Kyodonquaza"),("343.344.345","Paldiatina"),("349.350.351","Zekyushiram")]
        return random.choice(triples)

    def GenerateName(self):
        prefix_only = ['mr. ', 'regi', 'type: ', 'tapu ', 'iron ', "wo-", "ting-", "chi-", "chien-"]
        suffix_only = [' jr.', 'ese', 'mo-o']      
        n2_prefix_found = False
        n1_suffix_found = False

        name1 = random.choice(split_names).lower()
        name2 = random.choice(split_names).lower()
        
        for i in prefix_only:
            if i == name2:
                n2_prefix_found = True
        for i in suffix_only:
            if i == name1:
                n1_suffix_found = True

        if n2_prefix_found or n1_suffix_found:
            name = name2 + name1
        else:
            name = name1 + name2

        return name.title().strip()

    def GenerateStats(self, type=0):

        def stat_gen(type, min_base_bst, max_base_bst, soft_stat_min, soft_stat_max):
            #i wrote this all and then kinda forgot what it does
            stats = []
            base_bst = random.randint(min_base_bst,max_base_bst)
            for i in range(6):
                #for the max stat, it takes the remaining BST from the max BST divided by how many stats are left to generate
                max_stat = int((max_base_bst-sum(stats))/(6-i))
                #if this is over the soft stat max, then we roll a random one between 20, and the soft stat max + 30
                if max_stat >= soft_stat_max:
                    max_stat = random.randint(20, soft_stat_max+30)
                #for the min stat, we take the remaining BST from the min BST divided by how many stats are left to generate
                min_stat = int((min_base_bst-sum(stats))/(6-i))
                #if its under the soft stat min, we just set it to soft stat min minus 10
                if (min_stat <= soft_stat_min):
                    min_stat = soft_stat_min-10
                #and if after that its still over the max stat somehow, we just set it to max stat minus 10
                if (min_stat > max_stat):
                    min_stat = max_stat-10
                #and then it rolls an int between those two values, and appends it to the array
                stat = random.randint(min_stat,max_stat)
                stats.append(stat)
            return stats

        if type == 0:
            type = random.randint(1, 4)
            if type == 4:
                type = random.randint(1, 4)
        if type < 5:
            types_bst_stuff = [200, 375, 20, 80, 300, 450, 40, 110, 450, 600, 50, 150, 570, 720, 70, 225]
            min_base_bst = types_bst_stuff[(type*4) - 4]
            max_base_bst = types_bst_stuff[(type*4) - 3]
            soft_stat_min = types_bst_stuff[(type*4) - 2]
            soft_stat_max = types_bst_stuff[(type*4) - 1]

        if type < 5:
            stats = stat_gen(type, min_base_bst, max_base_bst, soft_stat_min, soft_stat_max)
            #40% chance to bump a stat up so that the BST is a multiple of 5
            if ((sum(stats) % 5) != 5) and (random.randint(1,5) < 3):
                stats[random.randint(0,5)] += (5-(sum(stats) % 5))
        else:             
            stats = [random.randint(1,255),random.randint(1,255),random.randint(1,255),random.randint(1,255),random.randint(1,255),random.randint(1,255)]
        stat_total = sum(stats)
        if type == 1:
            stage = "Baby"
        elif type == 2:
            stage = "Middle"
        elif type == 3:
            stage = "Fully Evolved"
        elif type == 4:
            stage = "Legendary"
        elif type == 5:
            stage = "Unknown"
        random.shuffle(stats)
        return stats, stage, stat_total   

    @commands.command(help="Get a random fused Pokemon team (custom only).", aliases=["rft"])
    @commands.cooldown(rate=1, per=10, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomfusedteam(self, ctx):
        await ctx.trigger_typing()
        fusions = []
        fusion_names = []
        for _ in range(6):
            results = self.GetCustomFusionNew(-1)
            while results[2] is None:
                results = self.GetCustomFusionNew(-1)
            fusions.append(results[0])
            if results[2] == results[3]:
                name = f"Mega {pokemon_names_fusion[results[2]-1].title()}"
            else:
                name = self.GenerateFusedName(results[2]-1, results[3]-1)
            fusion_names.append(name)

        width = 2853
        height = 1902
        new_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        for i, fusion_path in enumerate(fusions):
            row = i // 3
            col = i % 3
            x = col * 951
            y = row * 951
            try:
                with Image.open(fusion_path) as img:
                    img = img.resize((951, 951))
                    new_image.paste(img, (x, y))
            except Exception as e:
                logger.error(f"Error processing image {fusion_path}: {e}")
                await ctx.reply("An error occurred while creating the fused team image.")
                return
        
        with io.BytesIO() as image_binary:
            new_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            
            embed = discord.Embed(title=f"{ctx.author.display_name}'s Team")
            embed.set_image(url="attachment://fused_team.png")
            embed.set_footer(text=", ".join(fusion_names))
            
            await ctx.reply(embed=embed, file=discord.File(fp=image_binary, filename='fused_team.png'))



    @commands.command(help="Get a random fused Pokemon (custom only).", aliases=["rfc"])
    @commands.cooldown(rate=1, per=2, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomfusedcustom(self, ctx):
        triple = False
        query = Helpers.CommandStrip(self, ctx.message.content)
        unavailable_msg = ""
        space_names = ['mr. mime', 'mime jr.', 'nidoran f', 'nidoran m',"oricorio baile", "oricorio pom-pom","oricorio pau","oricorio sensu","lycanroc midday","lycanroc midnight","ultra necrozma","meloetta pirouette"]
        if not query.strip():
            query = None
        if query:
            await ctx.trigger_typing()
            query_split = query.split()
            index = -1
            found = False
            for n in space_names:
                if n in query.lower():
                    index = pokemon_names_fusion.index(n)+1
                    unavailable_msg = ""
                    found = True
                    break
            if not found:
                for i in query_split:
                    if i.lower() in pokemon_names_fusion:
                        index = pokemon_names_fusion.index(i.lower())+1
                        unavailable_msg = ""
                        break
                    elif i.lower() in (n.lower() for n in pokemon_names):
                        unavailable_msg = " | That pokemon isn't available. Rolling random instead."
        else:
            index = -1
        results = self.GetCustomFusionNew(index)
        if results[0] is None:
            await ctx.reply("Could not find a custom fusion, and triple fusions are unavailable. Please try again later.")
            return
        fusion = results[0]
        count = results[1]
        if results[2] == None:
            triple = True
            name = os.path.basename(fusion)
            name = name.replace('.png','')
        else:
            if results[2]-1 == results[3]-1:
                name = f"Mega {pokemon_names_fusion[results[2]-1]}"
            else:
                name = self.GenerateFusedName(results[2]-1,results[3]-1)
            name1 = pokemon_names_fusion[results[2]-1]
            name2 = pokemon_names_fusion[results[3]-1]
            name = name.title()
        fusion_embed = discord.Embed()
        if not triple:
            image_file = discord.File(fusion, filename=f'fusion.png')
            if len(ctx.guild.members) >= 200:
                fusion_embed.set_thumbnail(url=f"attachment://fusion.png")
            else:
                fusion_embed.set_image(url=f"attachment://fusion.png")
            fusion_embed.title = f'{name.title()}'
            fusion_embed.set_footer(text=f"{name1.title()} + {name2.title()}{unavailable_msg}")
            sent = await ctx.reply(file=image_file, embed=fusion_embed)
            if len(ctx.guild.members) <= 200:
                await asyncio.sleep(12)
                fusion_embed.set_thumbnail(url=f"attachment://fusion.png")
                fusion_embed.set_image(url='')
                await sent.edit(embed=fusion_embed)
        else:
            fusion_embed.title = f'WARNING: A Fusion Accident has occurred!'
            fusion_embed.set_image(url="https://i.imgur.com/KPHXUAl.png")  
            fusion_embed.description = f"Waiting for the smoke to clear..."
            sent = await ctx.reply(embed=fusion_embed)
            await asyncio.sleep(6)
            image_file = discord.File(fusion, filename=f'fusion.png')
            fusion_embed.title = f':sparkles: Triple Fusion: {name.title()} :sparkles:'
            fusion_embed.set_image(url="attachment://fusion.png")
            await sent.delete()
            fusion_embed.description = f""
            sent = await ctx.reply(file=image_file,embed=fusion_embed)
            if len(ctx.guild.members) > 80:
                await asyncio.sleep(12)
                fusion_embed.set_thumbnail(url=f"attachment://fusion.png")
                fusion_embed.set_image(url='')
                await sent.edit(embed=fusion_embed)


    @commands.command(help="Get a random Pokemon.", aliases=["rmon", "RMon", "Rmon", "RMON"])
    @commands.cooldown(rate=1, per=2, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randompokemon(self, ctx):
        pokemon_count = len(pokemon_names)
        shiny_rarity = 1365
        poke_num = random.randint(1, pokemon_count)
        shiny = random.randint(1,shiny_rarity)
        poke_name = pokemon_names[poke_num-1]
        if poke_num < 10:
            poke_num_string = f'00{poke_num}'
        elif poke_num < 100:
            poke_num_string = f'0{poke_num}'
        else:
            poke_num_string = str(poke_num)
        if poke_num < 906:
            if shiny == shiny_rarity:
                url = f'https://www.serebii.net/Shiny/SWSH/{poke_num_string}.png'
                message = f'**{poke_num} - :sparkles: {poke_name} :sparkles:**'
            else:
                url = f'https://www.serebii.net/swordshield/pokemon/{poke_num_string}.png'
                message = f'**{poke_num_string} - {poke_name}**'
        else:
            if shiny == shiny_rarity:
                url = f'https://www.serebii.net/Shiny/SV/{poke_num_string}.png'
                message = f'**{poke_num} - :sparkles: {poke_name} :sparkles:**'
            else:
                url = f'https://www.serebii.net/scarletviolet/pokemon/new/{poke_num_string}.png'
                message = f'**{poke_num_string} - {poke_name}**'
        poke_embed = discord.Embed()
        poke_embed.title = f'{message}'
        poke_embed.set_thumbnail(url=url)
        await ctx.reply(embed=poke_embed)
        #await asyncio.sleep(10)
        #poke_embed.set_thumbnail(url=url)
        #poke_embed.set_image(url='')
        #await sent.edit(embed=poke_embed)

    @commands.command(help="Get a random fused Pokemon (custom only).", aliases=["rfcOLD"])
    @commands.cooldown(rate=1, per=15, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomfusedcustomOLD(self, ctx):
        query = Helpers.CommandStrip(self, ctx.message.content)
        if not query.strip():
            query = None
        if query:
            if query.lower() not in pokemon_names_fusion: 
                await ctx.reply(f"{query} not available for fusion.")
                return
        sent = await ctx.reply(f"Searching for custom fusion...")
        await ctx.trigger_typing()
        if query:
            index = pokemon_names_fusion.index(query.lower()) + 1
        else:
            tripleroll = random.randint(1,self.triplechance)
            print(self.triplechance)
            if tripleroll == self.triplechance:
                self.triplechance = 500
                await asyncio.sleep(4)
                fusion = self.GetTripleFusion()
                image_url = f"https://gitlab.com/pokemoninfinitefusion/customsprites/-/raw/master/Other/Triples/{fusion[0]}.png"
                name = fusion[1]
                
                poke_embed = discord.Embed()
                poke_embed.title = f'WARNING: A Fusion Accident has occurred!'
                poke_embed.set_thumbnail(url="https://i.imgur.com/KPHXUAl.png")  
                poke_embed.description = f"Waiting for the smoke to clear..."
                await sent.edit(embed=poke_embed, content=None)
                
                poke_embed.title = f':sparkles: Triple Fusion: {name.title()} :sparkles:'
                poke_embed.description = f"**[Image Link]({image_url})**"
                if len(ctx.guild.members) >= 1000:
                    poke_embed.set_thumbnail(url=image_url)
                else:
                    poke_embed.set_image(url=image_url)
                
                await asyncio.sleep(6)
                await sent.edit(embed=poke_embed, content=None)
                if len(ctx.guild.members) < 100:
                    poke_embed.set_thumbnail(url=image_url)
                    poke_embed.set_image(url="")
                    await asyncio.sleep(15)
                    await sent.edit(embed=poke_embed, content=None)
                return
            else:
                if random.randint(1,6) == 1:
                    self.triplechance = self.triplechance-1
            index = random.randint(1,420)
        fusion_result = None
        i = 1
        fusion_result = self.GetCustomFusion(index)
        while fusion_result[0] == None:
            fusion_result = self.GetCustomFusion(index)
            i = i+1
            if i >= 30:
                fusion = self.GetTripleFusion()
                image_url = f"https://gitlab.com/pokemoninfinitefusion/customsprites/-/raw/master/Other/Triples/{fusion[0]}.png"
                name = fusion[1]
                
                poke_embed = discord.Embed()
                poke_embed.title = f'WARNING: A Fusion Accident has occurred!'
                poke_embed.set_thumbnail(url="https://i.imgur.com/KPHXUAl.png")  
                poke_embed.description = f"Waiting for the smoke to clear..."
                await sent.edit(embed=poke_embed, content=None)
                
                poke_embed.title = f':sparkles: Triple Fusion: {name.title()} :sparkles:'
                poke_embed.description = f"**[Image Link]({image_url})**"
                if len(ctx.guild.members) >= 1000:
                    poke_embed.set_thumbnail(url=image_url)
                else:
                    poke_embed.set_image(url=image_url)
                
                await asyncio.sleep(6)
                await sent.edit(embed=poke_embed, content=None)
                if len(ctx.guild.members) < 100:
                    poke_embed.set_thumbnail(url=image_url)
                    poke_embed.set_image(url="")
                    await asyncio.sleep(15)
                    await sent.edit(embed=poke_embed, content=None)
                return
            if i == 20:
                await sent.edit(content="Still searching.......")
            await asyncio.sleep(0.3)
        image_url = fusion_result[0]
        p1 = fusion_result[1][0]
        p2 = fusion_result[1][1]
        custom = "Custom Made"
        if i != None and i > 1:
            roll_count = f" | Took {i} rolls."
        else:
            roll_count = ""
        poke_embed = discord.Embed()

        name = self.GenerateFusedName(p1-1,p2-1)
        name1 = pokemon_names_fusion[p1-1]
        name2 = pokemon_names_fusion[p2-1]
        name = name.title()
        poke_embed.title = f'{name.title()}'
        poke_embed.set_footer(text=f"{name1.title()} + {name2.title()} | {custom}{roll_count}")
        poke_embed.description = f"**[Image Link]({image_url})**"
        if len(ctx.guild.members) >= 100:
            poke_embed.set_thumbnail(url=image_url)
        else:
            poke_embed.set_image(url=image_url)
        if sent is None:
            sent = await ctx.reply(embed=poke_embed)
        else:
            await sent.edit(embed=poke_embed, content=None)
        if len(ctx.guild.members) < 100:
            poke_embed.set_thumbnail(url=image_url)
            poke_embed.set_image(url="")
            await asyncio.sleep(15)
            await sent.edit(embed=poke_embed, content=None)
        return
                
    @commands.command(help="Get a fused Pokemon.", aliases=["fuse", "Fuse", "f", "pf", "Pf", "pfuse"])
    @commands.cooldown(rate=1, per=15, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def pokefuse(self, ctx):
        query = Helpers.CommandStrip(self, ctx.message.content)
        id1 = -1
        id2 = -1
        random_form = False
        if not query.strip():
            ctx.command.reset_cooldown(ctx)
            return
        query = query.split(',')
        if len(query) > 1:
            mon1 = query[0].strip()
            mon2 = query[1].strip()
        else:
            mon1 = query[0]
            mon2 = None
            random_form = True
        if mon1.lower() == "something":
            mon1 = random.choice(pokemon_names_fusion)
        if mon2 == None:
            mon2 = random.choice(pokemon_names_fusion)
        if mon2.lower() == "something":
            mon2 = random.choice(pokemon_names_fusion)
        if mon1.lower() in pokemon_names_fusion:            
            id1 = pokemon_names_fusion.index(mon1.lower()) + 1
        else:
            await ctx.reply(f"{mon1} is not available for fusion.")
            ctx.command.reset_cooldown(ctx)
            return
        if mon2.lower() in pokemon_names_fusion:
            id2 = pokemon_names_fusion.index(mon2.lower()) + 1
        else:
            await ctx.reply(f"{mon2} is not available for fusion.")
            ctx.command.reset_cooldown(ctx)
            return
        if random_form:
            if random.randint(0,1) == 1:
                id_temp = id1
                id1 = id2
                id2 = id_temp
        results = self.GetFusion(id1,id2)
        fusion = results[0]
        custom = "Auto-Generated"
        try:
            if 'CustomBattlers' in fusion:
                custom = "Custom Made"
            if results[1]-1 == results[2]-1:
                name = f"Mega {pokemon_names_fusion[results[1]-1]}"
            else:
                name = self.GenerateFusedName(results[1]-1,results[2]-1)        
            name1 = pokemon_names_fusion[results[1]-1]
            name2 = pokemon_names_fusion[results[2]-1]
            name = name.title()
            fusion_embed = discord.Embed()
            image_file = discord.File(fusion, filename=f'fusion.png')
            if len(ctx.guild.members) >= 200:
                fusion_embed.set_thumbnail(url=f"attachment://fusion.png")
            else:
                fusion_embed.set_image(url=f"attachment://fusion.png")
                fusion_embed.title = f'{name.title()}'
                fusion_embed.set_footer(text=f"{name1.title()} + {name2.title()} | {custom}")
                sent = await ctx.reply(file=image_file, embed=fusion_embed)
                if len(ctx.guild.members) > 80:
                    await asyncio.sleep(12)
                    fusion_embed.set_thumbnail(url=f"attachment://fusion.png")
                    fusion_embed.set_image(url='')
                    await sent.edit(embed=fusion_embed)
        except Exception as e:
            await ctx.reply(f"Error getting fusion. Likely no combination for the requested Pokemon, sorry!")
            ctx.command.reset_cooldown(ctx)
            return

        

    @commands.command(help="Get a random fused Pokemon.", aliases=["rfuse", "RFuse", "Rfuse", "RFUSE", "rf"])
    @commands.cooldown(rate=1, per=15, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomfused(self, ctx):
        fusion_result = self.GetRandomFusion()      
        sent = None  
        i = None
        image_url = fusion_result[0]
        p1 = fusion_result[1][0]
        p2 = fusion_result[1][1]
        if "Custom" in image_url:
            custom = "Custom Made"
        else:
            custom = "Auto Generated"
        if i != None and i > 1:
            roll_count = f" | Took {i} rolls."
        else:
            roll_count = ""
        poke_embed = discord.Embed()
        
        name = self.GenerateFusedName(p1-1,p2-1)
        name1 = pokemon_names_fusion[p1-1]
        name2 = pokemon_names_fusion[p2-1]
        name = name.title()
        poke_embed.title = f'{name.title()}'
        poke_embed.set_footer(text=f"{name1.title()} + {name2.title()} | {custom}{roll_count}")
        poke_embed.description = f"**[Image Link]({image_url})**"
        if len(ctx.guild.members) >= 100:
            poke_embed.set_thumbnail(url=image_url)
        else:
            poke_embed.set_image(url=image_url)
        if sent is None:
            sent = await ctx.reply(embed=poke_embed)
        else:
            await sent.edit(embed=poke_embed, content=None)
        if len(ctx.guild.members) < 100:
            poke_embed.set_thumbnail(url=image_url)
            poke_embed.set_image(url="")
            await asyncio.sleep(15)
            await sent.edit(embed=poke_embed, content=None)
        return
        
    @commands.command(help="Get a fused Pokemon.")
    @commands.cooldown(rate=1, per=15, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def pokefuseOLD(self, ctx):

        query = Helpers.CommandStrip(self, ctx.message.content)
        if not query.strip():
            ctx.command.reset_cooldown(ctx)
            return
        query = query.split(',')
        if len(query) > 1:
            mon1 = query[0].strip()
            mon2 = query[1].strip()
        else:
            mon1 = query[0]
            mon2 = None
        if mon1.lower() == "something":
            if mon2 == None or mon2.lower() == "something":
                await ctx.reply(f"You're thinking of !rf.")
                return
            mon1 = random.choice(pokemon_names_fusion)   
        if mon2 != None:
            if mon2.lower() == "something":
                mon2 = random.choice(pokemon_names_fusion)
        if mon1.lower() in pokemon_names_fusion:            
            index1 = pokemon_names_fusion.index(mon1.lower()) + 1
            if mon2 == None:
                index2 = random.randint(1,420)
            elif mon2.lower() not in pokemon_names_fusion:
                await ctx.reply(f"{mon2} is not available for fusion.")
                ctx.command.reset_cooldown(ctx)
                return
            else:
                index2 = pokemon_names_fusion.index(mon2.lower()) + 1
            r = random.randint(0,1)
            if r == 1 and mon2 == None:
                t = index2
                index2 = index1
                index1 = t               
            if (index1,index2) in self.fusion_cache:
                image_url = self.fusion_cache[(index1,index2)]
                if 'Custom' in image_url:
                    custom_found = True
                else:
                    custom_found = False
                print("Retrieved from cache!")
            else:
                custom_url = f"https://gitlab.com/infinitefusion/sprites/-/raw/master/CustomBattlers/{index1}/{index1}.{index2}.png"
                fallback_url = f"https://gitlab.com/infinitefusion/sprites/-/raw/master/Battlers/{index1}/{index1}.{index2}.png"
                custom_request = requests.get(custom_url)
                if custom_request.status_code != 404:
                    image_url = custom_url
                    custom_found = True
                else:
                    image_url = fallback_url
                    custom_found = False
                self.AddToFusionCache((index1,index2), image_url)
            if custom_found == True:
                custom = "Custom Made"
            else:
                custom = "Auto Generated"
            if index1 == index2 and custom_found == False:
                await ctx.reply(f"No custom fusion for double {mon1.title()}s.")
                ctx.command.reset_cooldown(ctx)
                return 
            poke_embed = discord.Embed()
            name = self.GenerateFusedName(index1-1,index2-1)
            name1 = pokemon_names_fusion[index1-1]
            name2 = pokemon_names_fusion[index2-1]
            poke_embed.title = f'{name.title()}'
            poke_embed.set_footer(text=f"{name1.title()} + {name2.title()} | {custom}")
            poke_embed.description = f"**[Image Link]({image_url})**"
            if len(ctx.guild.members) >= 100:
                poke_embed.set_thumbnail(url=image_url)
            else:
                poke_embed.set_image(url=image_url)
            sent = await ctx.reply(embed=poke_embed)
            if len(ctx.guild.members) < 100:
                poke_embed.set_thumbnail(url=image_url)
                poke_embed.set_image(url="")
                await asyncio.sleep(15)
                await sent.edit(embed=poke_embed)
            return
        else:
            await ctx.reply(f"{mon1} is not available for fusion.")
            ctx.command.reset_cooldown(ctx)
            return


    @commands.command(help="Get a random Pokemon move.", aliases=['rmove', 'Rmove', 'RMove', 'RMOVE'])
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randommove(self, ctx):
        api_results = Helpers.GetWebPage(self, 'https://pokeapi.co/api/v2/move/?offset=0&limit=20000')
        if api_results:
            move = random.choice(api_results.json()['results'])['name']
            move = move.title().replace("-", " ")
            await ctx.reply(f'{move}')
        else:
            await ctx.reply(f'Something went wrong when contacting the API.')

    @commands.command(help="Get a random Pokemon ability.", aliases=['rability', 'Rability', 'RAbility', 'RABILITY'])
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomability(self, ctx):
        api_results = Helpers.GetWebPage(self, 'https://pokeapi.co/api/v2/ability/?offset=0&limit=20000')
        if api_results:
            ability = random.choice(api_results.json()['results'])['name']
            ability = ability.title().replace("-", " ")
            await ctx.reply(f'{ability}')
        else:
            await ctx.reply(f'Something went wrong when contacting the API.')

    @commands.command(help="Get a random Pokemon item.", aliases=['ritem', 'Ritem', 'RItem', 'RITEM'])
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomitem(self, ctx):
        api_results = Helpers.GetWebPage(self, 'https://pokeapi.co/api/v2/item/?offset=0&limit=485')
        if api_results:
            item = random.choice(api_results.json()['results'])['name']
            item = item.title().replace("-", " ")
            await ctx.reply(f'{item}')
        else:
            await ctx.reply(f'Something went wrong when contacting the API.')

        

    @commands.command(help="Get information about a Pokemon (Gen 1 - 7).", aliases=['pdt', 'Pdt', 'PDT', 'pdata', 'pd'])
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def pokedata(self, ctx):
        poke = Helpers.CommandStrip(self, ctx.message.content).replace(' ', '-')
        api_results = Helpers.GetWebPage(self, f'https://pokeapi.co/api/v2/pokemon/{poke}/')
        if api_results:
            results_json = api_results.json()
            name = results_json['name'].title()
            number = results_json['id']
            if number < 100:
                number_string = f'0{number}'
            else:
                number_string = str(number)
            sprite = results_json['sprites']['front_default']

            abilities = results_json['abilities']
            abilities_formatted = []
            for a in reversed(abilities):
                ab_str = ''
                ab_str += f"{a['ability']['name'].title().replace('-', ' ')}"
                if a['is_hidden']:
                    ab_str += ' (Hidden)'
                abilities_formatted.append(ab_str)                
            
            typing = results_json['types']
            typing_formatted = []
            for t in reversed(typing):
                typing_formatted.append(t['type']['name'].title())
            
            stats = results_json['stats']                     # API stat order is Spe, SpD, SpA, Def, Atk, HP
            poke_embed = discord.Embed()
            poke_embed.title = f'{name.title()} - #{number}'
            if sprite != None:
                poke_embed.set_thumbnail(url=sprite)
            poke_embed.add_field(name='Type', value=' / '.join(typing_formatted), inline=True)
            poke_embed.add_field(name='Abilities', value=', '.join(abilities_formatted), inline=False)
            poke_embed.add_field(name='Base', value=(
                f"**HP:** {stats[5]['base_stat']}\n"
                f"**ATK:** {stats[4]['base_stat']}\n"
                f"**DEF:** {stats[3]['base_stat']}\n"
                ), inline=True)
            poke_embed.add_field(name='Stats', value=(
                f"**SP.ATK:** {stats[2]['base_stat']}\n"
                f"**SP.DEF:** {stats[1]['base_stat']}\n"
                f"**SPE:** {stats[0]['base_stat']}\n"
            ), inline=True)
            poke_embed.set_footer(text=f'More info: https://pokemondb.net/pokedex/{poke}')
            await ctx.reply(embed=poke_embed)
            
        else:
            await ctx.reply(f'No pokemon with that name or number found.')
    
    @commands.command(help="Generate a Pokemon name.", aliases=['rname', 'RName', 'Rname'])
    @commands.cooldown(rate=1, per=2, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def randomname(self, ctx):
        number = Helpers.FuzzyIntegerSearch(self, Helpers.CommandStrip(self, ctx.message.content))
        names = []
        if number == None:
            number = 1
        elif number < 1:
            number = 1
        elif number > 6:
            number = 6

        for i in range(number):
            names.append(self.GenerateName())
        name_string =  ', '.join(names)
        await ctx.reply(f'{name_string}')

    @commands.command(help="Generate an entirely random new Pokemon.", aliases=['gpoke', 'genpoke', 'GPoke', 'Genpoke', 'gmon'])
    @commands.cooldown(rate=1, per=5, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def generatepokemon(self, ctx):
        types = ['normal','fire','water','grass','fighting','flying','poison','electric','ground','psychic','rock','ice','bug','dragon','ghost','dark','steel','fairy']
        

        requested_stage = Helpers.CommandStrip(self, ctx.message.content).lower()
        if 'bab' in requested_stage:
            requested_stage = 1
        elif 'mid' in requested_stage or 'nfe' in requested_stage:
            requested_stage = 2
        elif 'full' in requested_stage:
            requested_stage = 3
        elif 'legend' in requested_stage:
            requested_stage = 4
        elif 'random' in requested_stage:
            requested_stage = 5
        else:
            requested_stage = 0

        stats, stage, stat_total = self.GenerateStats(requested_stage)

        await ctx.trigger_typing()

        name = self.GenerateName()

        # Generate Typing
        if random.randint(0,100) <= 40:
            # single typed
            typing = random.choice(types).title()
        else:
            # dual typed
            t1 = random.choice(types).title()
            while True:
                t2 = random.choice(types).title()
                if t1 != t2:
                    break
            typing = f'{t1}/{t2}'

        ## Generate Stats 
        #stats = []
        #min_base_bst = 500
        #max_base_bst = 720
        ## get a random base total to use
        #base_bst = random.randint(min_base_bst,max_base_bst)
        ## decide the stat weight
        ## clamped float value between 0.8 and 1.0, varying based on the base total
        ## higher base totals will tend to have higher stat weight
        ## On average (over 10000 runs) this process should result in an average BST of about 525, min 280, max 725.
        #stat_weight = round(max(min((base_bst / max_base_bst) * 1.5, 1.0), 0.8), 2)
        #for i in range(6):
        #    stat = random.randint(100,200) + random.randint(-65,55)
        #    if stat >= 150:
        #        for s in stats:
        #            if s >= 150:
        #                stat -= random.randint(25,149)
        #                break
        #    elif stat <= 70:
        #        for s in stats:
        #            if s <= 70:
        #                stat += random.randint(15, 50)
        #                break
        #    # subtract the stat from the remaining stat total, multiplying by stat weight
        #    # doing this should get more relatively accurate stat spreads ON AVERAGE (you can still end up with absolutely pathetic stats)
        #    base_bst -= round(stat * stat_weight)
        #    if base_bst <= 80:
        #        stat = random.randint(5,80)
        #    stats.append(stat)
        #random.shuffle(stats)
        #stat_total = sum(stats)

        # Generate Abilities
        api_results = Helpers.GetWebPage(self, 'https://pokeapi.co/api/v2/ability')
        if api_results:
            ability1 = random.choice(api_results.json()['results'])['name']
            ability1 = ability1.title().replace("-", " ")
            while True:
                ability2 = random.choice(api_results.json()['results'])['name']
                ability2 = ability2.title().replace("-", " ")

                ability3 = random.choice(api_results.json()['results'])['name']
                ability3 = ability3.title().replace("-", " ")

                if ability1 != ability2 and ability1 != ability3 and ability2 != ability3:
                    break
        else:
            await ctx.reply(f'Something went wrong when contacting the API.')
            return

        poke_embed = discord.Embed()
        poke_embed.title = f'{name}'
        poke_embed.add_field(name='Type', value=typing, inline=True)
        poke_embed.add_field(name='Stage', value=stage, inline=True)
        poke_embed.add_field(name='Abilities', value=f'{ability1}, {ability2}, {ability3} (Hidden)', inline=False)
        poke_embed.add_field(name=f'BST: {stat_total}', value=(
            f"**HP:** {stats[0]}\n"
            f"**ATK:** {stats[1]}\n"
            f"**DEF:** {stats[2]}\n"
            ), inline=True)
        poke_embed.add_field(name=f'Stats', value=(
            f"**SP.ATK:** {stats[3]}\n"
            f"**SP.DEF:** {stats[4]}\n"
            f"**SPE:** {stats[5]}\n"
        ), inline=True)
        await ctx.reply(embed=poke_embed)
        

        


def setup(client):
    client.add_cog(Pokemon(client))