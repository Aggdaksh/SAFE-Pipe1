import json
from pathlib import Path

import pytest

pytest.importorskip("lightgbm")

from safe_pipe.cli import main
from safe_pipe.schemas import WorkloadFamily, WorkloadSpec


def test_fitted_cli_recommends_and_abstains_for_large_shift(tmp_path: Path, capsys) -> None:
    assert main(["recommend-model", "--family", "sort_merge", "--sla", "13.1"]) == 0
    known = json.loads(capsys.readouterr().out)
    assert len(known["candidates"]) == 8
    assert known["decision"]["action"] == "recommend"
    assert known["decision"]["config_id"] == "w1_t2_1g"

    shifted = WorkloadSpec(
        family=WorkloadFamily.SORT_MERGE,
        input_bytes=3 * 178_382_606,
        estimated_rows=12_770_000,
        file_count=16,
        partition_count=16,
        skew_score=0.1,
    )
    path = tmp_path / "shifted.json"
    path.write_text(shifted.model_dump_json(), encoding="utf-8")
    assert main(["recommend-model", "--workload-json", str(path), "--sla", "13.1"]) == 0
    red = json.loads(capsys.readouterr().out)
    assert red["decision"]["action"] == "abstain"
    assert all(candidate["ood_state"] == "red" for candidate in red["candidates"])
