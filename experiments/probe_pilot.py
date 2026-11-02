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

from safe_pipe.research.probe_analysis import markdown_report, summarize

SCHEMA = "partition-probe-pilot-v1"
METHODS = ["full", "uniform", "uniform_memory", "partition_tail"]
MEMORY_FLOOR = 512 * 2**20


def source_fingerprints() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    files = ["experiments/probe_pilot.py", "safe_pipe/research/probe_workloads.py",
             "safe_pipe/research/probe_runner.py", "safe_pipe/research/probe_analysis.py"]
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


def prepare(preset: str, out_dir: Path, seed: int = 20261031) -> Path:
    from safe_pipe.research.probe_workloads import generate_instance, make_probe
    out_dir = out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError("Choose an empty output directory; existing experiments are never overwritten.")
    out_dir.mkdir(parents=True, exist_ok=True)
    recipes, configs, repeats = preset_definition(preset)
    fraction = 0.25
    datasets = {}
    dataset_fingerprints = {}
    for recipe in recipes:
        instance_id = recipe["instance_id"]
        root = out_dir / "datasets" / instance_id
        full = generate_instance(root / "full", recipe)
        uniform = make_probe(root / "full", root / "uniform", fraction=fraction, method="uniform", seed=seed)
        tail = make_probe(root / "full", root / "partition_tail", fraction=fraction, method="partition_tail", seed=seed)
        datasets[instance_id] = {m: str((root / ("uniform" if m == "uniform_memory" else m)).relative_to(out_dir)) for m in METHODS}
        dataset_fingerprints[instance_id] = {"full": canonical_hash(full), "uniform": canonical_hash(uniform),
                                             "uniform_memory": canonical_hash(uniform), "partition_tail": canonical_hash(tail)}
    cells = []
    rng = random.Random(seed)
    for repeat in range(1, repeats + 1):
        block = []
        for instance_id in datasets:
            for config in configs:
                for method in METHODS:
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
            "source_fingerprints": source_fingerprints(),
            "seed": seed, "fraction": fraction, "memory_floor_bytes": MEMORY_FLOOR,
            "memory_mapping": "floor + fraction * (target - floor); heuristic, not measured pressure equivalence",
            "methods": METHODS, "configs": configs, "recipes": recipes, "repeats": repeats,
            "ranking_tolerance": 0.05, "timeout_seconds": 90 if preset == "smoke" else 180,
            "datasets": datasets, "dataset_fingerprints": dataset_fingerprints, "cells": cells}
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
    root = path.resolve().parent
    if plan.get("source_fingerprints", source_fingerprints()) != source_fingerprints():
        raise ValueError("Research source changed since preparation; prepare a new versioned experiment")
    if plan["preset"] == "windows-screen" and platform.system() != "Windows":
        raise ValueError("The Windows screen is reserved for the experiment PC. Use mac-development here.")
    rows_path = root / "runs.jsonl"
    lock_path = root / ".running.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, f"{os.getpid()}\n".encode())
        records = load_records(rows_path, fingerprint)
        # Reject unknown identities before resuming; failed physical attempts remain completed cells.
        summarize(plan, records)
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
        completed = {r["cell_id"] for r in records}
        count = 0
        for cell in plan["cells"]:
            if cell["cell_id"] in completed:
                continue
            if count >= max_runs:
                break
            validate_host_budget(cell["run_config"])
            dataset = root / plan["datasets"][cell["instance_id"]][cell["method"]]
            manifest = load_manifest(dataset)
            print(json.dumps({"starting": cell["cell_id"], "instance": cell["instance_id"], "method": cell["method"],
                              "target": cell["target_config_id"], "repeat": cell["repeat_id"]}), flush=True)
            record = run_probe(dataset, cell["run_config"], timeout_s=plan["timeout_seconds"],
                               repeat_id=cell["repeat_id"], session_id=fingerprint[:16])
            record.update(cell)
            record.update(plan_sha256=fingerprint, manifest_sha256=canonical_hash(manifest),
                          dataset_path=plan["datasets"][cell["instance_id"]][cell["method"]])
            with rows_path.open("a") as f:
                f.write(json.dumps(record, allow_nan=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            count += 1
            print(json.dumps({"finished": cell["cell_id"], "status": record["status"], "timings": record.get("timings")}), flush=True)
            if record["status"] == "interrupted":
                print("Operator interruption recorded; no further cells will start.", flush=True)
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
    p.add_argument("--preset", choices=["smoke", "mac-limited", "mac-development", "windows-screen"], default="smoke")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20261031)
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
