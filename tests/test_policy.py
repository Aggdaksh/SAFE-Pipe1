from safe_pipe.models.ood import OODGate
from safe_pipe.schemas import OODState, WorkloadFamily, WorkloadSpec


def _workload(bytes_: int, family: WorkloadFamily = WorkloadFamily.SCAN_FILTER) -> WorkloadSpec:
    return WorkloadSpec(family=family, input_bytes=bytes_, estimated_rows=100, file_count=1, partition_count=1, skew_score=0)


def test_ood_gate_known_shift_and_unseen_family() -> None:
    gate = OODGate({"scan_filter": 100})
    assert gate.classify(_workload(100)) is OODState.GREEN
    assert gate.classify(_workload(150)) is OODState.YELLOW
    assert gate.classify(_workload(250)) is OODState.RED
    assert gate.classify(_workload(100, WorkloadFamily.GROUPBY)) is OODState.RED
