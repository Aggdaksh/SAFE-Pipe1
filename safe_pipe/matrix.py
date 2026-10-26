from __future__ import annotations

from safe_pipe.grid import load_grid
from safe_pipe.schemas import WorkloadFamily

N_REPEATS = 3


def planned_cells(n_repeats: int = N_REPEATS) -> list[dict[str, str | int]]:
    cells: list[dict[str, str | int]] = []
    configs = load_grid()
    for family in WorkloadFamily:
        for spec in configs:
            for repeat_id in range(1, n_repeats + 1):
                cells.append(
                    {
                        "family": family.value,
                        "config_id": spec.config_id,
                        "repeat_id": repeat_id,
                    }
                )
    return cells
