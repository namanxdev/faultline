import itertools
import json

import pytest

from faultline.report import pass_metrics, render, write_report


@pytest.mark.parametrize(("n", "c", "k"), [(3, 0, 1), (3, 1, 2), (3, 2, 3), (6, 4, 2), (3, 3, 3)])
def test_estimator_matches_enumeration(n, c, k):
    samples = list(itertools.combinations([True] * c + [False] * (n - c), k))
    assert pass_metrics(n, c, k) == pytest.approx(
        (
            sum(any(s) for s in samples) / len(samples),
            sum(all(s) for s in samples) / len(samples),
        )
    )


@pytest.mark.parametrize("args", [(0, 0, 1), (3, 4, 1), (3, 2, 4), (3, -1, 1), (3, 2, 0)])
def test_invalid_estimator_input(args):
    with pytest.raises(ValueError):
        pass_metrics(*args)


def test_report_reproduces_jsonl_and_keeps_task_groups(tmp_path):
    rows = [
        {
            "agent": "test",
            "ticket_id": t,
            "drift": "baseline",
            "grade": {"passed": success, "failure_tags": []},
            "usage": {"cost_usd": 0, "prompt_tokens": 0, "completion_tokens": 0},
        }
        for t, success in [("A", True), ("A", False), ("B", True)]
    ]
    path = tmp_path / "episodes.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    report = write_report(path).read_text(encoding="utf-8")
    assert report == render(rows)
    assert "| test | A | baseline | 1/2 | 2 | 1.000000 | 0.000000 |" in report
    assert "| test | B | baseline | 1/1 | 2 |" not in report


def test_models_are_reported_separately():
    rows = [
        {
            "agent": "llm",
            "model": model,
            "ticket_id": "A",
            "drift": "baseline",
            "grade": {"passed": model == "m1", "failure_tags": []},
            "usage": {"cost_usd": 0, "prompt_tokens": 0, "completion_tokens": 0},
        }
        for model in ("m1", "m2")
    ]
    report = render(rows)
    assert "| llm (m1) | A | baseline | 1/1 | 1 |" in report
    assert "| llm (m2) | A | baseline | 0/1 | 1 |" in report
