from __future__ import annotations

import copy
import json

import pytest

from experiments.probe_pilot import canonical_hash, load_records, mapped_config, preset_definition
from safe_pipe.research.probe_analysis import summarize


def fixture_matrix():
    configs = [{"config_id": "a"}, {"config_id": "b"}]
    cells = []
    records = []
    for method, values in {"full": {"a": [10, 11], "b": [20, 21]},
                           "uniform": {"a": [4, 4.1], "b": [2, 2.1]}}.items():
        for config, times in values.items():
            for repeat, t in enumerate(times, 1):
                cell = {"cell_id": f"{method}-{config}-{repeat}", "instance_id": "x",
                        "method": method, "target_config_id": config, "repeat_id": repeat}
                cells.append(cell)
                records.append({**cell, "status": "success", "timings": {"execution_seconds": t}})
    return {"cells": cells, "configs": configs, "repeats": 2, "ranking_tolerance": .05,
            "datasets": {"x": {}}, "methods": ["full", "uniform"], "role": "development_only"}, records


def test_known_rank_inversion_and_selected_runtime_regret():
    plan, records = fixture_matrix()
    summary = summarize(plan, records)
    comparison = summary["comparisons"][0]
    assert comparison["pair_counts"] == {"inverted": 1}
    assert comparison["proxy_selected_config"] == "b"
    assert comparison["selected_full_engine_regret"] == pytest.approx(20.5 / 10.5 - 1)
    assert "deadline guarantee" in " ".join(summary["method_notes"])


def test_failure_and_missing_repeats_cannot_disappear_from_ranking():
    plan, records = fixture_matrix()
    records[0]["status"] = "timeout"
    records[0]["timings"]["execution_seconds"] = 1  # Censoring cannot look like a fast completion.
    summary = summarize(plan, records[:-1])
    assert summary["statuses"]["timeout"] == 1
    assert summary["missing_cells"]
    assert not summary["comparisons"][0]["evaluable"]


def test_overlapping_repeat_ranges_are_unresolved():
    plan, records = fixture_matrix()
    records[1]["timings"]["execution_seconds"] = 22
    result = summarize(plan, records)["comparisons"][0]
    assert result["pair_counts"] == {"reference_unresolved": 1}
    assert result["inversion_fraction_among_resolved"] is None


def test_duplicate_or_mislabelled_cells_are_rejected():
    plan, records = fixture_matrix()
    with pytest.raises(ValueError, match="duplicated"):
        summarize(plan, records + records[:1])
    changed = copy.deepcopy(records)
    changed[0]["method"] = "uniform"
    with pytest.raises(ValueError, match="identity"):
        summarize(plan, changed)


def test_memory_matched_comparison_and_no_target_mutation():
    target = {"config_id": "a", "n_workers": 1, "threads_per_worker": 1, "memory_limit": "1000000000"}
    original = dict(target)
    uniform = mapped_config(target, "uniform", .25)
    memory = mapped_config(target, "uniform_memory", .25)
    tail = mapped_config(target, "partition_tail", .25)
    assert target == original
    assert uniform["memory_limit"] == target["memory_limit"]
    assert memory["memory_limit"] == tail["memory_limit"]
    assert 512 * 2**20 < int(tail["memory_limit"]) < 10**9


def test_resume_rejects_modified_plan_and_duplicates(tmp_path):
    path = tmp_path / "runs.jsonl"
    row = {"cell_id": "x", "plan_sha256": canonical_hash({"version": 1})}
    path.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="modified plan"):
        load_records(path, canonical_hash({"version": 2}))
    path.write_text((json.dumps(row) + "\n") * 2)
    with pytest.raises(ValueError, match="Duplicate"):
        load_records(path, row["plan_sha256"])


def test_preset_sizes_and_mac_worker_cap():
    for preset, expected in [("smoke", 16), ("mac-limited", 32), ("mac-development", 64), ("windows-screen", 768)]:
        recipes, configs, repeats = preset_definition(preset)
        assert len(recipes) * len(configs) * repeats * 4 == expected
        if preset != "windows-screen":
            assert all(c["n_workers"] == 1 and int(c["memory_limit"]) <= 2_000_000_000 for c in configs)


def test_mechanism_report_retains_missing_failure_and_unknown_evidence():
    from safe_pipe.research.probe_analysis import mechanism_summary, markdown_report
    plan = {"recipes": [{"instance_id": "x", "family": "groupby", "hot_fraction": .25,
                         "partition_imbalance": 0}], "configs": [{"config_id": "a"}, {"config_id": "b"}],
            "repeats": 3}
    rows = [{"instance_id": "x", "target_config_id": "a", "status": "execution_error",
             "diagnostics": {"failure_category": "worker_death_unknown_cause"},
             "conditions": {"flags": ["mains_lost_or_unknown"]}}]
    mechanism = mechanism_summary(plan, rows)
    group = mechanism["groups"][0]
    assert group["statuses"] == {"execution_error": 1}
    assert group["observed"] == 1 and group["expected"] == 3
    assert group["spill_unknown"] == group["diagnosis_unknown"] == group["condition_flagged"] == 1
    assert mechanism["groups"][1]["observed"] == 0
    report = markdown_report({"mechanism": mechanism, "recorded_cells": 1, "planned_cells": 6})
    assert "MANUAL REVIEW" in report and "execution_error" in report
