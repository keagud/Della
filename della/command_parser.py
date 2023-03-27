from __future__ import annotations

import abc
import logging
import os
import sys
from pathlib import Path
from typing import Callable, NamedTuple, Optional

from dateparse import DateParser
from dateparse.parseutil import DateResult

from .constants import CONFIG_PATH, TASK_FILE_PATH
from .init_tasks import DellaConfig, SyncManager
from .task import Task, TaskManager


class ParseResult(NamedTuple):
    original_input: str
    content: str
    command: str | None = None
    date_result: DateResult | None = None
    parent_identifier: str | None = None


class CommandsInterface(NamedTuple):
    alert: Callable[[str], None]
    resolve_task: Callable[[list[Task]], Task]
    confirm_delete: Callable[[Task], bool]
    resolve_sync: Callable[[], bool]


class CommandParser(metaclass=abc.ABCMeta):
    def __init__(
        self,
        interface: CommandsInterface,
        filepath: str | Path = TASK_FILE_PATH,
        config_path: str | Path = CONFIG_PATH,
        named_days: Optional[dict[str, str]] = None,
    ) -> None:
        self.date_parser = DateParser(named_days=named_days)

        self.interface = interface

        self.config = DellaConfig.load(filepath=config_path)

        self.sync_manager: Optional[SyncManager] = None

        if self.config.use_remote and self.config.sync_config is not None:
            self.sync_manager = SyncManager(self.config)

        self.filepath = Path(filepath).expanduser().resolve()

        if not self.filepath.exists():
            os.makedirs(self.filepath.parent, exist_ok=True)
            self.filepath.touch(exist_ok=True)

        self.manager = TaskManager.deserialize(filepath)

        self.task_env: Task = self.manager.root_task

    def list(self):
        raise NotImplementedError

    def prompt(self, *args, **kwargs):
        raise NotImplementedError

    def __enter__(self, *args, **kwargs):
        if self.config.use_remote and self.sync_manager is not None:
            print("fetching from remote...")
            self.sync_manager.pull_and_update()
        return self

    def __exit__(self, *args, **kwargs):
        with open(self.manager.save_file_path, "w") as taskfile:
            self.manager.serialize(taskfile)

        if self.config.use_remote and self.sync_manager is not None:
            print("pushing to remote...")
            self.sync_manager.push_and_update()

    def resolve_keyword(self, input_keyword: str) -> Task:
        options = self.manager.search(input_keyword)

        if not options:
            raise KeyError(f"'{input_keyword}' does not point to a valid task")

        located_task = options[0]

        if len(options) > 1:
            located_task = self.interface.resolve_task(options)

        return located_task

    def task_from_path(self, input_str: str):
        task_index = self.manager.tasks_index

        path_tokens = input_str.split("/")

        if not path_tokens:
            raise ValueError

        task_start = self.manager.root_task

        if path_tokens[0].startswith("#"):
            task_start = self.resolve_keyword(path_tokens[0].strip("#"))
            path_tokens = path_tokens[1:]

        resolved_path = task_start.path_str + "/".join(path_tokens)

        return task_index[resolved_path]

    def parse_input(self, input_str: str):
        date_match = self.date_parser.get_last(input_str)

        remainder = input_str[: date_match.start] if date_match else input_str

        remainder_tokens = remainder.strip().split()

        # @ marks a command, everything else is considered a new task to add
        command = None
        if remainder_tokens[0].startswith("@"):
            command = remainder_tokens[0][1:]
            remainder_tokens = remainder_tokens[1:]

        slug_patterns = [s for s in remainder_tokens if s.startswith("#")]

        parent_id = None
        if slug_patterns:
            first_slug_match = slug_patterns[0]
            parent_id = first_slug_match
            remainder_tokens.remove(first_slug_match)

        return ParseResult(
            input_str, " ".join(remainder_tokens), command, date_match, parent_id
        )

    def resolve_input(self, parse_result: ParseResult):
        _, content, command, date_result, parent_id = parse_result
        logging.debug(parse_result)

        if not parent_id:
            target_task = self.task_env

        else:
            target_task = self.task_from_path(parent_id)

        task_date = date_result.date if date_result is not None else None

        if not command:
            new_task = self.manager.add_task(content, target_task, task_date)
            self.manager.reindex()
            self.interface.alert(f"Added task: {new_task.path_str}")
            return

        if command.lower() in ("del", "delete", "rm", "done", "d"):
            self.manager.delete_task(
                target_task, warn_func=self.interface.confirm_delete
            )
            return None

        if command.lower() in ("q", "quit", "exit"):
            sys.exit(0)

        if command.lower() in ("ls", "list", "show", "l"):
            self.list()

            return None

        raise KeyError(f"@{command} is not a known command")

    def from_prompt(self, input_prompt: str):
        result = self.parse_input(input_prompt)
        self.resolve_input(result)
