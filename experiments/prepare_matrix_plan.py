"""Freeze a randomized order for the 96 scored physical Dask jobs."""

from __future__ import annotations

import json
import random
from pathlib import Path

from safe_pipe.matrix import planned_cells


def main() -> int:
    path = Path("configs/matrix_plan_main_v1.json")
    if path.exists():
        raise FileExistsError(path)
    cells = planned_cells()
    random.Random(2026).shuffle(cells)
    payload = {"data_version": "main-v1", "shuffle_seed": 2026, "cells": cells}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(cells)} cells to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
