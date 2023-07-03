import json
import base64
import boto3
from gtts import gTTS
from io import BytesIO

s3 = boto3.resource(u's3')
bucket_name = u'mp3tts1024'
bucket = s3.Bucket(bucket_name)
path_test = '/tmp'

def lambda_handler(event, context):
    # TODO implement
    original_message = event.get('message')
    reference = event.get('reference')
    print({'data': {'reference': reference, 'id': f'{context.aws_request_id}'}})
    #indexes = event.get('indexes')
    
    print(f'original_message: {original_message}')
    print(f'input length: {len(original_message)}')

    
    tts = gTTS(text=original_message, lang='en')
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    result = mp3_fp.getvalue()
    
    key = f'{len(original_message)}.mp3'
    
    final_path = f'{path_test}/{key}'
    
    with open(final_path, 'wb') as data:
        data.write(result)
        bucket.upload_file(final_path, key)   # Upload image directly inside bucket

    #b64_result = base64.b64encode(result)

    print("MessageSize:" + str(len(original_message)))
    print("FileSize:" + str(len(result)))
    
    return {
        'statusCode': 200,
        'message': original_message,
        's3Bucket': bucket_name,
        's3Key': key,
        'reference': reference
    }
