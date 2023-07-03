import logging
import azure.functions as func
import os
import json
import psutil
from multiprocessing import cpu_count
from better_profanity import profanity


profanity.load_censor_words()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
first_run = True


def get_available_memory():
    a = psutil.virtual_memory()
    return a.total/(1024*1024)


def main(req: func.HttpRequest,  context: func.Context) -> func.HttpResponse:
    global first_run
    cold_start = True if first_run else False
    first_run = False

    memory = get_available_memory()
    logger.info(
        f'memory: {memory}; cpu_cores: {cpu_count()}; cold start: {cold_start}; invocation id: {context.invocation_id}')

    req_body = req.get_json()
    message = req_body.get('message')
    reference = req_body.get('reference')

    filtered_message = profanity.censor(message)
    indexes = extract_indexes(filtered_message)
    indexes_percent = extract_indexes_percent(filtered_message)

    return func.HttpResponse(
        json.dumps({
            "originalMessage": message,
            "censoredMessage": filtered_message,
            "indexes": indexes,
            "indexesPercent": indexes_percent,
            "reference": reference,
            'cold_start': cold_start,
            'memory': memory,
            'invocation_id': context.invocation_id
        })
    )


def get_available_memory():
    a = psutil.virtual_memory()
    return a.total/(1024*1024)


def extract_indexes(text, char="*"):
    indexes = []
    in_word = False
    start = 0
    for index, value in enumerate(text):
        if value == char:
            if not in_word:
                # This is the first character, else this is one of many
                in_word = True
                start = index
        else:
            if in_word:
                # This is the first non-character
                in_word = False
                # indexes.append(((start - 1) / len(text), (index) / len(text)))
                indexes.append((start-1, index))

    if in_word:
        # indexes.append(((start - 1) / len(text), (index) / len(text)))
        indexes.append((start-1, index))

    return indexes


def extract_indexes_percent(text, char="*"):
    indexes = []
    in_word = False
    start = 0
    for index, value in enumerate(text):
        if value == char:
            if not in_word:
                # This is the first character, else this is one of many
                in_word = True
                start = index
        else:
            if in_word:
                # This is the first non-character
                in_word = False
                indexes.append(((start - 1) / len(text), (index) / len(text)))
                # indexes.append((start-1, index))

    if in_word:
        indexes.append(((start - 1) / len(text), (index) / len(text)))
        # indexes.append((start-1, index))

    return indexes
