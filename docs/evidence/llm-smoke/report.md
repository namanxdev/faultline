# faultline results

Episodes: 6; passed: 5; success: 83.33%.

Token cost estimate: $0.009685; tokens: 21053; unsettled reservations: $0.000000.

Costs are provider-billed amounts where reported, else uncached list prices.

| Agent | Task | Drift | c/n | k | pass@k | pass^k |
|---|---|---|---:|---:|---:|---:|
| llm (openrouter/openai/gpt-4.1-mini) | T-1001 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/openai/gpt-4.1-mini) | T-1003 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/openai/gpt-4.1-mini) | T-1004 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/openai/gpt-4.1-mini) | T-1006 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/openai/gpt-4.1-mini) | T-1008 | baseline | 1/1 | 1 | 1.000000 | 1.000000 |
| llm (openrouter/openai/gpt-4.1-mini) | T-1009 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |

## Macro means across tasks

| Agent | Drift | k | Tasks | pass@k | pass^k |
|---|---|---:|---:|---:|---:|
| llm (openrouter/openai/gpt-4.1-mini) | baseline | 1 | 6 | 0.833333 | 0.833333 |

## Failure tags

- wrong_status: 1

## Agent and infrastructure errors

None.

Each task/drift is estimated separately; trials are not pooled across tasks.
k > n is unavailable. Seeds help replay; hosted model responses are not deterministic.
