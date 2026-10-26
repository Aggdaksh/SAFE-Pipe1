from pathlib import Path

from safe_pipe.grid import get_config
from safe_pipe.schemas import FailureCategory, RunResult, RunStatus, WorkloadFamily, WorkloadSpec
from safe_pipe.store.jsonl import append_run, read_runs


def test_jsonl_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "runs.jsonl"
    result = RunResult(
        run_id="r1",
        workload=WorkloadSpec(
            family=WorkloadFamily.SCAN_FILTER,
            input_bytes=100,
            estimated_rows=10,
            file_count=1,
            partition_count=1,
            skew_score=0.0,
        ),
        config=get_config("w1_t1_1g"),
        status=RunStatus.SUCCESS,
        engine_seconds=0.2,
        failure_category=FailureCategory.NONE,
        backend="pandas_local",
    )
    append_run(path, result)
    loaded = read_runs(path)
    assert len(loaded) == 1
    assert loaded[0].run_id == "r1"
    assert loaded[0].config.config_id == "w1_t1_1g"
