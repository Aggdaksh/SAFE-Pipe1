"""Versioned data and deliberately unvalidated proxies for the probing pilot.

All sampling is based on input metadata, never full-job performance. Tail probes
are biased experiments, not approximate answers or proven faithful simulations.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

DATA_VERSION = "partition-probe-v1"
FAMILIES = {"groupby", "skewed_join"}


def _integer(value: Any, name: str, minimum: int = 1) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _fraction(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be a finite fraction")
    result = float(value)
    if not math.isfinite(result) or not 0 <= result <= 1 or (positive and result == 0):
        raise ValueError(f"{name} must be {'> 0 and ' if positive else ''}<= 1")
    return result


def _recipe(recipe: dict) -> dict:
    allowed = {"instance_id", "family", "n_rows", "n_files", "seed", "n_keys",
               "hot_fraction", "payload_columns", "partition_imbalance", "generation_mode"}
    if set(recipe) - allowed:
        raise ValueError(f"unknown recipe fields: {sorted(set(recipe) - allowed)}")
    family = recipe.get("family", "groupby")
    if family not in FAMILIES:
        raise ValueError(f"family must be one of {sorted(FAMILIES)}")
    mode = recipe.get("generation_mode", "legacy_interleaved")
    if mode not in {"legacy_interleaved", "independent_columns_v1"}:
        raise ValueError("unknown generation_mode")
    normalized = {
        "family": family,
        "n_rows": _integer(recipe.get("n_rows", 2000), "n_rows"),
        "n_files": _integer(recipe.get("n_files", 4), "n_files"),
        "seed": _integer(recipe.get("seed", 47), "seed", 0),
        "n_keys": _integer(recipe.get("n_keys", 128), "n_keys", 2),
        "hot_fraction": _fraction(recipe.get("hot_fraction", 0.0), "hot_fraction"),
        "payload_columns": _integer(recipe.get("payload_columns", 4), "payload_columns"),
        "partition_imbalance": _fraction(recipe.get("partition_imbalance", 0.0), "partition_imbalance"),
        "generation_mode": mode,
    }
    if normalized["n_rows"] < normalized["n_files"]:
        raise ValueError("n_rows must be >= n_files")
    instance_id = recipe.get("instance_id")
    if instance_id is None:
        instance_id = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()[:16]
    if not isinstance(instance_id, str) or not instance_id.strip():
        raise ValueError("instance_id must be a nonempty string")
    return {"instance_id": instance_id, **normalized}


def _empty_dest(dest: Path) -> None:
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise FileExistsError(f"refusing to overwrite nonempty destination: {dest}")
    dest.mkdir(parents=True, exist_ok=True)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _file_record(dest: Path, path: Path, relation: str) -> dict:
    parquet = pq.ParquetFile(path)
    return {
        "path": path.relative_to(dest).as_posix(),
        "relation": relation,
        "rows": parquet.metadata.num_rows,
        "compressed_bytes": path.stat().st_size,
        # Parquet's uncompressed encoded bytes, not peak pandas/Dask task memory.
        "logical_bytes": sum(parquet.metadata.row_group(i).total_byte_size
                             for i in range(parquet.metadata.num_row_groups)),
        "sha256": _sha(path),
    }


def _write(dest: Path, frame: pd.DataFrame, relation: str, index: int) -> dict:
    directory = dest / relation
    directory.mkdir(exist_ok=True)
    path = directory / f"part-{index:04d}.parquet"
    pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), path,
                   compression="snappy", row_group_size=65_536)
    return _file_record(dest, path, relation)


def _counts(rows: int, files: int, imbalance: float = 0.0) -> list[int]:
    extra = int((rows - files) * imbalance)
    ordinary = rows - extra
    counts = [ordinary // files + (i < ordinary % files) for i in range(files)]
    counts[0] += extra
    return counts


def _finish(dest: Path, manifest: dict, started: float) -> dict:
    files = manifest["files"]
    manifest.update({
        "data_version": DATA_VERSION,
        "path": str(dest.resolve()),
        "n_rows": sum(f["rows"] for f in files if f["relation"] == "left"),
        "n_right_rows": sum(f["rows"] for f in files if f["relation"] == "right"),
        "n_files": len(files),
        "compressed_bytes": sum(f["compressed_bytes"] for f in files),
        "logical_bytes": sum(f["logical_bytes"] for f in files),
        "logical_bytes_definition": "Parquet uncompressed encoded row-group bytes; not RSS/working set",
        "sha256": hashlib.sha256(json.dumps(
            [(f["path"], f["sha256"]) for f in files], separators=(",", ":")
        ).encode()).hexdigest(),
        "preparation_seconds": time.perf_counter() - started,
    })
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    return manifest


def generate_instance(dest: Path, recipe: dict) -> dict:
    """Generate a fresh instance, holding at most one input partition in memory."""
    started = time.perf_counter()
    dest = Path(dest)
    recipe = _recipe(recipe)
    _empty_dest(dest)
    rng = np.random.default_rng(recipe["seed"])
    # Independent streams preserve the same ordered rows when only file
    # boundaries change. The legacy generator remains available for old recipes.
    streams = [rng] * (recipe["payload_columns"] + 3)
    if recipe["generation_mode"] == "independent_columns_v1":
        streams = [np.random.default_rng(s) for s in
                   np.random.SeedSequence(recipe["seed"]).spawn(recipe["payload_columns"] + 3)]
    key_rng, hot_rng, *remaining = streams
    payload_rngs, rng = remaining[:-1], remaining[-1]
    files: list[dict] = []
    for index, rows in enumerate(_counts(recipe["n_rows"], recipe["n_files"],
                                        recipe["partition_imbalance"])):
        keys = key_rng.integers(1, recipe["n_keys"], size=rows, dtype=np.int64)
        keys[hot_rng.random(rows) < recipe["hot_fraction"]] = 0
        frame = pd.DataFrame({"key": keys})
        for col in range(recipe["payload_columns"]):
            frame[f"payload_{col}"] = payload_rngs[col].random(rows)
        file_record = _write(dest, frame, "left", index)
        file_record["hot_key_rows"] = int(np.count_nonzero(keys == 0))
        files.append(file_record)
    if recipe["family"] == "skewed_join":
        offset = 0
        # Unique-key dimension: no accidental quadratic join explosion.
        for index, rows in enumerate(_counts(recipe["n_keys"],
                                            min(recipe["n_files"], recipe["n_keys"]))):
            frame = pd.DataFrame({"key": np.arange(offset, offset + rows, dtype=np.int64),
                                  "dim": rng.random(rows) + 0.5})
            files.append(_write(dest, frame, "right", index))
            offset += rows
    return _finish(dest, {
        "instance_id": recipe["instance_id"], "parent_instance_id": recipe["instance_id"],
        "family": recipe["family"], "method": "full", "fraction": 1.0,
        "recipe": recipe, "files": files,
        "operator_contract": "groupby sum with split_out/task shuffle or unique-dimension inner hash join; all payloads consumed",
        "sampling": {"biased": False, "budget_scope": "primary left relation", "seed": recipe["seed"]},
    }, started)


def load_manifest(dataset_dir: Path, *, verify: bool = False) -> dict:
    """Read metadata; optionally verify every data hash (charge this I/O separately)."""
    dataset_dir = Path(dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text())
    if manifest.get("data_version") != DATA_VERSION:
        raise ValueError("unsupported research dataset version")
    declared = [file["path"] for file in manifest["files"]]
    if len(declared) != len(set(declared)):
        raise ValueError("manifest contains duplicate data paths")
    if verify:
        actual = {path.relative_to(dataset_dir).as_posix()
                  for path in dataset_dir.rglob("*.parquet")}
        if actual != set(declared):
            raise ValueError("dataset file inventory does not match manifest")
    for file in manifest["files"]:
        path = dataset_dir / file["path"]
        if not path.resolve().is_relative_to(dataset_dir.resolve()):
            raise ValueError("manifest path escapes dataset")
        if verify and (not path.is_file() or _sha(path) != file["sha256"]):
            raise ValueError(f"dataset hash mismatch: {file['path']}")
    return manifest


def _tail_counts(counts: np.ndarray, budget: int) -> np.ndarray:
    """Allocate exact budget with squared-size weights and capacity constraints."""
    selected = np.zeros(len(counts), dtype=np.int64)
    remaining = budget
    while remaining:
        capacity = counts - selected
        active = capacity > 0
        weights = np.where(active, counts.astype(float) ** 2, 0.0)
        desired = remaining * weights / weights.sum()
        increments = np.minimum(capacity, np.floor(desired).astype(np.int64))
        if not increments.any():
            increments[int(np.argmax(np.where(active, desired, -1.0)))] = 1
        selected += increments
        remaining -= int(increments.sum())
    return selected


def make_probe(source_dir: Path, dest: Path, fraction: float, method: str, seed: int) -> dict:
    """Create input-only probes. Join dimension is retained and charged in full.

    The budget is the exact number of fact/left rows; total bytes are *not* matched
    and must be reported. Tail probes overrepresent larger source partitions.
    """
    started = time.perf_counter()
    fraction = _fraction(fraction, "fraction", positive=True)
    seed = _integer(seed, "seed", 0)
    if method not in {"full", "uniform", "partition_tail"}:
        raise ValueError("unknown probe method")
    if method == "full" and fraction != 1:
        raise ValueError("full probes require fraction=1")
    source_dir, dest = Path(source_dir), Path(dest)
    source = load_manifest(source_dir, verify=True)
    if source["method"] != "full":
        raise ValueError("probes must be derived from the original full instance")
    if dest.resolve() == source_dir.resolve():
        raise ValueError("probe destination must differ from source")
    _empty_dest(dest)
    primary = [f for f in source["files"] if f["relation"] == "left"]
    counts = np.array([f["rows"] for f in primary], dtype=np.int64)
    budget = min(int(counts.sum()), max(1, round(int(counts.sum()) * fraction)))
    rng = np.random.default_rng(seed)
    selected = (_tail_counts(counts, budget) if method == "partition_tail"
                else rng.multivariate_hypergeometric(counts, budget))
    records: list[dict] = []
    for index, (file, keep) in enumerate(zip(primary, selected, strict=True)):
        frame = pd.read_parquet(source_dir / file["path"])
        indices = np.sort(rng.choice(len(frame), size=int(keep), replace=False))
        records.append(_write(dest, frame.iloc[indices].reset_index(drop=True), "left", index))
    for file in source["files"]:
        if file["relation"] == "right":
            target = dest / file["path"]
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source_dir / file["path"], target)
            records.append(_file_record(dest, target, "right"))
    sample_spec = json.dumps([source["sha256"], method, fraction, seed], separators=(",", ":"))
    return _finish(dest, {
        "instance_id": source["instance_id"] + ":" + hashlib.sha256(sample_spec.encode()).hexdigest()[:12],
        "parent_instance_id": source["instance_id"], "parent_sha256": source["sha256"],
        "family": source["family"], "recipe": source["recipe"],
        "method": method, "fraction": fraction, "files": records,
        "operator_contract": source["operator_contract"],
        "sampling": {
            "seed": seed, "budget_scope": "primary left relation only; full right dimension retained",
            "target_left_rows": budget, "source_left_rows": int(counts.sum()),
            "source_partition_rows": counts.tolist(), "selected_partition_rows": selected.tolist(),
            "biased": method == "partition_tail",
            "selection_information": "source Parquet row-count metadata only; no job outcomes",
            "fidelity_validated": False,
            "limitations": "metadata partition sizes do not establish post-shuffle sizes or hot-key fidelity; no runtime/ranking guarantee",
        },
    }, started)


def build_probe_result(dataset_dir: Path) -> Any:
    """Lazy scalar that requires all payloads and the declared shuffle operation."""
    import dask.dataframe as dd

    dataset_dir = Path(dataset_dir)
    manifest = load_manifest(dataset_dir)
    recipe = manifest["recipe"]
    payloads = [f"payload_{i}" for i in range(recipe["payload_columns"])]
    left = dd.read_parquet(str(dataset_dir / "left" / "*.parquet"), aggregate_files=False)
    if manifest["family"] == "groupby":
        grouped = left.groupby("key")[payloads].sum(
            split_out=recipe["n_files"], shuffle_method="tasks")
        return grouped.sum().sum()
    right = dd.read_parquet(str(dataset_dir / "right" / "*.parquet"), aggregate_files=False)
    joined = left.merge(right, on="key", how="inner", broadcast=False,
                        shuffle_method="tasks", npartitions=recipe["n_files"])
    return (joined[payloads].sum(axis=1) * joined["dim"]).sum()


def reference_value(dataset_dir: Path) -> float:
    """Small-data correctness oracle. Not a runtime predictor or large-data runner."""
    dataset_dir = Path(dataset_dir)
    manifest = load_manifest(dataset_dir)
    payloads = [f"payload_{i}" for i in range(manifest["recipe"]["payload_columns"])]
    left = pd.read_parquet(dataset_dir / "left")
    if manifest["family"] == "groupby":
        return float(left.groupby("key")[payloads].sum().sum().sum())
    right = pd.read_parquet(dataset_dir / "right")
    joined = left.merge(right, on="key", how="inner", validate="many_to_one")
    return float((joined[payloads].sum(axis=1) * joined["dim"]).sum())
