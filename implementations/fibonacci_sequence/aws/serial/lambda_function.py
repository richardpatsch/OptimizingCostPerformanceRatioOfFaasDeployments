'''Lambda Fibonacci code'''
from typing import (
    Dict,
)
import os
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from multiprocessing import cpu_count


first_run = True


def lambda_handler(event: Dict, context: Dict) -> Dict:
    '''Lambda handler function'''
    global first_run


    cold_start = True if first_run else False

    first_run = False

    n_list = event.get('n')

    results = multiple_fib(n_list)
    
    logger.info(f'cfg: {context.memory_limit_in_mb}; cold start: {cold_start}; {n_list}: {results}')
    print(f'cpu cores: {cpu_count()}')
    

    return {
        'cold_start': cold_start,
        'inputs': n_list,
        'outputs': results,
        'remaining_time': context.get_remaining_time_in_millis(),
    }


if __name__ == '__main__':
    event = {
        'n': 100,
    }

    response = handler(event=event, context={})

    print(response)
    
    
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