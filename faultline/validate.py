"""Offline gates over whole splits: every scripted agent against every task, in process.

Each episode still gets a fresh database and a fresh server instance. Only the process
boundary is skipped, which makes thousands of free episodes practical.
"""

import tempfile
from collections import Counter
from pathlib import Path

from mcp import Client

from faultline import itsm
from faultline.agents import NEAR_MISSES, TEMPLATE_NEAR_MISSES
from faultline.client import ToolClient
from faultline.db import TABLES, seed_rows, snapshot
from faultline.grader import Grade, grade_task
from faultline.runner import error_name, play, policy_version
from faultline.server import create_server
from faultline.tasks import SPLIT_DRIFTS, Task


async def episode(
    task: Task, drift: str, agent: str, skip: str | None = None, transcript: list | None = None
) -> tuple[Grade, str | None]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "state.sqlite3"
        seed_rows(path, task.schema, task.rows)
        tables = itsm.TABLES if task.domain == "itsm" else TABLES
        before = snapshot(path, tables)
        try:
            async with Client(create_server(path, drift, task.domain), cache=None) as connection:
                await play(
                    agent,
                    ToolClient(connection, transcript if transcript is not None else []),
                    task,
                    skip,
                )
        except Exception as exc:
            # A brittle agent stopping on an error is a result, not a harness failure.
            error = error_name(exc)
        else:
            error = None
        return grade_task(before, path, task, policy_version(drift)), error


def near_misses(task: Task) -> tuple[str, ...]:
    return (
        NEAR_MISSES[task.target] if task.template == "seed" else TEMPLATE_NEAR_MISSES[task.template]
    )


def checks(task: Task) -> list[tuple[str, str, str | None, str, bool]]:
    """(check, agent, skip, drift, must pass) for one task."""
    rows = [("oracle", "oracle", None, d, True) for d in SPLIT_DRIFTS[task.split]]
    rows += [("oracle_idem", "oracle_idem", None, d, True) for d in SPLIT_DRIFTS[task.split]]
    rows += [("reference, baseline", "reference", None, "baseline", True)]
    rows += [
        (f"{a}, baseline", a, None, "baseline", False)
        for a in ("null", "refund_all", "close_all", "resolve_all")
    ]
    rows += [
        (f"near miss: {s}", "oracle", s, "ambiguous_write" if s == "recheck" else "baseline", False)
        for s in near_misses(task)
    ]
    return rows


async def validate(tasks: list[Task]) -> str:
    totals, held = Counter(), Counter()
    failures = []
    for task in tasks:
        for check, agent, skip, drift, must_pass in checks(task):
            result, error = await episode(task, drift, agent, skip)
            totals[(task.domain, check)] += 1
            if result.passed == must_pass:
                held[(task.domain, check)] += 1
            else:
                failures.append(
                    f"- {task.task_id} {task.template} {check} {drift}: "
                    f"{result.failure_tags} {error or ''}"
                )
    splits = sorted({t.split for t in tasks})
    lines = [
        "# faultline offline validation",
        "",
        f"Splits: {', '.join(splits)}; tasks: {len(tasks)}; episodes: {sum(totals.values())}.",
        "Oracle checks run every task under every drift of its split. Gates that must fail",
        "run under baseline; the `recheck` near miss runs under ambiguous_write.",
        "",
        "| Domain | Check | Expected | Episodes | As expected |",
        "|---|---|---|---:|---:|",
    ]
    for (domain, check), n in sorted(totals.items()):
        expected = "pass" if check.startswith(("oracle", "reference")) else "fail"
        lines.append(f"| {domain} | {check} | {expected} | {n} | {held[(domain, check)]} |")
    lines += ["", "## Unexpected results", ""] + (failures or ["None."]) + [""]
    return "\n".join(lines)
