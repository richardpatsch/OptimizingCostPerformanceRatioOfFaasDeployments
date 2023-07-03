import json
import base64
import os
import boto3

from pydub import AudioSegment
from io import BytesIO

s3 = boto3.resource(u's3')

def lambda_handler(event, context):
    bucket_name = event.get('s3Bucket')
    s3_key = event.get('s3Key')
    reference = event.get('reference')
    print({'data': {'reference': reference, 'id': f'{context.aws_request_id}'}})


    uncensored_bytes = file_from_s3(bucket_name, s3_key)
    speech = AudioSegment.from_wav(uncensored_bytes)
    output = BytesIO()
    speech = speech.set_frame_rate(5000)
    speech = speech.set_sample_width(1)
    speech.export(output, format="wav")
    
    clean_name = s3_key.replace('.wav', '')
    new_key = f'{clean_name}_compressed.wav'
    upload_file(output.getvalue(), bucket_name, new_key)

    return {
        'statusCode': 200,
        's3Bucket': bucket_name,
        's3Key': new_key,
        'reference': reference
    }

def file_from_s3(bucket_name, key):
    local_path = f'/tmp/{key}'
    bucket = s3.Bucket(bucket_name)
    print(bucket_name)
    print(key)
    bucket.download_file(key, local_path)
    
    #read file and convert
    with open(local_path, "rb") as fh:
        filebytes = BytesIO(fh.read())   
        return filebytes
        
    
def upload_file(byte_object, bucket_name, key):
    local_path = f'/tmp/{key}'
    with open(local_path, "wb") as f:
        f.write(byte_object)
    
    bucket = s3.Bucket(bucket_name)
    bucket.upload_file(local_path, key)