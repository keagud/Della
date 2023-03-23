from pathlib import Path
from typing import Final


def resolve_path(path_str: str) -> Path:
    return Path(path_str).expanduser().resolve()


REMOTE_PATH: Final = resolve_path("~/della/tasks.toml")
CONFIG_PATH: Final = resolve_path("~/.config/della/config.toml")
TASK_FILE_PATH: Final = Path("~/.local/della/tasks.toml")

TMP_SYNCFILE: Final = "tmp_tasks.toml"
