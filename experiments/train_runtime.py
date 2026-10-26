"""Fit LightGBM once on the frozen grouped split and report held-out metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from safe_pipe.models.runtime import encoded_features, grouped_upper_quantile
from safe_pipe.schemas import RunStatus


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", type=Path, default=Path("data/curated/runs.csv"))
    parser.add_argument("--audit", type=Path, default=Path("data/curated/audit.json"))
    parser.add_argument("--split", type=Path, default=Path("configs/model_split_main_v1.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/main_v1"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("model output exists; refusing to overwrite the evaluated artifact")
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    split = json.loads(args.split.read_text(encoding="utf-8"))
    if audit["curated_csv_sha256"] != _sha256(args.table) or audit["data_version"] != split["data_version"]:
        raise ValueError("table hash or data version differs from audited frozen inputs")
    frame = pd.read_csv(args.table)
    frame = frame.loc[frame.status == RunStatus.SUCCESS.value].copy()
    if frame.empty or (frame.engine_seconds <= 0).any():
        raise ValueError("no valid successful runtimes")

    def split_for(row: pd.Series) -> str:
        groups = split["families"][row.family]
        hits = [name for name in ("train", "calibration", "test") if row.config_id in groups[name]]
        if len(hits) != 1:
            raise ValueError(f"cell has no unique split: {row.family}/{row.config_id}")
        return hits[0]

    frame["split"] = frame.apply(split_for, axis=1)
    group_sizes = frame.groupby(["family", "config_id", "split"]).size()
    if not (group_sizes == 3).all() or frame.split.value_counts().to_dict() != {"train": 36, "calibration": 36, "test": 24}:
        raise ValueError("expected grouped 3-repeat train/calibration/test split")

    features = encoded_features(frame)
    train = frame.split == "train"
    calibration = frame.split == "calibration"
    test = frame.split == "test"
    model = lgb.LGBMRegressor(
        n_estimators=120,
        learning_rate=0.05,
        num_leaves=7,
        min_child_samples=3,
        reg_lambda=1.0,
        random_state=2026,
        n_jobs=1,
        verbosity=-1,
    )
    model.fit(features.loc[train], np.log(frame.loc[train, "engine_seconds"]))
    cal_log_prediction = model.predict(features.loc[calibration])
    cal_rows = frame.loc[calibration, ["family", "config_id", "engine_seconds"]].copy()
    cal_rows["residual"] = np.log(cal_rows.engine_seconds) - cal_log_prediction
    group_scores = cal_rows.groupby(["family", "config_id"]).residual.max().to_numpy()
    upper_log_offset = grouped_upper_quantile(group_scores, alpha=0.1)

    test_rows = frame.loc[test, ["run_id", "family", "config_id", "repeat_id", "engine_seconds", "sla_seconds"]].copy()
    point = np.exp(model.predict(features.loc[test]))
    upper = point * np.exp(upper_log_offset)
    baseline_median = frame.loc[train].groupby("family").engine_seconds.median()
    test_rows["predicted_seconds"] = point
    test_rows["upper_seconds"] = upper
    test_rows["median_baseline_seconds"] = test_rows.family.map(baseline_median)
    test_rows["covered"] = test_rows.engine_seconds <= test_rows.upper_seconds
    test_rows["absolute_percentage_error"] = abs(test_rows.predicted_seconds - test_rows.engine_seconds) / test_rows.engine_seconds
    test_rows["baseline_absolute_percentage_error"] = abs(test_rows.median_baseline_seconds - test_rows.engine_seconds) / test_rows.engine_seconds
    metrics = {
        "data_version": split["data_version"],
        "train_rows": int(train.sum()),
        "calibration_rows": int(calibration.sum()),
        "calibration_groups": len(group_scores),
        "test_rows": int(test.sum()),
        "test_groups": int(test_rows.groupby(["family", "config_id"]).ngroups),
        "upper_log_offset": upper_log_offset,
        "test_mdape_percent": float(100 * test_rows.absolute_percentage_error.median()),
        "median_baseline_test_mdape_percent": float(100 * test_rows.baseline_absolute_percentage_error.median()),
        "test_row_upper_coverage": float(test_rows.covered.mean()),
        "test_group_upper_coverage": float(test_rows.groupby(["family", "config_id"]).covered.all().mean()),
        "mean_upper_width_seconds": float((test_rows.upper_seconds - test_rows.predicted_seconds).mean()),
        "table_sha256": _sha256(args.table),
        "split_sha256": _sha256(args.split),
        "model_spec": "LightGBM log-runtime; 120 trees, 7 leaves, min child 3, learning rate 0.05, L2 1; grouped max-residual split conformal alpha=0.1",
        "limitations": "Only four workload profiles and eight test family/config cells; all physical runs succeeded. Coverage is descriptive, not a validated population guarantee.",
    }
    args.output.mkdir(parents=True)
    model.booster_.save_model(str(args.output / "runtime_model.txt"))
    (args.output / "runtime_meta.json").write_text(
        json.dumps({"feature_names": list(features.columns), "upper_log_offset": upper_log_offset, "table_sha256": metrics["table_sha256"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output / "runtime_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    test_rows.to_csv(args.output / "runtime_test_predictions.csv", index=False)
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
