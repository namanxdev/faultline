import sys

import pytest

from drift_gym.cli import main
from drift_gym.db import snapshot


def test_seed_command(tmp_path, monkeypatch):
    path = tmp_path / "cli.sqlite3"
    monkeypatch.setattr(sys, "argv", ["drift-gym", "seed", str(path)])
    main()
    assert len(snapshot(path)["tickets"]) == 6


def test_cli_requires_a_command(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["drift-gym"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
