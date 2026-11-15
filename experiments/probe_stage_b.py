"""Prepare Stage B from the exact completed Stage A; all physical work is Windows-only."""
from __future__ import annotations

import argparse
import csv
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time

from experiments import probe_pilot as pilot
from safe_pipe.research.probe_fidelity import compact_outcome

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "configs/research_stage_b_v1.json"
PRESET = "windows-stage-b"


def specification() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def within(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if Path(relative).is_absolute() or not candidate.is_relative_to(root.resolve()):
        raise ValueError("Evidence path escapes its experiment directory")
    return candidate


def verify_diagnostics(root: Path, records: list[dict]) -> int:
    checked = 0
    for row in records:
        diagnostic = row.get("diagnostics") or {}
        if not diagnostic.get("retained") or not diagnostic.get("directory") or not diagnostic.get("files"):
            raise ValueError("Retained raw diagnostics are required")
        folder = within(root, diagnostic["directory"])
        for item in diagnostic["files"]:
            path = within(folder, item["file"])
            if path.stat().st_size != item["bytes"] or file_hash(path) != item["sha256"]:
                raise ValueError("Raw diagnostic file differs from its saved hash")
            checked += 1
        memory_events = diagnostic.get("nanny_memory_termination_events", [])
        if "nanny_memory_termination_count" in diagnostic and len(memory_events) != diagnostic["nanny_memory_termination_count"]:
            raise ValueError("Nanny evidence count differs from retained events")
        for event in memory_events:
            found = False
            for line in within(folder, event["source"]).read_text(encoding="utf-8").splitlines():
                try:
                    saved = json.loads(line)
                except ValueError:
                    continue  # Malformed/truncated evidence remains a separate quality flag.
                if saved.get("message") == event["message"] and saved.get("phase") == event["phase"] and saved.get("utc") == event["utc"]:
                    found = True
                    break
            if not found:
                raise ValueError("Claimed nanny event is absent from its saved raw log")
    return checked


def reference_bundle(path: Path, spec: dict) -> tuple[dict, dict, dict]:
    """Verify source compatibility and raw provenance without modifying Stage A."""
    from safe_pipe.research.probe_runner import _environment
    from safe_pipe.research.probe_workloads import load_manifest

    parent, fingerprint = pilot.load_plan(path)
    expected = json.loads((ROOT / spec["reference_export"]).read_text(encoding="utf-8"))
    if fingerprint != spec["reference_plan_sha256"] or pilot.canonical_hash(expected) != fingerprint:
        raise ValueError("Reference must be the exact completed Stage A plan pinned in the Stage B specification")
    if parent.get("preset") != "windows-stage-a" or parent["protocol"]["protocol_id"] != spec["reference_protocol_id"]:
        raise ValueError("Wrong reference experiment")
    if parent["frozen_environment"] != _environment():
        raise ValueError("Stage B must use the same recorded Windows environment as Stage A")
    # Collector, operator, generation and diagnostic semantics are unchanged.
    # Orchestration/reporting files may differ in the explicitly versioned new stage.
    for name in spec["compatible_execution_sources"]:
        if file_hash(ROOT / name) != parent["source_fingerprints"][name]:
            raise ValueError(f"Stage A execution semantics changed: {name}; a separate compatibility study is required")
    root = path.resolve().parent
    if (root / ".running.lock").exists() or list((root / "attempts").glob("*.json")):
        raise ValueError("Stage A has an active lock or unresolved attempt")
    rows = pilot.load_records(root / "runs.jsonl", fingerprint)
    expected_cells = {c["cell_id"]: c for c in parent["cells"]}
    if len(rows) != 48 or {r["cell_id"] for r in rows} != set(expected_cells):
        raise ValueError("Stage A requires all 48 unique retained attempts, including failures")
    for row in rows:
        cell = expected_cells[row["cell_id"]]
        for key in ("instance_id", "method", "target_config_id", "repeat_id", "run_config"):
            if row[key] != cell[key]:
                raise ValueError("Stage A raw record identity mismatch")
        if row["config"] != cell["run_config"] or row["environment"] != parent["frozen_environment"]:
            raise ValueError("Stage A measured config/environment mismatch")
    compact = [compact_outcome(row) for row in rows]
    if any(row["quality_issues"] for row in compact):
        raise ValueError("Stage A has incomplete/confounded evidence; review before using it as a reference")
    published_path = (ROOT / spec["reference_export"]).with_name("measurements.csv")
    with published_path.open(encoding="utf-8-sig", newline="") as stream:
        published_rows = list(csv.DictReader(stream))
    published = {r["cell_id"]: r for r in published_rows}
    if len(published_rows) != 48 or set(published) != set(expected_cells):
        raise ValueError("Published Stage A outcomes are incomplete")
    for row in rows:
        saved = published[row["cell_id"]]
        if saved["status"] != row["status"] or saved["dataset_sha256"] != row["dataset"]["sha256"]:
            raise ValueError("Stage A outcomes differ from the published evidence")
        numeric = {"result_value": row.get("result_value"),
                   **{k: row["timings"].get(k) for k in ("execution_seconds", "total_seconds", "end_to_end_seconds")},
                   "nanny_memory_termination_count": row["diagnostics"]["nanny_memory_termination_count"],
                   **{k: row["telemetry"].get(k) for k in ("spilled_disk_peak_bytes_sum", "paused_samples", "observed_restarts_lower_bound")}}
        if any((float(saved[k]) if saved[k] else None) != value for k, value in numeric.items()):
            raise ValueError("Stage A measurements differ from the published evidence")
    sources, descriptors = {}, {}
    for instance, methods in parent["datasets"].items():
        source = within(root, methods["full"])
        manifest = load_manifest(source, verify=True)
        if pilot.canonical_hash(manifest) != parent["dataset_fingerprints"][instance]["full"]:
            raise ValueError("Stage A dataset manifest changed")
        for row in (r for r in rows if r["instance_id"] == instance):
            if row["dataset"] != manifest or row["manifest_sha256"] != pilot.canonical_hash(manifest):
                raise ValueError("Stage A outcome is not bound to the verified full dataset")
        left_rows = [f["rows"] for f in manifest["files"] if f["relation"] == "left"]
        sources[instance] = source
        descriptors[instance] = {"dataset_sha256": manifest["sha256"],
                                 "manifest_sha256": pilot.canonical_hash(manifest),
                                 "fact_rows": manifest["n_rows"], "dimension_rows": manifest["n_right_rows"],
                                 "source_partition_rows": left_rows,
                                 "largest_file_row_share": max(left_rows) / sum(left_rows)}
    diagnostics_checked = verify_diagnostics(root, rows)
    return parent, {"plan_sha256": fingerprint, "raw_records_sha256": file_hash(root / "runs.jsonl"),
                    "source_revision": parent["git_base_revision"],
                    "frozen_environment": parent["frozen_environment"],
                    "datasets": descriptors, "configs": parent["configs"], "outcomes": compact,
                    "diagnostic_files_verified_at_preparation": diagnostics_checked,
                    "scope": "historical full-input outcomes; same data and recorded environment; not fresh online executions"}, sources


def sample_seed(spec: dict, instance: str, method: str) -> int:
    return int(pilot.canonical_hash([spec["sample_seed"], instance, method])[:8], 16)


def build_cells(parent: dict, spec: dict) -> list[dict]:
    cells = []
    rng = random.Random(spec["order_seed"])
    for repeat in range(1, spec["repeats"] + 1):
        block = []
        for instance in sorted(parent["datasets"]):
            for config in parent["configs"]:
                for method in spec["methods"]:
                    effective = dict(config)
                    effective["memory_limit"] = str(round(spec["memory_floor_bytes"] + method["fraction"] *
                                                          (int(config["memory_limit"]) - spec["memory_floor_bytes"])))
                    effective.update(base_config_id=config["config_id"], config_id=config["config_id"] + "__" + method["id"])
                    cell = {"instance_id": instance, "target_config_id": config["config_id"],
                            "method": method["id"], "fraction": method["fraction"],
                            "sample_seed": sample_seed(spec, instance, method["id"]),
                            "repeat_id": repeat, "run_config": effective}
                    cell["cell_id"] = pilot.canonical_hash(cell)[:24]
                    block.append(cell)
        rng.shuffle(block)
        cells.extend(block)
    return cells


def validate_plan(plan: dict) -> None:
    spec = plan["protocol"]
    if pilot.canonical_hash(spec) != plan["protocol_sha256"]:
        raise ValueError("Stage B protocol hash mismatch")
    reference = plan["reference"]
    if pilot.canonical_hash(reference) != plan["reference_sha256"] or reference["plan_sha256"] != spec["reference_plan_sha256"]:
        raise ValueError("Stage B reference snapshot mismatch")
    if len(reference["outcomes"]) != 48 or len({r["cell_id"] for r in reference["outcomes"]}) != 48:
        raise ValueError("Stage B needs all 48 unique full-reference outcomes")
    if plan["cells"] != build_cells(plan, spec) or len(plan["cells"]) != spec["planned_cells"]:
        raise ValueError("Stage B matrix differs from its declared design/order")
    if (len(plan["datasets"]) != spec["expected_instances"] or len(plan["configs"]) != spec["expected_target_configs"]
            or plan["repeats"] != spec["repeats"] or plan["methods"] != [m["id"] for m in spec["methods"]]
            or set(plan["datasets"]) != set(reference["datasets"])):
        raise ValueError("Stage B design dimensions mismatch")
    if (plan["configs"] != reference["configs"] or plan["timeout_seconds"] != spec["timeout_seconds"]
            or plan["frozen_environment"] != reference["frozen_environment"]):
        raise ValueError("Stage B config/time limit/environment differs from its frozen contract")
    for instance, methods in plan["datasets"].items():
        if set(methods) != set(plan["methods"]):
            raise ValueError("Stage B sample methods mismatch")
        for config in plan["configs"]:
            group = [r for r in reference["outcomes"] if r["instance_id"] == instance and r["target_config_id"] == config["config_id"]]
            if len(group) != 3 or {r["repeat_id"] for r in group} != {1, 2, 3} or any(r["method"] != "full" for r in group):
                raise ValueError("Stage B reference repeats/configurations mismatch")
        for method in spec["methods"]:
            sample = plan["sample_metadata"][instance][method["id"]]
            parent = reference["datasets"][instance]
            if (sample["parent_sha256"] != parent["dataset_sha256"] or sample["fraction"] != method["fraction"]
                    or sample["sample_seed"] != sample_seed(spec, instance, method["id"])
                    or sample["fact_rows"] != round(parent["fact_rows"] * method["fraction"])
                    or sample["dimension_rows"] != parent["dimension_rows"]):
                raise ValueError("Stage B sample provenance/budget mismatch")


def validate_sample(plan: dict, instance: str, method: str, manifest: dict) -> None:
    expected = plan["sample_metadata"][instance][method]
    observed = {"dataset_sha256": manifest["sha256"], "parent_sha256": manifest.get("parent_sha256"),
                "fraction": manifest["fraction"], "sample_seed": manifest["sampling"]["seed"],
                "fact_rows": manifest["n_rows"], "dimension_rows": manifest["n_right_rows"],
                "preparation_seconds": manifest["preparation_seconds"]}
    if observed != expected or manifest["method"] != "uniform" or manifest["parent_instance_id"] != instance:
        raise ValueError("Stage B sample differs from declared source, fraction, seed or budget")


def prepare(stage_a_plan: Path, out_dir: Path) -> Path:
    pilot.require_windows(PRESET)  # No data imports, directories or sample work on Mac.
    from safe_pipe.research.probe_diagnostics import host_conditions
    from safe_pipe.research.probe_runner import _environment
    from safe_pipe.research.probe_workloads import make_probe

    spec = specification()
    frozen_source = pilot.source_fingerprints()
    out_dir, stage_a_plan = out_dir.resolve(), stage_a_plan.resolve()
    parent_root = stage_a_plan.parent
    if out_dir.is_relative_to(parent_root) or parent_root.is_relative_to(out_dir):
        raise ValueError("Stage B must use a separate sibling directory, never overwrite/nest the Stage A source")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError("Choose a new empty Stage B output directory")
    conditions = host_conditions(parent_root)
    if conditions["battery_present"] and conditions["power_plugged"] is not True:
        raise ValueError("Connect the Windows laptop to mains before Stage B preparation")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_conditions = host_conditions(out_dir)
    if min(output_conditions["free_disk_bytes"], output_conditions["temp_free_disk_bytes"]) < spec["minimum_free_disk_bytes"]:
        raise ValueError("Stage B requires 10 GiB free on experiment and temporary drives")
    started = time.monotonic()
    parent, reference, sources = reference_bundle(stage_a_plan, spec)
    reference_seconds = time.monotonic() - started
    datasets, fingerprints, metadata = {}, {}, {}
    for instance, source in sorted(sources.items()):
        datasets[instance], fingerprints[instance], metadata[instance] = {}, {}, {}
        for method in spec["methods"]:
            relative = Path("datasets") / instance / method["id"]
            seed = sample_seed(spec, instance, method["id"])
            manifest = make_probe(source, out_dir / relative, method["fraction"], "uniform", seed)
            datasets[instance][method["id"]] = relative.as_posix()
            fingerprints[instance][method["id"]] = pilot.canonical_hash(manifest)
            metadata[instance][method["id"]] = {
                "dataset_sha256": manifest["sha256"], "parent_sha256": manifest["parent_sha256"],
                "fraction": manifest["fraction"], "sample_seed": seed, "fact_rows": manifest["n_rows"],
                "dimension_rows": manifest["n_right_rows"], "preparation_seconds": manifest["preparation_seconds"]}
    cells = build_cells(parent, spec)
    plan = {"schema_version": pilot.SCHEMA, "preset": PRESET, "role": spec["role"],
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "git_base_revision": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip(),
            "source_fingerprints": frozen_source, "frozen_environment": _environment(),
            "protocol": spec, "protocol_sha256": pilot.canonical_hash(spec),
            "reference": reference, "reference_sha256": pilot.canonical_hash(reference),
            "methods": [m["id"] for m in spec["methods"]], "configs": parent["configs"], "recipes": parent["recipes"],
            "repeats": spec["repeats"], "ranking_tolerance": .05, "timeout_seconds": spec["timeout_seconds"],
            "seed": spec["order_seed"], "memory_floor_bytes": spec["memory_floor_bytes"], "memory_mapping": spec["memory_mapping"],
            "datasets": datasets, "dataset_fingerprints": fingerprints, "sample_metadata": metadata, "cells": cells,
            "reference_verification_seconds_shared": reference_seconds,
            "preparation_total_seconds": time.monotonic() - started}
    validate_plan(plan)
    if pilot.source_fingerprints() != frozen_source or plan["frozen_environment"] != parent["frozen_environment"]:
        raise ValueError("Source/environment changed during preparation; preserve partial output and prepare a new version")
    path = out_dir / "plan.json"
    path.write_text(json.dumps(plan, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"plan": str(path), "planned_cells": len(cells), "sample_directories": 16,
                      "note": "Prepared samples and provenance only; zero new jobs executed."}))
    return path


