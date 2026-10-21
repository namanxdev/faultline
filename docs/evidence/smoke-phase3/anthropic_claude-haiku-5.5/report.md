# faultline results

Episodes: 6; passed: 6; success: 100.00%.

Token cost estimate: $0.007697; tokens: 60909; unsettled reservations: $0.000000.

Costs are provider-billed amounts where reported, else uncached list prices.

| Agent | Task | Drift | c/n | k | pass@k | pass^k |
|---|---|---|---:|---:|---:|---:|
| llm (openrouter/anthropic/claude-haiku-5.5, stale notes) | T-1001 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/anthropic/claude-haiku-5.5, stale notes) | T-1003 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/anthropic/claude-haiku-5.5, stale notes) | T-1004 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/anthropic/claude-haiku-5.5, stale notes) | T-1006 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/anthropic/claude-haiku-5.5, stale notes) | T-1008 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/anthropic/claude-haiku-5.5, stale notes) | T-1009 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |

## Macro means across tasks

| Agent | Drift | k | Tasks | pass@k | pass^k |
|---|---|---:|---:|---:|---:|
| llm (openrouter/anthropic/claude-haiku-5.5, stale notes) | baseline | 1 | 6 | 1.000000 | 1.000000 |

## Failure tags

None.

## Agent and infrastructure errors

None.

Each task/drift is estimated separately; trials are not pooled across tasks.
k > n is unavailable. Seeds help replay; hosted model responses are not deterministic.
