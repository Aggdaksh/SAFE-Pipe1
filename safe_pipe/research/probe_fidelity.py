"""Predeclared Stage B descriptive comparisons; no model or online-policy claims."""
from __future__ import annotations

from collections import Counter
import math
from statistics import median


def compact_outcome(row: dict) -> dict:
    """Exclude process addresses while retaining failure, censoring and quality."""
    telemetry = row.get("telemetry") or {}
    diagnostic = row.get("diagnostics") or {}
    conditions = row.get("conditions") or {}
    issues = []
    if row.get("status") not in {"success", "execution_error", "timeout"}:
        issues.append("infrastructure_or_interrupted_outcome")
    if conditions.get("flags") != [] or not conditions.get("samples", 0):
        issues.append("conditions_missing_or_flagged")
    if row.get("owned_descendants_alive_after_cleanup") != 0:
        issues.append("cleanup_missing_or_incomplete")
    if (diagnostic.get("retained") is not True or diagnostic.get("summary_error")
            or diagnostic.get("log_truncated") is not False
            or any(diagnostic.get(k) != 0 for k in ("log_write_errors", "malformed_log_lines"))):
        issues.append("diagnostics_incomplete")
    signals = {
        "nanny_termination": diagnostic.get("nanny_memory_termination_count"),
        "spill_bytes": telemetry.get("spilled_disk_peak_bytes_sum"),
        "paused_samples": telemetry.get("paused_samples"),
        "restarts": telemetry.get("observed_restarts_lower_bound"),
    }
    if (not telemetry.get("samples_total", 0) or telemetry.get("missing_initial_worker_records") != 0
            or not telemetry.get("workers")
            or any(w.get("sampling_errors") != 0 for w in telemetry.get("workers", []))
            or any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in signals.values())):
        issues.append("telemetry_incomplete")
    warnings = [name for name, value in signals.items() if isinstance(value, (int, float)) and value > 0]
    if row.get("status") in {"execution_error", "timeout"}:
        warnings.append(row["status"])
    timing = row.get("timings") or {}
    if row.get("status") == "success":
        value = row.get("result_value")
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            issues.append("successful_result_invalid")
    for key in ("total_seconds", "end_to_end_seconds"):
        value = timing.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            issues.append("timing_missing_or_invalid")
            break
    return {"cell_id": row["cell_id"], "instance_id": row["instance_id"],
            "target_config_id": row["target_config_id"], "method": row["method"],
            "repeat_id": row["repeat_id"], "status": row["status"],
            "result_value": row.get("result_value"),
            "signal": "unknown" if issues else ("warning" if warnings else "quiet"),
            "warnings": warnings, "quality_issues": issues, "signals": signals,
            "failure_category": diagnostic.get("failure_category"),
            "execution_seconds": timing.get("execution_seconds"),
            "total_seconds": timing.get("total_seconds"),
            "end_to_end_seconds": timing.get("end_to_end_seconds")}


def describe(rows: list[dict], expected: int) -> dict:
    statuses = Counter(r["status"] for r in rows)
    signals = Counter(r["signal"] for r in rows)
    complete = len(rows) == expected
    completion = ("incomplete" if not complete else "all_completed" if statuses["success"] == expected
                  else "none_completed" if not statuses["success"] else "mixed_completion")
    good_times = [r["execution_seconds"] for r in rows if r["status"] == "success"
                  and isinstance(r.get("execution_seconds"), (float, int))]
    return {"observed": len(rows), "expected": expected, "statuses": dict(statuses),
            "signals": dict(signals), "completion": completion,
            "complete_known": complete and not signals["unknown"],
            "successful_engine_seconds": good_times,
            "median_successful_engine_seconds": median(good_times) if good_times else None,
            "attempt_lifecycle_seconds": [r.get("total_seconds") for r in rows]}


def balanced_weight(config: dict, spec: dict) -> float:
    weights = spec["balanced_weights"]
    return (weights["time"] + weights["threads"] * config["n_workers"] * config["threads_per_worker"] / spec["normalization_threads"]
            + weights["memory"] * config["n_workers"] * int(config["memory_limit"]) / spec["normalization_memory_bytes"])


