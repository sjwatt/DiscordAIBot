import json
import os
import urllib.parse
import urllib.request

import requests


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


def get_model_list(startpos=0):
    # get the list of models from the folder "/mnt/nvme0n1p2/home/llm/comfy/ComfyUI/models/checkpoints"
    # each model is a file in that folder that ends with ".safetensors". strip the extension off the file name and list the files
    # get the list of files in the folder
    # get directory of this program
    model_list = []
    directory = os.path.dirname(os.path.realpath(__file__))
    checkpoints_dir = os.path.join(directory, "../../comfy/ComfyUI/models/checkpoints")
    for filename in os.listdir(checkpoints_dir):
        if filename.endswith(".safetensors"):
            model_list.append(filename[:-12])
    # limit the list to 25 items starting at startpos
    model_list = model_list[startpos:]
    model_list = model_list[:25]
    return model_list


def get_lora_list():
    lora_list = []
    #get directory of this program
    directory = os.path.dirname(os.path.realpath(__file__))
    #the relative directory is ../comfy/ComfyUI/models/lora
    for filename in os.listdir(directory + "../../comfy/ComfyUI/models/lora"):
        if filename.endswith(".safetensors"):
            lora_list.append(filename[:-12])
    return lora_list


def get_model_list_long():
    #get the list of models from the folder "/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/checkpoints"
    #each model is a file in that folder that ends with ".safetensors". strip the extension off the file name and list the files
    #get the list of files in the folder
    model_list = []
    directory = os.path.dirname(os.path.realpath(__file__))
    #trim the last 2 directories off the path
    directory = os.path.dirname(os.path.dirname(directory))
    
    for filename in os.listdir(directory + "/comfy/ComfyUI/models/checkpoints"):
        if filename.endswith(".safetensors"):
            model_list.append(filename[:-12])
            
    #sort the list
    model_list.sort()
    return model_list


def get_lora_list_long():
    #get the list of models from the folder "/media/llm/62717d96-7640-4917-bbdf-12e5ee74fd65/home/llm/comfy/ComfyUI/models/lora"
    #each model is a file in that folder that ends with ".safetensors". strip the extension off the file name and list the files
    #get the list of files in the folder
    lora_list = []
    directory = os.path.dirname(os.path.realpath(__file__))
    #trim the last 2 directories off the path
    directory = os.path.dirname(os.path.dirname(directory))
    
    for filename in os.listdir(directory + "/comfy/ComfyUI/models/loras"):
        if filename.endswith(".safetensors"):
            lora_list.append(filename[:-12])
    #sort the list
    lora_list.sort()
    return lora_list