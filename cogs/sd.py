import discord
import logging
import os.path
import json
import os
import io
import base64
import urllib.request
import requests
from PIL import Image
import random
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM
from bot import current_settings
from bot import convo
from bingart import BingArt
from bingart import AuthCookieError, PromptRejectedError
import asyncio
import functools
from internal.data.badwords import badwords
import re


class sd(commands.Cog):    

    def __init__(self, client):
        self.client = client
        self.server_url = "http://10.0.0.1:7860"
        out_dir = "X:\JimBot2\JimBot2\JimBot\internal\data\images"
        self.realmodels = ["dreamshaper_8.safetensors [879db523c3]", "jamJustAnotherMerge_v19BakedvaePruned.safetensors [4bfc37dab6]", "dogemix_v20.safetensors [c49d4a5216]"]
        self.animemodels = ["mistoonAnime_v30.safetensors [da52bf6da0]", "meinamix_meinaV10.safetensors [77b7dc4ef0]", "oneFORALLAnime_v35DPOVAE.safetensors [0677115c4b]"]
        self.bing = BingArt(auth_cookie=current_settings["keys"]["bing"])
        self.current_model = ""

    def generate_image(self, payload):
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(f'{self.server_url}/sdapi/v1/txt2img', headers={'Content-Type':'application/json'},data=data)
        response = urllib.request.urlopen(request)
        return json.loads(response.read().decode('utf-8'))

    def generate_bing_image(self, prompt):
        try:
            results = self.bing.generate_images(prompt)
            urls = []
            for img in results["images"]:
                urls.append(img)
            return urls
        except AuthCookieError:
            return -1
        except PromptRejectedError:
            return -2

    async def generate_bing_image_async(self, prompt):
        try:
            fn = functools.partial(self.bing.generate_images, prompt)
            results = await asyncio.get_event_loop().run_in_executor(None, fn)
            urls = []
            for r in results["images"]:
                urls.append(r["url"])
            if len(urls) > 0:
                return urls
            else:
                return -2
        except AuthCookieError:
            return -1
        except PromptRejectedError:
            return -2
        
    def download_images(self, urls):
        print('Images received. Downloading.')
        images = []
        for url in urls:
            print(url)
            response = requests.get(url)
            image = Image.open(io.BytesIO(response.content))
            images.append(image)
        return images
    
    def combine_images(self, images, rows, cols):
        print(f'Combining {len(images)} images.')
        w, h = images[0].size
        grid = Image.new('RGB', size=(cols*w, rows*h))
        grid_w, grid_h = grid.size

        for i, img in enumerate(images):
            grid.paste(img, box=(i%cols*w, i//cols*h))
        return grid

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)
    
    #@commands.command(aliases=["b"], help="Create an image")    
    #@commands.cooldown(rate=1, per=120, type=BucketType.guild)
    #@commands.has_role("Bot Use")
    #@commands.guild_only()
    #async def bingold(self, ctx):
    #    await ctx.trigger_typing()
    #    msg = Helpers.CommandStrip(self,ctx.message.content)
    #    if len(msg) > 1:
    #        img = self.generate_bing_image(msg)
    #        if img == -1:
    #            await ctx.reply("Image generation failed due to authorisation error. Command will likely no longer work.")
    #        elif img == -2:
    #            await ctx.reply("Image generation was rejected due to a restricted prompt. Bing will not generate images of nudity, violence, or public figures.")
    #        elif img == None:
    #            await ctx.reply("Image generation failed.")
    #        else:
    #            await ctx.reply(img)
    #    else:
    #        await ctx.command.reset_cooldown(ctx)
    #        await ctx.reply("You provided no prompt.")     

    @commands.command(aliases=["b"], help="Create an image")    
    @commands.cooldown(rate=1, per=600, type=BucketType.guild)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def bing(self, ctx):
        msg = Helpers.CommandStrip(self,ctx.message.content)
        if re.compile('|'.join(badwords),re.IGNORECASE).search(msg):
            await ctx.reply("Your prompt contained a term very likely to be rejected by Bing. Cooldown has been reset. Bing will not generate images of nudity, violence, or public figures. Please reword your prompt.")
            ctx.command.reset_cooldown(ctx)
            return
        if len(msg) > 1:
            sent = await ctx.reply("Image is generating. Please be patient - this may take a long time (>5 minutes).")
            await ctx.trigger_typing()
            task = asyncio.create_task(self.generate_bing_image_async(prompt=msg))
            await task
            urls = task.result()
            await sent.delete()
            await ctx.trigger_typing()
            if urls == -1:
                await ctx.reply("Image generation failed due to authorisation error. Command will likely no longer work.")
            elif urls == -2:
                await ctx.reply("Image generation was rejected due to a restricted prompt. Bing will not generate images of nudity, violence, or public figures.")
                ctx.command.reset_cooldown(ctx)
            elif urls == None:
                await ctx.reply("Image generation failed.")
            else:
                imgs = self.download_images(urls)
                cols = 1
                rows = 1
                if len(imgs) >= 3:
                    cols = 2
                    rows = 2
                elif len(imgs) == 2:
                    cols = 2
                grid = self.combine_images(imgs, rows, cols)
                grid.save(f'./internal/data/images/bing{ctx.guild.id}.jpg')
                image_file = discord.File(f'./internal/data/images/bing{ctx.guild.id}.jpg', filename='bing.jpg')
                await ctx.reply(file=image_file)
                ctx.command.reset_cooldown(ctx)
        else:
            ctx.command.reset_cooldown(ctx)
            await ctx.reply("You provided no prompt.")  

    #@commands.command(aliases=[], help="Create an image")    
    #@commands.cooldown(rate=1, per=60, type=BucketType.channel)
    #@commands.has_role("Bot Use")
    #@commands.guild_only()
    #async def flux(self, ctx):
    #    await ctx.trigger_typing()
    #    try:
    #        requests.get(self.server_url, timeout=1.5)
    #    except requests.ConnectionError:
    #        await ctx.reply("This command is not currently available.")
    #        return
    #    msg = Helpers.CommandStrip(self,ctx.message.content)
    #    msg = Helpers.DiscordEmoteConvert(self, msg)
    #    if len(msg) > 1:
    #        width, height = 1024, 1024
    #        cfg = 1
    #        steps = 4
    #        sampler = "Euler"
    #        model = "flux1DevV1V2Flux1_flux1SchnellBNBNF4.safetensors [e6cba6afca]"
    #        pos = ""
    #        neg = ""
    #        width = random.choice([1024,1024,864,1280])
    #        if width == 864:
    #            height = random.choice([1024,1280])
    #        elif width == 1280:
    #            height = random.choice([1024,864])
    #        payload = {
    #            "prompt": f"{pos}, {msg}",
    #            "negative_prompt": f"{neg}",
    #            "seed": -1,
    #            "steps": steps,
    #            "width": width,
    #            "height": height,
    #            "cfg_scale": cfg,
    #            "sampler_name": sampler,
    #            "n_iter": 1,
    #            "batch_size": 1,
    #            "enable_hr": False,
    #            "override_settings": {
    #                'sd_model_checkpoint' : model,
    #                'sd_vae' : 'None'
    #            }
    #        }
    #        response = self.generate_image(payload)
    #        image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
    #        image.save(f'./internal/data/images/sd{ctx.author.id}.png')
    #        if not ctx.message.channel.is_nsfw():
    #            image_file = discord.File(f'./internal/data/images/sd{ctx.author.id}.png', filename='SPOILER_sd.png')
    #            sent = await ctx.reply(file=image_file)
    #        else:
    #            image_file = discord.File(f'./internal/data/images/sd{ctx.author.id}.png', filename='sd.png')
    #            sent = await ctx.reply(file=image_file)
    #    else:
    #        response = f'You didn\'t enter a message.'
    #        await ctx.reply(response)
    #        return

    @commands.command(aliases=["fms"], help="Create a fake pokemon")    
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def fakemonsprite(self, ctx):
        await ctx.trigger_typing()
        try:
            requests.get(self.server_url, timeout=1.5)
        except:
            await ctx.reply("This command is not currently available.")
            return
        msg = Helpers.CommandStrip(self,ctx.message.content)
        msg = Helpers.DiscordEmoteConvert(self, msg)
        if len(msg) > 1:
            self.current_model = "dreamshaperXL_v21TurboDPMSDE.safetensors [4496b36d48]"
            neg = "((nsfw, naked, nude, sexy, underwear, partially clothed, erotic, nipples, breasts, penis, vagina, pussy, ass, sex))"
            pos = "pokemon, creature, cartoony, solo, full body,"
            sampler = "DPM++ SDE Karras"
            cfg = 2
            steps = 8
            vae = "sdxl_vae.safetensors"
            sprite = True
            if not ctx.message.channel.is_nsfw():
                neg = neg + "(nsfw,nude),"
            height = 768
            if "trainer" in msg.lower():
                pos = "__pktrainer__, full body, blank background"
            elif "frontback" in msg.lower() or "backfront" in msg.lower():
                pos = "__pkspritebf__, blank background"
                neg = f"{neg},((human))"
            else:
                pos = "__pksprite__, blank background"
                neg = f"{neg},((human))"
            pruned = msg.lower().replace("trainer", "")
            pruned = pruned.replace("frontback","")
            pruned = pruned.replace("backfront","")
            pruned = pruned.replace("artwork","")
            pruned = pruned.replace("pokemon","")
            pos = f"{pos},{pruned}"
            if "pkspritebf" in pos:
                width = 1536
            else:
                width = 768
            payload = {
                "prompt": f"{pos}",
                "negative_prompt": f"{neg}",
                "seed": -1,
                "steps": steps,
                "width": width,
                "height": height,
                "cfg_scale": cfg,
                "sampler_name": sampler,
                "n_iter": 1,
                "batch_size": 1,
                "enable_hr": False,
                "override_settings": {
                    'sd_model_checkpoint' : self.current_model,
                    'sd_vae' : vae
                },
                "alwayson_scripts": {"ADetailer": {"args": [True, False, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.3, "ad_dilate_erode": 4, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 6, "ad_mask_k_largest": 5, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "face_yolov8s.pt", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "Euler a", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.4, "ad_dilate_erode": 4, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 4, "ad_mask_k_largest": 0, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "None", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []},{"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.4, "ad_dilate_erode": 4, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 4, "ad_mask_k_largest": 0, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "None", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}]}}
            }

            response = self.generate_image(payload)
            image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
            image.save(f'./internal/data/images/fakemon{ctx.author.id}.png')
            img = Image.open(f'./internal/data/images/fakemon{ctx.author.id}.png')
            if sprite:
                new_img = img.resize((int(width/8), int(height/8)), resample=Image.NEAREST)
                new_img = new_img.convert('P', palette=Image.ADAPTIVE, colors=64)
                new_img = new_img.resize((width,  height), resample=Image.NEAREST)
                new_img.save(f'./internal/data/images/fakemon{ctx.author.id}.png')
        else:
            response = f'You didn\'t enter a message.'
        image_file = discord.File(f'./internal/data/images/fakemon{ctx.author.id}.png', filename='SPOILER_fakemon.png')
        sent = await ctx.reply(file=image_file)

    @commands.command(aliases=["fm"], help="Create a fake pokemon")    
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def fakemon(self, ctx):
        await ctx.trigger_typing()
        try:
            requests.get(self.server_url, timeout=1.5)
        except:
            await ctx.reply("This command is not currently available.")
            return
        msg = Helpers.CommandStrip(self,ctx.message.content)
        msg = Helpers.DiscordEmoteConvert(self, msg)
        if len(msg) >= 1:
            self.current_model = "catCitronAnimeTreasure_ilV9.safetensors [3761477265]"
            if "trainer" in msg.lower():
                msg = msg.lower().replace("trainer","")
                neg = "low quality, worst quality, lazynsfw, detailed background"
                pos = "masterpiece, best quality, absurdres, white background, blank background"
                lora = "<lora:Pokemon-Trainer-SpritesV2_Fp:1>, pixel art, simple background, full body,{|holding poke ball,}"
            else:
                neg = "low quality, worst quality, (((orb, sphere, round, ball))), ((multiple characters, group, crowd), (((ball, round, circle))), no characters, landscape"
                pos = "masterpiece, best quality, absurdres, ((black background, blank background))"
                lora = "<lora:Fakemon-_Sugimori:1> (Fakemon),Sugimori, pokemon \(creature\), no humans,animal, (solo))"
            sampler = "Euler a"
            cfg = 5.5
            steps = 30
            enable_hr = 'False'
            hr_scale = 1.35
            hr_second_pass_steps = 15
            hr_upscaler = 'Latent'
            denoising_strength = 0.6
            if not ctx.message.channel.is_nsfw():
                pos = pos + ",rating_safe, non-h"
                neg = neg + ",(lazynsfw), (((nsfw, nude, pussy, penis, naked, nipples, breasts, rating_explicit, explicit))) (gore, guro, pussy, penis, sex, vaginal, anal, semen, cum, ecchi, sexual, panties)"
            if len(msg.lower().split('!neg')) > 1:
                cneg = msg.lower().split('!neg')[1]
                msg = msg.lower().split('!neg')[0]
            else:
                cneg = ""
            if not ctx.message.channel.is_nsfw():
                neg = neg + ", nsfw"
                pos = pos + ""
            payload = {
                "prompt": f"{pos}, {msg}, {lora}",
                "negative_prompt": f"{neg},f{cneg}",
                "seed": -1,
                "steps": steps,
                "width": 1024,
                "height": 1024,
                "cfg_scale": cfg,
                "sampler_name": sampler,
                "n_iter": 1,
                "batch_size": 1,
                "enable_hr": enable_hr,
                "hr_upscaler": hr_upscaler,
                "hr_second_pass_steps": hr_second_pass_steps,
                "hr_scale": hr_scale,
                "denoising_strength" : denoising_strength,
                "override_settings": {
                    'sd_model_checkpoint' : self.current_model,
                    'sd_vae' : "sdxl_vae.safetensors"
                },
                "alwayson_scripts": {"Kohya HRFix Integrated":{"args" :[{"0" : True,"1" : 3,"2" : 2,"3" : 0,"4" : 0.35,"5" : True,"6" : "bicubic","7" : "bicubic"}]},"ADetailer": {"args": [True, False, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.3, "ad_dilate_erode": 4, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 6, "ad_mask_k_largest": 5, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "face_yolov8s.pt", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "Euler a", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.4, "ad_dilate_erode": 4, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 4, "ad_mask_k_largest": 0, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "None", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []},{"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.4, "ad_dilate_erode": 4, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 4, "ad_mask_k_largest": 0, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "None", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}]}}
            }
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.generate_image(payload))
            #response = self.generate_image(payload)
            image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
            image.save(f'./internal/data/images/fakemon{ctx.author.id}.png')
        else:
            response = f'You didn\'t enter a message.'
        image_file = discord.File(f'./internal/data/images/fakemon{ctx.author.id}.png', filename='SPOILER_fakemon.png')
        sent = await ctx.reply(file=image_file)
    # #@commands.command(aliases=[], help="Create an image")    
    # #@commands.cooldown(rate=1, per=30, type=BucketType.user)
    # #@commands.has_role("Bot Use")
    # #@commands.guild_only()
    # async def flux(self, ctx):
    #     await ctx.trigger_typing()
    #     try:
    #         requests.get(self.server_url, timeout=1.5)
    #     except:
    #         await ctx.reply("This command is not currently available.")
    #         return
    #     msg = Helpers.CommandStrip(self,ctx.message.content)
    #     msg = Helpers.DiscordEmoteConvert(self, msg)
    #     if len(msg) > 1:
    #         width = 1024
    #         height = 1024
    #         steps = 12
    #         model = "fluxFusionV24StepsGGUFNF4_V2NF4AIO.safetensors"
    #         pos = f"highres, 4k, 8k, amazing quality, {msg}"
    #         width = random.choice([1024,1024,864,1280])
    #         if width == 864:
    #             height = random.choice([1024,1280])
    #         elif width == 1280:
    #             height = random.choice([1024,864])
    #         payload = {
    #             "prompt": f"{pos}, {msg}",
    #             "seed": -1,
    #             "steps": steps,
    #             "width": width,
    #             "height": height,
    #             "cfg_scale": 1,
    #             "scheduler": 'Simple',
    #             "sampler_name": 'Euler',
    #             "n_iter": 1,
    #             "batch_size": 1,
    #             "enable_hr": False,
    #             "override_settings": {
    #                 'sd_model_checkpoint' : model
    #             }
    #         }

    #         response = self.generate_image(payload)
    #         image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
    #         image.save(f'./internal/data/images/sd{ctx.author.id}.png')
    #     else:
    #         response = f'You didn\'t enter a message.'
    #     if not ctx.message.channel.is_nsfw():
    #         image_file = discord.File(f'./internal/data/images/sd{ctx.author.id}.png', filename='SPOILER_sd.png')
    #         sent = await ctx.reply(file=image_file)
    #     else:
    #         image_file = discord.File(f'./internal/data/images/sd{ctx.author.id}.png', filename='sd.png')
    #         sent = await ctx.reply(file=image_file)

    @commands.command(aliases=["sdxl", "sd"], help="Create an image")    
    @commands.cooldown(rate=1, per=30, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def stablediffusion_xl(self, ctx):
        await ctx.trigger_typing()
        try:
            requests.get(self.server_url, timeout=1.5)
        except:
            await ctx.reply("This command is not currently available.")
            return
        msg = Helpers.CommandStrip(self,ctx.message.content)
        msg = Helpers.DiscordEmoteConvert(self, msg)
        if len(msg) > 1:
            width = 1024
            height = 1024
            enable_hr = 'False'
            hr_scale = '1.5'
            hr_second_pass_steps = 5
            hr_upscaler = 'Latent'
            denoising_strength = 0.6
            posSuf = ""

            xl_real_models_old = ["realvisxlV50_v50LightningBakedvae.safetensors [fabcadd933]"]
            xl_real_models = ["wildcardxXLFusion_fusionOG.safetensors [22ebc61141]"]
            xl_anime_realistic = ["illustrij_v18.safetensors [3c39254028]"]
            sprite = False
            vae = "sdxl_vae.safetensors"
            if "anime" in msg.lower() or "lora:pixel" in msg.lower():
                if "realistic" in msg.lower() and "lora:pixel" not in msg.lower():
                    if self.current_model not in xl_anime_realistic or random.randint(0,8) == 1:
                        self.current_model = random.choice(xl_anime_realistic)
                    msg = msg.replace("anime","")
                    msg = msg.replace("realistic", "")
                else:
                    self.current_model = "catCitronAnimeTreasure_ilV9.safetensors [3761477265]"
                    msg = msg.replace('anime','')
                neg = "lowres, worst quality, zoomed out, far away, bad quality, bad anatomy, bad hands, sketch, signature, watermark, logo, border,"
                if self.current_model in xl_anime_realistic:
                    pos = "realistic, 3d, "
                else:
                    pos = ""
                posSuf = ", <lora:illustrious_masterpieces_v3:1> masterpiece, best quality, very aesthetic"

                #if "style" not in msg.lower() and "ilartist" not in msg.lower():
                #    pos = pos + ", (anime screencap style), flat colours, outlines, shading, ("
                #else:
                #    pos = pos + ",("

                sampler = "Euler a"
                cfg = 5.5
                steps = 30
                enable_hr = 'False'
                hr_scale = 1.2
                hr_second_pass_steps = 10
                hr_upscaler = '4x_foolhardy_Remacri'
                denoising_strength = 0.35
                if not ctx.message.channel.is_nsfw():
                    pos = pos + ", (general)"
                    neg = neg + "(explicit), ((lazynsfw)), (((nsfw, nude, pussy, penis, naked, nipples, breasts, rating_explicit, loli, shota, child)))"
                '''else:
                    self.current_model = "lunarcherrymix_v22BaseIllustrxl20.safetensors [6a22ffd713]"
                    msg = msg.replace("anime","")
                neg = "low quality, worst quality, ((logo, qr code, text, english text, watermark, japanese text)), (loli, shota, child, gore, guro, pussy, penis, sex, vaginal, anal, semen, cum, ecchi, sexual, panties)"
                pos = "masterpiece, best quality, absurdres, "
                sampler = "Euler a"
                cfg = 5.5
                steps = 30
                enable_hr = 'True'
                hr_scale = 1.35
                hr_second_pass_steps = 15
                hr_upscaler = 'Latent'
                denoising_strength = 0.6
                if not ctx.message.channel.is_nsfw():
                    pos = pos + "rating_safe, non-h"
                    neg = neg + "(lazynsfw), (((nsfw, nude, pussy, penis, naked, nipples, breasts, rating_explicit, explicit)))"'''
            else:
                if random.randint(0,8) == 1 or self.current_model not in xl_real_models:
                    self.current_model = random.choice(xl_real_models)
                if "realistic" in msg.lower():
                    self.current_model = "juggernautXL_ragnarokBy.safetensors [dd08fa32f9]"
                    msg = msg.lower().replace("realistic", "")
                if "pkspif" in msg.lower() or "pk_trainer" in msg.lower() or "__pksprite" in msg.lower() or "__pktrainer" in msg.lower() or "pkspbf" in msg.lower():
                    self.current_model = "dreamshaperXL_v21TurboDPMSDE.safetensors [4496b36d48]"
                    sprite = True


                if self.current_model == "dreamshaperXL_v21TurboDPMSDE.safetensors [4496b36d48]":
                    neg = "BeyondSDXLv3, (((nsfw, nude, nipples, breasts, loli, shota, child, porn, softcore, hardcore)))"
                    pos = "best quality, high quality,"
                    if sprite == True:
                        neg = ""
                        pos = ""
                    sampler = "DPM++ SDE Karras"
                    cfg = 2
                    steps = 8
                    if not ctx.message.channel.is_nsfw():
                        neg = neg + "(nsfw,nude),"
                elif self.current_model == "realvisxlV50_v50LightningBakedvae.safetensors [fabcadd933]":
                    pos = ""
                    neg = "bad quality, worst quality, bad anatomy,  nsfw, nude, nipples, breasts, loli, shota, child, porn, softcore, hardcore"
                    cfg = 2
                    steps = random.randint(5,5)
                    sampler = "DPM++ SDE Karras"
                    enable_hr = 'True'
                    hr_scale = 1.5
                    hr_second_pass_steps = 5
                    hr_upscaler = 'Latent'
                    denoising_strength = 0.6
                elif self.current_model == "moxieDiffusionXL_v191.safetensors [5c19630a58]":
                    sampler = "Euler a"
                    steps = 30
                    cfg = random.randint(3,9)
                    neg = "ugly, deformed, noisy, blurry, low contrast, modernist, minimalist, abstract, plastic, long neck, asymmetrical eyes, signature, watermark, jpeg artifacts, cropped,"
                    pos = ""
                elif self.current_model == "wildcardxXLFusion_fusionOG.safetensors [22ebc61141]":
                    neg = "BeyondSDXLv3"
                    pos = f'<lora:dmd2_sdxl_4step_lora:0.7>,'
                    sampler = "Euler a"
                    cfg = 1.5
                    steps = random.randint(10,15)
                    enable_hr = 'True'
                    hr_scale = 1.5
                    hr_second_pass_steps = 7
                    hr_upscaler = 'Latent'
                    denoising_strength = 0.6
                    if not ctx.message.channel.is_nsfw():
                        neg = neg + "(nsfw, nude)"
                elif self.current_model == "valiantStallion_v30.safetensors [d2aa1d5cd3]":
                    neg = "score_4, score_5, loli, shota"
                    pos = "score_9, score_8_up, score_7_up, score_6_up, score_5_up, score_4_up, BREAK "
                    sampler = "DPM++ SDE"
                    cfg = 5
                    steps = 24
                elif self.current_model == "juggernautXL_ragnarokBy.safetensors [dd08fa32f9]":
                    cfg = round(random.uniform(3.0,6.0),2)
                    msg = msg.replace("realistic,","")
                    msg = msg.replace("realistic","")
                    steps = random.randint(30,40)
                    sampler = "DPM++ 2M Karras"
                    vae = "None"
                    enable_hr = 'True'
                    hr_scale = 1.5
                    hr_second_pass_steps = 15
                    hr_upscaler = 'Latent'
                    denoising_strength = 0.6
                    pos = ""
                    neg = "bad eyes, blurry, missing limbs, bad anatomy, cartoon, nsfw, nude, penis, breasts, pussy, vagina"
                elif self.current_model == "Dream_Diffusion_ Pony_V1 _By_ DICE.safetensors [70a97af393]":
                    cfg = random.randint(7,11)
                    steps = 35
                    sampler = "DPM++ 2M Turbo" 
                    pos = "(score_9, score_8_up, score_7_up), canon eos 5d mark iv, highly detailed, photorealistic, raw photo,"
                    neg = "score_4,score_5,score_6 ugly, deformed, bad quality, amateur drawing, beginner drawing, deformed, bad anatomy,"
                elif self.current_model == "damnPonyxlRealistic_damnV20Sweetspot.safetensors [12f1ac7a28]":
                    cfg = 7.5
                    steps = 25
                    sampler = "DPM++ 2M"
                    pos = "score_9, score_8_up,score_7_up, score_6_up, score_5_up, score_4_up,"
                    neg = "score_4, score_5,"
            
            width = random.choice([1024,1024,864,1280])
            if width == 864:
                height = random.choice([1024,1280])
            elif width == 1280:
                height = random.choice([1024,864])
            if sprite == True:
                height = 768
                if "pkspritebf" in msg.lower() or "pkspbf" in msg.lower():
                    width = 1536
                else:
                    width = 768
            if len(msg.lower().split('!neg')) > 1:
                cneg = msg.lower().split('!neg')[1]
                msg = msg.lower().split('!neg')[0]
            else:
                cneg = ""
            if not ctx.message.channel.is_nsfw():
                neg = neg + ", nsfw"
                pos = pos + ""
            payload = {
                "prompt": f"{pos}, {msg}, {posSuf}",
                "negative_prompt": f"{neg},{cneg}",
                "seed": -1,
                "steps": steps,
                "width": width,
                "height": height,
                "cfg_scale": cfg,
                "sampler_name": sampler,
                "n_iter": 1,
                "batch_size": 1,
                "enable_hr": enable_hr,
                "hr_upscaler": hr_upscaler,
                "hr_second_pass_steps": hr_second_pass_steps,
                "hr_scale": hr_scale,
                "denoising_strength" : denoising_strength,
                "override_settings": {
                    'sd_model_checkpoint' : self.current_model,
                    'sd_vae' : vae
                },
                "alwayson_scripts": {"ADetailer": {"args": [True, False, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.2, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.25, "ad_dilate_erode": 4, "ad_inpaint_height": 1024, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 1024, "ad_mask_blur": 4, "ad_mask_filter_method": "Area", "ad_mask_k": 5, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "face_yolov8s.pt", "ad_model_classes": "", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_scheduler": "Use same scheduler", "ad_steps": 28, "ad_tab_enable": True, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": True, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.48, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.3, "ad_dilate_erode": 4, "ad_inpaint_height": 1024, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 1024, "ad_mask_blur": 4, "ad_mask_filter_method": "Area", "ad_mask_k": 0, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0.036, "ad_model": "pussyV2.pt", "ad_model_classes": "", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "pussy, pussy juice, ", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_scheduler": "Use same scheduler", "ad_steps": 28, "ad_tab_enable": False, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": True, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.42, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.4, "ad_dilate_erode": 4, "ad_inpaint_height": 1024, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 1024, "ad_mask_blur": 4, "ad_mask_filter_method": "Area", "ad_mask_k": 4, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0.025, "ad_model": "penisV2.pt", "ad_model_classes": "", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "penis, ", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_scheduler": "Use same scheduler", "ad_steps": 28, "ad_tab_enable": False, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": True, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}]}, "API payload": {"args": []}, "Comments": {"args": []}, "ControlNet": {"args": [{"batch_image_dir": "", "batch_input_gallery": [], "batch_mask_dir": "", "batch_mask_gallery": [], "control_mode": "Balanced", "enabled": False, "generated_image": None, "guidance_end": 1, "guidance_start": 0, "hr_option": "Both", "image": None, "input_mode": "simple", "mask_image": None, "model": "None", "module": "None", "pixel_perfect": False, "processor_res": -1, "resize_mode": "Crop and Resize", "save_detected_map": True, "threshold_a": -1, "threshold_b": -1, "use_preview_as_input": False, "weight": 1}, {"batch_image_dir": "", "batch_input_gallery": [], "batch_mask_dir": "", "batch_mask_gallery": [], "control_mode": "Balanced", "enabled": False, "generated_image": None, "guidance_end": 1, "guidance_start": 0, "hr_option": "Both", "image": None, "input_mode": "simple", "mask_image": None, "model": "None", "module": "None", "pixel_perfect": False, "processor_res": -1, "resize_mode": "Crop and Resize", "save_detected_map": True, "threshold_a": -1, "threshold_b": -1, "use_preview_as_input": False, "weight": 1}, {"batch_image_dir": "", "batch_input_gallery": [], "batch_mask_dir": "", "batch_mask_gallery": [], "control_mode": "Balanced", "enabled": False, "generated_image": None, "guidance_end": 1, "guidance_start": 0, "hr_option": "Both", "image": None, "input_mode": "simple", "mask_image": None, "model": "None", "module": "None", "pixel_perfect": False, "processor_res": -1, "resize_mode": "Crop and Resize", "save_detected_map": True, "threshold_a": -1, "threshold_b": -1, "use_preview_as_input": False, "weight": 1}]}, "Dynamic Prompts v2.17.1": {"args": [True, False, 1, False, False, False, 1.1, 1.5, 100, 0.7, False, False, True, False, False, 0, "Gustavosta/MagicPrompt-Stable-Diffusion", ""]}, "DynamicThresholding (CFG-Fix) Integrated": {"args": [False, 7, 1, "Constant", 0, "Constant", 0, 1, "enable", "MEAN", "AD", 1]}, "Extra options": {"args": []}, "FreeU Integrated": {"args": [False, 1.01, 1.02, 0.99, 0.95]}, "HyperTile Integrated": {"args": [False, 256, 2, 0, False]}, "Kohya HRFix Integrated": {"args": [True, 3, 2, 0, 0.35, True, "bicubic", "bicubic"]}, "LatentModifier Integrated": {"args": [False, 0, "anisotropic", 0, "reinhard", 100, 0, "subtract", 0, 0, "gaussian", "add", 0, 100, 127, 0, "hard_clamp", 5, 0, "None", "None"]}, "Model keyword": {"args": [True, "keyword prompt", "keyword1, keyword2", "None", "textual inversion first", "None", "0.7", "None"]}, "MultiDiffusion Integrated": {"args": [False, "MultiDiffusion", 768, 768, 64, 4]}, "NegPiP": {"args": [True]}, "Never OOM Integrated": {"args": [False, False]}, "ReActor": {"args": [None, False, "0", "0", "inswapper_128.onnx", "CodeFormer", 1, True, "None", 1, 1, False, True, 1, 0, 0, False, 0.5, True, False, "CUDA", False, 0, "None", "", None, False, False, 0.5, 0, "tab_single"]}, "Refiner": {"args": [False, "", 0.8]}, "Seed": {"args": [-1, False, -1, 0, 0, 0]}, "SelfAttentionGuidance Integrated": {"args": [True, 0.5, 2]}, "StyleAlign Integrated": {"args": [False]}}
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.generate_image(payload))
            image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
            image.save(f'./internal/data/images/sd{ctx.author.id}.png')
            if sprite == True:
                img = Image.open(f'./internal/data/images/sd{ctx.author.id}.png')
                new_img = img.resize((int(width/8), int(height/8)), resample=Image.NEAREST)
                new_img = new_img.convert('P', palette=Image.ADAPTIVE, colors=64)
                new_img = new_img.resize((width,  height), resample=Image.NEAREST)
                new_img.save(f'./internal/data/images/sd{ctx.author.id}.png')
        else:
            response = f'You didn\'t enter a message.'
        if not ctx.message.channel.is_nsfw():
            image_file = discord.File(f'./internal/data/images/sd{ctx.author.id}.png', filename='SPOILER_sd.png')
            sent = await ctx.reply(file=image_file)
        else:
            image_file = discord.File(f'./internal/data/images/sd{ctx.author.id}.png', filename='sd.png')
            sent = await ctx.reply(file=image_file)



def setup(client):
    client.add_cog(sd(client))