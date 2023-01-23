import pytest

from della.node import Node, TaskNode, RootNode
from della.shell import Shell


@pytest.fixture(params=["yaml", "toml", "json"])
def get_filepath(request):
    return "tests/data/test." + request.param


@pytest.fixture()
def file_load(get_filepath):
    return RootNode(get_filepath)

@pytest.fixture()
def make_shell(get_filepath):
    return Shell(get_filepath)

def test_actions(file_load):
    root_node = file_load

    assert root_node is not None
