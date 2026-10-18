# faultline results

Episodes: 4; passed: 0; success: 0.00%.

Token cost estimate: $0.002066; tokens: 19636; unsettled reservations: $0.000000.

Costs are provider-billed amounts where reported, else uncached list prices.

| Agent | Task | Drift | c/n | k | pass@k | pass^k |
|---|---|---|---:|---:|---:|---:|
| llm (openrouter/openai/gpt-4.1-nano, stale notes) | train-0000 | description_drift | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/openai/gpt-4.1-nano, stale notes) | train-0007 | pagination | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/openai/gpt-4.1-nano, stale notes) | train-0008 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/openai/gpt-4.1-nano, stale notes) | train-0012 | rate_limit_429 | 0/1 | 1 | 0.000000 | 0.000000 |

## Macro means across tasks

| Agent | Drift | k | Tasks | pass@k | pass^k |
|---|---|---:|---:|---:|---:|
| llm (openrouter/openai/gpt-4.1-nano, stale notes) | baseline | 1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/openai/gpt-4.1-nano, stale notes) | description_drift | 1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/openai/gpt-4.1-nano, stale notes) | pagination | 1 | 1 | 0.000000 | 0.000000 |
| llm (openrouter/openai/gpt-4.1-nano, stale notes) | rate_limit_429 | 1 | 1 | 0.000000 | 0.000000 |

## Failure tags

- missed_refund: 1
- missing_decision: 1
- missing_note: 1
- over_refund: 1
- side_effects: 1
- unauthorized_refund: 1
- wrong_duplicate_link: 1
- wrong_priority: 1
- wrong_status: 2

## Agent and infrastructure errors

None.

Each task/drift is estimated separately; trials are not pooled across tasks.
k > n is unavailable. Seeds help replay; hosted model responses are not deterministic.
