import csv

from experiments import export_probe_evidence as exporter


def test_export_accepts_timeout_missing_phase_fields_and_retains_diagnosis(tmp_path, monkeypatch):
    base = {"cell_id": "a", "run_id": "first", "instance_id": "x", "method": "full",
            "target_config_id": "c", "repeat_id": 1, "status": "timeout",
            "config": {"memory_limit": "1000000000", "n_workers": 2, "threads_per_worker": 1},
            "dataset": {"sha256": "hash", "n_rows": 1, "n_right_rows": 0,
                        "compressed_bytes": 1, "logical_bytes": 1, "preparation_seconds": .1},
            "timings": {"total_seconds": 2}, "environment": {}, "host_budget": {"physical_bytes": 16},
            "diagnostics": {"failure_category": "timeout", "retained": True}}
    rows = [base, {**base, "cell_id": "b", "run_id": "second", "status": "success",
                   "timings": {"total_seconds": 3, "graph_build_seconds": .2, "compute_seconds": 1}}]
    monkeypatch.setattr(exporter, "load_plan", lambda _: ({}, "plan-hash"))
    monkeypatch.setattr(exporter, "load_records", lambda *a: rows)
    monkeypatch.setattr(exporter, "summarize", lambda *a: {"telemetry_by_cell": []})
    monkeypatch.setattr(exporter, "markdown_report", lambda _: "fixture report")
    exporter.export(tmp_path / "plan.json", tmp_path / "export")
    with (tmp_path / "export" / "measurements.csv").open() as stream:
        result = list(csv.DictReader(stream))
    assert result[0]["failure_category"] == "timeout"
    assert result[0]["compute_seconds"] == ""
    assert result[1]["compute_seconds"] == "1"
