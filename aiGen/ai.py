from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, StableDiffusionDepth2ImgPipeline, StableDiffusionUpscalePipeline
from io import BytesIO
import torch
import requests
import warnings
import time
import json
import base64
import random
import os
from discord_webhook import DiscordWebhook
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("Connecting...")

apiURL = "http://192.168.4.50:3504/worker"
webhookURL = "https://discord.com/api/webhooks"
uploadURL = None # Not done

config = {
    "cpuMode": False,
    "uploadToDiscord": False,
    "upload": False,
    "saveFile":False,
    "copyright":False,
    
    "workerID": None,
    "currentJob": None,
    "isJobMode": True
}
working = False

def makeRequest(typeIn, batchData=None, jobID=None, updateData=None):
    global apiURL
    global config
    
    if not config["workerID"]:
        response = requests.post(f"{apiURL}/add")
        responseData = response.json()
        if "good" in responseData and "workerID" in responseData:
            config["workerID"] = responseData["workerID"]
        else:
            print("[Warn] Failed to add worker!")
    
    headers = {'Content-Type': 'application/json'}
    defaultData = {}
    defaultData["workerID"] = config["workerID"]
    defaultData["jobID"] = config["currentJob"]
    match typeIn:
        case "uploadOLD":
            # base64IMG = base64.b64encode(fileData).decode("utf8")
            # defaultData["image"] = base64IMG
            # defaultData["number"] = number
            # response = requests.post(f"{apiURL}/upload", data=json.dumps(defaultData), headers=headers)
            return False
        case "upload":
            defaultData["images"] = batchData
            response = requests.post(f"{apiURL}/upload", data=json.dumps(defaultData), headers=headers)
            return True
        case "get":
            # TODO: Make it upload basic data about the worker, EG GPU memery, etc
            response = requests.get(f"{apiURL}/get", data=json.dumps(defaultData), headers=headers)
            js = response.json()
            if "good" in js:
                return js
            else:
                return None
        case "update":
            defaultData["update"] = updateData
            response = requests.post(f"{apiURL}/update", data=json.dumps(defaultData), headers=headers)
        case "getTypes":
            response = requests.get(f"{apiURL}/types", data=json.dumps(defaultData), headers=headers)
            return response.json() # EG ["andite/anything-v4.0","katakana/2D-Mix"]

# models = makeRequest("getTypes")

# print("Loading models...")
# pipes = {}
# 
# with warnings.catch_warnings():
#     warnings.simplefilter("ignore")
#     for model in models:
#         pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float16)
#         pipe = pipe.to("cuda")
#         pipe.safety_checker = lambda images, clip_input: (images, False)
#         if False:
#             pipe.enable_attention_slicing()
#         pipes[model] = pipe

print("Ready")

def progress_function(step: int, timestep: int, latents: torch.FloatTensor):
    global apiURL
    global config
    progress = step
    
    if config["isJobMode"]:
        makeRequest("update", jobID=config["currentJob"], updateData=progress)

