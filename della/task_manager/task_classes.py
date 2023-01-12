from __future__ import annotations

from datetime import date
from os import PathLike
from os.path import splitext
from os.path import exists

from typing import Any
from typing import Callable
from collections import namedtuple

import yaml
import toml
import json


MarkupHandler = namedtuple("MarkupHandler", ["load", "dump"])


class TaskNode:

    filetype_handlers: dict[str, MarkupHandler] = {
        "yaml": MarkupHandler(yaml.load, yaml.dump),
        "toml": MarkupHandler(toml.load, toml.dump),
        "json": MarkupHandler(json.load, json.dump),
    }

    def __init__(
        self, content: str, parent: TaskNode | None, due_date: date | None = None
    ) -> None:
        self.content = content
        self.due_date = due_date
        self.parent = parent

        self.subnodes: list[TaskNode] = []

    @classmethod
    def from_dict(cls, init_dict: dict, parent: TaskNode | None = None) -> TaskNode:  # type: ignore

        node_content: str = init_dict["content"]

        node_parent = parent

        node_due_date: date | None = (
            date.fromisoformat(date_str)
            if (date_str := init_dict["due_date"])
            else None
        )

        new_node = TaskNode(
            content=node_content, parent=node_parent, due_date=node_due_date
        )

        if "subnodes" in init_dict:

            for subdict in init_dict["subnodes"]:
                new_node.add_subnode(TaskNode.from_dict(subdict))

        return new_node

    @classmethod
    def init_from_file(cls, filepath: PathLike) -> TaskNode:  # type: ignore

        if not exists(filepath):
            raise FileNotFoundError

        _, file_ext = splitext(filepath)

        file_ext: str = file_ext.lower().strip()[1:]

        if not file_ext or not file_ext in cls.filetype_handlers:
            raise ValueError(
                f"Cannot initialize from file '{filepath}':"
                "extension '{file_ext}' is not in allowed extensions"
                "\n\t({', '.join(cls.filetype_handlers)})"
            )

        format_handler = cls.filetype_handlers[file_ext]

    def detatch_from_parent(self):
        if self.parent is not None:
            self.parent.subnodes.remove(self)
            return

        raise AttributeError("Cannot detatch a node with no parents")

    def change_parent(self, new_parent: TaskNode):
        if self in new_parent.subnodes:
            raise AttributeError(
                "This node is already a subnode of the specified parent node"
            )

        self.detatch_from_parent()
        self.parent = new_parent
        self.parent.add_subnode(self)

    def add_subnode(self, new_node: TaskNode):
        self.subnodes.append(new_node)

    def change_date(self, new_date: date):
        self.due_date = new_date

    def to_dict(self, depth: int = 0) -> dict[str, Any]:

        node_dict = {
            "parent": self.parent.content if self.parent is not None else "",
            "content": self.content,
            "due_date": self.due_date.isoformat if self.due_date is not None else "",
        }

        if depth != 0 and self.subnodes:

            node_dict["subnodes"] = [c.to_dict(depth=depth - 1) for c in self.subnodes]

        return node_dict

    def __iter__(self):
        return ((n) for n in self.subnodes)

    def __str__(self) -> str:  # type: ignore
        date_str = (
            f" [{self.due_date.isoformat()}]" if self.due_date is not None else ""
        )
        return self.content + date_str

    def display(self, depth: int = 0):
        pass
