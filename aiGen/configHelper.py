import os
import json

def ask(question):
    o = input(f"{question} (Y,N or OTHER): ")
    if o == "Y" or o == "y":
        return True
    elif o == "N" or o == "n":
        return False
    else:
        return o

print("Config Helper loaded!")

cpuMode = ask("CPU Mode")
uploadDiscord = ask("Upload to discord")
discordURL = None
if uploadDiscord:
    discordURL = ask("Discord URL")

copyrightE = ask("Copyright")
copyrightText = None
if copyrightE:
    copyrightText = ask("Copyright text")

saveFile = ask("Save file")

adv = ask("Would you like to see adv options? Such as VEA_TILINGs, and CPU_OFFLOAD?")

tiling = None
cpuOffload = None
slicing = None
attSlic = None

if adv:
    tiling = ask("vae_tiling")
    cpuOffload = ask("sequential_cpu_offload")
    attSlic = ask("attention_slicing")
    slicing = ask("vae_slicing")
    

data = {
    "config":{
        "cpuMode": bool(cpuMode) or False,
        "uploadToDiscord": bool(uploadDiscord) or False,
        "webhook": str(discordURL) or "",
        "upload": False,
        "saveFile": bool(saveFile) or False,
        "copyright": bool(copyrightE) or True,
        "copyrightMsg": str(copyrightText) or "AI IMAGE, ©ai.airplanegobrr.xyz",
    },
    "pipeConfig":{
        "vae_tiling": bool(tiling) or True,
        "sequential_cpu_offload": bool(cpuOffload) or True,
        "attention_slicing": bool(attSlic) or True,
        "vae_slicing": bool(slicing) or True
    }
}
print("\nDoes this look right?")
print(data)
needExit = ask("Save")

if not needExit:
    print("Fail. Rerunning!")
    import configHelper
else:
    print("Writing config.json")
    with open("config.json", "w") as f:
        f.write(json.dumps(data, indent=4))