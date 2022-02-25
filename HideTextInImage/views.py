from email.errors import MessageError
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import numpy as np
from PIL import Image
from pathlib import Path
from math import log10, sqrt
import cv2

original=''
compressed=''
MEDIA_URL='/media/'

# Create your views here.
def home(request):
    return render(request,'home.html')

def text(request):
    if 'messageError' in request.session:
        del request.session['messageError']
    return render(request,'homeText.html')

def PSNR(original, compressed):
    mse = np.mean((original - compressed) ** 2)
    if(mse == 0):
        return 100
    max_pixel = 255.0
    psnr = 20 * log10(max_pixel / sqrt(mse))
    return psnr

def encode(request):
    if request.method=="POST":
        myfile=request.FILES['myfile']
        message=request.POST['message']
        BASE_DIR = Path(__file__).resolve().parent.parent
        fs=FileSystemStorage()
        filename=fs.save(myfile.name,myfile)
        url=fs.url(filename)
        url1=str(BASE_DIR)+url
        original = cv2.imread(url1)
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
        messageError=''
        if req_pixels > total_pixels:
            messageError="ERROR: Need larger Image size"
            request.session['messageError']=messageError
            return render(request,"homeText.html",{'reqPixel':req_pixels,'totalPixel':total_pixels})
        else:
            index=0
            for p in range(total_pixels):
                for q in range(0, 3):
                    if index < req_pixels:
                        array[p][q] = int(bin(array[p][q])[2:9] + b_message[index], 2)
                        index += 1

            array=array.reshape(height, width, n)
            enc_img = Image.fromarray(array.astype('uint8'), img.mode)
            url2=str(BASE_DIR)+url
            enc_img.save(url2)
            message1="Message Encoded Successfully"
            fname=str(BASE_DIR)+str(MEDIA_URL)+filename
           
            compressed = cv2.imread(fname)
            mse = np.mean((original - compressed) ** 2)
            if(mse == 0):
                psnr = 100
            else:
                max_pixel = 255.0
                psnr = 20 * log10(max_pixel / sqrt(mse))
            return render(request,"encDownload.html",{'url':filename,'message':message,'message1':message1,'PSNR':psnr})

def decode(request):
        if request.method=="POST":
            myfile=request.FILES['myfile']
            BASE_DIR = Path(__file__).resolve().parent.parent
            fs=FileSystemStorage()
            filename=fs.save(myfile.name,myfile)
            url=fs.url(filename)
            url1=str(BASE_DIR)+url
            img = Image.open(url1, 'r')
            array = np.array(list(img.getdata()))
            if img.mode == 'RGB':
                n = 3
            elif img.mode == 'RGBA':
                n = 4
            total_pixels = array.size//n
            hidden_bits = ""
            for p in range(total_pixels):
                for q in range(0, 3):
                    hidden_bits += (bin(array[p][q])[2:][-1])
            hidden_bits = [hidden_bits[i:i+8] for i in range(0, len(hidden_bits), 8)]
            message = ""
            for i in range(len(hidden_bits)):
                if message[-6:] == "$ka1b2":
                    break
                else:
                    message += chr(int(hidden_bits[i], 2))
            msg = ""
            err_msg = ""
            if "$ka1b2" in message:
                msg = message[:-6]
            else:
                err_msg = "No Hidden Message Found"
            return render(request,"decDownload.html",{'msg':msg, 'err_msg': err_msg})