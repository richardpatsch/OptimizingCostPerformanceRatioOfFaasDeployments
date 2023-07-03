import json
import array
import numpy as np
import os
import base64
import boto3
from pydub import AudioSegment
from io import BytesIO

s3 = boto3.resource(u's3')

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


def lambda_handler(event, context):
    indexes_percent = event.get('indexesPercent')
    print("Length of Input-Indexes: " + str(len(indexes_percent)))
    
    reference = event.get('reference')
    print({'data': {'reference': reference, 'id': f'{context.aws_request_id}'}})


    bucket_name = event.get('s3Bucket')
    s3_key = event.get('s3Key')
    
    uncensored_bytes = file_from_s3(bucket_name, s3_key)
    speech = AudioSegment.from_wav(uncensored_bytes)

    samples = np.array(speech.get_array_of_samples())
    
    print(len(samples))
    
    # we use the inefficient implementation here
    for index, s in enumerate(samples):
        for start, end in indexes_percent:
            #print(start, end)
            start_sample = int((start) * len(samples))
            end_sample = int((end) * len(samples))
            if index > start_sample and index < end_sample:
                samples[index] = 0
                #print("yes!")
    
    
    #samples = np.right_shift(np.array(speech.get_array_of_samples()), 1)
    #shifted_samples_array = array.array(speech.array_type, samples)
    outputfile = BytesIO()
    new_sound = speech._spawn(samples)
    new_sound.export(outputfile, format="wav")
    
    clean_name = s3_key.replace('.wav', '')
    new_key = f'{clean_name}_censored.wav'
    upload_file(outputfile.getvalue(), bucket_name, new_key)

    # print file lengths
    print("Outputfilesize: " + str(len(outputfile.getvalue())))

    # TODO implement
    return {
        'statusCode': 200,
        's3Bucket': bucket_name,
        's3Key': new_key,
        'reference': reference
    }
