"""Bind advisor support to the audited table and immutable fitted artifacts.

No fitting occurs. An arbitrary new index cannot expand a model's support.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from safe_pipe.advisor import frozen_profiles, sha256_lf
from safe_pipe.grid import load_grid
from safe_pipe.memory import parse_gb


def freeze(index: Path, model_dir: Path, table: Path, audit_path: Path) -> dict:
    """Freeze the existing main-v1 Windows matrix; not a general retraining API."""
    output = model_dir / "advisor_support.json"
    if output.exists():
        raise ValueError("advisor support already exists; use a new versioned artifact directory")
    meta = json.loads((model_dir / "runtime_meta.json").read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    raw = table.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    # Existing Windows audit hashes raw CRLF bytes. Git may check them out as LF.
    variants = {hashlib.sha256(v).hexdigest() for v in (raw, lf, lf.replace(b"\n", b"\r\n"))}
    if meta["table_sha256"] not in variants or audit["curated_csv_sha256"] not in variants:
        raise ValueError("model/audit do not match the supplied table (including newline variants)")
    with table.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != audit["rows"] or len({r["run_id"] for r in rows}) != len(rows):
        raise ValueError("invalid row count or duplicate run IDs")
    profiles = frozen_profiles(index)
    manifests = {m["family"]: m for m in json.loads(index.read_text(encoding="utf-8"))}
    if set(profiles) != {r["family"] for r in rows}:
        raise ValueError("profile families do not match the measured table")
    fields = ("input_bytes", "estimated_rows", "file_count", "partition_count", "skew_score")
    configs = load_grid()
    by_id = {c.config_id: c for c in configs}
    if len(by_id) != len(configs) or set(by_id) != {r["config_id"] for r in rows}:
        raise ValueError("configuration grid differs from the measured table")
    for row in rows:
        manifest = manifests[row["family"]]
        if (row["dataset_sha256"] != manifest["sha256"]
                or row["data_version"] != manifest["data_version"]):
            raise ValueError("dataset fingerprint/version differs from measured rows")
        if (row["data_version"] != "main-v1" or row["hardware_class"] != "windows_32gb"
                or row["backend"] != "dask_local"):
            raise ValueError("support freezer is scoped to the main-v1 Windows Dask matrix")
        profile = profiles[row["family"]]
        if any(float(row[name]) != getattr(profile, name) for name in fields):
            raise ValueError("profile descriptors differ from measured rows")
        config = by_id[row["config_id"]]
        expected = {"n_workers": config.native.n_workers,
                    "threads_per_worker": config.native.threads_per_worker,
                    "memory_limit_gb": parse_gb(config.native.memory_limit),
                    "allocated_vcpus": config.allocated_vcpus,
                    "allocated_gb": config.allocated_gb}
        if (row["memory_limit"] != config.native.memory_limit
                or not config.native.processes
                or any(float(row[name]) != value for name, value in expected.items())):
            raise ValueError("configuration resources differ from measured rows")
    expected_cells = {(family, config, repeat) for family in profiles for config in by_id for repeat in (1, 2, 3)}
    if {(r["family"], r["config_id"], int(r["repeat_id"])) for r in rows} != expected_cells or len(rows) != len(expected_cells):
        raise ValueError("expected three distinct repeats for every frozen profile/configuration")
    bundle = {
        "schema_version": 1,
        "table_sha256_lf": sha256_lf(table),
        "artifact_sha256_lf": {name: sha256_lf(model_dir / name) for name in
                               ("runtime_model.txt", "runtime_meta.json", "runtime_metrics.json")},
        "profile_index_sha256_lf": sha256_lf(index),
        "profiles": {name: profile.model_dump(mode="json") for name, profile in profiles.items()},
        "configurations": [c.model_dump(mode="json") for c in configs],
        "recorded_executions": len(rows),
        "recorded_failures": sum(row["status"] != "success" for row in rows),
        "scope": "Frozen descriptor profiles on the recorded Windows benchmark host only.",
        "feature_note": "main-v1 contains nominal memory and fixed skew tags; no feature relabeling or retraining occurred.",
    }
    output.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path("configs/datasets_main_v1.json"))
    parser.add_argument("--model-dir", type=Path, default=Path("artifacts/main_v1"))
    parser.add_argument("--table", type=Path, default=Path("data/curated/runs.csv"))
    parser.add_argument("--audit", type=Path, default=Path("data/curated/audit.json"))
    args = parser.parse_args()
    bundle = freeze(args.index, args.model_dir, args.table, args.audit)
    print(f"Bound {len(bundle['profiles'])} profiles to {bundle['recorded_executions']} audited executions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
