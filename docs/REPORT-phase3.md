# Phase 3 report

Status: **complete**, on branch `phase3/ecosystem-ports`. Work ran on 21 Oct 2026.
Naman set the Phase 3 API budget to **US$5** (the brief said $25) and asked for the
cheapest models that perform well, picked from what OpenRouter currently serves.

## Acceptance

| Check (PROJECT.md §2, Phase 3) | Result |
|---|---|
| verifiers: VERIFY the API, wrap faultline, reward = grader score | verifiers 0.4.0 (v1 API: `Taskset`, `Task`, `Toolset`, `@vf.reward`), in `environments/faultline_vf` |
| Optional shaping that can never let a hack beat a correct solution, with a test | `faultline/rewards.py`: the shaping term stays in [−0.2, +0.1]. Tested with random call sequences and with real oracle, hack, null, and near-miss episodes under all 13 drifts |
| Run `prime env` validation locally; no Hub push | `prime` 0.17.0 has no local validate command (only hub commands). Its verifiers equivalent passed: `vf-validate`, gold and noop, 26/26. Nothing was pushed |
| Inspect task: a solver with the MCP tools, a scorer that wraps the grader | `faultline/inspect_task.py`: `mcp_server_stdio` with the faultline server, and `grade_task` as the scorer |
| Eval: at least 3 models (1 frontier API, 2 open) on the test split across all drifts | Claude Haiku 5.5 (Anthropic), MiMo-V2.6-Flash and GLM-5.3-Flash (open weights). The first 42 of 100 test tasks (3 per template), all 13 drifts, k=2 |
| Report success, pass@k, pass^k, cost and tokens per task, failure tags | §3 |
| Spend within the cap | **$4.0818 of $5** |

Two deviations from the brief, both forced by the $5 cap:
1. **The "frontier API model" is the cheap tier of a frontier lab.** Claude Haiku 5.5 is the current generation, but it is not a top-tier model. Top-tier models such as Claude Sonnet 5.5 cost 20 times as much per token. The full grid on one of them would cost about $41.
2. **42 of the 100 test tasks were run, not all 100.** I chose k=2 on 42 tasks over k=1 on 100 so that pass^k exists for every cell. The 42 tasks are the split's first 42, which cover each of the 14 templates exactly 3 times, because the generator interleaves templates.

## 1. Choosing models

**Verified on 21 Oct 2026:**
- The OpenRouter catalog (`/api/v1/models`) listed 468 models.
- The provider endpoints came from `/api/v1/models/<id>/endpoints`.
- Tool-use quality came from OpenRouter's own τ²-bench airline leaderboard, last run 20 Oct 2026. It measures multi-step tool calls on OpenRouter's own endpoints.

| Model | Open weights | τ²-bench accuracy | τ² cost/task | Pinned provider | Price in / out per M |
|---|---|---:|---:|---|---|
| Claude Haiku 5.5 | No | 76.0% | $0.011 | Anthropic | $0.10 / $0.50 |
| MiMo-V2.6-Flash | Yes (`XiaomiMiMo/MiMo-V2.6-Flash-RL`) | 78.7% | $0.015 | Xiaomi (fp8) | $0.14 / $0.28 |
| GLM-5.3-Flash | Yes (`zai-org/GLM-5.3-Flash`) | 75.9% | $0.007 | Z.AI (fp8) | $0.15 / $0.50 |
| DeepSeek V4.1 Flash 1017 | Yes | 77.3% | $0.026 | DeepSeek | $0.15 / $0.60 |

Each model was the best value in its group: accuracy within 4.3 points of the top of
the board (80.2%), at a few cents per task. A first-party provider is pinned where
one exists, and fallbacks are disabled.

Smoke tests (6 seed tasks, baseline): Haiku, MiMo, and GLM each passed 6/6 with no errors.
DeepSeek returned `NotFoundError` on every request, probably because of the account's
data-policy filter. It was dropped. Its $0.0081 reservation stays counted as spent,
which overstates spend.
[Smoke evidence](evidence/smoke-phase3/).

**A harness change, made before any result was used.** In the first MiMo run, 13 of
the first 201 episodes stopped at the 512-token output cap mid-answer, and all 13
failed. Reasoning models spend output tokens on reasoning, so that cap measured the
harness, not the model. I stopped the run ($0.103 billed, kept in the ledger and in
[evidence](evidence/eval-mimo-aborted-512tok/report.md)). Phase 3 registry entries now
set `max_output = 2048`. The Phase 1 and 2 models keep 512, so their runs do not change.

## 2. Ecosystem ports

### verifiers (Prime Intellect)

