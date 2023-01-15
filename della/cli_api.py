import os
from os import PathLike
from pathlib import Path


from .tasks import TaskNode
from dateparse import DateParser


def load_from_file(filepath: PathLike | str):

    if isinstance(filepath, str):
        filepath = Path(filepath)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No file named '{filepath}' could be found")

    return TaskNode.init_from_file(filepath)
