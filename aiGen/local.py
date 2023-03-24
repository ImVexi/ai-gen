from diffusers import StableDiffusionPipeline
import torch
import warnings
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
import random
import os
import time
from discord_webhook import DiscordWebhook, DiscordEmbed

cpuMode = True
uploadToDiscord = True
upload = True
saveFile = True
copyright = True

webhookURL = "https://discord.com/api/webhooks"

def noneDef(*a, **k):
    None

def t2i(steps=50, model=None, prompt="Error", negPrompt="Error",imgs=1, scale=7.5, height=512, width=512, progress=noneDef):
    print(f"Creating model [{model}]")
    
    warnings.simplefilter("ignore")
    pipe = None
    
    if cpuMode:
        pipe = StableDiffusionPipeline.from_pretrained(model)
        pipe = pipe.to("cpu")
    else:
        pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float16)
        pipe = pipe.to("cuda")
    
    pipe.safety_checker = lambda images, clip_input: (images, False) # Allows NSFW!!
    
    print(f"Generating with prompt [{prompt}]")
    
    start = time.time()
    images = pipe(prompt, negative_prompt=negPrompt, callback=progress, guidance_scale=int(scale), num_inference_steps=int(steps), num_images_per_prompt=int(imgs) or 1, height=int(height) or 512, width=int(width) or 512).images
    end = time.time()
    
    total = end-start
    
    print(f"Finished generating prompt")
    
    batch = {}
    
    path = "imgs/"+prompt+str(random.randint(-999,999))
    if not os.path.exists(path):
        os.makedirs(path)
    
    if uploadToDiscord:
        webhook = DiscordWebhook(url=webhookURL, content=f"Prompt: {prompt}\nNegprompt: {negPrompt}\nTime: {total}")
    
    imagesOutput = list(images)
    
    for imageIndex, image in enumerate(images):
        
        # Draw the text on the image, might remove
        if copyright:
            ImageDraw.Draw(image).text((image.size[0]/3, 10), "AI IMAGE, ©ai.airplanegobrr.xyz", font=ImageFont.truetype("arial.ttf", size=20), fill=(255, 255, 255), align="center", anchor="mm")
            ImageDraw.Draw(image).text((image.size[0]-180, image.size[1]-10), "AI IMAGE, ©ai.airplanegobrr.xyz", font=ImageFont.truetype("arial.ttf", size=20), fill=(255, 255, 255), align="center", anchor="mm")
        
        # Save the image to a file for debugging purposes
        if saveFile:
            image.save(f"{path}/{str(imageIndex)}.png", format="PNG")
        
        # embed = DiscordEmbed(title="Embed Title", description="Your Embed Description", color='03b2f8')

        if uploadToDiscord:
            with open(f"{path}/{str(imageIndex)}.png", "rb") as f:
                webhook.add_file(file=f.read(), filename=f"{str(imageIndex)}.png")
    
    if uploadToDiscord:
        webhook.execute()
    print(f"Done!")
    output = {}
    output["path"] = path
    output["images"] = imagesOutput
    output["total"] = total
    return output
    
# t2i(steps=1, model="andite/anything-v4.0", imgs=2, negPrompt="feet, ugly cat girl", prompt="cute cat girl, holding cat")

# top = tk.Tk()
# top.mainloop()