import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from pprint import pprint
from typing import Callable, Optional

import fabric
import toml
from constants import CONFIG_PATH, REMOTE_PATH, TASK_FILE_PATH, TMP_SYNCFILE


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
    def default(cls):
        default_config = {
            "local": {"tasks_path": TASK_FILE_PATH},
            "remote": {"use_remote": False, "tasks_path": REMOTE_PATH},
        }

        return DellaConfig(default_config, CONFIG_PATH)

    @classmethod
    def load(cls, filepath: str | Path = CONFIG_PATH):
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
            "connect_kwargs": {"key_filename": self.private_key_location.as_posix()},
        }

    @property
    def task_file_local(self) -> Path:
        return self._task_file_local

    @task_file_local.setter
    def task_file_local(self, input_path: Path | str):
        new_path = Path(input_path).expanduser().resolve()
        if not new_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.touch()

        self._task_file_local = new_path

    @property
    def task_file_remote(self) -> Path:
        if self._task_file_remote is None:
            raise KeyError

        return self._task_file_remote

    @task_file_remote.setter
    def task_file_remote(self, input_path: Path | str):
        new_abspath = Path(input_path).expanduser().resolve()
        self._task_file_remote = new_abspath.relative_to(Path.home())

    @property
    def private_key_location(self) -> Path:
        if self._private_key_location is None:
            raise KeyError

        return self._private_key_location

    @private_key_location.setter
    def private_key_location(self, input_path: Path | str):
        self._private_key_location = Path(input_path).expanduser().resolve()


class SyncManager:
    def __init__(
        self,
        config: Optional[DellaConfig] = None,
        resolve_func: Optional[Callable[..., bool]] = None,
    ):
        if config is None:
            config = DellaConfig.load()

        self.config = config

        self.resolve_func = resolve_func

        self.tmp_syncfile = self.config.task_file_local.parent.joinpath(TMP_SYNCFILE)

    def get_most_recent(self):
        return self.compare_file_versions(
            local=self.config.task_file_local, remote=self.tmp_syncfile
        )

    def fetch_remote(self):
        pprint(self.tmp_syncfile)

        self.config.task_file_local.parent.mkdir(exist_ok=True, parents=True)
        with fabric.Connection(**self.config.connect_args) as connection:
            connection.get(
                self.config.task_file_remote.as_posix(),
                local=self.tmp_syncfile.as_posix(),
            )

    def push_remote(self) -> None:
        remote_dir = self.config.task_file_remote.parent
        with fabric.Connection(**self.config.connect_args) as connection:
            connection.run(f"mkdir -p {remote_dir.as_posix()}")
            connection.put(
                self.config.task_file_local.as_posix(),
                remote=self.config.task_file_remote.as_posix(),
            )

    def pull_and_update(self) -> None:
        self.fetch_remote()

        if self.get_most_recent() == self.config.task_file_local:
            overwrite_newest = False
            if self.resolve_func is not None:
                overwrite_newest = self.resolve_func("pull")

            if not overwrite_newest:
                return

        shutil.move(self.tmp_syncfile, self.config.task_file_local)

    def push_and_update(self) -> None:
        try:
            self.fetch_remote()
        except FileNotFoundError:
            self.push_remote()
            return

        if self.get_most_recent() == self.tmp_syncfile:
            print("aaa")
            overwrite_newest = True
            if self.resolve_func is not None:
                overwrite_newest = self.resolve_func("push")
            if not overwrite_newest:
                return

        self.push_remote()
        os.remove(self.tmp_syncfile)

    def get_file_timestamp(self, file: Path):
        pprint(file)
        with open(file, "r") as infile:
            contents = toml.load(infile)
            pprint(contents)

        if not contents:
            return 0

        timestamp: int = contents["meta"]["timestamp"]

        return timestamp

    def compare_file_versions(
        self, local: Optional[Path], remote: Optional[Path]
    ) -> Path:
        if local is None and remote is None:
            raise FileNotFoundError

        if local is None or not local.exists():
            assert remote is not None
            return remote

        if remote is None or not remote.exists():
            return local

        local_timestamp = self.get_file_timestamp(local)
        remote_timestamp = self.get_file_timestamp(remote)

        return local if local_timestamp > remote_timestamp else remote


def main():
    sync_manager = SyncManager()
    sync_manager.pull_and_update()


if __name__ == "__main__":
    main()
