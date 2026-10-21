"""Export faultline tasks as Harbor task folders, plus the commands those folders run.

One Harbor task is one faultline task under one drift. The layout keeps every answer
out of the agent's reach:

- `main` (the agent's container) has no faultline code and no database.
- `tools` (a compose sidecar) owns the seeded database and serves the drifted tools
  over Streamable HTTP. The agent changes state only through MCP.
- `tests/` builds a separate verifier image with the grader and the expected outcome.
  Harbor copies the final database out of `tools` into it after the agent stops.
- `solution/` runs the drift-robust oracle against the same MCP endpoint.

    python -m faultline.harbor seed <task.json> <db>        # in the tools image build
    python -m faultline.harbor solve <url> <target> <domain>  # the oracle (solution/)
    python -m faultline.harbor grade <task.json> <db> <dir>  # the verifier (tests/)
    python -m faultline.harbor check <job>/result.json 1.0   # every trial got this reward
"""

import argparse
import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from faultline import __version__, agents, itsm
from faultline.db import SCHEMA, TABLES, seed_rows, snapshot
from faultline.grader import grade, grade_itsm
from faultline.llm import system_prompt, task_prompt
from faultline.runner import policy_version
from faultline.tasks import Task

IMAGE = f"faultline-harbor:{__version__}"
SERVER_NAME = "helpdesk"  # Neutral: the agent must not learn which benchmark this is.
PORT = 8765


def _toml_str(value: str) -> str:
    return json.dumps(value)


def task_toml(task: Task, drift: str, name: str) -> str:
    return f"""schema_version = "1.4"
artifacts = [{{ source = "/data/state.sqlite3", service = "tools" }}]

[task]
name = {_toml_str(name)}
description = {_toml_str(f"faultline {task.domain} task ({task.template}) under {drift}")}
authors = [{{ name = "Naman Gupta" }}]
keywords = ["faultline", "mcp", "tool-drift", {_toml_str(task.domain)}]

[metadata]
faultline_version = {_toml_str(__version__)}
task_id = {_toml_str(task.task_id)}
split = {_toml_str(task.split)}
template = {_toml_str(task.template)}
domain = {_toml_str(task.domain)}
drift = {_toml_str(drift)}

[agent]
timeout_sec = 900

[environment]
build_timeout_sec = 900
cpus = 1
memory_mb = 2048

[[environment.mcp_servers]]
name = {_toml_str(SERVER_NAME)}
transport = "streamable-http"
url = "http://tools:{PORT}/mcp"

[verifier]
timeout_sec = 300
environment_mode = "separate"
"""


MAIN_DOCKERFILE = """FROM python:3.12-slim
WORKDIR /workspace
"""

PROBE = f"import socket; socket.create_connection(('127.0.0.1', {PORT}), 2)"
COMPOSE = f"""services:
  main:
    depends_on:
      tools:
        condition: service_healthy
  tools:
    build:
      context: ./tools
    healthcheck:
      test: ["CMD", "python", "-c", "{PROBE}"]
      interval: 2s
      timeout: 5s
      retries: 60
"""


def tools_dockerfile(task: Task, drift: str) -> str:
    return f"""FROM {IMAGE}
COPY task.json /task/task.json
RUN python -m faultline.harbor seed /task/task.json /data/state.sqlite3
CMD ["faultline-server", "--http", "--host", "0.0.0.0", "--port", "{PORT}", \\
     "--db", "/data/state.sqlite3", "--drift", "{drift}", "--domain", "{task.domain}", \\
     "--name", "{SERVER_NAME}"]
"""


TESTS_DOCKERFILE = f"""FROM {IMAGE}
COPY . /tests/
RUN chmod +x /tests/test.sh
"""

TEST_SH = """#!/bin/sh
# Always rewrite the reward, whatever the agent left behind.
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
/usr/local/bin/python -m faultline.harbor grade /tests/task.json /data/state.sqlite3 /logs/verifier
"""


def solve_sh(task: Task) -> str:
    return f"""#!/bin/sh
set -e
# The oracle needs the faultline wheel shipped beside this script and an MCP client.
python3 -m pip install --quiet --no-deps /solution/faultline-{__version__}-py3-none-any.whl
python3 -m pip install --quiet "mcp==2.3.0"
python3 -m faultline.harbor solve http://tools:{PORT}/mcp {task.target} {task.domain}
"""


def instruction(task: Task) -> str:
    return f"{system_prompt('stale', task.domain)}\n{task_prompt(task.target)}\n"


