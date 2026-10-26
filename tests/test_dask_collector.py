from pathlib import Path

import dask

from safe_pipe.collector import collect_dask
from safe_pipe.grid import get_config
from safe_pipe.schemas import RunStatus, WorkloadFamily
from safe_pipe.workloads.generate import generate_family, workload_from_manifest


def test_dask_collector_records_success_and_timeout(tmp_path: Path, monkeypatch) -> None:
    family = WorkloadFamily.SCAN_FILTER
    manifest = generate_family(family, tmp_path, n_rows=400)
    kwargs = dict(
        family=family,
        dataset_dir=Path(manifest.path),
        workload=workload_from_manifest(manifest),
        config=get_config("w1_t1_1g"),
        data_version=manifest.data_version,
        timeout_s=30.0,
    )
    success = collect_dask(**kwargs)
    assert success.status is RunStatus.SUCCESS
    assert success.backend == "dask_local"

    import safe_pipe.collector as collector
    import time

    monkeypatch.setattr(collector, "build_dask_result", lambda *_: dask.delayed(time.sleep)(1.0))
    timed = collect_dask(**{**kwargs, "timeout_s": 0.01})
    assert timed.status is RunStatus.TIMEOUT
    assert timed.engine_seconds == 0.01
