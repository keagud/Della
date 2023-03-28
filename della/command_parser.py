from __future__ import annotations

import abc
import logging
import os
import sys
from pathlib import Path
from typing import Callable, NamedTuple, Optional

from dateparse import DateParser
from dateparse.parseutil import DateResult

from .constants import COMMAND_ALIASES, CONFIG_PATH, TASK_FILE_PATH
from .init_tasks import DellaConfig, SyncManager
from .task import Task, TaskException, TaskManager


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


def resolve_alias(input_command: str):
    for command, aliases in COMMAND_ALIASES.items():
        if input_command.lower() in aliases:
            return command

    raise TaskException(f"No command matching '{input_command}' could be resolved")


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

    def list(self, root_task: Optional[Task] = None):
        raise NotImplementedError

    def prompt(self, *args, **kwargs):
        raise NotImplementedError

    def __enter__(self, *args, **kwargs):
        if self.config.use_remote and self.sync_manager is not None:
            self.interface.alert("fetching from remote...")
            self.sync_manager.pull_and_update()
        return self

    def __exit__(self, *args, **kwargs):
        with open(self.manager.save_file_path, "w") as taskfile:
            self.manager.serialize(taskfile)

        if self.config.use_remote and self.sync_manager is not None:
            self.interface.alert("pushing to remote...")
            self.sync_manager.push_and_update()

    def resolve_keyword(self, input_keyword: str) -> Task:
        options = self.manager.search(input_keyword)

        if not options:
            raise TaskException(f"'{input_keyword}' does not point to a valid task")

        located_task = options[0]

        if len(options) > 1:
            located_task = self.interface.resolve_task(options)

        return located_task

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

        elif command is not None and remainder_tokens:
            parent_id = remainder_tokens[0]

        return ParseResult(
            input_str, " ".join(remainder_tokens), command, date_match, parent_id
        )

    def resolve_input(self, parse_result: ParseResult):
        _, content, command, date_result, parent_id = parse_result
        logging.debug(parse_result)

        if not parent_id:
            target_task = self.task_env

        else:
            target_task = self.manager.task_from_path(
                parent_id, resolve_func=self.interface.resolve_task
            )

        if target_task is None:
            raise TaskException("Could not resolve task")

        task_date = date_result.date if date_result is not None else None

        if not command:
            new_task = self.manager.add_task(content, target_task, task_date)
            self.manager.reindex()
            self.interface.alert(f"Added task: {new_task.path_str}")
            return

        matched_command = resolve_alias(command)

        match matched_command:
            case "home":
                self.task_env = self.manager.root_task
                self.interface.alert("Set context to root")

            case "delete":
                if target_task == self.manager.root_task:
                    raise TaskException("No task specified to delete")

                self.manager.delete_task(
                    target_task, warn_func=self.interface.confirm_delete
                )

            case "quit":
                sys.exit(0)

            case "list":
                self.list(root_task=target_task)

            case "set":
                self.task_env = target_task
                self.interface.alert(
                    f"Set the current context to {target_task.path_str}"
                )

    def from_prompt(self, input_prompt: str):
        result = self.parse_input(input_prompt)
        self.resolve_input(result)
