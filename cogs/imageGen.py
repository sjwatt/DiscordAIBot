""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 6.1.0
"""

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
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

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)

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
        
        message = f"{self.context.author} asked me to imagine {self.prompt}{' with negative prompt: ' + self.negative_prompt if self.negative_prompt else ''} using size: {self.size}"
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
        
    #variation button
    @discord.ui.button(label='Variation', style=discord.ButtonStyle.blurple, emoji="🔀", row=0)
    async def variation(self, interaction: discord.Interaction, button: discord.ui.Button):
        #update the button
        button.disabled = True
        await interaction.response.edit_message(view=self)
        #get a new image
        images=None
        if(self.model != None and self.lora != None):
            self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_IMG2IMGMODELLORA",self.model,self.lora,self.size,self.seed)
        elif(self.model != None):
            self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_IMG2IMGMODEL",self.model,None,self.size,self.seed)
        elif(self.lora != None):
            self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_IMG2IMGLORA",None,self.lora,self.size,self.seed)
        else:
            self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_IMG2IMG",size=self.size,seed=self.seed)
        
        
        
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
        await self.context.send(f"{self.context.author} reacted with {reaction[0]}")
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
        button.disabled = True
        await interaction.response.edit_message(view=self)
        button.disabled = False
        self.size = str(int(int(self.size) * 1.5))
        
        self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_UPSCALE")
        await self.context.send(file = discord.File(fp=self.parent.create_collage(self.images), filename=f"{self.spoiler.value}collage.png"), view=self)
        
        return
    
    #downscale button
    @discord.ui.button(label='Downscale', style=discord.ButtonStyle.blurple, emoji="🔎", row=0)
    async def downscale(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.

    #reaction handler
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        #get the message
        logger.info("on_reaction_add")
    
    
    #check if channel allowed or is DM
    def channel_check(ctx):
        if ctx.bot.channel_check(ctx):
            return True
        elif ctx.guild == None:
            return True
        return False
    
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
        if spoiler == None:
            spoiler = app_commands.Choice(name='no spoiler', value='')
        self.spolier = spoiler
        # Do your stuff here
        #create a view
        thisview = discord.ui.View(timeout=None)
        #send the view
        #tell the user what we are doing, optionally include the (negative prompt, model, and lora) if they are not None
        message = f"{context.author} asked me to imagine {prompt}{' with negative prompt: ' + negative_prompt if negative_prompt else ''} using size: {size}{', seed: ' + seed if seed else ''}"
        if(model != None):
            message += f" using model: {model}"
        if(lora != None):
            message += f" using lora: {lora}"
        
        await context.send(message, view=thisview)
        
        #generate seed if not provided
        if(seed == None):
            seed = random.randint(0,999999999999999)
            
        
        
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
        await context.send(file = discord.File(fp=self.create_collage(images), filename=f"{spoiler.value}collage.png"), view=view)

    async def generate_images(self, prompt: str,negative_prompt: str, config_name: str, model: str=None, lora: str=None, size: str="512", seed: int=random.randint(0,999999999999999)):
        with open(self.config[config_name]['CONFIG'], 'r') as file:
            workflow = json.load(file)
        
        generator = ImageGenerator(self.config)
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
        
        response_data = upload_image(temp_filepath,self.config['LOCAL']['SERVER_ADDRESS'])
        filename = response_data['name']
        
        with open(self.config[config_name]['CONFIG'], 'r') as file:
            workflow = json.load(file)
        
        generator = ImageGenerator(self.config)
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
    return json.loads(urllib.request.urlopen(req).read())

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

class ImageGenerator:
    def __init__(self, config):
        self.config = config
        self.client_id = str(uuid.uuid4())
        self.uri = f"ws://{config['LOCAL']['SERVER_ADDRESS']}/ws?clientId={self.client_id}"
        self.ws = None
        

    async def connect(self):
        self.ws = await websockets.connect(self.uri)

    async def get_images(self, prompt):
        if not self.ws:
            await self.connect()
    
        prompt_id = queue_prompt(prompt, self.client_id,self.config['LOCAL']['SERVER_ADDRESS'])['prompt_id']
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
                
        history = get_history(prompt_id,self.config['LOCAL']['SERVER_ADDRESS'])[prompt_id]
        #print("ImageGenerator.get_images history: " + str(history))
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image['subfolder'], image['type'],self.config['LOCAL']['SERVER_ADDRESS'])
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


        return output_images

    async def close(self):
        if self.ws:
            await self.ws.close()


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(Imagine(bot))
