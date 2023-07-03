
'''Lambda Fibonacci code'''
from typing import (
    Dict,
)
import fibonacci
import constants as c
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

    n = event.get('n', c.DEFAULT_FIBONACCI_N)

    n_th = fibonacci.calculate(n=n)
    
    logger.info(f'cfg: {context.memory_limit_in_mb}; cold start: {cold_start}; {n}: {n_th}')
    print(f'cpu cores: {cpu_count()}')
    

    return {
        'cold_start': cold_start,
        'n': n,
        'n_th': n_th,
        'remaining_time': context.get_remaining_time_in_millis(),
    }


if __name__ == '__main__':
    event = {
        'n': 100,
    }

    response = handler(event=event, context={})

    print(response)