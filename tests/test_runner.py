import json

import pytest

from drift_gym.db import snapshot
from drift_gym.report import render
from drift_gym.runner import redact, run


async def test_real_stdio_trials_are_isolated_and_report_matches(tmp_path):
    output = tmp_path / "run"
    results = await run(output, agent="reference", drifts=("baseline",), trials=1)
    assert len(results) == 6 and all(r["grade"]["passed"] for r in results)
    assert all(r["protocol_version"] == "2026-07-28" for r in results)
    assert all(r["error"] is None for r in results)
    seed = snapshot(output / "seed.sqlite3")
    assert all(t["status"] == "open" for t in seed["tickets"])
    assert len({r["seed"] for r in results}) == 6
    for result in results:
        assert (output / result["transcript"]).is_file()
        state = snapshot((output / result["transcript"]).with_name("state.sqlite3"))
        changed = [t for t in state["tickets"] if t["status"] != "open"]
        assert [t["ticket_id"] for t in changed] == [result["ticket_id"]]
    rows = [json.loads(line) for line in (output / "episodes.jsonl").read_text().splitlines()]
    assert (output / "report.md").read_text() == render(rows)
    with pytest.raises(FileExistsError):
        await run(output)


async def test_missing_key_fails_before_creating_artifacts(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        await run(tmp_path / "no-key", agent="llm")
    assert not (tmp_path / "no-key").exists()


def test_secret_redaction(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "local-secret-example")
    assert redact("local-secret-example sk-abcdefghijklmno") == "[REDACTED] [REDACTED]"


def test_json_escaped_secret_is_redacted_without_breaking_json(monkeypatch):
    secret = 'example-quote"and-backslash\\secret'
    monkeypatch.setenv("EXAMPLE_SECRET", secret)
    assert json.loads(redact(json.dumps({"content": secret}))) == {"content": "[REDACTED]"}
