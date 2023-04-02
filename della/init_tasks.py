import os
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path
from typing import Any, Callable, NamedTuple, Optional

import paramiko
import toml
from prompt_toolkit.styles import Style

from .constants import CONFIG_PATH, DEFAULT_CONFIG, TMP_SYNCFILE


def style_from_dict(style_dict: dict):
    styles = [f"{k}:ansi{v}" for k, v in style_dict.items() if k in ("fg", "bg")]
    styles.append(style_dict.get("extra", ""))
    return " ".join(styles)


def iter_style(styles_list: list[dict]):
    c = count()
    return [(f"task_level_{next(c)}", style_from_dict(d)) for d in styles_list]


def load_styles(styles_config: dict):
    styles = iter_style(styles_config.pop("tasks_display"))

    styles.extend(
        [
            (name.strip("choose_"), style_from_dict(content))
            for name, content in styles_config.items()
        ]
    )

    return Style(styles)


class SyncConfig(NamedTuple):
    address: str
    user: str
    task_file_remote: Path
    private_key_location: Path
    use_remote: Optional[bool]


@dataclass
class DellaConfig:
    init_dict: dict
    init_config_filepath: str | Path

    style: Style = field(init=False)
    config_filepath: Path = field(init=False)
    use_remote: bool = field(init=False)
    start_message: Optional[str] = None

    sync_config: Optional[SyncConfig] = None

    def serialize(self):
        data_dict = {"local": {"tasks_file_local": self.task_file_local.as_posix()}}

        remote_options: dict[str, Any] = {"use_remote": self.use_remote}

        if self.sync_config is not None:
            remote_options.update(self.sync_config._asdict())

        data_dict.update({"remote": remote_options})
        return data_dict

    @classmethod
    def default(cls):
        return DellaConfig(DEFAULT_CONFIG, CONFIG_PATH)

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
        self.style = load_styles(self.init_dict["style"])

        self.start_message = self.init_dict.get("start_message")

        self.config_filepath = Path(self.init_config_filepath).expanduser().resolve()

        self.task_file_local = local_options["task_file_local"]
        self.use_remote = remote_options["use_remote"]
        self.sync_config = None

        if self.use_remote:
            remote_options["private_key_location"] = (
                Path(remote_options["private_key_location"]).expanduser().resolve()
            )

            remote_file = Path(remote_options["task_file_remote"])

            remote_options["task_file_remote"] = (
                remote_file.expanduser().resolve().relative_to(remote_file.home())
            )

            self.sync_config = SyncConfig(**remote_options)

    @property
    def connect_args(self):
        if self.sync_config is None:
            raise ValueError

        return {
            "hostname": self.sync_config.address,
            "username": self.sync_config.user,
            "key_filename": self.sync_config.private_key_location.as_posix(),
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


class SyncManager:
    def __init__(
        self,
        config: Optional[DellaConfig] = None,
        resolve_func: Optional[Callable[..., bool]] = None,
    ):
        if config is None:
            config = DellaConfig.load()

        self.config = config
        sync_config = config.sync_config

        assert sync_config is not None
        self.sync_config: SyncConfig = sync_config

        self.resolve_func = resolve_func

        self.tmp_syncfile = self.config.task_file_local.parent.joinpath(TMP_SYNCFILE)

    def ping(self, count: int = 3):
        subprocess.run(
            ["ping", self.sync_config.address, f"-c {count}"]
        ).check_returncode()

    @contextmanager
    def get_connection(self):
        try:
            connect_client = paramiko.SSHClient()
            connect_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            connect_client.connect(**self.config.connect_args)
            yield connect_client.open_sftp()

        finally:
            connect_client.close()

    def get_most_recent(self):
        return self.compare_file_versions(
            local=self.config.task_file_local, remote=self.tmp_syncfile
        )

    def fetch_remote(self, connection: paramiko.SFTPClient):
        self.config.task_file_local.parent.mkdir(exist_ok=True, parents=True)
        connection.get(
            remotepath=self.sync_config.task_file_remote.as_posix(),
            localpath=self.tmp_syncfile.as_posix(),
        )

    def push_remote(self, connection: paramiko.SFTPClient) -> None:
        connection.put(
            localpath=self.config.task_file_local.as_posix(),
            remotepath=self.sync_config.task_file_remote.as_posix(),
        )

    def pull_and_update(self) -> None:
        with self.get_connection() as connection:
            self.fetch_remote(connection)

        if self.get_most_recent() == self.config.task_file_local:
            overwrite_newest = False
            if self.resolve_func is not None:
                overwrite_newest = self.resolve_func("pull")

            if not overwrite_newest:
                return

        shutil.move(self.tmp_syncfile, self.config.task_file_local)

    def push_and_update(self) -> None:
        with self.get_connection() as connection:
            try:
                self.fetch_remote(connection)
            except FileNotFoundError:
                self.push_remote(connection)
                return

            if self.get_most_recent() == self.tmp_syncfile:
                overwrite_newest = True
                if self.resolve_func is not None:
                    overwrite_newest = self.resolve_func("push")
                if not overwrite_newest:
                    return

            self.push_remote(connection)
        os.remove(self.tmp_syncfile)

    def get_file_timestamp(self, file: Path):
        with open(file, "r") as infile:
            contents = toml.load(infile)

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