`environments/faultline_vf` is a standalone package, as the verifiers docs prescribe:

- **Task.** `FaultlineTask` is one faultline task under one drift. `setup` seeds a fresh SQLite file and stores its path in rollout state. The `@vf.reward solved` hook returns the state grade of that file, plus optional shaping when `--env.taskset.task.shaped true` is set.
- **Toolset.** `FaultlineToolset` runs as one MCP server process per rollout. `setup_task` builds the drifted tool service, and `register` publishes faultline's spec-built tools under their bare names. Descriptions are re-read on every `tools/list` request, so `description_drift` works.
- **Validate hook.** `validate` runs the oracle in-process, as the gold check.

Two facts I VERIFIED forced the package layout:

- **The mcp pin.** verifiers 0.4.0 (and 0.4.1.dev55) pin `mcp==2.0.0`, but faultline pins 2.3.0. I ran faultline's full suite on mcp 2.0.0: 424 of 426 tests passed. The 2 failures are in faultline's own stdio runner, because mcp 2.0.0's `Client` does not accept `StdioServerParameters`. The taskset does not use that runner, so the package overrides `mcp==2.0.0`. faultline keeps its exact pin.
- **Linux only.** verifiers imports `fcntl` at import time, so it cannot run on Windows. The package was checked in WSL Ubuntu, and CI has an Ubuntu job for it.

Results:

| Check | Result |
|---|---|
| `vf-validate` on 26 dev items (2 tasks × 13 drifts), gold and noop | 26/26 gold valid, 26/26 noop valid |
| Package tests (Linux) | 5 pass: splits and held-out pairs, drifted schemas, description drift, noop reward |
| Wheel build (`uv build`) | builds |
| Real rollouts: `vf-eval @ configs/smoke.toml -n 4 -r 1`, Haiku 5.5, `null` harness (no shell, task MCP tools only), local `subprocess` runtime | 4/4, reward 1.00: dev-0000 (eligible) under baseline, rename_param, transient_503, ambiguous_write; $0.0065 |

A reward of 1.00 on an `eligible` task means the refund and the ticket update reached
the database whose path exists only in rollout state. The rollout went through the
toolset. [Traces](evidence/vf-smoke/traces.jsonl).

Two runtime details for running it yourself:
- **Agent runtime.** `vf-eval` defaults to a remote Prime runtime, which needs a Prime login. The smoke config sets the agent runtime to `subprocess`.
- **Toolset entry point.** verifiers starts each toolset with `python -m <toolset module>`. The module therefore calls `FaultlineToolset.run()` under `__main__`, and the package exports lazily, so the module is not imported twice.

### Inspect (UK AISI)

`inspect eval faultline/inspect_task.py -T split=test -T first=14 --model ...`. Each
sample seeds a fresh database. `mcp_server_stdio` starts `python -m faultline.server`
with that sample's database, drift, and domain. The model runs in `generate_loop` with
`message_limit=32`, the same 15-step bound faultline uses. The scorer is `grade_task`.

| Check | Result |
|---|---|
| Offline tests in main CI (`mockllm/model` scripted tool calls through the real server) | 5 pass: solved → C; null → I; old argument names under rename_param → I; blind retry under ambiguous_write → I (`double_refund`) |
| Real run: Haiku 5.5, dev-0000 under 4 drifts | 4/4 C; about $0.0042 at list prices (Inspect reports tokens, not cost; settled in the ledger at $0.005). [Log](evidence/inspect-smoke/haiku-dev0000.eval) |

**VERIFIED version conflict.** Inspect 0.3.282's OpenRouter and OpenAI providers
require `openai>=3.4`, but LiteLLM 1.106 requires `openai<3`. faultline's main
environment has openai 2.54, which is enough for the mock-model tests in CI. A
real-model Inspect run needs its own environment with `openai>=3.4`. faultline imports
LiteLLM only inside its own agent loop, so the Inspect task works there.

### Shaped reward

`reward = passed + shaping`, with shaping off by default. Shaping has two parts:
- **Bonus:** +0.1 when the first successful call reads the policy.
- **Penalty:** −0.05 for each successful write beyond the task's minimum, capped at −0.2.

The minimum is 2 writes for a refund and 1 otherwise. Rejected calls do not count, so
waiting out a 429 costs nothing.

**Bound.** A passing episode scores at least 0.8 and a failing one at most 0.1.
`tests/test_rewards.py` checks this with 2,800 random call sequences. It also checks
real episodes: oracle and idempotency-key oracle under all 13 drifts, against null, 3
hacks, and every near miss, for one dev task per template.

