from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from safe_pipe.research import probe_runner as runner


def test_budget_uses_available_memory_and_explicit_caps(monkeypatch):
    monkeypatch.setattr(runner.psutil, "virtual_memory", lambda: SimpleNamespace(total=16*runner.GIB, available=4*runner.GIB))
    config = {"n_workers": 1, "threads_per_worker": 1, "memory_limit": "1GB"}
    observed = runner.validate_host_budget(config)
    assert observed["aggregate_worker_cap_bytes"] == 1_000_000_000
    assert observed["reserved_headroom_bytes"] == 2*runner.GIB
    with pytest.raises(ValueError, match="insufficient available"):
        runner.validate_host_budget({**config, "n_workers": 3})
    with pytest.raises(ValueError, match="explicit"):
        runner.validate_host_budget({**config, "memory_limit": "auto"})
    with pytest.raises(ValueError, match="positive integer"):
        runner.validate_host_budget({**config, "n_workers": True})


def test_missing_telemetry_is_not_zero_spill(tmp_path):
    report = runner._summarize_telemetry(tmp_path, expected_workers=2)
    assert report["spilled_disk_peak_bytes_sum"] is None
    assert report["rss_peak_bytes_sum"] is None
    assert report["missing_initial_worker_records"] == 2
    assert report["worker_count_observed"] == 0


def test_telemetry_retains_restarts_and_labels_sum_of_peaks(tmp_path):
    for i, rss in enumerate([100, 200, 150]):
        (tmp_path / f"worker-{i}.json").write_text(json.dumps({
            "samples": 2, "peak_rss_bytes": rss, "peak_managed_in_memory_bytes": 30,
            "peak_spilled_disk_bytes": 0, "paused_samples": 0,
            "cumulative_spill_write_bytes": 0,
        }))
    report = runner._summarize_telemetry(tmp_path, expected_workers=2)
    assert report["rss_peak_bytes_sum"] == 450
    assert report["spilled_disk_peak_bytes_sum"] == 0
    assert report["samples_total"] == 6
    assert report["observed_restarts_lower_bound"] == 1
    assert "NOT a concurrent" in report["aggregation"]


def test_sampler_does_not_invent_supported_spill_metrics(tmp_path):
    sampler = runner._MemorySampler(str(tmp_path))
    sampler.worker = SimpleNamespace(state=SimpleNamespace(nbytes=120), data={}, status=SimpleNamespace(name="running"))
    sampler.process = SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=200))
    sampler.path = tmp_path / "worker-test.json"
    sampler.started = runner.time.monotonic()
    sampler.persisted = 0
    sampler.record = {
        "samples": 0, "sampling_errors": 0, "paused_samples": 0, "status_counts": {},
        "baseline_rss_bytes": None, "peak_rss_bytes": None, "peak_managed_total_bytes": None,
        "peak_managed_in_memory_bytes": None, "peak_spilled_memory_bytes": None,
        "peak_spilled_disk_bytes": None, "cumulative_spill_write_bytes": None,
        "cumulative_spill_write_count": None,
    }
    sampler.sample(force=True)
    record = json.loads(sampler.path.read_text())
    assert record["peak_rss_bytes"] == 200
    assert record["peak_managed_total_bytes"] == 120
    assert record["peak_spilled_disk_bytes"] is None
    assert record["peak_managed_in_memory_bytes"] is None
    assert record["cumulative_spill_write_bytes"] is None


def test_invalid_timeout_rejected_before_host_or_manifest(monkeypatch, tmp_path):
    # Import is deferred but the workload module is available in the branch.
    for value in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="timeout_s"):
            runner.run_probe(tmp_path, {}, value)


def test_graph_signature_counts_actual_graph():
    graph = SimpleNamespace(__dask_graph__=lambda: {("read-file", 0): 1, ("sum-chunk", 0): 2})
    info = runner._graph_info(graph)
    assert info["task_count"] == 2
    assert info["task_prefix_counts"] == {"read-file": 1, "sum-chunk": 1}
    assert len(info["key_sha256"]) == 64


def test_inspection_denial_is_rejected_before_spawning(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "validate_host_budget", lambda _: {})
    def denied(**kwargs):
        raise PermissionError("sandbox")
    monkeypatch.setattr(runner.psutil, "Process", lambda: SimpleNamespace(children=denied))
    with pytest.raises(ValueError, match="process inspection"):
        runner.run_probe(tmp_path, {}, 10)
