"""Persistence and resume checks without starting Dask or generating datasets."""
import json

import pytest

from experiments import probe_pilot as pilot
from safe_pipe.research import probe_runner, probe_workloads


def frozen_plan(tmp_path):
    manifest = {"fixture": "no physical dataset required"}
    configs = [{"config_id": name, "n_workers": 1, "threads_per_worker": 1,
                "memory_limit": "1000000000"} for name in ("a", "b")]
    cells = []
    for config in configs:
        cell = {"instance_id": "tiny", "target_config_id": config["config_id"],
                "method": "full", "repeat_id": 1, "run_config": config}
        cell["cell_id"] = pilot.canonical_hash(cell)[:24]
        cells.append(cell)
    plan = {"schema_version": pilot.SCHEMA, "preset": "smoke", "role": "development_only",
            "source_fingerprints": pilot.source_fingerprints(), "cells": cells,
            "configs": configs, "repeats": 1, "ranking_tolerance": .05,
            "methods": ["full"], "timeout_seconds": 10,
            "datasets": {"tiny": {"full": "datasets/tiny"}},
            "dataset_fingerprints": {"tiny": {"full": pilot.canonical_hash(manifest)}}}
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return path, plan, manifest


def test_interruption_is_persisted_stops_batch_and_is_not_retried(tmp_path, monkeypatch):
    path, plan, manifest = frozen_plan(tmp_path)
    calls = []
    monkeypatch.setattr(probe_runner, "validate_host_budget", lambda _: {})
    monkeypatch.setattr(probe_workloads, "load_manifest", lambda *a, **kw: manifest)

    def interrupted(dataset, config, **kwargs):
        calls.append(config["config_id"])
        return {"status": "interrupted", "timings": {"execution_seconds": None}}

    monkeypatch.setattr(probe_runner, "run_probe", interrupted)
    pilot.run(path, max_runs=2)
    records = pilot.load_records(tmp_path / "runs.jsonl", pilot.canonical_hash(plan))
    assert calls == ["a"]
    assert len(records) == 1 and records[0]["status"] == "interrupted"
    assert records[0]["cell_id"] == plan["cells"][0]["cell_id"]
    assert not (tmp_path / ".running.lock").exists()

    # A deliberate resume advances to the next cell, preserving the interrupted attempt.
    pilot.run(path, max_runs=2)
    records = pilot.load_records(tmp_path / "runs.jsonl", pilot.canonical_hash(plan))
    assert calls == ["a", "b"]
    assert len(records) == 2
    assert all(row["status"] == "interrupted" for row in records)
    assert not (tmp_path / ".running.lock").exists()


def test_changed_source_refuses_resume_before_any_physical_run(tmp_path, monkeypatch):
    path, plan, _ = frozen_plan(tmp_path)
    fingerprints = dict(plan["source_fingerprints"])
    fingerprints["experiments/probe_pilot.py"] = "changed"
    monkeypatch.setattr(pilot, "source_fingerprints", lambda: fingerprints)
    monkeypatch.setattr(probe_runner, "run_probe", lambda *a, **kw: pytest.fail("must not start a job"))
    with pytest.raises(ValueError, match="source changed"):
        pilot.run(path, max_runs=2)
    assert not (tmp_path / "runs.jsonl").exists()
    assert not (tmp_path / ".running.lock").exists()


def test_stage_a_generation_is_refused_on_mac_before_creating_files(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(probe_workloads, "generate_instance", lambda *a: pytest.fail("must not generate"))
    with pytest.raises(ValueError, match="Windows-only"):
        pilot.prepare("windows-stage-a", tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_stage_a_prepares_only_48_full_cells_with_independent_factors(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot.platform, "system", lambda: "Windows")
    from safe_pipe.research import probe_diagnostics
    monkeypatch.setattr(probe_diagnostics, "host_conditions", lambda _: {
        "free_disk_bytes": 100 * 2**30, "temp_free_disk_bytes": 100 * 2**30})
    recipes = []

    def fake_generate(path, recipe):
        recipes.append(recipe)
        return {"recipe": recipe}

    monkeypatch.setattr(probe_workloads, "generate_instance", fake_generate)
    monkeypatch.setattr(probe_workloads, "make_probe", lambda *a, **kw: pytest.fail("Stage A has no probes"))
    path = pilot.prepare("windows-stage-a", tmp_path / "stage-a")
    plan, _ = pilot.load_plan(path)
    assert len(plan["cells"]) == len({c["cell_id"] for c in plan["cells"]}) == 48
    assert plan["methods"] == ["full"]
    assert len(recipes) == 8 and {r["seed"] for r in recipes} == {911}
    assert {(r["hot_fraction"], r["partition_imbalance"]) for r in recipes} == {(0, 0), (.25, 0), (0, .6), (.25, .6)}
    assert all(r["generation_mode"] == "independent_columns_v1" for r in recipes)
    assert {c["run_config"]["memory_limit"] for c in plan["cells"]} == {"1000000000", "2000000000"}
    assert all(c["run_config"]["n_workers"] == 2 and c["run_config"]["threads_per_worker"] == 1 for c in plan["cells"])


def test_uncertain_physical_attempt_blocks_silent_retry(tmp_path, monkeypatch):
    path, plan, _ = frozen_plan(tmp_path)
    (tmp_path / "attempts").mkdir()
    marker = tmp_path / "attempts" / (plan["cells"][0]["cell_id"] + ".json")
    marker.write_text("{}")
    monkeypatch.setattr(probe_runner, "run_probe", lambda *a, **kw: pytest.fail("must not start"))
    with pytest.raises(ValueError, match="Unresolved physical attempt"):
        pilot.run(path, 1)
    assert marker.exists()
    assert not (tmp_path / ".running.lock").exists()
