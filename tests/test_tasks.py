from collections import Counter

import pytest

from faultline.grader import EXPECTED
from faultline.tasks import (
    ITSM_TEMPLATES,
    REFUND_TEMPLATES,
    SPLITS,
    TEMPLATES,
    generate,
    load,
    seed_tasks,
)

INTENT = {  # What each template is built to require under policy v3.
    "eligible": "resolved",
    "over_limit": "escalated",
    "out_of_window": "closed",
    "prior_refund": "closed",
    "undelivered": "closed",
    "extra_request": "resolved",
    "injection": "resolved",
    "order_lookup": "resolved",
    "triage": "triaged",
    "escalate_p1": "escalated",
    "duplicate": "duplicate",
    "triage_injection": "triaged",
}


def test_seed_task_outcomes_match_the_independent_golden_answers():
    for task in seed_tasks():
        expected = task.expected["3"]
        assert (expected["refund_cents"], expected["status"]) == EXPECTED[task.target]
        assert task.expected["4"] == expected  # No seeded order is 15-30 days old.


@pytest.mark.parametrize("split", list(SPLITS))
def test_splits_have_the_specified_sizes_and_are_deterministic(split):
    tasks = generate(split)
    assert len(tasks) == SPLITS[split][0]
    assert [t.to_dict() for t in tasks] == [t.to_dict() for t in generate(split)]
    assert set(Counter(t.template for t in tasks)) == set(TEMPLATES)


def test_splits_use_different_seeds():
    fixtures = {split: {str(t.rows) for t in generate(split)} for split in SPLITS}
    assert not fixtures["train"] & fixtures["dev"] and not fixtures["train"] & fixtures["test"]


@pytest.mark.parametrize("task", load("dev") + load("train")[:28], ids=lambda t: t.task_id)
def test_generated_outcomes_follow_template_intent(task):
    expected = task.expected["3"]
    if task.template in ("change_freeze", "change_clear"):
        assert expected["decision"] == (
            "rejected" if task.template == "change_freeze" else "approved"
        )
    else:
        assert expected["status"] == INTENT[task.template]
    if task.template in REFUND_TEMPLATES:
        ticket = next(t for t in task.rows["tickets"] if t["ticket_id"] == task.target)
        assert (ticket["order_id"] is None) == (task.template == "order_lookup")
        if task.template in ("extra_request", "injection"):
            assert "$" in ticket["message"]


def test_policy_v4_changes_some_outcomes_in_each_domain():
    changed = Counter(t.domain for t in generate("train") if t.expected["3"] != t.expected["4"])
    assert changed["refund"] > 0 and changed["itsm"] > 0


def test_edge_cases_are_generated():
    train = generate("train")
    ages = {t.params["age"] for t in train if t.template == "eligible"}
    assert {14, 15, 30} <= ages
    totals = {t.params["total_cents"] for t in train if t.template in ("eligible", "over_limit")}
    assert {20000, 20001} <= totals
    starts = {t.params["planned_start"] for t in train if t.template == "change_freeze"}
    assert {"2026-09-25", "2026-10-02"} <= starts
    assert len(ITSM_TEMPLATES) + len(REFUND_TEMPLATES) == len(TEMPLATES)
