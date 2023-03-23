from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import fabric
import toml


@dataclass
class DellaConfig:
    init_dict: dict

    init_config_filepath: str | Path

    config_filepath: Path = field(init=False)

    _task_file_local: Path = field(init=False)
    use_remote: bool = field(init=False)

    remote_ip: Optional[str] = field(init=False)
    remote_user: Optional[str] = field(init=False)

    _task_file_remote: Optional[Path] = field(init=False)
    _private_key_location: Optional[Path] = field(init=False)

    def serialize(self):
        data_dict = {"local": {"tasks_path": self.task_file_local}}

        remote_options = {
            k: v
            for k, v in {
                "use_remote": self.use_remote,
                "ip": self.remote_ip,
                "user": self.remote_user,
                "tasks_path": self.task_file_remote,
                "private_key_location": self.private_key_location,
            }.items()
            if v is not None
        }

        data_dict.update({"remote": remote_options})
        return data_dict

    @classmethod
    def load(cls, filepath: str | Path = "~/.config/della/config.toml"):
        config_file = Path(filepath).expanduser().resolve()

        with open(config_file, "r") as infile:
            init_dict = toml.load(infile)

        return DellaConfig(init_dict, config_file.as_posix())

    def save(self, filename: Optional[str | Path] = None):
        if filename is None:
            filename = self.config_filepath

        data_dict = self.serialize()

        save_path = Path(filename).expanduser().resolve()

        if not save_path.exists():
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.touch()

        with open(save_path, "w") as save_file:
            toml.dump(data_dict, save_file)

    def __post_init__(self):
        remote_options = self.init_dict["remote"]
        local_options = self.init_dict["local"]

        self.config_filepath = Path(self.init_config_filepath).expanduser().resolve()

        self.task_file_local = local_options["tasks_path"]
        self.use_remote = remote_options["use_remote"]

        self.remote_ip = remote_options.get("ip")
        self.remote_user = remote_options.get("user")
        self.task_file_remote = remote_options.get("tasks_path")
        self.private_key_location = remote_options.get("private_key_location")

        if self.use_remote:
            for option in (
                self.remote_ip,
                self.remote_user,
                self.task_file_remote,
                self.private_key_location,
            ):
                assert option is not None

    @property
    def connect_args(self):
        return {
            "host": self.remote_ip,
            "user": self.remote_user,
            "connect_kwargs": {"key_filename": self.private_key_location},
        }

    @property
    def task_file_local(self) -> str:
        return self._task_file_local.as_posix()

    @task_file_local.setter
    def task_file_local(self, input_path: Path | str):
        new_path = Path(input_path).expanduser().resolve()
        if not new_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.touch()

        self._task_file_local = new_path

    @property
    def task_file_remote(self) -> str:
        if self._task_file_remote is None:
            raise KeyError

        return self._task_file_remote.as_posix()

    @task_file_remote.setter
    def task_file_remote(self, input_path: Path | str):
        new_abspath = Path(input_path).expanduser().resolve()
        self._task_file_remote = new_abspath.relative_to(Path.home())

    @property
    def private_key_location(self) -> str:
        if self._private_key_location is None:
            raise KeyError

        return self._private_key_location.as_posix()

    @private_key_location.setter
    def private_key_location(self, input_path: Path | str):
        self._private_key_location = Path(input_path).expanduser().resolve()


def make_default_config():
    raise NotImplementedError


def get_file_timestamp(file: Path):
    with open(file, "r") as infile:
        contents = toml.load(infile)

    timestamp: int = contents["meta"]["timestamp"]

    return timestamp


def compare_file_versions(
    local: Optional[Path], remote: Optional[Path]
) -> Optional[Path]:
    if local is None and remote is None:
        return None

    if local is None or not local.exists():
        return remote

    if remote is None or not remote.exists():
        return local

    local_timestamp = get_file_timestamp(local)
    remote_timestamp = get_file_timestamp(remote)

    return local if local_timestamp > remote_timestamp else remote


def sync_remote(
    config: Optional[DellaConfig] = None,
    resolve_func: Optional[Callable[[None], bool]] = None,
):
    if config is None:
        config = DellaConfig.load()

    tasks_dir = Path(config.task_file_local).parent
    remote_taskfile = tasks_dir.joinpath("~tmp_tasks.toml")

    try:
        with fabric.Connection(**config.connect_args) as c:
            c.get(config.task_file_remote, local=remote_taskfile.as_posix())

    except FileNotFoundError:
        pass

    most_recent = compare_file_versions(Path(config.task_file_local), remote_taskfile)

    assert most_recent is not None


def push_remote(config: Optional[DellaConfig] = None):
    pass


def fetch_remote(
    config: DellaConfig,
):
    tasks_dir = Path(config.task_file_local).parent
    tmp_taskfile = tasks_dir.joinpath("~tmp_tasks.toml")

    with fabric.Connection(**config.connect_args) as c:
        c.get(config.task_file_remote, local=tmp_taskfile.as_posix())


def main():
    sync_remote()


if __name__ == "__main__":
    main()
