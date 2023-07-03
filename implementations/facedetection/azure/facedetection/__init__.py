import logging
import cv2
import os
import time
import json
import urllib.parse
import numpy as np
import psutil
import azure.functions as func
from multiprocessing import cpu_count


face_cascade = cv2.CascadeClassifier('facedetection/haarcascade_frontalface_default.xml')
output_folder = 'outputs/'
input_folder = 'inputs/'

DEFAULT_FIBONACCI_N = 10

first_run = True

def get_available_memory():
    a = psutil.virtual_memory()
    return a.total/(1024*1024)


def blob_to_array(blob):
    arr = np.asarray(bytearray(blob), dtype=np.uint8)
    return arr


def blur_faces(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    for (x, y, w, h) in faces:
        blurred_part = cv2.blur(img[y:y+h, x: x+w], ksize=(100, 100))
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        img[y:y+h, x: x+w] = blurred_part

    return img
    

def main(myblob: func.InputStream, context: func.Context, outblob: func.Out[bytes]):
    global first_run
    cold_start = True if first_run else False
    first_run = False
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")
    
    image_bytes = myblob.read()
    arr = blob_to_array(image_bytes)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    new_img = blur_faces(img)

    is_success, im_buf_arr = cv2.imencode(".jpg", new_img)
    byte_im = im_buf_arr.tobytes()

    outblob.set(byte_im)
    
    memory = get_available_memory()

    logging.info(f'memory: {memory}; cpu_cores: {cpu_count()}; cold start: {cold_start}; invocation id: {context.invocation_id}')
