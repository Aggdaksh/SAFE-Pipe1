from __future__ import annotations

from pathlib import Path

import pandas as pd

from safe_pipe.schemas import WorkloadFamily


def _read_parts(folder: Path) -> pd.DataFrame:
    files = sorted(folder.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(folder)
    return pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)


def execute_pandas(family: WorkloadFamily, dataset_dir: Path) -> float:
    """Run the logical DAG in pandas. Used on the 8GB Mac; Dask path is for the 16GB PC."""
    if family is WorkloadFamily.SCAN_FILTER:
        frame = _read_parts(dataset_dir)
        return float(frame.loc[frame["value"] > 0.5, "value"].mean())
    if family is WorkloadFamily.GROUPBY:
        frame = _read_parts(dataset_dir)
        return float(frame.groupby("key", sort=False)["value"].sum().mean())
    if family is WorkloadFamily.SKEWED_JOIN:
        left = _read_parts(dataset_dir / "left")
        right = _read_parts(dataset_dir / "right")
        merged = left.merge(right, on="key", how="inner")
        return float(merged["payload"].sum()) if len(merged) else 0.0
    if family is WorkloadFamily.SORT_MERGE:
        frame = _read_parts(dataset_dir)
        return float(frame.sort_values("key")["payload"].iloc[len(frame) // 2])
    raise ValueError(family)
