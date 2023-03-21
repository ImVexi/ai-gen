from diffusers import StableDiffusionPipeline
import torch
import requests
from io import BytesIO
import warnings
import time
import json
import base64
import asyncio

print("Connecting...")

apiURL = "http://192.168.4.50:3504/worker"

workerID = None
currentJobID = None

def makeRequest(typeIn, fileData=None, jobID=None, updateData=None,number=None):
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
        case "upload":
            base64IMG = base64.b64encode(fileData).decode("utf8")
            defaultData["image"] = base64IMG
            defaultData["number"] = number
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

def generate(steps=50, jobID=None, model=None, prompt="Error", imgs=1):
    global workerID
    global currentJobID
    global apiURL
    print(f"Generating prompt [{jobID}] with model {model}")
    
    warnings.simplefilter("ignore")
    pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float16)
    pipe = pipe.to("cuda")
    
    images = pipe(prompt, num_inference_steps=int(steps), callback=progress_function, num_images_per_prompt=int(imgs) or 1).images
    for imageIndex,image in enumerate(images):
        
        image_io = BytesIO()
        image.save(image_io, format="PNG")
        image_io.seek(0)
        data = image_io.read()
        asyncio.run(makeRequest("upload", fileData=data, jobID=currentJobID, number=imageIndex))

    print(f"Finished generating prompt [{jobID}]")
    
    
    print(f"Submitted [{jobID}]")


while True:
    print("Checking")
    try:
        jsonO = makeRequest("get")
        print(jsonO)
        print(jsonO["jobID"])
        if "jobID" in jsonO:
            currentJobID = jsonO["jobID"]
            generate(steps=jsonO["sample"] or 50, jobID=currentJobID, model=jsonO["model"] or "andite/anything-v4.0", prompt=jsonO["prompt"] or "Error", imgs=jsonO["imgs"] or 1)
    except:
        None
    finally: 
        print("Done")
    time.sleep(1)
