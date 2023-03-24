import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
import ai
import threading
from io import BytesIO
# import win32clipboard

##############
#   CONFIG   #
##############

webhookURL = "https://discord.com/api/webhooks/1088824131761491989/8stLgAVgvyIqZhvv4LbcXaGQU4m6zjxvMsiCCctCDkB8tJ_fAAPC4XRLmcCa2Jw3lH3w"
cpuMode = True
uploadToDiscord = True
upload = True
saveFile = True
copyright = True

default_prompt = "Doge"
default_negPrompt = "ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, blurry, bad anatomy, blurred, watermark, grainy, signature, cut off, draft, purple dots"
default_steps = 50
default_imgs = 1
default_height = 512
default_width = 512

##############
#   CONFIG   #
##############

ai.config["isJobMode"] = False
ai.config['cpuMode'] = cpuMode
ai.config['uploadToDiscord'] = uploadToDiscord
ai.config['upload'] = upload
ai.config['saveFile'] = saveFile
ai.config['copyright'] = copyright
ai.webhookURL = webhookURL

# ai.config(cpuModei=cpuMode,uploadToDiscordi=uploadToDiscord, uploadi=upload,saveFilei=saveFile,copyrighti=copyright)

root = tk.Tk()
root.title("AI")
promptBox = tk.Entry(root)
negBox = tk.Entry(root)
imgsBox = tk.Entry(root)
stepsBox = tk.Entry(root)
heightBox = tk.Entry(root)
widthBox = tk.Entry(root)

promptBox.insert(0, default_prompt)
negBox.insert(0, default_negPrompt)
stepsBox.insert(0, default_steps)
imgsBox.insert(0, default_imgs)
heightBox.insert(0, default_height)
widthBox.insert(0, default_width)

imgs = None
currentStep = None
working = False

lock = threading.Lock()

pb = ttk.Progressbar(
    root,
    orient='horizontal',
    length=300
)
pb.grid(column=0, row=0, columnspan=3, sticky = tk.E)
pt = tk.Label(root, text="Waiting...")
pt.grid(column=4, row=0,sticky = tk.W)

def progress_function(step: int, *args):
    global currentStep
    with lock:
        if step and isinstance(step, int):
            progress = step / currentStep * 100
            print(f"Progress: {progress}%")
            pb.configure(value=progress)
            pt.configure(text=f"Progress: {progress}%")

# Threading
def makeAI_T():
    global working
    global imgs
    global currentImg
    global currentStep
    working = True
    
    prompt = promptBox.get()
    negPrompt = negBox.get()
    steps = stepsBox.get()
    imgCount = imgsBox.get()
    width = widthBox.get()
    height = heightBox.get()
    currentStep = int(steps)
    print(prompt, negPrompt, steps, width, height)
    progress_function(0)
    output = ai.t2i(prompt=prompt, negPrompt=negPrompt, height=height, width=width, steps=steps, imgs=imgCount, model="andite/anything-v4.0", progress=progress_function)
    print(output)
    imgs = output["images"]
    currentImg=0
    index.configure(text=f"Index: {currentImg+1} Max: {len(imgs)}")
    
    img = ImageTk.PhotoImage(imgs[currentImg]) # tk.PhotoImage(ImageTk.PhotoImage(imgs[currentImg])).subsample(1, 1)
    imgElm.configure(image=img)
    imgElm.image = img
    working = False
    
def makeAI():
    if not working:
        t = threading.Thread(target=makeAI_T)
        t.start()
    else:
        tk.messagebox.showwarning(title="Error", message="There is a job running!")


row = 1
tk.Label(root, text="Prompt").grid(row = row, column = 0, sticky = tk.W, pady = 2)
promptBox.grid(row = row, column = 1, pady = 2)
row+=1

tk.Label(root, text="NegPrompt").grid(row = row, column = 0, sticky = tk.W, pady = 2)
negBox.grid(row =row, column = 1, sticky = tk.W, pady = 2)
row+=1

tk.Label(root, text="Steps").grid(row =row, column = 0, sticky = tk.W, pady = 2)
stepsBox.grid(row = row, column = 1, sticky = tk.W, pady = 2)
row+=1

