import json
from multiprocessing import Process, Pipe, current_process, cpu_count
from PipeComm import PipeComm
from CommandTypes import CommandTypes
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

first_run = True


def do_job(conn):
    while True:
        conn.send(PipeComm(CommandTypes.ASK_FOR_WORK))

        while not conn.poll(timeout=1):
            pass

        cmd = conn.recv()
        if cmd.command is CommandTypes.SHUTDOWN:
            #conn.close()
            break  # leave process

        task_input = cmd.data[0]
        task_index = cmd.data[1]

        task_output = fibonacci(task_input)

        #print(f'{task_index}, {task_input}, {task_output}, {current_process().name}')
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
        # tasks_to_accomplish.put((item, index))
        queue.append((item, index))

    parent_connections = []

    # creating processes
    for w in range(number_of_processes):
        # create a pipe for communication
        parent_conn, child_conn = Pipe(duplex=True)
        parent_connections.append(parent_conn)

        p = Process(target=do_job, args=(child_conn,))
        processes.append(p)
        p.start()

    while received_results < len(input_list) or sent_shutdowns < number_of_processes:
        for conn in parent_connections:
            if conn.poll(timeout=1):
                try:
                    received_message = conn.recv()
                    if received_message.command is CommandTypes.ASK_FOR_WORK:
                        if len(queue) > 0:
                            conn.send(PipeComm(CommandTypes.WORK, queue.pop()))
                            #print("send work to " + str(i))
                        else:
                            conn.send(PipeComm(CommandTypes.SHUTDOWN))
                            sent_shutdowns = sent_shutdowns + 1
                            #print("send Shutdown to " + str(i))
                    elif received_message.command is CommandTypes.SEND_RESULT:
                        #print("new Result from " + str(i))
                        results[received_message.data[0]] = received_message.data[1]
                        received_results = received_results + 1
                        #print("post new result")
                except EOFError:
                    #print("shit")
                    continue
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

def lambda_handler(event, context):
    global first_run
    cold_start = True if first_run else False
    first_run = False

    n_list = event.get('n')
    #input_list=[10,10,10,25,4]
    #result = fibo_processes(input_list=n_list, process_count=cpu_count())
    result = fibo_processes(input_list=n_list, process_count=5)

    print(n_list)
    print(result)
    
    logger.info(f'cfg: {context.memory_limit_in_mb}; cold start: {cold_start}; {n_list}: {result}')
    print(f'cpu cores: {cpu_count()}')

    return {
        'statusCode': 200,
        'cold_start': cold_start,
        'inputs': n_list,
        'outputs': result,
    }
