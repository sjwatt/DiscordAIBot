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
from discord import ui
import os
import json
import configparser
import logging
import uuid
import websockets
import random
import urllib.request
import urllib.parse
from io import BytesIO
from PIL import Image
from PIL import GifImagePlugin
from PIL import ImageSequence
import PIL
import sys
from datetime import datetime
from math import ceil, sqrt
import tempfile
import requests
import asyncio
import bleach

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)
liveRequestCount = 0


def get_model_list(startpos=0):
        #get the list of models from the folder "/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/checkpoints"
        #each model is a file in that folder that ends with ".safetensors". strip the extension off the file name and list the files
        #get the list of files in the folder
        model_list = []
        for filename in os.listdir("/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/checkpoints"):
            if filename.endswith(".safetensors"):
                model_list.append(filename[:-12])
        #limit the list to 25 items starting at startpos
        model_list = model_list[startpos:]
        model_list = model_list[:25]
        return model_list
    
def get_lora_list():
        lora_list = []
        for filename in os.listdir("/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/loras"):
            if filename.endswith(".safetensors"):
                lora_list.append(filename[:-12])
        return lora_list
    
#ImageChooser class(based on modal)
class ImageChooser(discord.ui.Modal):
    def __init__(self, context: Context,title="Modal"):
        super().__init__(timeout=None, title=title)
        self.context = context
        self.title = title
        self.prompt = ui.TextInput(label='Prompt')
        self.add_item(self.prompt)
        self.negative_prompt = ui.TextInput(label='Negative Prompt')
        self.add_item(self.negative_prompt)
        self.size = ui.TextInput(label='Size')
        self.add_item(self.size)
        self.seed = ui.TextInput(label='Seed')
        self.add_item(self.seed)
        
    async def send_modal(self, interaction: discord.Interaction):
        interaction.response._responded = True
        super().send_modal(interaction)
        
    async def on_submit(self, interaction: discord.Interaction):
        #ask the user to choose a model
        model_list = get_model_list(25)
        lora_list = get_lora_list()
        #create a select menu for the models
        model_select = ui.Select(placeholder="Choose a model",options=[discord.SelectOption(label=model,value=model) for model in model_list])
        #create a select menu for the loras
        lora_select = ui.Select(placeholder="Choose a lora",options=[discord.SelectOption(label=lora,value=lora) for lora in lora_list])
        #ask the user to choose a model and loras
        data = await interaction.response.send_message("Choose a model and lora", view=discord.ui.View(timeout=None).add_item(model_select).add_item(lora_select))
        


