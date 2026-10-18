"""Tag each task × drift cell by a cheap model's pass rate, to keep training tasks learnable."""

import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

from faultline.tasks import SPLIT_DRIFTS, SPLITS, TEMPLATES, generate, load

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


def sample(split: str) -> list | None:
    """The first task of each template under every drift of the split; None means all."""
    if split == "seed":
        return None
    tasks = load(split)
    firsts = [next(t for t in tasks if t.template == template) for template in TEMPLATES]
    return [(task, drift) for task in firsts for drift in SPLIT_DRIFTS[split]]


def cell(episode: dict) -> str:
    # Generated tasks are tagged per template: a template x drift tag covers all its tasks.
    template = episode.get("template")
    return template if template and template != "seed" else episode["ticket_id"]


def render(episodes: list[dict]) -> str:
    if not episodes:
        raise ValueError("No episodes to calibrate")
    cells = defaultdict(list)
    for e in episodes:
        cells[(e.get("model") or e["agent"], cell(e), e["drift"])].append(e)
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
    tags = {}
    for (model, task, drift), rows in sorted(cells.items()):
        n, c = len(rows), sum(r["grade"]["passed"] for r in rows)
        label = tags[(task, drift)] = tag(c, n)
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
    if any(e.get("template") not in (None, "seed") for e in episodes):
        lines += split_table(tags)[0]
    return "\n".join(lines)


def _row(split: str, stage: str, items: list, tags: dict) -> str:
    counts = Counter(tags.get((t.template, d), "untagged") for t, d in items)
    tasks = len({t.task_id for t, _ in items})
    share = counts["calibrated"] / len(items) if items else 0
    values = " | ".join(str(counts[k]) for k in (*TAGS, "untagged"))
    return f"| {split} | {stage} | {tasks} | {len(items)} | {values} | {share:.1%} |"


def split_table(tags: dict, minimum: int = SPLITS["train"][0]) -> tuple[list[str], dict]:
    """Tag mix per split as generated, then train filtered to calibrated items.

    Filtering keeps (task, drift) items whose template x drift cell is calibrated. If that
    leaves fewer than `minimum` distinct tasks, train is regenerated larger: generation is
    free and tags apply per template, so more tasks need no more API calls."""
    lines = [
        "## Splits before and after filtering",
        "",
        "One item is one task under one drift. Held-out combinations have no train tag.",
        "",
        "| Split | Stage | Tasks | Items | too_easy | calibrated | too_hard | untagged "
        "| Calibrated |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for split in SPLITS:
        items = [(t, d) for t in generate(split) for d in SPLIT_DRIFTS[split]]
        lines.append(_row(split, "as generated", items, tags))
    size = SPLITS["train"][0]
    while True:
        kept = [
            (t, d)
            for t in generate("train", size)
            for d in SPLIT_DRIFTS["train"]
            if tags.get((t.template, d)) == "calibrated"
        ]
        if len({t.task_id for t, _ in kept}) >= minimum or not kept:
            break
        size += len(TEMPLATES)
    lines += [_row("train", f"filtered (generated {size})", kept, tags), ""]
    return lines, {"size": size, "items": [[t.task_id, d] for t, d in kept]}


def write_calibration(path: Path) -> Path:
    episodes = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    output = path.with_name("calibration.md")
    output.write_text(render(episodes), encoding="utf-8")
    if any(e.get("template") not in (None, "seed") for e in episodes):
        passes = defaultdict(list)
        for e in episodes:
            passes[(cell(e), e["drift"])].append(e["grade"]["passed"])
        selection = split_table({k: tag(sum(v), len(v)) for k, v in passes.items()})[1]
        path.with_name("train-calibrated.json").write_text(json.dumps(selection), encoding="utf-8")
    return output
