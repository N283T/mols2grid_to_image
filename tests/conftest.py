import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "data"


@pytest.fixture
def output_dir():
    out = Path(__file__).parent / "output"
    out.mkdir(exist_ok=True)
    return out
