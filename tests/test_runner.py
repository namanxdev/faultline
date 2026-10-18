import json

import pytest

from faultline.db import snapshot
from faultline.report import render
from faultline.runner import error_name, redact, run


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


@pytest.mark.parametrize(
    ("model", "key"),
    [
        ("openrouter/openai/gpt-4.1-mini", "OPENROUTER_API_KEY"),
        ("openai/gpt-4.1-mini-2025-04-14", "OPENAI_API_KEY"),
    ],
)
async def test_missing_key_fails_before_creating_artifacts(tmp_path, monkeypatch, model, key):
    monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError, match=key):
        await run(tmp_path / "no-key", agent="llm", model=model)
    assert not (tmp_path / "no-key").exists()


async def test_unknown_model_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unknown model"):
        await run(tmp_path / "unknown", agent="llm", model="openrouter/some/unpriced-model")
    assert not (tmp_path / "unknown").exists()


async def test_ledger_refusal_leaves_no_run_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "local-placeholder")
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps({"phase": 1, "run": "old", "spent_usd": 4.5}) + "\n")
    with pytest.raises(ValueError, match="Phase 1 cap"):
        await run(tmp_path / "over", agent="llm", budget_usd=1, ledger=ledger)
    assert not (tmp_path / "over").exists()


def test_error_name_unwraps_task_group_errors():
    nested = ExceptionGroup("outer", [ExceptionGroup("inner", [KeyError("x")])])
    assert error_name(nested) == "KeyError"
    two = ExceptionGroup("two", [KeyError(), TimeoutError()])
    assert error_name(two) == "KeyError+TimeoutError"
    assert error_name(ValueError()) == "ValueError"


def test_secret_redaction(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "local-secret-example")
    assert redact("local-secret-example sk-abcdefghijklmno") == "[REDACTED] [REDACTED]"


def test_json_escaped_secret_is_redacted_without_breaking_json(monkeypatch):
    secret = 'example-quote"and-backslash\\secret'
    monkeypatch.setenv("EXAMPLE_SECRET", secret)
    assert json.loads(redact(json.dumps({"content": secret}))) == {"content": "[REDACTED]"}


async def test_unknown_notes_variant_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="notes"):
        await run(tmp_path / "notes", agent="llm", notes="helpful")
    assert not (tmp_path / "notes").exists()


async def test_generated_tasks_run_in_real_subprocesses_for_both_domains(tmp_path):
    from faultline.tasks import load

    dev = load("dev")
    lookup = next(t for t in dev if t.template == "order_lookup")
    change = next(t for t in dev if t.template == "change_freeze")
    items = [(lookup, "pagination"), (change, "rename_param+transient_503")]
    results = await run(tmp_path / "gen", agent="oracle", split="dev", trials=1, items=items)
    assert [r["domain"] for r in results] == ["refund", "itsm"]
    assert all(r["grade"]["passed"] and r["error"] is None for r in results)
    assert results[0]["episode_id"] == f"oracle-{lookup.task_id}-pagination-0"
    assert (tmp_path / "gen" / "seeds" / f"{change.task_id}.sqlite3").is_file()


async def test_train_split_refuses_held_out_drifts(tmp_path):
    with pytest.raises(ValueError, match="Held-out"):
        await run(
            tmp_path / "t", agent="oracle", split="train", drifts=("rename_param+ambiguous_write",)
        )
