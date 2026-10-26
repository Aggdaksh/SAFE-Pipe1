from __future__ import annotations

from safe_pipe.schemas import ConfigurationSpec


def expected_cost(config: ConfigurationSpec, runtime_s: float) -> float:
    """Normalized local cost: allocated vCPU-seconds + allocated GB-seconds (weights 1, 1)."""
    return config.allocated_vcpus * runtime_s + config.allocated_gb * runtime_s
