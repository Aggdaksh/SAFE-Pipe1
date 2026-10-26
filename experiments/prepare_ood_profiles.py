"""Save the four training-profile sizes used by the conservative OOD gate."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def main() -> int:
    path = Path("artifacts/main_v1/ood_profiles.json")
    if path.exists():
        raise FileExistsError(path)
    frame = pd.read_csv("data/curated/runs.csv")
    split = json.loads(Path("configs/model_split_main_v1.json").read_text(encoding="utf-8"))
    train = frame.loc[
        frame.apply(lambda row: row.config_id in split["families"][row.family]["train"], axis=1)
    ]
    sizes = {family: int(values.input_bytes.median()) for family, values in train.groupby("family")}
    if len(sizes) != 4:
        raise ValueError("training split must include all four families")
    payload = {
        "data_version": "main-v1",
        "bytes_by_family": sizes,
        "rule": "red for unseen family or >2x input-size shift; yellow for >1.25x; green otherwise",
        "limitation": "one measured profile per family; thresholds are conservative heuristics, not distance-calibrated",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
