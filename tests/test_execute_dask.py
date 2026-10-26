from pathlib import Path

import math
import pytest

pytest.importorskip("dask.dataframe")

from safe_pipe.adapters.dask_local import local_client
from safe_pipe.schemas import DaskNativeConfig, WorkloadFamily
from safe_pipe.workloads.execute_dask import execute_dask
from safe_pipe.workloads.generate import generate_family


@pytest.mark.parametrize("family", list(WorkloadFamily))
def test_dask_family_finishes_on_tiny_input(family: WorkloadFamily, tmp_path: Path) -> None:
    manifest = generate_family(family, tmp_path, n_rows=400, n_files=2)
    config = DaskNativeConfig(n_workers=1, threads_per_worker=1, memory_limit="512MB")
    with local_client(config):
        value = execute_dask(family, Path(manifest.path))
    assert math.isfinite(value)
