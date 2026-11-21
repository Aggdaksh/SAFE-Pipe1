"""Synthetic study/journal tests; no Dask workloads or fitted models are invoked."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from safe_pipe.validation import study


@pytest.fixture(autouse=True)
def fixed_study_clock(monkeypatch):
    monkeypatch.setattr(study, "_utc", lambda: "2026-11-20T02:00:00+00:00")


def synthetic_manifest() -> dict:
    configurations = [{"config_id": c, "native": {
        "n_workers": int(c[1]), "threads_per_worker": int(c[4]),
        "memory_limit": f"{c[6]}GB", "processes": True,
    }, "allocated_vcpus": int(c[1]) * int(c[4]), "allocated_gb": int(c[1]) * int(c[6])}
        for c in study.CONFIG_IDS]
    profiles = {family: {"family": family, "input_bytes": 1000, "estimated_rows": 100,
        "file_count": 2, "partition_count": 2, "skew_score": 0.1, "format": "parquet"}
        for family in study.FAMILIES}
    advice = {family: {
        "workload": profile, "preferences": {"mode": "balanced", "thread_weight": 0.5,
            "deadline_reserve": 0.0, "thread_reference": 4, "memory_reference_bytes": 4_000_000_000,
            "max_threads": None, "max_memory_gb": None},
        "engine_sla_seconds": 10.0, "effective_deadline_seconds": 10.0,
        "decision": {"action": "recommend", "config_id": "w1_t1_1g", "eligible_config_ids": list(study.CONFIG_IDS)},
        "candidates": [{"config_id": c["config_id"], "predicted_runtime_s": 2.0,
            "runtime_upper_s": 3.0, "eligible": True, "score": 0.1,
            "configured_threads": c["allocated_vcpus"], "total_memory_bytes": c["allocated_gb"] * 1_000_000_000,
            "rejection_reasons": []} for c in configurations],
    } for family, profile in profiles.items()}
    return study.seal_manifest({
        "schema_version": 1, "data_version": "main-v1", "run_set_id": "synthetic-only",
        "created_at": "2026-11-20T00:00:00+00:00", "host_scope": "original-host",
        "host_attestation": "Synthetic fixture, never an experiment",
        "environment": {"system": "Windows", "node": "fixture-pc", "platform": "fixture-windows"},
        "timeout_s": 120.0, "baseline_config_id": "w1_t1_2g",
        "retry_policy": "no retries; one terminal attempt per planned cell",
        "plan": [{"family": f, "config_id": c, "repeat_id": r}
                 for f in study.FAMILIES for c in study.CONFIG_IDS for r in (1, 2, 3)],
        "configurations": configurations, "profiles": profiles,
        "dataset_manifests": {f: {"family": f, "data_version": "main-v1"} for f in study.FAMILIES},
        "data_dir": "synthetic-do-not-read", "advice": advice,
        "source_sha256_lf": {"safe_pipe/test.py": "a" * 64},
        "input_sha256_lf": {"configs/test.json": "b" * 64},
    })


def synthetic_events(manifest: dict, count: int = 1) -> list[dict]:
    events = []
    config_map = {c["config_id"]: c for c in manifest["configurations"]}
    for i, cell in enumerate(manifest["plan"][:count]):
        start = {"event": "started", "study_id": manifest["study_id"],
            "run_set_id": manifest["run_set_id"], "attempt_id": f"attempt-{i}", "cell": cell,
            "timestamp": "2026-11-20T01:00:00+00:00", "power": {"power_plugged": True}}
        result = {"run_id": f"run-{i}", "workload": manifest["profiles"][cell["family"]],
            "config": config_map[cell["config_id"]], "repeat_id": cell["repeat_id"],
            "data_version": "main-v1", "backend": "dask_local", "voided": False,
            "hardware": "fixture-pc | fixture-windows", "sla_seconds": 10.0,
            "status": "success", "failure_category": "none", "engine_seconds": 2.0}
        finish = {**start, "event": "finished", "kind": "engine", "result": result,
            "error": None, "lifecycle_seconds": 4.0, "quality_flags": []}
        events.extend((start, finish))
    return events


def write_study(path: Path, manifest: dict, events=None) -> None:
    path.mkdir()
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (path / "attempts.jsonl").write_text("".join(json.dumps(e) + "\n" for e in (events or [])), encoding="utf-8")


def test_manifest_digest_detects_changed_advice():
    manifest = synthetic_manifest()
    study.validate_manifest(manifest)
    manifest["advice"]["groupby"]["candidates"][0]["predicted_runtime_s"] = 1.5
    with pytest.raises(ValueError, match="digest"):
        study.validate_manifest(manifest)


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "wrong_repeat", "new_config"])
def test_plan_requires_exact_96_cells(mutation):
    manifest = synthetic_manifest()
    if mutation == "duplicate":
        manifest["plan"][-1] = manifest["plan"][0]
    elif mutation == "missing":
        manifest["plan"].pop()
    elif mutation == "wrong_repeat":
        manifest["plan"][0]["repeat_id"] = True
    else:
        manifest["plan"][0]["config_id"] = "w4_t4_8g"
    with pytest.raises(ValueError):
        study.validate_manifest(study.seal_manifest(manifest))


def test_full_matrix_keeps_all_records_and_quality_flags():
    manifest = synthetic_manifest()
    events = synthetic_events(manifest, 96)
    events[1]["quality_flags"] = ["unplugged_at_attempt_end"]
    audit = study.audit_journal(manifest, events)
    assert len(audit["completed"]) == 96
    assert not audit["pending"] and not audit["missing"]
    assert audit["completed"][0]["quality_flags"] == ["unplugged_at_attempt_end"]


@pytest.mark.parametrize("mutation", ["wrong_study", "wrong_profile", "wrong_config", "wrong_host", "wrong_sla", "duplicate_run", "timestamp", "order"])
def test_journal_rejects_misbound_results(mutation):
    manifest = synthetic_manifest()
    events = synthetic_events(manifest, 2)
    if mutation == "wrong_study":
        events[1]["study_id"] = "bad"
    elif mutation == "wrong_profile":
        events[1]["result"]["workload"] = {**events[1]["result"]["workload"], "input_bytes": 999}
    elif mutation == "wrong_config":
        events[1]["result"]["config"] = manifest["configurations"][1]
    elif mutation == "wrong_host":
        events[1]["result"]["hardware"] = "another-pc"
    elif mutation == "wrong_sla":
        events[1]["result"]["sla_seconds"] = 999
    elif mutation == "duplicate_run":
        events[3]["result"]["run_id"] = events[1]["result"]["run_id"]
    elif mutation == "timestamp":
        events[1]["timestamp"] = "2026-11-19T01:00:00+00:00"
    else:
        events = events[2:4] + events[:2]
    with pytest.raises(ValueError):
        study.audit_journal(manifest, events)


@pytest.mark.parametrize("status,seconds", [("timeout", 120.0), ("error", None), ("oom", None)])
def test_failed_engine_results_retained_without_fabricated_runtime(status, seconds):
    manifest = synthetic_manifest()
    events = synthetic_events(manifest)
    events[1]["result"].update(status=status, engine_seconds=seconds, failure_category="actionable")
    events[1]["lifecycle_seconds"] = (seconds or 0) + 2.0
    audit = study.audit_journal(manifest, events)
    assert audit["completed"][0]["result"]["engine_seconds"] == seconds
    assert audit["completed"][0]["result"]["status"] == status


def test_success_cannot_have_missing_runtime():
    manifest = synthetic_manifest()
    events = synthetic_events(manifest)
    events[1]["result"]["engine_seconds"] = None
    with pytest.raises(ValueError, match="successful result"):
        study.audit_journal(manifest, events)


def test_pending_attempt_blocks_second_start():
    manifest = synthetic_manifest()
    events = synthetic_events(manifest, 2)
    with pytest.raises(ValueError, match="pending"):
        study.audit_journal(manifest, [events[0], events[2]])
    audit = study.audit_journal(manifest, [events[0]])
    assert len(audit["pending"]) == 1 and len(audit["missing"]) == 95


def test_infrastructure_failure_requires_ack_before_next_cell():
    manifest = synthetic_manifest()
    events = synthetic_events(manifest, 2)
    events[1].update(kind="infrastructure_error", result=None, error="phase unknown")
    with pytest.raises(ValueError, match="cleanup"):
        study.audit_journal(manifest, events)
    ack = {**events[1], "event": "cleanup_acknowledged", "workers_stopped": True, "reason": "Operator checked owned processes"}
    audit = study.audit_journal(manifest, events[:2] + [ack] + events[2:])
    assert len(audit["completed"]) == 2 and not audit["cleanup_required"]


def test_duplicate_or_orphan_terminal_rejected():
    manifest = synthetic_manifest()
    events = synthetic_events(manifest)
    with pytest.raises(ValueError):
        study.audit_journal(manifest, [events[1]])
    with pytest.raises(ValueError):
        study.audit_journal(manifest, events + [events[1]])


def test_truncated_journal_is_not_silently_discarded(tmp_path):
    write_study(tmp_path / "study", synthetic_manifest())
    (tmp_path / "study" / "attempts.jsonl").write_text('{"event":"started"', encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete final write"):
        study.read_events(tmp_path / "study")


def test_foreign_host_or_changed_source_refuses_resume(monkeypatch):
    manifest = synthetic_manifest()
    monkeypatch.setattr(study, "require_windows", lambda: None)
    monkeypatch.setattr(study, "environment_snapshot", lambda: {**manifest["environment"], "node": "other"})
    with pytest.raises(ValueError, match="host or software"):
        study.verify_compatible(manifest, check_datasets=False)
    monkeypatch.setattr(study, "environment_snapshot", lambda: manifest["environment"])
    monkeypatch.setattr(study, "source_hashes", lambda: {})
    with pytest.raises(ValueError, match="source or frozen"):
        study.verify_compatible(manifest, check_datasets=False)


def test_windows_guard_precedes_any_preparation(tmp_path, monkeypatch):
    monkeypatch.setattr(study.platform, "system", lambda: "Darwin")
    with pytest.raises(RuntimeError, match="Windows"):
        study.prepare_study(study_dir=tmp_path / "new", run_set_id="new", data_dir=tmp_path,
            host_scope="original-host", host_attestation="fixture", verification=tmp_path / "missing.json")
    assert not (tmp_path / "new").exists()


def test_existing_study_cannot_be_overwritten(tmp_path, monkeypatch):
    target = tmp_path / "exists"
    target.mkdir()
    monkeypatch.setattr(study, "require_windows", lambda: None)
    with pytest.raises(FileExistsError):
        study.prepare_study(study_dir=target, run_set_id="new", data_dir=tmp_path,
            host_scope="original-host", host_attestation="fixture", verification=tmp_path / "missing.json")


def test_failed_verification_receipt_prevents_data_access(tmp_path, monkeypatch):
    receipt = tmp_path / "verification.json"
    receipt.write_text(json.dumps({"verification_pass": False}), encoding="utf-8")
    monkeypatch.setattr(study, "require_windows", lambda: None)
    monkeypatch.setattr(study, "environment_snapshot", lambda: {})
    monkeypatch.setattr(study, "verify_datasets", lambda _: pytest.fail("must not inspect datasets before verification passes"))
    with pytest.raises(ValueError, match="passing Windows verification"):
        study.prepare_study(study_dir=tmp_path / "study", run_set_id="new", data_dir=tmp_path,
            host_scope="original-host", host_attestation="fixture", verification=receipt)
    assert not (tmp_path / "study").exists()


def test_lock_refuses_concurrent_writer(tmp_path):
    with study.writer_lock(tmp_path):
        with pytest.raises(RuntimeError, match="another process"):
            with study.writer_lock(tmp_path):
                pytest.fail("must not acquire twice")


def test_run_stops_after_collector_exception_and_requires_cleanup(tmp_path, monkeypatch):
    from safe_pipe import collector
    manifest = synthetic_manifest()
    folder = tmp_path / "study"
    write_study(folder, manifest)
    monkeypatch.setattr(study, "ROOT", tmp_path)
    monkeypatch.setattr(study, "require_windows", lambda: None)
    monkeypatch.setattr(study, "verify_compatible", lambda *args, **kwargs: None)
    monkeypatch.setattr(study, "power_snapshot", lambda: {"power_plugged": True})
    calls = []
    def broken(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("startup or cleanup failure")
    monkeypatch.setattr(collector, "collect_dask", broken)
    result = study.run_batch(folder, max_jobs=16)
    assert len(calls) == 1
    assert result["terminal_attempts"] == 1 and len(result["cleanup_required"]) == 1
    events = study.read_events(folder)
    assert events[1]["kind"] == "infrastructure_error" and events[1]["result"] is None
    with pytest.raises(ValueError, match="stopped-worker"):
        study.run_batch(folder, max_jobs=1)
    assert len(calls) == 1


def test_resolve_requires_worker_confirmation_and_never_retries(tmp_path, monkeypatch):
    manifest = synthetic_manifest()
    folder = tmp_path / "study"
    write_study(folder, manifest, synthetic_events(manifest)[:1])
    monkeypatch.setattr(study, "require_windows", lambda: None)
    monkeypatch.setattr(study, "environment_snapshot", lambda: manifest["environment"])
    with pytest.raises(ValueError, match="stopped-worker"):
        study.resolve_pending(folder, attempt_id="attempt-0", reason="checked")
    result = study.resolve_pending(folder, attempt_id="attempt-0", reason="owned processes stopped", workers_stopped=True)
    assert result["terminal_attempts"] == 1 and result["unstarted_cells"] == 95
    assert not result["cleanup_required"] and not result["pending_attempts"]
    audit = study.audit_journal(manifest, study.read_events(folder))
    assert audit["completed"][0]["kind"] == "aborted"
    assert audit["completed"][0]["lifecycle_seconds"] is None


def test_original_environment_deviations_are_explicit():
    report = study.compare_original_environment({"logical_cpus": 8, "ram_bytes": 16_000_000_000,
        "platform": "Windows-11-10.0.26200-SP0", "processor": "other CPU", "python": "3.14.6", "packages": {}})
    assert any(item["field"] == "logical_cpus" for item in report["differences"])
    assert not any(item["field"] == "windows_build" for item in report["differences"])


@pytest.mark.parametrize("mutation", ["runtime_exceeds_lifecycle", "wrong_timeout_limit", "unknown_category"])
def test_impossible_engine_timing_or_labels_are_rejected(mutation):
    manifest = synthetic_manifest()
    events = synthetic_events(manifest)
    if mutation == "runtime_exceeds_lifecycle":
        events[1]["result"]["engine_seconds"] = 1000.0
    elif mutation == "wrong_timeout_limit":
        events[1]["result"].update(status="timeout", failure_category="actionable")
    else:
        events[1]["result"]["failure_category"] = "mystery"
    with pytest.raises(ValueError):
        study.audit_journal(manifest, events)


def test_source_drift_during_attempt_is_persisted_and_stops_batch(tmp_path, monkeypatch):
    from safe_pipe import collector
    manifest = synthetic_manifest()
    folder = tmp_path / "study"
    write_study(folder, manifest)
    monkeypatch.setattr(study, "ROOT", tmp_path)
    monkeypatch.setattr(study, "require_windows", lambda: None)
    monkeypatch.setattr(study, "power_snapshot", lambda: {"power_plugged": True})
    checks = []
    def verify(*args, **kwargs):
        checks.append(1)
        if len(checks) >= 3:
            raise ValueError("source changed")
    monkeypatch.setattr(study, "verify_compatible", verify)
    # Using an infrastructure exception avoids invoking any engine or predictor.
    def broken(**kwargs):
        raise RuntimeError("fixture collection failure")
    monkeypatch.setattr(collector, "collect_dask", broken)
    result = study.run_batch(folder, max_jobs=16)
    assert result["terminal_attempts"] == 1 and result["quality_flagged_attempts"] == 1
    terminal = study.read_events(folder)[-1]
    assert "source_or_environment_changed_during_attempt" in terminal["quality_flags"]
    assert "source changed" in terminal["integrity_error"]


def test_prepare_freezes_advice_and_receipt_before_creating_empty_journal(tmp_path, monkeypatch):
    from safe_pipe import advisor, grid
    fixture = synthetic_manifest()
    root = tmp_path / "repo"
    (root / "configs").mkdir(parents=True)
    (root / study.INDEX).write_text(json.dumps(list(fixture["dataset_manifests"].values())), encoding="utf-8")
    (root / study.SLA).write_text(json.dumps({"data_version": "main-v1", "families": {
        family: {"sla_seconds": 10.0} for family in study.FAMILIES}}), encoding="utf-8")
    (root / study.PLAN).write_text(json.dumps({"data_version": "main-v1", "cells": fixture["plan"], "shuffle_seed": 2026}), encoding="utf-8")
    receipt = {"verification_pass": True, "source_sha256_lf": fixture["source_sha256_lf"],
        "environment": fixture["environment"], "created_utc": "2026-11-20T01:00:00+00:00"}
    verification = tmp_path / "verification.json"
    verification.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(study, "ROOT", root)
    monkeypatch.setattr(study, "require_windows", lambda: None)
    monkeypatch.setattr(study, "environment_snapshot", lambda: fixture["environment"])
    monkeypatch.setattr(study, "source_hashes", lambda: fixture["source_sha256_lf"])
    monkeypatch.setattr(study, "input_hashes", lambda: fixture["input_sha256_lf"])
    monkeypatch.setattr(study, "power_snapshot", lambda: {"power_plugged": True})
    checked = []
    monkeypatch.setattr(study, "verify_datasets", lambda manifest: checked.append(manifest))
    def model(value):
        return SimpleNamespace(model_dump=lambda **kwargs: value)
    monkeypatch.setattr(advisor, "frozen_profiles", lambda _: {
        family: model(value) for family, value in fixture["profiles"].items()})
    monkeypatch.setattr(advisor, "load_advice", lambda **kwargs: fixture["advice"][kwargs["workload"].model_dump()["family"]])
    monkeypatch.setattr(grid, "load_grid", lambda: [model(c) for c in fixture["configurations"]])
    frozen = study.prepare_study(study_dir=tmp_path / "study", run_set_id="fresh-fixture",
        data_dir=tmp_path / "data", host_scope="original-host", host_attestation="fixture only",
        verification=verification)
    assert len(checked) == 1
    assert frozen["advice"] == fixture["advice"] and frozen["verification"] == receipt
    assert study.read_events(tmp_path / "study") == []
    assert study.load_study(tmp_path / "study")["study_id"] == frozen["study_id"]


def test_preparation_rechecks_verification_after_dataset_hashing(tmp_path, monkeypatch):
    from safe_pipe import advisor
    fixture = synthetic_manifest()
    root = tmp_path / "repo"
    (root / "configs").mkdir(parents=True)
    (root / study.INDEX).write_text(json.dumps(list(fixture["dataset_manifests"].values())), encoding="utf-8")
    (root / study.SLA).write_text(json.dumps({"data_version": "main-v1", "families": {}}), encoding="utf-8")
    (root / study.PLAN).write_text(json.dumps({"data_version": "main-v1", "cells": fixture["plan"]}), encoding="utf-8")
    receipt = {"verification_pass": True, "source_sha256_lf": fixture["source_sha256_lf"],
        "environment": fixture["environment"], "created_utc": "2026-11-20T01:00:00+00:00"}
    verification = tmp_path / "verification.json"
    verification.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(study, "ROOT", root)
    monkeypatch.setattr(study, "require_windows", lambda: None)
    environment = dict(fixture["environment"])
    monkeypatch.setattr(study, "environment_snapshot", lambda: dict(environment))
    monkeypatch.setattr(study, "source_hashes", lambda: fixture["source_sha256_lf"])
    monkeypatch.setattr(study, "input_hashes", lambda: fixture["input_sha256_lf"])
    monkeypatch.setattr(study, "power_snapshot", lambda: {"power_plugged": True})
    monkeypatch.setattr(advisor, "frozen_profiles", lambda _: {})
    monkeypatch.setattr(study, "verify_datasets", lambda _: environment.update(node="unexpected-new-host"))
    with pytest.raises(ValueError, match="changed while checking datasets"):
        study.prepare_study(study_dir=tmp_path / "study", run_set_id="fresh-fixture",
            data_dir=tmp_path / "data", host_scope="original-host", host_attestation="fixture only",
            verification=verification)
    assert not (tmp_path / "study").exists()