tk.Label(root, text="Number Of Images").grid(row =row, column = 0, sticky = tk.W, pady = 2)
imgsBox.grid(row = row, column = 1, sticky = tk.W, pady = 2)
row+=1

tk.Label(root, text="Height").grid(row = row, column = 0, sticky = tk.W, pady = 2)
heightBox.grid(row = row, column = 1, sticky = tk.W, pady = 2)
row+=1

tk.Label(root, text="Width").grid(row = row, column = 0, sticky = tk.W, pady = 2)
widthBox.grid(row =row, column = 1, sticky = tk.W, pady = 2)
row+=1

make = tk.Button(root, text="GO!", command=makeAI)
make.grid(row = row, column = 0, pady = 2)

img = tk.PhotoImage(file = r"0.png").subsample(1, 1)

# setting image with the help of label
imgElm = tk.Label(root, image = img)
imgElm.grid(row = 2, column = 2, columnspan = 10, rowspan = 10, padx = 2, pady = 2)

currentImg = 0

index = tk.Label(root, text=f"Index: {currentImg} Max: N/A")
index.grid(row = row, column = 1, sticky = tk.W, pady = 2)

def backImg():
    global imgs
    global currentImg
    currentImg += -1
    print("Back")
    index.configure(text=f"Index: {currentImg+1} Max: {len(imgs)}")
    
    img = ImageTk.PhotoImage(imgs[currentImg]) # tk.PhotoImage(ImageTk.PhotoImage(imgs[currentImg])).subsample(1, 1)
    imgElm.configure(image=img)
    imgElm.image = img

def nextImg():
    global imgs
    global currentImg
    currentImg += 1
    print("Next")
    index.configure(text=f"Index: {currentImg+1} Max: {len(imgs)}")
    
    img = ImageTk.PhotoImage(imgs[currentImg])
    imgElm.configure(image=img)
    imgElm.image = img

def copy():
    output = BytesIO()
    imgs[currentImg].convert('RGB').save(output, 'BMP')
    data = output.getvalue()[14:]
    output.close()
    #win32clipboard.OpenClipboard()
    #win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    #win32clipboard.CloseClipboard()

# button widget
b1 = tk.Button(root, command=backImg, text = "Back")
b2 = tk.Button(root, command=nextImg, text = "Next")
c = tk.Button(root, command=copy, text="Copy")

# arranging button widgets
b1.grid(row = 1, column = 2, sticky = tk.E)
b2.grid(row = 1, column = 3, sticky = tk.W)
c.grid(row = 1, column= 4, sticky=tk.W)

# Configs
config_values = ai.config
cpuB = tk.Button(root, text=f"Toggle CPU Mode: {config_values['cpuMode']}", command=lambda: toggle_attribute_value('cpuMode', cpuB))
uploadB = tk.Button(root, text=f"Upload: {config_values['upload']}", command=lambda: toggle_attribute_value('upload', uploadB))
uploadDB = tk.Button(root, text=f"Upload Discord: {config_values['uploadToDiscord']}", command=lambda: toggle_attribute_value('uploadToDiscord', uploadDB))
saveB = tk.Button(root, text=f"Save file: {config_values['saveFile']}", command=lambda: toggle_attribute_value('saveFile', saveB))
copyrightB = tk.Button(root, text=f"Copyright (pls leave on? :( )): {config_values['copyright']}", command=lambda: toggle_attribute_value('copyright', copyrightB))

def toggle_attribute_value(attribute_name, button):
    config_values = ai.config
    value = config_values[attribute_name]
    config_values[attribute_name] = not value
    new_text = f"{attribute_name.capitalize()}: {not value}"
    button.configure(text=new_text)





row+=1
cpuB.grid(row = row, column = 0, sticky = tk.E)
uploadB.grid(row = row, column = 1, sticky = tk.E)
row+=1

uploadDB.grid(row = row, column = 0, sticky = tk.E)
saveB.grid(row = row, column = 1, sticky = tk.E)
row+=1

copyrightB.grid(row = row, column = 0, sticky = tk.E)

root.mainloop()
