# faultline on Harbor

[Harbor](https://pypi.org/project/harbor/) (0.24.0) runs agent harnesses, such as Claude
Code or Codex CLI, against sandboxed tasks. `faultline harbor-export` writes each
faultline task under each drift as one Harbor task folder.

## Build and run

From the repository root, with Docker running:

```sh
uv build --wheel
docker build -t faultline-harbor:0.1.0 -f harbor/Dockerfile .
uv run faultline harbor-export --split test --first 14 --output runs/harbor-tasks
harbor run -p runs/harbor-tasks -a oracle -e docker -n 8   # every reward must be 1.0
harbor run -p runs/harbor-tasks -a nop -e docker -n 8      # every reward must be 0.0
```

Install Harbor in its own environment (Python 3.12 or later), for example
`uv tool install harbor==0.24.0`. To evaluate a harness, pass `-a claude-code` or
`-a codex` with that harness's API key. Those runs are paid.

## Task layout

```text
<task>/
├── task.toml                   # MCP server, sidecar artifact, separate verifier
├── instruction.md              # the ticket prompt, as the faultline LLM agent gets it
├── environment/
│   ├── Dockerfile              # main: the agent's container (python:3.12-slim, nothing else)
│   ├── docker-compose.yaml     # adds the tools sidecar; main waits until it is healthy
│   └── tools/                  # faultline image + seeded database + drifted MCP server
├── tests/                      # a separate verifier image: grader + expected outcome
└── solution/solve.sh           # the drift-robust oracle, against the same MCP endpoint
```

## Why the answer stays out of reach

Harbor's adapter-review checklist (section 14, benchmark vulnerability) requires that
an agent cannot see the ground truth or influence the reward. This layout enforces that:

- **The agent's container holds no faultline code and no database.** Harnesses have a shell. With faultline installed, an agent could regenerate the task and read its expected outcome. With the database present, it could edit rows directly. Here the only way to change state is the MCP endpoint `http://tools:8765/mcp`.
- **The sidecar's `task.json` holds rows only.** The expected outcome exists only in `tests/`, which Harbor builds into a separate verifier image after the agent stops.
- **The verifier grades a copy of `/data/state.sqlite3`** collected from the sidecar (a `service = "tools"` artifact). `test.sh` writes a reward of 0 first, then the grader's result. It never trusts an existing file.
- **The MCP server identifies itself as `helpdesk`.** The instruction and the agent's container do not name the benchmark or the drift (`tests/test_harbor.py` checks this).

Each trial gets fresh containers. So, as in faultline's own runner, every trial has a
fresh database and fresh drift counters.
