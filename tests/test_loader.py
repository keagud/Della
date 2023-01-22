import pytest

from della import tasks
from della import cli_api

@pytest.fixture(params=["yaml", "toml", "json"])
def get_filepath(request):
    return "tests/data/test." + request.param


@pytest.fixture()
def file_load(get_filepath):
    return tasks.TaskNode.init_from_file(get_filepath)


@pytest.fixture
def make_manager(get_filepath):
    return cli_api.TaskManager(get_filepath)


def test_actions(file_load):
    root_node = file_load

    assert root_node is not None
    assert root_node.content == "this is the root node"


def test_task_manager(get_filepath):
    task_manager = cli_api.TaskManager(get_filepath)




