import json
import os
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from concurrent.futures import \
    ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count

first_run = True

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


def lambda_handler(event, context):
    '''Lambda handler function'''
    global first_run
    cold_start = True if first_run else False
    first_run = False

    n_list = event.get('n')
    results = fibonacci_multithreads(list_of_items=n_list)
    
    logger.info(f'cfg: {context.memory_limit_in_mb}; cold start: {cold_start}; {n_list}: {results}')
    print(f'cpu cores: {cpu_count()}')
    
    return {
        'cold_start': cold_start,
        'inputs': n_list,
        'outputs': results,
    }
