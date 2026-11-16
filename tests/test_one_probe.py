"""Synthetic decision-contract checks. Execute on Windows per project policy."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from safe_pipe.research.one_probe import (
    EconomicCase, Workload, fingerprint, finish_request, metadata_decision,
    observed_memory, plan_request, probe_evidence_choice, probe_sample_seed, validate_policy,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy():
    return json.loads((ROOT / "configs/research_one_probe_v1.json").read_text())


@pytest.fixture
def workload():
    return Workload("example", "a" * 64, "groupby", 2_000_000, 0, 16, (1_300_000, *([100_000] * 7)))


@pytest.fixture
def economics():
    # Artificial unit-test estimates, not a claim supported by the real data.
    return EconomicCase(10.0, 4.0, 6.0, 8.0, "synthetic-unit-test-only", True)


@pytest.fixture
def observation(workload, policy):
    worker = {"worker_origin": "initial", "effective_memory_limit_bytes": policy["probe_effective_memory_bytes"],
        "missing_worker_fields": [], "samples": 100, "sampling_errors": 0, "paused_samples": 0,
        "baseline_rss_bytes": 75_000_000, "peak_rss_bytes": 250_000_000,
        "peak_spilled_disk_bytes": 0, "worker_nanny_memory_termination_count": 0, "worker_evidence": []}
    return {"request_id": "r1", "dataset_sha256": workload.dataset_sha256,
        "workload_sha256": fingerprint(asdict(workload)), "fraction": .25,
        "sample_dataset_sha256": "b" * 64, "sampling_method": "uniform", "sample_seed": probe_sample_seed(workload, policy),
        "fact_rows": 500_000, "dimension_rows": 0,
        "effective_memory_bytes": policy["probe_effective_memory_bytes"], "n_workers": 2, "threads_per_worker": 1,
        "quality_complete": True, "status": "success", "result_value": 2.0,
        "restarts": 0, "workers": [deepcopy(worker), deepcopy(worker)], "profile_wall_seconds": 6.0}


def test_checked_in_policy_never_admits_even_with_optimistic_estimates(workload, policy, economics):
    assert policy["admission_enabled"] is False
    decision = plan_request(workload, policy, "r1", economics)
    assert decision["action"] == "select" and decision["config_id"] == "w2_t1_2g"
    assert decision["reason"] == "research_feasibility_gate_closed" and decision["probe_count"] == 0


def test_absolute_size_matters_at_same_partition_share(workload, policy):
    small = replace(workload, fact_rows=1_000_000, fact_partition_rows=(650_000, *([50_000] * 7)))
    large = replace(workload, fact_rows=3_000_000, fact_partition_rows=(1_950_000, *([150_000] * 7)))
    assert metadata_decision(small, policy)["config_id"] == "w2_t1_1g"
    assert metadata_decision(large, policy)["config_id"] == "w2_t1_2g"


def test_balanced_metadata_skips_probe_even_in_synthetic_enabled_policy(workload, policy, economics):
    policy["admission_enabled"] = True
    balanced = replace(workload, fact_partition_rows=(250_000,) * 8)
    decision = plan_request(balanced, policy, "r1", economics)
    assert decision["action"] == "select" and decision["probe_count"] == 0


@pytest.mark.parametrize("changes", [
    {"family": "other"}, {"fact_rows": 4_000_000}, {"dimension_rows": 1},
    {"payload_columns": 32}, {"dataset_sha256": "missing"},
    {"fact_partition_rows": (1,) * 8}, {"fact_rows": True},
])
def test_unknown_or_inconsistent_workload_abstains(workload, policy, changes):
    assert plan_request(replace(workload, **changes), policy, "r1")["action"] == "abstain"


@pytest.mark.parametrize("changes", [
    {"expected_saving_proxy": 4.0}, {"expected_profile_proxy": float("nan")},
    {"expected_profile_proxy": 0.0}, {"profile_wall_budget_seconds": 5.0},
    {"incremental_information_supported": False}, {"uses_target_full_outcome": True},
    {"evidence_source": ""},
])
def test_invalid_unprofitable_or_leaking_case_cannot_admit(workload, policy, economics, changes):
    policy["admission_enabled"] = True
    decision = plan_request(workload, policy, "r1", replace(economics, **changes))
    assert decision["action"] == "select" and decision["probe_count"] == 0


def test_synthetic_one_probe_transition_is_terminal(workload, policy, economics, observation):
    policy["admission_enabled"] = True
    pending = plan_request(workload, policy, "r1", economics)
    assert pending["action"] == "probe" and pending["probe_count"] == 1
    final = finish_request(workload, policy, pending, [observation])
    assert final["terminal"] and final["action"] == "select" and final["config_id"] == "w2_t1_1g"
    with pytest.raises(ValueError):
        finish_request(workload, policy, final, [observation])


def test_repeated_unbound_or_modified_pending_is_rejected(workload, policy, economics, observation):
    policy["admission_enabled"] = True
    pending = plan_request(workload, policy, "r1", economics)
    for observations in ([], [observation, observation], [{**observation, "request_id": "other"}]):
        with pytest.raises(ValueError):
            finish_request(workload, policy, pending, observations)
    altered = deepcopy(pending)
    altered["fallback_config_id"] = "w2_t1_1g"
    with pytest.raises(ValueError):
        finish_request(workload, policy, altered, [observation])


def test_budget_overrun_retains_cost_and_does_not_lower_cap(workload, policy, economics, observation):
    policy["admission_enabled"] = True
    pending = plan_request(workload, policy, "r1", economics)
    observation["profile_wall_seconds"] = 9.0
    result = finish_request(workload, policy, pending, [observation])
    assert result["config_id"] == "w2_t1_2g" and result["incurred_profile_wall_seconds"] == 9.0


@pytest.mark.parametrize("field,value", [
    ("peak_rss_bytes", None), ("sampling_errors", 1), ("peak_spilled_disk_bytes", 1),
    ("paused_samples", 1), ("worker_nanny_memory_termination_count", 1),
    ("missing_worker_fields", ["peak_rss_bytes"]), ("worker_evidence", None),
])
def test_bad_probe_measurement_cannot_enable_low_override(workload, policy, observation, field, value):
    observation["workers"][0][field] = value
    assert probe_evidence_choice(workload, policy, observation)["config_id"] == "w2_t1_2g"


@pytest.mark.parametrize("field,value", [("status", "execution_error"), ("restarts", 1), ("quality_complete", False), ("result_value", float("nan"))])
def test_bad_run_quality_cannot_enable_low_override(workload, policy, observation, field, value):
    observation[field] = value
    assert probe_evidence_choice(workload, policy, observation)["config_id"] == "w2_t1_2g"


def test_termination_event_is_not_hidden_by_low_saved_peak(workload, policy, observation):
    observation["workers"][0]["worker_evidence"] = [{"kind": "nanny_memory_restart", "rss_bytes": 700_000_000}]
    assert probe_evidence_choice(workload, policy, observation)["config_id"] == "w2_t1_2g"
    evidence = observed_memory({**observation["workers"][0], "worker_nanny_memory_termination_count": 1})
    assert evidence["sampled_peak_bytes"] == 250_000_000 and evidence["largest_observed_rss_bytes"] == 700_000_000
    assert evidence["memory_termination_observed"] and not evidence["exact_peak_known"]
    assert not evidence["automatic_regression_target"]


def test_threshold_boundary_and_configuration_binding(workload, policy, observation):
    for w in observation["workers"]:
        w["peak_rss_bytes"] = policy["probe_peak_ratio_cutoff"] * policy["probe_effective_memory_bytes"]
    assert probe_evidence_choice(workload, policy, observation)["config_id"] == "w2_t1_2g"
    observation["fraction"] = .125
    with pytest.raises(ValueError):
        probe_evidence_choice(workload, policy, observation)


def test_invalid_policy_mapping_is_rejected(policy):
    policy["probe_effective_memory_bytes"] += 1
    with pytest.raises(ValueError):
        validate_policy(policy)


def test_frozen_sample_seed_and_wrong_sample_rejected(workload, policy, observation):
    archived = replace(workload, instance_id="groupby-2000000-balanced-s911")
    assert probe_sample_seed(archived, policy) == 4142278465
    for field, value in (("sample_seed", 1), ("sampling_method", "partition_tail"), ("fact_rows", 250_000), ("sample_dataset_sha256", None)):
        with pytest.raises(ValueError):
            probe_evidence_choice(workload, policy, {**observation, field: value})


def test_missing_event_evidence_remains_unknown():
    result = observed_memory({"peak_rss_bytes": None, "worker_evidence": None})
    assert result["largest_observed_rss_bytes"] is None and result["memory_termination_observed"] is None
    assert not result["event_evidence_available"] and not result["automatic_regression_target"]


def test_windows_handoff_rejects_mac_before_creating_files(monkeypatch, tmp_path):
    from experiments.verify_one_probe import verify
    monkeypatch.setattr("experiments.verify_one_probe.platform.system", lambda: "Darwin")
    destination = tmp_path / "report"
    with pytest.raises(ValueError, match="Windows"):
        verify(destination)
    assert not destination.exists()


def test_windows_handoff_rejects_outputs_outside_reports(monkeypatch, tmp_path):
    from experiments.verify_one_probe import verify
    monkeypatch.setattr("experiments.verify_one_probe.platform.system", lambda: "Windows")
    destination = tmp_path / "report"
    with pytest.raises(ValueError, match="reports"):
        verify(destination)
    assert not destination.exists()
