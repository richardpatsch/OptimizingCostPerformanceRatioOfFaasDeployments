import logging
import azure.functions as func
import json
import psutil

from multiprocessing import Process, Pipe, cpu_count
from enum import Enum


logger = logging.getLogger()
logger.setLevel(logging.INFO)

first_run = True
TIMEOUT = 1


class CommandTypes(Enum):
    ASK_FOR_WORK = 'get_work'
    WORK = 'send_work'
    SEND_RESULT = 'send_result'
    SHUTDOWN = 'shutdown'


class PipeComm(object):
    def __init__(self, command: CommandTypes, data=None):
        self.command = command
        self.data = data


class ProcessInstance(object):
    def __init__(self, id):
        self.parent_connection, self.child_connection = Pipe(duplex=True)
        self.status = 'OPEN'
        self.id = id

    def close(self):
        self.status = 'CLOSED'
        self.parent_connection.close()


def get_available_memory():
    a = psutil.virtual_memory()
    return a.total/(1024*1024)


def do_job(conn):
    while True:
        while not conn.poll(timeout=0.2):
            pass

        cmd = conn.recv()

        if cmd.command is CommandTypes.SHUTDOWN:
            break  # leave process

        task_input = cmd.data[0]
        task_index = cmd.data[1]

        task_output = fibonacci(task_input)
        #print(task_index)

        # print(f'{task_index}, {task_input}, {task_output}, {current_process().name}')
        conn.send(PipeComm(CommandTypes.SEND_RESULT, (task_index, task_output)))

    return True


def fibo_processes(input_list, process_count):
    number_of_processes = process_count
    queue = []
    processes = []
    results = [None] * len(input_list)
    sent_shutdowns = 0
    received_results = 0

    for index, item in enumerate(input_list):
        queue.append((item, index))

    all_processes = []

    # creating processes
    for w in range(number_of_processes):
        pi = ProcessInstance(id=len(all_processes))
        all_processes.append(pi)
        p = Process(target=do_job, args=(pi.child_connection,))
        processes.append(p)
        p.start()

    # send initial work sets
    for pi in all_processes:
        if len(queue) > 0:
            pi.parent_connection.send(PipeComm(CommandTypes.WORK, queue.pop()))

    # deal with running processes and remaining work loads
    while received_results < len(input_list) or sent_shutdowns < number_of_processes:
        for pi in all_processes:
            if pi.status == 'OPEN':
                if pi.parent_connection.poll():
                    received_message = pi.parent_connection.recv()
                    if received_message.command is CommandTypes.SEND_RESULT:
                        results[received_message.data[0]] = received_message.data[1]
                        received_results = received_results + 1
                        if len(queue) > 0:
                            pi.parent_connection.send(PipeComm(CommandTypes.WORK, queue.pop()))
                        else:
                            pi.parent_connection.send(PipeComm(CommandTypes.SHUTDOWN))
                            pi.close()
                            sent_shutdowns = sent_shutdowns + 1

    # completing process
    for p in processes:
        p.join()

    return results


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

    result = fibo_processes(input_list=n_list, process_count=cpu_count())
    #print(n_list)
    #print(result)

    #logger.info(f'cfg: {context.memory_limit_in_mb}; cold start: {cold_start}; {n_list}: {result}')
    #print(f'cpu cores: {cpu_count()}')
    memory = get_available_memory()
    logger.info(f'memory: {memory}; cpu_cores: {cpu_count()}; cold start: {cold_start}; invocation id: {context.invocation_id}')


    return func.HttpResponse(
        json.dumps({
            'statusCode': 200,
            'cold_start': cold_start,
            'inputs': n_list,
            'outputs': result,
            'memory': memory,
            'invocation_id': context.invocation_id
        })
    )
