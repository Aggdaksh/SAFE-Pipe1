"""Windows handoff tests. Fixtures are synthetic records, not physical evidence."""
import json
import csv
from pathlib import Path

import pytest

from experiments import probe_pilot as pilot
from experiments import probe_stage_b as stage_b
from safe_pipe.research import probe_fidelity as fidelity


def outcome(cell, **changes):
    row = {**cell, "config": cell["run_config"], "status": "success", "result_value": 1.0,
           "timings": {"execution_seconds": .5, "total_seconds": 1.0, "end_to_end_seconds": 1.1},
           "owned_descendants_alive_after_cleanup": 0,
           "conditions": {"flags": [], "samples": 2},
           "diagnostics": {"retained": True, "log_truncated": False, "log_write_errors": 0,
                           "malformed_log_lines": 0, "nanny_memory_termination_count": 0,
                           "failure_category": "completed"},
           "telemetry": {"samples_total": 10, "missing_initial_worker_records": 0,
                         "workers": [{"sampling_errors": 0}, {"sampling_errors": 0}],
                         "spilled_disk_peak_bytes_sum": 0, "paused_samples": 0,
                         "observed_restarts_lower_bound": 0}}
    row.update(changes)
    return row


@pytest.fixture
def design():
    spec = stage_b.specification()
    parent = json.loads((stage_b.ROOT / spec["reference_export"]).read_text())
    descriptors = {}
    for recipe in parent["recipes"]:
        descriptors[recipe["instance_id"]] = {"dataset_sha256": "full-" + recipe["instance_id"],
            "fact_rows": recipe["n_rows"], "dimension_rows": recipe["n_keys"] if recipe["family"] == "skewed_join" else 0,
            "largest_file_row_share": .65 if recipe["partition_imbalance"] else .125}
    reference = {"plan_sha256": spec["reference_plan_sha256"], "frozen_environment": {},
                 "datasets": descriptors, "configs": parent["configs"],
                 "outcomes": [fidelity.compact_outcome(outcome(c)) for c in parent["cells"]]}
    datasets, fingerprints, samples, manifests = {}, {}, {}, {}
    for instance, descriptor in descriptors.items():
        datasets[instance], fingerprints[instance], samples[instance] = {}, {}, {}
        for method in spec["methods"]:
            key = method["id"]
            relative = f"datasets/{instance}/{key}"
            manifest = {"sha256": relative, "parent_sha256": descriptor["dataset_sha256"],
                        "parent_instance_id": instance, "method": "uniform", "fraction": method["fraction"],
                        "sampling": {"seed": stage_b.sample_seed(spec, instance, key)},
                        "n_rows": round(descriptor["fact_rows"] * method["fraction"]),
                        "n_right_rows": descriptor["dimension_rows"], "preparation_seconds": 2.0}
            datasets[instance][key] = relative
            manifests[relative] = manifest
            fingerprints[instance][key] = pilot.canonical_hash(manifest)
            samples[instance][key] = {"dataset_sha256": relative, "parent_sha256": descriptor["dataset_sha256"],
                "fraction": method["fraction"], "sample_seed": manifest["sampling"]["seed"],
                "fact_rows": manifest["n_rows"], "dimension_rows": manifest["n_right_rows"], "preparation_seconds": 2.0}
    plan = {"schema_version": pilot.SCHEMA, "preset": stage_b.PRESET, "role": spec["role"],
            "protocol": spec, "protocol_sha256": pilot.canonical_hash(spec),
            "reference": reference, "reference_sha256": pilot.canonical_hash(reference),
            "configs": parent["configs"], "recipes": parent["recipes"], "frozen_environment": {},
            "datasets": datasets, "dataset_fingerprints": fingerprints, "sample_metadata": samples,
            "repeats": 3, "methods": [m["id"] for m in spec["methods"]], "timeout_seconds": 180,
            "cells": stage_b.build_cells(parent, spec), "source_fingerprints": pilot.source_fingerprints()}
    return parent, plan, manifests


