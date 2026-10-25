from pydantic import ValidationError
import pytest

from safe_pipe.schemas import CandidateEstimate, OODState, WorkloadFamily, WorkloadSpec


def test_workload_rejects_zero_bytes() -> None:
    with pytest.raises(ValidationError):
        WorkloadSpec(
            family=WorkloadFamily.SCAN_FILTER,
            input_bytes=0,
            estimated_rows=1,
            file_count=1,
            partition_count=1,
            skew_score=0.0,
        )


def test_upper_bound_cannot_be_below_point() -> None:
    with pytest.raises(ValidationError):
        CandidateEstimate(
            config_id="c1",
            expected_runtime_s=10,
            runtime_upper_s=8,
            p_fail=0.0,
            expected_cost=1.0,
            ood_state=OODState.GREEN,
        )
