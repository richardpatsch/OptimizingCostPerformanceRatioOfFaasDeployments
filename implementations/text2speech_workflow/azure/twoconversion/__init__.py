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


def customConvert(input, output):
    if os.path.exists(output):
        os.remove(output)

    import subprocess
    args = ("./ffmpeg", "-i", f'{input}',  f'{output}')
    # Or just:
    # args = "bin/bar -c somefile.xml -d text.txt -r aString -f anotherString".split()
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    o = popen.stdout.read()
    print(o)


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    global first_run
    cold_start = True if first_run else False
    first_run = False

    req_body = req.get_json()
    message = req_body.get('message')
    reference = req_body.get('reference')
    key = req_body.get('key')

    logger.info(os.listdir())

    logger.info(f'{message}, {reference}, {key}')

    input_file_path = f'{tempfile.gettempdir()}/{key}'
    new_name = key.replace('.mp3', '.wav')
    output_file_path = f'{tempfile.gettempdir()}/{new_name}'

    logger.info("STEP 1")
    get_storage_file_write(key, input_file_path)
    logger.info("STEP 2")
    customConvert(input_file_path, output_file_path)
    logger.info("STEP 3")
    upload_file(output_file_path, new_name)

    # mp3_input = BytesIO(get_storage_file(key))
    # speech = AudioSegment.from_mp3(mp3_input)

    # output = BytesIO()
    # speech.export(output, format='wav')

    # logger.info(len(mp3_input.getvalue()))
    # logger.info(len(output.getvalue()))
    # logger.info(new_name)

    # write_storage_file(output.getvalue(), new_name)

    memory = get_available_memory()
    logger.info(
        f'memory: {memory}; cpu_cores: {cpu_count()}; cold start: {cold_start}; invocation id: {context.invocation_id}')

    return func.HttpResponse(
        json.dumps({
            'message': message,
            'key': new_name,
            'reference': reference,
            'cold_start': cold_start,
            'memory': memory,
            'invocation_id': context.invocation_id
        })
    )


STORAGEACCOUNTURL = "<accounturl>"
STORAGEACCOUNTKEY = "<key>"
CONTAINERNAME = "data"

5


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


def get_storage_file_write(filename, write_to):
    if os.path.exists(filename):
        os.remove(filename)

    BLOBNAME = filename

    try:
        blob_service_client_instance = BlobServiceClient(
            account_url=STORAGEACCOUNTURL, credential=STORAGEACCOUNTKEY)

        blob_client_instance = blob_service_client_instance.get_blob_client(
            CONTAINERNAME, BLOBNAME, snapshot=None)

        blob_data = blob_client_instance.download_blob()
        data = blob_data.readall()

        logger.info(write_to)
        with open(write_to, 'wb') as d:
            d.write(data)

        return data
    except:
        raise Exception(
            f'error while getting file: {CONTAINERNAME}/{BLOBNAME}')


def upload_file(full_path, key):
    BLOBNAME = key

    try:
        blob_service_client_instance = BlobServiceClient(
            account_url=STORAGEACCOUNTURL, credential=STORAGEACCOUNTKEY)

        blob_client_instance = blob_service_client_instance.get_blob_client(
            CONTAINERNAME, BLOBNAME, snapshot=None)

        with open(file=full_path, mode="rb") as data:
            blob_client_instance.upload_blob(data, overwrite=True)
            print("\nUploading to Azure Storage as blob:\n\t" + key)

            return True
    except:
        raise Exception(
            f'error while writing file: {CONTAINERNAME}/{BLOBNAME}')

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
        logger.info(upload_file_path)

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