#Buttons class(based on view)
class Buttons(discord.ui.View):
    def __init__(self, parent, context: Context, prompt, negative_prompt, images, model, lora,size,seed,spoiler, *, timeout=180):
        super().__init__(timeout=timeout)
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.images = images
        self.model = model
        self.lora = lora
        self.context = context
        self.parent = parent
        self.timeout = timeout
        self.size = size
        self.seed = seed
        self.spoiler = spoiler
    
    
    
    #re-roll button
    @discord.ui.button(label='Re-roll', style=discord.ButtonStyle.green, emoji="🎲", row=0)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        #check that the user that pressed the button is the same as the user that sent the message
        if(self.context.author != interaction.user):
            return
        global liveRequestCount
        message = f"{self.context.author} asked me to imagine {self.prompt}{' with negative prompt: ' + self.negative_prompt if self.negative_prompt else ''} using size: {self.size}" + f" There are {liveRequestCount} requests in progress"
        if(self.model != None):
            message += f" using model: {self.model}"
        if(self.lora != None):
            message += f" using lora: {self.lora}"
        await self.context.send(message)

        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        #update the button
        
        button.disabled = False
        
        #re-randomize the seed
        self.seed = random.randint(0,999999999999999)
        
        try:
            images=None
            if(self.model != None and self.lora != None):
                images = await self.parent.generate_images(self.prompt,self.negative_prompt,"LOCAL_TEXT2IMGMODELLORA",self.model,self.lora,self.size,self.seed)
            elif(self.model != None):
                images = await self.parent.generate_images(self.prompt,self.negative_prompt,"LOCAL_TEXT2IMGMODEL",self.model,None,self.size,self.seed)
            elif(self.lora != None):
                images = await self.parent.generate_images(self.prompt,self.negative_prompt,"LOCAL_TEXT2IMGLORA",None,self.lora,self.size,self.seed)
            else:
                images = await self.parent.generate_images(self.prompt,self.negative_prompt,"LOCAL_TEXT2IMG",size=self.size,seed=self.seed)
            self.images = images
            await self.context.send(file = discord.File(fp=self.parent.create_collage(images), filename=f"{self.spoiler.value}collage.png"), view=self)
        except Exception as e:
            #tell the user that something went wrong
            await self.context.send(f"Something went wrong: {e}")
            
        
    #variation button
    @discord.ui.button(label='Variation', style=discord.ButtonStyle.blurple, emoji="🔀", row=0)
    async def variation(self, interaction: discord.Interaction, button: discord.ui.Button):
        #check that the user that pressed the button is the same as the user that sent the message
        if(self.context.author != interaction.user):
            return
        #update the button
        button.disabled = True
        await interaction.response.edit_message(view=self)
        global liveRequestCount
        await self.context.send(f"{self.context.author} asked me to imagine variations of {self.prompt}{' with negative prompt: ' + self.negative_prompt if self.negative_prompt else ''} using size: {self.size}"  + f" There are {liveRequestCount} requests in progress")
        #get a new image
        try:
            images=None
            if(self.model != None and self.lora != None):
                self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_IMG2IMGMODELLORA",self.model,self.lora,self.size,self.seed)
            elif(self.model != None):
                self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_IMG2IMGMODEL",self.model,None,self.size,self.seed)
            elif(self.lora != None):
                self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_IMG2IMGLORA",None,self.lora,self.size,self.seed)
            else:
                self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_IMG2IMG",size=self.size,seed=self.seed)
        except Exception as e:
            #tell the user that something went wrong
            await self.context.send(f"Something went wrong: {e}")
            return
        
        
        reactions = await self.context.send(file = discord.File(fp=self.parent.create_collage(self.images), filename=f"{self.spoiler.value}collage.png"), view=self)
        #add number reactions
        #example: await reactions.add_reaction('1️⃣')
        #build list of reaction emojis
        reactios_to_add = []
        for i in range(len(self.images)):
            reactios_to_add.append(reaction_emojis[i])
         #send the reactions'
        await asyncio.gather(*[reactions.add_reaction(emoji) for emoji in reactios_to_add])
        
        
        #this section should be moved to its own handler
        #wait for reaction
        reaction = await self.context.bot.wait_for("reaction_add", check=lambda reaction, user: user == self.context.author and reaction.message.id == reactions.id and str(reaction.emoji) in reaction_emojis, timeout=self.timeout)
        #send the image corresponding to the reaction
        button.disabled = False
        #await self.context.send(file = discord.File(fp=self.images[reaction_emojis.index(str(reaction[0]))], filename=f"{self.spoiler.value}variation.png"), view=self)
        #acknolwedge the reaction
        await self.context.send(f"{self.context.author} chose {reaction[0]}")
        #get the index of the reaction from reaction_emojis
        index = reaction_emojis.index(str(reaction[0]))
        #send the image
        #clear all but the selected image
        self.images = [self.images[index]]
        #clear the reactions
        await reactions.clear_reactions()
        await self.context.send(file = discord.File(fp=self.parent.create_collage(self.images), filename=f"{self.spoiler.value}variation.png"), view=self)
        
    #upscale button
    @discord.ui.button(label='Upscale', style=discord.ButtonStyle.blurple, emoji="🔍", row=0)
    async def upscale(self, interaction: discord.Interaction, button: discord.ui.Button):
        #check that the user that pressed the button is the same as the user that sent the message
        if(self.context.author != interaction.user):
            return
        button.disabled = True
        await interaction.response.edit_message(view=self)
        button.disabled = False
        global liveRequestCount
        await self.context.send(f"{self.context.author} asked me to upscale {self.prompt}{' with negative prompt: ' + self.negative_prompt if self.negative_prompt else ''} using size: {self.size}"  + f" There are {liveRequestCount} requests in progress")
        self.size = str(int(int(self.size) * 1.5))
        try:
            self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_UPSCALE")
            await self.context.send(file = discord.File(fp=self.parent.create_collage(self.images), filename=f"{self.spoiler.value}collage.png"), view=self)
        except Exception as e:
            #tell the user that something went wrong
            await self.context.send(f"Something went wrong: {e}")
        return
    
    #downscale button
    @discord.ui.button(label='Downscale', style=discord.ButtonStyle.blurple, emoji="🔎", row=0)
    async def downscale(self, interaction: discord.Interaction, button: discord.ui.Button):
        #check that the user that pressed the button is the same as the user that sent the message
        if(self.context.author != interaction.user):
            return
        button.disabled = True
        await interaction.response.edit_message(view=self)
        button.disabled = False
        self.size = str(int(int(self.size) * .75))
        for i in range(len(self.images)):
            self.images[i] = self.images[i].resize((int(self.size), int(self.size)), PIL.Image.LANCZOS)
        await self.context.send(file = discord.File(fp=self.parent.create_collage(self.images), filename=f"{self.spoiler.value}collage.png"), view=self)
        return
    
    
