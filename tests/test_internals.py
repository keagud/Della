from pathlib import Path
from shutil import copy

import pytest
import toml

from della import cli


@pytest.fixture
def mock_config_file(tmp_path: Path, mock_task_file):
    mock_config_path = tmp_path.joinpath("config.toml").expanduser().resolve()
    copy(Path.cwd().joinpath("tests/dummy_config.toml"), mock_config_path)

    with open(mock_config_path, "r+") as config_file:
        config_contents = toml.load(config_file)
        config_contents["local"]["task_file_local"] = mock_task_file.as_posix()

        config_file.seek(0)
        toml.dump(config_contents, config_file)
        config_file.truncate()

    yield mock_config_path


@pytest.fixture
def mock_task_file(tmp_path: Path):
    mock_task_path = tmp_path.joinpath("tasks.toml").expanduser().resolve()
    mock_task_path.touch(exist_ok=True)
    yield mock_task_path


def test_setup(mock_config_file, capsys):
    with cli.CLI_Parser(config_file=mock_config_file) as c:
        c.from_prompt("@ls")
        output = capsys.readouterr()
        assert output.out.strip() == "No Tasks"
