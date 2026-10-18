# Phase 1 evidence

These are real evaluations, completed on 2026-10-18 local time. Scripted agents
are offline and free. The two LLM runs cost $0.1415 in total, billed by OpenRouter.

| Agent | Trials | Passed | Artifacts |
|---|---:|---:|---|
| Reference, four drifts | 72 | 27 | [Report](reference/report.md), [episodes](reference/episodes.jsonl) |
| Oracle, four drifts | 72 | 72 | [Report](oracle/report.md), [episodes](oracle/episodes.jsonl) |
| LLM gpt-4.1-mini (OpenRouter), four drifts | 72 | 59 | [Report](llm/report.md), [episodes](llm/episodes.jsonl) |
| LLM smoke test, baseline | 6 | 5 | [Report](llm-smoke/report.md), [episodes](llm-smoke/episodes.jsonl) |
| Null, baseline | 6 | 0 | [Report](null/report.md), [episodes](null/episodes.jsonl) |
| Refund all, baseline | 6 | 0 | [Report](refund_all/report.md), [episodes](refund_all/episodes.jsonl) |
| Close all, baseline | 6 | 0 | [Report](close_all/report.md), [episodes](close_all/episodes.jsonl) |
| Resolve all, baseline | 6 | 0 | [Report](resolve_all/report.md), [episodes](resolve_all/episodes.jsonl) |

Each folder also has the run's `config.json`. Transcript paths in the episode
records are relative to the original run folder, `runs/p1c-<agent>` (LLM: `runs/llm-phase1`, `runs/llm-smoke`), not this
evidence folder. Binary databases and full transcripts are local run artifacts.
The [phase report](../REPORT-phase1.md) gives the commands that recreate them.

Regenerate a report from saved records:

```sh
uv run faultline report docs/evidence/reference/episodes.jsonl
```

Seeds, SDK versions, and model settings are recorded in the configuration files.
The results are evidence for the six specified cases and tested attacks only.
