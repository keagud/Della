import pytest

from della import cli_api


@pytest.fixture(params=["yaml", "toml", "json"])
def file_load(request):

    target_filename: str = "tests/data/test." + request.param
    return cli_api.load_from_file(target_filename)


def test_loader(file_load):
    n = file_load
