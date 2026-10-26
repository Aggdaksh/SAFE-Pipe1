import pytest

from experiments.run_matrix import pending_cells
from safe_pipe.grid import get_config
from safe_pipe.matrix import planned_cells
from safe_pipe.schemas import RunResult, RunStatus, WorkloadFamily, WorkloadSpec


def test_resume_skips_completed_cell_and_rejects_duplicate() -> None:
    plan = planned_cells()
    row = RunResult(
        run_id="first",
        workload=WorkloadSpec(
            family=WorkloadFamily.SCAN_FILTER,
            input_bytes=100,
            estimated_rows=10,
            file_count=1,
            partition_count=1,
            skew_score=0,
        ),
        config=get_config("w1_t1_1g"),
        repeat_id=1,
        status=RunStatus.SUCCESS,
    )
    remaining = pending_cells(plan, [row])
    assert len(remaining) == 95
    assert {"family": "scan_filter", "config_id": "w1_t1_1g", "repeat_id": 1} not in remaining
    with pytest.raises(ValueError, match="duplicate"):
        pending_cells(plan, [row, row])
