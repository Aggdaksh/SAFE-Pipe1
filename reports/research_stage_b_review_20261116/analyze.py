"""Read existing compact evidence only; no project imports, tests or experiments.

Recompute Stage B choices/costs from CSV, not from the published summary.
Raw Windows datasets, worker records and logs are outside this review's scope.
"""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "reports/research_stage_a_windows_v1"
B = ROOT / "reports/research_stage_b_windows_v1"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def close(left, right):
    assert math.isclose(float(left), float(right), rel_tol=1e-10, abs_tol=1e-9), (left, right)


def main():
    plan, summary = read_json(B / "plan.json"), read_json(B / "summary.json")
    audit, findings = read_json(B / "completion_audit.json"), read_json(B / "findings.json")
    spec, ref = plan["protocol"], plan["reference"]
    rows, full = read_csv(B / "measurements.csv"), read_csv(A / "measurements.csv")
    assert len(rows) == len({r["cell_id"] for r in rows}) == 96
    assert len(full) == len({r["cell_id"] for r in full}) == 48
    assert canonical(plan) == audit["plan_sha256"] == summary["plan_sha256"]
    assert canonical(spec) == plan["protocol_sha256"]
    assert spec == read_json(ROOT / "configs/research_stage_b_v1.json")
    assert canonical(ref) == plan["reference_sha256"] == audit["reference_sha256"]
    assert canonical(read_json(A / "plan.json")) == ref["plan_sha256"] == spec["reference_plan_sha256"]
    source_matches = {}
    for name, expected in plan["source_fingerprints"].items():
        raw = (ROOT / name).read_bytes()
        forms = {"exact": raw, "Windows_CRLF": raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")}
        matches = [label for label, data in forms.items() if hashlib.sha256(data).hexdigest() == expected]
        assert matches, name
        source_matches[name] = matches[0]

    cells = {c["cell_id"]: c for c in plan["cells"]}
    exported = {r["cell_id"]: r for r in summary["probe_outcomes"]}
    assert set(cells) == set(exported) == {r["cell_id"] for r in rows}
    signal_columns = {"nanny_termination": "nanny_memory_termination_count",
                      "spill_bytes": "spilled_disk_peak_bytes_sum",
                      "paused_samples": "paused_samples", "restarts": "observed_restarts_lower_bound"}
    zero_columns = list(signal_columns.values()) + ["missing_initial_worker_records",
        "owned_descendants_alive_after_cleanup", "diagnostic_malformed_lines", "diagnostic_write_errors"]
    for row in rows:
        cell, outcome = cells[row["cell_id"]], exported[row["cell_id"]]
        for key in ("instance_id", "method", "target_config_id"):
            assert row[key] == cell[key] == outcome[key]
        for key in ("repeat_id", "sample_seed"):
            assert int(row[key]) == cell[key]
        assert float(row["fraction"]) == cell["fraction"]
        config = cell["run_config"]
        assert int(row["effective_memory_bytes"]) == int(config["memory_limit"])
        assert all(int(row[k]) == config[k] for k in ("n_workers", "threads_per_worker"))
        sample = plan["sample_metadata"][row["instance_id"]][row["method"]]
        for column, key in (("dataset_sha256", "dataset_sha256"), ("parent_dataset_sha256", "parent_sha256")):
            assert row[column] == sample[key]
        assert sample["parent_sha256"] == ref["datasets"][row["instance_id"]]["dataset_sha256"]
        for key in ("fact_rows", "dimension_rows", "sample_seed"):
            assert int(row[key]) == sample[key]
        close(row["preparation_seconds_shared_per_dataset"], sample["preparation_seconds"])
        assert all(float(row[k]) == 0 for k in zero_columns)
        assert row["status"] == outcome["status"] == "success"
        assert row["fidelity_signal"] == outcome["signal"] == "quiet"
        assert json.loads(row["fidelity_quality_issues"]) == outcome["quality_issues"] == []
        assert json.loads(row["condition_flags"]) == [] and int(row["condition_samples"]) > 0
        assert row["diagnostics_retained"] == "True" and row["diagnostic_log_truncated"] == "False"
        assert int(row["samples_total"]) > 0 and int(row["worker_count_observed"]) == 2
        assert math.isfinite(float(row["result_value"]))
        for key in ("execution_seconds", "total_seconds", "end_to_end_seconds", "result_value"):
            close(row[key], outcome[key])
        for signal, column in signal_columns.items():
            close(row[column], outcome["signals"][signal])

    full_by_id = {r["cell_id"]: r for r in full}
    assert set(full_by_id) == {r["cell_id"] for r in ref["outcomes"]}
    for outcome in ref["outcomes"]:
        row = full_by_id[outcome["cell_id"]]
        for key in ("instance_id", "method", "target_config_id", "status", "failure_category"):
            assert row[key] == outcome[key]
        assert int(row["repeat_id"]) == outcome["repeat_id"]
        assert row["dataset_sha256"] == ref["datasets"][row["instance_id"]]["dataset_sha256"]
        for key in ("execution_seconds", "total_seconds", "end_to_end_seconds"):
            close(row[key], outcome[key])
        warnings = [signal for signal, column in signal_columns.items() if float(row[column]) > 0]
        if row["status"] != "success":
            warnings.append(row["status"])
        assert warnings == outcome["warnings"] and outcome["quality_issues"] == []
        assert outcome["signal"] == ("warning" if warnings else "quiet")
        for signal, column in signal_columns.items():
            close(row[column], outcome["signals"][signal])

    groups = []
    for reported in summary["fidelity_groups"]:
        matches = lambda r: r["instance_id"] == reported["instance_id"] and r["target_config_id"] == reported["target_config_id"]
        probes = [r for r in rows if matches(r) and r["method"] == reported["method"]]
        historical = [r for r in ref["outcomes"] if matches(r)]
        assert len(probes) == len(historical) == 3
        assert {int(r["repeat_id"]) for r in probes} == {1, 2, 3}
        discrepancy = any(r["signal"] == "warning" for r in historical)
        assert reported["false_reassurance_candidate"] == discrepancy
        assert reported["comparison_available"] and not reported["unnecessary_warning_candidate"]
        if discrepancy:
            groups.append({k: reported[k] for k in ("instance_id", "target_config_id", "method")})
    assert len(summary["fidelity_groups"]) == 32 and len(groups) == 8

    configs = {c["config_id"]: c for c in plan["configs"]}
    weights = {name: spec["balanced_weights"]["time"]
        + spec["balanced_weights"]["threads"] * c["n_workers"] * c["threads_per_worker"] / spec["normalization_threads"]
        + spec["balanced_weights"]["memory"] * c["n_workers"] * int(c["memory_limit"]) / spec["normalization_memory_bytes"]
        for name, c in configs.items()}
    replays, ratios = [], []
    for instance, descriptor in sorted(ref["datasets"].items()):
        choices = {"fixed_1gb": (spec["low_memory_config"], None), "fixed_2gb": (spec["high_memory_config"], None),
            "file_metadata": (spec["high_memory_config"] if descriptor["largest_file_row_share"] > spec["metadata_baseline_max_file_share_threshold"] else spec["low_memory_config"], None)}
        for method in plan["methods"]:
            sample_rows = [r for r in rows if r["instance_id"] == instance and r["method"] == method]
            assert len(sample_rows) == 6
            assert all(math.isclose(float(r["result_value"]), float(sample_rows[0]["result_value"]), rel_tol=1e-9, abs_tol=1e-9) for r in sample_rows)
            times = {c: median(float(r["total_seconds"]) for r in sample_rows if r["target_config_id"] == c) for c in configs}
            chosen = min((times[c] * weights[c], c) for c in configs)[1]
            cost = sum(float(r["end_to_end_seconds"]) for r in sample_rows) + plan["sample_metadata"][instance][method]["preparation_seconds"]
            choices[method] = chosen, cost
            ratios.append(times[spec["low_memory_config"]] / times[spec["high_memory_config"]])
        for policy, (chosen, cost) in choices.items():
            historical = [r for r in full if r["instance_id"] == instance and r["target_config_id"] == chosen]
            times = [float(r["end_to_end_seconds"]) for r in historical if r["status"] == "success"]
            replay = dict(instance_id=instance, policy=policy, selected_config=chosen,
                statuses=dict(Counter(r["status"] for r in historical)), profiling_seconds=cost,
                successful_full_median_seconds=median(times) if times else None)
            saved = next(r for r in summary["baseline_replays"] if r["instance_id"] == instance and r["policy"] == policy)
            assert chosen == saved["selected_config"] and replay["statuses"] == saved["selected_full_outcomes"]["statuses"]
            assert saved["evaluable"] and not saved["fallback_used"]
            for value, key in ((cost, "profiling_seconds"), (replay["successful_full_median_seconds"], "median_successful_full_end_to_end_seconds")):
                if value is None:
                    assert saved[key] is None
                else:
                    close(value, saved[key])
            replays.append(replay)
    policies = {}
    for policy in choices:
        selected = [r for r in replays if r["policy"] == policy]
        costs = [r["profiling_seconds"] for r in selected if r["profiling_seconds"] is not None]
        full_times = [r["successful_full_median_seconds"] for r in selected if r["successful_full_median_seconds"] is not None]
        policies[policy] = dict(selected_config_counts=dict(Counter(r["selected_config"] for r in selected)),
            historical_full_statuses=dict(sum((Counter(r["statuses"]) for r in selected), Counter())),
            median_six_probe_and_preparation_seconds=median(costs) if costs else None,
            median_per_instance_successful_historical_full_seconds=median(full_times),
            instances_with_no_successful_historical_full_time=8-len(full_times))
        for key, value in policies[policy].items():
            saved = findings["policies"][policy][key]
            if isinstance(value, float):
                close(value, saved)
            else:
                assert value == saved
    result = dict(scope="Compact CSV/plan/summary cross-check only; raw Windows evidence not independently re-audited.",
        planned_and_unique_probe_rows=96, statuses=dict(Counter(r["status"] for r in rows)),
        signals=dict(Counter(r["fidelity_signal"] for r in rows)),
        canonical_plan_sha256=canonical(plan), source_hash_match_modes=source_matches,
        comparison_groups=32, false_reassurance_candidate_groups=groups,
        balanced_target_weights=weights,
        low_high_median_probe_lifecycle_ratio_range=[min(ratios), max(ratios)],
        policies=policies, replays=replays)
    destination = Path(__file__).with_name("analysis.json")
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"source_hash_match_modes", "replays", "false_reassurance_candidate_groups"}}, indent=2))


if __name__ == "__main__":
    main()
