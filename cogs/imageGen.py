""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 6.1.0
"""
#TODO: Incorporate Discord permissions/guilds API stuff for access control (eg dm permissions, roles, channels, etc)
          #partially complete, basic framework in place
#TODO: Incorporate User/server-credit system into commands similar to permissions
#TODO(ongoing): Build a comprehensive and flexible set of Comfi workflows that can be used and autoload them into bot commands
		#Autogenerate config.properties based on node numbers
#TODO(wishlist): workflow parser that auto-converts manager-stored workflows into API format and auto-populates config.properties
	#This needs a standard list of node tags for the command-generator
#TODO(nicetohave): Privacy feature: leave no trace setup where everything is ephemoral
#TODO: Automatically generate _config from config.properties file
#TODO: create an OS level system to monitor the bot and restart it if necessary, especially if it is killed


import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
import json
import configparser
import logging
import uuid
import websockets
import random
from io import BytesIO
from PIL import Image
from PIL import ImageSequence
import PIL
import sys
import os
from datetime import datetime
from math import ceil, sqrt
import tempfile
import bleach
from libs.Comfy_interface import get_model_list_long
from libs.Comfy_interface import get_lora_list_long
from libs.StandardView import StandardView
from libs.ImageChooser import ImageChooser

from libs.Comfy_interface import get_history, get_image, queue_prompt, upload_image
from libs.LiveRequestTracker import LiveRequestTracker
from libs.UserConfig import UserConfig

import yaml
with open("textTemplates/en.yaml", 'r') as stream:
    text = yaml.safe_load(stream)

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)

requests = LiveRequestTracker()
# Here we name the cog and create a new class for the cog.
class Imagine(commands.Cog, name="imagine"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config = configparser.ConfigParser()
        self.config.read('config.properties')
        
        logger.info(f"config: {self.config}")
        logger.info({section: dict(self.config[section]) for section in self.config.sections()})
    
    
    #check if channel allowed or is DM
    def channel_check(ctx):
        if ctx.bot.channel_check(ctx):
            return True
        return False
    
    
    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.
    
    @commands.hybrid_command(
        name="imaginehelp",
        description="This command displays the help text, along with a list of available models and Loras",
    )
    @commands.check(channel_check)
    async def helpcommand(self, context: Context):
        model_list = ""
        #add models with get_model_list here
        for model in get_model_list_long():
            model_list += f"- {model}\n"
        lora_list = ""
        #add loras with get_lora_list here
        for lora in get_lora_list_long():
            lora_list += f"- {lora}\n"
        #help command goes here
        message = f"""**StableDiffusion Bot Help**
**Command:** `/imagine`
Generate images with:
- `/imagine prompt="Your text here"`

**Optional:**
- `negative_prompt`: Avoid certain themes.
  - Ex: `negative_prompt="rain"`
  
  (Config Settings like model and lora are saved between commands)
- `model`: Choose a model (list below).
  - Ex: `model="dreamshaper_8"`
- `lora`: Low-Rank Adaptation, this modifies the model (list below).
  - Ex: `lora="CyberpunkSDXL"`
- `size`: Output size.
  - Ex: `size="1024"`
- `seed`: For consistent outputs.
  - Ex: `seed=12345`
- `spoiler`: Wrap output in a spoiler tag.
  - Ex: `spoiler=spoiler`
  

**Config saving and loading:**
- `/defaultconfig`: Load the default config.
- `/saveconfig slot="Slot name"`: Save your current config to a slot.
    - Ex: `/saveconfig slot="My config"`
- `/loadconfig slot="Slot name"`: Load a saved config from a slot.
    - Ex: `/loadconfig slot="My config"`
- `/listconfigs`: List your saved configs.
- `/deleteconfig slot="Slot name"`: Delete a saved config.
    - Ex: `/deleteconfig slot="My config"`