#list of reaction emojis (from 1 to 9)
reaction_emojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']



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
        elif ctx.guild == None:
            return True
        return False
    
    def get_model_list(self):
        #get the list of models from the folder "/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/checkpoints"
        #each model is a file in that folder that ends with ".safetensors". strip the extension off the file name and list the files
        #get the list of files in the folder
        model_list = []
        for filename in os.listdir("/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/checkpoints"):
            if filename.endswith(".safetensors"):
                model_list.append(filename[:-12])
        return model_list
    
    def get_lora_list(self):
        #get the list of models from the folder "/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/lora"
        #each model is a file in that folder that ends with ".safetensors". strip the extension off the file name and list the files
        #get the list of files in the folder
        lora_list = []
        for filename in os.listdir("/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/loras"):
            if filename.endswith(".safetensors"):
                lora_list.append(filename[:-12])
        return lora_list

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.
    
    @commands.hybrid_command(
        name="imaginehelp",
        description="This command displays the help text, along with a list of available models and Loras",
    )
    @commands.check(channel_check)
    async def helpcommand(self, context: Context):
        #help command goes here
        message = f"""**StableDiffusion Bot Help**
**Command:** `/imagine`
Generate images with:
- `/imagine prompt="Your text here"`
**Optional:**
- `negative_prompt`: Avoid certain themes.
  - Ex: `negative_prompt="rain"`
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
  
**Models:** *(Dynamic list)*
"""
        #add models with get_model_list here
        for model in self.get_model_list():
            message += f"- {model}\n"
        
        message += f"\n**LORAs:** *(Dynamic list)*\n"
        #add loras with get_lora_list here
        for lora in self.get_lora_list():
            message += f"- {lora}\n"
        
        await context.send(message)
    
    #reaction handler
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        #get the message
        logger.info("on_reaction_add")
    
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
        name="imagine",
        description="This is a testing command that does nothing.",
    )
    @app_commands.describe(prompt='Prompt for the image being generated')
    @app_commands.describe(negative_prompt='Prompt for what you want to steer the AI away from')
    #@app_commands.guilds(discord.Object(id=837394309225381939)) # Place your guild ID her
    @app_commands.describe(model='Model to use for generation')
    @app_commands.describe(lora='Lora to use for generation')
    @app_commands.describe(size='Size of the image to generate')
    @app_commands.describe(seed='Seed for the random number generator')
    @app_commands.choices(spoiler=[
        app_commands.Choice(name='no spoiler', value=''),
        app_commands.Choice(name='spoiler', value='SPOILER_'),
                                   ])
    @commands.check(channel_check)
    async def imaginecommand(self, context: Context, prompt: str, negative_prompt: str=None, model: str=None, lora: str=None,seed: str=None, size: str='512',spoiler: app_commands.Choice[str]=None) -> None:
        """
        This command runs the stableDiffusion program and displays an image.

        :param context: The application command context.
        """
        #sanitize all the inputs using bleach
        prompt = bleach.clean(prompt)
        if negative_prompt != None:
            negative_prompt = bleach.clean(negative_prompt)
        if model != None:
            model = bleach.clean(model)
        if lora != None:
            lora = bleach.clean(lora)
        if seed != None:
            seed = bleach.clean(seed)
        if size != None:
            size = bleach.clean(size)
        
        
        if spoiler == None:
            spoiler = app_commands.Choice(name='no spoiler', value='')
        self.spolier = spoiler
        # Do your stuff here
        #create a view
        thisview = discord.ui.View(timeout=None)
        #send the view
        #tell the user what we are doing, optionally include the (negative prompt, model, and lora) if they are not None
        global liveRequestCount
        message = f"{context.author} asked me to imagine {prompt}{' with negative prompt: ' + negative_prompt if negative_prompt else ''} using size: {size}{', seed: ' + seed if seed else ''}."
        if(model != None):
            message += f" using model: {model}"
        if(lora != None):
            message += f" using lora: {lora}"
        
        sent = await context.send(message + f" There are {liveRequestCount} requests in progress", view=thisview)
        
        #generate seed if not provided
        if(seed == None):
            seed = random.randint(0,999999999999999)
            
        
        try:
            if(int(size) > 4000):
                throw("Size too large")
            images=None
            if(model != None and lora != None):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGMODELLORA",model,lora,size,seed)
            elif(model != None):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGMODEL",model,None,size,seed)
            elif(lora != None):
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMGLORA",None,lora,size,seed)
            else:
                images = await self.generate_images(prompt,negative_prompt,"LOCAL_TEXT2IMG",size=size,seed=seed)
            
            view=Buttons(self, context, prompt, negative_prompt, images, model, lora,size,seed,spoiler)
            #delete the message that we sent earlier
            await context.send(content=message + f" There are {liveRequestCount} requests in progress",file = discord.File(fp=self.create_collage(images), filename=f"{spoiler.value}collage.png"), view=view)
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

