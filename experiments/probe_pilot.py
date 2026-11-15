"""Prepare, resume and audit an isolated development-only probe matrix.

Run with python -m experiments.probe_pilot --help. No existing datasets/models are modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import time

from safe_pipe.research.probe_analysis import markdown_report, summarize

SCHEMA = "partition-probe-pilot-v1"
METHODS = ["full", "uniform", "uniform_memory", "partition_tail"]
MEMORY_FLOOR = 512 * 2**20
STAGE_A_SPEC = Path(__file__).resolve().parents[1] / "configs/research_stage_a_v1.json"


def stage_a_definition() -> dict:
    return json.loads(STAGE_A_SPEC.read_text(encoding="utf-8"))


def require_windows(preset: str) -> None:
    if preset in {"windows-screen", "windows-stage-a"} and platform.system() != "Windows":
        raise ValueError("This experiment's preparation and execution are Windows-only")


def source_fingerprints() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    files = ["experiments/probe_pilot.py", "safe_pipe/research/probe_workloads.py",
             "safe_pipe/research/probe_runner.py", "safe_pipe/research/probe_analysis.py",
             "safe_pipe/research/probe_diagnostics.py", "configs/research_stage_a_v1.json"]
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def mapped_config(target: dict, method: str, fraction: float) -> dict:
    result = dict(target)
    if method in ("uniform_memory", "partition_tail"):
        cap = int(target["memory_limit"])
        result["memory_limit"] = str(round(MEMORY_FLOOR + fraction * (cap - MEMORY_FLOOR)))
    result["base_config_id"] = target["config_id"]
    result["config_id"] = target["config_id"] + "__" + method
    return result


def preset_definition(preset: str) -> tuple[list[dict], list[dict], int]:
    if preset == "windows-stage-a":
        spec = stage_a_definition()
        recipes = [{"instance_id": f"{family}-{spec['n_rows']}-{pattern['name']}-s{spec['generation_seed']}",
                    "family": family, "seed": spec["generation_seed"],
                    **{k: spec[k] for k in ("n_rows", "n_files", "n_keys", "payload_columns", "generation_mode")},
                    **{k: pattern[k] for k in ("hot_fraction", "partition_imbalance")}}
                   for family in spec["families"] for pattern in spec["patterns"]]
        return recipes, spec["configs"], spec["repeats"]
    if preset not in {"smoke", "mac-limited", "mac-development", "windows-screen"}:
        raise ValueError("Unknown research preset")
    smoke = preset == "smoke"
    workers = [1, 2] if preset == "windows-screen" else [1]
    memory = [1_000_000_000] if smoke or preset == "mac-limited" else [1_000_000_000, 2_000_000_000]
    configs = [{"config_id": f"w{w}_t{t}_{m // 10**9}g", "n_workers": w,
                "threads_per_worker": t, "memory_limit": str(m)}
               for w in workers for t in [1, 2] for m in memory]
    recipes = []
    sizes = [500_000, 1_000_000, 2_000_000] if preset == "windows-screen" else [2048 if smoke else 1_000_000]
    patterns = ["balanced", "uneven"] if preset == "windows-screen" else ["uneven"]
    for family in ["groupby", "skewed_join"]:
        for size in sizes:
            for pattern in patterns:
                recipes.append({"instance_id": f"{family}-{size}-{pattern}", "family": family,
                                "n_rows": size, "n_files": 4 if smoke else 8, "seed": 731,
                                "n_keys": max(16, size // 2), "payload_columns": 4 if smoke else 16,
                                "hot_fraction": 0.25 if pattern == "uneven" else 0.0,
                                "partition_imbalance": 0.60 if pattern == "uneven" else 0.0})
    return recipes, configs, 1 if smoke else 2


def prepare(preset: str, out_dir: Path, seed: int | None = None) -> Path:
    require_windows(preset)  # Before importing generation code or making directories.
    frozen_source = source_fingerprints()
    from safe_pipe.research.probe_workloads import generate_instance, make_probe
    spec = stage_a_definition() if preset == "windows-stage-a" else None
    if spec and seed is not None and seed != spec["order_seed"]:
        raise ValueError("Stage A order seed is frozen in the versioned specification")
    seed = spec["order_seed"] if spec else (20261031 if seed is None else seed)
    methods = spec["methods"] if spec else METHODS
    out_dir = out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError("Choose an empty output directory; existing experiments are never overwritten.")
    out_dir.mkdir(parents=True, exist_ok=True)
    if spec:
        from safe_pipe.research.probe_diagnostics import host_conditions
        conditions = host_conditions(out_dir)
        if min(conditions["free_disk_bytes"], conditions["temp_free_disk_bytes"]) < spec["minimum_free_disk_bytes"]:
            raise ValueError("Stage A requires at least 10 GiB free on both input and temporary drives")
    prepare_started = time.monotonic()
    recipes, configs, repeats = preset_definition(preset)
    fraction = 0.25
    datasets = {}
    dataset_fingerprints = {}
    for recipe in recipes:
        instance_id = recipe["instance_id"]
        root = out_dir / "datasets" / instance_id
        full = generate_instance(root / "full", recipe)
        manifests = {"full": full}
        if not spec:
            manifests["uniform"] = make_probe(root / "full", root / "uniform", fraction=fraction, method="uniform", seed=seed)
            manifests["partition_tail"] = make_probe(root / "full", root / "partition_tail", fraction=fraction, method="partition_tail", seed=seed)
            manifests["uniform_memory"] = manifests["uniform"]
        datasets[instance_id] = {m: str((root / ("uniform" if m == "uniform_memory" else m)).relative_to(out_dir)) for m in methods}
        dataset_fingerprints[instance_id] = {m: canonical_hash(manifests[m]) for m in methods}
    cells = []
    rng = random.Random(seed)
    for repeat in range(1, repeats + 1):
        block = []
        for instance_id in datasets:
            for config in configs:
                for method in methods:
                    cell = {"instance_id": instance_id, "target_config_id": config["config_id"],
                            "method": method, "repeat_id": repeat,
                            "run_config": mapped_config(config, method, fraction)}
                    cell["cell_id"] = canonical_hash(cell)[:24]
                    block.append(cell)
        rng.shuffle(block)
        cells.extend(block)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    plan = {"schema_version": SCHEMA, "created_utc": datetime.now(timezone.utc).isoformat(),
            "git_base_revision": revision, "preset": preset, "role": "development_only",
            "source_fingerprints": frozen_source,
            "seed": seed, "fraction": fraction, "memory_floor_bytes": MEMORY_FLOOR,
            "memory_mapping": "floor + fraction * (target - floor); heuristic, not measured pressure equivalence",
            "methods": methods, "configs": configs, "recipes": recipes, "repeats": repeats,
            "ranking_tolerance": 0.05, "timeout_seconds": spec["timeout_seconds"] if spec else (90 if preset == "smoke" else 180),
            "datasets": datasets, "dataset_fingerprints": dataset_fingerprints, "cells": cells}
    plan["preparation_total_seconds"] = time.monotonic() - prepare_started
    if spec:
        if len(cells) != spec["planned_cells"]:
            raise ValueError("Stage A cell count does not match specification")
        from safe_pipe.research.probe_runner import _environment
        plan.update(protocol=spec, protocol_sha256=canonical_hash(spec), fraction=1.0,
                    frozen_environment=_environment(),
                    memory_mapping="none; full inputs at target memory caps")
    if frozen_source != source_fingerprints():
        raise ValueError("Research source changed during preparation; preserve this partial directory and prepare a new version")
    path = out_dir / "plan.json"
    path.write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps({"plan": str(path), "planned_cells": len(cells), "preset": preset,
                      "note": "Development-only matrix; no experiments have run yet."}))
    return path


def load_plan(path: Path) -> tuple[dict, str]:
    plan = json.loads(path.read_text())
    if plan["schema_version"] != SCHEMA:
        raise ValueError("Unsupported research plan schema")
    if len({c["cell_id"] for c in plan["cells"]}) != len(plan["cells"]):
        raise ValueError("Duplicate cells in plan")
    for cell in plan["cells"]:
        if canonical_hash({k: v for k, v in cell.items() if k != "cell_id"})[:24] != cell["cell_id"]:
            raise ValueError("Cell parameters do not match frozen identity")
    return plan, canonical_hash(plan)


def load_records(path: Path, plan_hash: str) -> list[dict]:
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if any(r["plan_sha256"] != plan_hash for r in rows):
        raise ValueError("Run file belongs to another/modified plan")
    if len({r["cell_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate run cells; do not silently select favorable repeats")
    return rows


def run(path: Path, max_runs: int) -> None:
    from safe_pipe.research.probe_runner import run_probe, validate_host_budget
    from safe_pipe.research.probe_workloads import load_manifest
    plan, fingerprint = load_plan(path)
    if max_runs < 1:
        raise ValueError("max-runs must be positive")
    require_windows(plan["preset"])
    root = path.resolve().parent
    if plan.get("source_fingerprints", source_fingerprints()) != source_fingerprints():
        raise ValueError("Research source changed since preparation; prepare a new versioned experiment")
    if plan.get("frozen_environment"):
        from safe_pipe.research.probe_runner import _environment
        if _environment() != plan["frozen_environment"]:
            raise ValueError("Experiment environment changed; restore the frozen packages/host before resuming")
    rows_path = root / "runs.jsonl"
    lock_path = root / ".running.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, f"{os.getpid()}\n".encode())
        records = load_records(rows_path, fingerprint)
        # Reject unknown identities before resuming; failed physical attempts remain completed cells.
        summarize(plan, records)
        completed = {r["cell_id"] for r in records}
        unresolved = [p for p in (root / "attempts").glob("*.json") if p.stem not in completed]
        if unresolved:
            raise ValueError("Unresolved physical attempt marker: inspect raw diagnostics before any resume; never silently rerun it")
        batch_started = time.monotonic()
        # Audit data once per invocation, outside per-job timing; prohibit mutated samples on resume.
        audited = set()
        for instance_id, methods in plan["datasets"].items():
            for method, relative_path in methods.items():
                dataset = (root / relative_path).resolve()
                if not dataset.is_relative_to(root):
                    raise ValueError("Dataset path escapes experiment directory")
                manifest = load_manifest(dataset, verify=dataset not in audited)
                if canonical_hash(manifest) != plan["dataset_fingerprints"][instance_id][method]:
                    raise ValueError("Dataset manifest differs from frozen plan")
                audited.add(dataset)
        audit_seconds = time.monotonic() - batch_started
        batch_id = datetime.now(timezone.utc).isoformat()
        with (root / "batches.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"batch_id": batch_id, "plan_sha256": fingerprint,
                                "verification_seconds_shared": audit_seconds, "datasets_verified": len(audited)}) + "\n")
        spec = plan.get("protocol", {})
        count = 0
        for cell in plan["cells"]:
            if cell["cell_id"] in completed:
                continue
            if count >= max_runs:
                break
            validate_host_budget(cell["run_config"])
            dataset = root / plan["datasets"][cell["instance_id"]][cell["method"]]
            manifest = load_manifest(dataset)
            from safe_pipe.research.probe_diagnostics import host_conditions
            conditions = host_conditions(root)
            if spec.get("require_mains") and conditions["battery_present"] and conditions["power_plugged"] is not True:
                raise ValueError("Connect the experiment laptop to mains before resuming")
            if min(conditions["free_disk_bytes"], conditions["temp_free_disk_bytes"]) < spec.get("minimum_free_disk_bytes", 0):
                raise ValueError("Insufficient free disk before next cell; no attempt started")
            marker = root / "attempts" / (cell["cell_id"] + ".json")
            marker.parent.mkdir(exist_ok=True)
            with marker.open("x", encoding="utf-8") as f:
                f.write(json.dumps({"cell": cell, "plan_sha256": fingerprint, "batch_id": batch_id}) + "\n")
                f.flush()
                os.fsync(f.fileno())
            print(json.dumps({"starting": cell["cell_id"], "instance": cell["instance_id"], "method": cell["method"],
                              "target": cell["target_config_id"], "repeat": cell["repeat_id"]}), flush=True)
            record = run_probe(dataset, cell["run_config"], timeout_s=plan["timeout_seconds"],
                               repeat_id=cell["repeat_id"], session_id=fingerprint[:16],
                               diagnostics_dir=root / "diagnostics" / cell["cell_id"],
                               require_mains=spec.get("require_mains", False))
            record.update(cell)
            record.update(plan_sha256=fingerprint, manifest_sha256=canonical_hash(manifest),
                          dataset_path=plan["datasets"][cell["instance_id"]][cell["method"]])
            record["batch_id"] = batch_id
            if record.get("diagnostics", {}).get("directory"):
                record["diagnostics"]["directory"] = str(Path(record["diagnostics"]["directory"]).relative_to(root))
            persist_started = time.monotonic()
            with rows_path.open("a") as f:
                f.write(json.dumps(record, allow_nan=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            marker.unlink()
            with (root / "batches.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"batch_id": batch_id, "cell_id": cell["cell_id"],
                                   "row_persistence_seconds": time.monotonic() - persist_started}) + "\n")
            count += 1
            print(json.dumps({"finished": cell["cell_id"], "status": record["status"], "timings": record.get("timings")}), flush=True)
            if record["status"] == "interrupted":
                print("Operator interruption recorded; no further cells will start.", flush=True)
                break
            if record.get("conditions", {}).get("flags") or record["status"] in {"cleanup_error", "process_error", "startup_error"}:
                print("Condition/infrastructure issue retained; review before resuming.", flush=True)
                break
            diagnostic = record.get("diagnostics") or {}
            if diagnostic.get("summary_error") or diagnostic.get("log_write_errors") or diagnostic.get("log_truncated"):
                print("Incomplete diagnostics retained; review before resuming.", flush=True)
                break
        print(json.dumps({"new_records": count, "already_recorded": len(completed), "planned": len(plan["cells"])}))
    finally:
        os.close(fd)
        lock_path.unlink()


def analyze(path: Path) -> None:
    plan, fingerprint = load_plan(path)
    root = path.resolve().parent
    records = load_records(root / "runs.jsonl", fingerprint)
    summary = summarize(plan, records)
    summary["plan_sha256"] = fingerprint
    (root / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    (root / "REPORT.md").write_text(markdown_report(summary))
    print(json.dumps({"report": str(root / "REPORT.md"), "recorded": len(records), "planned": len(plan["cells"]),
                      "statuses": dict(Counter(r["status"] for r in records))}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--preset", choices=["smoke", "mac-limited", "mac-development", "windows-screen", "windows-stage-a"], default="smoke")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=None, help="Order/probe seed; Stage A fixes this in its versioned specification")
    for name in ("run", "analyze"):
        p = sub.add_parser(name)
        p.add_argument("--plan", type=Path, required=True)
        if name == "run":
            p.add_argument("--max-runs", type=int, default=4, help="Maximum new cells this invocation; failed cells remain recorded")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.preset, args.out_dir, args.seed)
        elif args.command == "run":
            if args.max_runs < 1:
                raise ValueError("max-runs must be positive")
            run(args.plan, args.max_runs)
        else:
            analyze(args.plan)
    except (ValueError, FileExistsError) as exc:
        parser.exit(2, f"Research runner: {exc}\n")


if __name__ == "__main__":
    main()
