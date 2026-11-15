"""Real local-process checks: bounded timeout and measured scalar correctness."""
import pytest

pytest.importorskip("distributed")
from safe_pipe.research.probe_runner import run_probe
from safe_pipe.research.probe_workloads import generate_instance, reference_value


def test_real_supervisor_result_and_worker_telemetry(tmp_path):
    dataset = tmp_path / "input"
    generate_instance(dataset, {"n_rows": 128, "n_files": 2, "payload_columns": 2})
    row = run_probe(dataset, {"config_id": "tiny", "n_workers": 1,
                             "threads_per_worker": 1, "memory_limit": "1GB"}, timeout_s=30,
                    diagnostics_dir=tmp_path / "diagnostics")
    assert row["status"] == "success", row.get("error")
    assert row["result_value"] == pytest.approx(reference_value(dataset))
    assert row["telemetry"]["samples_total"] > 0
    assert row["telemetry"]["rss_peak_bytes_sum"] > 0
    assert row["owned_descendants_alive_after_cleanup"] == 0
    assert any("shuffle" in prefix for prefix in row["graph"]["task_prefix_counts"])
    from pathlib import Path
    evidence = Path(row["diagnostics"]["directory"])
    assert evidence.is_dir() and row["diagnostics"]["retained"]
    assert (evidence / "supervisor.jsonl").is_file()
    assert (evidence / "scheduler-events.jsonl").is_file()
    assert row["diagnostics"]["malformed_log_lines"] == 0
    assert row["diagnostics"]["log_write_errors"] == 0
    assert row["memory_settings"]["terminate"] is not None
    assert row["timings"]["graph_build_seconds"] >= 0
    assert row["timings"]["compute_seconds"] > 0
    assert row["timings"]["end_to_end_seconds"] >= row["timings"]["total_seconds"]
    phases = ("setup_seconds", "execution_seconds", "telemetry_flush_seconds", "cleanup_seconds",
              "supervisor_finalize_seconds", "scratch_cleanup_seconds", "unattributed_seconds")
    assert sum(row["timings"][k] for k in phases) == pytest.approx(row["timings"]["total_seconds"], abs=.01)


def test_real_supervisor_wall_timeout_is_censored_and_cleaned(tmp_path):
    dataset = tmp_path / "input"
    generate_instance(dataset, {"n_rows": 128, "n_files": 2, "payload_columns": 2})
    row = run_probe(dataset, {"config_id": "tiny", "n_workers": 1,
                             "threads_per_worker": 1, "memory_limit": "1GB"}, timeout_s=0.2,
                    diagnostics_dir=tmp_path / "diagnostics")
    assert row["status"] == "timeout"
    assert row.get("result_value") is None
    assert row["timings"]["execution_seconds"] is None
    assert row["timings"]["total_seconds"] < 10
    assert row["owned_descendants_alive_after_cleanup"] == 0
    from pathlib import Path
    assert (Path(row["diagnostics"]["directory"]) / "supervisor-outcome.json").is_file()
    assert row["diagnostics"]["failure_category"] == "timeout"
