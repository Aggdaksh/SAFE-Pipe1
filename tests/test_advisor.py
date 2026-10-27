import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from safe_pipe.advisor import Preferences, advise, frozen_profiles, load_advice
from safe_pipe.cost import resource_score
from safe_pipe.memory import dask_memory_bytes, parse_gb
from safe_pipe.optimizer import recommend
from safe_pipe.schemas import CandidateEstimate, ObjectiveSpec, OODState

INDEX = Path("configs/datasets_main_v1.json")
MODELS = Path("artifacts/main_v1")


class StubPredictor:
    def __init__(self, point=None, upper=None):
        self.point = np.array(point if point is not None else [10] * 8, dtype=float)
        self.upper = np.array(upper if upper is not None else self.point * 1.5, dtype=float)

    def predict(self, frame):
        return self.point, self.upper


def report(preferences=None, **kwargs):
    profiles = frozen_profiles(INDEX)
    return advise(profiles["scan_filter"], kwargs.pop("predictor", StubPredictor()), profiles,
                  kwargs.pop("sla", 20), preferences, **kwargs)


def test_dimensionless_score_is_unit_and_candidate_set_independent():
    first = resource_score(10, 2, 2e9, time_reference_s=20)
    scaled = resource_score(10, 2, 2, time_reference_s=20, memory_reference_bytes=4)
    assert first == scaled
    assert first["resource_score"] == pytest.approx(0.25)
    assert first["thread_component"] + first["memory_component"] == first["resource_score"]


def test_native_memory_units_preserve_frozen_feature_convention():
    assert dask_memory_bytes("1GB") == 1_000_000_000
    assert dask_memory_bytes("1 GiB") == 1_073_741_824
    assert dask_memory_bytes("1.5 MB") == 1_500_000
    assert parse_gb("1GB") == 1  # frozen model feature encoding stays unchanged
    row = report()["candidates"][0]
    assert row["total_memory_bytes"] == 1_000_000_000


@pytest.mark.parametrize("value", ["0GB", "nanGB", "infGB", "-1GB", "auto", "1IB"])
def test_invalid_memory_is_rejected(value):
    with pytest.raises(ValueError):
        dask_memory_bytes(value)


@pytest.mark.parametrize("kwargs", [{"thread_weight": 1.1}, {"deadline_reserve": 1},
    {"thread_weight": float("nan")}, {"max_memory_gb": float("inf")}, {"max_threads": 0}])
def test_bad_preferences_fail_before_scoring(kwargs):
    with pytest.raises(ValidationError):
        Preferences(**kwargs)


def test_default_balanced_mode_makes_explicit_speed_resource_tradeoff():
    # Last config uses 4 threads/4GB. It is faster but consumes more resources.
    predictor = StubPredictor(point=[10, 12, 12, 12, 12, 12, 12, 6])
    balanced = report(predictor=predictor)
    resource = report(Preferences(mode="resource"), predictor=predictor)
    fastest = report(Preferences(mode="fastest"), predictor=predictor)
    assert balanced["preferences"]["mode"] == "balanced"
    assert resource["decision"]["config_id"] == "w1_t1_1g"
    assert balanced["decision"]["config_id"] == fastest["decision"]["config_id"] == "w2_t2_2g"


def test_upper_deadline_and_reserve_are_hard_constraints():
    assert report(sla=15)["decision"]["action"] == "recommend"
    refused = report(Preferences(deadline_reserve=0.01), sla=15)
    assert refused["decision"]["action"] == "abstain"
    assert all("runtime_upper_exceeds_deadline" in c["rejection_reasons"] for c in refused["candidates"])


def test_resource_budgets_and_profile_support_fail_closed():
    assert report(Preferences(max_memory_gb=0.9))["decision"]["action"] == "abstain"
    constrained = report(Preferences(max_threads=1))
    assert all(c["configured_threads"] == 1 for c in constrained["candidates"] if c["eligible"])
    profiles = frozen_profiles(INDEX)
    shifted = profiles["scan_filter"].model_copy(update={"partition_count": 17})
    result = advise(shifted, StubPredictor(), profiles, 20)
    assert result["decision"]["action"] == "abstain"
    assert result["support"]["mismatched_fields"] == ["partition_count"]
    assert result["failure_probability"] is None


