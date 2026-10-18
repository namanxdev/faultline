# faultline offline validation

Splits: dev, seed, test, train; tasks: 456; episodes: 14459.
Oracle checks run every task under every drift of its split. Gates that must fail
run under baseline; the `recheck` near miss runs under ambiguous_write.

| Domain | Check | Expected | Episodes | As expected |
|---|---|---|---:|---:|
| itsm | close_all, baseline | fail | 186 | 186 |
| itsm | near miss: decision | fail | 62 | 62 |
| itsm | near miss: escalate | fail | 31 | 31 |
| itsm | near miss: freeze | fail | 31 | 31 |
| itsm | near miss: ignore_message | fail | 31 | 31 |
| itsm | near miss: link | fail | 31 | 31 |
| itsm | near miss: note | fail | 186 | 186 |
| itsm | near miss: priority | fail | 62 | 62 |
| itsm | near miss: recheck | fail | 62 | 62 |
| itsm | near miss: status | fail | 124 | 124 |
| itsm | null, baseline | fail | 186 | 186 |
| itsm | oracle | pass | 2166 | 2166 |
| itsm | oracle_idem | pass | 2166 | 2166 |
| itsm | reference, baseline | pass | 186 | 186 |
| itsm | refund_all, baseline | fail | 186 | 186 |
| itsm | resolve_all, baseline | fail | 186 | 186 |
| refund | close_all, baseline | fail | 270 | 270 |
| refund | near miss: delivered | fail | 33 | 33 |
| refund | near miss: escalate | fail | 35 | 35 |
| refund | near miss: ignore_message | fail | 67 | 67 |
| refund | near miss: note | fail | 270 | 270 |
| refund | near miss: prior_refund | fail | 34 | 34 |
| refund | near miss: recheck | fail | 134 | 134 |
| refund | near miss: refund | fail | 134 | 134 |
| refund | near miss: status | fail | 270 | 270 |
| refund | near miss: window | fail | 34 | 34 |
| refund | null, baseline | fail | 270 | 270 |
| refund | oracle | pass | 3108 | 3108 |
| refund | oracle_idem | pass | 3108 | 3108 |
| refund | reference, baseline | pass | 270 | 270 |
| refund | refund_all, baseline | fail | 270 | 270 |
| refund | resolve_all, baseline | fail | 270 | 270 |

## Unexpected results

None.
