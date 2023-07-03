import logging
import os
import json
import azure.functions as func
import psutil
from multiprocessing import cpu_count

logger = logging.getLogger()
logger.setLevel(logging.INFO)


first_run = True


def get_available_memory():
    a = psutil.virtual_memory()
    return a.total/(1024*1024)


def multiple_fib(list):
    results = []
    for item in list:
        results.append(calculate(n=item))

    return results


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
    n_list = [n] * 12

    results = multiple_fib(n_list)

    #logger.info(f'cfg: {context.memory_limit_in_mb}; cold start: {cold_start}; {n_list}: {results}')
    #print(f'cpu cores: {cpu_count()}')
    #print(f'memory: {get_available_memory()}; cpu_cores: {cpu_count()}; cold start: {cold_start};')
    memory = get_available_memory()
    logger.info(f'memory: {memory}; cpu_cores: {cpu_count()}; cold start: {cold_start}; invocation id: {context.invocation_id}')


    return func.HttpResponse(
        json.dumps({
            'cold_start': cold_start,
            'inputs': n_list,
            'outputs': results,
            'memory': memory,
            'invocation_id': context.invocation_id
        })
    )