def test_what_if_tracks_whole_configuration_not_only_worker_count():
    result = report(compare_to="w1_t1_1g")
    changed = next(c for c in result["candidates"] if c["config_id"] == "w2_t1_1g")
    assert changed["comparison"]["total_memory_bytes_change"] == 1_000_000_000
    assert changed["comparison"]["configured_threads_change"] == 1
    assert changed["comparison"]["predicted_runtime_change_s"] == 0


@pytest.mark.parametrize("predictor", [StubPredictor(point=[10]), StubPredictor(point=[float("nan")] * 8),
    StubPredictor(point=[10] * 8, upper=[5] * 8)])
def test_invalid_predictor_cannot_silently_drop_or_rank_candidates(predictor):
    with pytest.raises(ValueError):
        report(predictor=predictor)


def test_hard_guard_cannot_be_disabled_by_legacy_failure_limit():
    candidate = CandidateEstimate(config_id="blocked", expected_runtime_s=1, runtime_upper_s=2,
        p_fail=1, expected_cost=1, ood_state=OODState.GREEN, guard_pass=False)
    assert recommend([candidate], ObjectiveSpec(sla_seconds=10, failure_limit=1)).config_id is None


def test_frozen_bundle_rejects_changed_profile_index_and_model(tmp_path):
    index = tmp_path / "index.json"
    shutil.copyfile(INDEX, index)
    model_dir = tmp_path / "models"
    shutil.copytree(MODELS, model_dir)
    profiles = frozen_profiles(index)
    payload = json.loads(index.read_text())
    payload[0]["input_bytes"] += 1
    index.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="profile index"):
        load_advice(workload=profiles["scan_filter"], index=index, model_dir=model_dir, sla_seconds=30)
    shutil.copyfile(INDEX, index)
    (model_dir / "runtime_model.txt").write_text("changed")
    with pytest.raises(ValueError, match="artifact changed"):
        load_advice(workload=profiles["scan_filter"], index=index, model_dir=model_dir, sla_seconds=30)


def test_frozen_bundle_rejects_changed_grid(monkeypatch):
    from safe_pipe.grid import load_grid

    changed = load_grid()
    changed[0].native.memory_limit = "2GB"
    monkeypatch.setattr("safe_pipe.advisor.load_grid", lambda: changed)
    with pytest.raises(ValueError, match="configuration grid"):
        load_advice(workload=frozen_profiles(INDEX)["scan_filter"], index=INDEX,
                    model_dir=MODELS, sla_seconds=30)


def test_freeze_binds_audited_table_and_rejects_changes(tmp_path):
    from experiments.freeze_advisor_support import freeze

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    for name in ("runtime_model.txt", "runtime_meta.json", "runtime_metrics.json"):
        shutil.copyfile(MODELS / name, model_dir / name)
    table = tmp_path / "runs.csv"
    source = Path("data/curated/runs.csv").read_bytes().replace(b"\r\n", b"\n")
    table.write_bytes(source.replace(b"\n", b"\r\n"))
    frozen = freeze(INDEX, model_dir, table, Path("data/curated/audit.json"))
    assert frozen == json.loads((MODELS / "advisor_support.json").read_text())
    with pytest.raises(ValueError, match="already exists"):
        freeze(INDEX, model_dir, table, Path("data/curated/audit.json"))
    (model_dir / "advisor_support.json").unlink()
    table.write_bytes(source.replace(b"success", b"error", 1))
    with pytest.raises(ValueError, match="model/audit"):
        freeze(INDEX, model_dir, table, Path("data/curated/audit.json"))


def test_real_fitted_advisor_and_cli(capsys):
    pytest.importorskip("lightgbm")
    from safe_pipe.cli import main

    assert main(["advise", "--family", "sort_merge", "--sla", "13.1"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result["candidates"]) == 8
    selected = next(c for c in result["candidates"] if c["config_id"] == result["decision"]["config_id"])
    assert selected["eligible"] and selected["runtime_upper_s"] <= 13.1
    assert result["evidence"]["known_workload_profiles"] == 4
    assert result["evidence"]["recorded_executions"] == 96
    assert result["failure_probability"] is None
    assert main(["advise", "--family", "sort_merge", "--sla", "0.01"]) == 0
    assert json.loads(capsys.readouterr().out)["decision"]["action"] == "abstain"
