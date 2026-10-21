# Phase 2.5 report: Harbor port

Status: **complete**, on branch `phase2.5/harbor-port`. Work ran on 21 Oct 2026.
**API spend: $0.** Every check uses Harbor's `oracle` and `nop` agents, which call no model.

## Acceptance

| Check (brief, Phase 2.5) | Result |
|---|---|
| Export each task as a Harbor task folder (`task.toml`, `instruction.md`, `environment/Dockerfile`, `tests/test.sh`, `solution/`) | `faultline harbor-export`: one folder per task × drift |
| The container installs faultline and serves the drifted MCP tools over Streamable HTTP | A `tools` compose sidecar serves them: `faultline-server --http --host 0.0.0.0`, named `helpdesk`. The agent's own container deliberately has no faultline (see "Design") |
| `test.sh` runs the state grader and writes the reward | It runs in a separate verifier image on the sidecar's final database and always rewrites `/logs/verifier/reward.txt` |
| `solution/` runs the oracle | `solve.sh` runs faultline's drift-robust oracle against the same MCP endpoint |
| VERIFY the Harbor task format and its MCP configuration | Harbor 0.24.0, task schema 1.4 (details below) |
| No publish to the Harbor registry | Nothing was published or uploaded |

## Results

Exported tasks: the first 14 test tasks (one per template, both domains) under all 13
drifts, 182 Harbor tasks. Run with Harbor 0.24.0, `-e docker`, 8 trials at a time, on
Docker 28.5.1 (Docker Desktop, Windows host, Linux containers).

| Agent | Trials | Reward 1.0 | Reward 0.0 | Errors | Wall time |
|---|---:|---:|---:|---:|---|
| `oracle` (runs `solution/solve.sh`) | 182 | 182 | 0 | 0 | 26 m 19 s |
| `nop` (does nothing) | 182 | 0 | 182 | 0 | 17 m 54 s (in parallel) |

`python -m faultline.harbor check <result.json> <reward>` checks every trial and every
exception. Both jobs pass. [Oracle result](evidence/harbor/oracle-result.json),
[nop result](evidence/harbor/nop-result.json).

One trial (`test-0000`, `rename_param+ambiguous_write`) was inspected by hand:
- **Final database:** exactly one $81.00 refund and a resolved ticket, although the first refund call returned the ambiguous 504.
- **Verifier output:** `grade.json` shows every check passed.

A new CI job repeats this on every pull request. It builds the images, exports one
task per template under `rename_param+ambiguous_write`, and requires reward 1 for the
oracle and reward 0 for `nop`.

## Design

The rule comes from Harbor's adapter-review checklist, §14 "Benchmark vulnerability
check": *"the agent must not be able to (a) see the ground truth, or (b) influence the
pass/fail signal."* Harnesses such as Claude Code have a shell, so the layout enforces
the rule with containers:

| Container | Contains | Agent access |
|---|---|---|
| `main` (built from `environment/Dockerfile`) | `python:3.12-slim` and the harness | Its own container |
| `tools` (compose sidecar) | faultline, the seeded SQLite database, the drifted MCP server | MCP over HTTP only (`http://tools:8765/mcp`) |
| verifier (built from `tests/Dockerfile`, separate mode) | faultline, the grader, the expected outcome, and a copy of the final database | None. It starts after the agent stops |

Each check maps to how it is met:

- **Ground truth.** It sits only in `tests/task.json`. The sidecar's `task.json` holds rows but no answer. A version of this port with faultline in `main` would let an agent regenerate the task and read its expected outcome, so `main` does not have faultline.
- **Reward integrity.** `test.sh` writes 0 before grading. The grader computes the reward from the sidecar's database against `tests/`. Interpreters are invoked by absolute path in the verifier image.
- **Benchmark identity.** The server reports `helpdesk`. `tests/test_harbor.py` checks that the instruction and the agent's Dockerfile contain neither "faultline" nor the drift name.
- **Fresh state.** Each trial gets new containers, so the database and drift counters are new. This is the same guarantee as faultline's runner.

The instruction is the faultline LLM agent's prompt: the domain instructions, the
stale API v1 notes, and the ticket line. So Harbor runs measure the same task.

## A bug the port found

`task.json` is written with sorted keys. For ITSM, that puts `changes` before
`cmdb_items`. Seeding in that order broke a foreign key, so the tools image failed to
build on every ITSM task. The fix: seed tables in schema order. `tests/test_harbor.py`
now runs one refund task, one ITSM task, and one seed task through the oracle over
real Streamable HTTP and grades them.

## What changed

- `faultline/harbor.py`:
  - `export` writes the task folders.
  - Container commands: `seed` (tools image build), `solve` (oracle over Streamable HTTP), `grade` (verifier), and `check` (a job's `result.json`).
- `faultline/cli.py`: `faultline harbor-export --split --first --drifts --wheel --output`.
- `faultline/server.py`: `--host` (bind address) and `--name` (server name shown to clients). The defaults keep the earlier behavior.
- `harbor/Dockerfile`: the base image for the sidecar and the verifier. It installs faultline `--no-deps` plus `mcp==2.3.0`, without LiteLLM. `harbor/README.md` documents usage and the design.
- `tests/test_harbor.py`: 8 tests. They cover the layout, the leak checks, overwrite refusal, a reward on every path, the oracle over HTTP on three tasks, and the job checker.
- CI: a `harbor` job, as above.
- Tests: 455 pass. Ruff is clean.

## Verified on 21 Oct 2026

| Fact | Source | Result |
|---|---|---|
| Harbor version | PyPI | 0.24.0 (5 Oct 2026), Python ≥ 3.12 |
| Task layout and schema | Installed `harbor/models/task/paths.py`, `config.py` | `task.toml`, `instruction.md`, `environment/`, `tests/test.sh`, `solution/solve.sh`; `schema_version = "1.4"` |
| MCP configuration | `MCPServerConfig` | `[[environment.mcp_servers]]` with `name`, `transport` (`stdio`, `sse`, `streamable-http`), `url` or `command` |
| Sidecars | `environments/docker/docker.py` | The task's `environment/docker-compose.yaml` merges over the base compose that builds `main` |
| Sidecar artifacts and separate verifier | `ArtifactConfig.service`, `trial.py`, `artifact_handler.py`, `verifier_mode.py` | Artifacts from a service are re-uploaded into the separate verifier at their source path; a `Dockerfile` in `tests/` makes that verifier image |
| Reward file | `cli/adapter_review.py` checklist | `/logs/verifier/reward.txt` |
| MCP SDK host check | `mcp==2.3.0` `MCPServer.sse_app` / transport security | DNS-rebinding protection turns on only for a localhost bind, so `0.0.0.0` in the sidecar accepts `tools:8765` |

## Not done

- **No paid harness run.** Claude Code, Codex CLI and OpenHands runs need their API keys and a budget. Use `harbor run -a claude-code ...` with the harness's key.
- **Only 182 of the 5,850 possible task × drift folders were run.** The full set exports the same way; at this machine's rate, a full oracle run would take several hours.
- **No publishing.** Nothing was pushed to the Harbor registry or uploaded with `harbor upload`.
