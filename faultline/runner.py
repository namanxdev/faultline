"""One fresh database copy and MCP subprocess per trial; six trials at a time."""

import asyncio
import json
import os
import re
import shutil
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

from mcp import Client, StdioServerParameters

from faultline import agents, itsm
from faultline.client import ToolClient
from faultline.db import TABLES, seed_rows, snapshot
from faultline.drifts import DRIFTS, HELD_OUT
from faultline.grader import grade_task
from faultline.llm import (
    DEFAULT_MODEL,
    MODELS,
    NOTES,
    PHASE_CAPS,
    Budget,
    Ledger,
    Usage,
    run_llm,
)
from faultline.report import write_report
from faultline.tasks import SPLIT_DRIFTS, SPLITS, Task, load

AGENTS = (
    "reference",
    "oracle",
    "oracle_idem",
    "null",
    "refund_all",
    "close_all",
    "resolve_all",
    "llm",
)


def policy_version(drift: str) -> int:
    return 4 if "policy_v4" in drift.split("+") else 3


async def play(agent: str, client: ToolClient, task: Task, skip: str | None = None) -> None:
    """Run one scripted agent on one task. `skip` turns the oracle into a near miss."""
    is_itsm = task.domain == "itsm"
    if agent in ("oracle", "oracle_idem"):
        solve = agents.itsm_oracle if is_itsm else agents.oracle
        await solve(client, task.target, skip, agent == "oracle_idem")
    elif agent == "reference":
        await (agents.itsm_reference if is_itsm else agents.reference)(client, task.target)
    elif agent == "null":
        await agents.null(client, task.target)
    else:
        await agents.hack(client, task.target, agent, task.targets)


def redact(text: str) -> str:
    for name, value in os.environ.items():
        if len(value) >= 8 and any(
            word in name.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")
        ):
            text = text.replace(json.dumps(value)[1:-1], "[REDACTED]")
            text = text.replace(value, "[REDACTED]")
    return re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[REDACTED]", text)


def error_name(exc: BaseException) -> str:
    # The SDK wraps agent errors in task-group ExceptionGroups; report the leaf cause.
    while isinstance(exc, BaseExceptionGroup) and len(exc.exceptions) == 1:
        exc = exc.exceptions[0]
    if isinstance(exc, BaseExceptionGroup):
        return "+".join(sorted({error_name(e) for e in exc.exceptions}))
    return type(exc).__name__


def write_json(path: Path, value) -> None:
    path.write_text(redact(json.dumps(value, indent=2, sort_keys=True)), encoding="utf-8")


async def run_trial(
    root: Path,
    seed_path: Path,
    agent: str,
    task: Task,
    drift: str,
    trial: int,
    seed: int,
    budget: Budget,
    model: str | None,
    notes: str | None,
) -> dict:
    episode_id = f"{agent}-{task.task_id}-{drift}-{trial}"
    directory = root / "trials" / episode_id
    directory.mkdir(parents=True)
    db_path = directory / "state.sqlite3"
    shutil.copyfile(seed_path, db_path)
    tables = itsm.TABLES if task.domain == "itsm" else TABLES
    before = snapshot(db_path, tables)
    transcript = []
    usage = Usage()
    error = None
    protocol = None
    # The tool server does not need provider credentials.
    env = {
        k: v
        for k, v in os.environ.items()
        if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PYTHONPATH"}
    }
    env.update({"DRIFT": drift, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"})
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "faultline.server", "--db", str(db_path.resolve()), "--domain", task.domain],
        env=env,
    )
    try:
        async with asyncio.timeout(180):
            # Disable SDK caching: re-reading after a write must observe the database.
            async with Client(params, cache=None, read_timeout_seconds=60) as connection:
                protocol = connection.protocol_version
                client = ToolClient(connection, transcript)
                if agent == "llm":
                    await run_llm(
                        client, task.target, seed, budget, usage, model, notes, task.domain
                    )
                else:
                    await play(agent, client, task)
    except Exception as exc:
        # Do not persist provider exception bodies: they can contain request credentials.
        error = error_name(exc)
        usage.finish_reason = error
    result = {
        "episode_id": episode_id,
        "agent": agent,
        "ticket_id": task.target,
        "task_id": task.task_id,
        "domain": task.domain,
        "template": task.template,
        "split": task.split,
        "policy_version": policy_version(drift),
        "drift": drift,
        "trial": trial,
        "seed": seed,
        "protocol_version": protocol,
        "model": model,
        "notes": notes,
        "usage": asdict(usage),
        "grade": grade_task(before, db_path, task, policy_version(drift)).to_dict(),
        "error": error,
        "transcript": str((directory / "transcript.json").relative_to(root)).replace("\\", "/"),
    }
    write_json(directory / "transcript.json", transcript)
    write_json(directory / "episode.json", result)
    return result


