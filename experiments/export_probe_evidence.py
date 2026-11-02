"""Export compact, reviewable evidence without generated data or private process addresses."""
from __future__ import annotations

import argparse
import csv
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
    rows = []
    for r in records:
        t = r.get("telemetry") or {}
        d = r["dataset"]
        rows.append({
            "cell_id": r["cell_id"], "run_id": r["run_id"], "instance_id": r["instance_id"],
            "method": r["method"], "target_config_id": r["target_config_id"], "repeat_id": r["repeat_id"],
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
            "optimized_task_count": (r.get("graph") or {}).get("task_count"),
            "optimized_task_prefixes": json.dumps((r.get("graph") or {}).get("task_prefix_counts", {}), sort_keys=True),
            "error": r.get("error"),
        })
    if rows:
        with (out / "measurements.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    summary.pop("telemetry_by_cell")
    summary["plan_sha256"] = fingerprint
    summary["environment"] = records[0]["environment"] if records else None
    summary["host_physical_bytes"] = records[0]["host_budget"]["physical_bytes"] if records else None
    summary["raw_evidence"] = "Complete raw records and Parquet are local under the experiment directory; this is a compact export."
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
