"""Generate and fingerprint the four main experiment datasets once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from safe_pipe.schemas import WorkloadFamily
from safe_pipe.workloads.generate import generate_family, verify_manifest, write_index


# Rows were calibrated from the physical T0b pilots in reports/t0b.md.
ROWS = {
    WorkloadFamily.SCAN_FILTER: 23_320_000,
    WorkloadFamily.GROUPBY: 14_970_000,
    WorkloadFamily.SKEWED_JOIN: 17_040_000,
    WorkloadFamily.SORT_MERGE: 12_770_000,
}
DATA_VERSION = "main-v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/generated/main-v1"))
    parser.add_argument("--index", type=Path, default=Path("configs/datasets_main_v1.json"))
    args = parser.parse_args()
    if args.output.exists() or args.index.exists():
        parser.error("main-v1 dataset or index already exists; refusing to rewrite frozen data")
    manifests = []
    for family in WorkloadFamily:
        manifest = generate_family(
            family,
            args.output,
            n_rows=ROWS[family],
            n_files=16,
            data_version=DATA_VERSION,
        )
        verify_manifest(manifest, args.output / family.value)
        if not 150_000_000 <= manifest.input_bytes <= 250_000_000:
            raise ValueError(f"{family.value} is outside the 150–250 MB target: {manifest.input_bytes}")
        manifests.append(manifest)
        print(json.dumps({"family": family.value, "rows": manifest.n_rows, "bytes": manifest.input_bytes, "sha256": manifest.sha256}), flush=True)
    write_index(args.output, manifests)
    args.index.parent.mkdir(parents=True, exist_ok=True)
    args.index.write_text(json.dumps([m.model_dump() for m in manifests], indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
