"""Conservative workload-profile gate for the four measured families."""

from __future__ import annotations

import math

from safe_pipe.schemas import OODState, WorkloadSpec


class OODGate:
    """Use known family and input size; thresholds are declared heuristics, not fitted."""

    def __init__(self, bytes_by_family: dict[str, int]):
        if not bytes_by_family or any(value <= 0 for value in bytes_by_family.values()):
            raise ValueError("need positive training sizes")
        self.bytes_by_family = bytes_by_family

    def classify(self, workload: WorkloadSpec) -> OODState:
        known_bytes = self.bytes_by_family.get(workload.family.value)
        if known_bytes is None:
            return OODState.RED
        ratio = workload.input_bytes / known_bytes
        distance = abs(math.log(ratio))
        if distance > math.log(2):
            return OODState.RED
        if distance > math.log(1.25):
            return OODState.YELLOW
        return OODState.GREEN
