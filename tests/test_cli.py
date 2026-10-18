import sys

import pytest

from faultline.cli import main
from faultline.db import snapshot


def test_seed_command(tmp_path, monkeypatch):
    path = tmp_path / "cli.sqlite3"
    monkeypatch.setattr(sys, "argv", ["faultline", "seed", str(path)])
    main()
    assert len(snapshot(path)["tickets"]) == 6


def test_cli_requires_a_command(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["faultline"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
