import logging
import azure.functions as func
import json
import psutil

from concurrent.futures import \
    ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count

logger = logging.getLogger()
logger.setLevel(logging.INFO)


first_run = True


def get_available_memory():
    a = psutil.virtual_memory()
    return a.total/(1024*1024)


# task that is performed in parallel
def task(item, index):
    return fibonacci(n=item), index


# multi-threading function
def fibonacci_multithreads(list_of_items):
    if len(list_of_items) == 0:
        return 0

    all_tasks = []

    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        for item_index in range(len(list_of_items)):
            all_tasks.append(
                executor.submit(
                    task,
                    list_of_items[item_index],
                    item_index))

            temp_res = list(range(len(list_of_items)))

            # process completed tasks
            for future in as_completed(all_tasks):
                n_th, index = future.result()
                temp_res[index] = n_th

        return temp_res


def fibonacci(n: int) -> int:
    if type(n) is not int or n == 0:
        raise TypeError('n must be an integer greater than 0 (zero)')

    if n <= 2:
        return 1

    return fibonacci(n=n-1) + fibonacci(n=n-2)


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

    results = fibonacci_multithreads(list_of_items=n_list)

    #logger.info(f'cfg: {context.memory_limit_in_mb}; cold start: {cold_start}; {n_list}: {results}')
    #print(f'cpu cores: {cpu_count()}')
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
