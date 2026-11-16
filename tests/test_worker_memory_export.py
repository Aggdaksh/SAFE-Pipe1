"""Synthetic evidence tests only: no Dask, data generation or benchmark execution."""
import csv
import json

import pytest

from experiments.export_worker_memory import (
    canonical_hash, collect_stage, compact, event_worker_index, export,
    file_hash, pair_snapshots, safe_event, write_csv,
)


def test_lifetimes_not_collapsed_on_pid_reuse_and_divergence(tmp_path):
    a = {"pid": 7, "started_utc": "2026-01-01T00:00:01+00:00", "peak_rss_bytes": 100}
    b = {**a, "started_utc": "2026-01-01T00:00:02+00:00", "peak_rss_bytes": 200}
    divergent = {**a, "peak_rss_bytes": 101}
    pairs = pair_snapshots([a, b], [(tmp_path / "a.json", divergent), (tmp_path / "b.json", b)])
    assert len(pairs) == 3
    assert sum(source == "diagnostic_only" for _, _, source in pairs) == 1
    assert sum(path is None for _, path, _ in pairs) == 1
    assert next(path for w, path, _ in pairs if w == b).name == "b.json"


def test_event_attribution_uses_lifetime_and_preserves_ambiguity():
    workers = [{"pid": 7, "address": "a", "started_utc": "2026-01-01T00:00:01+00:00"},
               {"pid": 7, "address": "b", "started_utc": "2026-01-01T00:00:03+00:00"}]
    assert event_worker_index(workers, pid=7) is None
    assert event_worker_index(workers, pid=7, utc="2026-01-01T00:00:02+00:00") == 0
    assert event_worker_index(workers, pid=7, utc="2026-01-01T00:00:04+00:00") == 1
    assert event_worker_index(workers, pid=7, address="a") == 0
    assert event_worker_index(workers, pid=8) is None
    assert event_worker_index(workers) is None


def test_evidence_whitelist_keeps_hash_and_excludes_identifiers():
    raw = {"utc": "now", "phase": "execution", "details": {"pid": 7, "worker": "secret-address", "rss": 123},
           "message": "sensitive-local-path"}
    result = safe_event(raw, "nanny_memory_restart", "scheduler-events.jsonl")
    assert result["rss_bytes"] == 123
    assert result["raw_event_sha256"] == canonical_hash(raw)
    assert "secret-address" not in compact(result)
    assert "sensitive-local-path" not in compact(result)


@pytest.fixture
def evidence(tmp_path):
    """One synthetic run: two initial lifetimes and one post-termination added lifetime."""
    root = tmp_path / "data/probes/windows-stage-a-v1"
    published = tmp_path / "reports/research_stage_a_windows_v1"
    root.mkdir(parents=True)
    published.mkdir(parents=True)
    config = {"config_id": "low__full", "memory_limit": "1000", "n_workers": 2, "threads_per_worker": 1}
    cell = {"instance_id": "example", "target_config_id": "low", "method": "full", "repeat_id": 1, "run_config": config}
    cell["cell_id"] = canonical_hash(cell)[:24]
    plan = {"cells": [cell], "fraction": 1.0, "configs": [{"config_id": "low", "memory_limit": "1000"}]}
    plan_hash = canonical_hash(plan)
    workers = [{"pid": i + 1, "address": f"private-{i}", "started_utc": f"2026-01-01T00:00:0{i+1}+00:00",
                "effective_memory_limit_bytes": 1000, "samples": 2, "peak_spilled_disk_bytes": 0,
                "memory_settings": {"max-spill": False}} for i in range(3)]
    scheduler = [{"utc": w["started_utc"], "phase": "setup" if i < 2 else "execution",
                  "kind": "initial_worker" if i < 2 else "worker_added", "worker": w["address"]}
                 for i, w in enumerate(workers)]
    event = {"source": "supervisor.jsonl", "utc": "2026-01-01T00:00:02.5+00:00", "phase": "execution",
             "message": "Worker private-0 (pid=1) exceeded 95% memory budget. Restarting..."}
    directory = root / "diagnostics/example/run"
    directory.mkdir(parents=True)
    (directory / "scheduler-events.jsonl").write_text("\n".join(compact(e) for e in scheduler), encoding="utf-8")
    (directory / "supervisor.jsonl").write_text(compact({k: v for k, v in event.items() if k != "source"}), encoding="utf-8")
    for i, w in enumerate(workers):
        (directory / f"worker-{i}.json").write_text(compact(w), encoding="utf-8")
    manifest = [{"file": p.name, "bytes": p.stat().st_size, "sha256": file_hash(p)} for p in sorted(directory.iterdir())]
    record = {**cell, "config": config, "run_id": "run", "status": "success", "plan_sha256": plan_hash,
              "dataset": {"family": "groupby", "fraction": 1.0},
              "telemetry": {"workers": workers, "worker_count_observed": 3, "observed_restarts_lower_bound": 1},
              "diagnostics": {"directory": "diagnostics/example/run", "retained": True, "files": manifest,
                              "nanny_memory_termination_events": [event], "nanny_memory_termination_count": 1,
                              "worker_exit_events": [{"pid": 1, "utc": event["utc"], "phase": "execution", "signal": 15}]}}
    (root / "plan.json").write_text(compact(plan), encoding="utf-8")
    (published / "plan.json").write_text(compact(plan), encoding="utf-8")
    (root / "runs.jsonl").write_text(compact(record) + "\n", encoding="utf-8")
    (published / "completion_audit.json").write_text(compact({"recorded": 1, "statuses": {"success": 1},
                "diagnostic_files_hash_verified": len(manifest), "raw_nanny_memory_messages_verified": 1}), encoding="utf-8")
    return tmp_path, root, directory, plan_hash, file_hash(root / "runs.jsonl")


