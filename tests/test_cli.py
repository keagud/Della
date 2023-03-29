import pathlib

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from della import cli, constants


@pytest.fixture(autouse=True)
def mock_input():
    with create_pipe_input() as pipe:
        with create_app_session(input=pipe, output=DummyOutput()):
            yield pipe


@pytest.fixture
def mock_config_file(tmp_path: pathlib.Path):
    mock_config_path = tmp_path.joinpath("config.toml").expanduser().resolve()
    mock_config_path.touch(exist_ok=True)
    yield mock_config_path


@pytest.fixture
def mock_task_file(tmp_path: pathlib.Path):
    mock_task_path = tmp_path.joinpath("tasks.toml").expanduser().resolve()
    mock_task_path.touch(exist_ok=True)
    yield mock_task_path


@pytest.fixture(autouse=True)
def mock_paths(monkeypatch, mock_config_file, mock_task_file):
    monkeypatch.setattr(constants, "CONFIG_PATH", mock_config_file.as_posix())

    monkeypatch.setattr(constants, "TASK_FILE_PATH", mock_task_file.as_posix())


def test_prompt():
    with cli.CLI_Parser():
        mock_input.send_text("@ls")
