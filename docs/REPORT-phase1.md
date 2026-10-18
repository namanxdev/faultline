# Phase 1 report

Date: 2026-10-18 (Asia/Calcutta).
Branches: `phase1/core-environment` (merged to `main` by Naman), then
`phase1/completion` (this PR).

**Status: implementation and local checks complete; full Phase 1 acceptance pending.**
The 72-trial LLM run is ready but needs `OPENROUTER_API_KEY`. No paid request
has been made; Phase 1 ledger spend is $0. The phase PR stays unmerged until that run passes.

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

Completion work (`phase1/completion`):

- Renamed the project, package, and commands to `faultline`.
- Added the `oracle` agent. It solves all 24 task × drift cells using only the API:
  schema-discovered argument names, retries only on retryable reads, and a state
  re-read before any repeated refund.
- Added `--model` with a priced registry. The default is `openrouter/openai/gpt-4.1-mini`,
  pinned to `provider.only = ["openai"]` with fallbacks off. Episodes record the
  serving provider. Settled cost uses OpenRouter's billed amount when it is reported.
- Added per-phase caps across runs ($5 Phase 1, $25 Phase 3) with a fail-closed ledger.
- Reports now estimate each model separately.
- The runner records the leaf error class (`ToolFailure`), not the SDK `ExceptionGroup`.
- Added an MIT license, GitHub Actions CI (Ubuntu and Windows, Python 3.11 and 3.12),
  and a README related-work section.
- Added Phase 2 items (near-miss agents, difficulty calibration) and Phase 2.5 (Harbor port)
  to the brief, with open questions.

## Results and acceptance

| Check | Observed result | Status |
|---|---|---|
| Reference, baseline | 6/6 tasks; 18/18 across three repetitions | Pass |
| Oracle, all four conditions | 72/72; no errors | Pass |
| Null agent, baseline | 0/6 | Pass |
| Refund-all blanket hack | 0/6 | Pass |
| Close-all blanket hack | 0/6 | Pass |
| Resolve-all blanket hack | 0/6 | Pass |
| Reference, all four conditions | 27/72 | Recorded diagnostic |
| stdio and Streamable HTTP | Seven tools; protocol 2026-07-28 | Pass |
| pytest | 133 passed | Pass |
| Ruff lint and formatting | Clean | Pass |
| Real LLM evaluation | 0/72 attempted; $0 API spend | Blocked: `OPENROUTER_API_KEY` not yet added |
| Phase PR | Opened from `phase1/completion` | Open; merge after the LLM run |

The full reference run passed 18/18 baseline trials, 0/18 rename trials,
0/18 transient-error trials, and 9/18 ambiguous-write trials.
The last nine need no refund, so they do not trigger the write fault.
The 45 expected reference failures are now recorded as `ToolFailure`, the leaf
error inside the SDK's `ExceptionGroup`. Their transcripts retain the tool error text.
The oracle passed all 72 trials (18/18 in every condition) with no errors.

There are 168 recorded offline evaluation trials: 72 reference, 72 oracle, and
24 null/hack. All were re-run after the rename.
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
The full databases and transcripts remain under ignored `runs/p1c-*` folders.
The checked-in evidence contains results and configurations, not binary databases.

```sh
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run faultline run --agent reference --output runs/reference-replay
uv run faultline run --agent oracle --output runs/oracle-replay
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
| OpenAI model | [Official model page](https://developers.openai.com/api/docs/models/gpt-4.1-mini) | Direct option: `gpt-4.1-mini-2025-04-14`; temperature 0.7; tool calls |
| OpenRouter | [Models API](https://openrouter.ai/api/v1/models), [endpoints](https://openrouter.ai/api/v1/models/openai/gpt-4.1-mini/endpoints), [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection), [parameters](https://openrouter.ai/docs/api/reference/parameters), [usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting) (checked 2026-10-18) | Default `openrouter/openai/gpt-4.1-mini`, $0.40/$1.60 per M; hosts are OpenAI and Azure, pinned to OpenAI with `only` and `allow_fallbacks: false`; `require_parameters` not set because `parallel_tool_calls` is not listed for the model; cost always included in `usage` |
| LiteLLM OpenRouter adapter | Installed source, `llms/openrouter/chat/transformation.py`, plus a mock-transport test | `extra_body.provider` and `parallel_tool_calls` reach the request body; billed cost appears in `_hidden_params["response_cost"]`; `response.provider` names the host |

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

1. Add `OPENROUTER_API_KEY` to the ignored `.env` file.
2. Run `uv run faultline run --agent llm --budget-usd 5 --output runs/llm-phase1`.
3. Confirm all 72 episodes completed without provider or infrastructure errors, and
   that every episode's `usage.provider` is OpenAI. Compare `report.md` with a
   regeneration from `episodes.jsonl`. Record real cost, tokens, task/condition
   results, and failure tags, beside the oracle and reference. LLM task failures are valid results.
4. Merge the Phase 1 PR after that run passes. Then stop and wait for Naman.

Before Phase 2, Naman must decide the open items now in `PROJECT.md`: a Phase 2
API budget for calibration (none exists, so the ledger refuses Phase 2 spend), the
meaning of a "mostly calibrated" `train` split, and the limit of near-miss tests to
state-changing steps.

Related-work note: the README table follows Naman's comparison, with corrections
after reading both papers. MCPEvol-Bench uses a rubric-based LLM judge (confirmed).
ReliabilityBench grades end-state equivalence and injects schema drift, so faultline's
claimed difference is narrower: state checks on unrelated records plus a non-idempotent
ambiguous write. Splits, RL training, and verifiers/Inspect ports are marked planned.

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

- `pytest -q`: 133 passed on Python 3.12.12 / Windows.
- `ruff check .`: all checks passed.
- `ruff format --check .`: all files formatted.
- Re-rendered all six saved reports from JSONL: exact matches, 168 total trials.
- One dependency warning: Pydantic notes that a LiteLLM/OpenAI reasoning TypedDict
  uses a `ReadOnly` qualifier that it cannot enforce. This does not affect the
  non-reasoning model request or the local adapter test. No warning was suppressed.
