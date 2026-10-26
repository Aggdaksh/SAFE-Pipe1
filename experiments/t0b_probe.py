"""T0b: generate about 50 MB of Parquet and compare 1 GB vs 2 GB Dask workers."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import psutil

from safe_pipe.collector import collect_dask
from safe_pipe.grid import get_config
from safe_pipe.schemas import WorkloadFamily
from safe_pipe.store.jsonl import append_run
from safe_pipe.workloads.generate import generate_family, workload_from_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T0b probe on the experiment PC")
    parser.add_argument(
        "--experiment-host",
        action="store_true",
        help="Required. Confirms this is the designated experiment PC.",
    )
    parser.add_argument("--target-mb", type=float, default=50.0)
    parser.add_argument("--family", choices=[f.value for f in WorkloadFamily], default="scan_filter")
    parser.add_argument("--output", type=Path, default=Path("data/probes/t0b"))
    parser.add_argument("--timeout", type=float, default=480.0)
    args = parser.parse_args(argv)
    if not args.experiment_host:
        print(
            "T0b starts Dask workers at 1GB and 2GB. "
            "Re-run with --experiment-host on the designated PC after T0 passes.",
            file=sys.stderr,
        )
        return 2
    if psutil.virtual_memory().total < 16 * 1024**3:
        print("T0b requires at least 16 GiB of physical RAM.", file=sys.stderr)
        return 2
    if not 1 <= args.target_mb <= 300 or args.timeout <= 0:
        parser.error("target-mb must be 1..300 and timeout must be positive")

    family = WorkloadFamily(args.family)
    sample = generate_family(family, args.output / "calibration", n_rows=100_000, n_files=2, data_version="t0b-calibration")
    target_bytes = int(args.target_mb * 1_000_000)
    rows = math.ceil(sample.n_rows * target_bytes / sample.input_bytes)
    manifest = generate_family(
        family,
        args.output / "dataset",
        n_rows=rows,
        n_files=16,
        seed=sample.seed,
        data_version="t0b-pilot-v1",
    )
    print(json.dumps({"rows": rows, "parquet_bytes": manifest.input_bytes, "target_bytes": target_bytes}), flush=True)
    workload = workload_from_manifest(manifest, skew_score=1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1)
    results = []
    for config_id in ("w1_t1_1g", "w1_t1_2g"):
        result = collect_dask(
            family=family,
            dataset_dir=Path(manifest.path),
            workload=workload,
            config=get_config(config_id),
            timeout_s=args.timeout,
            data_version=manifest.data_version,
        )
        append_run(args.output / "runs.jsonl", result)
        results.append(result)
        print(result.model_dump_json(indent=2), flush=True)
    print(json.dumps({"status": [r.status.value for r in results], "engine_seconds": [r.engine_seconds for r in results]}))
    return 0 if all(r.status.value == "success" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
