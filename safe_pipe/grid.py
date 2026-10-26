from __future__ import annotations

import json
from pathlib import Path

from safe_pipe.memory import parse_gb
from safe_pipe.schemas import ConfigurationSpec, DaskNativeConfig

DEFAULT_GRID_PATH = Path(__file__).resolve().parent.parent / "configs" / "dask_grid.json"


def load_grid(path: Path | None = None) -> list[ConfigurationSpec]:
    raw = json.loads((path or DEFAULT_GRID_PATH).read_text(encoding="utf-8"))
    out: list[ConfigurationSpec] = []
    for row in raw["configs"]:
        native = DaskNativeConfig(
            n_workers=row["n_workers"],
            threads_per_worker=row["threads_per_worker"],
            memory_limit=row["memory_limit"],
        )
        out.append(
            ConfigurationSpec(
                config_id=row["config_id"],
                native=native,
                allocated_vcpus=float(native.n_workers * native.threads_per_worker),
                allocated_gb=native.n_workers * parse_gb(native.memory_limit),
            )
        )
    return out


def get_config(config_id: str, path: Path | None = None) -> ConfigurationSpec:
    for spec in load_grid(path):
        if spec.config_id == config_id:
            return spec
    raise KeyError(config_id)
