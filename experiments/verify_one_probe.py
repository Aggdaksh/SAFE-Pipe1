"""Windows-only synthetic tests and compact-evidence replay. No workload runner.

python -m experiments.verify_one_probe --out reports/one_probe_windows_checks_v1
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_replay():
    from safe_pipe.research.one_probe import (
        Workload, EconomicCase, fingerprint, plan_request, probe_evidence_choice, observed_memory,
    )
    policy = load(ROOT / "configs/research_one_probe_v1.json")
    if policy["admission_enabled"] is not False:
        raise ValueError("This checks-only handoff requires the disabled admission policy")
    expected = load(ROOT / "reports/one_probe_feasibility_20261116/analysis.json")
    for relative, value in expected["input_sha256_lf_text"].items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != value:
            raise ValueError(f"Compact evidence/specification changed: {relative}")
    plan = load(ROOT / "reports/research_stage_b_windows_v1/plan.json")
    a_plan = load(ROOT / "reports/research_stage_a_windows_v1/plan.json")
    source = ROOT / "reports/worker_memory_stage_a_b_v1"
    workers, runs = load(source / "workers.json"), load(source / "runs.json")
    summary = load(ROOT / "reports/research_stage_b_windows_v1/summary.json")
    outcomes = {r["cell_id"]: r for r in summary["probe_outcomes"]}
    by_cell = defaultdict(list)
    for worker in workers:
        by_cell[worker["cell_id"]].append(worker)
    recipes = {r["instance_id"]: r for r in a_plan["recipes"]}
    replay = []
    # Artificially optimistic estimates test that the disabled gate still wins.
    optimistic = EconomicCase(1000.0, 1.0, 1.0, 10.0, "verification-only-not-measured", True)
    for reference in expected["instances"]:
        instance = reference["instance_id"]
        d = plan["reference"]["datasets"][instance]
        r = recipes[instance]
        workload = Workload(instance, d["dataset_sha256"], r["family"], d["fact_rows"], d["dimension_rows"],
                            r["payload_columns"], tuple(d["source_partition_rows"]))
        default = plan_request(workload, policy, f"offline:{instance}", optimistic)
        wanted = reference["policies"]["guarded_default_admission_disabled"]["selected_config"]
        if default["action"] != "select" or default["config_id"] != wanted or default["probe_count"] != 0:
            raise ValueError("Default decision does not match the frozen development replay")
        classified = []
        for probe in reference["probe_decisions"]:
            cell_id = probe["probe_cell_id"]
            row = next(r for r in runs if r["cell_id"] == cell_id)
            outcome = outcomes[cell_id]
            if outcome["signal"] != "quiet" or outcome["quality_issues"] or row["parent_dataset_sha256"] != workload.dataset_sha256:
                raise ValueError("Expected complete, bound Stage B development observation")
            observation = {"request_id": f"offline:{cell_id}", "dataset_sha256": row["parent_dataset_sha256"],
                "workload_sha256": fingerprint(asdict(workload)), "fraction": row["sample_fraction"],
                "sample_dataset_sha256": row["dataset_sha256"], "sampling_method": plan["protocol"]["sampling_method"],
                "sample_seed": row["sample_seed"],
                "fact_rows": plan["sample_metadata"][instance][row["method"]]["fact_rows"],
                "dimension_rows": plan["sample_metadata"][instance][row["method"]]["dimension_rows"],
                "effective_memory_bytes": row["configured_effective_memory_limit_bytes"],
                "n_workers": row["n_workers"], "threads_per_worker": row["threads_per_worker"],
                "quality_complete": not outcome["quality_issues"] and not row["unmatched_worker_evidence"],
                "status": row["run_status"], "result_value": outcome["result_value"],
                "restarts": row["run_observed_restarts_lower_bound"], "workers": by_cell[cell_id],
                "profile_wall_seconds": probe["profile_wall_seconds"]}
            classified_row = probe_evidence_choice(workload, policy, observation)
            if (classified_row["config_id"] != probe["selected_config"]
                    or not math.isclose(classified_row.get("peak_ratio", -1), probe["peak_ratio"], rel_tol=1e-12)):
                raise ValueError("Single-observation classifier disagrees with the standalone analysis")
            classified.append({"probe_cell_id": cell_id, "decision": classified_row,
                               "role": "counterfactual only; admission was not enabled"})
        replay.append({"instance_id": instance, "default_decision": default, "single_observation_counterfactuals": classified})
    termination_records = [observed_memory(w) for w in workers if w["worker_nanny_memory_termination_count"]]
    if (len(termination_records) != 37 or any(r["exact_peak_known"] or r["automatic_regression_target"] for r in termination_records)
            or sum(r["largest_observed_rss_bytes"] > r["sampled_peak_bytes"] for r in termination_records) != 36):
        raise ValueError("Event-aware memory representation does not match retained evidence")
    return {"default_decisions_checked": len(replay), "single_observation_decisions_checked": sum(len(r["single_observation_counterfactuals"]) for r in replay),
            "independence_note": "Each decision sees one observation; these are NOT statistically independent workloads.",
            "termination_records_checked": len(termination_records), "replay": replay,
            "admission_enabled": False, "physical_attempts_executed": 0, "new_pilot_enabled": False}


def verify(out: Path):
    if platform.system() != "Windows":
        raise ValueError("Execute project runtime checks on Windows; this Mac is for edits/static checks only")
    out = out.resolve()
    reports_root = (ROOT / "reports").resolve()
    if (out == reports_root or not out.is_relative_to(reports_root)
            or (out.exists() and (not out.is_dir() or any(out.iterdir())))):
        raise ValueError("Choose a new, empty subdirectory of this repository's reports directory")
    out.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / p for p in ("safe_pipe/research/one_probe.py", "experiments/verify_one_probe.py",
        "tests/test_one_probe.py", "configs/research_one_probe_v1.json")]
    initial = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    # Override the repository's own -q so double-quiet mode cannot hide the
    # passed-test summary we retain and verify below.
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "tests/test_one_probe.py"]
    tested = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    output = tested.stdout + tested.stderr
    (out / "WINDOWS_TEST_OUTPUT.txt").write_text(output, encoding="utf-8")
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "platform": platform.system(),
              "python": sys.version, "source_sha256": initial, "test_exit_code": tested.returncode,
              "scope": "Synthetic decision checks and existing compact evidence only; no dataset/job/model execution."}
    try:
        if tested.returncode != 0:
            raise ValueError("Targeted tests failed; preserve output and fix before proceeding")
        passed = re.search(r"(\d+) passed", output)
        if passed is None:
            raise ValueError("Cannot verify the targeted passed-test count from retained output")
        result["tests_passed"] = int(passed[1])
        result.update(compact_replay())
        if any(digest(ROOT / p) != value for p, value in initial.items()):
            raise ValueError("Source changed during verification")
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        result.update(git_revision=revision.stdout.strip(), verification_pass=True)
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        result.update(verification_pass=False, error=f"{type(exc).__name__}: {exc}")
    (out / "verification.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "README.md").write_text(
        "# One-probe Windows verification\n\n"
        f"Verification: {'PASS' if result['verification_pass'] else 'FAIL — inspect verification.json'}. "
        f"Targeted tests passed: {result.get('tests_passed', 'not verified')}.\n\n"
        "See WINDOWS_TEST_OUTPUT.txt and verification.json. These are software checks and existing-evidence replays, "
        "not fresh policy experiments. Probe admission and the proposed 48-attempt pilot remain disabled.\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.out)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Verification not started: {exc}\n")
    print(json.dumps({k: result.get(k) for k in ("verification_pass", "tests_passed", "default_decisions_checked", "admission_enabled", "new_pilot_enabled", "error")}))
    if not result["verification_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
