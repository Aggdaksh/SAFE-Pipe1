"""Export compact, reviewable evidence without generated data or private process addresses."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from experiments.probe_pilot import load_plan, load_records
from safe_pipe.research.probe_analysis import markdown_report, summarize


def export(plan_path: Path, out: Path) -> None:
    plan, fingerprint = load_plan(plan_path)
    records = load_records(plan_path.parent / "runs.jsonl", fingerprint)
    summary = summarize(plan, records)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Evidence destination must be empty")
    out.mkdir(parents=True, exist_ok=True)
    fidelity_by_cell = {r["cell_id"]: r for r in summary.get("probe_outcomes", [])}
    rows = []
    for r in records:
        t = r.get("telemetry") or {}
        diagnostic = r.get("diagnostics") or {}
        d = r["dataset"]
        rows.append({
            "cell_id": r["cell_id"], "run_id": r["run_id"], "instance_id": r["instance_id"],
            "method": r["method"], "target_config_id": r["target_config_id"], "repeat_id": r["repeat_id"],
            "fraction": r.get("fraction", d.get("fraction")),
            "sample_seed": r.get("sample_seed", (d.get("sampling") or {}).get("seed")),
            "parent_dataset_sha256": d.get("parent_sha256"),
            "fidelity_signal": fidelity_by_cell.get(r["cell_id"], {}).get("signal"),
            "fidelity_quality_issues": json.dumps(fidelity_by_cell.get(r["cell_id"], {}).get("quality_issues", [])),
            "status": r["status"], "result_value": r.get("result_value"),
            "started_utc": r.get("started_utc"), "finished_utc": r.get("finished_utc"),
            "effective_memory_bytes": r["config"]["memory_limit"],
            "n_workers": r["config"]["n_workers"], "threads_per_worker": r["config"]["threads_per_worker"],
            "dataset_sha256": d["sha256"], "fact_rows": d["n_rows"], "dimension_rows": d["n_right_rows"],
            "input_file_bytes": d["compressed_bytes"], "parquet_encoded_bytes": d["logical_bytes"],
            "preparation_seconds_shared_per_dataset": d["preparation_seconds"],
            **r["timings"],
            **{k: t.get(k) for k in ("rss_peak_bytes_sum", "managed_peak_bytes_sum", "spilled_disk_peak_bytes_sum",
                                   "cumulative_spill_write_bytes_observed", "paused_samples", "samples_total",
                                   "worker_count_observed", "observed_restarts_lower_bound", "missing_initial_worker_records")},
            "owned_descendants_alive_after_cleanup": r.get("owned_descendants_alive_after_cleanup"),
            "failure_category": diagnostic.get("failure_category"),
            "nanny_memory_termination_count": diagnostic.get("nanny_memory_termination_count"),
            "worker_exit_statuses": json.dumps([{k: e.get(k) for k in ("exit_status", "signal", "phase")}
                                               for e in diagnostic.get("worker_exit_events", [])]),
            "worker_removals_before_cleanup": diagnostic.get("worker_removals_before_cleanup"),
            "diagnostics_retained": diagnostic.get("retained"),
            "diagnostic_file_count": len(diagnostic["files"]) if "files" in diagnostic else None,
            "diagnostic_log_truncated": diagnostic.get("log_truncated"),
            "diagnostic_malformed_lines": diagnostic.get("malformed_log_lines"),
            "diagnostic_write_errors": diagnostic.get("log_write_errors"),
            "memory_settings": json.dumps(r.get("memory_settings"), sort_keys=True),
            "condition_flags": json.dumps((r.get("conditions") or {}).get("flags", [])),
            "condition_samples": (r.get("conditions") or {}).get("samples"),
            "optimized_task_count": (r.get("graph") or {}).get("task_count"),
            "optimized_task_prefixes": json.dumps((r.get("graph") or {}).get("task_prefix_counts", {}), sort_keys=True),
            "error": r.get("error"),
        })
    if rows:
        with (out / "measurements.csv").open("w", newline="") as f:
            # A timeout before setup has fewer timing fields than a completed job.
            writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for row in rows for k in row)), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    summary.pop("telemetry_by_cell")
    summary["plan_sha256"] = fingerprint
    summary["environment"] = records[0]["environment"] if records else None
    summary["host_physical_bytes"] = records[0]["host_budget"]["physical_bytes"] if records else None
    summary["raw_evidence"] = "Complete raw records and Parquet are local under the experiment directory; this is a compact export."
    if plan.get("preset") == "windows-stage-b":
        summary["reference_sha256"] = plan["reference_sha256"]
        summary["reference_plan_sha256"] = plan["reference"]["plan_sha256"]
        audit_path = plan_path.parent / "completion_audit.json"
        if audit_path.exists():
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            if (audit.get("plan_sha256") != fingerprint or audit.get("recorded") != len(records)
                    or audit.get("runs_sha256") != hashlib.sha256((plan_path.parent / "runs.jsonl").read_bytes()).hexdigest()):
                raise ValueError("Completion audit is stale or belongs to another experiment")
            (out / "completion_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    batches = plan_path.parent / "batches.jsonl"
    if batches.exists():
        batch_rows = [json.loads(line) for line in batches.read_text().splitlines() if line.strip()]
        summary["batch_accounting"] = {
            "verification_seconds_shared_total": sum(r.get("verification_seconds_shared", 0) for r in batch_rows),
            "row_persistence_seconds_total": sum(r.get("row_persistence_seconds", 0) for r in batch_rows),
            "scope": "Shared collection audit and persistence, not per-request online policy costs"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    (out / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    (out / "REPORT.md").write_text(markdown_report(summary))
    print(json.dumps({"export": str(out.resolve()), "measurements": len(rows)}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    export(args.plan, args.out)


if __name__ == "__main__":
    main()
