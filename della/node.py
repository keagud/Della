from __future__ import annotations
from pathlib import Path
from os import PathLike
from datetime import date

from typing import TextIO
from typing import Any

import toml


class Node:
    def __init__(self):

        # DIY virtual constructor
        if not type(self) in (type(TaskNode), type(RootNode)):
            raise NotImplementedError

        self.subnodes: list[TaskNode] = []

    def asdict(self, depth: int = 1):

        node_dict: dict[str, Any] = {}

        if isinstance(self, TaskNode):

            node_dict = {
                "content": self.content,
                "due_date": self.due_date.isoformat()
                if self.due_date is not None
                else "",
                "unique_id": self.unique_id if self.unique_id is not None else "",
            }

        if depth != 0 and self.subnodes:
            node_dict["subnodes"] = [c.asdict(depth=depth - 1) for c in self.subnodes]

        return node_dict

    def del_subnode(self, n: TaskNode):
        self.subnodes.remove(n)

    def add_subnode(self, n: TaskNode):
        self.subnodes.append(n)

    @property
    def root(self) -> RootNode:
        raise NotImplementedError

    def __iter__(self):
        return ((n) for n in self.subnodes)

    def display(self, max_depth: int = -1, indent: str = " ", bullet: str = ""):
        """Return a formatted string with this node's info, recursively"""

        def recursive_display(n: Node, depth: int):

            if isinstance(n, RootNode):
                lines = []
            else:
                lines = [(indent * depth) + bullet + str(n)]

            if max_depth < 0 or max_depth < max_depth:
                for s in n.subnodes:
                    lines.extend(recursive_display(s, depth + 1))

            return lines

        return "\n".join(recursive_display(self, 0))


class TaskNode(Node):
    def __init__(
        self,
        content: str,
        parent: Node,
        due_date: date | None = None,
        unique_id: str | None = None,
    ):
        super().__init__()
        self.parent = parent
        self.content = content
        self._root: RootNode = parent.root
        self.due_date = due_date
        self.unique_id = unique_id

    @classmethod
    def from_dict(cls, init_dict: dict, parent: Node) -> TaskNode:

        node_content: str = init_dict["content"]
        node_due_date: date | None = (
            date.fromisoformat(date_str)
            if (date_str := init_dict["due_date"])
            else None
        )

        node_unique_id: str | None = init_dict.get("unique_id")

        new_node = TaskNode(
            content=node_content,
            parent=parent,
            due_date=node_due_date,
            unique_id=node_unique_id,
        )

        if "subnodes" in init_dict:

            for subdict in init_dict["subnodes"]:
                new_node.add_subnode(TaskNode.from_dict(subdict, new_node))

        return new_node

    @property
    def unique_id(self):
        return self.unique_id

    @unique_id.setter
    def unique_id(self, new_id):
        if new_id in self.root.uids_index:
            raise KeyError(f"")
        self.unique_id = new_id
        self.root.uids_index[new_id] = self

    @property
    def parent(self) -> Node:
        return self.parent

    @parent.setter
    def parent(self, p: Node) -> None:
        if hasattr(self, "parent"):
            old_parent = self.parent
            old_parent.del_subnode(self)

        self.root = p.root
        setattr(self, "parent", p)
        p.add_subnode(self)

    @property
    def root(self) -> RootNode:
        return self._root

    @root.setter
    def root(self, r):
        self._root = r

    def __str__(self) -> str:
        date_str = (
            f" [{self.due_date.isoformat()}]" if self.due_date is not None else ""
        )
        return self.content + date_str


class RootNode(Node):

    default_filepath: Path = Path("~/.local/tasks.toml").expanduser()

    def __init__(self, filepath: str | PathLike | None = None):
        super().__init__()

        self.filepath: PathLike = (
            Path(filepath) if filepath is not None else self.default_filepath
        )

        self.uids_index: dict[str, TaskNode] = {}

        if not self.filepath.exists():
            self.filepath.touch()

        with open(self.filepath, "r") as infile:
            data_dict = toml.load(infile)

        if data_dict and "subnodes" in data_dict:
            for n in data_dict["subnodes"]:
                self.add_subnode(TaskNode.from_dict(n, self))

    def serialize(self, fstream: TextIO) -> str:

        if not fstream.writable():
            raise IOError("Cannot write to stream")

        return toml.dump(self.asdict(depth=-1), fstream)

    @property
    def root(self):
        return self
