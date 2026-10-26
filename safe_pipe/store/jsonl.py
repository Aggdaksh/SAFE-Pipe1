from __future__ import annotations

import json
from pathlib import Path

from safe_pipe.schemas import RunResult


def append_run(path: Path, result: RunResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(result.model_dump_json() + "\n")


def read_runs(path: Path) -> list[RunResult]:
    if not path.exists():
        return []
    rows: list[RunResult] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(RunResult.model_validate(json.loads(line)))
    return rows
