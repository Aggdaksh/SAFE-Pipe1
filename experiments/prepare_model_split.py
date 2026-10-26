"""Freeze grouped train/calibration/test cells before fitting the runtime model."""

from __future__ import annotations

import json
import random
from pathlib import Path

from safe_pipe.grid import load_grid
from safe_pipe.schemas import WorkloadFamily


def main() -> int:
    path = Path("configs/model_split_main_v1.json")
    if path.exists():
        raise FileExistsError(path)
    rng = random.Random(2027)
    configs = [spec.config_id for spec in load_grid()]
    families = {}
    for family in WorkloadFamily:
        shuffled = configs.copy()
        rng.shuffle(shuffled)
        families[family.value] = {"train": shuffled[:3], "calibration": shuffled[3:6], "test": shuffled[6:]}
    payload = {
        "data_version": "main-v1",
        "seed": 2027,
        "group": "family + config_id; all three repeats of each cell remain in one split",
        "families": families,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote grouped split to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
