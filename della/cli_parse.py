import sys
from signal import SIGINT, signal

from .command_parser import CommandParser
from .task import Task


def cli_enter(
    self: CommandParser,
    *args,
    **kwargs,
):
    return self


def cli_alert(message: str) -> None:
    print(message)


def cli_warn(t: Task):
    print(f"Are you sure you want to delete '{t.full_path}'? (y/n)", end="")
    if t.subtasks:
        print(f"\nIt has {len(t.subtasks)} subtasks that will also be deleted", end="")

    user_reply = input(" ")

    return user_reply.lower().startswith("y")


def cli_resolve(tasks: list[Task]):
    print(
        "Multiple matches! Input the number of the target, or anything else to cancel"
    )

    for i, t in enumerate(tasks, start=1):
        print(f"{i}. {str(t)}")

    selection = input()

    if not selection.isnumeric():
        return None

    selection_int = int(selection) - 1

    if not 0 <= selection_int < len(tasks):
        print("Invalid selection")
        return None

    return tasks[selection_int]


def command_exit(self: CommandParser, *args, **kwargs):
    with open(self.manager.save_file_path, "w") as taskfile:
        self.manager.serialize(taskfile)

    print(f"Saved to {self.manager.save_file_path}")


def make_cli(filepath: str = "~/.local/della/tasks.toml"):
    class CLI_Parser(CommandParser):
        def __enter__(self, *args, **kwargs):
            signal(SIGINT, self._sigint_handler)
            return cli_enter(self, *args, **kwargs)

        def _sigint_handler(self, signal_received, frame):
            self.__exit__(None, None, None)
            sys.exit(0)

        def __exit__(self, *args, **kwargs):
            return command_exit(self, *args, **kwargs)

    new_parser = CLI_Parser(
        filepath=filepath,
        resolve_func=cli_resolve,
        warn_func=cli_warn,
        alert_func=cli_alert,
    )

    return new_parser
