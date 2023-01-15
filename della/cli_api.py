import os
from os import PathLike
from pathlib import Path


from tasks import TaskNode
from dateparse import DateParser


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
