"""Unbiased finite-sample success and reliability estimates, per task and drift."""

import json
from collections import Counter, defaultdict
from math import comb
from pathlib import Path


def pass_metrics(n: int, c: int, k: int) -> tuple[float, float]:
    if not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError("Require 0 <= c <= n and 1 <= k <= n")
    denominator = comb(n, k)
    return 1 - (comb(n - c, k) if n - c >= k else 0) / denominator, (
        comb(c, k) if c >= k else 0
    ) / denominator


def render(episodes: list[dict]) -> str:
    if not episodes:
        raise ValueError("No episodes to report")
    groups = defaultdict(list)
    for episode in episodes:
        # Different models must never share an estimate, even under the same agent name.
        model = episode.get("model")
        agent = f"{episode['agent']} ({model})" if model else episode["agent"]
        groups[(agent, episode["ticket_id"], episode["drift"])].append(episode)
    passed = sum(e["grade"]["passed"] for e in episodes)
    cost = sum(e["usage"]["cost_usd"] for e in episodes)
    reserved = sum(e["usage"].get("reserved_usd", 0) for e in episodes)
    tokens = sum(e["usage"]["prompt_tokens"] + e["usage"]["completion_tokens"] for e in episodes)
    lines = [
        "# faultline results",
        "",
        f"Episodes: {len(episodes)}; passed: {passed}; success: {passed / len(episodes):.2%}.",
        "",
        f"Token cost estimate: ${cost:.6f}; tokens: {tokens}; "
        f"unsettled reservations: ${reserved:.6f}.",
        "",
        "Costs are provider-billed amounts where reported, else uncached list prices.",
        "",
        "| Agent | Task | Drift | c/n | k | pass@k | pass^k |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    estimates = defaultdict(list)
    for (agent, task, drift), rows in sorted(groups.items()):
        n, c = len(rows), sum(r["grade"]["passed"] for r in rows)
        for k in range(1, min(3, n) + 1):
            at_k, all_k = pass_metrics(n, c, k)
            estimates[(agent, drift, k)].append((at_k, all_k))
            lines.append(
                f"| {agent} | {task} | {drift} | {c}/{n} | {k} | {at_k:.6f} | {all_k:.6f} |"
            )
    lines += [
        "",
        "## Macro means across tasks",
        "",
        "| Agent | Drift | k | Tasks | pass@k | pass^k |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for (agent, drift, k), values in sorted(estimates.items()):
        at_k = sum(v[0] for v in values) / len(values)
        all_k = sum(v[1] for v in values) / len(values)
        lines.append(f"| {agent} | {drift} | {k} | {len(values)} | {at_k:.6f} | {all_k:.6f} |")
    tags = Counter(tag for e in episodes for tag in e["grade"]["failure_tags"])
    errors = Counter(e["error"] for e in episodes if e.get("error"))
    lines += ["", "## Failure tags", ""]
    lines += [f"- {tag}: {count}" for tag, count in sorted(tags.items())] or ["None."]
    lines += ["", "## Agent and infrastructure errors", ""]
    lines += [f"- {error}: {count}" for error, count in sorted(errors.items())] or ["None."]
    lines += [
        "",
        "Each task/drift is estimated separately; trials are not pooled across tasks.",
        "k > n is unavailable. Seeds help replay; hosted model responses are not deterministic.",
        "",
    ]
    return "\n".join(lines)


def write_report(path: Path) -> Path:
    episodes = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    output = path.with_name("report.md")
    output.write_text(render(episodes), encoding="utf-8")
    return output
