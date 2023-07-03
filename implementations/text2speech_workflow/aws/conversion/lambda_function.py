import json
import base64
import boto3

from pydub import AudioSegment
from io import BytesIO

s3 = boto3.resource(u's3')


def lambda_handler(event, context):
    reference = event.get('reference')

    print({'data': {'reference': reference, 'id': f'{context.aws_request_id}'}})

    original_message = event.get('message')
    bucket_name = event.get('s3Bucket')
    s3_key = event.get('s3Key')
    
    print(s3_key)
    #get mp3 from s3
    local_path =  f'/tmp/{s3_key}'
    bucket = s3.Bucket(bucket_name)
    bucket.download_file(s3_key, local_path)

    #read file and convert
    with open(local_path, "rb") as fh:
        mp3_input = BytesIO(fh.read())   
        
    inputSize = len(mp3_input.getvalue())
    speech = AudioSegment.from_mp3(mp3_input)
    
    output = BytesIO()
    speech.export(output, format='wav')
    new_name = s3_key.replace('.mp3', '.wav')
    
    # Write the stuff
    new_path = f'/tmp/{new_name}'
    with open(new_path, "wb") as f:
        f.write(output.getbuffer())
    
    #upload to s3 again
    bucket.upload_file(new_path, new_name)   # Upload image directly inside bucket
    
    print("Inputfilesize: " + str(inputSize))
    print("Outputfilesize: " + str(len(output.getvalue())))
    
    return {
        'statusCode': 200,
        'message': original_message,
        's3Bucket': bucket_name,
        's3Key': new_name,
        'reference': reference
    }
