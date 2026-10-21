"""Inspect AI task. One sample is one faultline task under one drift.

The tools are the faultline MCP server itself, over stdio: a fresh process and database
per sample. The scorer is the state grader; it never reads the transcript.

    uv run inspect eval faultline/inspect_task.py -T split=test -T first=14 --model ...
"""

import sys
import tempfile
from functools import cache
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser, GenerateConfig, get_model
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.tool import mcp_connection, mcp_server_stdio

from faultline import itsm
from faultline.db import TABLES, seed_rows, snapshot
from faultline.grader import grade_task
from faultline.llm import MAX_OUTPUT, system_prompt, task_prompt
from faultline.runner import policy_version
from faultline.tasks import SPLIT_DRIFTS, load
from faultline.tasks import Task as FaultlineTask


@cache
def _tasks(split: str) -> dict[str, FaultlineTask]:
    return {t.task_id: t for t in load(split)}


def dataset(split: str, first: int | None = None, drifts: str | None = None) -> list[Sample]:
    chosen = drifts.split(",") if drifts else SPLIT_DRIFTS[split]
    return [
        Sample(
            input=task_prompt(t.target),
            id=f"{t.task_id}/{drift}",
            metadata={"split": split, "task_id": t.task_id, "drift": drift},
        )
        for t in list(_tasks(split).values())[:first]
        for drift in chosen
    ]


@solver
def faultline_agent(notes: str = "stale"):
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata
        target = _tasks(meta["split"])[meta["task_id"]]
        db = Path(tempfile.mkdtemp(prefix="faultline-inspect-")) / "state.sqlite3"
        seed_rows(db, target.schema, target.rows)
        tables = itsm.TABLES if target.domain == "itsm" else TABLES
        state.store.set("db", str(db))
        state.store.set("before", snapshot(db, tables))
        server = mcp_server_stdio(
            name="faultline",
            command=sys.executable,
            args=["-m", "faultline.server", "--db", str(db), "--drift", meta["drift"]]
            + ["--domain", target.domain],
        )
        state.messages = [
            ChatMessageSystem(content=system_prompt(notes, target.domain)),
            ChatMessageUser(content=task_prompt(target.target)),
        ]
        async with mcp_connection([server]):
            # generate_loop returns only the messages it added.
            added, state.output = await get_model().generate_loop(state.messages, tools=[server])
        state.messages.extend(added)
        return state

    return solve


@scorer(metrics=[accuracy(), stderr()])
def faultline_grader():
    async def score(state: TaskState, target: Target) -> Score:
        meta = state.metadata
        task_ = _tasks(meta["split"])[meta["task_id"]]
        result = grade_task(
            state.store.get("before"), state.store.get("db"), task_, policy_version(meta["drift"])
        )
        return Score(
            value=CORRECT if result.passed else INCORRECT,
            explanation=", ".join(result.failure_tags) or "passed",
            metadata=result.to_dict(),
        )

    return score


@task
def faultline(
    split: str = "dev",
    first: int | None = None,
    drifts: str | None = None,
    notes: str = "stale",
    max_tokens: int = MAX_OUTPUT,
) -> Task:
    """Same settings as the faultline LLM agent: temperature 0.7, one tool call per step,
    and at most 15 model steps (32 messages). Raise max_tokens for reasoning models."""
    return Task(
        dataset=dataset(split, first, drifts),
        solver=faultline_agent(notes),
        scorer=faultline_grader(),
        message_limit=32,
        config=GenerateConfig(temperature=0.7, max_tokens=max_tokens, parallel_tool_calls=False),
    )
