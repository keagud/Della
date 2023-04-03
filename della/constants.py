from pathlib import Path
from typing import Final

import toml

from .default_config import DEFAULT_CONFIG_TEXT


def resolve_path(path_str: str) -> Path:
    return Path(path_str).expanduser().resolve()


REMOTE_PATH: Final = resolve_path("~/della/tasks.toml")
CONFIG_PATH: Final = resolve_path("~/.config/della/config.toml")

TMP_SYNCFILE: Final = "tmp_tasks.toml"


_commands = {
    "list": ["ls"],
    "delete": [
        "del",
        "rm",
    ],
    "set": ["cd"],
    "home": ["root"],
    "quit": ["q", "exit"],
    "move": ["mv"],
    "help": ["h"],
}


COMMAND_ALIASES: Final = {
    command: frozenset(aliases + [command]) for command, aliases in _commands.items()
}

DEFAULT_START_MESSAGE = """
Type <ansiblue>@help</ansiblue> to see the command list
"""


DEFAULT_CONFIG: Final = toml.loads(DEFAULT_CONFIG_TEXT)


with open("defcon.toml", "w") as outfile:
    toml.dump(DEFAULT_CONFIG, outfile)


HELP_MESSAGE = """
To add a task, just type it into the prompt:
    get apples at the store <ansired>wednesday</ansired>

If the task content includes a literal date you don't want to include as the due date,
escape it with a '\\'

To target a specific task for a command, prefix it with '#'. 
You can also target its subtasks this way, e.g. <ansiyellow>#foo/bar/baz</ansiyellow>
But you can also just target the subtask directly, e.g. <ansiyellow>#baz</ansiyellow>
If the task pointed to is ambiguous, you will be prompted to clarify.

Commands:
    <ansiblue>@set, @cd</ansiblue> <ansiyellow>#task</ansiyellow>
        Set a task as the current working project. 
        Any new tasks added will use this task as its parent,
        unless specified otherwise. 

    <ansiblue>@home, @root</ansiblue>
        Reset the current working project to the root.
        
    <ansiblue>@list, @ls</ansiblue>  <ansiyellow>[ #task ]</ansiyellow>
        List the tasks in the current project, or the specified task if given.
        
    <ansiblue>@delete, @del, @rm</ansiblue> <ansiyellow>#task</ansiyellow>
        Remove the specified task.

    <ansiblue>@move, @mv</ansiblue> <ansiyellow>#task</ansiyellow>
        Move a task and all its subtasks to a new parent. 
        This will prompt a second time for the new parent.

    <ansiblue>@quit, @q, @exit</ansiblue>
        Exit Della. 
        Your tasks are saved automatically, and synced to a remote server if configured.

    <ansiblue>@help</ansiblue>
        Prints this message. 
"""
