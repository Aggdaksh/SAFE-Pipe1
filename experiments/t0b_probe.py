"""T0b — 50 MB 1g vs 2g probe. 16 GB experiment PC only. Not for the 8 GB Mac."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T0b probe (16GB PC only)")
    parser.add_argument(
        "--i-am-on-16gb",
        action="store_true",
        help="Required. Confirms this is not the 8GB coding Mac.",
    )
    args = parser.parse_args(argv)
    if not args.i_am_on_16gb:
        print(
            "T0b starts Dask workers at 1GB and 2GB. That is for the 16GB experiment PC.\n"
            "Re-run with --i-am-on-16gb on that machine after T0 succeeds.",
            file=sys.stderr,
        )
        return 2
    print("T0b Dask body waits until official T0 passes on the 16GB PC.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
