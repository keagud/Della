"""Defines the Task class"""

from __future__ import annotations

import types
from datetime import date as DateType
from functools import partial
from pathlib import Path
from typing import Optional, TextIO

import toml


class Task:
    def __init__(
        self,
        content: str,
        parent: Optional[Task],
        due_date: Optional[DateType] = None,
    ) -> None:
        self.content = content
        self.due_date = due_date
        self.parent = parent

        self.subtasks = []

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, new_parent: Task | None):
        if self._parent is not None:
            self._parent.subtasks.remove(self)

        self._parent = new_parent

    def __str__(self):
        raise NotImplementedError

    def _to_dict(self, recurse: bool = True):
        pass

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
        save_file: str | Path,
        show_days_until: bool = True,
        date_format: str = "%a, %b %d",
    ):
        self.date_format = date_format
        self.show_days_until = show_days_until

        self.save_file_path = save_file

        self.root_task = Task("All Tasks", None)

    @property
    def save_file_path(self):
        return self._save_file_path

    @save_file_path.setter
    def save_file_path(self, new_path: str | Path):
        self._save_file_path = Path(new_path).expanduser().resolve()

    def _set_task_format(self, target_task: Task):
        def task_str(task: Task):
            def make_display_date():
                if task.due_date is None:
                    return ""

                display_date = " " + task.due_date.strftime(self.date_format)

                if not self.show_days_until:
                    return display_date

                days_until_delta = task.due_date - DateType.today()

                return f"{display_date} (in {days_until_delta.days} days)"

            subtask_summary = (
                " " if not task.subtasks else f"| {len(task.subtasks)} subtasks"
            )

            return f"{task.content}{subtask_summary}{make_display_date()}".strip()

        target_task.__str__ = types.MethodType(task_str, target_task)

    def add_task(
        self, content: str, parent: Optional[Task], due_date: Optional[DateType] = None
    ):
        if parent is None:
            parent = self.root_task

        return Task(content, parent, due_date)

    def serialize(self, fp: TextIO):
        tasks_dicts = self.root_task._to_dict(recurse=True)
        toml.dump(tasks_dicts, fp)

        return tasks_dicts

    @classmethod
    def deserialize(cls, filepath: str | Path, fp: Optional[TextIO] = None, **kwargs):
        new_manager = TaskManager(save_file=filepath, **kwargs)

        data_dict: dict[str, str | list] = {}

        if not fp:
            with open(new_manager.save_file_path, "r") as load_file:
                data_dict = toml.load(load_file)
        else:
            data_dict = toml.load(fp)

        def dict_init(parent_task: Task, task_dict: dict):
            new_content = task_dict.get("content", "")

            try:
                new_due_date = DateType.fromisoformat(task_dict.get("due_date", ""))
            except ValueError:
                new_due_date = None

            new_task = Task(new_content, parent_task, new_due_date)

            if "subtasks" in task_dict.keys():
                make_subtask = partial(dict_init, parent_task=new_task)
                map(make_subtask, task_dict["subtasks"])

        root_subtasks = data_dict.get("subtasks", [])

        if isinstance(root_subtasks, str):
            error_text = f"Error deserializing {filepath}:"
            "expected subtasks as a list, not a string"
            raise ValueError(error_text)

        map(partial(dict_init, parent_task=new_manager.root_task), root_subtasks)

        return new_manager
