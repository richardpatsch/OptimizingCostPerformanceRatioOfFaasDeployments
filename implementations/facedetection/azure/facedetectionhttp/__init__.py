import logging
import azure.functions as func
import numpy as np
import psutil
import cv2
import json

from multiprocessing import cpu_count
from azure.storage.blob import BlobServiceClient

face_cascade = cv2.CascadeClassifier(
    'facedetectionhttp/haarcascade_frontalface_default.xml')
output_folder = 'outputs/'
input_folder = 'inputs/'

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


def get_blob_bytes(filename):
    STORAGEACCOUNTURL = "<storageurl>"
    STORAGEACCOUNTKEY = "<accountkey>"
    CONTAINERNAME = "inputs"
    BLOBNAME = filename

    try:
        blob_service_client_instance = BlobServiceClient(
            account_url=STORAGEACCOUNTURL, credential=STORAGEACCOUNTKEY)

        blob_client_instance = blob_service_client_instance.get_blob_client(
            CONTAINERNAME, BLOBNAME, snapshot=None)

        blob_data = blob_client_instance.download_blob()
        data = blob_data.readall()
        return data
    except:
        raise Exception(
            f'error while getting file: {CONTAINERNAME}/{BLOBNAME}')


def main(req: func.HttpRequest, context: func.Context, outblob: func.Out[bytes]) -> func.HttpResponse:
    global first_run
    cold_start = True if first_run else False
    first_run = False
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('blobname')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('blobname')

    if name:
        try:
            image_bytes = get_blob_bytes(filename=name)
            arr = blob_to_array(image_bytes)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            new_img = blur_faces(img)
            is_success, im_buf_arr = cv2.imencode(".jpg", new_img)
            byte_im = im_buf_arr.tobytes()
            outblob.set(byte_im)

            memory = get_available_memory()

            logging.info(
                f'memory: {memory}; cpu_cores: {cpu_count()}; cold start: {cold_start}; invocation id: {context.invocation_id}')

            return func.HttpResponse(
                json.dumps({
                    'cold_start': cold_start,
                    'memory': memory,
                    'filename': name,
                    'invocation_id': context.invocation_id,
                    'statusCode': 200
                })
            )
        except:
            return func.HttpResponse(
                json.dumps({
                    'error': 'error'
                })
            )
    else:
        return func.HttpResponse(
            json.dumps({
                'cold_start': cold_start,
                'error': 'Pass a blobname in the query to make trigger a face detection',
                'statusCode': 200
            })
        )
