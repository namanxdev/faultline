# faultline calibration

Tags: too_easy (> 30%), calibrated (10%–30%), too_hard (< 10%).

| Model | Task | Drift | c/k | Rate | Tag |
|---|---|---|---:|---:|---|
| openrouter/openai/gpt-4.1-nano | T-1001 | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | T-1001 | baseline | 5/8 | 62.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1001 | rename_param | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | T-1001 | transient_503 | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1003 | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | T-1003 | baseline | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | T-1003 | rename_param | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | T-1003 | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | T-1004 | ambiguous_write | 5/8 | 62.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1004 | baseline | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1004 | rename_param | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1004 | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | T-1006 | ambiguous_write | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1006 | baseline | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1006 | rename_param | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1006 | transient_503 | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1008 | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | T-1008 | baseline | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | T-1008 | rename_param | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | T-1008 | transient_503 | 4/8 | 50.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1009 | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | T-1009 | baseline | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1009 | rename_param | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | T-1009 | transient_503 | 4/8 | 50.0% | too_easy |

## Tag counts

| Model | Drift | too_easy | calibrated | too_hard |
|---|---|---:|---:|---:|
| openrouter/openai/gpt-4.1-nano | all | 13 | 3 | 8 |
| openrouter/openai/gpt-4.1-nano | ambiguous_write | 2 | 0 | 4 |
| openrouter/openai/gpt-4.1-nano | baseline | 4 | 1 | 1 |
| openrouter/openai/gpt-4.1-nano | rename_param | 3 | 2 | 1 |
| openrouter/openai/gpt-4.1-nano | transient_503 | 4 | 0 | 2 |

## Agent and infrastructure errors

None.

Tags are noisy. At k=8, calibrated means 1 or 2 passes and too_hard means 0; a cell
whose true rate is 20% scores 0/8 about 17% of the time. Each row logs its k.
