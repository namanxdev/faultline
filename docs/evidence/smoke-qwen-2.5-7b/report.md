# faultline results

Episodes: 6; passed: 3; success: 50.00%.

Token cost estimate: $0.004903; tokens: 47564; unsettled reservations: $0.000000.

Costs are provider-billed amounts where reported, else uncached list prices.

| Agent | Task | Drift | c/n | k | pass@k | pass^k |
|---|---|---|---:|---:|---:|---:|
| llm (openrouter/qwen/qwen-2.5-7b-instruct, stale notes) | T-1001 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/qwen/qwen-2.5-7b-instruct, stale notes) | T-1003 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/qwen/qwen-2.5-7b-instruct, stale notes) | T-1004 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/qwen/qwen-2.5-7b-instruct, stale notes) | T-1006 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/qwen/qwen-2.5-7b-instruct, stale notes) | T-1008 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/qwen/qwen-2.5-7b-instruct, stale notes) | T-1009 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |

## Macro means across tasks

| Agent | Drift | k | Tasks | pass@k | pass^k |
|---|---|---:|---:|---:|---:|
| llm (openrouter/qwen/qwen-2.5-7b-instruct, stale notes) | baseline | 1 | 6 | 0.500000 | 0.500000 |

## Failure tags

- missed_refund: 1
- unauthorized_refund: 2
- wrong_status: 3

## Agent and infrastructure errors

None.

Each task/drift is estimated separately; trials are not pooled across tasks.
k > n is unavailable. Seeds help replay; hosted model responses are not deterministic.
