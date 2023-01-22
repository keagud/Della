import os

from os import PathLike
from pathlib import Path
from datetime import date
from collections import namedtuple
from copy import copy
import re

from typing import Type
from typing import Any


from tasks import TaskNode
from dateparse import DateParser, dateparse
from dateparse.dateparse import DateInfoTuple

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

        self.working_path = ["/"]

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

    #FINDER METHODS
    #for getting the target node of an action from user input

    def extract_path(self, input_str: str, from_end: bool = False) -> str | None:
        """
        Extract the segment of the input string that represents a path to a task.
        (Either an @id or /path/to/task, or @combo/of/the/two)
        If not is present, returns None
        """

        tokens: list[str] = re.split(r"\s+", input_str)

        if from_end:
            tokens.reverse()

        return next(
            (word for word in tokens if word.startswith("@") or "/" in word), None
        )

    def parse_relative_path(
        self, input_str: str, base_node: TaskNode | None = None
    ) -> TaskNode | None:
        """Get the node pointed to by a path relative to the given node, or current active node"""

        path_content = input_str.split("/")

        if base_node is None:
            base_node = self.current_node

        iter_node: TaskNode | None = base_node

        for path_loc in path_content[1:]:
            iter_node = next(
                (
                    n
                    for n in iter_node.subnodes
                    if n.content.lower() == path_loc.lower()
                ),
                None,
            )

            if iter_node is None:
                break

        return iter_node

    def parse_absolute_path(self, input_str: str) -> TaskNode | None:
        """Get the node pointed to by an absolute path (starting from the root node)"""
        return self.parse_relative_path(input_str, base_node=self.root_node)

    def parse_uid_path(self, input_str: str) -> TaskNode | None:
        """Get the node pointed to a path relative to an @id, or None if not found"""

        path_content = input_str.split("/")
        path_start = path_content[0]
        path_remainder_str = "/".join(path_content[1:])

        clean_id = re.sub(r"^@", "", path_start).lower()
        if not clean_id in self.unique_ids:
            return None

        base_node = self.unique_ids[clean_id]

        return self.parse_relative_path(path_remainder_str, base_node=base_node)

    def get_action_target(self, input_str: str) -> TaskNode:

        target_path = self.extract_path(input_str)

        if target_path is None:
            return self.current_node

        if target_path.startswith("@"):
            target = self.parse_uid_path(target_path)

        else:

            target = (
                match
                if (match := self.parse_absolute_path(input_str)) is not None
                else self.parse_relative_path(input_str)
            )

        if target is None:
            raise ValueError("Cannot resolve action target for '{input_str}'")

        return target

    def add_from_input(self, input_str: str):
        """main interface function to add a task at the current node"""
        operation_root = self.get_action_target(input_str)

        # TODO update dateparse api
        task_date_info: DateInfoTuple | None = self.date_parser.get_last_info(input_str)

        task_date: date | None = None
        if task_date_info is not None:
            start, end = task_date_info.start, task_date_info.end
            input_str = input_str[start:end]
            task_date = task_date_info.date

        return TaskNode(input_str, operation_root, due_date=task_date)

    # NODE ACTIONS
    #these methods all target a node
        
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

