import CommandTypes


class PipeComm(object):
    def __init__(self, command: CommandTypes, data=None):
        self.command = command
        self.data = data