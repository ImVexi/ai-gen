from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, StableDiffusionDepth2ImgPipeline, StableDiffusionUpscalePipeline
from io import BytesIO
from PIL import Image
import torch
import requests
import warnings
import time
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import nvidia_smi

GPUMode = False
GPUMem = 0
GPUCount = None

nvidia_smi.nvmlInit()
GPUCount = nvidia_smi.nvmlDeviceGetCount()
if GPUCount > 0:
    handle = nvidia_smi.nvmlDeviceGetHandleByIndex(1)
    info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
    max = round((info.total/1024)/1024,2)
    print(max)

print("Connecting...")

apiURL = "http://192.168.4.50:3504/worker"

workerID = None
currentJobID = None
working = False

def makeRequest(typeIn, batchData=None, jobID=None, updateData=None):
    global workerID
    global currentJobID
    global apiURL
    
    if not workerID:
        response = requests.post(f"{apiURL}/add")
        responseData = response.json()
        if "good" in responseData and "workerID" in responseData:
            workerID = responseData["workerID"]
        else:
            print("[Warn] Failed to add worker!")
    
    headers = {'Content-Type': 'application/json'}
    defaultData = {}
    defaultData["workerID"] = workerID
    defaultData["jobID"] = jobID
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


models = makeRequest("getTypes")

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

print("Ready as", workerID)

def progress_function(step: int, timestep: int, latents: torch.FloatTensor):
    # Calculate the progress as a percentage
    progress = (step) 

    # Update the progress bar
    # if progress%1 == 1:
    global workerID
    global currentJobID
    global apiURL
    # print(f"Progress: {progress} {currentJobID}")
    makeRequest("update", jobID=currentJobID, updateData=progress)

def t2i(steps=50, jobID=None, model=None, prompt="Error", negPrompt="Error",imgs=1, scale=7.5):
    global workerID
    global currentJobID
    global apiURL
    global working
    
    print(f"Creating model [{model}]")
    
    warnings.simplefilter("ignore")
    pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float16)
    pipe = pipe.to("cuda")
    pipe.safety_checker = lambda images, clip_input: (images, False) # Allows NSFW!!
    
    print(f"Generating job [{jobID}] with prompt [{prompt}]")
    
    
    images = pipe(prompt, negative_prompt=negPrompt, guidance_scale=int(scale), num_inference_steps=int(steps), callback=progress_function, num_images_per_prompt=int(imgs) or 1).images
    
    print(f"Finished generating prompt [{jobID}]")
    
    batch = {}
    
    for imageIndex, image in enumerate(images):
        # Draw the text on the image, might remove
        ImageDraw.Draw(image).text((image.size[0]/3, 10), "AI IMAGE, ©ai.airplanegobrr.xyz", font=ImageFont.truetype("arial.ttf", size=20), fill=(255, 255, 255), align="center", anchor="mm")
        ImageDraw.Draw(image).text((image.size[0]-180, image.size[1]-10), "AI IMAGE, ©ai.airplanegobrr.xyz", font=ImageFont.truetype("arial.ttf", size=20), fill=(255, 255, 255), align="center", anchor="mm")
        
        # Save the image to a file for debugging purposes
        with BytesIO() as image_io:
            image.save(image_io, format="PNG")
            image_io.seek(0)
            base64IMG = base64.b64encode(image_io.read()).decode("utf8")
        
            # Add the encoded image to the batch
            batch[imageIndex] = base64IMG
        
    makeRequest("upload", batchData=batch, jobID=currentJobID)
    print(f"Submitted [{jobID}]")
    working = False

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

while True:
    print("Checking", working)
    if not working:
        try:
            jsonO = makeRequest("get")
            # print(jsonO)
            # print(jsonO["jobID"])
            if jsonO and "jobID" in jsonO:
                currentJobID = jsonO["jobID"]
                working = True # This shouldn't be needed but there was an issue
                t2i(steps=jsonO["sample"] or 50, jobID=currentJobID, model=jsonO["model"] or "andite/anything-v4.0", prompt=jsonO["prompt"] or "Error", imgs=jsonO["imgs"] or 1, negPrompt=jsonO["negPrompt"] or "Error")
        except Exception as e:
            print(e)
        finally: 
            print("Done")
    time.sleep(1)
