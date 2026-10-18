"""Tag each task × drift cell by a cheap model's pass rate, to keep training tasks learnable."""

import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

# Exact fractions: at k=8 the rates come in steps of 1/8, and floats must not move a boundary.
TOO_EASY_ABOVE = Fraction(3, 10)
TOO_HARD_BELOW = Fraction(1, 10)
TAGS = ("too_easy", "calibrated", "too_hard")


def tag(c: int, n: int) -> str:
    if not 0 <= c <= n or n < 1:
        raise ValueError("Require 0 <= c <= n and n >= 1")
    rate = Fraction(c, n)
    if rate > TOO_EASY_ABOVE:
        return "too_easy"
    if rate < TOO_HARD_BELOW:
        return "too_hard"
    return "calibrated"


def render(episodes: list[dict]) -> str:
    if not episodes:
        raise ValueError("No episodes to calibrate")
    cells = defaultdict(list)
    for e in episodes:
        cells[(e.get("model") or e["agent"], e["ticket_id"], e["drift"])].append(e)
    lines = [
        "# faultline calibration",
        "",
        f"Tags: too_easy (> {float(TOO_EASY_ABOVE):.0%}), calibrated "
        f"({float(TOO_HARD_BELOW):.0%}–{float(TOO_EASY_ABOVE):.0%}), "
        f"too_hard (< {float(TOO_HARD_BELOW):.0%}).",
        "",
        "| Model | Task | Drift | c/k | Rate | Tag |",
        "|---|---|---|---:|---:|---|",
    ]
    counts = defaultdict(Counter)
    for (model, task, drift), rows in sorted(cells.items()):
        n, c = len(rows), sum(r["grade"]["passed"] for r in rows)
        label = tag(c, n)
        counts[(model, "all")][label] += 1
        counts[(model, drift)][label] += 1
        lines.append(f"| {model} | {task} | {drift} | {c}/{n} | {c / n:.1%} | {label} |")
    lines += [
        "",
        "## Tag counts",
        "",
        "| Model | Drift | too_easy | calibrated | too_hard |",
        "|---|---|---:|---:|---:|",
    ]
    for (model, drift), counter in sorted(counts.items()):
        lines.append(f"| {model} | {drift} | " + " | ".join(str(counter[t]) for t in TAGS) + " |")
    errors = Counter(e["error"] for e in episodes if e.get("error"))
    lines += ["", "## Agent and infrastructure errors", ""]
    lines += [f"- {error}: {count}" for error, count in sorted(errors.items())] or ["None."]
    lines += [
        "",
        "Tags are noisy. At k=8, calibrated means 1 or 2 passes and too_hard means 0; a cell",
        "whose true rate is 20% scores 0/8 about 17% of the time. Each row logs its k.",
        "",
    ]
    return "\n".join(lines)


def write_calibration(path: Path) -> Path:
    episodes = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    output = path.with_name("calibration.md")
    output.write_text(render(episodes), encoding="utf-8")
    return output
