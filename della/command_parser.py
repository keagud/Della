from __future__ import annotations

import os
from pathlib import Path
from pprint import pprint
from typing import Callable, NamedTuple, Optional

from dateparse import DateParser
from dateparse.parseutil import DateResult

from .task import Task, TaskManager


class ParseResult(NamedTuple):
    original_input: str
    content: str
    command: str | None = None
    date_result: DateResult | None = None
    parent_identifier: str | None = None


class CommandParser:
    def __init__(
        self,
        filepath: str | Path = "~/.local/tasks.toml",
        named_days: Optional[dict[str, str]] = None,
        resolve_func: Optional[Callable[[list[Task]], Task | None]] = None,
        warn_func: Optional[Callable[[Task], bool]] = None,
        alert_func: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.date_parser = DateParser(named_days=named_days)
        self.resolve_func = resolve_func
        self.warn_func = warn_func

        if not alert_func:
            self.alert_func = lambda *args, **kwargs: None
        else:
            self.alert_func = alert_func

        self.filepath = Path(filepath).expanduser().resolve()

        if not self.filepath.exists():
            os.makedirs(self.filepath.parent, exist_ok=True)
            self.filepath.touch(exist_ok=True)

        self.manager = TaskManager.deserialize(filepath)

        self.task_env: Task = self.manager.root_task

    def __enter__(self, *args, **kwargs):
        raise NotImplementedError

    def __exit__(self, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def create(cls, mode: str = "cli", *args, **kwargs):
        c = CommandParser(*args, **kwargs, alert_func=print)

        return c

    def task_search(
        self,
        search_str: str | None,
    ):
        if search_str is None:
            return None

        # ipdb.set_trace()
        search_results = self.manager.search(search_str)

        if not search_results:
            return None

        if len(search_results) == 1:
            return search_results[0]

        if self.resolve_func is not None:
            return self.resolve_func(search_results)

        return None

    def parse_input(self, input_str: str):
        date_match = self.date_parser.get_last(input_str)

        remainder = input_str[: date_match.start] if date_match else input_str

        remainder_tokens = remainder.strip().split()

        # ! marks a command, everything else is considered a new task to add
        command = None
        if remainder_tokens[0].startswith("!"):
            command = remainder_tokens[0][1:]
            remainder_tokens = remainder_tokens[1:]

        slug_patterns = [s for s in remainder_tokens if s.startswith("#")]

        parent_id = None
        if slug_patterns:
            first_slug_match = slug_patterns[0]

            remainder_tokens.remove(first_slug_match)

            parent_id = first_slug_match.strip("#")

            print(remainder_tokens)
        return ParseResult(
            input_str, " ".join(remainder_tokens), command, date_match, parent_id
        )

    def resolve_input(self, parse_result: ParseResult):
        _, content, command, date_result, parent_id = parse_result
        task_parent = self.task_search(parent_id)
        pprint(parse_result)
        if task_parent is None:
            task_parent = self.task_env

        task_date = date_result.date if date_result is not None else None

        if not command:
            new_task = self.manager.add_task(content, task_parent, task_date)
            self.manager.reindex()
            self.alert_func(f"Added task: {new_task.path_str}")
            return

        if command.lower() in ("del", "rm", "done", "d"):
            target_str = content

            target_task = self.task_search(target_str)

            if target_task is None:
                raise ValueError(f"Could not find {target_str}")

            self.manager.delete_task(target_task, warn_func=self.warn_func)

            return None

        if command.lower() in ("ls", "list", "show", "l"):
            self.alert_func(str(self.manager))

            return None

        raise KeyError(f"!{command} is not a known command")

    def from_prompt(self, input_prompt: str):
        result = self.parse_input(input_prompt)
        self.resolve_input(result)