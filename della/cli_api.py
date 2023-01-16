import os

from os import PathLike
from pathlib import Path
from datetime import date
from collections import namedtuple
from copy import copy

from typing import Type
from typing import Any


from tasks import TaskNode
from dateparse import DateParser

CommandList = namedtuple("CommandList", "delete finish move list")


class TaskManager:

    default_task_path: PathLike = Path("~/.local/tasks.toml")

    def load_from_file(self, filepath: PathLike | str = default_task_path) -> TaskNode:

        if isinstance(filepath, str):
            filepath = Path(filepath)

        if not os.path.exists(filepath):
            if filepath != self.default_task_path:
                raise FileNotFoundError(f"No file named '{filepath}' could be found")

            print(f"No task file found at {str(self.default_task_path)} - creating")
            os.makedirs(self.default_task_path)

            return TaskNode("", None, None)

        return TaskNode.init_from_file(filepath)

    def __init__(self, filepath: PathLike | str = default_task_path) -> None:

        self.root_node: TaskNode = self.load_from_file(filepath)
        self.task_file_path = filepath
        self.current_node = self.root_node

        self.unique_ids: dict[str, TaskNode] = {}

        self._index_nodes()

        self.date_parser = DateParser()

    def _index_nodes(self):
        """index unique node ids for quick lookup when user requests it"""

        def recursive_index(node: TaskNode):

            if (uid := node.unique_id) is not None:

                if uid in self.unique_ids:
                    raise KeyError("Two nodes cannot have the same unique id")

                self.unique_ids[uid] = copy(node)

            for subnode in node.subnodes:
                recursive_index(subnode)

        recursive_index(self.root_node)

    def write_to_file(self, target_file: str | PathLike = default_task_path):

        _, serialize_format = (e.lower() for e in os.path.splitext(str(target_file)))

        if (
            not serialize_format
            or serialize_format not in TaskNode.filetype_handlers.keys()
        ):
            raise FileNotFoundError(
                f"Target extension {serialize_format} cannot be resolved"
            )

        with open(target_file, "w") as outfile:
            self.root_node.serialize(outfile, target_format=serialize_format)

    def add_from_input(self, input_str: str):
        """main interface function to add a task at the current node"""
        # TODO

    def get_node_from_name(self, input_str: str) -> TaskNode:  # type: ignore

        path_tree: list[str] = input_str.split("/")

        path_tree.reverse()

        for i, location in enumerate(path_tree):
            if location in self.unique_ids:
                return self.unique_ids[location]

    def change_active_node(self, node: TaskNode | str):
        """set the current node to the given one, or the one pointed to by the given id"""

        target_node: Any = node

        if isinstance(node, str):
            target_node = self.unique_ids.get(node, None)

        if not isinstance(target_node, TaskNode):
            raise Exception("No node with that ID exists")

        self.current_node = target_node

    def new_subnode(self, content: str, due_date: date | None = None):
        pass

    def delete_node(self, node: TaskNode):
        pass

    def mark_node_complete(self, node: TaskNode):
        pass

    def display_nodes(self, depth: int = -1, from_root: bool = True):
        """Print all nodes to the given depth"""
        pass
