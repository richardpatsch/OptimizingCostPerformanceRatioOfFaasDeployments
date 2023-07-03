import logging
import azure.functions as func
import os
import json
import psutil
from multiprocessing import cpu_count
from azure.storage.blob import BlobServiceClient
import tempfile
from pydub import AudioSegment
from io import BytesIO


logger = logging.getLogger()
logger.setLevel(logging.INFO)
first_run = True


def get_available_memory():
    a = psutil.virtual_memory()
    return a.total/(1024*1024)


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    global first_run
    cold_start = True if first_run else False
    first_run = False

    req_body = req.get_json()
    key = req_body.get('key')
    reference = req_body.get('reference')

    uncensored_bytes = BytesIO(get_storage_file(key))
    speech = AudioSegment.from_wav(uncensored_bytes)
    output = BytesIO()
    speech = speech.set_frame_rate(5000)
    speech = speech.set_sample_width(1)
    speech.export(output, format="wav")

    clean_name = key.replace('.wav', '')
    new_key = f'{clean_name}_compressed.wav'
    write_storage_file(output.getvalue(), new_key)

    memory = get_available_memory()
    logger.info(
        f'memory: {memory}; cpu_cores: {cpu_count()}; cold start: {cold_start}; invocation id: {context.invocation_id}')

    return func.HttpResponse(
        json.dumps({
            'key': new_key,
            'reference': reference,
            'cold_start': cold_start,
            'memory': memory,
            'invocation_id': context.invocation_id
        })
    )


STORAGEACCOUNTURL = "<account>"
STORAGEACCOUNTKEY = "<key>"
CONTAINERNAME = "data"


def get_storage_file(filename):
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


# input is .getvalue()
def write_storage_file(bytedata, filename):
    BLOBNAME = filename

    try:
        blob_service_client_instance = BlobServiceClient(
            account_url=STORAGEACCOUNTURL, credential=STORAGEACCOUNTKEY)

        blob_client_instance = blob_service_client_instance.get_blob_client(
            CONTAINERNAME, BLOBNAME, snapshot=None)

        # Create a file in the local data directory to upload and download

        upload_file_path = os.path.join(tempfile.gettempdir(), filename)
        print(upload_file_path)

        with open(upload_file_path, 'wb') as data:
            data.write(bytedata)

            with open(file=upload_file_path, mode="rb") as data:
                blob_client_instance.upload_blob(data, overwrite=True)
                print("\nUploading to Azure Storage as blob:\n\t" + filename)

                return True

        return False
    except:
        raise Exception(
            f'error while writing file: {CONTAINERNAME}/{BLOBNAME}')
