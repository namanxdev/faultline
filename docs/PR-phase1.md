# Add the Phase 1 refund environment and tool-drift evaluation runner

Agents can now process six seeded refund tickets through real MCP tools while
parameter names change, reads fail once, or a refund commits before a timeout.
The grader checks final SQLite state and rejects incorrect refunds, missing
actions, and changes to unrelated records.

The implementation includes stdio and Streamable HTTP, reference/null/hack
agents, a budgeted OpenAI agent through LiteLLM, isolated concurrent trials,
transcripts, and reproducible pass@k/pass^k reports.

Validation: 93 tests pass; Ruff lint and format checks pass. The recorded
reference baseline passes 18/18 repeated trials, the null agent fails 6/6,
and all 18 blanket hacks fail. Five reports exactly reproduce 96 saved episodes.

This PR remains a draft until the required 72-trial paid LLM evaluation is
completed. No OpenAI API key was available, and no paid requests were made.
See `docs/REPORT-phase1.md` for evidence, limitations, and remaining acceptance work.
