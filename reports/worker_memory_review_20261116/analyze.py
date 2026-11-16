"""Review committed worker summaries only; no project imports or workload runs."""
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "reports/worker_memory_stage_a_b_v1"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def csv_value(value):
    return "" if value is None else canonical(value) if isinstance(value, (list, dict)) else str(value)


def describe(values):
    return {"count": len(values), "minimum": min(values), "median": median(values), "maximum": max(values)}


def main():
    workers, runs = read_json(SOURCE / "workers.json"), read_json(SOURCE / "runs.json")
    verification = read_json(SOURCE / "verification.json")
    csv_rows = read_csv(SOURCE / "workers.csv")
    assert verification["integrity_pass"] and len(workers) == len(csv_rows) == 321
    assert all({k: csv_value(v) for k, v in row.items()} == csv_row for row, csv_row in zip(workers, csv_rows))
    assert len(runs) == len({r["cell_id"] for r in runs}) == 144
    assert len({w["worker_lifetime_id"] for w in workers}) == 321
    reference_plan = read_json(ROOT / "reports/research_stage_b_windows_v1/plan.json")
    original, cells = {}, {}
    for stage in ("A", "B"):
        source = ROOT / f"reports/research_stage_{stage.lower()}_windows_v1"
        plan, audit = read_json(source / "plan.json"), read_json(source / "completion_audit.json")
        report = next(s for s in verification["stages"] if s["stage"] == stage)
        assert report["integrity_pass"] and not report["issues"] and not report["missing_worker_fields"]
        assert report["plan_canonical_sha256"] == hashlib.sha256(canonical(plan).encode()).hexdigest()
        raw_hash = reference_plan["reference"]["raw_records_sha256"] if stage == "A" else audit["runs_sha256"]
        assert report["runs_sha256"] == report["expected_runs_sha256"] == raw_hash
        assert report["diagnostic_files_hash_verified"] == audit["diagnostic_files_hash_verified"]
        original.update({r["cell_id"]: r for r in read_csv(source / "measurements.csv")})
        cells.update({c["cell_id"]: (stage, c) for c in plan["cells"]})
    assert set(original) == {r["cell_id"] for r in runs}
    by_cell = defaultdict(list)
    for worker in workers:
        by_cell[worker["cell_id"]].append(worker)
    aggregates = {"peak_rss_bytes": "rss_peak_bytes_sum", "peak_managed_in_memory_bytes": "managed_peak_bytes_sum",
        "peak_spilled_disk_bytes": "spilled_disk_peak_bytes_sum", "paused_samples": "paused_samples",
        "samples": "samples_total", "cumulative_spill_write_bytes": "cumulative_spill_write_bytes_observed"}
    for run in runs:
        group, old = by_cell[run["cell_id"]], original[run["cell_id"]]
        stage, cell = cells[run["cell_id"]]
        assert run["stage"] == stage
        assert all(run[k] == cell[k] for k in ("instance_id", "method", "repeat_id", "target_config_id"))
        if stage == "B":
            assert run["sample_fraction"] == cell["fraction"] and run["sample_seed"] == cell["sample_seed"]
            sample = reference_plan["sample_metadata"][run["instance_id"]][run["method"]]
            assert run["dataset_sha256"] == sample["dataset_sha256"]
            assert run["parent_dataset_sha256"] == sample["parent_sha256"]
        else:
            assert run["sample_fraction"] == 1 and run["parent_dataset_sha256"] is None
        for name, column in (("run_id", "run_id"), ("instance_id", "instance_id"), ("method", "method"),
                             ("target_config_id", "target_config_id"), ("dataset_sha256", "dataset_sha256"),
                             ("run_status", "status")):
            assert run[name] == old[column]
        for name in ("n_workers", "threads_per_worker", "repeat_id"):
            assert run[name] == int(old[name])
        assert run["configured_effective_memory_limit_bytes"] == int(old["effective_memory_bytes"])
        assert len(group) == run["exported_worker_lifetimes"] == run["run_worker_count_observed"] == int(old["worker_count_observed"])
        assert not run["unmatched_worker_evidence"]
        assert sum(w["worker_origin"] == "initial" for w in group) == 2
        for worker in group:
            assert all(worker[k] == v for k, v in run.items() if k in worker)
            assert not worker["missing_worker_fields"] and worker["sampling_errors"] == 0
            assert worker["effective_memory_limit_bytes"] == run["configured_effective_memory_limit_bytes"]
            assert 0 < worker["baseline_rss_bytes"] <= worker["peak_rss_bytes"] and worker["samples"] > 0
        for field, column in aggregates.items():
            assert math.isclose(sum(w[field] for w in group), float(old[column]), rel_tol=1e-12, abs_tol=1e-8)
        assert sum(w["worker_nanny_memory_termination_count"] for w in group) == run["run_nanny_memory_termination_count"] == int(old["nanny_memory_termination_count"])

    # Exploratory continuous feature: maximum individual lifetime peak/cap per
    # probe run, then median over repeats. No summing concurrent/lifetime peaks.
    groups = defaultdict(list)
    for run in runs:
        if run["stage"] == "B":
            assert run["exported_worker_lifetimes"] == 2
            groups[(run["instance_id"], run["target_config_id"], run["sample_fraction"])].append(
                max(w["peak_rss_bytes"] / w["effective_memory_limit_bytes"] for w in by_cell[run["cell_id"]]))
    pressure = {(r["instance_id"], r["target_config_id"]) for r in reference_plan["reference"]["outcomes"] if r["signal"] == "warning"}
    records = []
    for (instance, config, fraction), ratios in sorted(groups.items()):
        assert len(ratios) == 3
        descriptor = reference_plan["reference"]["datasets"][instance]
        records.append({"instance_id": instance, "target_config_id": config, "fraction": fraction,
            "historical_full_warning_observed": (instance, config) in pressure,
            "metadata_escalates": descriptor["largest_file_row_share"] > reference_plan["protocol"]["metadata_baseline_max_file_share_threshold"],
            "probe_run_max_peak_over_cap": ratios, "median_over_three_repeats": median(ratios)})
    low = [r for r in records if r["target_config_id"] == "w2_t1_1g"]
    assert len(low) == 16 and all(r["historical_full_warning_observed"] == r["metadata_escalates"] for r in low)
    cohorts = []
    for fraction in (.125, .25):
        for warning in (False, True):
            selected = [r for r in low if r["fraction"] == fraction and r["historical_full_warning_observed"] == warning]
            assert len(selected) == 4
            cohorts.append({"fraction": fraction, "historical_full_warning_observed": warning,
                "group_medians": describe([r["median_over_three_repeats"] for r in selected]),
                "individual_probe_runs": describe([v for r in selected for v in r["probe_run_max_peak_over_cap"]])})

    # Independent nanny event readings can exceed the last retained worker peak.
    terminated = [w for w in workers if w["worker_nanny_memory_termination_count"]]
    event_ratios, saved_ratios, lags, differences, below, above = [], [], [], [], 0, 0
    for worker in terminated:
        assert worker["stage"] == "A" and worker["worker_nanny_memory_termination_count"] == 1
        events = [e for e in worker["worker_evidence"] if e["kind"] == "nanny_memory_restart"]
        assert len(events) == 1 and isinstance(events[0]["rss_bytes"], int)
        event, cap = events[0], worker["effective_memory_limit_bytes"]
        event_ratio, saved_ratio = event["rss_bytes"] / cap, worker["peak_rss_bytes"] / cap
        event_ratios.append(event_ratio)
        saved_ratios.append(saved_ratio)
        below += saved_ratio < worker["memory_settings"]["terminate"]
        above += event_ratio > worker["memory_settings"]["terminate"]
        lags.append((datetime.fromisoformat(event["utc"]) - datetime.fromisoformat(worker["last_sample_utc"])).total_seconds())
        differences.append(event["rss_bytes"] - worker["peak_rss_bytes"])
    assert len(terminated) == 37
    result = {"scope": "Exploratory review of committed worker export; no workloads, project tests or training.",
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.iterdir()) if p.suffix in {".json", ".csv"}},
        "compact_checks_pass": True, "runs": len(runs), "worker_lifetimes": len(workers),
        "worker_origins": {stage: dict(Counter(w["worker_origin"] for w in workers if w["stage"] == stage)) for stage in ("A", "B")},
        "low_cap_cohorts": cohorts, "probe_groups": records,
        "low_cap_full_warning_groups_equal_metadata_escalation_groups": True,
        "terminated_worker_snapshot_comparison": {"lifetimes": len(terminated), "saved_peaks_below_termination_threshold": below,
            "nanny_event_rss_above_termination_threshold": above, "saved_peak_over_cap": describe(saved_ratios),
            "nanny_event_rss_over_cap": describe(event_ratios), "event_minus_last_retained_sample_seconds": describe(lags),
            "event_rss_exceeds_saved_peak_count": sum(d > 0 for d in differences), "maximum_excess_bytes": max(differences)},
        "probe_first_sample_rss_bytes": describe([w["baseline_rss_bytes"] for w in workers if w["stage"] == "B"]),
        "limitations": ["Full raw Windows files were not rehashed by this Mac review; Windows verification is separately reported.",
            "One seed, eight instances, shared samples and runtime repeats; no independent classifier evaluation.",
            "The continuous ratio is an exploratory feature, not a frozen threshold or a validated failure predictor.",
            "Warning includes successful jobs with pressure; do not replace it with a deterministic failure label.",
            "Missing brief peaks and abrupt-death persistence limit memory extrapolation; first sampled RSS is not fixed overhead.",
            "Probe overhead and lack of improvement over metadata remain unresolved; no new runs or training scheduled."]}
    Path(__file__).with_name("analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"input_sha256", "probe_groups", "limitations"}}, indent=2))


if __name__ == "__main__":
    main()
