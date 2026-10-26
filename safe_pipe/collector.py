from __future__ import annotations

import time
import uuid
from pathlib import Path

from safe_pipe.classify import category_for_status, classify_exception
from safe_pipe.schemas import (
    ConfigurationSpec,
    FailureCategory,
    RunResult,
    RunStatus,
    WorkloadFamily,
    WorkloadSpec,
)
from safe_pipe.workloads.execute_pandas import execute_pandas


def collect_pandas(
    *,
    family: WorkloadFamily,
    dataset_dir: Path,
    workload: WorkloadSpec,
    config: ConfigurationSpec,
    timeout_s: float,
    repeat_id: int = 1,
    data_version: str = "tiny-v1",
    hardware: str = "mac-8gb-coding-pandas",
) -> RunResult:
    """Execute one cell without Dask. Timeout is enforced in-process after the call returns
    only as a wall-clock check; long pandas jobs on tiny data should finish quickly.
    """
    t0 = time.perf_counter()
    status = RunStatus.SUCCESS
    category = FailureCategory.NONE
    notes = ""
    value: float | None = None
    try:
        value = execute_pandas(family, dataset_dir)
        elapsed = time.perf_counter() - t0
        if elapsed > timeout_s:
            status = RunStatus.TIMEOUT
            category = FailureCategory.ACTIONABLE
            notes = f"wall clock {elapsed:.3f}s exceeded timeout {timeout_s}"
            elapsed = timeout_s
    except Exception as exc:  # noqa: BLE001 — collector must label, not crash the matrix
        elapsed = time.perf_counter() - t0
        status, category = classify_exception(exc)
        notes = f"{type(exc).__name__}: {exc}"
        if status is RunStatus.SUCCESS:
            status = RunStatus.ERROR
            category = category_for_status(status)

    return RunResult(
        run_id=str(uuid.uuid4()),
        workload=workload,
        config=config,
        status=status,
        engine_seconds=elapsed,
        notes=notes if value is None else f"{notes} result={value}".strip(),
        repeat_id=repeat_id,
        data_version=data_version,
        hardware=hardware,
        failure_category=category,
        backend="pandas_local",
    )
