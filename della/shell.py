from os import PathLike
from signal import signal
from signal import SIGINT

from prompt_toolkit import print_formatted_text
from prompt_toolkit import prompt
from prompt_toolkit import PromptSession


from tasks import TaskNode
from dateparse import DateParser
from cli_api import * 

 



class Shell:
    def __init__(self, filepath: PathLike | str, prompt_str: str = "@>") -> None:

        # associate the interrupt signal (e.g. ctrl-c) with the _interrupt method
        # this means ctrl-c interrupts can trigger save to file
        # and aren't caught as exceptions

        signal(SIGINT, self._interrupt)
        self.session = PromptSession(prompt_str)


        self.filepath = filepath
        self.task_manager = TaskManager(filepath)

    def __enter__(self):
        return self

    def write_to_file(self):
        self.task_manager.write_to_file(self.filepath)

    def load_from_file(self):
        self.task_manager.load_from_file(self.filepath)

    def _interrupt(self, signal_received, frame):

        self.write_to_file()

        self.__exit__(None, None, None)
        exit(0)

    def get_input(self) -> str:

        try:
            return self.session.prompt()

        except Exception:
            pass

        return "s"

    def __exit__(self, exit_type, exit_value, extit_tb, sep="\n"):
        pass


with Shell("~/Code") as s:
    pass
