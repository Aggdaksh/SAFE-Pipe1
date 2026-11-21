"""Evaluate saved pre-run recommendations against a fresh study journal."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from safe_pipe.validation.evaluate import export_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New report directory; existing output is never overwritten")
    parser.add_argument("--allow-partial", action="store_true", help="Write an explicitly incomplete progress report")
    args = parser.parse_args(argv)
    try:
        summary = export_report(args.study_dir, args.output, allow_partial=args.allow_partial)
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps({"output": str(args.output), "completion": summary["completion"],
                      "acceptance": summary["acceptance"]}, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
