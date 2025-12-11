
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "data"

@pytest.fixture
def output_dir(tmp_path):
    return tmp_path
