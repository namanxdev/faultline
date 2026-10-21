"""Commands to seed a database, run evaluations, and regenerate reports."""

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from faultline import __version__
from faultline.calibrate import sample, write_calibration
from faultline.db import seed_database
from faultline.environment import DRIFTS
from faultline.harbor import export
from faultline.llm import CALIBRATION_MODEL, DEFAULT_MODEL, MODELS, NOTES, PHASE_CAPS
from faultline.report import write_report
from faultline.runner import AGENTS, run
from faultline.tasks import SPLIT_DRIFTS, SPLITS, load
from faultline.validate import validate


def main() -> None:
    load_dotenv(Path.cwd() / ".env", override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("seed")
    seed.add_argument("path", type=Path)
    report = commands.add_parser("report")
    report.add_argument("episodes", type=Path)
    evaluate = commands.add_parser("run")
    evaluate.add_argument("--agent", choices=AGENTS, default="reference")
    evaluate.add_argument("--split", choices=["seed", *SPLITS], default="seed")
    evaluate.add_argument("--first", type=int, help="Use only the split's first N tasks")
    evaluate.add_argument("--drifts", nargs="+", choices=DRIFTS, help="Default: the split's")
    evaluate.add_argument("--trials", type=int, default=3)
    evaluate.add_argument("--concurrency", type=int, default=6)
    evaluate.add_argument("--seed", type=int, default=1729)
    evaluate.add_argument("--budget-usd", type=float, default=5.0)
    evaluate.add_argument("--model", choices=sorted(MODELS), default=DEFAULT_MODEL)
    evaluate.add_argument("--phase", type=int, choices=sorted(PHASE_CAPS), default=1)
    evaluate.add_argument("--ledger", type=Path, default=Path("runs/spend-ledger.jsonl"))
    evaluate.add_argument("--notes", choices=sorted(NOTES), default="stale")
    evaluate.add_argument("--output", type=Path, required=True)
    calibrate = commands.add_parser("calibrate")
    calibrate.add_argument("--model", choices=sorted(MODELS), default=CALIBRATION_MODEL)
    calibrate.add_argument("--split", choices=["seed", *SPLITS], default="train")
    calibrate.add_argument("--k", type=int, default=8)
    calibrate.add_argument("--concurrency", type=int, default=6)
    calibrate.add_argument("--seed", type=int, default=1729)
    calibrate.add_argument("--budget-usd", type=float, default=0.5)
    calibrate.add_argument("--phase", type=int, choices=sorted(PHASE_CAPS), default=2)
    calibrate.add_argument("--ledger", type=Path, default=Path("runs/spend-ledger.jsonl"))
    source = calibrate.add_mutually_exclusive_group(required=True)
    source.add_argument("--output", type=Path, help="Run a new paid calibration here")
    source.add_argument("--episodes", type=Path, help="Re-tag an existing episodes.jsonl")
    hb = commands.add_parser("harbor-export", help="Write Harbor task folders")
    hb.add_argument("--split", choices=["seed", *SPLITS], default="test")
    hb.add_argument("--first", type=int)
    hb.add_argument("--drifts", nargs="+", choices=DRIFTS, help="Default: the split's")
    hb.add_argument(
        "--wheel", type=Path, default=Path(f"dist/faultline-{__version__}-py3-none-any.whl")
    )
    hb.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("validate")
    check.add_argument("--splits", nargs="+", choices=["seed", *SPLITS], default=["seed", *SPLITS])
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "seed":
            seed_database(args.path)
            print(args.path)
        elif args.command == "report":
            print(write_report(args.episodes))
        elif args.command == "calibrate":
            episodes = args.episodes
            if episodes is None:
                asyncio.run(
                    run(
                        args.output,
                        "llm",
                        None,
                        args.k,
                        args.concurrency,
                        args.seed,
                        args.budget_usd,
                        args.model,
                        args.phase,
                        args.ledger,
                        split=args.split,
                        items=sample(args.split),
                    )
                )
                episodes = args.output / "episodes.jsonl"
            print(write_calibration(episodes))
        elif args.command == "harbor-export":
            if not args.wheel.is_file():
                parser.error(f"{args.wheel} not found; run `uv build --wheel` first")
            tasks = load(args.split)[: args.first]
            drifts = args.drifts or SPLIT_DRIFTS[args.split]
            written = export([(t, d) for t in tasks for d in drifts], args.output, args.wheel)
            print(f"{len(written)} Harbor tasks in {args.output}")
        elif args.command == "validate":
            tasks = [task for split in args.splits for task in load(split)]
            args.output.parent.mkdir(parents=True, exist_ok=True)
            summary = asyncio.run(validate(tasks))
            args.output.write_text(summary, encoding="utf-8")
            print(args.output)
            if "## Unexpected results\n\nNone." not in summary:
                parser.exit(1, "Validation found unexpected results.\n")
        else:
            results = asyncio.run(
                run(
                    args.output,
                    args.agent,
                    tuple(args.drifts) if args.drifts else None,
                    args.trials,
                    args.concurrency,
                    args.seed,
                    args.budget_usd,
                    args.model,
                    args.phase,
                    args.ledger,
                    args.notes,
                    args.split,
                    first=args.first,
                )
            )
            passed = sum(row["grade"]["passed"] for row in results)
            print(f"{passed}/{len(results)} passed. Report: {args.output / 'report.md'}")
            if args.agent == "llm" and any(row["error"] for row in results):
                parser.exit(
                    1, "LLM run has errors. Inspect episodes.jsonl before claiming completion.\n"
                )
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
