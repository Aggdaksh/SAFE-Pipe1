"""Synthetic prospective-evaluation contracts; run on Windows, no Dask jobs."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest

from safe_pipe.validation.evaluate import evaluate_records, evaluate_study, export_report
from safe_pipe.validation.study import seal_manifest


ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("scan_filter", "groupby", "skewed_join", "sort_merge")
CONFIG_IDS = tuple(f"w{w}_t{t}_{m}g" for w in (1, 2) for t in (1, 2) for m in (1, 2))
START = datetime(2026, 11, 20, tzinfo=timezone.utc)
POWER = {"status": "reported", "power_plugged": True, "percent": 100}


def fixture_manifest(*, abstain=False, upper=None):
    """Frozen scalar predictions: no model import or physical benchmark needed."""
    support = json.loads((ROOT / "artifacts/main_v1/advisor_support.json").read_text(encoding="utf-8"))
    datasets = {row["family"]: row for row in json.loads((ROOT / "configs/datasets_main_v1.json").read_text(encoding="utf-8"))}
    advice = {}
    for family in FAMILIES:
        candidates = []
        for config in support["configurations"]:
            native = config["native"]
            threads = native["n_workers"] * native["threads_per_worker"]
            memory = native["n_workers"] * int(native["memory_limit"][0]) * 1_000_000_000
            point = 2.0
            bound = 12.0 if abstain else (upper or {}).get(config["config_id"], 4.0)
            reasons = ["runtime_upper_exceeds_deadline"] if bound > 10 else []
            candidates.append({"config_id": config["config_id"], "predicted_runtime_s": point,
                "runtime_upper_s": bound, "configured_threads": threads, "total_memory_bytes": memory,
                "score": 0.5 * 0.2 + 0.5 * 0.2 * (0.5 * threads / 4 + 0.5 * memory / 4e9),
                "eligible": not reasons, "rejection_reasons": reasons})
        eligible = sorted((row for row in candidates if row["eligible"]),
                          key=lambda row: (row["score"], row["runtime_upper_s"], row["config_id"]))
        advice[family] = {
            "workload": support["profiles"][family], "engine_sla_seconds": 10.0,
            "effective_deadline_seconds": 10.0, "support": {"matched": True},
            "preferences": {"mode": "balanced", "thread_weight": 0.5, "deadline_reserve": 0.0,
                            "max_threads": None, "max_memory_gb": None, "thread_reference": 4,
                            "memory_reference_bytes": 4_000_000_000},
            "candidates": candidates,
            "decision": {"action": "recommend" if eligible else "abstain",
                         "config_id": eligible[0]["config_id"] if eligible else None,
                         "reason": "synthetic frozen decision"},
        }
    return seal_manifest({
        "schema_version": 1, "data_version": "main-v1", "run_set_id": "synthetic-fresh-v1",
        "created_at": START.isoformat(), "host_scope": "original-host",
        "host_attestation": "Synthetic test fixture; not an executed study.",
        "environment": {"system": "Windows", "node": "test-pc", "platform": "Windows-test"},
        "data_dir": "C:/synthetic-data", "dataset_manifests": datasets,
        "profiles": support["profiles"], "configurations": support["configurations"],
        "plan": [{"family": f, "config_id": c, "repeat_id": r} for f in FAMILIES for c in CONFIG_IDS for r in (1, 2, 3)],
        "advice": advice, "baseline_config_id": "w1_t1_2g", "timeout_s": 120.0,
        "retry_policy": "no retries; one terminal attempt per planned cell",
        "source_sha256_lf": {"safe_pipe/validation/study.py": "a" * 64},
        "input_sha256_lf": {"configs/datasets_main_v1.json": "b" * 64},
    })


def fixture_events(manifest, *, count=96, runtimes=None):
    configs = {config["config_id"]: config for config in manifest["configurations"]}
    events = []
    for position, cell in enumerate(manifest["plan"][:count]):
        base = {"study_id": manifest["study_id"], "run_set_id": manifest["run_set_id"],
                "attempt_id": f"attempt-{position}", "cell": dict(cell), "power": copy.deepcopy(POWER)}
        runtime = (runtimes or {}).get((cell["family"], cell["config_id"], cell["repeat_id"]), float(cell["repeat_id"]))
        result = {"run_id": f"run-{position}", "workload": copy.deepcopy(manifest["profiles"][cell["family"]]),
                  "config": copy.deepcopy(configs[cell["config_id"]]), "status": "success", "engine_seconds": runtime,
                  "failure_category": "none", "notes": "result=1", "repeat_id": cell["repeat_id"],
                  "data_version": "main-v1", "hardware": "test-pc | Windows-test", "backend": "dask_local",
                  "sla_seconds": manifest["advice"][cell["family"]]["engine_sla_seconds"], "voided": False}
        events.append({**copy.deepcopy(base), "event": "started", "timestamp": (START + timedelta(seconds=position * 200 + 1)).isoformat()})
        events.append({**copy.deepcopy(base), "event": "finished", "timestamp": (START + timedelta(seconds=position * 200 + runtime + 2)).isoformat(),
                       "kind": "engine", "result": result, "lifecycle_seconds": runtime + 1, "error": None, "quality_flags": []})
    return events


def write_study(path, manifest, events):
    path.mkdir()
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (path / "attempts.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")


def test_complete_counts_predictions_and_observed_si_resources():
    manifest = fixture_manifest()
    result = evaluate_records(manifest, fixture_events(manifest))
    assert result["completion"]["status"] == "complete"
    assert result["all_configurations"]["planned_cells"] == 96
    assert result["selected_configurations"]["planned_cells"] == 12
    assert result["selected_configurations"]["successful_jobs"] == 12
    assert result["all_configurations"]["runtime_mdape_percent"] == pytest.approx(100 / 3)
    assert result["all_configurations"]["upper_coverage"]["fraction"] == 1
    assert result["all_configurations"]["quality_flagged_cells"] == 0
    profile = result["profiles"]["scan_filter"]
    assert profile["selected_config_id"] == "w1_t1_1g"
    assert profile["selected"]["successful_engine_seconds"] == {"count": 3, "values": [1., 2., 3.], "median": 2., "minimum": 1., "maximum": 3.}
    row = next(row for row in result["cells"] if row["family"] == "scan_filter" and row["config_id"] == "w2_t2_2g" and row["repeat_id"] == 2)
    assert row["configured_thread_seconds"] == 8
    assert row["configured_gb_seconds"] == 8
    assert row["observed_engine_score"] == pytest.approx(.2)


def test_partial_and_pending_are_not_miscounted_as_success():
    manifest = fixture_manifest()
    events = fixture_events(manifest, count=2)[:-1]
    with pytest.raises(ValueError, match="incomplete"):
        evaluate_records(manifest, events)
    result = evaluate_records(manifest, events, allow_partial=True)
    assert result["completion"] == {"status": "incomplete", "planned_cells": 96, "terminal_attempts": 1,
                                     "pending_attempts": 1, "unstarted_cells": 94, "cleanup_required": []}
    assert result["selected_configurations"]["successful_jobs"] == 1
    assert result["profiles"]["scan_filter"]["hindsight_oracle"]["status"] == "incomplete"


def test_empty_report_has_unavailable_prediction_metrics():
    result = evaluate_records(fixture_manifest(), [], allow_partial=True)
    assert result["all_configurations"]["runtime_mdape_percent"] is None
    assert result["all_configurations"]["upper_coverage"]["fraction"] is None
    assert result["all_configurations"]["successful_engine_seconds"]["median"] is None
    assert result["all_configurations"]["successful_jobs"] == 0


def test_startup_failure_keeps_null_runtime_and_requires_cleanup():
    manifest = fixture_manifest()
    events = fixture_events(manifest, count=1)
    events[1].update(kind="infrastructure_error", result=None, error="cluster startup failed", lifecycle_seconds=2.)
    partial = evaluate_records(manifest, events, allow_partial=True)
    failed = partial["selected_configurations"]["unsuccessful_attempts"][0]
    assert failed["status"] == "infrastructure_error"
    assert failed["actual_engine_seconds"] is None
    assert failed["configured_gb_seconds"] is None
    assert failed["error"] == "cluster startup failed"
    assert len(partial["completion"]["cleanup_required"]) == 1
    assert partial["selected_configurations"]["runtime_mdape_percent"] is None


def test_engine_failure_notes_timeout_censoring_and_missing_duration():
    manifest = fixture_manifest()
    events = fixture_events(manifest, count=3)
    events[1]["result"].update(status="timeout", failure_category="actionable", engine_seconds=120., notes="job exceeded timeout")
    events[1]["lifecycle_seconds"] = 121.
    events[1]["timestamp"] = (START + timedelta(seconds=122)).isoformat()
    events[3]["result"].update(status="error", failure_category="non_configuration", engine_seconds=None, notes="engine measurement unavailable")
    result = evaluate_records(manifest, events, allow_partial=True)
    outcomes = result["selected_configurations"]
    assert outcomes["successful_jobs"] == 1
    assert outcomes["runtime_error_denominator_successful_jobs"] == 1
    assert outcomes["runtime_mdape_percent"] == pytest.approx(100 / 3)
    timeout, unknown = outcomes["unsuccessful_attempts"]
    assert timeout["duration_is_censored"] is True
    assert timeout["actual_engine_seconds"] == 120
    assert timeout["error"] == "job exceeded timeout"
    assert unknown["actual_engine_seconds"] is None
    assert unknown["configured_thread_seconds"] is None


def test_final_infrastructure_failure_requires_cleanup_even_with_96_terminal_cells():
    manifest = fixture_manifest()
    events = fixture_events(manifest)
    events[-1].update(kind="infrastructure_error", result=None, error="cleanup failed", lifecycle_seconds=4.)
    with pytest.raises(ValueError, match="incomplete"):
        evaluate_records(manifest, events)
    partial = evaluate_records(manifest, events, allow_partial=True)
    assert partial["completion"]["terminal_attempts"] == 96
    assert partial["completion"]["status"] == "incomplete"
    events.append({"event": "cleanup_acknowledged", "study_id": manifest["study_id"],
                   "run_set_id": manifest["run_set_id"], "cell": copy.deepcopy(events[-1]["cell"]),
                   "attempt_id": events[-1]["attempt_id"], "timestamp": (START + timedelta(seconds=20000)).isoformat(),
                   "workers_stopped": True, "reason": "Synthetic operator confirmation."})
    complete = evaluate_records(manifest, events)
    assert complete["completion"]["status"] == "complete"
    assert complete["all_configurations"]["successful_jobs"] == 95
    assert complete["all_configurations"]["non_success_terminal_attempts"] == 1


def test_abstention_is_zero_selected_jobs_and_no_paired_baseline_cohort():
    manifest = fixture_manifest(abstain=True)
    result = evaluate_records(manifest, fixture_events(manifest))
    assert result["acceptance"]["accepted_profiles"] == 0
    assert result["selected_configurations"]["planned_cells"] == 0
    assert result["baseline_on_accepted_profiles"]["planned_cells"] == 0
    assert result["selected_configurations"]["upper_coverage"]["fraction"] is None
    assert result["profiles"]["scan_filter"]["hindsight_oracle"]["config_id"] == "w1_t1_1g"


def test_oracle_uses_actual_feasibility_not_predicted_upper_gate():
    manifest = fixture_manifest(upper={"w1_t1_1g": 12.})
    result = evaluate_records(manifest, fixture_events(manifest))
    profile = result["profiles"]["scan_filter"]
    assert profile["selected_config_id"] == "w1_t1_2g"
    assert profile["hindsight_oracle"]["config_id"] == "w1_t1_1g"
    assert profile["hindsight_oracle"]["selected_regret_percent"] > 0


def test_no_observed_feasible_oracle_and_no_favorable_cost_subset():
    manifest = fixture_manifest()
    events = fixture_events(manifest, runtimes={(cell["family"], cell["config_id"], cell["repeat_id"]): 11. for cell in manifest["plan"]})
    result = evaluate_records(manifest, events)
    assert result["profiles"]["groupby"]["hindsight_oracle"]["status"] == "no_feasible_configuration"
    assert result["selected_configurations"]["successful_engine_deadline_misses"] == 12
    assert result["paired_feasible_cost_comparisons"]["profile_count"] == 0


def test_reserved_deadline_is_reported_separately():
    manifest = fixture_manifest()
    for report in manifest["advice"].values():
        report["preferences"]["deadline_reserve"] = .5
        report["effective_deadline_seconds"] = 5.
    manifest = seal_manifest(manifest)
    events = fixture_events(manifest, runtimes={(cell["family"], cell["config_id"], cell["repeat_id"]): 7. for cell in manifest["plan"]})
    result = evaluate_records(manifest, events)
    assert result["selected_configurations"]["successes_within_engine_deadline"] == 12
    assert result["selected_configurations"]["successes_within_effective_deadline"] == 0


@pytest.mark.parametrize("mutation", ["wrong_profile", "wrong_config", "wrong_sla", "wrong_host", "wrong_repeat", "wrong_study", "old_time", "duplicate_run_id", "duplicate_cell", "duplicate_finish"])
def test_bad_evidence_cannot_be_joined_to_frozen_predictions(mutation):
    manifest = fixture_manifest()
    events = fixture_events(manifest, count=2)
    if mutation == "wrong_profile":
        events[1]["result"]["workload"]["input_bytes"] += 1
    elif mutation == "wrong_config":
        events[1]["result"]["config"]["native"]["n_workers"] = 2
    elif mutation == "wrong_sla":
        events[1]["result"]["sla_seconds"] += 1
    elif mutation == "wrong_host":
        events[1]["result"]["hardware"] = "other computer"
    elif mutation == "wrong_repeat":
        events[1]["result"]["repeat_id"] = 3
    elif mutation == "wrong_study":
        events[0]["study_id"] = "0" * 64
    elif mutation == "old_time":
        events[0]["timestamp"] = (START - timedelta(seconds=1)).isoformat()
    elif mutation == "duplicate_run_id":
        events[3]["result"]["run_id"] = events[1]["result"]["run_id"]
    elif mutation == "duplicate_cell":
        events[2]["cell"] = dict(events[0]["cell"])
    elif mutation == "duplicate_finish":
        events.insert(2, copy.deepcopy(events[1]))
    with pytest.raises(ValueError):
        evaluate_records(manifest, events, allow_partial=True)


def test_candidate_eligibility_tampering_is_rejected_even_if_resealed():
    manifest = fixture_manifest()
    candidate = manifest["advice"]["scan_filter"]["candidates"][0]
    candidate["rejection_reasons"] = ["runtime_upper_exceeds_deadline"]
    candidate["eligible"] = False
    manifest["advice"]["scan_filter"]["decision"]["config_id"] = "w1_t1_2g"
    manifest = seal_manifest(manifest)
    with pytest.raises(ValueError, match="eligibility"):
        evaluate_records(manifest, [], allow_partial=True)


def test_per_cell_prediction_join_and_quality_flags_remain_visible():
    manifest = fixture_manifest()
    events = fixture_events(manifest, count=1)
    events[1]["power"]["power_plugged"] = False
    events[1]["quality_flags"] = ["unplugged_at_attempt_end"]
    result = evaluate_records(manifest, events, allow_partial=True)
    row = result["cells"][0]
    assert row["family"] == events[1]["cell"]["family"]
    assert row["config_id"] == events[1]["result"]["config"]["config_id"]
    assert row["predicted_runtime_s"] == 2
    assert row["actual_engine_seconds"] == 1
    assert row["power_before"]["power_plugged"] is True
    assert row["power_after"]["power_plugged"] is False
    assert result["all_configurations"]["quality_flag_counts"] == {"unplugged_at_attempt_end": 1}


def test_export_is_replayable_and_refuses_overwrite(tmp_path):
    manifest = fixture_manifest()
    events = fixture_events(manifest)
    study, output = tmp_path / "study", tmp_path / "report"
    write_study(study, manifest, events)
    summary = export_report(study, output)
    assert evaluate_study(output) == summary
    raw_events = [json.loads(line) for line in (output / "attempts.jsonl").read_text(encoding="utf-8").splitlines()]
    expected_hash = hashlib.sha256(json.dumps(raw_events, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    assert summary["evidence"]["journal_snapshot_sha256"] == expected_hash
    assert len((output / "cells.csv").read_text(encoding="utf-8").splitlines()) == 97
    assert "COMPLETE" in (output / "README.md").read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        export_report(study, output)
    with pytest.raises(ValueError, match="separate"):
        export_report(study, study / "report")


def test_export_partial_clearly_labels_progress(tmp_path):
    manifest = fixture_manifest()
    study, output = tmp_path / "study", tmp_path / "partial"
    write_study(study, manifest, fixture_events(manifest, count=1))
    with pytest.raises(ValueError, match="incomplete"):
        export_report(study, output)
    assert not output.exists()
    summary = export_report(study, output, allow_partial=True)
    assert summary["completion"]["status"] == "incomplete"
    assert "INCOMPLETE" in (output / "README.md").read_text(encoding="utf-8")
