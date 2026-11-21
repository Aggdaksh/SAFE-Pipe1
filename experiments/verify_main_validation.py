"""Verify the main-advisor changes on Windows before preparing a fresh study.

This runs the software suite, including its tiny Dask integration fixtures.
It does not generate the main datasets, train a model, or run the 96-cell study.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def fingerprints(root: Path = ROOT) -> dict[str, str]:
    """Only named source/evidence directories; never inspect environment secrets."""
    paths = [root / "pyproject.toml", root / "data/curated/runs.csv"]
    for directory, pattern in (("safe_pipe", "*.py"), ("experiments", "*.py"),
                               ("tests", "*.py"), ("configs", "*.json"),
                               ("artifacts/main_v1", "*.json"),
                               ("artifacts/main_v1", "*.txt")):
        paths.extend((root / directory).rglob(pattern))
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(
            p.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for p in sorted(set(paths))
    }


def test_counts(path: Path) -> dict[str, int]:
    document = ET.parse(path).getroot()
    cases = list(document.iter("testcase"))
    failed = sum(c.find("failure") is not None for c in cases)
    errors = sum(c.find("error") is not None for c in cases)
    skipped = sum(c.find("skipped") is not None for c in cases)
    return {"collected": len(cases), "passed": len(cases) - failed - errors - skipped,
            "failed": failed, "errors": errors, "skipped": skipped}


def verify(out: Path) -> dict:
    # The guard precedes all project imports, subprocesses and filesystem writes.
    if platform.system() != "Windows":
        raise ValueError("Run software checks on Windows. This Mac is for editing/static checks only.")
    from safe_pipe.validation.study import environment_snapshot

    out = out.resolve()
    reports = (ROOT / "reports").resolve()
    if out == reports or not out.is_relative_to(reports) or out.exists():
        raise ValueError("Choose a NEW directory beneath this repository's reports/ directory.")
    before = fingerprints()
    environment = environment_snapshot()
    out.mkdir(parents=True, exist_ok=False)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    result = {
        "schema_version": 1, "verification_pass": False,
        "created_utc": datetime.now(timezone.utc).isoformat(), "git_revision": revision,
        "source_sha256_lf": before, "environment": environment,
        "scope": "Full software suite including tiny Dask integration fixtures; no main-matrix runs or training.",
        "fresh_study_cells_executed": 0,
    }
    commands = [
        ("PIP_CHECK.txt", [sys.executable, "-m", "pip", "check"]),
        ("WINDOWS_TEST_OUTPUT.txt", [sys.executable, "-m", "pytest", "-o", "addopts=",
          "-q", "--tb=short", "--junitxml", str(out / "tests.xml"), "tests"]),
    ]
    result["commands"] = []
    try:
        for log_name, command in commands:
            # Output streams directly to disk, retaining diagnostics if interrupted.
            with (out / log_name).open("x", encoding="utf-8") as log:
                completed = subprocess.run(command, cwd=ROOT, stdout=log,
                                           stderr=subprocess.STDOUT, timeout=1800)
            result["commands"].append({"argv": command, "exit_code": completed.returncode,
                                       "log": log_name})
            if completed.returncode != 0:
                raise ValueError(f"Software verification failed; inspect {log_name}.")
        result["tests"] = test_counts(out / "tests.xml")
        counts = result["tests"]
        if counts["passed"] == 0 or counts["failed"] or counts["errors"] or counts["skipped"]:
            raise ValueError("Expected the complete installed suite to pass with no skipped tests.")
        if fingerprints() != before or environment_snapshot() != environment:
            raise ValueError("Source, frozen evidence or execution environment changed during checks.")
        result["verification_pass"] = True
    except (Exception, KeyboardInterrupt) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    (out / "verification.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    status = "PASS" if result["verification_pass"] else "FAIL / INCOMPLETE"
    (out / "README.md").write_text(
        f"# Windows advisor-validation software verification\n\nResult: **{status}**.\n\n"
        "See verification.json, WINDOWS_TEST_OUTPUT.txt and tests.xml for exact counts and source identity. "
        "Tiny integration jobs are software checks, not fresh main-study measurements. "
        "No model was trained. A passing receipt is required before preparing the study.\n",
        encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.out)
    except (ValueError, OSError, ImportError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Verification not started: {exc}\n")
    print(json.dumps({key: result.get(key) for key in
                      ("verification_pass", "tests", "fresh_study_cells_executed", "error")}))
    return 0 if result["verification_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
