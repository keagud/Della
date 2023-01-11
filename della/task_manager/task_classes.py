from __future__ import annotations
from datetime import date
from os import PathLike
from typing import Any


class TaskNode:
    content: str
    due_date: date | None
    subnodes: list[TaskNode]
    parent: TaskNode | None

    def __init__(
        self, content: str, parent: TaskNode | None, due_date: date | None = None
    ) -> None:
        pass

    @classmethod
    def set_formatting(cls):
        pass

    @staticmethod
    def init_from_file(filepath: PathLike) -> TaskNode:  # type: ignore
        pass

    def detatch_from_parent(self):
        if self.parent is not None:
            self.parent.subnodes.remove(self)
            return

        raise AttributeError("Cannot detatch a node with no parents")

    def change_parent(self, new_parent: TaskNode):
        if self in new_parent.subnodes:
            raise AttributeError(
                "This node is already a child of the specified parent node"
            )

        self.detatch_from_parent()
        self.parent = new_parent
        self.parent.add_subnode(self)


    def add_subnode(self, new_node: TaskNode):
        self.subnodes.append(new_node)

    def change_date(self, new_date: date):
        self.due_date = new_date

    def to_dict(self, recurse: bool = True) -> dict[str, str]:  # type: ignore

        pass

    def __iter__(self):
        return ((n) for n in self.subnodes)

    def __str__(self) -> str:  # type: ignore
        pass

    def display(self):
        pass
