# faultline results

Episodes: 6; passed: 0; success: 0.00%.

Token cost estimate: $0.000000; tokens: 0; unsettled reservations: $0.008136.

Costs are provider-billed amounts where reported, else uncached list prices.

| Agent | Task | Drift | c/n | k | pass@k | pass^k |
|---|---|---|---:|---:|---:|---:|
| llm (openrouter/deepseek/deepseek-v4.1-flash-1017, stale notes) | T-1001 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/deepseek/deepseek-v4.1-flash-1017, stale notes) | T-1003 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/deepseek/deepseek-v4.1-flash-1017, stale notes) | T-1004 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/deepseek/deepseek-v4.1-flash-1017, stale notes) | T-1006 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/deepseek/deepseek-v4.1-flash-1017, stale notes) | T-1008 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/deepseek/deepseek-v4.1-flash-1017, stale notes) | T-1009 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |

## Macro means across tasks

| Agent | Drift | k | Tasks | pass@k | pass^k |
|---|---|---:|---:|---:|---:|
| llm (openrouter/deepseek/deepseek-v4.1-flash-1017, stale notes) | baseline | 1 | 6 | 0.000000 | 0.000000 |

## Failure tags

- missed_refund: 3
- missing_note: 6
- wrong_status: 6

## Agent and infrastructure errors

- NotFoundError: 6

Each task/drift is estimated separately; trials are not pooled across tasks.
k > n is unavailable. Seeds help replay; hosted model responses are not deterministic.