def queue_prompt(prompt, client_id, server_address):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    result = json.loads(urllib.request.urlopen(req).read())
    return result

def get_image(filename, subfolder, folder_type, server_address):
    #print("get_image filename:" + subfolder + filename)
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id, server_address):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())
    
def upload_image(filepath,server_address, subfolder=None, folder_type=None, overwrite=False):
    url = f"http://{server_address}/upload/image"
    files = {'image': open(filepath, 'rb')}
    data = {
        'overwrite': str(overwrite).lower()
    }
    if subfolder:
        data['subfolder'] = subfolder
    if folder_type:
        data['type'] = folder_type
    response = requests.post(url, files=files, data=data)
    return response.json()

#get the server address from the config file, round robin sequentially the addresses
currentServer = 0
def get_server_address(config):
    server_addresses = config['LOCAL']['SERVER_ADDRESS'].split(',')
    global currentServer
    server_address = server_addresses[currentServer]
    currentServer = (currentServer + 1) % len(server_addresses)
    return server_address

#ServerContext class, provides a server context for processes that need a server.
#Since each server stores temp files as part of some processes it is necessary to use the same server through that process
class ServerContext:
    def __init__(self, config):
        self.config = config
        self.server_address = get_server_address(config)


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
        global liveRequestCount
        liveRequestCount += 1
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
                    gif_data = get_image(gif['filename'], gif['subfolder'], gif['type'])
                    if 'final_output' in gif['filename']:
                        pil_gif = Image.open(BytesIO(gif_data))
                        
                        logger.info("ImageGenerator.get_images image data size:" + str(sys.getsizeof(pil_gif)))
                        output_images.append(pil_gif)

        liveRequestCount -= 1
        return output_images

    async def close(self):
        if self.ws:
            await self.ws.close()


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(Imagine(bot))
