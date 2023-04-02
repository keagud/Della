import shutil
from pathlib import Path

import toml
from invoke import task

from della.constants import CONFIG_PATH, DEFAULT_CONFIG

local_task_path = (
    Path(DEFAULT_CONFIG["local"]["task_file_local"]).expanduser().resolve()
)

test_tasks = toml.loads(
    r"""
[meta]
timestamp = 0

[tasks]
content = "All Tasks"
due_date = "None"
[[tasks.subtasks]]
content = "Project Foo"
due_date = "None"

[[tasks.subtasks.subtasks]]
content = "task baz"
due_date = "2023-24-12"

[[tasks.subtasks.subtasks]]
content = "a task"
due_date = "None"

[[tasks.subtasks.subtasks]]
content = "biff"
due_date = "None"

[[tasks.subtasks.subtasks]]
content = "fix dates"
due_date = "2023-04-07"

[[tasks.subtasks.subtasks.subtasks]]
content = "a nested subtask"
due_date = "None"

[[tasks.subtasks]]
content = "Project Bar"                        
due_date = "2024-06-30"                        

[[tasks.subtasks.subtasks]]
content = "item 1"                        
due_date = "None"                        

                        """
)


def get_tmp_path(target_path: Path) -> Path:
    tmp_filename = f"user_{target_path.stem}.toml"
    return target_path.parent.joinpath(tmp_filename).expanduser().resolve()


def setup_dummy_file(target_path: Path, default_contents: dict) -> None:
    tmp_path = get_tmp_path(target_path)
    with open(target_path, "r") as infile:
        file_contents = toml.load(infile)

    if file_contents == default_contents:
        return

    shutil.move(target_path, tmp_path)

    with open(target_path, "w") as outfile:
        toml.dump(default_contents, outfile)


def undo_dummy(target_path: Path):
    tmp_path = get_tmp_path(target_path)
    shutil.move(tmp_path, target_path)


@task
def setup(c):
    setup_dummy_file(CONFIG_PATH, DEFAULT_CONFIG)
    setup_dummy_file(local_task_path, test_tasks)


@task
def teardown(c):
    undo_dummy(CONFIG_PATH)
    undo_dummy(local_task_path)
