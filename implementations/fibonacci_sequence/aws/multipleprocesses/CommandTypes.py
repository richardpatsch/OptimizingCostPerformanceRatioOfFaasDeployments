from enum import Enum


class CommandTypes(Enum):
    ASK_FOR_WORK = 'get_work'
    WORK = 'send_work'
    SEND_RESULT = 'send_result'
    SHUTDOWN = 'shutdown'
