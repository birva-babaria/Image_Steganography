from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
import speech_recognition as sr
from django.core.files.storage import FileSystemStorage
import numpy as np
from PIL import Image
from pathlib import Path
# Create your views here.
def home(request):
    return render(request,'home.html')

def micro(request):
    if request.method=="GET":
        message = request.GET['record']
        rec = sr.Recognizer()
        with sr.Microphone() as mic:
            print('Please say the message that you want to hide...')
            audio = rec.listen(mic)
            print('Message recorded!')
            message = rec.recognize_google(audio)
        return render(request,"home.html",{'msg':message})

def normalUpload(request):
    if request.method=="POST":
        myfile=request.FILES['myfile']
        message=request.POST['message']
        BASE_DIR = Path(__file__).resolve().parent.parent
        fs=FileSystemStorage()
        filename=fs.save(myfile.name,myfile)
        url=fs.url(filename)
        url1=str(BASE_DIR)+url
        img = Image.open(url1, 'r')
        width, height = img.size
        array = np.array(list(img.getdata()))
        if img.mode == 'RGB':
            n = 3
        elif img.mode == 'RGBA':
            n = 4
        total_pixels = array.size//n
        message += "$ka1b2"
        b_message = ''.join([format(ord(i), "08b") for i in message])
        req_pixels = len(b_message)
        if req_pixels > total_pixels:
            message1="ERROR: Need larger file size"
        else:
            index=0
            for p in range(total_pixels):
                for q in range(0, 3):
                    if index < req_pixels:
                        array[p][q] = int(bin(array[p][q])[2:9] + b_message[index], 2)
                        index += 1

            array=array.reshape(height, width, n)
            enc_img = Image.fromarray(array.astype('uint8'), img.mode)
            enc_img.save(str(BASE_DIR)+url)
            message1="Image Encoded Successfully"
            return render(request,"download.html",{'url':filename,'message':message,'message1':message1})
    