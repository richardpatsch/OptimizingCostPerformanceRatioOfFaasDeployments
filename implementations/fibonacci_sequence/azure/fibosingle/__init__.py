import logging
import azure.functions as func
import os
import json
import psutil
from multiprocessing import cpu_count

logger = logging.getLogger()
logger.setLevel(logging.INFO)


DEFAULT_FIBONACCI_N = 10

first_run = True

def get_available_memory():
    a = psutil.virtual_memory()
    return a.total/(1024*1024)


def calculate(*, n: int) -> int:
    if type(n) is not int or n == 0:
        raise TypeError('n must be an integer greater than 0 (zero)')

    if n <= 2:
        return 1

    return calculate(n=n-1) + calculate(n=n-2)


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    global first_run
    cold_start = True if first_run else False
    first_run = False
    n = req.params.get('n')
    if not n:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('n')

    if not n:
        return func.HttpResponse(
            json.dumps({
                'error': 'parameter n was not provided'
            })
        )

    n = int(n)  # has to be a number

    n_th = calculate(n=n)
    #logger.info(f'cfg: {context.memory_limit_in_mb}; cold start: {cold_start}; {n}: {n_th}')
    #print(f'cpu cores: {cpu_count()}')
    memory = get_available_memory()
    logger.info(f'memory: {memory}; cpu_cores: {cpu_count()}; cold start: {cold_start}; invocation id: {context.invocation_id}')


    return func.HttpResponse(
        json.dumps({
            'cold_start': cold_start,
            'n': n,
            'n_th': n_th,
            'memory': memory,
            'invocation_id': context.invocation_id
        })
    )
