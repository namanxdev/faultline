import json
import sys

import pytest

from faultline.calibrate import render, tag, write_calibration
from faultline.cli import main


@pytest.mark.parametrize(
    ("c", "expected"),
    [(0, "too_hard"), (1, "calibrated"), (2, "calibrated"), (3, "too_easy"), (8, "too_easy")],
)
def test_tags_at_k8(c, expected):
    assert tag(c, 8) == expected


def test_tag_boundaries_are_exact():
    # 10% and 30% are inside the calibrated band; float rounding must not move them.
    assert tag(1, 10) == tag(3, 10) == "calibrated"
    assert tag(31, 100) == "too_easy" and tag(9, 100) == "too_hard"


@pytest.mark.parametrize("args", [(1, 0), (-1, 8), (9, 8)])
def test_invalid_tag_input(args):
    with pytest.raises(ValueError):
        tag(*args)


def rows(model, task, drift, passes, k=8):
    return [
        {
            "agent": "llm",
            "model": model,
            "ticket_id": task,
            "drift": drift,
            "error": None,
            "grade": {"passed": i < passes, "failure_tags": []},
        }
        for i in range(k)
    ]


def test_render_tags_cells_and_counts_per_model_and_drift():
    episodes = rows("m1", "A", "baseline", 8) + rows("m1", "B", "baseline", 2)
    episodes += rows("m1", "A", "ambiguous_write", 0) + rows("m2", "A", "baseline", 1)
    report = render(episodes)
    assert "| m1 | A | baseline | 8/8 | 100.0% | too_easy |" in report
    assert "| m1 | B | baseline | 2/8 | 25.0% | calibrated |" in report
    assert "| m1 | A | ambiguous_write | 0/8 | 0.0% | too_hard |" in report
    assert "| m1 | all | 1 | 1 | 1 |" in report
    assert "| m1 | baseline | 1 | 1 | 0 |" in report
    assert "| m2 | all | 0 | 1 | 0 |" in report


def test_calibrate_cli_retags_saved_episodes(tmp_path, monkeypatch):
    path = tmp_path / "episodes.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows("m1", "A", "baseline", 1)))
    monkeypatch.setattr(sys, "argv", ["faultline", "calibrate", "--episodes", str(path)])
    main()
    assert (tmp_path / "calibration.md").read_text(encoding="utf-8") == render(
        rows("m1", "A", "baseline", 1)
    )
    assert write_calibration(path).name == "calibration.md"


def test_calibrate_cli_refuses_paid_run_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # No .env here.
    monkeypatch.setattr(sys, "argv", ["faultline", "calibrate", "--output", str(tmp_path / "c")])
    with pytest.raises(SystemExit):
        main()
    assert not (tmp_path / "c").exists()
