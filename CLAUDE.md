# faultline

An RL training and evaluation environment for tool-using agents whose MCP tools drift
during work. `PROJECT.md` (local only, git-ignored) is the build brief and the source of truth for phases,
acceptance checks, and budgets. Read it before starting phase work.

## Commands

```sh
uv sync --locked                     # install (Python 3.11+, .venv)
uv run pytest -q                     # all tests; no network or API keys needed
uv run ruff check . && uv run ruff format --check .
uv run faultline run --agent oracle --output runs/<new-dir>      # offline, free
uv run faultline run --agent llm --budget-usd 5 --output runs/<new-dir>  # PAID
uv run faultline report runs/<dir>/episodes.jsonl                # regenerate report
uv run faultline validate --output runs/<new-dir>/validation.md  # all gates, offline
uv run faultline-server --db <db> [--drift rename_param] [--http --port 8765]
uv run inspect eval faultline/inspect_task.py -T split=dev --model mockllm/model  # free check
```

Run all three checks (pytest, ruff check, ruff format --check) before every commit.
CI runs them on Ubuntu and Windows, Python 3.11 and 3.12.

## Layout

- `faultline/db.py`: refund schema and seed fixture; money is integer cents, decimal strings on the wire.
- `faultline/toolspec.py`: tools as data (`ToolSpec`, `Param`); drifts rewrite them.
- `faultline/environment.py`: the drift-aware `Tools` engine and the refund domain.
  The server is deliberately permissive.
- `faultline/itsm.py`: the ITSM domain (incidents, changes, approvals, CMDB items).
- `faultline/drifts/`: one module per perturbation, each with a `rationale`.
  `combined.py` lists pairs; `HELD_OUT` pairs never run on train.
- `faultline/server.py`: official MCP SDK v2 (`MCPServer`), built from specs; stdio and HTTP.
- `faultline/tasks.py`: seed tasks and procedural splits (train 300, dev 50, test 100).
  Expected outcomes come from the policy text, not from the agents.
- `faultline/grader.py`: judges final DB state only (`grade`, `grade_itsm`, `grade_task`).
- `faultline/agents.py`: `reference` (brittle by design), `oracle` and `itsm_oracle`
  (must solve every task × drift), near misses via `skip`, `null`, and blanket hacks.
- `faultline/validate.py`: offline gates over whole splits (`faultline validate`).
- `faultline/calibrate.py`: tags template × drift cells; filters train.
- `faultline/rewards.py`: optional bounded shaping on top of the 0/1 grade.
- `faultline/inspect_task.py`: Inspect task; tools are the faultline MCP server over stdio.
- `environments/faultline_vf/`: verifiers 0.4 taskset, its own package and lock
  (overrides mcp to 2.0.0; Linux only, verifiers imports fcntl). Test it in WSL or CI.
- `faultline/harbor.py` + `harbor/`: Harbor export (`faultline harbor-export`), sidecar MCP
  server, separate verifier. Rebuild `faultline-harbor:<version>` after code changes.
- `faultline/llm.py`: model registry (`MODELS`), prompts, budget, phase spend ledger.
- `faultline/runner.py`: fresh DB copy and fresh server process per trial.
- `docs/evidence/`: checked-in results; each `report.md` must regenerate byte-for-byte.

## Hard rules (from the brief)

- One branch and one PR per phase. Never push to `main`. GitHub rulesets enforce this:
  `main` needs a PR with all 6 CI checks passing (no force push, no deletion), and `v*`
  tags cannot be moved or deleted. If you add a CI job, add it to the `protect main` ruleset. Merge a phase PR only after
  every acceptance check in `PROJECT.md` passes, including paid runs.
- Never spend API or GPU money beyond the phase cap, and never start a paid run
  without Naman's OK. Caps live in `PHASE_CAPS`; the ledger enforces them across runs.
- Never publish to PyPI, the Environments Hub, or the Harbor registry without Naman's OK.
- The grader never reads the transcript to decide pass/fail.
- Every number in README or docs must come from a recorded run. Mark unbuilt
  features as *planned*. No claim the results do not support.
- **VERIFY** SDK, provider, and paper facts against live docs before writing code or
  claims. Record what you checked in the phase report.
- No secrets in the repo or transcripts. Keys only via env or the ignored `.env`.
- No Infradock code, data, names, or results anywhere.

## Project conventions

- Plain Python, small modules, every module tested. Match the existing terse style.
- A new model needs a `MODELS` entry with verified prices, its key variable, and
  routing. OpenRouter entries pin one provider (`only`, `allow_fallbacks: false`).
- Agents must use only what the MCP API exposes. They must never read `DRIFT`.
- Run outputs go in a new `runs/<dir>`. Runs refuse to overwrite, and `runs/` is git-ignored.
- End-of-phase docs: `docs/REPORT-phaseN.md` (committed) and `docs/LEARN-phaseN.md`
  (local only, git-ignored; ASD-STE100 style, a Mermaid diagram, 3 hard decisions,
  5 interview questions with answers). Never commit `PROJECT.md` or `LEARN` files.
- Stage files explicitly; don't `git add -A` over untracked user files.

---

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

State your assumptions explicitly. If uncertain, ask.

If multiple interpretations exist, present them - don't pick silently.

If a simpler approach exists, say so. Push back when warranted.

If something is unclear, stop. Name what's confusing. Ask.

2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

No features beyond what was asked.

No abstractions for single-use code.

No "flexibility" or "configurability" that wasn't requested.

No error handling for impossible scenarios.

If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:

Don't "improve" adjacent code, comments, or formatting.

Don't refactor things that aren't broken.

Match existing style, even if you'd do it differently.

If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

Remove imports/variables/functions that YOUR changes made unused.

Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

"Add validation" → "Write tests for invalid inputs, then make them pass"

"Fix the bug" → "Write a test that reproduces it, then make it pass"

"Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
