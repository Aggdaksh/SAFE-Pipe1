from pathlib import Path

from safe_pipe.collector import collect_pandas
from safe_pipe.grid import get_config
from safe_pipe.matrix import planned_cells
from safe_pipe.schemas import RunStatus, WorkloadFamily
from safe_pipe.workloads.generate import generate_family, verify_manifest, workload_from_manifest
from safe_pipe.workloads.execute_pandas import execute_pandas


def test_planned_matrix_is_96() -> None:
    assert len(planned_cells()) == 96


def test_tiny_families_execute_in_pandas(tmp_path: Path) -> None:
    dest = tmp_path / "data"
    for family in WorkloadFamily:
        manifest = generate_family(family, dest, n_rows=400, n_files=2)
        assert manifest.input_bytes > 0
        assert (Path(manifest.path) / "manifest.json").exists()
        verify_manifest(manifest, Path(manifest.path))
        execute_pandas(family, Path(manifest.path))


def test_collector_records_success_and_timeout(tmp_path: Path) -> None:
    family = WorkloadFamily.SCAN_FILTER
    manifest = generate_family(family, tmp_path, n_rows=400)
    workload = workload_from_manifest(manifest)
    config = get_config("w1_t1_1g")
    ok = collect_pandas(
        family=family,
        dataset_dir=Path(manifest.path),
        workload=workload,
        config=config,
        timeout_s=30.0,
    )
    assert ok.status is RunStatus.SUCCESS
    timed = collect_pandas(
        family=family,
        dataset_dir=Path(manifest.path),
        workload=workload,
        config=config,
        timeout_s=0.0,
    )
    assert timed.status is RunStatus.TIMEOUT
