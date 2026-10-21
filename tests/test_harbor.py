import asyncio
import json
import os
import socket
import subprocess
import sys
import tomllib

import httpx
import pytest
from mcp import Client

from faultline.harbor import SERVER_NAME, export, grade_files, seed, solve
from faultline.tasks import load

TEST = load("test")
ITEMS = [
    (TEST[0], "rename_param+ambiguous_write"),
    (TEST[12], "baseline"),
    (load("seed")[5], "baseline"),
]


@pytest.fixture
def exported(tmp_path):
    wheel = tmp_path / "faultline-0.1.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel")
    return export(ITEMS, tmp_path / "tasks", wheel)


def test_export_writes_the_harbor_layout(exported):
    for root in exported:
        for path in (
            "task.toml",
            "instruction.md",
            "environment/Dockerfile",
            "environment/docker-compose.yaml",
            "environment/tools/Dockerfile",
            "environment/tools/task.json",
            "tests/Dockerfile",
            "tests/test.sh",
            "tests/task.json",
            "solution/solve.sh",
        ):
            assert (root / path).is_file(), path
        config = tomllib.loads((root / "task.toml").read_text(encoding="utf-8"))
        assert config["verifier"]["environment_mode"] == "separate"
        assert config["artifacts"] == [{"source": "/data/state.sqlite3", "service": "tools"}]
        server = config["environment"]["mcp_servers"][0]
        assert server == {
            "name": SERVER_NAME,
            "transport": "streamable-http",
            "url": "http://tools:8765/mcp",
        }
        assert b"\r\n" not in (root / "tests" / "test.sh").read_bytes()


def test_agent_visible_files_hold_no_answer_or_benchmark_identity(exported):
    for (task, drift), root in zip(ITEMS, exported, strict=True):
        # The agent sees the instruction and its own container, built from these files.
        visible = [root / "instruction.md", root / "environment" / "Dockerfile"]
        text = "\n".join(p.read_text(encoding="utf-8") for p in visible).lower()
        assert "faultline" not in text and drift not in text and "expected" not in text
        assert task.target in (root / "instruction.md").read_text(encoding="utf-8")
        # The sidecar gets rows but no answer; only the separate verifier gets the answer.
        tools = json.loads((root / "environment/tools/task.json").read_text(encoding="utf-8"))
        assert "expected" not in tools
        tests = json.loads((root / "tests/task.json").read_text(encoding="utf-8"))
        assert tests["expected"] == task.expected["3"]
        assert "COPY" not in (root / "environment" / "Dockerfile").read_text(encoding="utf-8")


def test_export_refuses_to_overwrite(exported, tmp_path):
    with pytest.raises(FileExistsError):
        export(ITEMS, tmp_path / "tasks", tmp_path / "faultline-0.1.0-py3-none-any.whl")


def test_grading_writes_a_reward_on_every_path(exported, tmp_path):
    root = exported[0]
    db = tmp_path / "state.sqlite3"
    seed(root / "environment/tools/task.json", db)
    assert grade_files(root / "tests/task.json", db, tmp_path / "v") is False
    assert (tmp_path / "v" / "reward.txt").read_text() == "0\n"
    assert (
        grade_files(root / "tests/task.json", tmp_path / "missing.sqlite3", tmp_path / "m") is False
    )
    assert "missing" in (tmp_path / "m" / "grade.json").read_text()


@pytest.mark.parametrize("index", range(len(ITEMS)))
async def test_oracle_solves_over_streamable_http_and_the_grade_is_one(exported, tmp_path, index):
    task, drift = ITEMS[index]
    root = exported[index]
    db = tmp_path / "state.sqlite3"
    seed(root / "environment/tools/task.json", db)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    args = ["--db", str(db), "--drift", drift, "--domain", task.domain, "--name", SERVER_NAME]
    process = subprocess.Popen(
        [sys.executable, "-m", "faultline.server", *args, "--http", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        async with asyncio.timeout(60), httpx.AsyncClient() as http:
            while True:
                assert process.poll() is None
                try:
                    await http.get(url)
                    break
                except httpx.ConnectError:
                    await asyncio.sleep(0.1)
        async with Client(url, cache=None) as connection:
            assert connection.server_info.name == SERVER_NAME
        await solve(url, task.target, task.domain)
    finally:
        process.terminate()
        await asyncio.to_thread(process.wait, timeout=10)
    assert grade_files(root / "tests/task.json", db, tmp_path / "v") is True
    assert (tmp_path / "v" / "reward.txt").read_text() == "1\n"


def job(tmp_path, rewards, errored=0, exceptions=None):
    stats = {
        "n_errored_trials": errored,
        "evals": {
            "oracle__tasks": {
                "exception_stats": exceptions or {},
                "reward_stats": {"reward": {str(v): [f"t{i}"] for i, v in enumerate(rewards)}},
            }
        },
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps({"n_total_trials": len(rewards), "stats": stats}))
    return path


def test_check_job_flags_any_other_reward_or_error(tmp_path):
    from faultline.harbor import check_job

    assert check_job(job(tmp_path, [1.0, 1.0]), 1.0) == (2, [])
    assert check_job(job(tmp_path, [1.0, 0.0]), 1.0)[1] == ["t1: reward 0.0"]
    total, problems = check_job(job(tmp_path, [0.0], 1, {"BuildError": ["t9"]}), 0.0)
    assert problems == ["1 errored trials", "oracle__tasks: BuildError"]
