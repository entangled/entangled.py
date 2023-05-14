import pytest
from pathlib import Path


@pytest.fixture
def data():
    return Path(__file__).parent / "data"


@pytest.fixture(params=list((Path(__file__).parent / "data").glob("*.md")))
def markdown(request):
    with open(request.param, "r") as f:
        yield f.read()
