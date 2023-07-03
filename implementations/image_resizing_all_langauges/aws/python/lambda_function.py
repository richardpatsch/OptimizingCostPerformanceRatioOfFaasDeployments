import boto3
import os
import io
from timeit import default_timer as timer
from PIL import Image


def lambda_handler(event, context):
    s3 = boto3.client('s3')

    s3_bucket = event['s3Bucket']
    s3_key = event['s3Key']

    # Get the original image
    file_byte_string = s3.get_object(Bucket=s3_bucket, Key=s3_key)['Body'].read()

    start = timer()
    # Load image with PIL (Python Imaging Library)
    img = Image.open(io.BytesIO(file_byte_string))

    # Calculate new height to maintain aspect ratio
    base_width = 100
    width_percent = (base_width / float(img.size[0]))
    new_height = int((float(img.size[1]) * float(width_percent)))

    # Resize while maintaining aspect ratio
    img = img.resize((base_width, new_height), Image.ANTIALIAS)

    # Save the resized image to a BytesIO object to return
    with io.BytesIO() as output:
        img.save(output, format='PNG')
        output.seek(0)

        end = timer()
        time_diff = (end - start) * 1000  # to get ms
        memory = os.environ['AWS_LAMBDA_FUNCTION_MEMORY_SIZE']

        log_message = {'KeyName': s3_key, 'Memory': int(memory), 'ImageTime': time_diff, 'Language': 'python',
                       'RequestId': context.aws_request_id}
        print(log_message)

        # Write resized image back to S3
        s3.put_object(Bucket=s3_bucket, Key="resized/python_" + s3_key, Body=output, ContentType='image/png')

    return {
        'statusCode': 200,
        'body': f'Image {s3_key} in bucket {s3_bucket} resized successfully!'
    }
