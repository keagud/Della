import click, prompt_toolkit

from task_utils import *
from prompt_toolkit import print_formatted_text as printformat
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.completion import NestedCompleter



def make_shell_parser(prompt_text = "@> ", prompt_format = "#1C8E40"):

    formatted_prompt = FormattedText([(prompt_format, prompt_text)])

    session = prompt_toolkit.PromptSession(message=formatted_prompt)

    completer  = NestedCompleter.from_nested_dict({})

    quit_commands = ("q", "quit", "exit")

    while not (user_input := session.prompt()) in quit_commands:
        yield(user_input)

    return None


def run_shell(prompt_text = "@> ", prompt_format = "#1C8E40"):
    parser = make_shell_parser(prompt_text=prompt_text, prompt_format=prompt_format)

    for command in parser:
        printformat(command)
