from __future__ import annotations

import math

from safe_pipe.schemas import ConfigurationSpec


def expected_cost(config: ConfigurationSpec, runtime_s: float) -> float:
    """Legacy main-v1 resource proxy, preserved to reproduce published tables."""
    return config.allocated_vcpus * runtime_s + config.allocated_gb * runtime_s


def resource_score(
    runtime_s: float, threads: int, memory_bytes: int, *, time_reference_s: float,
    thread_weight: float = 0.5, thread_reference: int = 4,
    memory_reference_bytes: int = 4_000_000_000,
) -> dict[str, float]:
    """Dimensionless configured-resource time score with fixed references.

    Weights express preferences, not learned prices. No candidate-dependent
    min/max normalization, and no measured CPU, monetary or energy claim.
    """
    positive = (runtime_s, threads, memory_bytes, time_reference_s, thread_reference, memory_reference_bytes)
    if any(not math.isfinite(v) or v <= 0 for v in positive):
        raise ValueError("resource values and reference values must be finite and positive")
    if not math.isfinite(thread_weight) or not 0 <= thread_weight <= 1:
        raise ValueError("thread_weight must be in [0, 1]")
    time_ratio = runtime_s / time_reference_s
    thread_component = time_ratio * thread_weight * threads / thread_reference
    memory_component = time_ratio * (1 - thread_weight) * memory_bytes / memory_reference_bytes
    return {"time_ratio": time_ratio, "thread_component": thread_component,
            "memory_component": memory_component, "resource_score": thread_component + memory_component}
