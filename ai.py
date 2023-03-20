from diffusers import StableDiffusionPipeline
import torch
import requests
from io import BytesIO
import warnings
import time
import json
import base64

print("Connecting...")

print(f"Identifying as worker")

pipes = {}

apiURL = "http://192.168.4.50:3504/worker"

print("Loading models...")

# ,"katakana/2D-Mix"

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for model in ["andite/anything-v4.0","katakana/2D-Mix"]:
        pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float16)
        pipe = pipe.to("cuda")
        pipe.safety_checker = lambda images, clip_input: (images, False)
        if False:
            pipe.enable_attention_slicing()
        pipes[model] = pipe

print("Ready!")


def generate(prompt, steps= 50):
    print(f"Generating prompt [{prompt['jobID']}] with model {prompt['model']}")
    if ("sample" in prompt):
        steps = prompt["sample"]
    print(steps, prompt)
    pipe = pipes[prompt['model']]
    image = pipe(prompt['prompt'], num_inference_steps=int(steps), negative_prompt="").images[0]
    
    image_io = BytesIO()
    image.save(image_io, format="PNG")
    image_io.seek(0)
    data = image_io.read()
    # with open(f"imgs/{prompt['id']}-{random.randrange(5)}.png", "wb") as r:
    #     r.write(data)

    print(f"Finished generating prompt [{prompt['jobID']}]")
    
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    base64IMG = base64.b64encode(data).decode("utf8")
    payload = json.dumps({"image": base64IMG})
    e = requests.post(f"{apiURL}/done/{prompt['jobID']}", data=payload, headers=headers)
    print(e.text)
    print(f"Submitted [{prompt['jobID']}]")


while True:
    print("Checking")
    try:
        response = requests.get(f"{apiURL}/get")
        jsonO = response.json()
        print(jsonO)
        if "jobID" in jsonO:
            generate(jsonO)
    finally: 
        print("Done")
    time.sleep(0.5)
