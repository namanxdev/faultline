# Phase 1 report

Date: 2026-10-18 (Asia/Calcutta).
Branch: `phase1/core-environment`.

**Status: implementation and local checks complete; full Phase 1 acceptance pending.**
The 72-trial LLM run needs `OPENAI_API_KEY`. No paid request has been made.
The GitHub repository and phase PR also remain pending.

## What changed

- Added deterministic SQLite fixtures for the six refund-support tickets.
- Added all seven tools with decimal-string dollar amounts and integer-cent storage.
- Added baseline, parameter rename, transient read failure, and ambiguous write modes.
- Added official MCP stdio and Streamable HTTP adapters.
- Added independent final-state grading, exact refund-row checks, history preservation,
  failure tags, and checks on all unrelated records.
- Added reference, null, three blanket-hack agents, and a bounded LiteLLM agent.
- Added an asynchronous runner with six concurrent trials, isolated databases and
  processes, fixed seeds, transcripts, token usage, and cost reservations.
- Added deterministic reports with per-task pass@k, pass^k, and macro means.
- Added dependency locking, command-line entry points, README, and a learning guide.

## Results and acceptance

| Check | Observed result | Status |
|---|---|---|
| Reference, baseline | 6/6 tasks; 18/18 across three repetitions | Pass |
| Null agent, baseline | 0/6 | Pass |
| Refund-all blanket hack | 0/6 | Pass |
| Close-all blanket hack | 0/6 | Pass |
| Resolve-all blanket hack | 0/6 | Pass |
| Reference, all four conditions | 27/72 | Recorded diagnostic |
| stdio and Streamable HTTP | Seven tools; protocol 2026-07-28 | Pass |
| pytest | 93 passed | Pass |
| Ruff lint and formatting | Clean | Pass |
| Real LLM evaluation | 0/72 attempted; $0 API spend | Blocked: missing key |
| Phase PR | Repository does not yet exist | Pending bootstrap authorization |

The full reference run passed 18/18 baseline trials, 0/18 rename trials,
0/18 transient-error trials, and 9/18 ambiguous-write trials.
The last nine need no refund, so they do not trigger the write fault.
The 45 expected reference failures are recorded as `ExceptionGroup` errors by
the SDK context manager. Their transcripts retain the underlying tool errors.

There are 96 recorded offline evaluation trials: 72 reference and 24 null/hack.
These use real MCP subprocesses. No model calls are involved in those results.
Tests also exercise in-process MCP clients, a real HTTP server, and a local
mock HTTP transport through the actual LiteLLM/OpenAI adapter.

The blanket hacks act on every ticket while assigned one ticket. This is how
the no-side-effects requirement rejects all of them. A targeted close action
can be correct on an expired ticket; rejecting that would be a grader bug.
Separate tests cover targeted mistakes, including split refunds whose sum is
correct, over-refunds, unauthorized refunds, missing notes, history changes,
and unrelated record mutations.

## Evidence and reproduction

[Evidence index](evidence/README.md) links the raw episode records and reports.
The full databases and transcripts remain under ignored `runs/phase1-*` folders.
The checked-in evidence contains results and configurations, not binary databases.

```sh
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run faultline run --agent reference --output runs/reference-replay
uv run faultline run --agent null --drifts baseline --trials 1 --output runs/null-replay
uv run faultline run --agent refund_all --drifts baseline --trials 1 --output runs/refund-all-replay
uv run faultline run --agent close_all --drifts baseline --trials 1 --output runs/close-all-replay
uv run faultline run --agent resolve_all --drifts baseline --trials 1 --output runs/resolve-all-replay
```

Regenerate any checked-in report with, for example:

```sh
uv run faultline report docs/evidence/reference/episodes.jsonl
```

## Live documentation verification

Checked on 2026-10-17 UTC, with local validation completed on 2026-10-18.

| Dependency | Evidence | Implementation choice |
|---|---|---|
| Official MCP SDK | [PyPI release](https://pypi.org/project/mcp/2.3.0/), [client docs](https://py.sdk.modelcontextprotocol.io/client/), [server docs](https://py.sdk.modelcontextprotocol.io/servers/) | Stable `mcp==2.3.0`; v2 `MCPServer` and `Client` |
| MCP protocol | Live docs plus both transport integration tests | Negotiates `2026-07-28` |
| LiteLLM | [Function-calling docs](https://docs.litellm.ai/docs/completion/function_call), installed source | Lock resolves 1.105.1; async tool loop; retries disabled |
| OpenAI model | [Official model page](https://developers.openai.com/api/docs/models/gpt-4.1-mini) | Pinned `gpt-4.1-mini-2025-04-14`; temperature 0.7; tool calls |

The stable MCP SDK now uses v2 names and snake-case fields. We followed the live
documentation rather than older FastMCP/ClientSession examples. It supports the
revision requested in the brief. Money format, delivery-window anchoring, and
policy precedence were unspecified details: the code uses decimal strings,
days since delivery, and rejects prior refunds or ineligible delivery dates
before considering high-value escalation. These choices preserve all six seed outcomes.

The chosen OpenAI model is marked deprecated in the current docs. It is a
small non-reasoning snapshot compatible with the brief's temperature setting.
Account access remains unverified. If unavailable, select and verify a replacement
and update its price bounds before any paid call. No fallback model is selected silently.

## Limits and remaining work

1. Make `OPENAI_API_KEY` available in the environment or ignored `.env` file.
2. Run `uv run faultline run --agent llm --output runs/openai-phase1 --budget-usd 5`.
3. Confirm all 72 episodes completed without provider or infrastructure errors.
   Compare `report.md` with a regeneration from `episodes.jsonl`. Record real cost,
   tokens, task/condition results, and failure tags. LLM task failures are valid results.
4. Create the public repository and initialize a base branch before opening the
   phase PR. `gh` authentication works. The brief explicitly prohibits pushing
   `main` without Naman's OK. Local `main` points only to the original scaffold
   commit `f5bff78`; phase work stays on its own branch.
5. Stop after Phase 1 and wait for Naman before starting Phase 2.

The grader sees final state only. It does not prove action order or detect a
fully reversed mutation. A nonempty note is sufficient; note quality is not
graded. The refund server is intentionally permissive. The six golden cases
are not a broad generalization benchmark. Error codes are simulated tool errors,
not HTTP transport failures. Budget totals are conservative standard-price
estimates and apply to one run; separate runs need a shared external spend tally.

The first sandboxed pytest attempt could not use Windows temporary/cache paths.
Workspace-local scratch paths passed, and the normal command subsequently
passed outside the sandbox. This was an environment permission issue.

## Final validation

- `pytest -q`: 93 passed in 17.32 seconds on Python 3.12.12 / Windows.
- `ruff check .`: all checks passed.
- `ruff format --check .`: all files formatted.
- Re-rendered all five saved reports from JSONL: exact matches, 96 total trials.
- One dependency warning: Pydantic notes that a LiteLLM/OpenAI reasoning TypedDict
  uses a `ReadOnly` qualifier that it cannot enforce. This does not affect the
  non-reasoning model request or the local adapter test. No warning was suppressed.
