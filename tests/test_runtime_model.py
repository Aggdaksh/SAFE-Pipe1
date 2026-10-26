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
