from diffusers import StableDiffusionPipeline
import torch
pipe = StableDiffusionPipeline.from_pretrained("andite/anything-v4.0", torch_dtype=torch.float16)
pipe = pipe.to("cuda")
pipe.safety_checker = lambda images, clip_input: (images, False)
if False:
    pipe.enable_attention_slicing()

def progress_function(step: int, timestep: int, latents: torch.FloatTensor):
    # Calculate the progress as a percentage
    progress = (step) 

    # Update the progress bar
    if progress%2 == 1: print(f"Progress: {progress}")

print()