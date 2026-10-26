"""Measure three successful 2 GB pilots per family, then freeze SLA deadlines."""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path

from safe_pipe.collector import collect_dask
from safe_pipe.grid import get_config
from safe_pipe.schemas import DatasetManifest, RunStatus, WorkloadFamily
from safe_pipe.store.jsonl import append_run
from safe_pipe.workloads.generate import verify_manifest, workload_from_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/generated/main-v1"))
    parser.add_argument("--index", type=Path, default=Path("configs/datasets_main_v1.json"))
    parser.add_argument("--output", type=Path, default=Path("configs/family_sla_main_v1.json"))
    parser.add_argument("--pilot-store", type=Path, default=Path("data/probes/sla_main_v1/runs.jsonl"))
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    if args.output.exists() or args.pilot_store.exists():
        parser.error("SLA output or pilot log already exists; refusing to mix pilots")
    manifests = {
        manifest.family: manifest
        for item in json.loads(args.index.read_text(encoding="utf-8"))
        for manifest in [DatasetManifest.model_validate(item)]
    }
    if set(manifests) != set(WorkloadFamily):
        raise ValueError("index must contain exactly four families")
    for family, manifest in manifests.items():
        verify_manifest(manifest, args.data_dir / family.value)

    cells = [(family, repeat) for family in WorkloadFamily for repeat in (1, 2, 3)]
    random.Random(2026).shuffle(cells)
    times: dict[WorkloadFamily, list[float]] = {family: [] for family in WorkloadFamily}
    for family, repeat_id in cells:
        manifest = manifests[family]
        result = collect_dask(
            family=family,
            dataset_dir=args.data_dir / family.value,
            workload=workload_from_manifest(manifest, skew_score=1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1),
            config=get_config("w1_t1_2g"),
            timeout_s=args.timeout,
            repeat_id=repeat_id,
            data_version=manifest.data_version,
        )
        append_run(args.pilot_store, result)
        print(json.dumps({"family": family.value, "repeat": repeat_id, "status": result.status.value, "seconds": result.engine_seconds}), flush=True)
        if result.status is not RunStatus.SUCCESS or result.engine_seconds is None:
            raise RuntimeError(f"pilot failed for {family.value}; inspect {args.pilot_store}")
        times[family].append(result.engine_seconds)

    payload = {
        "data_version": "main-v1",
        "method": "1.5 times median of three w1_t1_2g pilot engine times, rounded up to 0.1s",
        "families": {
            family.value: {
                "pilot_seconds": sorted(values),
                "median_seconds": statistics.median(values),
                "sla_seconds": math.ceil(1.5 * statistics.median(values) * 10) / 10,
            }
            for family, values in times.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
