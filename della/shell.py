import re
import os
from datetime import date
from os import PathLike
from pathlib import Path
from signal import signal
from signal import SIGINT

from prompt_toolkit import print_formatted_text
from prompt_toolkit import prompt
from prompt_toolkit import PromptSession


from dateparse import DateParser
from dateparse.dateparse import DateInfoTuple

from .node import Node, TaskNode, RootNode


class Shell:
    def __init__(self, filepath: str | PathLike | None = None, prompt_str: str = "@>"):

        self.root: RootNode = RootNode(filepath)

        self.filepath: PathLike = self.root.filepath
        self.current_node: Node = self.root

        self.date_parser = DateParser()

        self.command_keywords = {
            "move": ["mv", "move"],
            "delete": ["del", "rm", "delete"],
            "list": ["list", "ls"],
            "complete": ["done"],
            "edit": ["edit"],
        }
        # associate the interrupt signal (e.g. ctrl-c) with the _interrupt method
        # this means ctrl-c interrupts can trigger save to file
        # and aren't caught as exceptions

        signal(SIGINT, self._interrupt)
        self.session = PromptSession(prompt_str)

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
            (
                word
                for word in tokens
                if word.startswith("@") or ("/" in word and not word.startswith("/"))
            ),
            None,
        )

    def parse_relative_path(
        self, input_str: str, base_node: Node | None = None
    ) -> TaskNode | None:
        """Get the node pointed to by a path relative to the given node, or current active node"""

        path_content = input_str.split("/")

        if base_node is None:
            base_node = self.current_node

        iter_node: Node | None = base_node

        if base_node == self.root:
            pass

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

        if not isinstance(iter_node, Node):
            return iter_node

    def parse_absolute_path(self, input_str: str) -> TaskNode | None:
        """Get the node pointed to by an absolute path (starting from the root node)"""
        return self.parse_relative_path(input_str, base_node=self.root)

    def parse_uid_path(self, input_str: str) -> TaskNode | None:
        """Get the node pointed to a path relative to an @id, or None if not found"""

        unique_id_index = self.root.uids_index
        path_content = input_str.split("/")
        path_start = path_content[0]
        path_remainder_str = "/".join(path_content[1:])

        clean_id = re.sub(r"^@", "", path_start).lower()
        if not clean_id in unique_id_index:
            return None

        base_node = unique_id_index[clean_id]

        return self.parse_relative_path(path_remainder_str, base_node=base_node)

    def get_action_target(self, input_str: str) -> Node:

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

    def _add_from_input(self, input_str: str, parent: TaskNode):
        """main interface function to add a task at the given node, from user input"""

        task_date_info: DateInfoTuple | None = self.date_parser.get_last_info(input_str)

        task_date: date | None = None
        if task_date_info is not None:
            start, end = task_date_info.start, task_date_info.end
            input_str = input_str[start:end]
            task_date = task_date_info.date

        return TaskNode(input_str, parent, due_date=task_date)

    def command(self, input_str: str):

        target = (
            match
            if (match := self.get_action_target(input_str)) is not None
            else self.current_node
        )

        command_key: str = "add"
        input_remainder = input_str

        if (tokens := re.split(r"\s+", input_str))[0].startswith("/"):
            command_key = tokens[0][1:]
            input_remainder = " ".join(tokens[1:])

        command_key = command_key.lower()

        if not command_key in self.command_keywords.keys():
            for key, variants in self.command_keywords.items():
                if command_key in variants:
                    command_key = key
                    break

        match command_key:
            case "add":
                if not isinstance(target, TaskNode):
                    raise Exception
                self._add_from_input(input_remainder, target)
            case "move":
                # TODO
                pass
            case "delete":
                pass
            case "list":
                pass
            case "complete":
                pass
            case "edit":
                pass

    def __enter__(self):
        return self

    def write_to_file(self):

        with open(self.filepath, "w") as outfile:
            self.root.serialize(outfile)

    def _interrupt(self, signal_received, frame):

        self.write_to_file()

        self.__exit__(None, None, None)
        exit(0)

    def get_input(self) -> str:
        return self.session.prompt()

    def input_loop(self):
        while True:
            self.get_input()

    def __exit__(self, exit_type, exit_value, extit_tb, sep="\n"):
        pass
