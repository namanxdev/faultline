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

from faultline import agents
from faultline.client import ToolClient
from faultline.db import TICKET_IDS, seed_database, snapshot
from faultline.environment import DRIFTS
from faultline.grader import grade
from faultline.llm import MODEL, Budget, Usage, run_llm
from faultline.report import write_report

AGENTS = ("reference", "null", "refund_all", "close_all", "resolve_all", "llm")


def redact(text: str) -> str:
    for name, value in os.environ.items():
        if len(value) >= 8 and any(
            word in name.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")
        ):
            text = text.replace(json.dumps(value)[1:-1], "[REDACTED]")
            text = text.replace(value, "[REDACTED]")
    return re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[REDACTED]", text)


def write_json(path: Path, value) -> None:
    path.write_text(redact(json.dumps(value, indent=2, sort_keys=True)), encoding="utf-8")


async def run_trial(
    root: Path,
    seed_path: Path,
    agent: str,
    ticket_id: str,
    drift: str,
    trial: int,
    seed: int,
    budget: Budget,
) -> dict:
    episode_id = f"{agent}-{ticket_id}-{drift}-{trial}"
    directory = root / "trials" / episode_id
    directory.mkdir(parents=True)
    db_path = directory / "state.sqlite3"
    shutil.copyfile(seed_path, db_path)
    before = snapshot(db_path)
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
        args=["-m", "faultline.server", "--db", str(db_path.resolve())],
        env=env,
    )
    try:
        async with asyncio.timeout(180):
            # Disable SDK caching: re-reading after a write must observe the database.
            async with Client(params, cache=None, read_timeout_seconds=60) as connection:
                protocol = connection.protocol_version
                client = ToolClient(connection, transcript)
                if agent == "llm":
                    await run_llm(client, ticket_id, seed, budget, usage)
                elif agent in ("reference", "null"):
                    await getattr(agents, agent)(client, ticket_id)
                else:
                    await agents.hack(client, ticket_id, agent)
    except Exception as exc:
        # Do not persist provider exception bodies: they can contain request credentials.
        error = type(exc).__name__
        usage.finish_reason = error
    result = {
        "episode_id": episode_id,
        "agent": agent,
        "ticket_id": ticket_id,
        "drift": drift,
        "trial": trial,
        "seed": seed,
        "protocol_version": protocol,
        "model": MODEL if agent == "llm" else None,
        "usage": asdict(usage),
        "grade": grade(before, db_path, ticket_id).to_dict(),
        "error": error,
        "transcript": str((directory / "transcript.json").relative_to(root)).replace("\\", "/"),
    }
    write_json(directory / "transcript.json", transcript)
    write_json(directory / "episode.json", result)
    return result


async def run(
    output: Path,
    agent: str = "reference",
    drifts: tuple = DRIFTS,
    trials: int = 3,
    concurrency: int = 6,
    seed: int = 1729,
    budget_usd: float = 5.0,
) -> list[dict]:
    if agent not in AGENTS or not drifts or any(d not in DRIFTS for d in drifts):
        raise ValueError("Unknown agent or drift")
    if len(set(drifts)) != len(drifts):
        raise ValueError("Duplicate drifts would overwrite trial artifacts")
    if trials < 1 or concurrency < 1:
        raise ValueError("Trials and concurrency must be positive")
    budget = Budget(budget_usd)
    if agent == "llm" and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Set OPENAI_API_KEY in the environment or local .env before an LLM run")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    seed_path = output / "seed.sqlite3"
    seed_database(seed_path)
    write_json(
        output / "config.json",
        {
            "agent": agent,
            "drifts": drifts,
            "trials": trials,
            "concurrency": concurrency,
            "seed": seed,
            "budget_usd": budget_usd,
            "model": MODEL if agent == "llm" else None,
            "versions": {p: version(p) for p in ("mcp", "litellm")},
            "python": sys.version,
            "temperature": 0.7,
            "max_steps": 15,
        },
    )
    semaphore = asyncio.Semaphore(concurrency)

    async def limited(ticket_id: str, drift: str, trial: int, trial_seed: int):
        async with semaphore:
            result = await run_trial(
                output, seed_path, agent, ticket_id, drift, trial, trial_seed, budget
            )
            # No await between open and close: one event-loop writer at a time.
            with (output / "episodes.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(redact(json.dumps(result, sort_keys=True)) + "\n")
            return result

    jobs = [
        (ticket, drift, trial)
        for ticket in TICKET_IDS
        for drift in drifts
        for trial in range(trials)
    ]
    results = await asyncio.gather(
        *(limited(*job, seed + index * 100) for index, job in enumerate(jobs))
    )
    # Stable final ordering makes report reproduction and comparisons easier.
    (output / "episodes.jsonl").write_text(
        "".join(redact(json.dumps(row, sort_keys=True)) + "\n" for row in results),
        encoding="utf-8",
    )
    write_report(output / "episodes.jsonl")
    return results
