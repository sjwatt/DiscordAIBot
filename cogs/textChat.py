""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 6.1.0
"""

from discord.ext import commands
from discord.ext.commands import Context
import requests
import html

#get logging
import logging
logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)

# Here we name the cog and create a new class for the cog.
class TextChat(commands.Cog, name="textChat"):
    def __init__(self, bot) -> None:
        self.bot = bot

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.

    @commands.hybrid_command(
        name="chat",
        description="Chat with the AI",
    )
    async def testcommand(self, context: Context, prompt: str) -> None:
        """
        This is a testing command that does nothing.

        :param context: The application command context.
        """
        # Do your stuff here
        await context.defer()
        #get the id of the conversation, for a channel it's the channel id for a dm it's the user id
        history_id = context.channel.id
        logger.info("history_id: " + str(history_id))
        
        response = run_chatbot(prompt, history_id)
        await context.send(context.author.name + ": " + prompt + "\n" + "AI: " + response)
        # Don't forget to remove "pass", I added this just because there's no content in the method.
        
    @commands.hybrid_command(
        name="resetchathistory",
        description="Reset the chat history for this channel",
    )
    async def resetchathistory(self, context: Context) -> None:
        """
        This is a testing command that does nothing.

        :param context: The application command context.
        """
        # Do your stuff here
        await context.defer()
        #get the id of the conversation, for a channel it's the channel id for a dm it's the user id
        history_id = context.channel.id
        
        #open the history file
        with open('history', 'r') as file:
            history = file.read()
            if history == '':
                history = {'0': {'internal': [], 'visible': []}}
            else:
                history = eval(history)
        #check the history for the conversation
        if history_id in history:
            history[history_id] = {'internal': [], 'visible': []}
        else:
            history[history_id] = {'internal': [], 'visible': []}
        #save the history to file
        with open('history', 'w') as file:
            file.write(str(history))
        await context.send("Chat history reset")

HOST = 'localhost:5000'
URI = f'http://{HOST}/api/v1/chat'

with open('context', 'r') as file:
    context = file.read()
with open('greeting', 'r') as file:
    greeting = file.read()

def run_chatbot(user_input, history_id):
    #open the history file
    with open('history', 'r') as file:
        history = file.read()
        if history == '':
            history = {'0': {'internal': [], 'visible': []}}
        else:
            history = eval(history)
    #check the history for the conversation
    if history_id in history:
        pass
    else:
        history[history_id] = {'internal': [], 'visible': []}
    print(user_input)
    logger.info("history: " + str(history[history_id]))
    request = {
        'user_input': user_input,
        'max_new_tokens': 1000,
        'auto_max_new_tokens': True,
        'max_tokens_second': 0,
        'history': history[history_id],
        'mode': 'chat',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'character': 'Example',
        'instruction_template': 'Vicuna-v1.1',  # Will get autodetected if unset
        'your_name': 'You',
         'name1': 'You', # Optional
         'name2': 'Chiharu Yamada', # Optional
         'context': context,
        # Optional
        'greeting': greeting, # Optional
        'name1_instruct': 'USER:', # Optional
        'name2_instruct': 'ASSISTANT:', # Optional
        'context_instruct': 'A chat between a curious user and an affectionate Anime girl. She has an incredibly interesting and complex past and character. She is polite, friendly and looking for love. She loves to talk a lot.', # Optional
        'turn_template': '<|user|> <|user-message|>\n<|bot|> <|bot-message|></s>\n', # Optional
        'regenerate': False,
        '_continue': False,
        'chat_instruct_command': 'Continue the chat dialogue below. Write a single reply for the character "<|character|>".\n\n<|prompt|>',

        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'simple-1',
        # 'do_sample': True,
        # 'temperature': 0.7,
        # 'top_p': 0.1,
        # 'typical_p': 1,
        # 'epsilon_cutoff': 0,  # In units of 1e-4
        # 'eta_cutoff': 0,  # In units of 1e-4
        # 'tfs': 1,
        # 'top_a': 0,
        # 'repetition_penalty': 1.18,
        # 'repetition_penalty_range': 0,
        # 'top_k': 40,
        # 'min_length': 100,
        # 'no_repeat_ngram_size': 0,
        # 'num_beams': 1,
        # 'penalty_alpha': 0,
        # 'length_penalty': 1,
        # 'early_stopping': False,
        # 'mirostat_mode': 0,
        # 'mirostat_tau': 5,
        # 'mirostat_eta': 0.1,
        # 'grammar_string': '',
        # 'guidance_scale': 1,
        # 'negative_prompt': '',

        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2048,
        'ban_eos_token': False,
        'custom_token_bans': '',
        'skip_special_tokens': True,
        'stopping_strings': []
    }

    response = requests.post(URI, json=request)
    if response.status_code == 200:
        history[history_id] = response.json()['results'][0]['history']
        #save the history to file
        with open('history', 'w') as file:
            file.write(str(history))
        #print(history)
        result2 = history[history_id]['visible'][-1][-1]
        result3 = html.unescape(result2)
        return result3

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(TextChat(bot))