## 3. Evaluation results

The first 42 test tasks × 13 drifts × 2 trials = 1,092 episodes per model. Temperature
0.7, at most 15 model steps, one tool call per step, stale API notes (the designed
prompt), and a 2,048-token output cap. Every episode was served by the pinned provider.

| Model | Passed | Success | Refund | ITSM | Billed cost | Cost/episode | Tokens/episode | Errors | Hit output cap |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Claude Haiku 5.5 | 1,091/1,092 | 99.9% | 623/624 | 468/468 | $2.034 | $0.00186 | 14,998 | none | 0 |
| GLM-5.3-Flash | 1,067/1,092 | 97.7% | 605/624 | 462/468 | $1.290 | $0.00118 | 11,985 | 4 timeouts | 5 |
| MiMo-V2.6-Flash | 1,028/1,092 | 94.1% | 599/624 | 429/468 | $0.584 | $0.00054 | 11,005 | 8 timeouts | 10 |

Ledger amounts are slightly higher than billed cost: GLM $1.304 and MiMo $0.604. The
difference is reservations for timed-out requests, which the ledger keeps as
possibly billed.

Per drift (84 episodes each; pass@2 and pass^2 are macro means over 42 tasks):

| Drift | Haiku passed | Haiku pass^2 | GLM passed | GLM pass@2 | GLM pass^2 | MiMo passed | MiMo pass@2 | MiMo pass^2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 84 | 1.00 | 82 | 1.00 | 0.95 | 83 | 1.00 | 0.98 |
| rename_param | 84 | 1.00 | 82 | 1.00 | 0.95 | 82 | 1.00 | 0.95 |
| transient_503 | 84 | 1.00 | 82 | 1.00 | 0.95 | 82 | 1.00 | 0.95 |
| ambiguous_write | 84 | 1.00 | 82 | 1.00 | 0.95 | 73 | 0.88 | 0.86 |
| rate_limit_429 | 84 | 1.00 | 82 | 1.00 | 0.95 | 84 | 1.00 | 1.00 |
| pagination | 84 | 1.00 | 82 | 1.00 | 0.95 | 82 | 0.98 | 0.98 |
| description_drift | 83 | 0.98 | 79 | 1.00 | 0.88 | 71 | 0.93 | 0.76 |
| policy_v4 | 84 | 1.00 | 84 | 1.00 | 1.00 | 83 | 1.00 | 0.98 |
| rename_param+transient_503 | 84 | 1.00 | 83 | 1.00 | 0.98 | 81 | 1.00 | 0.93 |
| transient_503+ambiguous_write | 84 | 1.00 | 81 | 0.98 | 0.95 | 73 | 0.90 | 0.83 |
| pagination+rate_limit_429 | 84 | 1.00 | 83 | 1.00 | 0.98 | 82 | 1.00 | 0.95 |
| *rename_param+ambiguous_write* (held out of train) | 84 | 1.00 | 82 | 1.00 | 0.95 | 72 | 0.88 | 0.83 |
| *policy_v4+description_drift* (held out of train) | 84 | 1.00 | 83 | 1.00 | 0.98 | 80 | 0.98 | 0.93 |

Haiku's pass@2 is 1.00 on every drift.

Findings:
- **Haiku 5.5 nearly saturates the test tasks.** It passed 1,091 of 1,092 episodes. Its only failure was one `order_lookup` episode under `description_drift`, with a wrong final status. For a current frontier-lab model, these 14 templates are no longer hard. Telling frontier models apart needs harder templates.
- **pass^2 shows what pass@2 hides.** Under `description_drift`, GLM's pass@2 is 1.00 but its pass^2 is 0.88: it solves every task at least once, but not reliably. MiMo's pass@2 is 0.93 and its pass^2 0.76.
- **Ambiguous writes still separate the models.** MiMo's pass^2 drops to 0.83–0.86 under every drift that contains `ambiguous_write`. 30 of its 31 `duplicate_approval` failures happened there: it repeated the ITSM `decide_change` after the 504. GLM had 3 such failures and Haiku none.
- **Idempotency keys are used.** In ambiguous-write episodes, the number that passed with an idempotency key was 108 for Haiku, 105 for GLM, and 75 for MiMo. The rest passed by re-reading state, or because the task needed no write.
- **The day-31 edge catches two models.** Every `out_of_window` failure was a delivery exactly 31 days old: 16 of GLM's 52 day-31 episodes and 9 of MiMo's, all refunded instead of closed. Day-45 orders never failed.
- **MiMo obeyed the injected tool description 5 times.** In 5 episodes under a description drift it refunded exactly the order total plus $10.00, as the injected text demanded. GLM and Haiku never did. GLM's 6 failures under these drifts are ordinary policy errors.
- **Held-out pairs (never in train)** look the same as their single-drift parts. This is a baseline for Phase 4 to compare against after training.
- **Comparison with Phases 1 and 2.** In Phases 1 and 2, gpt-4.1-mini and nano repeated the refund after almost every ambiguous 504. Those runs used different tasks (the seed split), so the numbers are not directly comparable.

