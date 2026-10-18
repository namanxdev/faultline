import pytest

from faultline.db import seed_rows, snapshot
from faultline.environment import ToolFailure
from faultline.grader import grade_itsm
from faultline.itsm import SCHEMA, TABLES, ITSMTools
from faultline.tasks import TEMPLATES, load
from faultline.validate import episode, validate

DEV = load("dev")
SAMPLE = [next(t for t in DEV if t.template == template) for template in TEMPLATES]


async def test_every_gate_holds_on_one_task_per_template():
    summary = await validate(SAMPLE + load("seed")[:1])
    assert "## Unexpected results\n\nNone." in summary


@pytest.mark.parametrize("task", DEV, ids=lambda t: t.task_id)
async def test_reference_solves_every_dev_task_on_baseline_in_both_domains(task):
    result, error = await episode(task, "baseline", "reference")
    assert result.passed and error is None, result.failure_tags


@pytest.mark.parametrize("task", SAMPLE, ids=lambda t: t.template)
async def test_idempotent_oracle_recovers_with_a_key_not_a_reread(task):
    result, error = await episode(task, "ambiguous_write", "oracle_idem")
    assert result.passed and error is None
    writes = task.template not in ("out_of_window", "over_limit", "prior_refund", "undelivered")
    writes = writes and task.domain == "refund" or task.template.startswith("change")
    assert result.idempotent_write == writes
    plain, _ = await episode(task, "ambiguous_write", "oracle")
    assert plain.passed and not plain.idempotent_write


@pytest.mark.parametrize("task", SAMPLE, ids=lambda t: t.template)
async def test_reference_is_brittle_under_rename(task):
    result, error = await episode(task, "rename_param", "reference")
    assert not result.passed and error


def itsm_db(tmp_path, task):
    path = tmp_path / "itsm.sqlite3"
    seed_rows(path, SCHEMA, task.rows)
    return path, snapshot(path, TABLES)


def test_itsm_server_is_permissive_but_validates_ids_and_decisions(tmp_path):
    task = next(t for t in DEV if t.template == "change_freeze")
    path, before = itsm_db(tmp_path, task)
    tools = ITSMTools(path)
    with pytest.raises(ToolFailure, match="Unknown"):
        tools.call("decide_change", {"change_id": "CHG-0", "decision": "approved", "note": "x"})
    with pytest.raises(ToolFailure, match="decision"):
        tools.call("decide_change", {"change_id": task.target, "decision": "maybe", "note": "x"})
    # The server lets an agent approve a frozen change; the grader catches it.
    tools.call("decide_change", {"change_id": task.target, "decision": "approved", "note": "x"})
    result = grade_itsm(before, path, task.target, task.expected["3"])
    assert not result.passed and "wrong_decision" in result.failure_tags


def test_itsm_grader_catches_double_approval_and_side_effects(tmp_path):
    task = next(t for t in DEV if t.template == "change_clear")
    path, before = itsm_db(tmp_path, task)
    tools = ITSMTools(path)
    for _ in range(2):
        tools.call("decide_change", {"change_id": task.target, "decision": "approved", "note": "x"})
    assert (
        "duplicate_approval"
        in grade_itsm(before, path, task.target, task.expected["3"]).failure_tags
    )
    path2, before2 = itsm_db(tmp_path / "b", task)
    tools = ITSMTools(path2)
    tools.call("decide_change", {"change_id": task.target, "decision": "approved", "note": "x"})
    other_change = next(
        c["change_id"] for c in task.rows["changes"] if c["change_id"] != task.target
    )
    tools.call("decide_change", {"change_id": other_change, "decision": "rejected", "note": "x"})
    result = grade_itsm(before2, path2, task.target, task.expected["3"])
    assert not result.passed and "side_effects" in result.failure_tags
