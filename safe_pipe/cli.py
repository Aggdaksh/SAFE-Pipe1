from __future__ import annotations

import argparse
import json

from safe_pipe import __version__
from safe_pipe.optimizer import recommend
from safe_pipe.schemas import CandidateEstimate, ObjectiveSpec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="safe-pipe")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="cmd")

    rec = sub.add_parser("recommend", help="Rank candidate estimates from a JSON file")
    rec.add_argument("--estimates", required=True, help="JSON list of CandidateEstimate")
    rec.add_argument("--sla", type=float, required=True)
    rec.add_argument("--failure-limit", type=float, default=0.1)

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if args.cmd == "recommend":
        with open(args.estimates, encoding="utf-8") as fh:
            raw = json.load(fh)
        estimates = [CandidateEstimate.model_validate(row) for row in raw]
        decision = recommend(estimates, ObjectiveSpec(sla_seconds=args.sla, failure_limit=args.failure_limit))
        print(decision.model_dump_json(indent=2))
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
