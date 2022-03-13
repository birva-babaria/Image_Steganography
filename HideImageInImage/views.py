import cv2
from django.http import HttpResponseRedirect
from django.shortcuts import render
from pathlib import Path
from PIL import Image
import numpy as np
from math import log10, sqrt
from django.core.files.storage import FileSystemStorage
# Create your views here.
original=''
compressed=''
MEDIA_URL='/media/'

def image(request):
    if 'messageError1' in request.session:
        del request.session['messageError1']
    if 'decodeError' in request.session:
        del request.session['decodeError']
    return render(request, 'homeImage.html')


def add_leading_zeros(binary_number, expected_length):
    length = len(binary_number)
    return (expected_length - length) * '0' + binary_number


def rgb_to_binary(r, g, b):
    return add_leading_zeros(bin(r)[2:], 8), add_leading_zeros(bin(g)[2:], 8), add_leading_zeros(bin(b)[2:], 8)


def get_binary_pixel_values(img, width, height):
    hidden_image_pixels = ''
    for col in range(width):
        for row in range(height):
            pixel = img[col, row]
            r = pixel[0]
            g = pixel[1]
            b = pixel[2]
            r_binary, g_binary, b_binary = rgb_to_binary(r, g, b)
            hidden_image_pixels += r_binary + g_binary + b_binary
    return hidden_image_pixels


def encode(img_visible, img_hidden):
    encoded_image = img_visible.load()
    img_hidden_copy = img_hidden.load()
    width_visible, height_visible = img_visible.size
    width_hidden, height_hidden = img_hidden.size
    hidden_image_pixels = get_binary_pixel_values(
        img_hidden_copy, width_hidden, height_hidden)
    encoded_image = change_binary_values(
        encoded_image, hidden_image_pixels, width_visible, height_visible, width_hidden, height_hidden)
    return img_visible


def change_binary_values(img_visible, hidden_image_pixels, width_visible, height_visible, width_hidden, height_hidden):
    idx = 0
    for col in range(width_visible):
        for row in range(height_visible):
            if row == 0 and col == 0:
                width_hidden_binary = add_leading_zeros(
                    bin(width_hidden)[2:], 12)
                height_hidden_binary = add_leading_zeros(
                    bin(height_hidden)[2:], 12)
                w_h_binary = width_hidden_binary + height_hidden_binary
                img_visible[col, row] = (int(w_h_binary[0:8], 2), int(
                    w_h_binary[8:16], 2), int(w_h_binary[16:24], 2))
                continue
            r, g, b = img_visible[col, row]
            r_binary, g_binary, b_binary = rgb_to_binary(r, g, b)
            r_binary = r_binary[0:4] + hidden_image_pixels[idx:idx+4]
            g_binary = g_binary[0:4] + hidden_image_pixels[idx+4:idx+8]
            b_binary = b_binary[0:4] + hidden_image_pixels[idx+8:idx+12]
            idx += 12
            img_visible[col, row] = (
                int(r_binary, 2), int(g_binary, 2), int(b_binary, 2))
            if idx >= len(hidden_image_pixels):
                return img_visible
    return img_visible


def encodeImage(request):
    if request.method == "POST":
        imageToHide = request.FILES['imageToHide']
        hideImage = request.FILES['hideImage']
        BASE_DIR = Path(__file__).resolve().parent.parent
        fs = FileSystemStorage()
        filename1 = fs.save(imageToHide.name, imageToHide)
        url_1 = fs.url(filename1)
        url1 = str(BASE_DIR)+url_1
        filename2 = fs.save(hideImage.name, hideImage)
        url_2 = fs.url(filename2)
        url2 = str(BASE_DIR)+url_2
        original=cv2.imread(url2)
        img_visible = Image.open(url2, 'r')

        array = np.array(list(img_visible.getdata()))
        if img_visible.mode == 'RGB':
            n = 3
        elif img_visible.mode == 'RGBA':
            n = 4
        total_pixels = array.size//n
        img_hidden = Image.open(url1, 'r')
        
        array1 = np.array(list(img_hidden.getdata()))
        if img_visible.mode == 'RGB':
            n = 3
        elif img_visible.mode == 'RGBA':
            n = 4
        required_pixels = array1.size//n
        
        if required_pixels >= total_pixels:
            messageError = "ERROR: Need larger image size"
            request.session['messageError1'] = messageError
            return render(request, "homeImage.html",{'reqPixel':required_pixels,'totalPixel':total_pixels})
        else:
            encoded_image = encode(img_visible, img_hidden)
            encoded_image.save(url2)    
            message1 = "Image Encoded Successfully"
            fname=str(BASE_DIR)+str(MEDIA_URL)+filename2
            compressed = cv2.imread(fname)
            mse = np.mean((original - compressed)**2)
            if(mse == 0):
                psnr = 100
            else:
                max_pixel = 255.0
                psnr = 20 * log10(max_pixel / sqrt(mse))
            return render(request, "encImage.html", {'url1': filename1, 'url2': filename2, 'message1': message1,'PSNR':psnr})

def extract_hidden_pixels(image, width_visible, height_visible, pixel_count):
    hidden_image_pixels = ''
    idx = 0
    for col in range(width_visible):
        for row in range(height_visible):
            if row == 0 and col == 0:
                continue
            r, g, b = image[col, row]
            r_binary, g_binary, b_binary = rgb_to_binary(r, g, b)
            hidden_image_pixels += r_binary[4:8] + \
                g_binary[4:8] + b_binary[4:8]
            if idx >= pixel_count * 2:
                return hidden_image_pixels
    return hidden_image_pixels


def reconstruct_image(image_pixels, width, height):
    image = Image.new("RGB", (width, height))
    image_copy = image.load()
    idx = 0
    for col in range(width):
        for row in range(height):
            r_binary = image_pixels[idx:idx+8]
            g_binary = image_pixels[idx+8:idx+16]
            b_binary = image_pixels[idx+16:idx+24]
            image_copy[col, row] = (int(r_binary, 2), int(g_binary, 2), int(b_binary, 2))
            idx += 24
    return image


def decode(image):
    image_copy = image.load()
    width_visible, height_visible = image.size
    r, g, b = image_copy[0, 0]
    r_binary, g_binary, b_binary = rgb_to_binary(r, g, b)
    w_h_binary = r_binary + g_binary + b_binary
    width_hidden = int(w_h_binary[0:12], 2)
    height_hidden = int(w_h_binary[12:24], 2)
    pixel_count = width_hidden * height_hidden
    hidden_image_pixels = extract_hidden_pixels(
        image_copy, width_visible, height_visible, pixel_count)
    decoded_image = reconstruct_image(
        hidden_image_pixels, width_hidden, height_hidden)
    return decoded_image


def decodeImage(request):
    if request.method == "POST":
        try:
            decFile = request.FILES['decFile']
            BASE_DIR = Path(__file__).resolve().parent.parent
            fs = FileSystemStorage()
            filename = fs.save(decFile.name, decFile)
            url = fs.url(filename)
            url1 = str(BASE_DIR)+url
            img = Image.open(url1, 'r')
            decoded_image = decode(img)
            decoded_image.save(url1)
        except:
            request.session['decodeError'] = "Image can't be decoded!"
        return render(request, "decImage.html", {'url': url1})
