import cv2
import os
import time
import json
import urllib.parse
import numpy as np
import boto3

print('Loading function')

s3 = boto3.client('s3')
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
output_folder = 'output_images/'
input_folder = 'input_images/'

def blur_faces(img):
    # Convert into grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)
    # Draw rectangle around the faces

    for (x, y, w, h) in faces:
        blurred_part = cv2.blur(img[y:y+h, x: x+w], ksize=(100, 100))
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        # img = cv2.blur(img, (10,10))
        img[y:y+h, x: x+w] = blurred_part

    return img

    
def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        nparr = np.frombuffer(obj['Body'].read(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        new_img = blur_faces(img)
        
        # reimg = cv2.resize(img, (100,100))
        image_string = cv2.imencode('.jpeg', new_img)[1].tostring()
        
        filename = key.replace(input_folder, '').replace('.jpg', '').replace('.jpeg', '')
        
        s3.put_object(Bucket=bucket, Key = f'{output_folder}{filename}.jpg', Body=image_string)

        return { 
            'statusCode': 200,
            'contentType': obj['ContentType'],

        }
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
        
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