async def run(
    output: Path,
    agent: str = "reference",
    drifts: tuple | None = None,
    trials: int = 3,
    concurrency: int = 6,
    seed: int = 1729,
    budget_usd: float = 5.0,
    model: str = DEFAULT_MODEL,
    phase: int = 1,
    ledger: Path = Path("runs/spend-ledger.jsonl"),
    notes: str = "stale",
    split: str = "seed",
    items: list[tuple[Task, str]] | None = None,
) -> list[dict]:
    if split != "seed" and split not in SPLITS:
        raise ValueError(f"Unknown split {split}")
    drifts = tuple(drifts or SPLIT_DRIFTS[split])
    if agent not in AGENTS or not drifts or any(d not in DRIFTS for d in drifts):
        raise ValueError("Unknown agent or drift")
    if split == "train" and set(drifts) & set(HELD_OUT):
        raise ValueError("Held-out drift combinations never run on the train split")
    if len(set(drifts)) != len(drifts):
        raise ValueError("Duplicate drifts would overwrite trial artifacts")
    if trials < 1 or concurrency < 1:
        raise ValueError("Trials and concurrency must be positive")
    if notes not in NOTES:
        raise ValueError(f"Unknown notes variant {notes}")
    model = model if agent == "llm" else None
    notes = notes if agent == "llm" else None
    if model is not None:
        if model not in MODELS:
            raise ValueError(f"Unknown model {model}; add it to MODELS with verified prices")
        if not os.environ.get(MODELS[model].key_env):
            raise ValueError(
                f"Set {MODELS[model].key_env} in the environment or local .env before an LLM run"
            )
        spend = Ledger(ledger.resolve(), phase)
    budget = Budget(budget_usd, PHASE_CAPS[phase] if model else PHASE_CAPS[1])
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    if model is not None:
        try:
            spend.reserve(str(output), budget_usd)
        except ValueError:
            output.rmdir()
            raise
    tasks = load(split)
    items = items or [(task, drift) for task in tasks for drift in drifts]
    seeds = {}
    for task, _ in items:
        if task.task_id not in seeds:
            # Seeded tasks share one database; generated tasks each have their own.
            seeded = task.split == "seed"
            path = output / ("seed.sqlite3" if seeded else f"seeds/{task.task_id}.sqlite3")
            if not path.exists():
                seed_rows(path, task.schema, task.rows)
            seeds[task.task_id] = path
    write_json(
        output / "config.json",
        {
            "agent": agent,
            "drifts": drifts,
            "split": split,
            "items": len(items),
            "trials": trials,
            "concurrency": concurrency,
            "seed": seed,
            "budget_usd": budget_usd,
            "model": model,
            "provider_params": MODELS[model].params if model else None,
            "notes": notes,
            "phase": phase,
            "versions": {p: version(p) for p in ("mcp", "litellm")},
            "python": sys.version,
            "temperature": 0.7,
            "max_steps": 15,
        },
    )
    semaphore = asyncio.Semaphore(concurrency)

    async def limited(task: Task, drift: str, trial: int, trial_seed: int):
        async with semaphore:
            result = await run_trial(
                output,
                seeds[task.task_id],
                agent,
                task,
                drift,
                trial,
                trial_seed,
                budget,
                model,
                notes,
            )
            # No await between open and close: one event-loop writer at a time.
            with (output / "episodes.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(redact(json.dumps(result, sort_keys=True)) + "\n")
            return result

    jobs = [(task, drift, trial) for task, drift in items for trial in range(trials)]
    try:
        results = await asyncio.gather(
            *(limited(*job, seed + index * 100) for index, job in enumerate(jobs))
        )
    finally:
        if model is not None:
            # Unsettled reservations may have been billed; count them as spent.
            spend.settle(str(output), float(budget.committed))
    # Stable final ordering makes report reproduction and comparisons easier.
    (output / "episodes.jsonl").write_text(
        "".join(redact(json.dumps(row, sort_keys=True)) + "\n" for row in results),
        encoding="utf-8",
    )
    write_report(output / "episodes.jsonl")
    return results
