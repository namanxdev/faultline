import pytest

from drift_gym.db import seed_database


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "seed.sqlite3"
    seed_database(path)
    return path
