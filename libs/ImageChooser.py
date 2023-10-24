#ImageChooser class(based on modal)
from libs.Comfy_interface import get_lora_list, get_model_list


import discord
from discord import ui
from discord.ext.commands import Context


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