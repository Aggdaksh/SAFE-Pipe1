"""Pure, unvalidated research decisions. Never executes jobs or loads a model.

The checked-in policy disables probe admission. Diagnostic classification is
separate from admission and does not constitute an online policy evaluation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def finite(value: Any, *, positive: bool = False) -> bool:
    return (type(value) in (int, float) and math.isfinite(value)
            and (value > 0 if positive else value >= 0))


def validate_policy(policy: dict) -> None:
    """Reject altered/malformed contracts rather than silently changing units."""
    if type(policy.get("admission_enabled")) is not bool or not policy.get("policy_id"):
        raise ValueError("Policy identity/admission flag missing")
    for key in ("n_workers", "threads_per_worker", "low_memory_bytes", "high_memory_bytes",
                "minimum_fact_rows", "maximum_fact_rows", "fact_files", "payload_columns",
                "join_dimension_rows", "numeric_column_bytes", "metadata_reserve_bytes",
                "metadata_lower_copy_factor", "metadata_upper_copy_factor", "probe_memory_floor_bytes",
                "probe_effective_memory_bytes", "probe_seed_base"):
        if type(policy.get(key)) is not int or policy[key] <= 0:
            raise ValueError(f"Invalid policy integer: {key}")
    for key in ("metadata_capacity_fraction", "probe_fraction", "probe_peak_ratio_cutoff"):
        if not finite(policy.get(key), positive=True) or policy[key] >= 1:
            raise ValueError(f"Invalid policy fraction: {key}")
    if (type(policy.get("maximum_probes_per_request")) is not int or policy["maximum_probes_per_request"] != 1 or policy["n_workers"] != 2
            or policy["threads_per_worker"] != 1 or policy["numeric_column_bytes"] != 8
            or policy["low_memory_bytes"] >= policy["high_memory_bytes"]
            or policy["minimum_fact_rows"] > policy["maximum_fact_rows"]
            or policy["metadata_lower_copy_factor"] > policy["metadata_upper_copy_factor"]
            or policy["probe_memory_floor_bytes"] >= policy["low_memory_bytes"]
            or policy.get("probe_sampling_method") != "uniform"
            or policy.get("probe_method_id") != "uniform_memory_f0250" or policy["probe_fraction"] != .25
            or not isinstance(policy.get("supported_families"), list)
            or any(not isinstance(family, str) for family in policy["supported_families"])
            or set(policy["supported_families"]) != {"groupby", "skewed_join"}
            or any(not isinstance(policy.get(k), str) or not policy[k] for k in ("low_config_id", "high_config_id"))
            or policy["low_config_id"] == policy["high_config_id"]):
        raise ValueError("Unsupported/inconsistent research policy contract")
    mapped = round(policy["probe_memory_floor_bytes"] + policy["probe_fraction"] *
                   (policy["low_memory_bytes"] - policy["probe_memory_floor_bytes"]))
    if mapped != policy["probe_effective_memory_bytes"]:
        raise ValueError("Probe cap does not match the frozen mapping")
    objective = policy.get("objective", {})
    for key, expected in {"time_weight": .5, "threads_weight": .25, "memory_weight": .25,
                          "normalization_threads": 4, "normalization_memory_bytes": 4_000_000_000}.items():
        if not finite(objective.get(key), positive=True) or objective[key] != expected:
            raise ValueError("Economic estimates require the declared balanced objective units")


@dataclass(frozen=True)
class Workload:
    """Pre-decision row/schema metadata; never includes full-job outcomes."""
    instance_id: str
    dataset_sha256: str
    family: str
    fact_rows: int
    dimension_rows: int
    payload_columns: int
    fact_partition_rows: tuple[int, ...]


@dataclass(frozen=True)
class EconomicCase:
    """External development estimates, not guarantees or target-run labels."""
    expected_saving_proxy: float
    expected_profile_proxy: float
    expected_profile_wall_seconds: float
    profile_wall_budget_seconds: float
    evidence_source: str
    incremental_information_supported: bool
    uses_target_full_outcome: bool = False


def probe_sample_seed(workload: Workload, policy: dict) -> int:
    """Same deterministic per-instance quarter-sample identity as Stage B."""
    return int(fingerprint([policy["probe_seed_base"], workload.instance_id, policy["probe_method_id"]])[:8], 16)


def unsupported(workload: Workload, policy: dict) -> str | None:
    if (not isinstance(workload.instance_id, str) or not workload.instance_id
            or not isinstance(workload.dataset_sha256, str) or len(workload.dataset_sha256) != 64
            or any(c not in "0123456789abcdef" for c in workload.dataset_sha256)):
        return "missing_dataset_identity"
    if workload.family not in policy["supported_families"]:
        return "unsupported_family"
    if (type(workload.fact_rows) is not int or not policy["minimum_fact_rows"] <= workload.fact_rows <= policy["maximum_fact_rows"]
            or type(workload.payload_columns) is not int or workload.payload_columns != policy["payload_columns"]
            or type(workload.dimension_rows) is not int or workload.dimension_rows !=
                (policy["join_dimension_rows"] if workload.family == "skewed_join" else 0)
            or not isinstance(workload.fact_partition_rows, tuple)
            or len(workload.fact_partition_rows) != policy["fact_files"]
            or any(type(n) is not int or n <= 0 for n in workload.fact_partition_rows)
            or sum(workload.fact_partition_rows) != workload.fact_rows):
        return "unsupported_or_inconsistent_shape"
    return None


def metadata_decision(workload: Workload, policy: dict) -> dict:
    validate_policy(policy)
    reason = unsupported(workload, policy)
    if reason:
        return {"action": "abstain", "config_id": None, "reason": reason}
    width = policy["numeric_column_bytes"] * (1 + workload.payload_columns)
    total = workload.fact_rows * width + workload.dimension_rows * 2 * policy["numeric_column_bytes"]
    largest = max(workload.fact_partition_rows) * width
    common = policy["metadata_reserve_bytes"] + total / policy["n_workers"]
    lower = common + policy["metadata_lower_copy_factor"] * largest
    upper = common + policy["metadata_upper_copy_factor"] * largest
    low_budget = policy["metadata_capacity_fraction"] * policy["low_memory_bytes"]
    high_budget = policy["metadata_capacity_fraction"] * policy["high_memory_bytes"]
    config = policy["low_config_id"] if upper <= low_budget else policy["high_config_id"] if upper <= high_budget else None
    return {"action": "select" if config else "abstain", "config_id": config,
            "reason": "metadata_scenario_choice" if config else "metadata_exceeds_declared_caps",
            "dense_total_input_bytes": total, "dense_largest_fact_partition_bytes": largest,
            "metadata_lower_scenario_bytes": lower, "metadata_upper_scenario_bytes": upper,
            "ambiguous_at_low_cap": lower <= low_budget < upper,
            "interpretation": "Handset input-size scenarios, not statistical bounds or a safety guarantee."}


def plan_request(workload: Workload, policy: dict, request_id: str, economics: EconomicCase | None = None) -> dict:
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("A request identity is required")
    base = metadata_decision(workload, policy)
    identity = {"request_id": request_id, "policy_sha256": fingerprint(policy),
                "workload_sha256": fingerprint(asdict(workload)), "dataset_sha256": workload.dataset_sha256}
    decision = {**base, **identity, "probe_count": 0}
    if base["action"] == "abstain" or not base.get("ambiguous_at_low_cap"):
        return decision
    if not policy["admission_enabled"]:
        return {**decision, "reason": "research_feasibility_gate_closed"}
    if economics is None:
        return {**decision, "reason": "no_economic_case"}
    if (not isinstance(economics.evidence_source, str) or not economics.evidence_source.strip()
            or economics.incremental_information_supported is not True
            or economics.uses_target_full_outcome is not False):
        return {**decision, "reason": "unsupported_or_leaking_economic_case"}
    if not all(finite(getattr(economics, key), positive=True) for key in
               ("expected_saving_proxy", "expected_profile_proxy", "expected_profile_wall_seconds", "profile_wall_budget_seconds")):
        return {**decision, "reason": "invalid_economic_estimates"}
    if economics.expected_saving_proxy <= economics.expected_profile_proxy:
        return {**decision, "reason": "estimated_profile_cost_not_recovered"}
    if economics.expected_profile_wall_seconds > economics.profile_wall_budget_seconds:
        return {**decision, "reason": "estimated_profile_wall_budget_exceeded"}
    return {**decision, "action": "probe", "config_id": None, "fallback_config_id": base["config_id"],
            "reason": "one_probe_requested_under_revised_research_policy", "probe_count": 1,
            "probe_contract": {"fraction": policy["probe_fraction"], "effective_memory_bytes": policy["probe_effective_memory_bytes"],
                               "sampling_method": policy["probe_sampling_method"], "sample_seed": probe_sample_seed(workload, policy),
                               "fact_rows": round(workload.fact_rows * policy["probe_fraction"]), "dimension_rows": workload.dimension_rows,
                               "n_workers": policy["n_workers"], "threads_per_worker": policy["threads_per_worker"],
                               "wall_budget_seconds": economics.profile_wall_budget_seconds},
            "economic_case": asdict(economics)}


def observed_memory(worker: dict) -> dict:
    """Keep both sources; even their maximum is only a largest observed value."""
    peak = worker.get("peak_rss_bytes")
    records = worker.get("worker_evidence")
    available = isinstance(records, list) and all(isinstance(e, dict) for e in records)
    events = [e.get("rss_bytes") for e in records if e.get("kind") == "nanny_memory_restart"] if available else []
    valid = [v for v in [peak, *events] if finite(v, positive=True)]
    count = worker.get("worker_nanny_memory_termination_count")
    event_termination = available and any(e.get("kind") in {"nanny_memory_restart", "nanny_memory_termination"} for e in records)
    termination = True if event_termination or (type(count) is int and count > 0) else False if type(count) is int and count == 0 and available else None
    return {"sampled_peak_bytes": peak, "nanny_event_rss_bytes": events, "event_evidence_available": available,
            "largest_observed_rss_bytes": max(valid) if valid else None,
            "memory_termination_observed": termination,
            "exact_peak_known": False, "automatic_regression_target": False}


def probe_evidence_choice(workload: Workload, policy: dict, observation: dict) -> dict:
    """Counterfactual single-observation classifier, separate from admission.

    Observation quality must come from retained telemetry/diagnostic/condition
    checks. Failed/unknown probes cannot lower the metadata recommendation.
    """
    base = metadata_decision(workload, policy)
    if base["action"] == "abstain":
        return base
    if (observation.get("dataset_sha256") != workload.dataset_sha256
            or observation.get("workload_sha256") != fingerprint(asdict(workload))
            or observation.get("fraction") != policy["probe_fraction"]
            or observation.get("sampling_method") != policy["probe_sampling_method"]
            or observation.get("sample_seed") != probe_sample_seed(workload, policy)
            or observation.get("fact_rows") != round(workload.fact_rows * policy["probe_fraction"])
            or observation.get("dimension_rows") != workload.dimension_rows
            or not isinstance(observation.get("sample_dataset_sha256"), str)
            or len(observation["sample_dataset_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in observation["sample_dataset_sha256"])
            or observation.get("effective_memory_bytes") != policy["probe_effective_memory_bytes"]
            or observation.get("n_workers") != policy["n_workers"]
            or observation.get("threads_per_worker") != policy["threads_per_worker"]):
        raise ValueError("Probe observation is not bound to this workload/sample/configuration")
    fallback = {**base, "reason": "unknown_or_warning_probe_keeps_metadata_choice", "probe_count": 1}
    workers = observation.get("workers")
    if (observation.get("quality_complete") is not True or observation.get("status") != "success"
            or not finite(observation.get("result_value"))
            or not isinstance(workers, list) or len(workers) != policy["n_workers"]
            or type(observation.get("restarts")) is not int or observation["restarts"] != 0):
        return fallback
    ratios = []
    for worker in workers:
        if (not isinstance(worker, dict) or not isinstance(worker.get("worker_evidence"), list)
                or any(not isinstance(e, dict) for e in worker["worker_evidence"])
                or worker.get("effective_memory_limit_bytes") != policy["probe_effective_memory_bytes"]
                or worker.get("worker_origin") != "initial"
                or worker.get("missing_worker_fields") != []
                or not finite(worker.get("samples"), positive=True)
                or not finite(worker.get("baseline_rss_bytes"), positive=True)
                or not finite(worker.get("peak_rss_bytes"), positive=True)
                or worker["baseline_rss_bytes"] > worker["peak_rss_bytes"]
                or any(type(worker.get(k)) is not int or worker[k] != 0 for k in
                       ("sampling_errors", "paused_samples", "peak_spilled_disk_bytes", "worker_nanny_memory_termination_count"))):
            return fallback
        if any(e.get("kind") in {"nanny_memory_restart", "nanny_memory_termination", "worker_exit_before_cleanup"}
               for e in worker.get("worker_evidence", [])):
            return fallback
        ratios.append(worker["peak_rss_bytes"] / worker["effective_memory_limit_bytes"])
    ratio = max(ratios)
    below = ratio < policy["probe_peak_ratio_cutoff"] and not math.isclose(ratio, policy["probe_peak_ratio_cutoff"], rel_tol=1e-12)
    return {**base, "config_id": policy["low_config_id"] if below else policy["high_config_id"],
            "reason": "uncalibrated_single_probe_threshold", "probe_count": 1, "peak_ratio": ratio}


def finish_request(workload: Workload, policy: dict, pending: dict, observations: list[dict]) -> dict:
    """One requested probe produces a terminal decision; never requests another."""
    validate_policy(policy)
    if (not isinstance(pending, dict) or not isinstance(observations, list) or len(observations) != 1
            or not isinstance(observations[0], dict) or pending.get("action") != "probe" or pending.get("probe_count") != 1
            or pending.get("policy_sha256") != fingerprint(policy)
            or pending.get("workload_sha256") != fingerprint(asdict(workload))
            or pending.get("dataset_sha256") != workload.dataset_sha256
            or observations[0].get("request_id") != pending.get("request_id")):
        raise ValueError("Expected exactly one bound observation for a pending request")
    observation = observations[0]
    # Reconstruct admission so a hand-written/modified pending decision cannot
    # silently bypass the policy gate or change its fallback/budget.
    try:
        economics = EconomicCase(**pending.get("economic_case", {}))
    except (TypeError, ValueError) as exc:
        raise ValueError("Pending economic case missing or malformed") from exc
    if pending != plan_request(workload, policy, pending["request_id"], economics):
        raise ValueError("Pending decision differs from the policy's admission contract")
    result = probe_evidence_choice(workload, policy, observation)
    paid = observation.get("profile_wall_seconds")
    if not finite(paid, positive=True) or paid > pending["probe_contract"]["wall_budget_seconds"]:
        result = {**metadata_decision(workload, policy), "reason": "profile_budget_exceeded_or_unknown", "probe_count": 1}
    return {**result, "request_id": pending["request_id"], "policy_sha256": pending["policy_sha256"],
            "terminal": True, "incurred_profile_wall_seconds": paid,
            "budget_note": "Decision check only. An execution supervisor must enforce wall limits; no runner is implemented here."}
