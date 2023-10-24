from discord import ui
from libs.LiveRequestTracker import LiveRequestTracker
import PIL
import discord
from discord.ext.commands import Context
import asyncio
import random
import logging

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)

#list of reaction emojis (from 1 to 9)
reaction_emojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']


class PromptModal(discord.ui.Modal):
    def __init__(self, context: Context,title="Input", prompt: str="", negative_prompt: str=""):
        super().__init__(timeout=None, title=title)
        self.context = context
        self.title = title
        self.input = ui.TextInput(label="prompt", placeholder=prompt)
        self.add_item(self.input)
        self.input2 = ui.TextInput(label="negative prompt", placeholder=negative_prompt)
        self.add_item(self.input2)

    async def on_submit(self, interaction: discord.Interaction):
        #store the new prompt in the database
        #get the current config


        config = await self.context.bot.database.get_config(self.context.author.id)

        #update the config
        config["prompt"] = self.input.value
        config["negative_prompt"] = self.input2.value
        #store the config in the database
        await self.context.bot.database.store_config(self.context.author.id, config)


        #tell the user that we updated the prompt
        await interaction.response.send_message(f"Updated prompt to: {self.input.value}")

class StandardView(discord.ui.View):
    def __init__(self, parent, context: Context, prompt, negative_prompt, images, model, lora,size,seed,spoiler,requests, *, timeout=300):
        super().__init__(timeout=timeout)
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.images = images

        self.old_images = {}
        self.model = model
        self.lora = lora
        self.context = context
        self.parent = parent
        self.timeout = timeout
        self.size = size
        self.seed = seed
        self.spoiler = spoiler
        self.requests = requests

    #re-roll button
    @discord.ui.button(label='Re-roll', style=discord.ButtonStyle.green, emoji="🎲", row=0)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        #check that the user that pressed the button is the same as the user that sent the message
        if(self.context.author != interaction.user):
            return
        message = f"{self.context.author} asked me to imagine {self.prompt}{' with negative prompt: ' + self.negative_prompt if self.negative_prompt else ''} using size: {self.size}" + f" There are {self.requests.get()} requests in progress"
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
        if self.model == "":
            self.model = None
        if self.lora == "":
            self.lora = None
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
            self.old_images[interaction.message.id] = self.images
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
        #check to see if the prompt has changed
        config = await self.context.bot.database.get_config(self.context.author.id)
        if config.get('prompt') != self.prompt:
            self.prompt = config.get('prompt')
        await self.context.send(f"{self.context.author} asked me to imagine variations of {self.prompt}{' with negative prompt: ' + self.negative_prompt if self.negative_prompt else ''} using size: {self.size}"  + f" There are {self.requests.get()} requests in progress")
        #get a new image
        if self.model == "":
            self.model = None
        if self.lora == "":
            self.lora = None
        try:
            images=None
            self.old_images[interaction.message.id] = self.images
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
        self.old_images[interaction.message.id] = self.images
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
        await self.context.send(f"{self.context.author} asked me to upscale {self.prompt}{' with negative prompt: ' + self.negative_prompt if self.negative_prompt else ''} using size: {self.size}"  + f" There are {self.requests.get()} requests in progress")
        #get the size from self.images[0]
        size = self.images[0].size
        logger.info(f"size: {size}")
        self.size = str(int(int(self.size) * 1.5))
        try:
            self.old_images[interaction.message.id] = self.images
            self.images = await self.parent.generate_variations(self.images[0],self.prompt,self.negative_prompt,"LOCAL_UPSCALE")
            await self.context.send(file = discord.File(fp=self.parent.create_collage(self.images), filename=f"{self.spoiler.value}collage.png"), view=self)
        except Exception as e:
            #tell the user that something went wrong
            await self.context.send(f"Something went wrong: {e}")
        return

    #downscale button
    @discord.ui.button(label='Downscale', style=discord.ButtonStyle.blurple, emoji="🔎", row=1)
    async def downscale(self, interaction: discord.Interaction, button: discord.ui.Button):
        #check that the user that pressed the button is the same as the user that sent the message
        if(self.context.author != interaction.user):
            return
        button.disabled = True
        await interaction.response.edit_message(view=self)
        button.disabled = False
        self.size = str(int(int(self.size) * .75))
        for i in range(len(self.images)):
            self.old_images[interaction.message.id] = self.images
            self.images[i] = self.images[i].resize((int(self.size), int(self.size)), PIL.Image.LANCZOS)
        await self.context.send(file = discord.File(fp=self.parent.create_collage(self.images), filename=f"{self.spoiler.value}collage.png"), view=self)
        return

    @discord.ui.button(label='Change Prompt', style=discord.ButtonStyle.blurple, emoji="📝", row=1)
    async def changeprompt(self, interaction: discord.Interaction, button: discord.ui.Button):
        if(self.context.author != interaction.user):
            return
        #send a modal to ask for a new prompt
        modal = PromptModal(context=self.context,title="Prompt",prompt=self.prompt, negative_prompt=self.negative_prompt)
        await interaction.response.send_modal(modal)
        #update self.prompt from the database
        config = await self.context.bot.database.get_config(self.context.author.id)
        self.prompt = config.get('prompt')
        self.negative_prompt = config.get('negative_prompt')


    @discord.ui.button(label='Save to DM', style=discord.ButtonStyle.blurple, emoji="💾", row=1)
    async def savetodm(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(view=self)
        #logger.info(f"self.old_images: {self.old_images}")
        #logger.info(f"message id: {interaction.message.id}")
        images = None
        #check to see if the message id is in self.old_images
        if interaction.message.id in self.old_images:
            #if it is, use the old images
            images = self.old_images[interaction.message.id]
        else:
            #if it isn't, use the new images
            images = self.images
        #save all of the image to the user's DMs
        for image in images:
            await interaction.user.send(file = discord.File(fp=self.parent.create_collage([image]), filename=f"{self.spoiler.value}image.png"))
        await self.context.send(f"Saved to DMs")