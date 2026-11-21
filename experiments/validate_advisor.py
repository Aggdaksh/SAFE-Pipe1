"""Prepare and collect an isolated prospective main-v1 advisor study on Windows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from safe_pipe.validation.study import (
    acknowledge_cleanup, prepare_study, resolve_pending, run_batch, study_status,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="Verify originals and freeze advice before collecting results")
    prepare.add_argument("--study-dir", type=Path, required=True)
    prepare.add_argument("--run-set-id", required=True)
    prepare.add_argument("--data-dir", type=Path, default=Path("data/generated/main-v1"))
    prepare.add_argument("--verification", type=Path, required=True, help="Passing Windows verification.json for these exact sources/environment")
    prepare.add_argument("--host-scope", choices=("original-host", "transfer"), required=True)
    prepare.add_argument("--host-attestation", required=True, help="Operator's basis for host identity and controlled conditions; not automatic verification")
    prepare.add_argument("--timeout", type=float, default=120.0, help="Original collector future-result wait timeout, not total lifecycle timeout")
    run = sub.add_parser("run", help="Run at most a bounded batch, resuming only unstarted cells")
    run.add_argument("--study-dir", type=Path, required=True)
    run.add_argument("--max-jobs", type=int, default=16)
    status = sub.add_parser("status", help="Audit saved records without executing workloads")
    status.add_argument("--study-dir", type=Path, required=True)
    for name, help_text in (
        ("resolve", "Record an interrupted pending attempt as aborted without retrying it"),
        ("acknowledge-cleanup", "Confirm workers from an errored/interrupted terminal attempt are stopped"),
    ):
        recovery = sub.add_parser(name, help=help_text)
        recovery.add_argument("--study-dir", type=Path, required=True)
        recovery.add_argument("--attempt-id", required=True)
        recovery.add_argument("--reason", required=True)
        recovery.add_argument("--workers-stopped", action="store_true", required=True,
                              help="Confirm this study's worker processes are stopped before continuing")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            frozen = prepare_study(study_dir=args.study_dir, run_set_id=args.run_set_id,
                data_dir=args.data_dir, host_scope=args.host_scope, host_attestation=args.host_attestation,
                verification=args.verification, timeout_s=args.timeout)
            result = {"run_set_id": frozen["run_set_id"], "study_id": frozen["study_id"],
                      "planned_cells": len(frozen["plan"]), "physical_attempts": 0,
                      "original_environment_comparison": frozen["original_environment_comparison"]}
        elif args.command == "run":
            result = run_batch(args.study_dir, max_jobs=args.max_jobs)
        elif args.command == "status":
            result = study_status(args.study_dir)
        else:
            action = resolve_pending if args.command == "resolve" else acknowledge_cleanup
            result = action(args.study_dir, attempt_id=args.attempt_id, reason=args.reason,
                            workers_stopped=args.workers_stopped)
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        parser.exit(1, f"Study stopped: {exc}\n")
    except KeyboardInterrupt:
        parser.exit(130, "Interrupted. Inspect status and confirm owned workers stopped before recovery.\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
