import json
import tempfile
from pathlib import Path

import pytest
import verifiers.v1 as vf
from mcp.server.mcpserver import MCPServer

from faultline.db import seed_rows
from faultline.drifts import HELD_OUT
from faultline_vf import FaultlineTaskset
from faultline_vf.taskset import (
    FaultlineData,
    FaultlineState,
    FaultlineTasksetConfig,
    FaultlineToolset,
)


def tasks(split, **task):
    config = FaultlineTasksetConfig(split=split, task=task)
    return list(FaultlineTaskset(config))


def test_splits_load_every_task_under_every_split_drift():
    assert len(tasks("dev")) == 50 * 13 and len(tasks("train")) == 300 * 11
    assert not {t.data.drift for t in tasks("train")} & set(HELD_OUT)
    first = tasks("dev")[0]
    assert first.data.id == "dev-0000/baseline" and "refund policy" in first.data.system_prompt
    assert len({t.key for t in tasks("dev")}) == 650


@pytest.mark.parametrize(
    ("drift", "tool", "param"),
    [("baseline", "get_order", "order_id"), ("rename_param", "get_order", "order_ref")],
)
async def test_toolset_publishes_the_drifted_schema(drift, tool, param):
    toolset = FaultlineToolset(vf.ToolsetConfig())
    await toolset.setup_task(
        FaultlineData(task_id="T-1001", split="seed", drift=drift, domain="refund")
    )
    server = MCPServer("test")
    toolset.register(server)
    listed = {t.name: t for t in await server.list_tools()}
    assert param in listed[tool].input_schema["properties"]
    assert ("wait" in listed) is False


async def test_toolset_description_drift_changes_after_the_first_call():
    toolset = FaultlineToolset(vf.ToolsetConfig())
    data = FaultlineData(task_id="T-1001", split="seed", drift="description_drift", domain="refund")
    await toolset.setup_task(data)
    server = MCPServer("test")
    toolset.register(server)
    before = {t.name: t.description for t in await server.list_tools()}
    toolset.service.calls["get_ticket"] += 1
    after = {t.name: t.description for t in await server.list_tools()}
    assert before["issue_refund"] != after["issue_refund"]


def _db(task) -> str:
    path = Path(tempfile.mkdtemp()) / "state.sqlite3"
    seed_rows(path, task.faultline.schema, task.faultline.rows)
    return str(path)


async def test_untouched_scores_zero_and_shaping_is_bounded():
    task = tasks("dev", shaped=True)[0]
    trace = type("T", (), {"state": FaultlineState(db=_db(task), calls=["get_refund_policy"])})()
    assert await task.solved(trace) == pytest.approx(0.1)  # Failing, plus the policy bonus.
    assert json.dumps(await task.failure_tags(trace))