def summarize_stage_b(plan: dict, records: list[dict]) -> dict:
    spec, reference = plan["protocol"], plan["reference"]
    expected = {cell["cell_id"]: cell for cell in plan["cells"]}
    seen = set()
    for row in records:
        cell = expected.get(row["cell_id"])
        if cell is None or row["cell_id"] in seen:
            raise ValueError("Unknown or duplicated Stage B cell")
        for key in ("instance_id", "method", "fraction", "sample_seed", "target_config_id", "repeat_id", "run_config"):
            if row.get(key) != cell[key]:
                raise ValueError(f"Stage B cell identity mismatch: {key}")
        if row.get("config") != cell["run_config"]:
            raise ValueError("Stage B measured configuration differs from frozen configuration")
        seen.add(row["cell_id"])
    probes = [compact_outcome(row) for row in records]
    full = reference["outcomes"]
    inconsistent = []
    for instance in plan["datasets"]:
        for method in plan["methods"]:
            sample_rows = [r for r in probes if r["instance_id"] == instance and r["method"] == method]
            values = [r.get("result_value") for r in sample_rows if r["status"] == "success"]
            if values and (any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in values)
                           or any(not math.isclose(v, values[0], rel_tol=1e-9, abs_tol=1e-9) for v in values)):
                inconsistent.append({"instance_id": instance, "method": method})
                for row in sample_rows:
                    row["signal"] = "unknown"
                    row["quality_issues"].append("sample_scalar_inconsistent")
    groups = []
    for instance in sorted(plan["datasets"]):
        for config in plan["configs"]:
            full_rows = [r for r in full if r["instance_id"] == instance and r["target_config_id"] == config["config_id"]]
            full_summary = describe(full_rows, 3)
            for method in spec["methods"]:
                probe_rows = [r for r in probes if r["instance_id"] == instance and r["target_config_id"] == config["config_id"]
                              and r["method"] == method["id"]]
                probe_summary = describe(probe_rows, plan["repeats"])
                known = full_summary["complete_known"] and probe_summary["complete_known"]
                groups.append({"instance_id": instance, "target_config_id": config["config_id"],
                               "method": method["id"], "fraction": method["fraction"],
                               "full": full_summary, "probe": probe_summary, "comparison_available": known,
                               "false_reassurance_candidate": (bool(probe_summary["signals"].get("quiet", 0) and full_summary["signals"].get("warning", 0)) if known else None),
                               "unnecessary_warning_candidate": (bool(probe_summary["signals"].get("warning", 0) and full_summary["signals"].get("quiet", 0) == 3) if known else None)})
    # Repeats share one sample; these are 32 group comparisons, not independent
    # classifier examples or synchronous pairs of a probe with a full execution.
    replays = baseline_replays(plan, probes)
    return {"schema_version": "stage-b-fidelity-report-v1", "role": plan["role"],
            "planned_cells": len(expected), "recorded_cells": len(records),
            "missing_cells": sorted(set(expected) - seen), "statuses": dict(Counter(r["status"] for r in records)),
            "telemetry_by_cell": [], "fidelity_groups": groups, "baseline_replays": replays,
            "probe_outcomes": probes, "inconsistent_successful_results": inconsistent,
            "comparison_counts": {"eligible_groups": sum(g["comparison_available"] for g in groups),
                                  "false_reassurance_candidate_groups": sum(g["false_reassurance_candidate"] is True for g in groups),
                                  "unnecessary_warning_candidate_groups": sum(g["unnecessary_warning_candidate"] is True for g in groups)},
            "method_notes": [
                "One generated seed, one non-nested sample per fraction, three runtime repeats; eight workload instances.",
                "Full references are historical Stage A executions; no synchronous repeat pairing or independent policy evaluation.",
                "Warning includes failure, nanny termination, spill, pauses or restarts; quality gaps are unknown, never quiet.",
                "Mixed full outcomes remain mixed; group discrepancy counts are not calibrated false-positive/negative rates.",
                "Join samples retain the entire dimension; scaled memory may create proxy-only pressure.",
                "Probe preparation is charged once per instance/fraction; three repeats per candidate are all charged in diagnostic replay.",
                "Configured GB-seconds/thread-seconds are lifecycle allocation proxies, not measured utilization; preparation resource use is unmeasured.",
                "Replays use historical full outcomes, exclude unmeasured controller/metadata overhead, and do not establish online savings.",
                "Stop after Stage B for review; no automatic training, Stage C or main merge.",
            ]}