def test_read_only_export_preserves_missing_zero_false_and_restart(evidence):
    repo, root, directory, plan_hash, raw_hash = evidence
    tracked = {}
    rows, runs, summary = collect_stage(repo, "A", raw_hash, plan_hash, tracked)
    # This deliberately one-cell fixture is not a completed 48-run study.
    assert summary["issues"] == [{"kind": "run_or_cell_coverage_mismatch"}]
    assert len(rows) == 3 and len({r["worker_lifetime_id"] for r in rows}) == 3
    assert [r["worker_origin"] for r in rows] == ["initial", "initial", "added_during_run"]
    assert rows[0]["worker_nanny_memory_termination_count"] == 1
    assert rows[2]["worker_nanny_memory_termination_count"] == 0
    assert all(row["baseline_rss_bytes"] is None for row in rows)
    assert all(row["peak_spilled_disk_bytes"] == 0 for row in rows)
    assert all(row["memory_settings"]["max-spill"] is False for row in rows)
    assert summary["missing_worker_fields"]["baseline_rss_bytes"] == 3
    assert runs[0]["unmatched_worker_evidence"] == []
    assert "private-" not in compact(rows) + compact(runs)
    assert all(file_hash(path) == digest for path, digest in tracked.items())


def test_hash_mismatch_is_not_marked_verified(evidence):
    repo, _, _, plan_hash, _ = evidence
    _, _, summary = collect_stage(repo, "A", "0" * 64, plan_hash, {})
    assert not summary["integrity_pass"]
    assert {"kind": "raw_records_hash_mismatch"} in summary["issues"]


def test_missing_snapshot_retains_telemetry_lifetime(evidence):
    repo, _, directory, plan_hash, raw_hash = evidence
    (directory / "worker-0.json").unlink()
    rows, _, summary = collect_stage(repo, "A", raw_hash, plan_hash, {})
    assert len(rows) == 3
    assert rows[0]["snapshot_sha256"] is None
    assert summary["telemetry_only_lifetimes"] == 1
    assert any(issue["kind"] == "missing_diagnostic_file" for issue in summary["issues"])
    assert not summary["integrity_pass"]


def test_reject_raw_destination_before_reading_or_writing(tmp_path):
    with pytest.raises(ValueError, match="original data"):
        export(tmp_path, tmp_path / "data/probes/unsafe")
    assert not (tmp_path / "data").exists()


def test_csv_null_and_nested_values_roundtrip(tmp_path):
    row = {"baseline_rss_bytes": None, "peak_spilled_disk_bytes": 0,
           "memory_settings": {"max-spill": False}, "worker_evidence": []}
    path = tmp_path / "example.csv"
    write_csv(path, [row])
    with path.open(encoding="utf-8", newline="") as stream:
        read = next(csv.DictReader(stream))
    assert read["baseline_rss_bytes"] == ""
    assert read["peak_spilled_disk_bytes"] == "0"
    assert json.loads(read["memory_settings"]) == {"max-spill": False}
    assert json.loads(read["worker_evidence"]) == []
