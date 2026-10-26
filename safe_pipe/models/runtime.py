"""Encoding and grouped split-conformal upper bounds for successful runtimes."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from safe_pipe.features import PRE_RUN_COLUMNS
from safe_pipe.grid import load_grid
from safe_pipe.schemas import WorkloadFamily


def encoded_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Use only the declared pre-run fields and fixed, known categories."""
    data = frame.loc[:, PRE_RUN_COLUMNS].copy()
    data["family"] = pd.Categorical(data["family"], categories=[family.value for family in WorkloadFamily])
    data["config_id"] = pd.Categorical(data["config_id"], categories=[config.config_id for config in load_grid()])
    if data[["family", "config_id"]].isna().any().any():
        raise ValueError("unknown workload family or config id")
    return pd.get_dummies(data, columns=["family", "config_id"], dtype=float).astype(float)


def grouped_upper_quantile(scores: np.ndarray, alpha: float = 0.1) -> float:
    """Finite-sample split-conformal rank over independent family/config cells."""
    if not 0 < alpha < 1 or len(scores) == 0 or not np.isfinite(scores).all():
        raise ValueError("invalid calibration scores or alpha")
    rank = math.ceil((len(scores) + 1) * (1 - alpha))
    if rank > len(scores):
        raise ValueError("too few calibration groups for a finite upper bound")
    return max(0.0, float(np.sort(scores)[rank - 1]))


class RuntimePredictor:
    def __init__(self, model_path: Path, feature_names: list[str], upper_log_offset: float):
        import lightgbm as lgb

        self.booster = lgb.Booster(model_file=str(model_path))
        self.feature_names = feature_names
        self.upper_log_offset = upper_log_offset

    def predict(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        encoded = encoded_features(frame).reindex(columns=self.feature_names, fill_value=0.0)
        point = np.exp(self.booster.predict(encoded))
        upper = point * math.exp(self.upper_log_offset)
        return point, upper
