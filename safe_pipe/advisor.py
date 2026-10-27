"""Explainable constrained configuration selection using frozen runtime artifacts.

This is a policy layer, not a new trained model or a safety guarantee. Inference
targets the original Windows benchmark environment, not the calling machine.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from safe_pipe.cost import resource_score
from safe_pipe.grid import load_grid
from safe_pipe.memory import dask_memory_bytes
from safe_pipe.policy import candidate_frame
from safe_pipe.schemas import DatasetManifest, WorkloadFamily, WorkloadSpec
from safe_pipe.workloads.generate import workload_from_manifest


class Preferences(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")
    mode: Literal["resource", "fastest", "balanced"] = "balanced"
    thread_weight: float = Field(default=0.5, ge=0, le=1)
    deadline_reserve: float = Field(default=0.0, ge=0, lt=1)
    max_threads: int | None = Field(default=None, gt=0)
    max_memory_gb: float | None = Field(default=None, gt=0)
    thread_reference: int = Field(default=4, gt=0)
    memory_reference_bytes: int = Field(default=4_000_000_000, gt=0)


class Predictor(Protocol):
    def predict(self, frame): ...


def frozen_profiles(index: Path) -> dict[str, WorkloadSpec]:
    """Preserve historical feature values, including the legacy skew tags."""
    manifests = [DatasetManifest.model_validate(row) for row in json.loads(index.read_text(encoding="utf-8"))]
    if len({m.family for m in manifests}) != len(manifests):
        raise ValueError("expected one frozen profile per family")
    return {
        m.family.value: workload_from_manifest(
            m, skew_score=1.2 if m.family is WorkloadFamily.SKEWED_JOIN else 0.1,
        ) for m in manifests
    }


def profile_support(workload: WorkloadSpec, profiles: dict[str, WorkloadSpec]) -> dict:
    known = profiles.get(workload.family.value)
    if known is None:
        return {"status": "unsupported", "matched": False, "mismatched_fields": ["family"]}
    requested = workload.model_dump()
    baseline = known.model_dump()
    mismatches = [name for name in baseline if requested[name] != baseline[name]]
    return {"status": "matched_frozen_profile" if not mismatches else "insufficient_evidence",
            "matched": not mismatches, "mismatched_fields": mismatches,
            "note": "Descriptor match only; does not verify dataset contents or hardware compatibility."}


def advise(
    workload: WorkloadSpec, predictor: Predictor, profiles: dict[str, WorkloadSpec],
    sla_seconds: float, preferences: Preferences | None = None,
    compare_to: str = "w1_t1_2g",
) -> dict:
    preferences = preferences or Preferences()
    if not math.isfinite(sla_seconds) or sla_seconds <= 0:
        raise ValueError("engine SLA must be finite and positive")
    configs = load_grid()
    if compare_to not in {c.config_id for c in configs}:
        raise ValueError(f"unknown comparison configuration: {compare_to}")
    support = profile_support(workload, profiles)
    point, upper = predictor.predict(candidate_frame(workload))
    if len(point) != len(configs) or len(upper) != len(configs):
        raise ValueError("predictor must return exactly one point and upper value per candidate")
    deadline = sla_seconds * (1 - preferences.deadline_reserve)
    candidates = []
    for config, predicted, bound in zip(configs, point, upper):
        predicted, bound = float(predicted), float(bound)
        if not math.isfinite(predicted) or not math.isfinite(bound) or predicted <= 0 or bound < predicted:
            raise ValueError("predictor returned invalid runtime estimates")
        threads = config.native.n_workers * config.native.threads_per_worker
        per_worker_bytes = dask_memory_bytes(config.native.memory_limit)
        memory = config.native.n_workers * per_worker_bytes
        parts = resource_score(
            predicted, threads, memory, time_reference_s=sla_seconds,
            thread_weight=preferences.thread_weight,
            thread_reference=preferences.thread_reference,
            memory_reference_bytes=preferences.memory_reference_bytes,
        )
        latency_weight = {"resource": 0.0, "balanced": 0.5, "fastest": 1.0}[preferences.mode]
        score = (1 - latency_weight) * parts["resource_score"] + latency_weight * parts["time_ratio"]
        reasons = []
        if not support["matched"]:
            reasons.append("unsupported_workload_profile")
        if bound > deadline:
            reasons.append("runtime_upper_exceeds_deadline")
        if preferences.max_threads is not None and threads > preferences.max_threads:
            reasons.append("configured_threads_exceed_budget")
        if preferences.max_memory_gb is not None and memory / 1e9 > preferences.max_memory_gb:
            reasons.append("configured_memory_exceeds_budget")
        # Retain a declared coarse guard, separate from probabilities. Compressed
        # bytes/total memory is not evidence of peak per-worker memory safety.
        if workload.input_bytes > 4 * memory:
            reasons.append("heuristic_input_memory_guard")
        candidates.append({
            "config_id": config.config_id,
            "n_workers": config.native.n_workers,
            "threads_per_worker": config.native.threads_per_worker,
            "configured_threads": threads,
            "memory_limit_per_worker": config.native.memory_limit,
            "memory_bytes_per_worker": per_worker_bytes,
            "total_memory_bytes": memory, "total_memory_gb": memory / 1e9,
            "predicted_runtime_s": predicted, "runtime_upper_s": bound,
            "deadline_headroom_s": deadline - bound,
            "configured_thread_seconds": threads * predicted,
            "configured_gb_seconds": memory / 1e9 * predicted,
            "score": score, "score_components": parts,
            "eligible": not reasons, "rejection_reasons": reasons,
        })
    reference = next(row for row in candidates if row["config_id"] == compare_to)
    for row in candidates:
        row["comparison"] = {
            "reference_config_id": compare_to,
            "predicted_runtime_change_s": row["predicted_runtime_s"] - reference["predicted_runtime_s"],
            "predicted_runtime_reduction_percent": 100 * (1 - row["predicted_runtime_s"] / reference["predicted_runtime_s"]),
            "score_change": row["score"] - reference["score"],
            "configured_threads_change": row["configured_threads"] - reference["configured_threads"],
            "total_memory_bytes_change": row["total_memory_bytes"] - reference["total_memory_bytes"],
            "interpretation": "Model-based whole-configuration comparison, not a causal or measured improvement.",
        }
    eligible = sorted((r for r in candidates if r["eligible"]),
                      key=lambda r: (r["score"], r["runtime_upper_s"], r["config_id"]))
    return {
        "policy_version": "normalized-resource-v1",
        "workload": workload.model_dump(mode="json"),
        "preferences": preferences.model_dump(mode="json"),
        "engine_sla_seconds": sla_seconds, "effective_deadline_seconds": deadline,
        "timing_scope": "Engine execution only; cluster startup and profiling are excluded by the frozen model.",
        "prediction_target": "Original Windows benchmark environment; transfer to another host is unvalidated.",
        "support": support,
        "decision": {
            "action": "recommend" if eligible else "abstain",
            "config_id": eligible[0]["config_id"] if eligible else None,
            "reason": "minimum declared score among eligible candidates" if eligible else "no candidate passes all support, budget and deadline checks",
            "eligible_config_ids": [r["config_id"] for r in eligible],
        },
        "candidates": candidates,
        "failure_probability": None,
        "limitations": [
            "No learned failure probability is available; memory checks are heuristic.",
            "Bounds come from the frozen cell-group calibration, not an independently validated selected-policy guarantee.",
            "Resource weights are preferences. They were not learned or optimized on test outcomes.",
            "Frozen feature encoding retains legacy nominal GB and skew tags. Scoring uses actual SI/IEC configured bytes.",
            "No job is automatically executed, including after abstention.",
        ],
    }


def load_advice(
    *, workload: WorkloadSpec, index: Path, model_dir: Path,
    sla_seconds: float, preferences: Preferences | None = None, compare_to: str = "w1_t1_2g",
) -> dict:
    from safe_pipe.models.runtime import RuntimePredictor

    support_path = model_dir / "advisor_support.json"
    if not support_path.is_file():
        raise ValueError("missing advisor_support.json; freeze support from the audited training table first")
    bundle = json.loads(support_path.read_text(encoding="utf-8"))
    if bundle.get("schema_version") != 1:
        raise ValueError("unsupported advisor support schema")
    if [c.model_dump(mode="json") for c in load_grid()] != bundle.get("configurations"):
        raise ValueError("configuration grid differs from the frozen model support")
    required = {"runtime_model.txt", "runtime_meta.json", "runtime_metrics.json"}
    if set(bundle["artifact_sha256_lf"]) != required:
        raise ValueError("invalid advisor artifact manifest")
    for name, expected in bundle["artifact_sha256_lf"].items():
        if sha256_lf(model_dir / name) != expected:
            raise ValueError(f"frozen artifact changed: {name}")
    if sha256_lf(index) != bundle["profile_index_sha256_lf"]:
        raise ValueError("profile index differs from the frozen model support")
    meta = json.loads((model_dir / "runtime_meta.json").read_text(encoding="utf-8"))
    metrics = json.loads((model_dir / "runtime_metrics.json").read_text(encoding="utf-8"))
    model_path = model_dir / "runtime_model.txt"
    profiles = frozen_profiles(index)
    if {k: v.model_dump(mode="json") for k, v in profiles.items()} != bundle["profiles"]:
        raise ValueError("profile descriptors differ from audited support")
    predictor = RuntimePredictor(model_path, meta["feature_names"], meta["upper_log_offset"])
    report = advise(workload, predictor, profiles, sla_seconds, preferences, compare_to)
    report["evidence"] = {
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "profile_index_sha256": hashlib.sha256(index.read_bytes()).hexdigest(),
        "training_table_sha256_recorded": meta["table_sha256"],
        "known_workload_profiles": len(profiles),
        "training_rows": metrics["train_rows"],
        "calibration_rows": metrics["calibration_rows"],
        "test_rows": metrics["test_rows"], "test_config_groups": metrics["test_groups"],
        "bound_method": "main-v1 maximum-per-cell residual upper multiplier",
        "upper_multiplier": math.exp(meta["upper_log_offset"]),
        "policy_validation": "No independent new-profile policy evaluation yet.",
        "recorded_executions": bundle["recorded_executions"],
        "recorded_failures": bundle["recorded_failures"],
    }
    return report


def sha256_lf(path: Path) -> str:
    """Ignore only Git's Windows/Unix newline conversion for text artifacts."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
