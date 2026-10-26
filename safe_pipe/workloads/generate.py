from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from safe_pipe.schemas import DatasetManifest, WorkloadFamily, WorkloadSpec

TINY_ROWS = 2_000
DATA_VERSION = "tiny-v1"


def tiny_spec(family: WorkloadFamily) -> tuple[int, int, int]:
    """rows, files, seed. Tiny on purpose: safe on the 8GB coding Mac."""
    return TINY_ROWS, 2, 47 + list(WorkloadFamily).index(family)


def _split_frame(frame: pd.DataFrame, n_files: int) -> list[pd.DataFrame]:
    n = len(frame)
    sizes = [n // n_files + (1 if i < n % n_files else 0) for i in range(n_files)]
    parts: list[pd.DataFrame] = []
    start = 0
    for size in sizes:
        parts.append(frame.iloc[start : start + size])
        start += size
    return parts


def _write_parts(frame: pd.DataFrame, out_dir: Path, n_files: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for i, part in enumerate(_split_frame(frame, n_files)):
        path = out_dir / f"part-{i:04d}.parquet"
        table = pa.Table.from_pandas(part.reset_index(drop=True), preserve_index=False)
        pq.write_table(table, path)
        total += path.stat().st_size
    return total


def _sha256_dir(out_dir: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(out_dir.glob("*.parquet")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def generate_family(
    family: WorkloadFamily,
    dest: Path,
    *,
    n_rows: int | None = None,
    n_files: int | None = None,
    seed: int | None = None,
) -> DatasetManifest:
    rows, files, default_seed = tiny_spec(family)
    n_rows = rows if n_rows is None else n_rows
    n_files = files if n_files is None else n_files
    seed = default_seed if seed is None else seed
    rng = np.random.default_rng(seed)
    family_dir = dest / family.value
    if family_dir.exists():
        for leftover in family_dir.glob("*.parquet"):
            leftover.unlink()

    if family is WorkloadFamily.SCAN_FILTER:
        frame = pd.DataFrame(
            {
                "value": rng.random(n_rows),
                "flag": rng.integers(0, 2, size=n_rows),
            }
        )
        input_bytes = _write_parts(frame, family_dir, n_files)
    elif family is WorkloadFamily.GROUPBY:
        keys = rng.integers(0, max(16, n_rows // 50), size=n_rows)
        frame = pd.DataFrame({"key": keys, "value": rng.normal(size=n_rows)})
        input_bytes = _write_parts(frame, family_dir, n_files)
    elif family is WorkloadFamily.SKEWED_JOIN:
        zipf = rng.zipf(1.5, size=n_rows)
        left = pd.DataFrame({"key": zipf, "payload": rng.random(n_rows)})
        n_right = max(32, n_rows // 20)
        right = pd.DataFrame({"key": np.arange(1, n_right + 1), "dim": rng.random(n_right)})
        left_bytes = _write_parts(left, family_dir / "left", n_files)
        right_bytes = _write_parts(right, family_dir / "right", 1)
        input_bytes = left_bytes + right_bytes
        family_dir.mkdir(parents=True, exist_ok=True)
    elif family is WorkloadFamily.SORT_MERGE:
        frame = pd.DataFrame(
            {
                "key": rng.integers(0, n_rows, size=n_rows),
                "payload": rng.random(n_rows),
            }
        )
        input_bytes = _write_parts(frame, family_dir, n_files)
    else:
        raise ValueError(family)

    if family is WorkloadFamily.SKEWED_JOIN:
        hasher = hashlib.sha256()
        for folder in (family_dir / "left", family_dir / "right"):
            for path in sorted(folder.glob("*.parquet")):
                hasher.update(path.read_bytes())
        sha = hasher.hexdigest()
    else:
        sha = _sha256_dir(family_dir)

    manifest = DatasetManifest(
        data_version=DATA_VERSION,
        family=family,
        seed=seed,
        n_rows=n_rows,
        n_files=n_files,
        input_bytes=input_bytes,
        path=str(family_dir),
        sha256=sha,
    )
    (family_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest


def workload_from_manifest(manifest: DatasetManifest, skew_score: float = 0.0) -> WorkloadSpec:
    return WorkloadSpec(
        family=manifest.family,
        input_bytes=max(manifest.input_bytes, 1),
        estimated_rows=manifest.n_rows,
        file_count=manifest.n_files,
        partition_count=manifest.n_files,
        skew_score=skew_score,
    )


def write_index(dest: Path, manifests: list[DatasetManifest]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    payload = [m.model_dump() for m in manifests]
    (dest / "index.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