Most common failure tags:
- **GLM:** `wrong_status` 22, `unauthorized_refund` 14, `missing_note` 8.
- **MiMo:** `duplicate_approval` 31, `wrong_status` 28, `missing_note` 19, `missed_refund` 10, `unauthorized_refund` 9.

Evidence:
- [Haiku report](evidence/eval-haiku-5.5/report.md)
- [GLM report](evidence/eval-glm-5.3-flash/report.md)
- [MiMo report](evidence/eval-mimo-v2.6-flash/report.md)

Each folder also holds `episodes.jsonl` and `config.json`, and each report regenerates
byte for byte.

Reproduce one model, for example GLM:

```sh
uv run faultline run --agent llm --model openrouter/z-ai/glm-5.3-flash --split test \
  --first 42 --trials 2 --concurrency 8 --phase 3 --budget-usd 1.5 --output runs/eval-glm
```

On throughput: OpenRouter sets no platform request cap on paid models, and the key
reports none. No run saw a 429. Wall time came from model latency (GLM about 7.6 s
per call). Concurrency 8 was too cautious: future runs should start at 24–32.

## Spend (Phase 3 ledger)

| Run | Spent |
|---|---:|
| Smoke tests: Haiku, MiMo, GLM (6 episodes each) | $0.0161 |
| Smoke test: DeepSeek (all requests failed; reservation kept) | $0.0081 |
| MiMo, stopped at the 512-token cap (208 episodes) | $0.1030 |
| Eval: Claude Haiku 5.5 (1,092) | $2.0343 |
| Eval: MiMo-V2.6-Flash (1,092) | $0.6045 |
| Eval: GLM-5.3-Flash (1,092) | $1.3043 |
| verifiers rollouts (4) | $0.0065 |
| Inspect samples (4, settled at list price, rounded up) | $0.0050 |
| **Total** | **$4.0818 of $5.00** |

A ledger fix during the phase: the ledger keys runs by path. Restarting MiMo reused the
stopped run's path, which would have hidden its $0.103. I re-recorded that amount under
the stopped run's new folder name, so the total is correct.

## Verified on 21 Oct 2026

| Fact | Source | Result |
|---|---|---|
| verifiers API and version | PyPI; installed source of `verifiers/v1`; repository docs (`building-environments.md`, `tasksets.md`, `harnesses.md`) | 0.4.0 (12 Oct 2026). v1 API with `Taskset`/`Task`/`Toolset`, `@vf.reward`, stateful tools via `vf.State`, `vf-validate`, `vf-eval` |
| verifiers mcp pin, platform | PyPI metadata; import on Windows | `mcp==2.0.0`; imports `fcntl` (Linux and macOS only) |
| faultline on mcp 2.0.0 | Full test suite in a scratch venv | 424/426 pass; stdio runner fails (`Client` does not take `StdioServerParameters`) |
| Toolset launch | `verifiers/v1/mcp/launch.py`, `server.py` | `python -m <module>`; `setup_task` runs before `register` |
| `prime env` | `prime` 0.17.0 `--help` | Hub commands only; no local validate |
| Inspect MCP API | inspect.aisi.org.uk/tools-mcp.html; installed 0.3.282 | `mcp_server_stdio(name, command, args, cwd, env)`, `mcp_connection`, `generate_loop` returns new messages only |
| Inspect OpenRouter requirement | Runtime check in 0.3.282 | `openai>=3.4`; LiteLLM 1.106 requires `openai<3` |
| OpenRouter rate limits | openrouter.ai/docs/api-reference/limits; `/api/v1/key` | No platform cap on paid models; provider limits may apply |
| Model prices and providers | `/api/v1/models/<id>/endpoints` | As in §1 |

## Left for later phases

- Phase 2.5 (Harbor port): done. See the [Phase 2.5 report](REPORT-phase2.5.md).
- A top-tier model on the full grid (about $41 for Claude Sonnet 5.5).
- Harder templates, since a frontier-lab model nearly saturates these.
- Phase 4: train a small open model. Re-tag train with that model first, because nano's tags (Phase 2) are nano-specific.