**Models:** *(Dynamic list)*
{model_list}
**LORAs:** *(Dynamic list)*
{lora_list}"""
        
        
        #split the message into chunks of 2000 characters, preserving whole lines
        message_chunks = []
        while len(message) > 0:
            message_chunks.append(message[:2000])
            message = message[2000:]
        #send the message chunks
        for message in message_chunks:
            await context.send(message)
    
    #reaction handler
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        #get the message
        logger.debug("on_reaction_add")
        logger.debug(reaction.message)
    
    @commands.hybrid_command(
        name="sd",
        description="Generate an image with a dialog box",
    )
    @commands.check(channel_check)
    async def sdcommand(self, context: Context) -> None:
        #show the image generation modal to the user
        
        modal = ImageChooser(context)
        await context.interaction.response.send_modal(modal)
        
    @commands.hybrid_command(
        name="saveconfig",
        description="Save your current config",
    )
    @app_commands.describe(slot="Slot to save your config to")
    @commands.check(channel_check)
    async def saveconfigcommand(self, context: Context, slot: str) -> None:
        conf = UserConfig(self.bot,context.author.id)
        try:
            await conf.loadconfig()
            await conf.saveToSlot(slot)
            await context.send(f"Saved config to slot: {slot}\n{conf}\nUse /listconfigs to see saved configs.", ephemeral=True)
        except Exception as e:
            await context.send(f"Something went wrong: {e}", ephemeral=True)
        
    @commands.hybrid_command(
        name="loadconfig",
        description="Load a saved config",
    )
    @app_commands.describe(slot="Slot to load your config from")
    @commands.check(channel_check)
    async def loadconfigcommand(self, context: Context, slot: str) -> None:
        conf = UserConfig(self.bot,context.author.id)
        try:
            await conf.loadFromSlot(slot)
            await context.send(f"Loaded config from slot: {slot}\n{conf}", ephemeral=True)
        except Exception as e:
            await context.send(f"Something went wrong: {e}.\n Use /listconfigs to see saved configs.", ephemeral=True)
        
    @commands.hybrid_command(
        name="defaultconfig",
        description="Load the default config",
    )
    @commands.check(channel_check)
    async def defaultconfigcommand(self, context: Context) -> None:
        try:
            conf = UserConfig(self.bot,context.author.id)
            await conf.default()
            #tell the user that we're loading the default config
            await context.send(f"Default config loaded, last config saved to \"last\" slot. Use /listconfigs to see saved configs.", ephemeral=True)
        except Exception as e:
            #tell the user that something went wrong
            await context.send(f"Something went wrong: {e}", ephemeral=True)
    @commands.hybrid_command(
        name="listconfigs",
        description="List your saved configs",
    )
    @commands.check(channel_check)
    async def listconfigscommand(self, context: Context) -> None:
        try:
            conf = UserConfig(self.bot,context.author.id)
            message = await conf.listSlots()
            await context.send(f"Saved configs:\nUse /loadconfig to load or /saveconfig to save.\nUse /defaultconfig to reset to default(your current config will be saved.)\n" + message, ephemeral=True)
        except Exception as e:
            #tell the user that something went wrong
            await context.send(f"Something went wrong: {e}", ephemeral=True)
        
    #delete config command
    @commands.hybrid_command(
        name="deleteconfig",
        description="Delete a saved config",
    )
    @app_commands.describe(slot="Slot to delete your config from")
    @commands.check(channel_check)
    async def deleteconfigcommand(self, context: Context, slot: str) -> None:
        #sanitize the name input
        slot = bleach.clean(slot)
        #delete the config (slot) from the database
        try:
            await self.bot.database.delete_config(context.author.id, slot)
            #tell the user that we deleted the config
            await context.send(f"Deleted config from slot: {slot}", ephemeral=True)
        except Exception as e:
            #tell the user that something went wrong
            await context.send(f"Something went wrong: {e}", ephemeral=True)
        
    @commands.hybrid_command(
        name="upload",
        description="Process an uploaded image",
    )
    @commands.check(channel_check)
    @app_commands.describe(prompt='Prompt to use for image processing')
    @app_commands.describe(negative_prompt='Negative prompt to use for image processing')
    async def uploadcommand(self, context: Context, image: discord.Attachment, prompt:str="", negative_prompt:str="") -> None:
        #convert the image to a PIL image
        imagefile = Image.open(BytesIO(await image.read()))
        #load the user's config from the database
        conf = UserConfig(self.bot,context.author.id)
        await conf.loadconfig()
        #set the config values to the inputs
        await conf.set('prompt',prompt)
        await conf.set('negative_prompt',negative_prompt)
        
        view=StandardView(self, context, conf.get('prompt'), conf.get('negative_prompt'), [imagefile], conf.get('model'), conf.get('lora'),512,random.randint(0,999999999999999),app_commands.Choice(name='no spoiler', value=''),requests)
        await context.send(file = discord.File(fp=self.save_file(imagefile), filename=f"collage.png"), view=view)
        
    #imagineanimation command, this is the animation generation command
    @commands.hybrid_command(
        name="imagineanimation",
        description="Generate an animation",
    )
    @app_commands.describe(prompt='Prompt for the animation being generated')
    @app_commands.describe(negative_prompt='Prompt for what you want to steer the AI away from')
    @app_commands.describe(model='Model to use for generation')
    @app_commands.describe(lora='Lora to use for generation')
    @app_commands.describe(framecount='number of frames to generate')
    @commands.check(channel_check)
    async def imagineanimationcommand(self, context: Context, prompt: str, negative_prompt: str=None, model: str=None, lora: str=None, framecount: str="25") -> None:
        #get the user's config from the database
        config = await self.bot.database.get_config(context.author.id)
        #sanitize the inputs
        prompt = bleach.clean(prompt)
        if negative_prompt != None:
            negative_prompt = bleach.clean(negative_prompt)
        if model != None:
            model = bleach.clean(model)
            config['model'] = model
        if lora != None:
            lora = bleach.clean(lora)
            config['lora'] = lora
        framecount = bleach.clean(framecount)
        #store the config back to the database
        await self.bot.database.store_config(context.author.id, config)
        
        #store the config back to the database
        await self.bot.database.store_config(context.author.id, config)
        #tell the user that we are generating the animation
        
        await context.send(f"{context.author} asked me to imagine an animation of {prompt}{' with negative prompt: ' + negative_prompt if negative_prompt else ''} and {framecount} frames. There are {requests.get()} requests in progress")
        #generate the animation
        gif = await self.generate_animation(config_name="LOCAL_TEXT2ANIMATION",prompt=prompt,negative_prompt=negative_prompt, framecount=framecount)
        #send the animation(no buttons)
        await context.send(file = discord.File(fp=self.create_gif(gif), filename=f"animation.gif"))
        return
    
    #imagine command, this is the main image generation command
    @commands.hybrid_command(
        name="imagine",
        description="Generate an image",
    )
    @app_commands.describe(prompt='Prompt for the image being generated')
    @app_commands.describe(negative_prompt='Prompt for what you want to steer the AI away from')
    @app_commands.describe(model='Model to use for generation')
    @app_commands.describe(lora='Lora to use for generation')
    @app_commands.describe(size='Size of the image to generate')
    @app_commands.describe(seed='Seed for the random number generator')
    @app_commands.choices(spoiler=[
        app_commands.Choice(name='no spoiler', value=''),
        app_commands.Choice(name='spoiler', value='SPOILER_'),
                                   ])
    @commands.check(channel_check)
    async def imaginecommand(self, context: Context, prompt: str, negative_prompt: str=None, model: str=None, lora: str=None,seed: str=None, size: str=None,spoiler: app_commands.Choice[str]=None) -> None:
        """
        This command runs the stableDiffusion program and displays an image.

        :param context: The application command context.
        """
        #try to load the user's previous config
        config = await self.bot.database.get_config(context.author.id)
        
        #sanitize all the inputs using bleach
        logger.info("config loaded:" + str(config))
        prompt = bleach.clean(prompt)
        if negative_prompt != None:
            negative_prompt = bleach.clean(negative_prompt)
        if spoiler == None:
            spoiler = app_commands.Choice(name='no spoiler', value='')
        self.spolier = spoiler
        
        #handle config using new config system
        #load the user's config from the database
        conf = UserConfig(self.bot,context.author.id)
        await conf.loadconfig()
        #set the config values to the inputs
        await conf.set('model',model)
        await conf.set('lora',lora)
        
        #check to see if the user has a seed set, if not, generate one but dont set it to the config
        if seed == None:
            userSeed = conf.get('seed')
            if userSeed == "":
                seed = random.randint(0,999999999999999)
            else:
                seed = userSeed
        else:
            seed = bleach.clean(seed)
            await conf.set('seed',seed)
            
        
        #default size to 512
        if size == None:
            size = "1024"
        await conf.set('size',size)
        thisview = discord.ui.View(timeout=None)
        
        message = f"{context.author} asked me to imagine {prompt}{' with negative prompt: ' + negative_prompt if negative_prompt else ''} using size: {conf.get('size')}{', seed: ' + str(seed) if seed else ''}. Generating this image will burn about 1/2 a gram of coal. "
        if(conf.get('model') != ""):
            message += f" using model: {conf.get('model')}"
        if(conf.get('lora') != ""):
            message += f" using lora: {conf.get('lora')}"
        
        sent = await context.send(message + f" There are {requests.get()} requests in progress", view=thisview)
        
        try:
            if(int(size) > 4000):
                throw("Size too large")
            images=None
            if(conf.get('model') != "" and conf.get('lora') != ""):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGMODELLORA",conf.get('model'),conf.get('lora'),conf.get('size'),seed)
            elif(conf.get('model') != ""):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGMODEL",conf.get('model'),conf.get('lora'),conf.get('size'),seed)
            elif(conf.get('lora') != ""):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGLORA",conf.get('model'),conf.get('lora'),conf.get('size'),seed)
            else:
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMG",conf.get('model'),conf.get('lora'),conf.get('size'),seed)
            
            view=StandardView(self, context, prompt, negative_prompt, images, conf.get('model'),conf.get('lora'),conf.get('size'),seed,spoiler,requests)
            #delete the message that we sent earlier
            await context.send(content=message + f" There are {requests.get()} requests in progress",file = discord.File(fp=self.create_collage(images), filename=f"{spoiler.value}collage.png"), view=view)
            #TODO: Change this to an edit instead of a delete and send
        except Exception as e:
            #tell the user that something went wrong
            await context.send(f"Something went wrong: {e}")

        
    # Scan the directory for model files and extract model names
    def get_choices_from_directory(directory):
        model_files = [f for f in os.listdir(directory) if f.endswith('.safetensors')]  # Limit to first 25
        model_names = [os.path.splitext(f)[0] for f in model_files]
        return [app_commands.Choice(name=model_name, value=i) for i, model_name in enumerate(model_names)]
        
    # Dynamically get model choices from the specified directories
    directory = os.path.dirname(os.path.realpath(__file__))
    directory = os.path.dirname(os.path.dirname(directory))
    model_choices = get_choices_from_directory("/mnt/nvme0n1p2/ComfyUI/models/checkpoints")
    remove_models = ["dreamshaper_7","v1-5-pruned-emaonly","chilloutmix_NiPrunedFp32Fix","768-v-ema","colossusProjectXLSFW_v202BakedVAE","anything-v3-fp16-pruned","epicrealism_naturalSinRC1VAE"]
    #remove the models in remove_models from the list of model_choices
    for model in remove_models:
        for choice in model_choices:
            if choice.name == model:
                model_choices.remove(choice)
    #sort the model_choices
    model_choices.sort(key=lambda x: x.name)
    #trim the model_choices to 25
    model_choices = model_choices[:25]
    
    lora_choices = get_choices_from_directory("/mnt/nvme0n1p2/ComfyUI/models/loras") 
    #sort the lora_choices alphabetically
    lora_choices.sort(key=lambda x: x.name)
    
    
    
    @commands.hybrid_command(
        name="img",
        description="Generate an image, dropdown mode",
    )
    @app_commands.describe(prompt='Prompt for the image being generated')
    @app_commands.describe(negative_prompt='Prompt for what you want to steer the AI away from')
    @app_commands.choices(model=model_choices)
    @app_commands.choices(lora=lora_choices)
    @app_commands.describe(size='Size of the image to generate')
    @app_commands.describe(seed='Seed for the random number generator')
    @app_commands.choices(spoiler=[
        app_commands.Choice(name='no spoiler', value=''),
        app_commands.Choice(name='spoiler', value='SPOILER_'),
                                   ])
    @commands.check(channel_check)
    async def imgcommand(self, context: Context, prompt: str, negative_prompt: str=None, model: app_commands.Choice[int]=None, lora: app_commands.Choice[int]=None,seed: str=None, size: str=None,spoiler: app_commands.Choice[str]=None) -> None:
        context.defer()
        """
        This command runs the stableDiffusion program and displays an image.

        :param context: The application command context.
        """
        logger.info("imgcommand")
        #try to load the user's previous config
        config = await self.bot.database.get_config(context.author.id)
        
        #sanitize all the inputs using bleach
        logger.info("config loaded:" + str(config))
        prompt = bleach.clean(prompt)
        if negative_prompt != None:
            negative_prompt = bleach.clean(negative_prompt)
        if spoiler == None:
            spoiler = app_commands.Choice(name='no spoiler', value='')
        self.spolier = spoiler
        
        #handle config using new config system
        #load the user's config from the database
        conf = UserConfig(self.bot,context.author.id)
        await conf.loadconfig()
        #set the config values to the inputs
        if model != None:
            await conf.set('model',model.name)
        if lora != None:
            await conf.set('lora',lora.name)
        
        #check to see if the user has a seed set, if not, generate one but dont set it to the config
        if seed == None:
            userSeed = conf.get('seed')
            if userSeed == "":
                seed = random.randint(0,999999999999999)
            else:
                seed = userSeed
        else:
            seed = bleach.clean(seed)
            await conf.set('seed',seed)
            
        
        #default size to 1024
        if size == None:
            size = "512"
        await conf.set('size',size)
        thisview = discord.ui.View(timeout=None)
        
        message = f"{context.author} asked me to imagine {prompt}{' with negative prompt: ' + negative_prompt if negative_prompt else ''} using size: {conf.get('size')}{', seed: ' + str(seed) if seed else ''}."
        if(conf.get('model') != ""):
            message += f" using model: {conf.get('model')}"
        if(conf.get('lora') != ""):
            message += f" using lora: {conf.get('lora')}"
        
        sent = await context.send(message + f" There are {requests.get()} requests in progress", view=thisview)
        
        try:
            if(int(size) > 4000):
                throw("Size too large")
            images=None
            if(conf.get('model') != "" and conf.get('lora') != ""):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGMODELLORA",conf.get('model'),conf.get('lora'),conf.get('size'),seed)
            elif(conf.get('model') != ""):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGMODEL",conf.get('model'),conf.get('lora'),conf.get('size'),seed)
            elif(conf.get('lora') != ""):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGLORA",conf.get('model'),conf.get('lora'),conf.get('size'),seed)
            else:
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMG",conf.get('model'),conf.get('lora'),conf.get('size'),seed)
            
            view=StandardView(self, context, prompt, negative_prompt, images, conf.get('model'),conf.get('lora'),conf.get('size'),seed,spoiler,requests)
            #delete the message that we sent earlier
            await context.send(content=message + f" There are {requests.get()} requests in progress",file = discord.File(fp=self.create_collage(images), filename=f"{spoiler.value}collage.png"), view=view)
            #TODO: Change this to an edit instead of a delete and send
        except Exception as e:
            #tell the user that something went wrong
            await context.send(f"Something went wrong: {e}")
    
    
    async def generate_images(self, prompt: str,negative_prompt: str, config_name: str, model: str=None, lora: str=None, size: str="512", seed: int=random.randint(0,999999999999999)):
        with open(self.config[config_name]['CONFIG'], 'r') as file:
            workflow = json.load(file)
        serverContext = ServerContext(self.config)
        
        generator = ImageGenerator(self.config,serverContext)
        await generator.connect()

        prompt_nodes = self.config.get(config_name, 'PROMPT_NODES').split(',')
        neg_prompt_nodes = self.config.get(config_name, 'NEG_PROMPT_NODES').split(',')
        rand_seed_nodes = self.config.get(config_name, 'RAND_SEED_NODES').split(',')
        
        model_nodes = [' ']
        lora_nodes = [' ']
        size_nodes = [' ']
        try:
            model_nodes = self.config.get(config_name, 'MODEL_NODES').split(',')
        except:
            pass
        try:
            lora_nodes = self.config.get(config_name, 'LORA_NODES').split(',')
        except:
            pass
        try:
            size_nodes = self.config.get(config_name, 'SIZE_NODES').split(',')
        except:
            pass
        
        #print(workflow)
        # Modify the prompt dictionary
        if(prompt != None and prompt_nodes[0] != ''):
            for node in prompt_nodes:
                workflow[node]["inputs"]["text"] = prompt
        if(negative_prompt != None and neg_prompt_nodes[0] != ''):
            for node in neg_prompt_nodes:
                workflow[node]["inputs"]["text"] = negative_prompt
        if(rand_seed_nodes[0] != ''):
            for node in rand_seed_nodes:
                workflow[node]["inputs"]["seed"] = seed
        if(model_nodes[0] != ' '):
            for node in model_nodes:
                workflow[node]["inputs"]["ckpt_name"] = model + ".safetensors"
        if(lora_nodes[0] != ' '):
            for node in lora_nodes:
                workflow[node]["inputs"]["lora_name"] = lora + ".safetensors"
        if(size_nodes[0] != ' '):
            for node in size_nodes:
                workflow[node]["inputs"]["width"] = size
                workflow[node]["inputs"]["height"] = size
        
        images = await generator.get_images(workflow)
        await generator.close()

        return images
    
    async def generate_animation(self,config_name: str, prompt: str,negative_prompt: str, model: str=None, lora: str=None, size: str="512", seed: int=random.randint(0,999999999999999), framecount: str="25"):
        with open(self.config[config_name]['CONFIG'], 'r') as file:
            workflow = json.load(file)
        serverContext = ServerContext(self.config)
        
        generator = ImageGenerator(self.config,serverContext)
        await generator.connect()
        
        prompt_nodes = self.config.get(config_name, 'PROMPT_NODES').split(',')
        neg_prompt_nodes = self.config.get(config_name, 'NEG_PROMPT_NODES').split(',')
        rand_seed_nodes = self.config.get(config_name, 'RAND_SEED_NODES').split(',')
        framecount_nodes = self.config.get(config_name, 'FRAMECOUNT_NODES').split(',')
        #model_nodes = self.config.get(config_name, 'MODEL_NODES').split(',')
        #lora_nodes = self.config.get(config_name, 'LORA_NODES').split(',')
        
        if(prompt != None and prompt_nodes[0] != ''):
            for node in prompt_nodes:
                workflow[node]["inputs"]["text"] = prompt
        if(negative_prompt != None and neg_prompt_nodes[0] != ''):
            for node in neg_prompt_nodes:
                workflow[node]["inputs"]["text"] = negative_prompt
        if(rand_seed_nodes[0] != ''):
            for node in rand_seed_nodes:
                workflow[node]["inputs"]["seed"] = seed
        if(framecount_nodes[0] != ''):
            for node in framecount_nodes:
                workflow[node]["inputs"]["video_frames"] = framecount
        #if(model_nodes[0] != ' '):
        #    for node in model_nodes:
        #        workflow[node]["inputs"]["ckpt_name"] = model + ".safetensors"
        #if(lora_nodes[0] != ' '):
        #    for node in lora_nodes:
        #        workflow[node]["inputs"]["lora_name"] = lora + ".safetensors"
        
        logger.info("ImageGenerator.generate_animation workflow:" + str(workflow))
        images = await generator.get_images(workflow)
        await generator.close()

        return images
        
    
    async def generate_variations(self, image: Image.Image, prompt: str,negative_prompt: str, config_name: str, model: str=None, lora: str=None, size: str=None, seed: int=random.randint(0,999999999999999)):
        #if the image is over 512 pixels, downscale it
        if(image.width > 512 and config_name != "LOCAL_UPSCALE"):
            image = image.resize((512, 512), PIL.Image.LANCZOS)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            image.save(temp_file, format="PNG")
            temp_filepath = temp_file.name
        
        serverContext = ServerContext(self.config)
        
        response_data = upload_image(temp_filepath,serverContext.server_address)
        filename = response_data['name']
        
        with open(self.config[config_name]['CONFIG'], 'r') as file:
            workflow = json.load(file)
        
        generator = ImageGenerator(self.config,serverContext)
        await generator.connect()

        prompt_nodes = self.config.get(config_name, 'PROMPT_NODES').split(',')
        neg_prompt_nodes = self.config.get(config_name, 'NEG_PROMPT_NODES').split(',')
        rand_seed_nodes = self.config.get(config_name, 'RAND_SEED_NODES').split(',')
        file_input_nodes = self.config.get(config_name, 'FILE_INPUT_NODES').split(',')
        model_nodes = [' ']
        lora_nodes = [' ']
        try:
            model_nodes = self.config.get(config_name, 'MODEL_NODES').split(',')
            logger.info("ImageGenerator.generate_variations model_nodes:" + str(model_nodes))
        except:
            pass
        try:
            lora_nodes = self.config.get(config_name, 'LORA_NODES').split(',')
            logger.info("ImageGenerator.generate_variations lora_nodes:" + str(lora_nodes))
        except:
            pass
        
        if(prompt != None and prompt_nodes[0] != ''):
            for node in prompt_nodes:
                workflow[node]["inputs"]["text"] = prompt
        if(negative_prompt != None and neg_prompt_nodes[0] != ''):
            for node in neg_prompt_nodes:
                workflow[node]["inputs"]["text"] = negative_prompt
        if(rand_seed_nodes[0] != ''):
            for node in rand_seed_nodes:
                workflow[node]["inputs"]["seed"] = seed
        if(model_nodes[0] != ' '):
            for node in model_nodes:
                workflow[node]["inputs"]["ckpt_name"] = model + ".safetensors"
        if(lora_nodes[0] != ' '):
            for node in lora_nodes:
                workflow[node]["inputs"]["lora_name"] = lora + ".safetensors"
        if(file_input_nodes[0] != ''):
            for node in file_input_nodes:
                logger.info("ImageGenerator.generate_variations filename:" + filename)
                workflow[node]["inputs"]["image"] = filename
                
        logger.info("ImageGenerator.generate_images workflow:" + str(workflow))
        images = await generator.get_images(workflow)
        await generator.close()
        
        return images
    
    
    def create_collage(self,images):
        num_images = len(images)
        num_cols = ceil(sqrt(num_images))
        num_rows = ceil(num_images / num_cols)
        collage_width = max(image.width for image in images) * num_cols
        collage_height = max(image.height for image in images) * num_rows
        collage = Image.new('RGB', (collage_width, collage_height))

        for idx, image in enumerate(images):
            row = idx // num_cols
            col = idx % num_cols
            x_offset = col * image.width
            y_offset = row * image.height
            collage.paste(image, (x_offset, y_offset))

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        collage_path = f"./out/images_{timestamp}.png"
        collage.save(collage_path)

        return collage_path
    
    def save_file(self, image):
        image_width = image.width
        image_height = image.height
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = f"./out/images_{timestamp}.png"
        output = Image.new('RGB', (image_width, image_height), (255, 255, 255))
        output.paste(image, (0, 0))
        output.save(file_path)
        return file_path
    
    def create_gif(self,gif_images):
        gif_image = gif_images[0]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"./out/images_{timestamp}.gif"
        
        #ChatGPT wrote this
        if getattr(gif_image, "is_animated", False):
            frames = [frame.copy() for frame in ImageSequence.Iterator(gif_image)]
            frames[0].save(filename, save_all=True, append_images=frames[1:], loop=0, duration=gif_image.info['duration'])
        else:
            gif_image.save(filename, 'GIF')
        return filename

#get the server address from the config file, round robin sequentially the addresses


#ServerContext class, provides a server context for processes that need a server.
#Since each server stores temp files as part of some processes it is necessary to use the same server through that process
currentServer = 0
class ServerContext:
    def __init__(self, config):
        self.config = config
        self.server_address = self.get_server_address()
    
    #get a server address in a thread safe way
    def get_server_address(self):
        server_addresses = self.config['LOCAL']['SERVER_ADDRESS'].split(',')
        global currentServer
        server_address = server_addresses[currentServer]
        currentServer = (currentServer + 1) % len(server_addresses)
        return server_address
    


class ImageGenerator:
    def __init__(self, config, serverContext):
        self.config = config
        self.client_id = str(uuid.uuid4())
        self.serverContext = serverContext
        self.uri = f"ws://{self.serverContext.server_address}/ws?clientId={self.client_id}"
        self.ws = None
        
    async def connect(self):
        self.ws = await websockets.connect(self.uri)

    async def get_images(self, prompt):
        requests.increment()
        if not self.ws:
            await self.connect()
    
        prompt_id = queue_prompt(prompt, self.client_id,self.serverContext.server_address)['prompt_id']
        currently_Executing_Prompt = None
        output_images = []
        async for out in self.ws:
            try:
                message = json.loads(out)
                logger.info(str(message))
                if message['type'] == 'execution_start':
                    currently_Executing_Prompt = message['data']['prompt_id']
                if message['type'] == 'executing' and prompt_id == currently_Executing_Prompt:
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break
            except ValueError as e:
                #print("Incompatible response from ComfyUI");
                #logger.error("Incompatible response from ComfyUI")
                try:
                    message=json.loads(out)
                    logger.info(str(message))
                except:
                    pass
                
        history = get_history(prompt_id,self.serverContext.server_address)[prompt_id]
        #print("ImageGenerator.get_images history: " + str(history))
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image['subfolder'], image['type'],self.serverContext.server_address)
                    if 'final_output' in image['filename']:
                        pil_image = Image.open(BytesIO(image_data))
                        
                        logger.info("ImageGenerator.get_images image data size:" + str(sys.getsizeof(pil_image)))
                        output_images.append(pil_image)

            if 'gifs' in node_output:
                for gif in node_output['gifs']:
                    gif_data = get_image(gif['filename'], gif['subfolder'], gif['type'], self.serverContext.server_address)
                    if 'final_output' in gif['filename']:
                        pil_gif = Image.open(BytesIO(gif_data))
                        
                        logger.info("ImageGenerator.get_images image data size:" + str(sys.getsizeof(pil_gif)))
                        output_images.append(pil_gif)

        requests.decrement()
        return output_images

    async def close(self):
        if self.ws:
            await self.ws.close()


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(Imagine(bot))