def baseline_replays(plan: dict, probes: list[dict]) -> list[dict]:
    spec, reference = plan["protocol"], plan["reference"]
    configs = {c["config_id"]: c for c in plan["configs"]}
    result = []
    measured_configs = {cell["cell_id"]: cell["run_config"] for cell in plan["cells"]}
    for instance, descriptor in sorted(reference["datasets"].items()):
        fixed = {"fixed_1gb": spec["low_memory_config"], "fixed_2gb": spec["high_memory_config"],
                 "file_metadata": spec["high_memory_config"] if descriptor["largest_file_row_share"] > spec["metadata_baseline_max_file_share_threshold"] else spec["low_memory_config"]}
        choices = [(name, config, None, None, None, None, None) for name, config in fixed.items()]
        for method in spec["methods"]:
            rows = [r for r in probes if r["instance_id"] == instance and r["method"] == method["id"]]
            preparation = plan["sample_metadata"][instance][method["id"]]["preparation_seconds"]
            if len(rows) != len(configs) * plan["repeats"] or any(r["signal"] == "unknown" for r in rows):
                known_cost = sum(r["end_to_end_seconds"] for r in rows
                                 if isinstance(r.get("end_to_end_seconds"), (int, float))
                                 and math.isfinite(r["end_to_end_seconds"]) and r["end_to_end_seconds"] > 0)
                result.append({"instance_id": instance, "policy": method["id"], "evaluable": False,
                               "probe_preparation_seconds_once": preparation,
                               "observed_profiling_seconds_lower_bound": preparation + known_cost,
                               "reason": "requires every declared probe repeat with known quality; incurred outcomes remain in report"})
                continue
            eligible = []
            for config_id, config in configs.items():
                group = [r for r in rows if r["target_config_id"] == config_id]
                if len(group) == plan["repeats"] and all(r["signal"] == "quiet" for r in group):
                    eligible.append((median(r["total_seconds"] for r in group) * balanced_weight(config, spec), config_id))
            choice = min(eligible)[1] if eligible else spec["high_memory_config"]
            paid = sum(r["end_to_end_seconds"] for r in rows)
            memory_time = sum(r["total_seconds"] * measured_configs[r["cell_id"]]["n_workers"] *
                              int(measured_configs[r["cell_id"]]["memory_limit"]) / 1e9 for r in rows)
            thread_time = sum(r["total_seconds"] * measured_configs[r["cell_id"]]["n_workers"] *
                              measured_configs[r["cell_id"]]["threads_per_worker"] for r in rows)
            choices.append((method["id"], choice, preparation, paid, not eligible, memory_time, thread_time))
        for policy, choice, preparation, paid, fallback, memory_time, thread_time in choices:
            selected = [r for r in reference["outcomes"] if r["instance_id"] == instance and r["target_config_id"] == choice]
            config = configs[choice]
            full = describe(selected, 3)
            success_times = [r["total_seconds"] for r in selected if r["status"] == "success"]
            full_time = median(success_times) if success_times else None
            complete_times = [r["end_to_end_seconds"] for r in selected if r["status"] == "success"]
            full_end_to_end = median(complete_times) if complete_times else None
            cost = None if paid is None else paid + preparation
            result.append({"instance_id": instance, "policy": policy, "evaluable": True,
                           "selected_config": choice, "fallback_used": fallback,
                           "selected_full_outcomes": full,
                           "probe_preparation_seconds_once": preparation, "probe_attempt_seconds_sum": paid,
                           "profiling_seconds": cost,
                           "probe_configured_gb_seconds_proxy": memory_time,
                           "probe_configured_thread_seconds_proxy": thread_time,
                           "median_successful_full_lifecycle_seconds": full_time,
                           "median_successful_full_end_to_end_seconds": full_end_to_end,
                           "constructed_successful_request_seconds": (cost + full_end_to_end if cost is not None and full_end_to_end is not None else None),
                           "configured_total_memory_bytes": config["n_workers"] * int(config["memory_limit"]),
                           "median_successful_full_balanced_resource_seconds": (full_time * balanced_weight(config, spec) if full_time is not None else None),
                           "scope": "historical replay; completion and warnings precede conditional successful-time summaries; rule/controller overhead unmeasured"})
    return result


def markdown_stage_b(summary: dict) -> str:
    lines = ["# Stage B probe fidelity diagnosis", "",
             f"Recorded {summary['recorded_cells']} / {summary['planned_cells']} attempts; statuses: {summary['statuses']}.", "",
             "| Instance | Cap | Fraction | Full outcomes | Probe quiet / warning / unknown | Comparison |",
             "| --- | --- | --- | --- | --- | --- |"]
    for group in summary["fidelity_groups"]:
        signals = group["probe"]["signals"]
        label = ("incomplete/unknown" if not group["comparison_available"] else
                 "false reassurance candidate" if group["false_reassurance_candidate"] else
                 "unnecessary warning candidate" if group["unnecessary_warning_candidate"] else "no declared discrepancy")
        lines.append(f"| {group['instance_id']} | {group['target_config_id']} | {group['fraction']} | "
                     f"{group['full']['statuses']} | {signals.get('quiet', 0)} / {signals.get('warning', 0)} / {signals.get('unknown', 0)} | {label} |")
    lines += ["", "## Baseline and probe-choice replay", "",
              "No new selected full jobs were executed by this report. See summary.json for all costs and mixed outcomes.", "",
              "| Instance | Rule | Choice | Full successes / attempts | Profiling seconds |",
              "| --- | --- | --- | --- | --- |"]
    for replay in summary["baseline_replays"]:
        if not replay["evaluable"]:
            lines.append(f"| {replay['instance_id']} | {replay['policy']} | pending/unknown | — | "
                         f"at least {replay['observed_profiling_seconds_lower_bound']:.3f} paid |")
            continue
        full = replay["selected_full_outcomes"]
        cost = replay["profiling_seconds"]
        cost_text = f"{cost:.3f}" if cost is not None else "no executed probes; rule overhead unmeasured"
        lines.append(f"| {replay['instance_id']} | {replay['policy']} | {replay['selected_config']} | "
                     f"{full['statuses'].get('success', 0)} / {full['observed']} | {cost_text} |")
    lines += ["", f"Scalar inconsistencies within the same sample: {summary['inconsistent_successful_results']}", ""]
    lines.extend(f"- {note}" for note in summary["method_notes"])
    return "\n".join(lines) + "\n"
