from __future__ import annotations

import json

import pytest

pytest.importorskip("pyarrow")
pytest.importorskip("pandas")
pytest.importorskip("dask.dataframe")

from safe_pipe.research.probe_workloads import (
    build_probe_result,
    generate_instance,
    load_manifest,
    make_probe,
    reference_value,
)


def recipe(family="groupby", **overrides):
    return {"instance_id": "development-a", "family": family, "n_rows": 240,
            "n_files": 4, "seed": 17, "n_keys": 32, "hot_fraction": 0.6,
            "payload_columns": 3, "partition_imbalance": 0.7, **overrides}


@pytest.mark.parametrize("family", ["groupby", "skewed_join"])
def test_deterministic_data_and_all_payload_operator_correctness(tmp_path, family):
    import pandas as pd

    first = generate_instance(tmp_path / "a", recipe(family))
    second = generate_instance(tmp_path / "b", recipe(family))
    assert first["sha256"] == second["sha256"]
    assert first["n_rows"] == 240
    assert first["compressed_bytes"] > 0 and first["logical_bytes"] > 0
    assert load_manifest(tmp_path / "a", verify=True)["sha256"] == first["sha256"]
    actual = float(build_probe_result(tmp_path / "a").compute(scheduler="synchronous"))
    assert actual == pytest.approx(reference_value(tmp_path / "a"), rel=1e-12)
    left = pd.read_parquet(tmp_path / "a" / "left")
    if family == "groupby":
        expected = float(left[["payload_0", "payload_1", "payload_2"]].sum().sum())
        assert actual == pytest.approx(expected)
        assert actual > float(left["payload_0"].sum())
    else:
        right = pd.read_parquet(tmp_path / "a" / "right")
        assert right["key"].is_unique
        assert set(left["key"]) <= set(right["key"])
        assert sum(f["relation"] == "right" for f in first["files"]) > 1


@pytest.mark.parametrize("family", ["groupby", "skewed_join"])
@pytest.mark.parametrize("method", ["uniform", "partition_tail"])
def test_probe_exact_budget_reproducibility_and_join_matches(tmp_path, family, method):
    import pandas as pd

    original = generate_instance(tmp_path / "source", recipe(family))
    a = make_probe(tmp_path / "source", tmp_path / "a", 0.125, method, 7)
    b = make_probe(tmp_path / "source", tmp_path / "b", 0.125, method, 7)
    assert a["n_rows"] == 30
    assert a["sha256"] == b["sha256"]
    assert a["parent_sha256"] == original["sha256"]
    assert a["parent_instance_id"] == "development-a"
    assert a["sampling"]["fidelity_validated"] is False
    actual = float(build_probe_result(tmp_path / "a").compute(scheduler="synchronous"))
    assert actual == pytest.approx(reference_value(tmp_path / "a"), rel=1e-12)
    if family == "skewed_join":
        left = pd.read_parquet(tmp_path / "a" / "left")
        right = pd.read_parquet(tmp_path / "a" / "right")
        assert len(left.merge(right, on="key", how="inner")) == len(left)
        assert a["n_right_rows"] == original["n_right_rows"]
        assert "full right dimension retained" in a["sampling"]["budget_scope"]


def test_tail_oversamples_large_input_partition_without_outcomes(tmp_path):
    generate_instance(tmp_path / "source", recipe(n_rows=1000, partition_imbalance=0.8))
    probe = make_probe(tmp_path / "source", tmp_path / "tail", 0.2, "partition_tail", 3)
    sampling = probe["sampling"]
    assert sum(sampling["selected_partition_rows"]) == 200
    assert sampling["selected_partition_rows"][0] / 200 > sampling["source_partition_rows"][0] / 1000
    assert sampling["biased"]
    assert "metadata only" in sampling["selection_information"]


@pytest.mark.parametrize("method", ["uniform", "partition_tail"])
def test_very_small_probes_with_empty_partitions_still_execute(tmp_path, method):
    generate_instance(tmp_path / "source", recipe("skewed_join"))
    probe = make_probe(tmp_path / "source", tmp_path / "probe", 0.001, method, 5)
    assert probe["n_rows"] == 1
    assert float(build_probe_result(tmp_path / "probe").compute(scheduler="synchronous")) == pytest.approx(
        reference_value(tmp_path / "probe"))


def test_full_probe_preserves_every_value_and_overwrite_refused(tmp_path):
    source = generate_instance(tmp_path / "source", recipe())
    full = make_probe(tmp_path / "source", tmp_path / "full", 1.0, "full", 4)
    assert full["n_rows"] == source["n_rows"]
    assert reference_value(tmp_path / "full") == reference_value(tmp_path / "source")
    with pytest.raises(FileExistsError):
        generate_instance(tmp_path / "source", recipe())
    with pytest.raises(FileExistsError):
        make_probe(tmp_path / "source", tmp_path / "full", 1.0, "full", 4)


def test_altered_source_and_escaping_manifest_rejected(tmp_path):
    source = generate_instance(tmp_path / "source", recipe())
    path = tmp_path / "source" / source["files"][0]["path"]
    path.write_bytes(b"altered")
    with pytest.raises(ValueError, match="hash mismatch"):
        make_probe(tmp_path / "source", tmp_path / "probe", 0.2, "uniform", 2)
    assert not (tmp_path / "probe").exists()
    source["files"][0]["path"] = "../escape.parquet"
    (tmp_path / "source" / "manifest.json").write_text(json.dumps(source))
    with pytest.raises(ValueError, match="escapes"):
        load_manifest(tmp_path / "source")


def test_unlisted_data_cannot_silently_enter_probe(tmp_path):
    generate_instance(tmp_path / "source", recipe())
    (tmp_path / "source" / "left" / "extra.parquet").write_bytes(b"unlisted")
    with pytest.raises(ValueError, match="inventory"):
        make_probe(tmp_path / "source", tmp_path / "probe", 0.2, "uniform", 1)


@pytest.mark.parametrize("change", [{"n_rows": 0}, {"n_rows": 2}, {"n_files": True},
                                     {"hot_fraction": float("nan")}, {"payload_columns": 0},
                                     {"family": "sort"}, {"n_keys": 1}, {"unknown": 1}])
def test_bad_recipes_leave_no_destination(tmp_path, change):
    with pytest.raises(ValueError):
        generate_instance(tmp_path / "bad", recipe(**change))
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("fraction,method", [(0, "uniform"), (float("inf"), "uniform"),
                                            (1.1, "uniform"), (0.2, "full"), (0.2, "bogus")])
def test_bad_probe_parameters(tmp_path, fraction, method):
    with pytest.raises(ValueError):
        make_probe(tmp_path / "missing", tmp_path / "probe", fraction, method, 1)
