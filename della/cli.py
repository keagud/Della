import sys
from pathlib import Path
from shutil import get_terminal_size
from signal import SIGINT, signal
from typing import Optional

from getchoice import ChoicePrinter
from halo import Halo
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.completion import FuzzyCompleter
from prompt_toolkit.formatted_text import merge_formatted_text, to_formatted_text
from prompt_toolkit.layout.processors import Processor
from prompt_toolkit.styles import Style

from .command_parser import CommandParser, CommandsInterface
from .completion import CommandProcessor, DateProcessor, TaskCompleter, TaskProcessor
from .constants import CONFIG_PATH, HELP_MESSAGE
from .default_config import DEFAULT_CONFIG_TEXT
from .init_tasks import DellaConfig
from .task import Task, TaskException


def _format_tag(text: str, tag: str):
    return f"<{tag}>{text}</{tag}>"


def make_cli_interface(styling: Style):
    chooser = ChoicePrinter(style=styling)

    def cli_alert(message: str) -> None:
        print_formatted_text(HTML(_format_tag(message, "alert")), style=styling)

    def cli_resolve_task(options: list[Task]) -> Task:
        alert_title = "Multiple matches! Which did you mean?"

        _, chosen = chooser.getchoice(
            [(t.path_str, t) for t in options], title=alert_title
        )
        return chosen

    def cli_confirm_delete(t: Task) -> bool:
        delete_message = f"Really delete '{t}?'"

        if t.subtasks:
            delete_message += f"\nIt has {len(t.subtasks)} subtasks"

        _, chosen = chooser.yes_no(title=delete_message)
        return chosen

    def cli_help():
        print_formatted_text(HTML(HELP_MESSAGE))

    def cli_resolve_sync() -> bool:
        # TODO
        return True

    return CommandsInterface(
        cli_alert, cli_resolve_task, cli_confirm_delete, cli_resolve_sync, cli_help
    )


class CLI_Parser(CommandParser):
    def __init__(
        self,
        config_file: str | Path = CONFIG_PATH,
        named_days: Optional[dict[str, str]] = None,
        prompt_display: str = "=> ",
        prompt_color: str = "ansicyan",
        followup_prompt: str = ">> ",
    ) -> None:
        self.prompt_display = prompt_display
        self.prompt_color = prompt_color
        self.followup_prompt = followup_prompt

        if not Path(config_file).exists():
            with open(config_file, "w") as new_config:
                new_config.write(DEFAULT_CONFIG_TEXT)

        self.config = DellaConfig.load(config_file)

        super().__init__(
            make_cli_interface(self.config.style),
            self.config,
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

    def make_prompt_display(self, followup: bool = False):
        elements = ""

        display = self.prompt_display if not followup else self.followup_prompt
        if self.task_env != self.manager.root_task:
            elements = "/".join(t.slug for t in self.task_env.full_path[-3:]) + "|"

        return HTML(f"<{self.prompt_color}>{elements}{display}</{self.prompt_color}>")

    def update_completions(self):
        task_completer = TaskCompleter.from_tasks(self.manager.root_task)
        self.completer = FuzzyCompleter(task_completer, WORD=False)
        return self.completer

    def format_subtasks(
        self,
        t,
        level=0,
        term_width: Optional[int] = None,
    ):
        if term_width is None:
            term_width, _ = get_terminal_size()
            term_width -= 5

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

            formatted_line.append(left_content)

            if display_date:
                formatted_line.append(f"{display_date:>{right_padding}}")

            line_str = _format_tag(
                "".join(formatted_line) + "\n", f"task_level_{level}"
            )

            line_formatted = to_formatted_text(HTML(line_str))
            ls.append(line_formatted)

            if subtask.subtasks:
                recurse_args = {
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
        formatted = merge_formatted_text(self.format_tasks(root_task=root_task))
        print_formatted_text(formatted, style=self.config.style)

    def query(self, followup: bool = False) -> str:
        return self.session.prompt(
            self.make_prompt_display(followup=followup),
            completer=self.update_completions(),
            input_processors=self.processors,
        )

    def prompt(self):
        self.from_prompt(self.query())

    def __enter__(self, *args, **kwargs):
        signal(SIGINT, self._sigint_handler)

        if not self.config.use_remote or not self.config.sync_config:
            super().__enter__()
            return self

        with Halo(text="Loading from remote", spinner="bouncingBar"):
            return super().__enter__()

    def __exit__(self, *args, **kwargs):
        if not self.config.use_remote or not self.config.sync_config:
            super().__exit__()

        with Halo(text="Syncing with remote", spinner="bouncingBar"):
            super().__exit__()

    def _sigint_handler(self, signal_received, frame):
        self.__exit__(None, None, None)
        sys.exit(0)


def start_cli_prompt(*args, **kwargs):
    with CLI_Parser() as cli_prompt:
        if cli_prompt.config.start_message:
            print_formatted_text(HTML(cli_prompt.config.start_message))
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
