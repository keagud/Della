import sys
from itertools import cycle
from pathlib import Path
from shutil import get_terminal_size
from signal import SIGINT, signal
from typing import Optional

from getchoice import ChoicePrinter
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.completion import FuzzyCompleter
from prompt_toolkit.formatted_text import FormattedText

from .command_parser import CommandParser
from .completion import TaskCompleter
from .constants import CONFIG_PATH, TASK_FILE_PATH
from .debugging import debug
from .task import Task


def color_print(message, color, end="\n"):
    print_formatted_text(HTML(f"<{color}>{message}</{color}>"), end=end)


def make_cli_interface(normal_style: str, selected_style: str, title_style: str):
    chooser = ChoicePrinter(
        normal_style=normal_style,
        title_style=title_style,
        selected_style=selected_style,
    )

    def cli_alert(message: str) -> None:
        print_formatted_text(FormattedText([(normal_style, message)]))

    def cli_resolve_task(options: list[Task]) -> Task:
        alert_title = "Multiple matches!"
        " Input the number of the target, or anything else to cancel"

        return chooser.getchoice([(t.path_str, t) for t in options], title=alert_title)


def cli_alert(message: str) -> None:
    color_print(message, "skyblue")


def cli_warn(t: Task, color="red"):
    warn_text = f"Are you sure you want to delete '{t.path_str}'? (y/n)"

    color_print(warn_text, color, end="")

    if t.subtasks:
        subtask_text = (
            f"\nIt has {len(t.subtasks)} subtasks that will also be deleted: "
        )
        color_print(subtask_text, color, end="")

    user_reply = input(" ")

    proceed_delete = user_reply.lower().startswith("y")

    if proceed_delete:
        color_print(f'Deleted "{str(t)}"', "red")

    return proceed_delete


@debug
def cli_resolve(tasks: list[Task], color="red"):
    color_print(
        "Multiple matches! Input the number of the target, or anything else to cancel",
        color,
    )

    for i, t in enumerate(tasks, start=1):
        print(f"{i}. {t.full_path}")

    selection = input()

    selection_int = int(selection) - 1

    if not 0 <= selection_int < len(tasks):
        raise IndexError("Invalid selection")

    return tasks[selection_int]


class CLI_Parser(CommandParser):
    def __init__(
        self,
        filepath: str | Path = TASK_FILE_PATH,
        config_file: str | Path = CONFIG_PATH,
        named_days: Optional[dict[str, str]] = None,
        prompt_display: str = "@=> ",
        prompt_color: str = "skyblue",
    ) -> None:
        super().__init__(
            filepath,
            config_file,
            named_days,
            resolve_func=cli_resolve,
            warn_func=cli_warn,
            alert_func=cli_alert,
        )

        prompt_display = f"<{prompt_color}>{prompt_display}</{prompt_color}>"
        self.session = PromptSession(
            HTML(prompt_display),
            complete_while_typing=True,
            completer=self.update_completions(),
        )
        self.indent = " "

        color_options = [
            "crimson",
            "darkorange",
            "gold",
            "lawngreen",
            "turquoise",
            "skyblue",
            "mediumslateblue",
            "violet",
        ]
        self.colors_iter = cycle(reversed(color_options))

    def update_completions(self):
        task_completer = TaskCompleter.from_tasks(self.manager.root_task)
        self.completer = FuzzyCompleter(task_completer, WORD=False)
        return self.completer

    def format_subtasks(
        self,
        t,
        color=None,
        level=0,
        term_width: Optional[int] = None,
    ):
        if term_width is None:
            term_width, _ = get_terminal_size()
            term_width -= 5
        if color is None:
            color = next(self.colors_iter)

        ls = []

        for index, subtask in enumerate(t.subtasks, start=1):
            formatted_line = []
            content, subtask_summary, display_date = subtask.decompose()

            # TODO properly handle line breaks

            left_content = "".join(
                (
                    f"{self.indent * level}{index}. ",
                    content,
                    f" | {subtask_summary}" if subtask_summary else " ",
                )
            )

            right_padding = term_width - len(left_content)

            formatted_line.append(f"<{color}>")

            formatted_line.append(left_content)

            if display_date:
                formatted_line.append(f"{display_date:>{right_padding}}")

            formatted_line.append(f"</{color}>")

            ls.append("".join(formatted_line))

            if subtask.subtasks:
                recurse_args = {
                    "color": next(self.colors_iter),
                    "term_width": term_width,
                    "level": level + 1,
                }
                ls.extend(self.format_subtasks(subtask, **recurse_args))

        return ls

    def format_tasks(
        self,
        root_task: Optional[Task] = None,
    ) -> list[str]:
        if root_task is None:
            root_task = self.manager.root_task

        if not root_task.subtasks:
            return ["No Tasks"]

        return self.format_subtasks(self.manager.root_task)

    def list(self, root_task: Task | None = None):
        formatted = "\n".join(self.format_tasks(root_task=root_task))
        print_formatted_text(HTML(formatted))

    def prompt(self):
        self.from_prompt(self.session.prompt(completer=self.update_completions()))

    def ___enter__(self, *args, **kwargs):
        signal(SIGINT, self._sigint_handler)
        return super().__enter__()

    def _sigint_handler(self, signal_received, frame):
        self.__exit__(None, None, None)
        sys.exit(0)


def start_cli_prompt(*args, **kwargs):
    with CLI_Parser() as cli_prompt:
        try:
            while True:
                cli_prompt.prompt()

        except KeyboardInterrupt:
            sys.exit(0)

        except EOFError:
            sys.exit(0)