@contextmanager
def keep_awake():
    """Windows thread-scoped request; does not change the user's power scheme."""
    import ctypes
    set_state = ctypes.windll.kernel32.SetThreadExecutionState
    set_state.argtypes = [ctypes.c_uint]
    set_state.restype = ctypes.c_uint
    previous = set_state(0x80000001)
    if not previous:
        raise RuntimeError("Windows system-awake request failed; no batch started")
    try:
        yield
    finally:
        set_state(previous)


def audit(path: Path) -> None:
    pilot.require_windows(PRESET)
    from safe_pipe.research.probe_workloads import load_manifest
    from safe_pipe.research.probe_runner import _environment
    from safe_pipe.research.probe_analysis import summarize

    plan, fingerprint = pilot.load_plan(path)
    if plan["preset"] != PRESET:
        raise ValueError("Use a Stage B plan")
    root = path.resolve().parent
    if plan["source_fingerprints"] != pilot.source_fingerprints() or plan["frozen_environment"] != _environment():
        raise ValueError("Frozen Stage B source/environment mismatch")
    rows = pilot.load_records(root / "runs.jsonl", fingerprint)
    summary = summarize(plan, rows)
    if summary["missing_cells"] or summary["inconsistent_successful_results"]:
        raise ValueError("Stage B incomplete or successful results inconsistent; preserve and review")
    if (root / ".running.lock").exists() or list((root / "attempts").glob("*.json")):
        raise ValueError("Active/unresolved Stage B attempt")
    manifests = {}
    for instance, methods in plan["datasets"].items():
        for method, relative in methods.items():
            manifest = load_manifest(within(root, relative), verify=True)
            if pilot.canonical_hash(manifest) != plan["dataset_fingerprints"][instance][method]:
                raise ValueError("Stage B sample changed")
            validate_sample(plan, instance, method, manifest)
            manifests[(instance, method)] = manifest
    for row in rows:
        if row["dataset"] != manifests[(row["instance_id"], row["method"])] or row["environment"] != plan["frozen_environment"]:
            raise ValueError("Stage B record differs from frozen dataset/environment")
        if row.get("owned_descendants_alive_after_cleanup") != 0:
            raise ValueError("Cleanup issue; inspect before declaring completion")
    checked = verify_diagnostics(root, rows)
    quality = [r["cell_id"] for r in summary["probe_outcomes"] if r["quality_issues"]]
    result = {"planned": len(plan["cells"]), "recorded": len(rows), "statuses": summary["statuses"],
              "runs_sha256": file_hash(root / "runs.jsonl"),
              "plan_sha256": fingerprint, "reference_sha256": plan["reference_sha256"],
              "sample_directories_verified": len(manifests), "diagnostic_files_hash_verified": checked,
              "raw_nanny_messages_verified": sum(r["diagnostics"].get("nanny_memory_termination_count", 0) for r in rows),
              "quality_flagged_cells": quality, "quality_pass": not quality,
              "interpretation": "Integrity audit retains failed/unknown/confounded attempts; no automatic next stage"}
    (root / "completion_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--stage-a-plan", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    for name in ("run", "analyze", "audit"):
        p = sub.add_parser(name)
        p.add_argument("--plan", type=Path, required=True)
        if name == "run":
            p.add_argument("--max-runs", type=int, default=4)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            pilot.require_windows(PRESET)
            with keep_awake():
                prepare(args.stage_a_plan, args.out_dir)
        else:
            plan, _ = pilot.load_plan(args.plan)
            if plan["preset"] != PRESET:
                raise ValueError("Use a Stage B plan with this command")
            if args.command == "run":
                pilot.require_windows(PRESET)
                with keep_awake():
                    pilot.run(args.plan, args.max_runs)
            elif args.command == "audit":
                audit(args.plan)
            else:
                pilot.analyze(args.plan)
    except (ValueError, FileExistsError, FileNotFoundError, RuntimeError) as exc:
        parser.exit(2, f"Stage B: {exc}\n")


if __name__ == "__main__":
    main()
