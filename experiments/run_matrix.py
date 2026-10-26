"""Run a bounded batch of frozen matrix cells, one LocalCluster at a time."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from safe_pipe.collector import collect_dask
from safe_pipe.grid import get_config
from safe_pipe.matrix import planned_cells
from safe_pipe.schemas import DatasetManifest, RunResult, WorkloadFamily
from safe_pipe.store.jsonl import append_run, read_runs
from safe_pipe.workloads.generate import verify_manifest, workload_from_manifest


def cell_key(row: dict | RunResult) -> tuple[str, str, int]:
    if isinstance(row, RunResult):
        return (row.workload.family.value, row.config.config_id, row.repeat_id)
    return (str(row["family"]), str(row["config_id"]), int(row["repeat_id"]))


def pending_cells(plan: list[dict], existing: list[RunResult]) -> list[dict]:
    keys = [cell_key(cell) for cell in plan]
    expected = {cell_key(cell) for cell in planned_cells()}
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("frozen plan must contain exactly the declared 96 cells")
    completed = [cell_key(row) for row in existing]
    completed_set = set(completed)
    if len(completed) != len(completed_set) or not completed_set <= set(keys):
        raise ValueError("run log has duplicate or unexpected matrix cells")
    return [cell for cell in plan if cell_key(cell) not in completed_set]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/generated/main-v1"))
    parser.add_argument("--index", type=Path, default=Path("configs/datasets_main_v1.json"))
    parser.add_argument("--sla", type=Path, default=Path("configs/family_sla_main_v1.json"))
    parser.add_argument("--plan", type=Path, default=Path("configs/matrix_plan_main_v1.json"))
    parser.add_argument("--store", type=Path, default=Path("data/runs/main_v1.jsonl"))
    parser.add_argument("--max-jobs", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    if args.max_jobs < 1 or args.timeout <= 0:
        parser.error("max-jobs and timeout must be positive")

    plan_data = json.loads(args.plan.read_text(encoding="utf-8"))
    sla_data = json.loads(args.sla.read_text(encoding="utf-8"))
    if plan_data["data_version"] != sla_data["data_version"]:
        raise ValueError("plan and SLA data versions differ")
    manifests = {
        manifest.family: manifest
        for item in json.loads(args.index.read_text(encoding="utf-8"))
        for manifest in [DatasetManifest.model_validate(item)]
    }
    if set(manifests) != set(WorkloadFamily) or any(m.data_version != plan_data["data_version"] for m in manifests.values()):
        raise ValueError("manifest index must contain exactly four families in the plan version")
    for family, manifest in manifests.items():
        verify_manifest(manifest, args.data_dir / family.value)

    existing = read_runs(args.store)
    if any(row.backend != "dask_local" or row.data_version != plan_data["data_version"] for row in existing):
        raise ValueError("run log contains a different backend or data version")
    remaining = pending_cells(plan_data["cells"], existing)
    print(f"completed={len(existing)} remaining={len(remaining)} this_batch={min(args.max_jobs, len(remaining))}", flush=True)
    for cell in remaining[: args.max_jobs]:
        family = WorkloadFamily(cell["family"])
        manifest = manifests[family]
        sla_seconds = float(sla_data["families"][family.value]["sla_seconds"])
        start_wall = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        result = collect_dask(
            family=family,
            dataset_dir=args.data_dir / family.value,
            workload=workload_from_manifest(manifest, skew_score=1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1),
            config=get_config(cell["config_id"]),
            timeout_s=args.timeout,
            repeat_id=int(cell["repeat_id"]),
            data_version=manifest.data_version,
            sla_seconds=sla_seconds,
        )
        append_run(args.store, result)
        print(json.dumps({"started": start_wall, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "family": family.value, "config": cell["config_id"], "repeat": cell["repeat_id"], "status": result.status.value, "engine_seconds": result.engine_seconds}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
