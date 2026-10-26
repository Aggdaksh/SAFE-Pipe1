from __future__ import annotations

import argparse
import json
from pathlib import Path

from safe_pipe import __version__
from safe_pipe.grid import load_grid
from safe_pipe.optimizer import recommend
from safe_pipe.schemas import CandidateEstimate, ObjectiveSpec, WorkloadFamily
from safe_pipe.workloads.generate import generate_family, write_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="safe-pipe")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="cmd")

    rec = sub.add_parser("recommend", help="Rank candidate estimates from a JSON file")
    rec.add_argument("--estimates", required=True, help="JSON list of CandidateEstimate")
    rec.add_argument("--sla", type=float, required=True)
    rec.add_argument("--failure-limit", type=float, default=0.1)

    sub.add_parser("grid", help="Print the frozen 8 Dask configs")

    gen = sub.add_parser("generate", help="Write tiny Parquet families (8GB-Mac safe)")
    gen.add_argument("--dest", default="data/generated")
    gen.add_argument("--family", choices=[f.value for f in WorkloadFamily], action="append")

    col = sub.add_parser("collect", help="Run one tiny pandas cell and append JSONL")
    col.add_argument("--family", required=True, choices=[f.value for f in WorkloadFamily])
    col.add_argument("--config-id", default="w1_t1_1g")
    col.add_argument("--data-dir", default="data/generated")
    col.add_argument("--store", default="data/runs/runs.jsonl")
    col.add_argument("--timeout", type=float, default=30.0)

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
    if args.cmd == "grid":
        print(json.dumps([c.model_dump() for c in load_grid()], indent=2))
        return 0
    if args.cmd == "generate":
        families = [WorkloadFamily(f) for f in (args.family or [x.value for x in WorkloadFamily])]
        dest = Path(args.dest)
        manifests = [generate_family(family, dest) for family in families]
        write_index(dest, manifests)
        print(json.dumps([m.model_dump() for m in manifests], indent=2))
        return 0
    if args.cmd == "collect":
        from safe_pipe.collector import collect_pandas
        from safe_pipe.grid import get_config
        from safe_pipe.store.jsonl import append_run
        from safe_pipe.workloads.generate import workload_from_manifest

        family = WorkloadFamily(args.family)
        dest = Path(args.data_dir)
        manifest = generate_family(family, dest)
        skew = 1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1
        result = collect_pandas(
            family=family,
            dataset_dir=Path(manifest.path),
            workload=workload_from_manifest(manifest, skew_score=skew),
            config=get_config(args.config_id),
            timeout_s=args.timeout,
        )
        append_run(Path(args.store), result)
        print(result.model_dump_json(indent=2))
        return 0 if result.status.value == "success" else 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
