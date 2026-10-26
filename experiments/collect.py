"""Collect one pandas cell (8GB Mac) or, later, a Dask cell on the 16GB PC."""

from __future__ import annotations

import argparse
from pathlib import Path

from safe_pipe.collector import collect_pandas
from safe_pipe.grid import get_config
from safe_pipe.schemas import WorkloadFamily
from safe_pipe.store.jsonl import append_run
from safe_pipe.workloads.generate import generate_family, workload_from_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True, choices=[f.value for f in WorkloadFamily])
    parser.add_argument("--config-id", default="w1_t1_1g")
    parser.add_argument("--data-dir", default="data/generated")
    parser.add_argument("--store", default="data/runs/runs.jsonl")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--backend", choices=["pandas"], default="pandas")
    args = parser.parse_args()
    if args.backend != "pandas":
        raise SystemExit("Only pandas backend is allowed on the 8GB coding Mac.")

    family = WorkloadFamily(args.family)
    dest = Path(args.data_dir)
    manifest = generate_family(family, dest)
    workload = workload_from_manifest(manifest, skew_score=1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1)
    config = get_config(args.config_id)
    result = collect_pandas(
        family=family,
        dataset_dir=Path(manifest.path),
        workload=workload,
        config=config,
        timeout_s=args.timeout,
    )
    append_run(Path(args.store), result)
    print(result.model_dump_json(indent=2))
    return 0 if result.status.value == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
