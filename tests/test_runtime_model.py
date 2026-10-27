import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from safe_pipe.features import LABEL_COLUMNS, PRE_RUN_COLUMNS
from safe_pipe.models.runtime import encoded_features, grouped_upper_quantile


def test_model_features_exclude_labels_and_use_known_categories() -> None:
    assert not set(PRE_RUN_COLUMNS) & set(LABEL_COLUMNS)
    row = {
        "family": "scan_filter", "input_bytes": 100, "estimated_rows": 10,
        "file_count": 1, "partition_count": 1, "skew_score": 0,
        "config_id": "w1_t1_1g", "n_workers": 1, "threads_per_worker": 1,
        "memory_limit_gb": 1, "allocated_vcpus": 1, "allocated_gb": 1,
        "engine_seconds": 999,
    }
    features = encoded_features(pd.DataFrame([row]))
    assert "engine_seconds" not in features
    assert features.shape[0] == 1


def test_conformal_rank_uses_groups_and_refuses_too_few() -> None:
    assert grouped_upper_quantile(np.arange(1, 13, dtype=float), 0.1) == 12
    with pytest.raises(ValueError, match="too few"):
        grouped_upper_quantile(np.arange(1, 9, dtype=float), 0.1)


def test_fitted_model_crlf_matches_original_file_loader(tmp_path: Path) -> None:
    pytest.importorskip("lightgbm")
    source = Path("artifacts/main_v1/runtime_model.txt").read_bytes().replace(b"\r\n", b"\n")
    lf_path = tmp_path / "model_lf.txt"
    crlf_path = tmp_path / "model_crlf.txt"
    lf_path.write_bytes(source)
    crlf_path.write_bytes(source.replace(b"\n", b"\r\n"))
    # Isolate native LightGBM: a regression in newline handling must fail this
    # test without aborting the entire pytest process.
    code = """
import json, math, sys
from pathlib import Path
import lightgbm as lgb
import numpy as np
import pandas as pd
from safe_pipe.models.runtime import RuntimePredictor, encoded_features
meta = json.loads(Path('artifacts/main_v1/runtime_meta.json').read_text())
frame = pd.read_csv('data/curated/runs.csv')
encoded = encoded_features(frame).reindex(columns=meta['feature_names'], fill_value=0.0)
expected = np.exp(lgb.Booster(model_file=sys.argv[1]).predict(encoded))
point, upper = RuntimePredictor(Path(sys.argv[2]), meta['feature_names'], meta['upper_log_offset']).predict(frame)
np.testing.assert_array_equal(point, expected)
np.testing.assert_array_equal(upper, expected * math.exp(meta['upper_log_offset']))
print(len(point))
"""
    completed = subprocess.run([sys.executable, "-B", "-c", code, str(lf_path), str(crlf_path)],
                               capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr[-4000:]
    assert completed.stdout.strip() == "96"
    assert crlf_path.read_bytes() == source.replace(b"\n", b"\r\n")


def test_fitted_advisor_accepts_crlf_checkout(tmp_path: Path) -> None:
    pytest.importorskip("lightgbm")
    from safe_pipe.advisor import frozen_profiles, load_advice

    index = Path("configs/datasets_main_v1.json")
    model_dir = Path("artifacts/main_v1")
    workload = frozen_profiles(index)["sort_merge"]
    expected = load_advice(workload=workload, index=index, model_dir=model_dir, sla_seconds=13.1)
    copied = tmp_path / "artifacts"
    shutil.copytree(model_dir, copied)
    copied_index = tmp_path / "index.json"
    copied_index.write_bytes(index.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    for path in copied.iterdir():
        if path.suffix in {".json", ".txt", ".csv"}:
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    result = load_advice(workload=workload, index=copied_index, model_dir=copied, sla_seconds=13.1)
    # Raw-file hashes intentionally reflect the checkout's byte representation.
    for key in ("model_sha256", "profile_index_sha256"):
        result["evidence"].pop(key)
        expected["evidence"].pop(key)
    assert result == expected
