from pathlib import Path

import pytest

from safe_pipe.schemas import WorkloadFamily
from safe_pipe.workloads.execute_dask import execute_dask


def test_dask_execute_is_explicitly_unimplemented(tmp_path: Path) -> None:
    with pytest.raises(NotImplementedError, match="16GB"):
        execute_dask(WorkloadFamily.SCAN_FILTER, tmp_path)
