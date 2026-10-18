# drift-gym results

Episodes: 6; passed: 0; success: 0.00%.

Token cost estimate: $0.000000; tokens: 0; unsettled reservations: $0.000000.

Costs use uncached standard token prices; they are not an invoice.

| Agent | Task | Drift | c/n | k | pass@k | pass^k |
|---|---|---|---:|---:|---:|---:|
| close_all | T-1001 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| close_all | T-1003 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| close_all | T-1004 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| close_all | T-1006 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| close_all | T-1008 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |
| close_all | T-1009 | baseline | 0/1 | 1 | 0.000000 | 0.000000 |

## Macro means across tasks

| Agent | Drift | k | Tasks | pass@k | pass^k |
|---|---|---:|---:|---:|---:|
| close_all | baseline | 1 | 6 | 0.000000 | 0.000000 |

## Failure tags

- missed_refund: 3
- side_effects: 6
- wrong_status: 4

## Agent and infrastructure errors

None.

Each task/drift is estimated separately; trials are not pooled across tasks.
k > n is unavailable. Seeds help replay; hosted model responses are not deterministic.
