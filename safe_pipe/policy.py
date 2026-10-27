"""Convert one pre-run workload profile into declared candidate estimates."""

from __future__ import annotations

import pandas as pd

from safe_pipe.grid import load_grid
from safe_pipe.memory import parse_gb
from safe_pipe.models.ood import OODGate
from safe_pipe.models.runtime import RuntimePredictor
from safe_pipe.schemas import CandidateEstimate, WorkloadSpec


def candidate_frame(workload: WorkloadSpec) -> pd.DataFrame:
    """One pre-run feature row for each frozen configuration, in grid order."""
    configs = load_grid()
    rows = []
    for config in configs:
        rows.append(
            {
                "family": workload.family.value,
                "input_bytes": workload.input_bytes,
                "estimated_rows": workload.estimated_rows,
                "file_count": workload.file_count,
                "partition_count": workload.partition_count,
                "skew_score": workload.skew_score,
                "config_id": config.config_id,
                "n_workers": config.native.n_workers,
                "threads_per_worker": config.native.threads_per_worker,
                "memory_limit_gb": parse_gb(config.native.memory_limit),
                "allocated_vcpus": config.allocated_vcpus,
                "allocated_gb": config.allocated_gb,
            }
        )
    return pd.DataFrame(rows)


def estimate_candidates(workload: WorkloadSpec, predictor: RuntimePredictor, ood_gate: OODGate) -> list[CandidateEstimate]:
    configs = load_grid()
    point, upper = predictor.predict(candidate_frame(workload))
    state = ood_gate.classify(workload)
    estimates = []
    for config, expected_runtime, upper_runtime in zip(configs, point, upper):
        # All 96 physical runs succeeded. This is a rule flag, not a calibrated
        # failure probability; the report must not imply measured risk reduction.
        hard_memory_guard = workload.input_bytes > 4 * config.allocated_gb * 1024**3
        estimates.append(
            CandidateEstimate(
                config_id=config.config_id,
                expected_runtime_s=float(expected_runtime),
                runtime_upper_s=float(upper_runtime),
                p_fail=1.0 if hard_memory_guard else 0.0,
                guard_pass=not hard_memory_guard,
                expected_cost=float(expected_runtime * (config.allocated_vcpus + config.allocated_gb)),
                ood_state=state,
            )
        )
    return estimates
