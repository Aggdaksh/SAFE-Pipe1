"""Evaluate a frozen advisor against a separate, append-only fresh-run study.

No model is loaded, fitted, or consulted here. Predictions come exclusively from
the advice saved before the study started. Completed engine failures, aborted
attempts, missing work and abstention are deliberately different outcomes.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median

from safe_pipe.cost import resource_score
from safe_pipe.memory import dask_memory_bytes
from safe_pipe.validation.study import audit_journal, load_study, read_events


def _distribution(values: list[float]) -> dict:
    return {
        "count": len(values), "values": values,
        "median": median(values) if values else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }


def _key(cell: dict) -> tuple[str, str, int]:
    return cell["family"], cell["config_id"], cell["repeat_id"]


def _finite(value, name: str, *, positive: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ValueError(f"invalid {name}")
    return float(value)


def _observed_score(runtime: float, config: dict, report: dict) -> float:
    native = config["native"]
    preferences = report["preferences"]
    parts = resource_score(
        runtime, native["n_workers"] * native["threads_per_worker"],
        native["n_workers"] * dask_memory_bytes(native["memory_limit"]),
        time_reference_s=report["engine_sla_seconds"],
        thread_weight=preferences["thread_weight"],
        thread_reference=preferences["thread_reference"],
        memory_reference_bytes=preferences["memory_reference_bytes"],
    )
    speed_weight = {"balanced": 0.5, "fastest": 1.0, "resource": 0.0}[preferences["mode"]]
    return speed_weight * parts["time_ratio"] + (1 - speed_weight) * parts["resource_score"]


def _advice_index(manifest: dict) -> dict:
    """Fail on inconsistent predictions even if a test fixture was re-sealed."""
    configurations = {row["config_id"]: row for row in manifest["configurations"]}
    result = {}
    if set(manifest["advice"]) != set(manifest["profiles"]):
        raise ValueError("saved advice does not cover the frozen profiles")
    for family, report in manifest["advice"].items():
        if report["workload"] != manifest["profiles"][family]:
            raise ValueError("saved advice workload differs from the frozen profile")
        deadline = _finite(report["engine_sla_seconds"], "engine deadline")
        effective = _finite(report["effective_deadline_seconds"], "effective deadline")
        preferences = report["preferences"]
        if preferences["mode"] != "balanced":
            raise ValueError("this study evaluates the predeclared balanced primary policy")
        if not math.isclose(effective, deadline * (1 - preferences["deadline_reserve"]), rel_tol=1e-12):
            raise ValueError("saved effective deadline differs from frozen preferences")
        candidates = {row["config_id"]: row for row in report["candidates"]}
        if len(candidates) != len(report["candidates"]) or set(candidates) != set(configurations):
            raise ValueError("saved candidates must match the complete configuration grid")
        for config_id, row in candidates.items():
            point = _finite(row["predicted_runtime_s"], "saved point prediction")
            upper = _finite(row["runtime_upper_s"], "saved upper prediction")
            if upper < point:
                raise ValueError("saved upper prediction is below its point prediction")
            config = configurations[config_id]
            native = config["native"]
            if (row["configured_threads"] != native["n_workers"] * native["threads_per_worker"]
                    or row["total_memory_bytes"] != native["n_workers"] * dask_memory_bytes(native["memory_limit"])):
                raise ValueError("saved candidate resource quantities differ from the frozen grid")
            if not math.isclose(row["score"], _observed_score(point, config, report), rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("saved candidate score differs from frozen preferences")
            reasons = []
            if not report["support"]["matched"]:
                reasons.append("unsupported_workload_profile")
            if upper > effective:
                reasons.append("runtime_upper_exceeds_deadline")
            if preferences["max_threads"] is not None and row["configured_threads"] > preferences["max_threads"]:
                reasons.append("configured_threads_exceed_budget")
            if preferences["max_memory_gb"] is not None and row["total_memory_bytes"] / 1e9 > preferences["max_memory_gb"]:
                reasons.append("configured_memory_exceeds_budget")
            if report["workload"]["input_bytes"] > 4 * row["total_memory_bytes"]:
                reasons.append("heuristic_input_memory_guard")
            if row["rejection_reasons"] != reasons or type(row["eligible"]) is not bool or row["eligible"] != (not reasons):
                raise ValueError("saved candidate eligibility differs from frozen constraints")
        eligible = sorted(
            (row for row in candidates.values() if row["eligible"]),
            key=lambda row: (row["score"], row["runtime_upper_s"], row["config_id"]),
        )
        decision = report["decision"]
        expected = eligible[0]["config_id"] if eligible else None
        if (decision["config_id"] != expected
                or decision["action"] != ("recommend" if eligible else "abstain")):
            raise ValueError("saved decision does not match the frozen candidate ranking")
        result[family] = candidates
    return result


def _outcomes(rows: list[dict]) -> dict:
    terminal = [row for row in rows if row["phase"] == "completed"]
    successful = [row for row in terminal if row["status"] == "success"]
    failed = [row for row in terminal if row["status"] != "success"]
    covered = sum(row["actual_engine_seconds"] <= row["runtime_upper_s"] for row in successful)
    errors = [100 * abs(row["actual_engine_seconds"] - row["predicted_runtime_s"])
              / row["actual_engine_seconds"] for row in successful]
    return {
        "planned_cells": len(rows), "terminal_attempts": len(terminal),
        "pending_attempts": sum(row["phase"] == "pending" for row in rows),
        "unstarted_cells": sum(row["phase"] == "unstarted" for row in rows),
        "status_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
        "quality_flagged_cells": sum(bool(row["quality_flags"]) for row in rows),
        "quality_flag_counts": dict(sorted(Counter(flag for row in rows for flag in row["quality_flags"]).items())),
        "successful_jobs": len(successful), "non_success_terminal_attempts": len(failed),
        "successes_within_engine_deadline": sum(row["within_engine_deadline"] for row in successful),
        "successes_within_effective_deadline": sum(row["within_effective_deadline"] for row in successful),
        "successful_engine_deadline_misses": sum(not row["within_engine_deadline"] for row in successful),
        "successful_effective_deadline_misses": sum(not row["within_effective_deadline"] for row in successful),
        "runtime_mdape_percent": median(errors) if errors else None,
        "runtime_error_denominator_successful_jobs": len(successful),
        "upper_coverage": {"covered_successful_jobs": covered,
                           "denominator_successful_jobs": len(successful),
                           "fraction": covered / len(successful) if successful else None},
        "successful_engine_seconds": _distribution([row["actual_engine_seconds"] for row in successful]),
        "successful_engine_scores": _distribution([row["observed_engine_score"] for row in successful]),
        "successful_configured_thread_seconds": _distribution([row["configured_thread_seconds"] for row in successful]),
        "successful_configured_gb_seconds": _distribution([row["configured_gb_seconds"] for row in successful]),
        "recorded_lifecycle_seconds": _distribution([row["lifecycle_seconds"] for row in terminal
                                                     if row["lifecycle_seconds"] is not None]),
        "unsuccessful_attempts": [
            {key: row[key] for key in ("family", "config_id", "repeat_id", "attempt_id", "status",
                                      "actual_engine_seconds", "duration_is_censored", "lifecycle_seconds",
                                      "configured_thread_seconds", "configured_gb_seconds", "error", "quality_flags")}
            for row in failed
        ],
    }


def evaluate_records(manifest: dict, events: list[dict], *, allow_partial: bool = False) -> dict:
    """Pure evaluation over saved evidence; journal validation is shared with collection."""
    audit = audit_journal(manifest, events)
    candidates = _advice_index(manifest)
    cleanup_required = audit.get("cleanup_required", [])
    complete = not audit["pending"] and not audit["missing"] and not cleanup_required
    if not complete and not allow_partial:
        raise ValueError("study is incomplete; use --allow-partial for a labelled progress report")
    completed = {_key(row["cell"]): row for row in audit["completed"]}
    pending = {_key(row["cell"]): row for row in audit["pending"]}
    starts = {_key(row["cell"]): row for row in events if row["event"] == "started"}
    configurations = {row["config_id"]: row for row in manifest["configurations"]}
    rows = []
    for cell in manifest["plan"]:
        family, config_id, _ = _key(cell)
        advice = manifest["advice"][family]
        candidate = candidates[family][config_id]
        event = completed.get(_key(cell))
        start = pending.get(_key(cell))
        result = event["result"] if event else None
        status = (result["status"] if result else event["kind"]) if event else ("pending" if start else "unstarted")
        duration = result.get("engine_seconds") if result else None
        if duration is not None:
            duration = _finite(duration, "observed engine duration")
        success = status == "success"
        quality_flags = list(event.get("quality_flags", [])) if event else []
        if event and ("power" not in starts.get(_key(cell), {}) or "power" not in event):
            quality_flags.append("power_observation_missing")
        if event and event.get("power", {}).get("power_plugged") is False:
            quality_flags.append("unplugged_at_attempt_end")
        if event and event.get("power", {}).get("power_plugged") is None:
            quality_flags.append("power_state_unverified")
        rows.append({
            **cell, "study_id": manifest["study_id"], "run_set_id": manifest["run_set_id"],
            "phase": "completed" if event else ("pending" if start else "unstarted"),
            "attempt_id": event["attempt_id"] if event else (start["attempt_id"] if start else None),
            "run_id": result["run_id"] if result else None,
            "status": status, "failure_category": result.get("failure_category") if result else None,
            "selected": advice["decision"]["config_id"] == config_id,
            "baseline": manifest["baseline_config_id"] == config_id,
            "predicted_runtime_s": candidate["predicted_runtime_s"], "runtime_upper_s": candidate["runtime_upper_s"],
            "engine_sla_seconds": advice["engine_sla_seconds"],
            "effective_deadline_seconds": advice["effective_deadline_seconds"],
            "actual_engine_seconds": duration,
            "duration_is_censored": status == "timeout",
            "within_engine_deadline": bool(success and duration <= advice["engine_sla_seconds"]),
            "within_effective_deadline": bool(success and duration <= advice["effective_deadline_seconds"]),
            "observed_engine_score": _observed_score(duration, configurations[config_id], advice) if duration is not None else None,
            "configured_thread_seconds": duration * candidate["configured_threads"] if duration is not None else None,
            "configured_gb_seconds": duration * candidate["total_memory_bytes"] / 1e9 if duration is not None else None,
            "lifecycle_seconds": event["lifecycle_seconds"] if event else None,
            "error": (event["error"] or (result.get("notes") if result and not success else None)) if event else None,
            "power_before": starts.get(_key(cell), {}).get("power"),
            "power_after": event.get("power") if event else None,
            "quality_flags": sorted(set(quality_flags)),
        })
    profiles = {}
    selected_rows, matched_baseline_rows = [], []
    paired_cost_comparisons = []
    for family, advice in manifest["advice"].items():
        family_rows = [row for row in rows if row["family"] == family]
        groups = {config_id: _outcomes([row for row in family_rows if row["config_id"] == config_id])
                  for config_id in configurations}
        selected = advice["decision"]["config_id"]
        chosen = [row for row in family_rows if row["config_id"] == selected]
        baseline = [row for row in family_rows if row["baseline"]]
        if selected is not None:
            selected_rows.extend(chosen)
            matched_baseline_rows.extend(baseline)
        eligible_oracles = []
        all_family_terminal = all(row["phase"] == "completed" for row in family_rows)
        if all_family_terminal:
            for config_id, group in groups.items():
                # The oracle uses observed feasibility. The predictor's upper
                # estimate is NOT a hindsight feasibility constraint.
                candidate = candidates[family][config_id]
                allowed = not set(candidate["rejection_reasons"]) - {"runtime_upper_exceeds_deadline"}
                if (allowed and group["planned_cells"] == 3
                        and group["successes_within_effective_deadline"] == 3):
                    eligible_oracles.append((group["successful_engine_scores"]["median"], config_id))
        eligible_oracles.sort()
        oracle_id = eligible_oracles[0][1] if eligible_oracles else None
        chosen_metrics = _outcomes(chosen)
        baseline_metrics = _outcomes(baseline)
        pair = None
        if (selected is not None and chosen_metrics["successes_within_effective_deadline"] == 3
                and baseline_metrics["successes_within_effective_deadline"] == 3):
            selected_score = chosen_metrics["successful_engine_scores"]["median"]
            reference_score = baseline_metrics["successful_engine_scores"]["median"]
            pair = {"family": family, "selected_config_id": selected,
                    "baseline_config_id": manifest["baseline_config_id"],
                    "selected_median_engine_score": selected_score, "baseline_median_engine_score": reference_score,
                    "score_reduction_percent": 100 * (1 - selected_score / reference_score)}
            paired_cost_comparisons.append(pair)
        regret = None
        if oracle_id is not None and chosen_metrics["successes_within_effective_deadline"] == 3:
            regret = 100 * (chosen_metrics["successful_engine_scores"]["median"] / eligible_oracles[0][0] - 1)
        profiles[family] = {
            "action": advice["decision"]["action"], "selected_config_id": selected,
            "reason": advice["decision"]["reason"],
            "engine_deadline_seconds": advice["engine_sla_seconds"],
            "effective_deadline_seconds": advice["effective_deadline_seconds"],
            "selected": chosen_metrics, "baseline": baseline_metrics, "configurations": groups,
            "paired_feasible_comparison": pair,
            "hindsight_oracle": {
                "status": "available" if oracle_id else ("no_feasible_configuration" if all_family_terminal else "incomplete"),
                "config_id": oracle_id, "feasible_configuration_count": len(eligible_oracles),
                "median_engine_score": eligible_oracles[0][0] if oracle_id else None,
                "selected_regret_percent": regret,
                "criterion": "All three repeats succeed within effective deadline, pass frozen support/budgets/memory guard; minimum median observed balanced engine score, tie by config ID. Noisy hindsight reference only.",
            },
        }
    accepted = [family for family, report in manifest["advice"].items() if report["decision"]["action"] == "recommend"]
    journal_digest = hashlib.sha256(json.dumps(events, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return {
        "schema_version": 1, "study_id": manifest["study_id"], "run_set_id": manifest["run_set_id"],
        "evaluation": "fresh frozen-profile repeatability" if manifest["host_scope"] == "original-host" else "fresh frozen-profile host transfer",
        "host_scope": manifest["host_scope"], "environment": manifest["environment"],
        "host_attestation": manifest.get("host_attestation"),
        "original_environment_comparison": manifest.get("original_environment_comparison"),
        "completion": {"status": "complete" if complete else "incomplete", "planned_cells": len(rows),
                       "terminal_attempts": len(completed), "pending_attempts": len(pending),
                       "unstarted_cells": len(audit["missing"]), "cleanup_required": cleanup_required},
        "evidence": {"manifest_study_id": manifest["study_id"], "journal_snapshot_sha256": journal_digest,
                     "journal_hash_encoding": "SHA256 of JSON event array, sorted keys, compact separators, UTF-8",
                     "journal_event_count": len(events), "last_event_timestamp": events[-1]["timestamp"] if events else None,
                     "prediction_source": "pre-run advice embedded in frozen study manifest; no inference or fitting during evaluation"},
        "acceptance": {"accepted_profiles": len(accepted), "total_profiles": len(profiles),
                       "accepted_families": accepted, "abstained_families": [f for f in profiles if f not in accepted]},
        "all_configurations": _outcomes(rows), "selected_configurations": _outcomes(selected_rows),
        "baseline_on_accepted_profiles": {"config_id": manifest["baseline_config_id"], **_outcomes(matched_baseline_rows)},
        "paired_feasible_cost_comparisons": {
            "profile_count": len(paired_cost_comparisons), "accepted_profile_count": len(accepted),
            "comparisons": paired_cost_comparisons,
            "note": "Cost reductions are shown only when both choices succeeded within the effective deadline in all three repeats. Other failures remain in outcome tables; this subset is not an overall policy improvement estimate.",
        },
        "profiles": profiles, "cells": rows,
        "limitations": [
            "Four exact profiles on a recorded host; repeated executions do not establish new-workload generalization.",
            "Original-host scope is operator-attested; environment fingerprints bind collection/resume, not independent proof of machine identity.",
            "Acceptance counts profiles, deadline outcomes count selected repetitions; neither abstention nor an unstarted cell is a success.",
            "MdAPE and upper coverage condition on successful engine runs. Failures, timeouts and unavailable durations are retained separately.",
            "Configured thread/GB-seconds and balanced scores cover engine time only. They are allocation-time proxies, not measured CPU, peak memory, energy or currency.",
            "Timeout engine duration is censored and the original collector records the future-wait timeout budget. Its allocation-time proxy omits graph construction and is not exact engine resource exposure or time to successful completion.",
            "Lifecycle time includes the collector call (cluster setup, engine and cleanup); input verification, advice preparation and evaluation are outside it.",
            "Three repeats provide observed medians/ranges, not precise tail probabilities or selected-policy coverage guarantees.",
            "Power and other quality flags remain visible in every affected cell. Aggregates retain flagged attempts; they must not be presented as a wholly controlled study.",
            "An unfavorable performance result can still be a complete, audited experiment. Any subsequent tuning needs another untouched evaluation.",
        ],
    }


def evaluate_study(study_dir: Path, *, allow_partial: bool = False) -> dict:
    return evaluate_records(load_study(study_dir), read_events(study_dir), allow_partial=allow_partial)


def _display(value, decimals: int = 3) -> str:
    return "unavailable" if value is None else (f"{value:.{decimals}f}" if isinstance(value, float) else str(value))


def _markdown(summary: dict) -> str:
    selected = summary["selected_configurations"]
    overall = summary["all_configurations"]
    completion = summary["completion"]
    lines = [
        "# Fresh advisor evaluation", "", f"Study: `{summary['run_set_id']}`", "",
        f"**Status: {completion['status'].upper()}** — {completion['terminal_attempts']}/{completion['planned_cells']} planned cells have terminal attempt records.", "",
        f"Scope: {summary['evaluation']}. The original-host classification, where present, is operator-attested.", "",
        f"Recorded host attestation: {summary['host_attestation']}", "",
        f"Historical environment comparison: {json.dumps(summary['original_environment_comparison'], sort_keys=True)}. A changed software environment must be considered when interpreting repeatability.", "",
        f"Quality: {overall['quality_flagged_cells']} cells carry flags. Flagged observations remain in the aggregates; review cells.csv and summary.json before interpreting comparisons.", "",
        f"Recommendations: {summary['acceptance']['accepted_profiles']}/{summary['acceptance']['total_profiles']} profiles; abstention is not successful execution.", "",
        f"Selected configurations: {selected['successful_jobs']}/{selected['planned_cells']} successful jobs; {selected['successes_within_engine_deadline']}/{selected['planned_cells']} successful within engine deadline. Pending/unstarted cells remain in the planned denominator.", "",
        f"All-configuration successful-run MdAPE: {_display(overall['runtime_mdape_percent'])}% on {overall['runtime_error_denominator_successful_jobs']} successful jobs. Upper coverage: {overall['upper_coverage']['covered_successful_jobs']}/{overall['upper_coverage']['denominator_successful_jobs']} successful jobs. No success observations means these metrics are unavailable.", "",
        "| Profile | Choice | Successes / planned | Within engine deadline | Median successful engine seconds | Hindsight choice |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for family, report in summary["profiles"].items():
        result = report["selected"]
        lines.append(f"| {family} | {report['selected_config_id'] or 'abstain'} | {result['successful_jobs']}/{result['planned_cells']} | {result['successes_within_engine_deadline']} | {_display(result['successful_engine_seconds']['median'])} | {report['hindsight_oracle']['config_id'] or report['hindsight_oracle']['status']} |")
    lines.extend(["", "The fixed baseline uses the same accepted profiles. Failed choices are retained; a cheaper failed run is not a saving. Paired cost comparisons require three feasible successes for both choices and state their restricted denominator.", "", "Individual cells, unsuccessful attempts, baseline outcomes, observed ranges, reserved-deadline outcomes and cost components are in `summary.json` and `cells.csv`.", "", "## Interpretation", ""])
    lines.extend(f"- {note}" for note in summary["limitations"])
    return "\n".join(lines) + "\n"


def export_report(study_dir: Path, output_dir: Path, *, allow_partial: bool = False) -> dict:
    """Create a new report directory, never overwrite existing evidence."""
    manifest, events = load_study(study_dir), read_events(study_dir)
    summary = evaluate_records(manifest, events, allow_partial=allow_partial)
    study_dir, output_dir = Path(study_dir).resolve(), Path(output_dir).resolve()
    if output_dir == study_dir or study_dir in output_dir.parents:
        raise ValueError("report output must be separate from the frozen study directory")
    output_dir.mkdir(parents=True, exist_ok=False)
    # Export the precise in-memory snapshot evaluated above, not a later reread
    # of a journal that a collector might have appended to in the meantime.
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output_dir / "attempts.jsonl").write_text("".join(
        json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n" for event in events
    ), encoding="utf-8")
    rows = summary["cells"]
    with (output_dir / "cells.csv").open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({key: json.dumps(value, sort_keys=True, allow_nan=False) if isinstance(value, (dict, list)) else value
                         for key, value in row.items()} for row in rows)
    (output_dir / "README.md").write_text(_markdown(summary), encoding="utf-8")
    # Write summary last: a partially written output is never a completed report.
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return summary