def test_stage_b_fixed_budget_and_memory_mapping(design):
    _, plan, _ = design
    stage_b.validate_plan(plan)
    assert len(plan["cells"]) == len({c["cell_id"] for c in plan["cells"]}) == 96
    assert {c["run_config"]["memory_limit"] for c in plan["cells"]} == {
        "594762048", "652653184", "719762048", "902653184"}
    assert all(c["method"] != "full" for c in plan["cells"])
    assert len({(c["instance_id"], c["method"], c["sample_seed"]) for c in plan["cells"]}) == 16
    assert [c["repeat_id"] for c in plan["cells"]] == [1] * 32 + [2] * 32 + [3] * 32


@pytest.mark.parametrize("mutation", ["fraction", "order", "reference", "sample", "timeout"])
def test_frozen_contract_rejects_mutation(design, mutation):
    _, plan, _ = design
    if mutation == "fraction":
        plan["cells"][0]["fraction"] = .5
    elif mutation == "order":
        plan["cells"].reverse()
    elif mutation == "reference":
        plan["reference"]["outcomes"].pop()
    elif mutation == "timeout":
        plan["timeout_seconds"] = 10
    else:
        next(iter(plan["sample_metadata"].values()))[plan["methods"][0]]["dimension_rows"] += 1
    with pytest.raises(ValueError):
        stage_b.validate_plan(plan)


