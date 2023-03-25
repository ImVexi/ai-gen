from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, StableDiffusionDepth2ImgPipeline, StableDiffusionUpscalePipeline
from io import BytesIO
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
uploadURL = None  # Not done

working = False


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

class doThing:
    def __init__(self):
        self.pipeConfig = {
            "vae_tiling": True,
            "sequential_cpu_offload": True,
            "attention_slicing": True,
            "vae_slicing": True
        }
        self.config = {
            "cpuMode": False,
            "uploadToDiscord": False,
            "upload": False,
            "saveFile": False,
            "copyright": False,
            "copyrightMsg": "",
            "webhook": None,

            "isJobMode": False
        }
        
        self.currentJob = None
        self.workerID = None
        self.apiURL = "http://192.168.4.50/worker"

    def makeRequest(self, typeIn, batchData=None, jobID=None, updateData=None):

        headers = {'Content-Type': 'application/json'}
        defaultData = {
            "workerID": self.workerID or None,
            "jobID": self.currentJob or None,
            "hwInfo": {
                "user": os.getlogin(),
                "CPU": os.cpu_count()
            }
        }

        if not self.workerID:
            response = requests.post(
                f"{self.apiURL}/add", data=json.dumps(defaultData), headers=headers)
            responseData = response.json()
            if "good" in responseData and "workerID" in responseData:
                self.workerID = responseData["workerID"]
            else:
                print("[Warn] Failed to add worker!")

        match typeIn:
            case "uploadOLD":
                # base64IMG = base64.b64encode(fileData).decode("utf8")
                # defaultData["image"] = base64IMG
                # defaultData["number"] = number
                # response = requests.post(f"{apiURL}/upload", data=json.dumps(defaultData), headers=headers)
                return False
            case "upload":
                defaultData["images"] = batchData
                response = requests.post(
                    f"{self.apiURL}/upload", data=json.dumps(defaultData), headers=headers)
                return True
            case "get":
                # TODO: Make it upload basic data about the worker, EG GPU memery, etc
                response = requests.get(
                    f"{self.apiURL}/get", data=json.dumps(defaultData), headers=headers)
                js = response.json()
                if "good" in js:
                    return js
                else:
                    return None
            case "update":
                defaultData["update"] = updateData
                response = requests.post(
                    f"{self.apiURL}/update", data=json.dumps(defaultData), headers=headers)
            case "getTypes":
                response = requests.get(
                    f"{self.apiURL}/types", data=json.dumps(defaultData), headers=headers)
                # EG ["andite/anything-v4.0","katakana/2D-Mix"]
                return response.json()
    
    def progress_function(self, step: int, timestep: int, latents):
        progress = step

        self.makeRequest("update", jobID=self.currentJob, updateData=progress)

    def createPipe(self, model):
        pipe = None
        if self.config["cpuMode"]:
            # print("CPU")
            pipe = StableDiffusionPipeline.from_pretrained(model)
            pipe = pipe.to("cpu")
        else:
            # print("CUDA")
            import torch
            pipe = StableDiffusionPipeline.from_pretrained(
                model, torch_dtype=torch.float16)
            pipe = pipe.to("cuda")
            # This helps use less VRAM with bigger IMGs, Leave it on
            if self.pipeConfig["vae_tiling"]:
                pipe.enable_vae_tiling()
            if self.pipeConfig["sequential_cpu_offload"]:
                pipe.enable_sequential_cpu_offload()

        # Allows NSFW!!
        pipe.safety_checker = lambda images, clip_input: (images, False)

        if self.pipeConfig["attention_slicing"]:
            pipe.enable_attention_slicing()
        if self.pipeConfig["vae_slicing"]:
            pipe.enable_vae_slicing()
        return pipe

    def t2i(self, steps=50, jobID=None, model=None, prompt="Error", negPrompt="Error", imgs=1, scale=7.5, height=512, width=512, progress=progress_function):
        global apiURL
        global working

        global config

        print(f"Creating model [{model}]")

        warnings.simplefilter("ignore")
        pipe = self.createPipe(model)

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
        if self.config["uploadToDiscord"]:
            webhook = DiscordWebhook(
                url=self.config["webhook"], content=f"Prompt: {prompt}\nNegprompt: {negPrompt}\nTime: {total}")

        path = None

        if self.config["saveFile"]:
            path = "imgs/"+prompt+str(random.randint(-999, 999))
            if not os.path.exists(path):
                os.makedirs(path)

        for imageIndex, image in enumerate(images):
            # Draw the text on the image, might remove
            if self.config["copyright"]:
                ImageDraw.Draw(image).text((image.size[0]/3, 10), self.config["copyrightMsg"], font=ImageFont.truetype(
                    "arial.ttf", size=20), fill=(255, 255, 255), align="center", anchor="mm")
                ImageDraw.Draw(image).text((image.size[0]-180, image.size[1]-10), self.config["copyrightMsg"], font=ImageFont.truetype(
                    "arial.ttf", size=20), fill=(255, 255, 255), align="center", anchor="mm")

            # Save the image to a file for debugging purposes
            with BytesIO() as image_io:
                image.save(image_io, format="PNG")
                image_io.seek(0)
                base64IMG = base64.b64encode(image_io.read()).decode("utf8")

                if self.config["uploadToDiscord"]:
                    image.save(f"{str(imageIndex)}.png", format="PNG")
                    webhook.add_file(
                        file=f"{str(imageIndex)}.png", filename=f"{str(imageIndex)}.png")
                if self.config["saveFile"]:
                    image.save(f"{path}/{str(imageIndex)}.png", format="PNG")

                # Add the encoded image to the batch
                batch[imageIndex] = base64IMG

        if self.config["uploadToDiscord"]:
            webhook.execute()

        if self.config["isJobMode"]:
            self.makeRequest("upload", batchData=batch, jobID=self.currentJob)
            print(f"Submitted [{jobID}]")
        output = {
            "path": path,
            "images": list(images),
            "total": total
        }
        working = False
        return output

    def i2i(self):
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16)

        pipe = pipe.to("cuda")

        url = "https://raw.githubusercontent.com/CompVis/stable-diffusion/main/assets/stable-samples/img2img/sketch-mountains-input.jpg"

        response = requests.get(url)

        init_image = Image.open(BytesIO(response.content)).convert("RGB")

        init_image = init_image.resize((768, 512))

        prompt = "A fantasy landscape, trending on artstation"

        images = pipe(prompt=prompt, image=init_image,
                      strength=0.75, guidance_scale=7.5).images

        images[0].save("fantasy_landscape.png")

    def d2i(self):
        # Prompt + Image
        pipe = StableDiffusionDepth2ImgPipeline.from_pretrained(
            "stabilityai/stable-diffusion-2-depth", torch_dtype=torch.float16,)

        pipe.to("cuda")

        url = "http://images.cocodataset.org/val2017/000000039769.jpg"

        init_image = Image.open(requests.get(url, stream=True).raw)

        prompt = "two tigers"

        n_propmt = "bad, deformed, ugly, bad anotomy"

        image = pipe(prompt=prompt, image=init_image,
                     negative_prompt=n_propmt, strength=0.7).images[0]

    def upscale(self, image=None, prompt=None):
        pipe = StableDiffusionUpscalePipeline.from_pretrained(
            "stabilityai/stable-diffusion-x4-upscaler", revision="fp16", torch_dtype=torch.float16)

        pipe = pipe.to("cuda")

        upscaled_image = pipe(prompt=prompt, image=Image.open(
            BytesIO(image)).convert("RGB").resize((128, 128))).images[0]

        upscaled_image.save("upsampled_cat.png")

    def check(self):
        global working
        print("Checking", working)
        if not working:
            try:
                jsonO = self.makeRequest("get")
                # print(jsonO)
                # print(jsonO["jobID"])
                if jsonO and "jobID" in jsonO:
                    self.currentJob = jsonO["jobID"]
                    working = True  # This shouldn't be needed but there was an issue
                    self.t2i(steps=jsonO["sample"] or 50, jobID=self.currentJob, model=jsonO["model"] or "andite/anything-v4.0",
                        prompt=jsonO["prompt"] or "Error", imgs=jsonO["imgs"] or 1, negPrompt=jsonO["negPrompt"] or "Error")
            except Exception as e:
                print(e)
                working = False
            finally:
                print("Done")


if __name__ == "__main__":
    print("Main!")
    worker = doThing()
    worker.config["isJobMode"] = True
    
    while True:
        worker.check()
        time.sleep(1)

# while True:
    # check()
    # time.sleep(1)
