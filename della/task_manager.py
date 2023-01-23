import os

from os import PathLike
from pathlib import Path
from datetime import date
from collections import namedtuple
from copy import copy
import re

from typing import Type
from typing import Any

from .task_node import TaskNode
from dateparse import DateParser, dateparse
from dateparse.dateparse import DateInfoTuple



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

    # FINDER METHODS
    # for getting the target node of an action from user input
    # these methods all target a node

    def set_uid(self, new_id: str, node: TaskNode | None = None):
        if node is None:
            node = self.current_node

        new_id = new_id.lower()

        if new_id in self.unique_ids:
            conficting_node = self.unique_ids[new_id]
            raise KeyError(
                f"The unique identifier '{new_id}' is already associated with '{conficting_node.full_path_str}'"
            )

        self.unique_id = new_id

    def add_subnode(self, node: TaskNode, subnode_args: dict[str, Any]):
        subnode_content: str = subnode_args["content"]
        subnode_date: date | None = subnode_args.get("unique_id", None)
        subnode_uid: str | None = subnode_args.get("unique_id", None)

        return TaskNode(subnode_content, node, subnode_date, subnode_uid)

    def mark_complete(self, node: TaskNode):
        # TODO
        pass

    def delete_node(self, node: TaskNode):

        if node.parent is None:
            raise Exception("Cannot delete the root project!")

        if node.subnodes:
            # TODO warn before deleting a node with subnodes
            pass

        node.detatch_from_parent()

    def move_node(self, node: TaskNode, new_parent: TaskNode):
        node.change_parent(new_parent)

    def set_active(self, node: TaskNode):
        self.current_node = node
