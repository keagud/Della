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
from prompt_toolkit.layout.processors import Processor

from .command_parser import CommandParser, CommandsInterface
from .completion import CommandProcessor, DateProcessor, TaskCompleter, TaskProcessor
from .constants import CONFIG_PATH
from .task import Task, TaskException


def make_cli_interface(normal_style: str, selected_style: str, title_style: str):
    chooser = ChoicePrinter(
        normal_style=normal_style,
        title_style=title_style,
        selected_style=selected_style,
    )

    def cli_alert(message: str, style=normal_style) -> None:
        print_formatted_text(FormattedText([(style, message)]))

    def cli_resolve_task(options: list[Task]) -> Task:
        alert_title = "Multiple matches!"
        " Input the number of the target, or anything else to cancel"

        _, chosen = chooser.getchoice(
            [(t.path_str, t) for t in options], title=alert_title
        )
        return chosen

    def cli_confirm_delete(t: Task) -> bool:
        delete_message = f"Really delete '{t}?'"

        if t.subtasks:
            delete_message += f"\nIt has {len(t.subtasks)} subtasks"

        _, chosen = chooser.getchoice(
            [("yes", True), ("no", False)], title=delete_message
        )
        return chosen

    def cli_resolve_sync() -> bool:
        return True

    return CommandsInterface(
        cli_alert, cli_resolve_task, cli_confirm_delete, cli_resolve_sync
    )


class CLI_Parser(CommandParser):
    def __init__(
        self,
        styling: dict = {
            "normal_style": "skyblue",
            "title_style": "skyblue bold",
            "selected_style": "skyblue italic",
        },
        config_file: str | Path = CONFIG_PATH,
        named_days: Optional[dict[str, str]] = None,
        prompt_display: str = "=> ",
        prompt_color: str = "skyblue",
    ) -> None:
        self.prompt_display = prompt_display
        self.prompt_color = prompt_color

        super().__init__(
            make_cli_interface(**styling),
            config_file,
            named_days,
        )

        self.processors: list[Processor] = [
            DateProcessor(self.date_parser),
            CommandProcessor(),
            TaskProcessor(self.manager),
        ]

        prompt_display = f"<{prompt_color}>{prompt_display}</{prompt_color}>"
        self.session = PromptSession(
            self.make_prompt_display(),
            complete_while_typing=True,
            completer=self.update_completions(),
            input_processors=self.processors,
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

    def make_prompt_display(self):
        elements = ""
        if self.task_env != self.manager.root_task:
            elements = "/".join(t.slug for t in self.task_env.full_path[-3:]) + "|"

        return HTML(
            f"<{self.prompt_color}>{elements}{self.prompt_display}</{self.prompt_color}>"
        )

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

        return self.format_subtasks(root_task)

    def list(self, root_task: Task | None = None):
        formatted = "\n".join(self.format_tasks(root_task=root_task))
        print_formatted_text(HTML(formatted))

    def prompt(self):
        self.from_prompt(
            self.session.prompt(
                self.make_prompt_display(),
                completer=self.update_completions(),
                input_processors=self.processors,
            )
        )

    def ___enter__(self, *args, **kwargs):
        signal(SIGINT, self._sigint_handler)
        return super().__enter__()

    def _sigint_handler(self, signal_received, frame):
        self.__exit__(None, None, None)
        sys.exit(0)


def start_cli_prompt(*args, **kwargs):
    with CLI_Parser() as cli_prompt:
        while True:
            try:
                cli_prompt.prompt()

            except TaskException as e:
                cli_prompt.interface.alert(str(e))
                continue

            except KeyboardInterrupt:
                sys.exit(0)

            except EOFError:
                sys.exit(0)
