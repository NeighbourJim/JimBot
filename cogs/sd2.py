import discord
import logging
import io
import base64
import requests
import random
import asyncio
from PIL import Image
from discord.ext import commands
from discord.ext.commands import BucketType

from internal.logs import logger
from internal.helpers import Helpers
from internal.command_blacklist_manager import BLM


class sd2(commands.Cog):

    # Model checkpoint filenames
    MODEL_WILDCARD   = "wildcardxXLFusion_fusionOG.safetensors [22ebc61141]"
    MODEL_JUGGERNAUT = "juggernautXL_ragnarokBy.safetensors [dd08fa32f9]"
    MODEL_DREAMSHAPER = "dreamshaperXL_v21TurboDPMSDE.safetensors [4496b36d48]"
    MODEL_ANIME      = "ccatCitronAnimeTreasure_ilV9.safetensors [3761477265]"
    MODEL_CIRCUSMIX  = "circusmix_v70.safetensors [da1f675d63]"
    MODEL_FAKEMON    = "catCitronAnimeTreasure_ilV9.safetensors [3761477265]"

    def __init__(self, client):
        self.client = client
        self.server_url = "http://10.0.0.1:7860"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_image(self, payload):
        """POST a txt2img payload to the SD API. Returns parsed JSON or None."""
        try:
            response = requests.post(
                f'{self.server_url}/sdapi/v1/txt2img',
                json=payload,
                timeout=120,
            )
            return response.json()
        except Exception as ex:
            logger.LogPrint(f'SD API call failed - {ex}', logging.ERROR)
            return None

    async def _check_server(self, ctx) -> bool:
        """Return True if the SD server is reachable, else reply and return False."""
        try:
            requests.get(self.server_url, timeout=1.5)
            return True
        except Exception:
            await ctx.reply("This command is not currently available.")
            return False

    def _pixelate_sprite(self, path, width, height):
        """Downscale to pixel art and save back to the same path."""
        img = Image.open(path)
        img = img.resize((width // 8, height // 8), resample=Image.NEAREST)
        img = img.convert('P', palette=Image.ADAPTIVE, colors=64)
        img = img.resize((width, height), resample=Image.NEAREST)
        img.save(path)

    def _parse_user_neg(self, msg):
        """Split a prompt on '!neg', returning (prompt, custom_negative)."""
        parts = msg.split('!neg', 1)
        if len(parts) > 1:
            return parts[0].strip(), parts[1].strip()
        return msg, ""

    def _adetailer_face_args(self):
        """ADetailer config with face detection only (fakemonsprite, fakemon)."""
        face_slot = {
            "ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1,
            "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0,
            "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1,
            "ad_denoising_strength": 0.3, "ad_dilate_erode": 4, "ad_inpaint_height": 512,
            "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32,
            "ad_inpaint_width": 512, "ad_mask_blur": 6, "ad_mask_k_largest": 5,
            "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0,
            "ad_model": "face_yolov8s.pt", "ad_negative_prompt": "", "ad_noise_multiplier": 1,
            "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "Euler a", "ad_steps": 28,
            "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False,
            "ad_use_inpaint_width_height": False, "ad_use_noise_multiplier": False,
            "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False,
            "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": [],
        }
        disabled_slot = {
            "ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1,
            "ad_confidence": 0.3, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0,
            "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1,
            "ad_denoising_strength": 0.4, "ad_dilate_erode": 4, "ad_inpaint_height": 512,
            "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32,
            "ad_inpaint_width": 512, "ad_mask_blur": 4, "ad_mask_k_largest": 0,
            "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None", "ad_mask_min_ratio": 0,
            "ad_model": "None", "ad_negative_prompt": "", "ad_noise_multiplier": 1,
            "ad_prompt": "", "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras",
            "ad_steps": 28, "ad_use_cfg_scale": False, "ad_use_checkpoint": False,
            "ad_use_clip_skip": False, "ad_use_inpaint_width_height": False,
            "ad_use_noise_multiplier": False, "ad_use_sampler": False, "ad_use_steps": False,
            "ad_use_vae": False, "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0,
            "is_api": [],
        }
        return {"ADetailer": {"args": [True, False, face_slot, disabled_slot, disabled_slot]}}

    def _adetailer_full_args(self):
        """ADetailer config with face, pussy, and penis detectors (stablediffusion_xl)."""
        face_slot = {
            "ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1,
            "ad_confidence": 0.2, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0,
            "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1,
            "ad_denoising_strength": 0.25, "ad_dilate_erode": 4, "ad_inpaint_height": 1024,
            "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32,
            "ad_inpaint_width": 1024, "ad_mask_blur": 4, "ad_mask_filter_method": "Area",
            "ad_mask_k": 5, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None",
            "ad_mask_min_ratio": 0, "ad_model": "face_yolov8s.pt", "ad_model_classes": "",
            "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "",
            "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras",
            "ad_scheduler": "Use same scheduler", "ad_steps": 28, "ad_tab_enable": True,
            "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False,
            "ad_use_inpaint_width_height": True, "ad_use_noise_multiplier": False,
            "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False,
            "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": [],
        }
        pussy_slot = {
            "ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1,
            "ad_confidence": 0.48, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0,
            "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1,
            "ad_denoising_strength": 0.3, "ad_dilate_erode": 4, "ad_inpaint_height": 1024,
            "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32,
            "ad_inpaint_width": 1024, "ad_mask_blur": 4, "ad_mask_filter_method": "Area",
            "ad_mask_k": 0, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None",
            "ad_mask_min_ratio": 0.036, "ad_model": "pussyV2.pt", "ad_model_classes": "",
            "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "pussy, pussy juice, ",
            "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras",
            "ad_scheduler": "Use same scheduler", "ad_steps": 28, "ad_tab_enable": False,
            "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False,
            "ad_use_inpaint_width_height": True, "ad_use_noise_multiplier": False,
            "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False,
            "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": [],
        }
        penis_slot = {
            "ad_cfg_scale": 7, "ad_checkpoint": "Use same checkpoint", "ad_clip_skip": 1,
            "ad_confidence": 0.42, "ad_controlnet_guidance_end": 1, "ad_controlnet_guidance_start": 0,
            "ad_controlnet_model": "None", "ad_controlnet_module": "None", "ad_controlnet_weight": 1,
            "ad_denoising_strength": 0.4, "ad_dilate_erode": 4, "ad_inpaint_height": 1024,
            "ad_inpaint_only_masked": True, "ad_inpaint_only_masked_padding": 32,
            "ad_inpaint_width": 1024, "ad_mask_blur": 4, "ad_mask_filter_method": "Area",
            "ad_mask_k": 4, "ad_mask_max_ratio": 1, "ad_mask_merge_invert": "None",
            "ad_mask_min_ratio": 0.025, "ad_model": "penisV2.pt", "ad_model_classes": "",
            "ad_negative_prompt": "", "ad_noise_multiplier": 1, "ad_prompt": "penis, ",
            "ad_restore_face": False, "ad_sampler": "DPM++ 2M Karras",
            "ad_scheduler": "Use same scheduler", "ad_steps": 28, "ad_tab_enable": False,
            "ad_use_cfg_scale": False, "ad_use_checkpoint": False, "ad_use_clip_skip": False,
            "ad_use_inpaint_width_height": True, "ad_use_noise_multiplier": False,
            "ad_use_sampler": False, "ad_use_steps": False, "ad_use_vae": False,
            "ad_vae": "Use same VAE", "ad_x_offset": 0, "ad_y_offset": 0, "is_api": [],
        }
        return {"ADetailer": {"args": [True, False, face_slot, pussy_slot, penis_slot]}}

    async def cog_check(self, ctx):
        return BLM.CheckIfCommandAllowed(ctx)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    @commands.command(aliases=["fms"], help="Create a fake pokemon sprite")
    @commands.cooldown(rate=1, per=10, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def fakemonsprite(self, ctx):
        await ctx.trigger_typing()
        if not await self._check_server(ctx):
            return

        msg = Helpers.CommandStrip(self, ctx.message.content)
        msg = Helpers.DiscordEmoteConvert(self, msg)
        if len(msg) <= 1:
            await ctx.reply("You didn't enter a message.")
            return

        model = self.MODEL_DREAMSHAPER
        vae = "sdxl_vae.safetensors"
        sampler = "DPM++ SDE Karras"
        cfg = 2
        steps = 8
        neg = "((nsfw, naked, nude, sexy, underwear, partially clothed, erotic, nipples, breasts, penis, vagina, pussy, ass, sex))"

        if not ctx.message.channel.is_nsfw():
            neg += ",(nsfw,nude)"

        if "trainer" in msg.lower():
            pos = "__pktrainer__, full body, blank background"
        elif "frontback" in msg.lower() or "backfront" in msg.lower():
            pos = "__pkspritebf__, blank background"
            neg += ",((human))"
        else:
            pos = "__pksprite__, blank background"
            neg += ",((human))"

        pruned = msg.lower()
        for word in ("trainer", "frontback", "backfront", "artwork", "pokemon"):
            pruned = pruned.replace(word, "")
        pos = f"{pos},{pruned}"

        width = 1536 if "pkspritebf" in pos else 768
        height = 768

        payload = {
            "prompt": pos,
            "negative_prompt": neg,
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
                "sd_model_checkpoint": model,
                "sd_vae": vae,
            },
            "alwayson_scripts": self._adetailer_face_args(),
        }

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: self._generate_image(payload))
        if response is None:
            await ctx.reply("This command is not currently available.")
            return

        out_path = f'./internal/data/images/fakemon{ctx.author.id}.png'
        image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
        image.save(out_path)
        self._pixelate_sprite(out_path, width, height)

        await ctx.reply(file=discord.File(out_path, filename='SPOILER_fakemon.png'))

    @commands.command(aliases=["fm"], help="Create a fake pokemon")
    @commands.cooldown(rate=1, per=4, type=BucketType.channel)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def fakemon(self, ctx):
        await ctx.trigger_typing()
        if not await self._check_server(ctx):
            return

        msg = Helpers.CommandStrip(self, ctx.message.content)
        msg = Helpers.DiscordEmoteConvert(self, msg)
        if len(msg) < 1:
            await ctx.reply("You didn't enter a message.")
            return

        model = self.MODEL_FAKEMON
        sampler = "LCM Karras"
        cfg = 1.5
        steps = 12
        hr_scale = 1.35
        hr_second_pass_steps = 6
        hr_upscaler = "Latent"
        denoising_strength = 0.6

        if "trainer" in msg.lower():
            msg = msg.lower().replace("trainer", "").strip()
            neg = "low quality, worst quality, lazynsfw, detailed background"
            pos = "<lora:HerrscherAGGA2025_DMD2_Color-Recovery_V6:1>,masterpiece, best quality, absurdres, white background, blank background"
            lora = "<lora:Pokemon-Trainer-SpritesV2_Fp:1>, pixel art, simple background, full body,{|holding poke ball,}"
        else:
            neg = "low quality, worst quality, (((orb, sphere, round, ball))), ((multiple characters, group, crowd)), (((ball, round, circle))), no characters, landscape"
            pos = "<lora:HerrscherAGGA2025_DMD2_Color-Recovery_V6:1>,masterpiece, best quality, absurdres, ((black background, blank background))"
            lora = "<lora:Fakemon-_Sugimori:1> (Fakemon),Sugimori, pokemon \\(creature\\), no humans,animal, (solo))"

        if not ctx.message.channel.is_nsfw():
            pos += ", rating_safe, non-h"
            neg += ", (lazynsfw), (((nsfw, nude, pussy, penis, naked, nipples, breasts, rating_explicit, explicit))), (gore, guro, pussy, penis, sex, vaginal, anal, semen, cum, ecchi, sexual, panties), nsfw"

        msg, cneg = self._parse_user_neg(msg)

        payload = {
            "prompt": f"{pos}, {msg}, {lora}",
            "negative_prompt": f"{neg},{cneg}",
            "seed": -1,
            "steps": steps,
            "width": 1024,
            "height": 1024,
            "cfg_scale": cfg,
            "sampler_name": sampler,
            "n_iter": 1,
            "batch_size": 1,
            "enable_hr": False,
            "hr_upscaler": hr_upscaler,
            "hr_second_pass_steps": hr_second_pass_steps,
            "hr_scale": hr_scale,
            "denoising_strength": denoising_strength,
            "override_settings": {
                "sd_model_checkpoint": model,
                "sd_vae": "sdxl_vae.safetensors",
            },
            "alwayson_scripts": {
                "Kohya HRFix Integrated": {"args": [{"0": True, "1": 3, "2": 2, "3": 0, "4": 0.35, "5": True, "6": "bicubic", "7": "bicubic"}]},
                **self._adetailer_face_args(),
            },
        }

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: self._generate_image(payload))
        if response is None:
            await ctx.reply("This command is not currently available.")
            return

        out_path = f'./internal/data/images/fakemon{ctx.author.id}.png'
        image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
        image.save(out_path)
        await ctx.reply(file=discord.File(out_path, filename='SPOILER_fakemon.png'))

    @commands.command(aliases=["sdxl", "sd"], help="Create an image")
    @commands.cooldown(rate=1, per=30, type=BucketType.user)
    @commands.has_role("Bot Use")
    @commands.guild_only()
    async def stablediffusion_xl(self, ctx):
        await ctx.trigger_typing()
        if not await self._check_server(ctx):
            return

        msg = Helpers.CommandStrip(self, ctx.message.content)
        msg = Helpers.DiscordEmoteConvert(self, msg)
        if len(msg) <= 1:
            await ctx.reply("You didn't enter a message.")
            return

        xl_real_models = [self.MODEL_WILDCARD]
        xl_anime_realistic = [self.MODEL_CIRCUSMIX]

        vae = "sdxl_vae.safetensors"
        sprite = False
        posSuf = ""
        enable_hr = False
        hr_scale = 1.5
        hr_second_pass_steps = 5
        hr_upscaler = "Latent"
        denoising_strength = 0.6

        if "anime" in msg.lower() or "lora:pixel" in msg.lower():
            if "realistic" in msg.lower() and "lora:pixel" not in msg.lower():
                model = random.choice(xl_anime_realistic)
                msg = msg.replace("anime", "").replace("realistic", "")
                pos = "(realistic), (3d), (photograph), "
                neg = "lowres, worst quality, zoomed out, far away, bad quality, bad anatomy, bad hands, sketch, signature, watermark, logo, border,"
            else:
                model = self.MODEL_ANIME
                msg = msg.replace("anime", "")
                pos = "masterpiece, absurdres, newest, perfect quality, best quality, absolutely eye-catching,"
                neg = "(((realistic, 3d, 3d render))), lowres, worst quality, zoomed out, far away, bad quality, bad anatomy, bad hands, sketch, signature, watermark, logo, border,"

            posSuf = ", <lora:HerrscherAGGA2025_DMD2_Color-Recovery_V6:1>"
            sampler = "LCM Karras"
            cfg = 1
            steps = 12
            enable_hr = True
            hr_scale = 1.5
            hr_second_pass_steps = 6
            denoising_strength = 0.65

            if not ctx.message.channel.is_nsfw():
                pos += ", (general), "
                neg += "(explicit), ((lazynsfw)), (((nsfw, nude, pussy, penis, naked, nipples, breasts, rating_explicit, loli, shota, child)))"

        else:
            model = random.choice(xl_real_models)

            if "realistic" in msg.lower():
                model = self.MODEL_JUGGERNAUT
                msg = msg.lower().replace("realistic", "")

            if any(kw in msg.lower() for kw in ("pkspif", "pk_trainer", "__pksprite", "__pktrainer", "pkspbf")):
                model = self.MODEL_DREAMSHAPER
                sprite = True

            if model == self.MODEL_DREAMSHAPER:
                neg = "BeyondSDXLv3, (((nsfw, nude, nipples, breasts, loli, shota, child, porn, softcore, hardcore)))"
                pos = "best quality, high quality,"
                if sprite:
                    neg = ""
                    pos = ""
                sampler = "DPM++ SDE Karras"
                cfg = 2
                steps = 8
                if not ctx.message.channel.is_nsfw():
                    neg += "(nsfw,nude),"

            elif model == self.MODEL_WILDCARD:
                neg = "BeyondSDXLv3"
                pos = "<lora:HerrscherAGGA2025_DMD2_Color-Recovery_V6:1>,"
                sampler = "LCM Karras"
                cfg = 1
                steps = random.randint(10, 12)
                enable_hr = True
                hr_second_pass_steps = 6
                denoising_strength = 0.6
                if not ctx.message.channel.is_nsfw():
                    neg += "(nsfw, nude)"

            elif model == self.MODEL_JUGGERNAUT:
                cfg = 1.5
                steps = random.randint(10, 14)
                sampler = "LCM Karras"
                vae = "None"
                enable_hr = True
                hr_second_pass_steps = 6
                denoising_strength = 0.6
                pos = "<lora:HerrscherAGGA2025_DMD2_Color-Recovery_V6:1>,"
                neg = "bad eyes, blurry, missing limbs, bad anatomy, cartoon, nsfw, nude, penis, breasts, pussy, vagina"

        # Randomise resolution, then override for sprites
        width = random.choice([1024, 1024, 864, 1280])
        if width == 864:
            height = random.choice([1024, 1280])
        elif width == 1280:
            height = random.choice([1024, 864])
        else:
            height = 1024

        if sprite:
            height = 768
            width = 1536 if any(kw in msg.lower() for kw in ("pkspritebf", "pkspbf")) else 768

        msg, cneg = self._parse_user_neg(msg)

        if not ctx.message.channel.is_nsfw():
            neg += ", nsfw"

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
            "denoising_strength": denoising_strength,
            "override_settings": {
                "sd_model_checkpoint": model,
                "sd_vae": vae,
            },
            "alwayson_scripts": {
                "API payload": {"args": []},
                "Comments": {"args": []},
                "ControlNet": {"args": [
                    {"batch_image_dir": "", "batch_input_gallery": [], "batch_mask_dir": "", "batch_mask_gallery": [], "control_mode": "Balanced", "enabled": False, "generated_image": None, "guidance_end": 1, "guidance_start": 0, "hr_option": "Both", "image": None, "input_mode": "simple", "mask_image": None, "model": "None", "module": "None", "pixel_perfect": False, "processor_res": -1, "resize_mode": "Crop and Resize", "save_detected_map": True, "threshold_a": -1, "threshold_b": -1, "use_preview_as_input": False, "weight": 1},
                    {"batch_image_dir": "", "batch_input_gallery": [], "batch_mask_dir": "", "batch_mask_gallery": [], "control_mode": "Balanced", "enabled": False, "generated_image": None, "guidance_end": 1, "guidance_start": 0, "hr_option": "Both", "image": None, "input_mode": "simple", "mask_image": None, "model": "None", "module": "None", "pixel_perfect": False, "processor_res": -1, "resize_mode": "Crop and Resize", "save_detected_map": True, "threshold_a": -1, "threshold_b": -1, "use_preview_as_input": False, "weight": 1},
                    {"batch_image_dir": "", "batch_input_gallery": [], "batch_mask_dir": "", "batch_mask_gallery": [], "control_mode": "Balanced", "enabled": False, "generated_image": None, "guidance_end": 1, "guidance_start": 0, "hr_option": "Both", "image": None, "input_mode": "simple", "mask_image": None, "model": "None", "module": "None", "pixel_perfect": False, "processor_res": -1, "resize_mode": "Crop and Resize", "save_detected_map": True, "threshold_a": -1, "threshold_b": -1, "use_preview_as_input": False, "weight": 1},
                ]},
                "Dynamic Prompts v2.17.1": {"args": [True, False, 1, False, False, False, 1.1, 1.5, 100, 0.7, False, False, True, False, False, 0, "Gustavosta/MagicPrompt-Stable-Diffusion", ""]},
                "DynamicThresholding (CFG-Fix) Integrated": {"args": [False, 7, 1, "Constant", 0, "Constant", 0, 1, "enable", "MEAN", "AD", 1]},
                "Extra options": {"args": []},
                "FreeU Integrated": {"args": [False, 1.01, 1.02, 0.99, 0.95]},
                "HyperTile Integrated": {"args": [False, 256, 2, 0, False]},
                "Kohya HRFix Integrated": {"args": [True, 3, 2, 0, 0.35, True, "bicubic", "bicubic"]},
                "LatentModifier Integrated": {"args": [False, 0, "anisotropic", 0, "reinhard", 100, 0, "subtract", 0, 0, "gaussian", "add", 0, 100, 127, 0, "hard_clamp", 5, 0, "None", "None"]},
                "Model keyword": {"args": [True, "keyword prompt", "keyword1, keyword2", "None", "textual inversion first", "None", "0.7", "None"]},
                "MultiDiffusion Integrated": {"args": [False, "MultiDiffusion", 768, 768, 64, 4]},
                "NegPiP": {"args": [True]},
                "Never OOM Integrated": {"args": [False, False]},
                "ReActor": {"args": [None, False, "0", "0", "inswapper_128.onnx", "CodeFormer", 1, True, "None", 1, 1, False, True, 1, 0, 0, False, 0.5, True, False, "CUDA", False, 0, "None", "", None, False, False, 0.5, 0, "tab_single"]},
                "Refiner": {"args": [False, "", 0.8]},
                "Seed": {"args": [-1, False, -1, 0, 0, 0]},
                "SelfAttentionGuidance Integrated": {"args": [True, 0.5, 2]},
                "StyleAlign Integrated": {"args": [False]},
                **self._adetailer_full_args(),
            },
        }

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: self._generate_image(payload))
        if response is None:
            await ctx.reply("This command is not currently available.")
            return

        out_path = f'./internal/data/images/sd{ctx.author.id}.png'
        image = Image.open(io.BytesIO(base64.b64decode(response['images'][0])))
        image.save(out_path)

        if sprite:
            self._pixelate_sprite(out_path, width, height)

        filename = 'sd.png' if ctx.message.channel.is_nsfw() else 'SPOILER_sd.png'
        await ctx.reply(file=discord.File(out_path, filename=filename))


def setup(client):
    client.add_cog(sd2(client))