def export(items: list[tuple[Task, str]], output: Path, wheel: Path) -> list[Path]:
    """Write one Harbor task folder per (task, drift). Refuses to overwrite."""
    output.mkdir(parents=True, exist_ok=False)
    written = []
    for task, drift in items:
        name = f"faultline/{task.task_id}-{drift.replace('+', '-')}"
        root = output / name.split("/")[1]
        (root / "environment" / "tools").mkdir(parents=True)
        (root / "tests").mkdir()
        (root / "solution").mkdir()
        (root / "task.toml").write_text(task_toml(task, drift, name), encoding="utf-8")
        (root / "instruction.md").write_text(instruction(task), encoding="utf-8")
        (root / "environment" / "Dockerfile").write_text(MAIN_DOCKERFILE, encoding="utf-8")
        (root / "environment" / "docker-compose.yaml").write_text(COMPOSE, encoding="utf-8")
        tools = root / "environment" / "tools"
        (tools / "Dockerfile").write_text(tools_dockerfile(task, drift), encoding="utf-8")
        _write_json(tools / "task.json", {"domain": task.domain, "rows": task.rows})
        expected = task.expected[str(policy_version(drift))]
        _write_json(
            root / "tests" / "task.json",
            {"domain": task.domain, "target": task.target, "rows": task.rows, "expected": expected}
            | {"seed_task": task.template == "seed"},
        )
        (root / "tests" / "Dockerfile").write_text(TESTS_DOCKERFILE, encoding="utf-8")
        _write_script(root / "tests" / "test.sh", TEST_SH)
        _write_script(root / "solution" / "solve.sh", solve_sh(task))
        shutil.copyfile(wheel, root / "solution" / wheel.name)
        written.append(root)
    return written


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=1, sort_keys=True), encoding="utf-8")


def _write_script(path: Path, text: str) -> None:
    path.write_bytes(text.encode())  # LF line endings, also on Windows hosts.


def _ordered(data: dict) -> tuple[str, tuple, dict]:
    """Schema, tables, and rows in foreign-key order (the JSON file sorts its keys)."""
    schema, tables = (SCHEMA, TABLES) if data["domain"] == "refund" else (itsm.SCHEMA, itsm.TABLES)
    return schema, tables, {t: data["rows"][t] for t in tables if t in data["rows"]}


def seed(task_json: Path, db: Path) -> None:
    schema, _, rows = _ordered(json.loads(task_json.read_text(encoding="utf-8")))
    seed_rows(db, schema, rows)


async def solve(url: str, target: str, domain: str) -> None:
    from mcp import Client

    from faultline.client import ToolClient

    async with Client(url, cache=None) as connection:
        client = ToolClient(connection, [])
        await (agents.itsm_oracle if domain == "itsm" else agents.oracle)(client, target)


def grade_files(task_json: Path, db: Path, out: Path) -> bool:
    """Grade the final database; write reward.txt (1 or 0) and grade.json."""
    data = json.loads(task_json.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    passed, details = False, {"error": "final database missing"}
    if db.is_file():
        schema, tables, rows = _ordered(data)
        fresh = Path(tempfile.mkdtemp()) / "seed.sqlite3"
        seed_rows(fresh, schema, rows)
        before = snapshot(fresh, tables)
        if data["domain"] == "itsm":
            result = grade_itsm(before, db, data["target"], data["expected"])
        else:
            expected = None if data["seed_task"] else data["expected"]
            result = grade(before, db, data["target"], expected)
        passed, details = result.passed, result.to_dict()
    (out / "reward.txt").write_text("1\n" if passed else "0\n", encoding="utf-8")
    _write_json(out / "grade.json", details)
    return passed


def check_job(result_json: Path, reward: float) -> tuple[int, list[str]]:
    """Trials in a Harbor job, and every problem: errors, or any other reward."""
    result = json.loads(result_json.read_text(encoding="utf-8"))
    stats = result["stats"]
    problems = [f"{stats['n_errored_trials']} errored trials"] if stats["n_errored_trials"] else []
    for name, run in stats["evals"].items():
        problems += [f"{name}: {e}" for e in run["exception_stats"]]
        for value, trials in run["reward_stats"].get("reward", {}).items():
            if float(value) != reward:
                problems += [f"{t}: reward {value}" for t in trials]
    return result["n_total_trials"], problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    cmd = commands.add_parser("seed")
    cmd.add_argument("task_json", type=Path)
    cmd.add_argument("db", type=Path)
    cmd = commands.add_parser("solve")
    cmd.add_argument("url")
    cmd.add_argument("target")
    cmd.add_argument("domain", choices=["refund", "itsm"])
    cmd = commands.add_parser("check")
    cmd.add_argument("result_json", type=Path)
    cmd.add_argument("reward", type=float)
    cmd = commands.add_parser("grade")
    cmd.add_argument("task_json", type=Path)
    cmd.add_argument("db", type=Path)
    cmd.add_argument("out", type=Path)
    args = parser.parse_args()
    if args.command == "seed":
        seed(args.task_json, args.db)
    elif args.command == "solve":
        asyncio.run(solve(args.url, args.target, args.domain))
    elif args.command == "check":
        total, problems = check_job(args.result_json, args.reward)
        print(f"{total} trials; {len(problems)} problems", *problems, sep="\n")
        if problems or not total:
            raise SystemExit(1)
    else:
        print("reward", int(grade_files(args.task_json, args.db, args.out)))


if __name__ == "__main__":
    main()