def test_prepare_refuses_mac_before_data_or_output(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot.platform, "system", lambda: "Darwin")
    with pytest.raises(ValueError, match="Windows-only"):
        stage_b.prepare(tmp_path / "absent" / "plan.json", tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_preparation_reuses_reference_and_creates_only_16_samples(design, tmp_path, monkeypatch):
    from safe_pipe.research import probe_diagnostics, probe_runner, probe_workloads
    parent, plan, manifests = design
    monkeypatch.setattr(pilot.platform, "system", lambda: "Windows")
    monkeypatch.setattr(probe_runner, "_environment", lambda: {})
    monkeypatch.setattr(probe_diagnostics, "host_conditions", lambda _: {
        "battery_present": False, "free_disk_bytes": 100 * 2**30, "temp_free_disk_bytes": 100 * 2**30})
    parent["frozen_environment"] = {}
    sources = {i: tmp_path / "stage-a" / "datasets" / i for i in plan["datasets"]}
    calls = []
    monkeypatch.setattr(stage_b, "reference_bundle", lambda *a: (parent, plan["reference"], sources))
    monkeypatch.setattr(probe_workloads, "generate_instance", lambda *a, **kw: pytest.fail("must not regenerate Stage A"))

    def sample(source, dest, fraction, method, seed):
        relative = dest.relative_to(tmp_path / "stage-b").as_posix()
        manifest = manifests[relative]
        assert source == sources[manifest["parent_instance_id"]]
        assert fraction == manifest["fraction"] and method == "uniform" and seed == manifest["sampling"]["seed"]
        calls.append(relative)
        return manifest

    monkeypatch.setattr(probe_workloads, "make_probe", sample)
    path = stage_b.prepare(tmp_path / "stage-a" / "plan.json", tmp_path / "stage-b")
    actual, _ = pilot.load_plan(path)
    assert len(calls) == len(set(calls)) == 16
    assert len(actual["cells"]) == 96 and actual["reference"] == plan["reference"]
    assert not (tmp_path / "stage-a").exists()
    assert not (tmp_path / "stage-b" / "runs.jsonl").exists()


def test_changed_collector_rejected_before_sampling(monkeypatch):
    from safe_pipe.research import probe_runner
    spec = stage_b.specification()
    path = stage_b.ROOT / spec["reference_export"]
    parent = json.loads(path.read_text())
    monkeypatch.setattr(probe_runner, "_environment", lambda: parent["frozen_environment"])
    monkeypatch.setattr(stage_b, "file_hash", lambda _: "changed")
    with pytest.raises(ValueError, match="execution semantics changed"):
        stage_b.reference_bundle(path, spec)


def test_raw_diagnostic_mutation_and_path_escape_are_rejected(tmp_path):
    path = tmp_path / "diagnostics" / "run"
    path.mkdir(parents=True)
    (path / "log.txt").write_text("original")
    row = {"diagnostics": {"retained": True, "directory": "diagnostics/run", "files": [
        {"file": "log.txt", "bytes": 8, "sha256": stage_b.file_hash(path / "log.txt")}]}}
    assert stage_b.verify_diagnostics(tmp_path, [row]) == 1
    (path / "log.txt").write_text("modified")
    with pytest.raises(ValueError, match="saved hash"):
        stage_b.verify_diagnostics(tmp_path, [row])
    with pytest.raises(ValueError, match="escapes"):
        stage_b.within(tmp_path, "../unrelated")


def test_failed_probe_is_persisted_and_not_retried(design, tmp_path, monkeypatch):
    from safe_pipe.research import probe_diagnostics, probe_runner, probe_workloads
    _, plan, manifests = design
    monkeypatch.setattr(pilot.platform, "system", lambda: "Windows")
    monkeypatch.setattr(probe_runner, "validate_host_budget", lambda _: {})
    monkeypatch.setattr(probe_workloads, "load_manifest", lambda path, **kw: manifests[Path(path).relative_to(tmp_path).as_posix()])
    monkeypatch.setattr(probe_diagnostics, "host_conditions", lambda _: {
        "battery_present": False, "free_disk_bytes": 100 * 2**30, "temp_free_disk_bytes": 100 * 2**30})
    calls = []

    def physical_stub(dataset, config, **kwargs):
        cell = plan["cells"][len(calls)]
        calls.append(cell["cell_id"])
        return outcome(cell, status="execution_error")

    monkeypatch.setattr(probe_runner, "run_probe", physical_stub)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    pilot.run(path, 1)
    pilot.run(path, 1)
    rows = pilot.load_records(tmp_path / "runs.jsonl", pilot.canonical_hash(plan))
    assert calls == [c["cell_id"] for c in plan["cells"][:2]]
    assert len(rows) == 2 and all(r["status"] == "execution_error" for r in rows)
    assert not list((tmp_path / "attempts").glob("*.json"))


def test_quiet_warning_unknown_are_distinct(design):
    _, plan, _ = design
    row = outcome(plan["cells"][0])
    assert fidelity.compact_outcome(row)["signal"] == "quiet"
    row["telemetry"]["spilled_disk_peak_bytes_sum"] = 1
    assert fidelity.compact_outcome(row)["signal"] == "warning"
    row["conditions"]["flags"] = ["mains_lost_or_unknown"]
    assert fidelity.compact_outcome(row)["signal"] == "unknown"
    row = outcome(plan["cells"][0])
    row["telemetry"]["spilled_disk_peak_bytes_sum"] = None
    assert fidelity.compact_outcome(row)["signal"] == "unknown"
    row = outcome(plan["cells"][0], status="timeout")
    assert fidelity.compact_outcome(row)["signal"] == "warning"


def test_mixed_full_outcomes_are_not_erased_by_successful_probes(design):
    _, plan, _ = design
    full = plan["reference"]["outcomes"][0]
    full.update(status="execution_error", signal="warning", warnings=["execution_error"])
    result = fidelity.summarize_stage_b(plan, [outcome(c) for c in plan["cells"]])
    groups = [g for g in result["fidelity_groups"] if g["instance_id"] == full["instance_id"]
              and g["target_config_id"] == full["target_config_id"]]
    assert len(groups) == 2
    assert all(g["full"]["completion"] == "mixed_completion" for g in groups)
    assert all(g["false_reassurance_candidate"] is True for g in groups)
    assert all(g["full"]["statuses"] == {"execution_error": 1, "success": 2} for g in groups)


def test_probe_only_warnings_and_paid_fallback_keep_all_costs(design):
    _, plan, _ = design
    rows = [outcome(c) for c in plan["cells"]]
    for row in rows:
        row["telemetry"]["paused_samples"] = 1
    result = fidelity.summarize_stage_b(plan, rows)
    assert result["comparison_counts"]["unnecessary_warning_candidate_groups"] == 32
    replay = next(r for r in result["baseline_replays"] if r["policy"] == plan["methods"][0])
    assert replay["fallback_used"] and replay["selected_config"] == "w2_t1_2g"
    assert replay["profiling_seconds"] == pytest.approx(2 + 6 * 1.1)
    assert replay["constructed_successful_request_seconds"] == pytest.approx(2 + 6 * 1.1 + 1.1)
    assert replay["probe_configured_gb_seconds_proxy"] > 0


def test_partial_or_unknown_probes_do_not_become_complete_replay(design):
    _, plan, _ = design
    rows = [outcome(c) for c in plan["cells"]]
    rows[0]["conditions"]["flags"] = ["unknown_power"]
    result = fidelity.summarize_stage_b(plan, rows[:-1])
    assert len(result["missing_cells"]) == 1
    assert result["comparison_counts"]["eligible_groups"] < 32
    assert any(not r["evaluable"] for r in result["baseline_replays"])
    assert all(r["observed_profiling_seconds_lower_bound"] >= 2 for r in result["baseline_replays"] if not r["evaluable"])


@pytest.mark.parametrize("field", ["fraction", "sample_seed", "config"])
def test_analysis_rejects_changed_measurement_identity(design, field):
    _, plan, _ = design
    row = outcome(plan["cells"][0])
    row[field] = None
    with pytest.raises(ValueError, match="identity|configuration"):
        fidelity.summarize_stage_b(plan, [row])


def test_same_sample_result_mismatch_is_reported(design):
    _, plan, _ = design
    rows = [outcome(c) for c in plan["cells"]]
    rows[0]["result_value"] = 2.0
    result = fidelity.summarize_stage_b(plan, rows)
    assert result["inconsistent_successful_results"] == [{"instance_id": rows[0]["instance_id"], "method": rows[0]["method"]}]
    affected = next(r for r in result["baseline_replays"] if r["instance_id"] == rows[0]["instance_id"] and r["policy"] == rows[0]["method"])
    assert affected["evaluable"] is False
    assert "Scalar inconsistencies" in fidelity.markdown_stage_b(result)


def test_partial_export_retains_reference_fraction_quality_and_rejects_stale_audit(design, tmp_path):
    from experiments import export_probe_evidence
    _, plan, manifests = design
    cell = plan["cells"][0]
    relative = plan["datasets"][cell["instance_id"]][cell["method"]]
    row = outcome(cell)
    row.update(run_id="fixture", plan_sha256=pilot.canonical_hash(plan), environment={},
               host_budget={"physical_bytes": 32 * 2**30},
               dataset={**manifests[relative], "compressed_bytes": 1, "logical_bytes": 1})
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    (tmp_path / "runs.jsonl").write_text(json.dumps(row) + "\n")
    export_probe_evidence.export(path, tmp_path / "export")
    with (tmp_path / "export" / "measurements.csv").open() as stream:
        measured = list(csv.DictReader(stream))[0]
    assert float(measured["fraction"]) == cell["fraction"]
    assert measured["fidelity_signal"] == "quiet"
    summary = json.loads((tmp_path / "export" / "summary.json").read_text())
    assert summary["reference_plan_sha256"] == plan["reference"]["plan_sha256"]
    assert summary["recorded_cells"] == 1 and len(summary["missing_cells"]) == 95
    (tmp_path / "completion_audit.json").write_text(json.dumps({
        "plan_sha256": pilot.canonical_hash(plan), "recorded": 1, "runs_sha256": "stale"}))
    with pytest.raises(ValueError, match="stale"):
        export_probe_evidence.export(path, tmp_path / "stale-export")
