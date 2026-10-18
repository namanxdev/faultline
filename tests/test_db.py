import pytest

from faultline.db import cents, dollars, seed_database, snapshot


def test_seed_is_deterministic_and_refuses_overwrite(database, tmp_path):
    other = tmp_path / "other.sqlite3"
    seed_database(other)
    assert snapshot(database) == snapshot(other)
    assert len(snapshot(database)["tickets"]) == 6
    with pytest.raises(FileExistsError):
        seed_database(database)


@pytest.mark.parametrize("value", ["0", "-1", "1.001", "nan", "inf", "oops", True])
def test_invalid_money(value):
    with pytest.raises(ValueError):
        cents(value)


def test_exact_money():
    assert cents("49.99") == 4999
    assert cents(80) == 8000
    assert dollars(1) == "0.01"
