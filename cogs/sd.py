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
        self.realmodels = ["dreamshaper_8.safetensors [879db523c3]", "beautyfool_v20.safetensors [d825c0badc]",  "jamJustAnotherMerge_v19BakedvaePruned.safetensors [4bfc37dab6]", "darksun_v41.safetensors [6d6e223662]", "realisticVisionV51_v51VAE.safetensors [ef76aa2332]", "photon_v1.safetensors [ec41bd2a82]", "animerge_v21.safetensors [ddd2ef83f6]"]
        self.animemodels = ["meinamix_meinaV10.safetensors [77b7dc4ef0]", "aniverse_thxEd14Pruned.safetensors [20a58e64b5]", "Anything-V3.0.ckpt [8712e20a5d]", "cartunafied_v3.safetensors [894530779c]", "meinapastel_v5AnimeIllustration.safetensors [ff1bb68db1]"]
        self.bing = BingArt(auth_cookie=current_settings["keys"]["bing"])

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

    @commands.command(aliases=["sd", "ig2"], help="Create an image")    
    @commands.cooldown(rate=1, per=70, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def paint(self, ctx):
        await ctx.trigger_typing()
        try:
            requests.get(self.server_url)
        except requests.ConnectionError:
            await ctx.reply("This command is not currently available.")
            return
        msg = Helpers.CommandStrip(self,ctx.message.content)
        if len(msg) > 1:
            if "fakemon" in msg.lower():
                model = "dreamshaper_8.safetensors [879db523c3]"
            elif "anime" in msg.lower():
                model = random.choice(self.animemodels)
            elif "real" in msg.lower():
                model = random.choice(self.realmodels)
            else:
                if random.randint(0,1) == 1:
                    model = random.choice(self.animemodels)
                else:
                    model = random.choice(self.realmodels)
            if len(msg.lower().split('!neg')) > 1:
                cneg = msg.lower().split('!neg')[1]
                msg = msg.lower().split('!neg')[0]
            else:
                cneg = ""
            if ctx.message.channel.is_nsfw():
                neg = "easynegative2, HDA_BadHands_neg, (Asian:1.3), (loli:1.3)"
                pos = "masterpiece, best quality"
            else:
                neg = "easynegative2, HDA_BadHands_neg, (Asian:1.3), (nsfw:1.5), (nude:1.3), (pussy:1.3), (nipples:1.3), (penis:1.3), (loli:1.3)"
                pos = "masterpiece, best quality, (sfw), softcore, <lora:NSFWFilter:-0.8>"
            payload = {
                "prompt": f"{pos}, {msg}",
                "negative_prompt": f"{neg},f{cneg}",
                "seed": -1,
                "steps": 25,
                "width": 512,
                "height": 512,
                "cfg_scale": 7,
                "sampler_name": "DPM++ 2M SDE Karras",
                "n_iter": 1,
                "batch_size": 1,
                "enable_hr": True,
                "denoising_strength" : 0.55,
                "hr_resize_x" : 0,
                "hr_resize_y" : 0,
                "hr_scale" : 2,
                "hr_second_pass_steps" : 15,
                "hr_upscaler" : "Latent",
                "override_settings": {
                    'sd_model_checkpoint' : model
                },
                "alwayson_scripts": {"ADetailer": {"args": [True, False, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.3, "ad_dilate_erode": 4, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 6, "ad_mask_k_largest": 5, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "face_yolov8s.pt", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.5, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.45, "ad_dilate_erode": 8, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 4, "ad_mask_k_largest": 0, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "hand_yolov8n.pt", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "close up of a hand, <lyco:GoodHands-beta2:1>, nice hands, ", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}, {"ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1, "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0, "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1, "ad_denoising_strength": 0.4, "ad_dilate_erode": 4, "ad_inpaint_height": 512, "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32, "ad_inpaint_width": 512, "ad_mask_blur": 4, "ad_mask_k_largest": 0, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0, "ad_model": "None", "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras", "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": []}]}}
            }

            response = self.generate_image(payload)
            image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
            image.save(f'./internal/data/images/sd{ctx.guild.id}.jpg')
        else:
            response = f'You didn\'t enter a message.'
        if not ctx.message.channel.is_nsfw():
            image_file = discord.File(f'./internal/data/images/sd{ctx.guild.id}.jpg', filename='SPOILER_sd.jpg')
            sent = await ctx.reply(file=image_file)
        else:
            image_file = discord.File(f'./internal/data/images/sd{ctx.guild.id}.jpg', filename='sd.jpg')
            sent = await ctx.reply(file=image_file)



def setup(client):
    client.add_cog(sd(client))