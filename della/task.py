"""Defines the Task class"""

from __future__ import annotations

import time
import types
from collections import deque
from datetime import date as DateType
from functools import cached_property, partial
from itertools import chain
from pathlib import Path
from typing import Callable, Optional, TextIO

import toml
from slugify import slugify


class TaskException(KeyError):
    def __init__(self, message, *args, **kwargs) -> None:
        self.message = str(message)
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        return self.message


class Task:
    def __init__(
        self,
        content: str,
        parent: Optional[Task],
        due_date: Optional[DateType] = None,
    ) -> None:
        if not content:
            raise TaskException("A task cannot be empty")

        self.content = content
        self.due_date = due_date
        self._parent = None
        self.parent = parent
        self.slug = slugify(self.content)
        self.subtasks = []

    @classmethod
    def init_from_dict(cls, task_parent: Task, task_dict: dict):
        new_content = task_dict["content"]

        try:
            new_due_date = DateType.fromisoformat(task_dict.get("due_date", ""))
        except ValueError:
            new_due_date = None

        new_task = Task(new_content, task_parent, new_due_date)

        [
            Task.init_from_dict(new_task, d)
            for d in task_dict.get("subtasks", [])
            if isinstance(d, dict)
        ]

        return new_task

    @cached_property
    def full_path(self) -> list[Task]:
        if self.parent is None:
            return []

        return self.parent.full_path + [self]

    @cached_property
    def path_str(self) -> str:
        return "/".join(s.slug for s in self.full_path)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, new_parent: Task | None):
        if self._parent is not None:
            self._parent.subtasks.remove(self)

        if new_parent is not None:
            new_parent.subtasks.append(self)

        self._parent = new_parent

    def __iter__(self):
        yield self
        if self.subtasks:
            yield from chain.from_iterable(i for i in (s for s in self.subtasks))

    def decompose(self):
        raise NotImplementedError

    def __str__(self):
        return self.content

    def __repr__(self):
        if self.due_date is None:
            return self.content

        return f"{self.content} | {self.due_date}"

    def _define_subtasks(self, s: list[Task]):
        self.subtasks = s

    def _to_dict(self, recurse: bool = True):
        save_dict: dict[str, str | list] = {
            "content": self.content,
            "due_date": "None" if not self.due_date else self.due_date.isoformat(),
        }

        if recurse and self.subtasks:
            save_dict["subtasks"] = [c._to_dict(recurse=True) for c in self.subtasks]

        return save_dict


class TaskManager:
    def __init__(
        self,
        save_file: str | Path = "~/.local/della/tasks.toml",
        show_days_until: bool = True,
        date_format: str = "%a, %b %d",
    ):
        self.date_format = date_format
        self.show_days_until = show_days_until

        self.save_file_path = save_file

        self.root_task = Task("All Tasks", None)
        self.tasks_index: dict[str, Task] = {}
        self.active_task = self.root_task

    @property
    def save_file_path(self):
        return self._save_file_path

    @save_file_path.setter
    def save_file_path(self, new_path: str | Path):
        self._save_file_path = Path(new_path).expanduser().resolve()

    def __iter__(self):
        yield from (i for i in self.root_task if i is not self.root_task)

    def _set_task_format(self, target_task: Task):
        def task_decompose(task: Task):
            def make_display_date():
                if task.due_date is None:
                    return ""

                display_date = " " + task.due_date.strftime(self.date_format)

                if not self.show_days_until:
                    return display_date

                days_until_delta = task.due_date - DateType.today()

                return f"{display_date} (in {days_until_delta.days} days)"

            subtask_summary = (
                "" if not task.subtasks else f"{len(task.subtasks)} subtasks"
            )

            return (task.content, subtask_summary, make_display_date())

        def task_str(task: Task):
            return " | ".join([t for t in task_decompose(task) if t])

        target_task.decompose = types.MethodType(task_decompose, target_task)
        target_task.__str__ = types.MethodType(task_str, target_task)

    def add_task(
        self,
        content: str,
        parent: Optional[Task] = None,
        due_date: Optional[DateType] = None,
    ):
        if parent is None:
            parent = self.root_task

        new_task = Task(content, parent, due_date)

        new_task.parent = parent

        self._set_task_format(new_task)

        self.tasks_index[new_task.path_str] = new_task

        self.reindex()
        return new_task

    def move_task(self, target_task: Task, new_parent: Task):
        self.reindex()
        target_task.parent = new_parent
        self.reindex()

    def __repr__(self):
        self.reindex()
        return self.tasks_index.__repr__()

    def serialize(self, fp: TextIO):
        data_dict = {
            "meta": {"timestamp": int(time.time())},
            "tasks": self.root_task._to_dict(recurse=True),
        }

        toml.dump(data_dict, fp)

        return data_dict

    @classmethod
    def deserialize(cls, filepath: str | Path, fp: Optional[TextIO] = None, **kwargs):
        new_manager = TaskManager(save_file=filepath, **kwargs)
        data_dict: dict[str, dict] = {}

        if not fp:
            with open(new_manager.save_file_path, "r") as load_file:
                data_dict = toml.load(load_file)
        else:
            data_dict = toml.load(fp)

        tasks_dict: dict[str, str | list[dict]] = data_dict.get("tasks", {})

        tasks = [v for v in tasks_dict.get("subtasks", []) if isinstance(v, dict)]
        root_subtasks = list(
            map(partial(Task.init_from_dict, new_manager.root_task), tasks)
        )

        new_manager.root_task._define_subtasks(root_subtasks)

        new_manager.reindex()
        return new_manager

    def reindex(self):
        self.tasks_index.clear()
        for task in self:
            path_str: str = task.path_str
            if path_str in self.tasks_index and self.tasks_index[path_str] != task:
                self.delete_task(task)
                raise TaskException(f"{path_str} already present")
            self.tasks_index[path_str] = task

            self._set_task_format(task)

    def search(
        self,
        target_str: str,
        search_start: Optional[Task] = None,
        test_func: Optional[Callable[[str, Task], bool]] = None,
    ) -> list[Task]:
        if not search_start:
            search_start = self.root_task

        if not test_func:

            def _test_func(a, b):
                return a == b.slug

            test_func = _test_func

        search_queue = deque(search_start.subtasks)
        found = []

        while search_queue:
            t = search_queue.pop()

            if test_func(target_str, t):
                found.append(t)

            if t.subtasks:
                search_queue.extendleft(t.subtasks)

        return found

    def task_from_path(
        self, input_str: str, resolve_func: Optional[Callable] = None
    ) -> Task | None:
        task_index = self.tasks_index

        task_start = self.root_task

        path_tokens = input_str.split("/")

        if not path_tokens:
            raise ValueError

        initial_token = path_tokens[0]

        if initial_token.startswith("#") and len(initial_token) > 1:
            task_start_options = self.search(initial_token.strip("#"))

            if not task_start_options:
                return None

            if len(task_start_options) > 1:
                if resolve_func is not None:
                    task_start = resolve_func(task_start_options)
                else:
                    return None

            task_start = task_start_options[0]

            path_tokens = path_tokens[1:]

        resolved_path = "/".join([t.slug for t in task_start.full_path] + path_tokens)

        return task_index.get(resolved_path)

    def delete_task(
        self, task: Task, warn_func: Optional[Callable[[Task], bool]] = None
    ) -> bool:
        if warn_func and not warn_func(task):
            return False

        task.parent = None
        self.reindex()

        return True
