"""Commands to seed a database, run evaluations, and regenerate reports."""

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from faultline.db import seed_database
from faultline.environment import DRIFTS
from faultline.llm import DEFAULT_MODEL, MODELS, NOTES, PHASE_CAPS
from faultline.report import write_report
from faultline.runner import AGENTS, run


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
    evaluate.add_argument("--drifts", nargs="+", choices=DRIFTS, default=list(DRIFTS))
    evaluate.add_argument("--trials", type=int, default=3)
    evaluate.add_argument("--concurrency", type=int, default=6)
    evaluate.add_argument("--seed", type=int, default=1729)
    evaluate.add_argument("--budget-usd", type=float, default=5.0)
    evaluate.add_argument("--model", choices=sorted(MODELS), default=DEFAULT_MODEL)
    evaluate.add_argument("--phase", type=int, choices=sorted(PHASE_CAPS), default=1)
    evaluate.add_argument("--ledger", type=Path, default=Path("runs/spend-ledger.jsonl"))
    evaluate.add_argument("--notes", choices=sorted(NOTES), default="stale")
    evaluate.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "seed":
            seed_database(args.path)
            print(args.path)
        elif args.command == "report":
            print(write_report(args.episodes))
        else:
            results = asyncio.run(
                run(
                    args.output,
                    args.agent,
                    tuple(args.drifts),
                    args.trials,
                    args.concurrency,
                    args.seed,
                    args.budget_usd,
                    args.model,
                    args.phase,
                    args.ledger,
                    args.notes,
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
