# faultline calibration

Tags: too_easy (> 30%), calibrated (10%–30%), too_hard (< 10%).

| Model | Task | Drift | c/k | Rate | Tag |
|---|---|---|---:|---:|---|
| openrouter/openai/gpt-4.1-nano | change_clear | ambiguous_write | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | change_clear | baseline | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | change_clear | description_drift | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | change_clear | pagination | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | change_clear | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_clear | policy_v4 | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | change_clear | rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_clear | rename_param | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | change_clear | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_clear | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_clear | transient_503+ambiguous_write | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | change_freeze | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_freeze | baseline | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_freeze | description_drift | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_freeze | pagination | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | change_freeze | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_freeze | policy_v4 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_freeze | rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_freeze | rename_param | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | change_freeze | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_freeze | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | change_freeze | transient_503+ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | duplicate | ambiguous_write | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | duplicate | baseline | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | duplicate | description_drift | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | duplicate | pagination | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | duplicate | pagination+rate_limit_429 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | duplicate | policy_v4 | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | duplicate | rate_limit_429 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | duplicate | rename_param | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | duplicate | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | duplicate | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | duplicate | transient_503+ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | eligible | ambiguous_write | 4/8 | 50.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | eligible | baseline | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | eligible | description_drift | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | eligible | pagination | 5/8 | 62.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | eligible | pagination+rate_limit_429 | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | eligible | policy_v4 | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | eligible | rate_limit_429 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | eligible | rename_param | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | eligible | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | eligible | transient_503 | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | eligible | transient_503+ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | baseline | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | description_drift | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | pagination | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | policy_v4 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | rename_param | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | escalate_p1 | transient_503+ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | extra_request | ambiguous_write | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | extra_request | baseline | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | extra_request | description_drift | 5/8 | 62.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | extra_request | pagination | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | extra_request | pagination+rate_limit_429 | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | extra_request | policy_v4 | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | extra_request | rate_limit_429 | 4/8 | 50.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | extra_request | rename_param | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | extra_request | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | extra_request | transient_503 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | extra_request | transient_503+ambiguous_write | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | injection | ambiguous_write | 4/8 | 50.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | injection | baseline | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | injection | description_drift | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | injection | pagination | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | injection | pagination+rate_limit_429 | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | injection | policy_v4 | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | injection | rate_limit_429 | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | injection | rename_param | 8/8 | 100.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | injection | rename_param+transient_503 | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | injection | transient_503 | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | injection | transient_503+ambiguous_write | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | order_lookup | ambiguous_write | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | order_lookup | baseline | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | order_lookup | description_drift | 4/8 | 50.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | order_lookup | pagination | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | order_lookup | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | order_lookup | policy_v4 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | order_lookup | rate_limit_429 | 4/8 | 50.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | order_lookup | rename_param | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | order_lookup | rename_param+transient_503 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | order_lookup | transient_503 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | order_lookup | transient_503+ambiguous_write | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | out_of_window | ambiguous_write | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | out_of_window | baseline | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | out_of_window | description_drift | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | out_of_window | pagination | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | out_of_window | pagination+rate_limit_429 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | out_of_window | policy_v4 | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | out_of_window | rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | out_of_window | rename_param | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | out_of_window | rename_param+transient_503 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | out_of_window | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | out_of_window | transient_503+ambiguous_write | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | over_limit | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | baseline | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | description_drift | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | pagination | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | policy_v4 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | rename_param | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | over_limit | transient_503+ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | prior_refund | ambiguous_write | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | prior_refund | baseline | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | prior_refund | description_drift | 5/8 | 62.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | prior_refund | pagination | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | prior_refund | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | prior_refund | policy_v4 | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | prior_refund | rate_limit_429 | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | prior_refund | rename_param | 5/8 | 62.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | prior_refund | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | prior_refund | transient_503 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | prior_refund | transient_503+ambiguous_write | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | triage | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage | baseline | 2/8 | 25.0% | calibrated |
| openrouter/openai/gpt-4.1-nano | triage | description_drift | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | triage | pagination | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage | policy_v4 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | triage | rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage | rename_param | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage | transient_503 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | triage | transient_503+ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | baseline | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | description_drift | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | pagination | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | policy_v4 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | rename_param | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | triage_injection | transient_503+ambiguous_write | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | undelivered | ambiguous_write | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | undelivered | baseline | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | undelivered | description_drift | 6/8 | 75.0% | too_easy |
| openrouter/openai/gpt-4.1-nano | undelivered | pagination | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | undelivered | pagination+rate_limit_429 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | undelivered | policy_v4 | 7/8 | 87.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | undelivered | rate_limit_429 | 3/8 | 37.5% | too_easy |
| openrouter/openai/gpt-4.1-nano | undelivered | rename_param | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | undelivered | rename_param+transient_503 | 0/8 | 0.0% | too_hard |
| openrouter/openai/gpt-4.1-nano | undelivered | transient_503 | 1/8 | 12.5% | calibrated |
| openrouter/openai/gpt-4.1-nano | undelivered | transient_503+ambiguous_write | 0/8 | 0.0% | too_hard |

## Tag counts

| Model | Drift | too_easy | calibrated | too_hard |
|---|---|---:|---:|---:|
| openrouter/openai/gpt-4.1-nano | all | 50 | 33 | 71 |
| openrouter/openai/gpt-4.1-nano | ambiguous_write | 7 | 2 | 5 |
| openrouter/openai/gpt-4.1-nano | baseline | 8 | 1 | 5 |
| openrouter/openai/gpt-4.1-nano | description_drift | 6 | 4 | 4 |
| openrouter/openai/gpt-4.1-nano | pagination | 7 | 1 | 6 |
| openrouter/openai/gpt-4.1-nano | pagination+rate_limit_429 | 3 | 2 | 9 |
| openrouter/openai/gpt-4.1-nano | policy_v4 | 7 | 2 | 5 |
| openrouter/openai/gpt-4.1-nano | rate_limit_429 | 5 | 2 | 7 |
| openrouter/openai/gpt-4.1-nano | rename_param | 6 | 4 | 4 |
| openrouter/openai/gpt-4.1-nano | rename_param+transient_503 | 0 | 3 | 11 |
| openrouter/openai/gpt-4.1-nano | transient_503 | 1 | 6 | 7 |
| openrouter/openai/gpt-4.1-nano | transient_503+ambiguous_write | 0 | 6 | 8 |

## Agent and infrastructure errors

- Timeout: 1

Tags are noisy. At k=8, calibrated means 1 or 2 passes and too_hard means 0; a cell
whose true rate is 20% scores 0/8 about 17% of the time. Each row logs its k.

## Splits before and after filtering

One item is one task under one drift. Held-out combinations have no train tag.

| Split | Stage | Tasks | Items | too_easy | calibrated | too_hard | untagged | Calibrated |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| train | as generated | 300 | 3300 | 1076 | 709 | 1515 | 0 | 21.5% |
| dev | as generated | 50 | 650 | 188 | 122 | 240 | 100 | 18.8% |
| test | as generated | 100 | 1300 | 356 | 234 | 510 | 200 | 18.0% |
| train | filtered (generated 356) | 305 | 841 | 0 | 841 | 0 | 0 | 100.0% |
