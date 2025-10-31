from azurite.lib.hooks.hook_base import HookBase


class Hook(HookBase):


    def __init__(self, logger, arguments):
        super().__init__(logger, arguments)

    def execute_hook(self):
        self._logger.debug(f"Running Python3 Hook: {self._arguments}")
        if not self._subproc.run_command_exit_code(f"python3 {self._arguments}") == 0:
            raise Exception(f"Python Hook Returned non 0 result ({self._arguments})")
