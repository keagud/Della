import sys
from itertools import cycle
from pathlib import Path
from signal import SIGINT, signal
from typing import Optional

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.completion import NestedCompleter

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


class CLI_Parser(CommandParser):
    def __init__(
        self,
        filepath: str | Path = "~/.local/tasks.toml",
        named_days: Optional[dict[str, str]] = None,
        prompt_display: str = "> ",
    ) -> None:
        super().__init__(
            filepath,
            named_days,
            resolve_func=cli_resolve,
            warn_func=cli_warn,
            alert_func=cli_alert,
        )

        self.session = PromptSession(
            prompt_display,
            complete_while_typing=True,
            completer=self.update_completions(),
        )
        self.indent = " "

        color_options = ["red", "orange", "yellow", "green", "blue", "purple"]
        self.colors_iter = cycle(reversed(color_options))

    def make_completions(self, task_node: Optional[Task] = None):
        if task_node is None:
            task_node = self.manager.root_task
        d = {}

        for task in task_node.subtasks:
            content = None

            if task.subtasks:
                content = self.make_completions(task)

            d[task.slug] = content

        return d

    def update_completions(self):
        completions = self.make_completions()
        self.completer = NestedCompleter.from_nested_dict(completions)
        return self.completer

    def format_subtasks(self, t, color=None, level=0):
        if color is None:
            color = next(self.colors_iter)

        ls = []
        for index, subtask in enumerate(t.subtasks, start=1):
            content, subtask_summary, display_date = subtask.decompose()
            formatted = (
                "{front_indent}<{color}>{}.{content:<8s}"
                "{sub_summary:<8s}{date:>8s}</{color}>".format(
                    index,
                    front_indent=self.indent * level,
                    color=color,
                    content=content,
                    date=display_date,
                    sub_summary=subtask_summary,
                )
            )

            ls.append(formatted)

            if subtask.subtasks:
                next_color = next(self.colors_iter)
                ls.extend(
                    self.format_subtasks(subtask, color=next_color, level=level + 1)
                )

        return ls

    def format_tasks(
        self,
        root_task: Optional[Task] = None,
    ) -> list[str]:
        if root_task is None:
            root_task = self.manager.root_task

        if not root_task.subtasks:
            return ["No Tasks"]
        return self.format_subtasks(root_task)

    def list(self, root_task: Task | None = None):
        formatted = "\n".join(self.format_tasks(root_task=root_task))
        print_formatted_text(HTML(formatted))

    def prompt(self):
        self.from_prompt(self.session.prompt(completer=self.update_completions()))

    def __enter__(self, *args, **kwargs):
        signal(SIGINT, self._sigint_handler)
        return cli_enter(self, *args, **kwargs)

    def _sigint_handler(self, signal_received, frame):
        self.__exit__(None, None, None)
        sys.exit(0)

    def __exit__(self, *args, **kwargs):
        return command_exit(self, *args, **kwargs)