def t2i(steps=50, jobID=None, model=None, prompt="Error", negPrompt="Error",imgs=1, scale=7.5, height=512, width=512, progress=progress_function):
    global apiURL
    global working
    
    global config
    
    print(f"Creating model [{model}]")
    
    warnings.simplefilter("ignore")
    pipe = None
    
    if config["cpuMode"]:
        # print("CPU")
        pipe = StableDiffusionPipeline.from_pretrained(model)
        pipe = pipe.to("cpu")
    else:
        # print("CUDA")
        pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float16)
        pipe = pipe.to("cuda")
        
    pipe.safety_checker = lambda images, clip_input: (images, False) # Allows NSFW!!
    
    print(f"Generating job [{jobID}] with prompt [{prompt}]")
    
    start = time.time()
    images = pipe(
        prompt,
        negative_prompt=negPrompt,
        callback=progress,
        guidance_scale=int(scale),
        num_inference_steps=int(steps),
        num_images_per_prompt=int(imgs) or 1,
        height=int(height) or 512,
        width=int(width) or 512
    ).images
    end = time.time()
    
    total = end-start
    
    print(f"Finished generating prompt [{jobID}]")
    
    batch = {}
    if config["uploadToDiscord"]:
        webhook = DiscordWebhook(url=webhookURL, content=f"Prompt: {prompt}\nNegprompt: {negPrompt}\nTime: {total}")
    
    if config["saveFile"]:
        path = "imgs/"+prompt+str(random.randint(-999,999))
        if not os.path.exists(path):
            os.makedirs(path)
    
    for imageIndex, image in enumerate(images):
        # Draw the text on the image, might remove
        if config["copyright"]:
            ImageDraw.Draw(image).text((image.size[0]/3, 10), "AI IMAGE, ©ai.airplanegobrr.xyz", font=ImageFont.truetype("arial.ttf", size=20), fill=(255, 255, 255), align="center", anchor="mm")
            ImageDraw.Draw(image).text((image.size[0]-180, image.size[1]-10), "AI IMAGE, ©ai.airplanegobrr.xyz", font=ImageFont.truetype("arial.ttf", size=20), fill=(255, 255, 255), align="center", anchor="mm")
        
        # Save the image to a file for debugging purposes
        with BytesIO() as image_io:
            image.save(image_io, format="PNG")
            image_io.seek(0)
            base64IMG = base64.b64encode(image_io.read()).decode("utf8")
            
            if config["uploadToDiscord"]:
                webhook.add_file(file=image_io, filename=f"{str(imageIndex)}.png")
        
            # Add the encoded image to the batch
            batch[imageIndex] = base64IMG
    
    if config["isJobMode"]:
        makeRequest("upload", batchData=batch, jobID=config["currentJob"])
        print(f"Submitted [{jobID}]")
    output = {
        "path": path,
        "images": list(images),
        "total": total
    }
    working = False
    return output

def i2i():
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16)

    pipe = pipe.to("cuda")

    url = "https://raw.githubusercontent.com/CompVis/stable-diffusion/main/assets/stable-samples/img2img/sketch-mountains-input.jpg"

    response = requests.get(url)

    init_image = Image.open(BytesIO(response.content)).convert("RGB")

    init_image = init_image.resize((768, 512))

    prompt = "A fantasy landscape, trending on artstation"

    images = pipe(prompt=prompt, image=init_image, strength=0.75, guidance_scale=7.5).images

    images[0].save("fantasy_landscape.png")

def d2i():
    # Prompt + Image
    pipe = StableDiffusionDepth2ImgPipeline.from_pretrained("stabilityai/stable-diffusion-2-depth",torch_dtype=torch.float16,)

    pipe.to("cuda")


    url = "http://images.cocodataset.org/val2017/000000039769.jpg"

    init_image = Image.open(requests.get(url, stream=True).raw)

    prompt = "two tigers"

    n_propmt = "bad, deformed, ugly, bad anotomy"

    image = pipe(prompt=prompt, image=init_image, negative_prompt=n_propmt, strength=0.7).images[0]

def upscale(image=None, prompt=None):
    pipe = StableDiffusionUpscalePipeline.from_pretrained("stabilityai/stable-diffusion-x4-upscaler", revision="fp16", torch_dtype=torch.float16)

    pipe = pipe.to("cuda")

    upscaled_image = pipe(prompt=prompt, image=Image.open(BytesIO(image)).convert("RGB").resize((128, 128))).images[0]

    upscaled_image.save("upsampled_cat.png")

def check():
    print("Checking", working)
    if not working:
        try:
            jsonO = makeRequest("get")
            # print(jsonO)
            # print(jsonO["jobID"])
            if jsonO and "jobID" in jsonO:
                config["currentJob"] = jsonO["jobID"]
                working = True # This shouldn't be needed but there was an issue
                t2i(steps=jsonO["sample"] or 50, jobID=config["currentJob"], model=jsonO["model"] or "andite/anything-v4.0", prompt=jsonO["prompt"] or "Error", imgs=jsonO["imgs"] or 1, negPrompt=jsonO["negPrompt"] or "Error")
        except Exception as e:
            print(e)
            working = False
        finally: 
            print("Done")

# while True:
    # check()
    # time.sleep(1)
