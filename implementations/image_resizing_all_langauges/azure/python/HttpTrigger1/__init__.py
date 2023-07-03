import os
import io
import json
import azure.functions as func
from timeit import default_timer as timer
import logging
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

first_run = True

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    global first_run
    cold_start = True if first_run else False
    first_run = False
    
    req_body = req.get_json()
    connection_string = req_body.get('connectionString')
    container_name = req_body.get('containerName')
    blob_name = req_body.get('blobName')

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Get the original image
    blob_client = blob_service_client.get_blob_client(
        container_name, blob_name)
    file_byte_string = blob_client.download_blob().readall()

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

        log_message = {'KeyName': blob_name, 'Memory': int(0), 'ImageTime': time_diff, 'Language': 'python',
                'RequestId': context.invocation_id, 'ColdStart': cold_start}
        
        logging.info(json.dumps(log_message))
        # Write resized image back to Blob
        blob_client = blob_service_client.get_blob_client(
            container_name, "resized/python_" + blob_name)
        blob_client.upload_blob(output, blob_type="BlockBlob", overwrite=True)

    return func.HttpResponse(
        json.dumps({
            "status_code": 200,
            "message": f"Image {blob_name} in container {container_name} resized successfully!",
            "cold_start": cold_start
        })
    )
