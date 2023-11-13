
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext import tasks
#import modal stuff
from discord import ui
import os
import logging
import time

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)

class Janitor(commands.Cog, name="janitor"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.clear_temp_files.start(self)
        
    @commands.command(
        name="ping",
        description="Returns the bot's latency in milliseconds.",
    )
    async def ping(self, ctx: Context) -> None:
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")
    
    #clear the temp files every n seconds
    @tasks.loop(seconds=10)
    async def clear_temp_files(self,*args):
        #TODO: clear the temp files from the bot
        #the temp files are in the /out folder relative to bot.py, delete anything older than 10 minutes
        for file in os.listdir("out"):
            if file.endswith(".png"):
                if os.path.getmtime("out/"+file) < time.time() - 600:
                    os.remove("out/"+file)
                    logger.info("Deleting file: " + "out/"+file)
        #TODO: clear the temp files from Comfy
        comfyDir = "../ComfyUI/"
        for subdir in ["output/","input/","temp/"]:
            for file in os.listdir(comfyDir + subdir):
                if file.endswith(".png"):
                    if os.path.getmtime(comfyDir+subdir+file) < time.time() - 600:
                        os.remove(comfyDir+subdir+file)
                        logger.info("Deleting file: " + comfyDir+subdir+file)
        
   
async def setup(bot) -> None:
    await bot.add_cog(Janitor(bot))
