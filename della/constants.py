from pathlib import Path
from typing import Final


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
    "home": ["h"],
    "quit": ["q", "exit"],
    "move": ["mv"],
}


COMMAND_ALIASES: Final = {
    command: frozenset(aliases + [command]) for command, aliases in _commands.items()
}


DEFAULT_CONFIG: Final = {
    "local": {"task_file_local": "~/.local/della/tasks.toml"},
    "remote": {"use_remote": False},
    "style": {
        "tasks_display": [{"fg": "cyan"}, {"fg": "green"}, {"fg": "white"}],
        "normal": {"fg": "white"},
        "alert": {"fg": "red", "extra": "bold"},
        "highlight_command": {"fg": "blue", "extra": "italic"},
        "highlight_date": {"fg": "white", "bg": "blue", "extra": "italic"},
        "highlight_task": {"fg": "yellow", "extra": "bold"},
        "choose_title": {"fg": "blue"},
        "choose_selected": {"fg": "green", "extra": "italic underline"},
        "choose_unselected": {"fg": "cyan"},
    },
}
