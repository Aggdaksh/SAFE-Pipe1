"""Validate the frozen 96-run log and export a flat, shareable run table."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from safe_pipe.features import PRE_RUN_COLUMNS
from safe_pipe.grid import get_config
from safe_pipe.memory import parse_gb
from safe_pipe.schemas import DatasetManifest, FailureCategory, RunStatus, WorkloadFamily
from safe_pipe.store.jsonl import read_runs


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, default=Path("data/runs/main_v1.jsonl"))
    parser.add_argument("--index", type=Path, default=Path("configs/datasets_main_v1.json"))
    parser.add_argument("--sla", type=Path, default=Path("configs/family_sla_main_v1.json"))
    parser.add_argument("--plan", type=Path, default=Path("configs/matrix_plan_main_v1.json"))
    parser.add_argument("--output", type=Path, default=Path("data/curated"))
    args = parser.parse_args()

    rows = read_runs(args.store)
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    sla = json.loads(args.sla.read_text(encoding="utf-8"))
    manifests = {
        item.family: item
        for value in json.loads(args.index.read_text(encoding="utf-8"))
        for item in [DatasetManifest.model_validate(value)]
    }
    if len(rows) != 96 or len(plan["cells"]) != 96:
        raise ValueError(f"expected 96 physical rows and plan cells, found {len(rows)} rows")
    if plan["data_version"] != sla["data_version"] or set(manifests) != set(WorkloadFamily):
        raise ValueError("frozen input versions or family set differ")

    flat = []
    seen = set()
    for position, (run, cell) in enumerate(zip(rows, plan["cells"]), start=1):
        family = run.workload.family
        key = (family.value, run.config.config_id, run.repeat_id)
        expected = (cell["family"], cell["config_id"], cell["repeat_id"])
        if key != expected or key in seen:
            raise ValueError(f"row {position}: missing, duplicate, or out-of-order matrix cell")
        seen.add(key)
        manifest = manifests[family]
        config = get_config(run.config.config_id)
        expected_sla = float(sla["families"][family.value]["sla_seconds"])
        if run.backend != "dask_local" or run.data_version != plan["data_version"] or run.voided:
            raise ValueError(f"row {position}: backend, version, or void flag mismatch")
        if run.config != config or run.workload.input_bytes != manifest.input_bytes or run.workload.estimated_rows != manifest.n_rows:
            raise ValueError(f"row {position}: config or pre-run workload mismatch")
        if run.sla_seconds != expected_sla:
            raise ValueError(f"row {position}: SLA differs from pre-frozen deadline")
        if run.engine_seconds is None or run.engine_seconds <= 0:
            raise ValueError(f"row {position}: missing duration")
        if run.status is RunStatus.SUCCESS and run.failure_category is not FailureCategory.NONE:
            raise ValueError(f"row {position}: successful run has a failure category")
        flat.append(
            {
                "run_id": run.run_id,
                "family": family.value,
                "config_id": run.config.config_id,
                "repeat_id": run.repeat_id,
                "data_version": run.data_version,
                "hardware_class": "windows_32gb",
                "backend": run.backend,
                "input_bytes": run.workload.input_bytes,
                "estimated_rows": run.workload.estimated_rows,
                "file_count": run.workload.file_count,
                "partition_count": run.workload.partition_count,
                "skew_score": run.workload.skew_score,
                "dataset_sha256": manifest.sha256,
                "n_workers": config.native.n_workers,
                "threads_per_worker": config.native.threads_per_worker,
                "memory_limit": config.native.memory_limit,
                "memory_limit_gb": parse_gb(config.native.memory_limit),
                "allocated_vcpus": config.allocated_vcpus,
                "allocated_gb": config.allocated_gb,
                "sla_seconds": expected_sla,
                "status": run.status.value,
                "failure_category": run.failure_category.value,
                "engine_seconds": run.engine_seconds,
                "sla_miss": run.status is not RunStatus.SUCCESS or run.engine_seconds > expected_sla,
                "peak_memory_bytes": run.peak_memory_bytes,
            }
        )

    frame = pd.DataFrame(flat)
    if not set(PRE_RUN_COLUMNS) <= set(frame) or {"engine_seconds", "status"} & set(PRE_RUN_COLUMNS):
        raise ValueError("model feature whitelist is invalid")
    args.output.mkdir(parents=True, exist_ok=True)
    csv_path = args.output / "runs.csv"
    parquet_path = args.output / "runs.parquet"
    frame.to_csv(csv_path, index=False)
    frame.to_parquet(parquet_path, index=False)
    summary = {
        "data_version": plan["data_version"],
        "rows": len(frame),
        "unique_cells": len(seen),
        "status_counts": dict(Counter(frame.status)),
        "sla_misses": int(frame.sla_miss.sum()),
        "raw_jsonl_sha256": _sha256(args.store),
        "curated_csv_sha256": _sha256(csv_path),
        "curated_parquet_sha256": _sha256(parquet_path),
        "model_pre_run_columns": PRE_RUN_COLUMNS,
    }
    (args.output / "audit.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
