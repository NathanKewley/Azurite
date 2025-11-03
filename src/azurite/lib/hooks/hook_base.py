from azurite.lib.subproc import Subproc

class HookBase():

    def __init__(self, logger, hook_arguments):
        self._logger = logger
        self._arguments = hook_arguments
        self._subproc = Subproc()

    def execute_hook(self):
        raise NotImplementedError()
