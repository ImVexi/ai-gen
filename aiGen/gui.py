import tkinter as tk
from PIL import ImageTk, Image
import local
import threading
from io import BytesIO
import win32clipboard

##############
#   CONFIG   #
##############

webhookURL = "https://discord.com/api/webhooks/1088669801897013339/abPnI5ZSMEIZh70yYYwDGsMK1Nt3_5MTZPFhUxMLOWoRQnMjEoSALxtCa7vgl7mCfSbd"
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

local.config(cpuModei=cpuMode,uploadToDiscordi=uploadToDiscord, uploadi=upload,saveFilei=saveFile,copyrighti=copyright)

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

def progress_function(step, timestep, latents):
    if step and isinstance(step, int):
        None
        # print(step/currentStep*100) broke as heck

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
    output = local.t2i(prompt=prompt, negPrompt=negPrompt, height=height, width=width, steps=steps, imgs=imgCount, model="andite/anything-v4.0", progress=progress_function)
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

row = 0
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
imgElm.grid(row = 0, column = 2, columnspan = 2, rowspan = row, padx = 2, pady = 2)

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
    win32clipboard.OpenClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

# button widget
b1 = tk.Button(root, command=backImg, text = "Back")
b2 = tk.Button(root, command=nextImg, text = "Next")
c = tk.Button(root, command=copy, text="Copy")

# arranging button widgets
b1.grid(row = row, column = 2, sticky = tk.E)
b2.grid(row = row, column = 3, sticky = tk.W)
c.grid(row = row, column= 3, sticky=tk.E)

# Configs
cpuB = tk.Button(root, text=f"Toggle CPU Mode: {local.cpuMode}", command=lambda: toggle_attribute_value(local, 'cpuMode', cpuB))
uploadB = tk.Button(root, text=f"Upload: {local.upload}", command=lambda: toggle_attribute_value(local, 'upload', uploadB))
uploadDB = tk.Button(root, text=f"Upload Discord: {local.uploadToDiscord}", command=lambda: toggle_attribute_value(local, 'uploadToDiscord', uploadDB))
saveB = tk.Button(root, text=f"Save file: {local.saveFile}", command=lambda: toggle_attribute_value(local, 'saveFile', saveB))
copyrightB = tk.Button(root, text=f"Copyright (pls leave on? :( )): {local.copyright}", command=lambda: toggle_attribute_value(local, 'copyright', copyrightB))

def toggle_attribute_value(obj, attribute_name, button):
    value = getattr(obj, attribute_name)
    setattr(obj, attribute_name, not value)
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