"""Real local-process checks: bounded timeout and measured scalar correctness."""
import pytest

pytest.importorskip("distributed")
from safe_pipe.research.probe_runner import run_probe
from safe_pipe.research.probe_workloads import generate_instance, reference_value


def test_real_supervisor_result_and_worker_telemetry(tmp_path):
    dataset = tmp_path / "input"
    generate_instance(dataset, {"n_rows": 128, "n_files": 2, "payload_columns": 2})
    row = run_probe(dataset, {"config_id": "tiny", "n_workers": 1,
                             "threads_per_worker": 1, "memory_limit": "1GB"}, timeout_s=30)
    assert row["status"] == "success", row.get("error")
    assert row["result_value"] == pytest.approx(reference_value(dataset))
    assert row["telemetry"]["samples_total"] > 0
    assert row["telemetry"]["rss_peak_bytes_sum"] > 0
    assert row["owned_descendants_alive_after_cleanup"] == 0
    assert any("shuffle" in prefix for prefix in row["graph"]["task_prefix_counts"])


def test_real_supervisor_wall_timeout_is_censored_and_cleaned(tmp_path):
    dataset = tmp_path / "input"
    generate_instance(dataset, {"n_rows": 128, "n_files": 2, "payload_columns": 2})
    row = run_probe(dataset, {"config_id": "tiny", "n_workers": 1,
                             "threads_per_worker": 1, "memory_limit": "1GB"}, timeout_s=0.2)
    assert row["status"] == "timeout"
    assert row.get("result_value") is None
    assert row["timings"]["execution_seconds"] is None
    assert row["timings"]["total_seconds"] < 10
    assert row["owned_descendants_alive_after_cleanup"] == 0
