import click, prompt_toolkit

from task_utils import *
from prompt_toolkit import print_formatted_text as printformat
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.completion import NestedCompleter


class UserInput:
    pass


class TaskShell:
    def __init__(
        self,
        planner: Planner,
        session: prompt_toolkit.PromptSession | None = None,
        prompt_start: str = "@",
        prompt_end: str = ">",
    ) -> None:


        self.active_project:Project|None = None
        self.project_path: list[str] = []

        self.session = (
            session if session is not None else prompt_toolkit.PromptSession()
        )

    def parse(self):
        pass

    def set_project(self, path: str | list):
        
        if isinstance(path, str):
            path = path.split("/")
        self.project_path = path


    def get_message(self):
        # -> (Project, str)
        pass


def make_shell_parser(prompt_text="@> ", prompt_format="#1C8E40"):

    formatted_prompt = FormattedText([(prompt_format, prompt_text)])

    session = prompt_toolkit.PromptSession(message=formatted_prompt)

    completer = NestedCompleter.from_nested_dict({})

    quit_commands = ("q", "quit", "exit")

    while not (user_input := session.prompt(completer=completer)) in quit_commands:
        yield (user_input)

    return None


def run_shell(prompt_text="@> ", prompt_format="#1C8E40"):
    parser = make_shell_parser(prompt_text=prompt_text, prompt_format=prompt_format)

    for command in parser:
        printformat(command)
