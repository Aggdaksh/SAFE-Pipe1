"""Export existing Stage A/B worker lifetimes; stdlib only, no Dask execution.

Run: python -m experiments.export_worker_memory --out reports/worker_memory_stage_a_b_v1
Raw inputs are opened read-only. Public evidence uses lifetime indices, not PID/address/path.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


WORKER_FIELDS = (
    "started_utc", "last_sample_utc", "effective_memory_limit_bytes",
    "baseline_rss_bytes", "peak_rss_bytes", "peak_managed_total_bytes",
    "peak_managed_in_memory_bytes", "peak_spilled_memory_bytes", "peak_spilled_disk_bytes",
    "cumulative_spill_write_bytes", "cumulative_spill_write_count", "samples",
    "sampling_errors", "paused_samples", "measurement_window_s", "status_counts", "memory_settings",
)
SETTINGS = ("target", "spill", "pause", "terminate", "monitor-interval", "max-spill")


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_hash(value):
    return hashlib.sha256(compact(value).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: compact(v) if isinstance(v, (dict, list)) else v for k, v in row.items()}
                         for row in rows)


def pair_snapshots(workers, snapshots):
    """Exact matches only; preserve divergent/diagnostic-only records as separate rows."""
    remaining = list(snapshots)
    pairs = []
    for worker in workers:
        match = next((i for i, (_, snapshot) in enumerate(remaining) if snapshot == worker), None)
        pairs.append((worker, remaining.pop(match)[0] if match is not None else None, "telemetry"))
    pairs.extend((snapshot, path, "diagnostic_only") for path, snapshot in remaining)
    return sorted(pairs, key=lambda p: (p[0].get("started_utc") or "", canonical_hash(p[0]), str(p[1])))


def event_worker_index(workers, *, pid=None, address=None, utc=None):
    """Never guess a lifetime from PID alone when reuse remains ambiguous."""
    if pid is None and address is None:
        return None
    candidates = [i for i, worker in enumerate(workers)
                  if (pid is None or worker.get("pid") == pid)
                  and (address is None or worker.get("address") == address)]
    if len(candidates) > 1 and utc:
        started = [i for i in candidates if workers[i].get("started_utc") is not None
                   and workers[i]["started_utc"] <= utc]
        if started:
            latest = max(workers[i]["started_utc"] for i in started)
            candidates = [i for i in started if workers[i]["started_utc"] == latest]
    return candidates[0] if len(candidates) == 1 else None


def safe_event(event, kind, source):
    """Whitelist exported evidence, keeping a hash for linkage to the retained raw event."""
    return {"kind": kind, "source": source, "utc": event.get("utc"), "phase": event.get("phase"),
            "raw_event_sha256": canonical_hash(event),
            **{k: event.get(k) for k in ("exit_status", "signal") if k in event},
            **({"rss_bytes": (event.get("details") or {}).get("rss")}
               if kind == "nanny_memory_restart" else {})}


def collect_stage(repo, stage, expected_raw_hash, expected_plan_hash, tracked):
    root = repo / f"data/probes/windows-stage-{stage.lower()}-v1"
    published = repo / f"reports/research_stage_{stage.lower()}_windows_v1"
    issues = []

    def problem(kind, **context):
        issues.append({"kind": kind, **context})

    def tracked_json(path):
        if not path.is_file():
            problem("missing_file", file_role=path.name)
            return None
        tracked[path] = file_hash(path)
        return read_json(path)

    plan = tracked_json(root / "plan.json")
    audit = tracked_json(published / "completion_audit.json")
    public_plan = tracked_json(published / "plan.json")
    runs_path = root / "runs.jsonl"
    if plan is None or not runs_path.is_file():
        problem("missing_required_plan_or_raw_records")
        return [], [], {"stage": stage, "issues": issues, "integrity_pass": False}
    tracked[runs_path] = file_hash(runs_path)
    records = read_lines(runs_path)
    plan_hash = canonical_hash(plan)
    if plan_hash != expected_plan_hash or public_plan != plan:
        problem("plan_hash_or_published_plan_mismatch")
    if tracked[runs_path] != expected_raw_hash:
        problem("raw_records_hash_mismatch")
    if stage == "B" and audit and (audit.get("plan_sha256") != plan_hash
                                   or audit.get("reference_sha256") != plan.get("reference_sha256")):
        problem("completion_audit_plan_or_reference_mismatch")
    for name in ("protocol", "reference"):
        if name in plan and canonical_hash(plan[name]) != plan.get(name + "_sha256"):
            problem("embedded_hash_mismatch", object=name)
    cells = {c["cell_id"]: c for c in plan["cells"]}
    expected_count = 48 if stage == "A" else 96
    if (len(cells) != expected_count or len(records) != expected_count
            or {r.get("cell_id") for r in records} != set(cells)
            or len({r.get("run_id") for r in records}) != len(records)):
        problem("run_or_cell_coverage_mismatch")
    for c in cells.values():
        if canonical_hash({k: v for k, v in c.items() if k != "cell_id"})[:24] != c["cell_id"]:
            problem("cell_hash_mismatch", cell_id=c["cell_id"])
    statuses = dict(Counter(r.get("status") for r in records))
    if audit and (audit.get("recorded") != len(records) or audit.get("statuses") != statuses):
        problem("completion_audit_count_or_status_mismatch")

    output, run_output = [], []
    verified_files = raw_nanny_verified = 0
    snapshot_matches = diagnostic_only = telemetry_only = 0
    missing = Counter()
    for record in records:
        cell_id = record.get("cell_id")
        cell = cells.get(cell_id, {})
        if record.get("plan_sha256") != plan_hash:
            problem("run_plan_hash_mismatch", cell_id=cell_id)
        for key in ("instance_id", "target_config_id", "method", "repeat_id", "run_config"):
            if record.get(key) != cell.get(key):
                problem("run_cell_identity_mismatch", cell_id=cell_id, field=key)
        if record.get("config") != cell.get("run_config"):
            problem("effective_configuration_mismatch", cell_id=cell_id)
        dataset = record.get("dataset") or {}
        fraction = record.get("fraction", dataset.get("fraction"))
        expected_fraction = cell.get("fraction", plan.get("fraction"))
        if fraction != expected_fraction:
            problem("sample_fraction_mismatch", cell_id=cell_id)
        diagnostic = record.get("diagnostics") or {}
        telemetry = record.get("telemetry") or {}
        if diagnostic.get("retained") is not True:
            problem("diagnostics_not_marked_retained", cell_id=cell_id)
        if telemetry.get("worker_count_observed") != len(telemetry.get("workers") or []):
            problem("telemetry_worker_count_mismatch", cell_id=cell_id)
        # Resolve only declared evidence under this raw root; never write there.
        directory = (root / diagnostic.get("directory", "__missing__")).resolve()
        if not directory.is_relative_to(root.resolve()):
            raise ValueError("Diagnostic directory escaped raw root")
        manifest = diagnostic.get("files")
        if manifest is None:
            problem("missing_diagnostic_manifest", cell_id=cell_id)
        for entry in manifest or []:
            path = (directory / entry["file"]).resolve()
            if not path.is_relative_to(directory):
                raise ValueError("Diagnostic file escaped run directory")
            if not path.is_file():
                problem("missing_diagnostic_file", cell_id=cell_id, manifest_index=(manifest or []).index(entry))
                continue
            tracked[path] = file_hash(path)
            if tracked[path] != entry.get("sha256") or path.stat().st_size != entry.get("bytes"):
                problem("diagnostic_hash_or_size_mismatch", cell_id=cell_id,
                        manifest_index=(manifest or []).index(entry))
            else:
                verified_files += 1
        snapshots = []
        declared_names = {entry["file"] for entry in manifest or []}
        for path in sorted(directory.glob("worker-*.json")):
            tracked[path] = file_hash(path)
            if path.name not in declared_names:
                problem("unmanifested_worker_snapshot", cell_id=cell_id)
            snapshots.append((path, read_json(path)))
        pairs = pair_snapshots(telemetry.get("workers") or [], snapshots)
        snapshot_matches += sum(path is not None and source == "telemetry" for _, path, source in pairs)
        diagnostic_only += sum(source == "diagnostic_only" for _, _, source in pairs)
        telemetry_only += sum(path is None for _, path, _ in pairs)
        if any(path is None or source != "telemetry" for _, path, source in pairs):
            problem("worker_snapshot_telemetry_mismatch", cell_id=cell_id)
        if not pairs:
            problem("no_worker_lifetimes", cell_id=cell_id)
        workers = [worker for worker, _, _ in pairs]
        evidence = [[] for _ in workers]
        unmatched = []
        log_rows = {}
        for name in ("supervisor.jsonl", "scheduler-events.jsonl"):
            path = directory / name
            if path.is_file():
                tracked[path] = file_hash(path)
                log_rows[name] = read_lines(path)
            else:
                log_rows[name] = None
                problem("missing_evidence_log", cell_id=cell_id, file_role=name)

        def assign(event, kind, source, pid=None, address=None):
            index = event_worker_index(workers, pid=pid, address=address, utc=event.get("utc"))
            exported = safe_event(event, kind, source)
            if index is None:
                unmatched.append(exported)
            else:
                evidence[index].append(exported)

        nanny_events = diagnostic.get("nanny_memory_termination_events")
        exits = diagnostic.get("worker_exit_events")
        if nanny_events is None or exits is None:
            problem("missing_diagnostic_event_list", cell_id=cell_id)
        if nanny_events is not None and diagnostic.get("nanny_memory_termination_count") != len(nanny_events):
            problem("nanny_event_count_mismatch", cell_id=cell_id)
        for event in nanny_events or []:
            raw = log_rows.get(event.get("source"))
            if raw is not None and any(all(e.get(k) == event.get(k) for k in ("utc", "phase", "message")) for e in raw):
                raw_nanny_verified += 1
            else:
                problem("nanny_event_not_found_in_raw_log", cell_id=cell_id)
            match = re.search(r"Worker (\S+) \(pid=(\d+)\)", event.get("message", ""))
            assign(event, "nanny_memory_termination", "supervisor.jsonl",
                   pid=int(match[2]) if match else None, address=match[1] if match else None)
        for event in exits or []:
            assign(event, "worker_exit_before_cleanup", "runs.jsonl:diagnostics.worker_exit_events", pid=event.get("pid"))
        for event in log_rows.get("scheduler-events.jsonl") or []:
            kind = event.get("kind")
            if kind in ("initial_worker", "worker_added", "worker_removed", "nanny_memory_restart"):
                details = event.get("details") or {}
                assign(event, kind, "scheduler-events.jsonl", pid=details.get("pid"),
                       address=event.get("worker", details.get("worker")))
        target = next((config for config in plan["configs"] if config["config_id"] == record.get("target_config_id")), {})
        config = record.get("config") or {}
        metadata = {
            "stage": stage, "run_id": record.get("run_id"), "cell_id": cell_id,
            "instance_id": record.get("instance_id"), "workload": dataset.get("family"),
            "method": record.get("method"), "sample_fraction": fraction,
            "sample_fraction_source": "run.fraction" if "fraction" in record else "run.dataset.fraction",
            "sample_seed": record.get("sample_seed", (dataset.get("sampling") or {}).get("seed")),
            "repeat_id": record.get("repeat_id"), "target_config_id": record.get("target_config_id"),
            "config_id": config.get("config_id"), "n_workers": config.get("n_workers"),
            "threads_per_worker": config.get("threads_per_worker"),
            "target_memory_limit_bytes": int(target["memory_limit"]) if target.get("memory_limit") is not None else None,
            "configured_effective_memory_limit_bytes": int(config["memory_limit"]) if config.get("memory_limit") is not None else None,
            "dataset_sha256": dataset.get("sha256"), "manifest_sha256": record.get("manifest_sha256"),
            "parent_dataset_sha256": dataset.get("parent_sha256"),
            "run_status": record.get("status"), "failure_category": diagnostic.get("failure_category"),
            "run_started_utc": record.get("started_utc"), "run_finished_utc": record.get("finished_utc"),
            "run_observed_restarts_lower_bound": telemetry.get("observed_restarts_lower_bound"),
            "run_expected_workers": telemetry.get("expected_workers"),
            "run_worker_count_observed": telemetry.get("worker_count_observed"),
            "run_missing_initial_worker_records": telemetry.get("missing_initial_worker_records"),
            "run_nanny_memory_termination_count": diagnostic.get("nanny_memory_termination_count"),
            "run_worker_removals_before_cleanup": diagnostic.get("worker_removals_before_cleanup"),
            "sample_interval_ms": telemetry.get("sample_interval_ms"),
            "snapshot_persist_interval_s": telemetry.get("snapshot_persist_interval_s"),
            "measurement_scope": telemetry.get("window"),
        }
        run_output.append({**metadata, "exported_worker_lifetimes": len(pairs),
                           "unmatched_worker_evidence": unmatched})
        for index, (worker, path, source) in enumerate(pairs):
            events = evidence[index]
            kinds = {e["kind"] for e in events}
            origin = ("initial" if "initial_worker" in kinds else
                      "added_during_run" if "worker_added" in kinds else "unknown")
            row = {**metadata, "worker_lifetime_id": f"{stage}:{cell_id}:w{index + 1:02d}",
                   "worker_lifetime_index": index + 1, "worker_origin": origin,
                   "record_source": source, "snapshot_sha256": tracked.get(path.resolve()) if path else None,
                   "telemetry_worker_sha256": canonical_hash(worker) if source == "telemetry" else None,
                   **{key: worker.get(key) for key in WORKER_FIELDS},
                   "worker_nanny_memory_termination_count": sum(e["kind"] == "nanny_memory_termination" for e in events)
                   if nanny_events is not None and log_rows["supervisor.jsonl"] is not None else None,
                   "worker_exit_before_cleanup_count": sum(e["kind"] == "worker_exit_before_cleanup" for e in events)
                   if exits is not None else None,
                   "worker_evidence": events}
            absent = [key for key in WORKER_FIELDS if worker.get(key) is None]
            absent.extend("memory_settings." + key for key in SETTINGS
                          if (worker.get("memory_settings") or {}).get(key) is None)
            row["missing_worker_fields"] = absent
            missing.update(absent)
            if (worker.get("effective_memory_limit_bytes") is not None
                    and row["configured_effective_memory_limit_bytes"] is not None
                    and worker["effective_memory_limit_bytes"] != row["configured_effective_memory_limit_bytes"]):
                problem("worker_effective_limit_mismatch", cell_id=cell_id, worker_lifetime_index=index + 1)
            output.append(row)
    if audit and verified_files != audit.get("diagnostic_files_hash_verified"):
        problem("completion_audit_diagnostic_file_count_mismatch")
    if audit and raw_nanny_verified != audit.get("raw_nanny_memory_messages_verified" if stage == "A" else "raw_nanny_messages_verified"):
        problem("completion_audit_nanny_message_count_mismatch")
    summary = {"stage": stage, "planned_runs": len(cells), "recorded_runs": len(records), "statuses": statuses,
               "plan_canonical_sha256": plan_hash, "plan_file_sha256": tracked[root / "plan.json"],
               "runs_sha256": tracked[runs_path], "expected_plan_sha256": expected_plan_hash,
               "expected_runs_sha256": expected_raw_hash, "exported_worker_lifetimes": len(output),
               "exact_snapshot_telemetry_matches": snapshot_matches,
               "diagnostic_only_lifetimes": diagnostic_only, "telemetry_only_lifetimes": telemetry_only,
               "diagnostic_files_hash_verified": verified_files, "raw_nanny_messages_verified": raw_nanny_verified,
               "worker_origins": dict(Counter(row["worker_origin"] for row in output)),
               "missing_worker_fields": dict(missing),
               "unmatched_worker_evidence_count": sum(len(row["unmatched_worker_evidence"]) for row in run_output),
               "issues": issues, "integrity_pass": not issues}
    return output, run_output, summary


def export(repo, out):
    repo, out = repo.resolve(), out.resolve()
    # Destination must stay outside original inputs, even for an empty directory.
    if out.is_relative_to(repo / "data") or out == repo:
        raise ValueError("Export destination cannot be inside original data or the repository root")
    if out.exists() and any(out.iterdir()):
        raise ValueError("Export destination must be empty")
    b_plan_path = repo / "data/probes/windows-stage-b-v1/plan.json"
    b_audit_path = repo / "reports/research_stage_b_windows_v1/completion_audit.json"
    if not b_plan_path.is_file() or not b_audit_path.is_file():
        raise ValueError("Missing Stage B plan/audit needed to pin existing Stage A/B raw hashes")
    b_plan, b_audit = read_json(b_plan_path), read_json(b_audit_path)
    tracked = {b_plan_path: file_hash(b_plan_path), b_audit_path: file_hash(b_audit_path)}
    workers, runs, stages = [], [], []
    for stage, raw_hash, plan_hash in (
        ("A", b_plan["reference"]["raw_records_sha256"], b_plan["reference"]["plan_sha256"]),
        ("B", b_audit["runs_sha256"], b_audit["plan_sha256"]),
    ):
        worker_rows, run_rows, summary = collect_stage(repo, stage, raw_hash, plan_hash, tracked)
        workers.extend(worker_rows)
        runs.extend(run_rows)
        stages.append(summary)
    changed = [path.name for path, digest in tracked.items() if not path.is_file() or file_hash(path) != digest]
    if changed:
        raise ValueError("Original evidence changed while reading; export aborted")
    verification = {"schema_version": "worker-memory-export-v1",
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "scope": "existing Stage A/B records only; no workload execution or data/model generation",
                    "hash_anchors": {"A": "Stage B frozen plan reference (canonical plan + raw JSONL byte hash)",
                                     "B": "published Stage B completion audit"},
                    "original_files_rehashed_unchanged": len(tracked),
                    "stages": stages, "integrity_pass": all(s["integrity_pass"] for s in stages)}
    out.mkdir(parents=True, exist_ok=True)
    for name, value in (("workers.json", workers), ("runs.json", runs), ("verification.json", verification)):
        (out / name).write_text(compact(value) + "\n", encoding="utf-8")
    write_csv(out / "workers.csv", workers)
    lines = ["# Stage A/B worker memory export", "",
             "Read-only export of the existing Windows attempts. No benchmarks, datasets, models or main merge.", "",
             "| Stage | Runs (success/error) | Worker lifetimes | Initial / added | Verified diagnostic files | Nanny messages |",
             "| --- | --- | --- | --- | --- | --- |"]
    for s in stages:
        counts, origins = s.get("statuses", {}), s.get("worker_origins", {})
        lines.append(f"| {s['stage']} | {s.get('recorded_runs')} ({counts.get('success', 0)}/{counts.get('execution_error', 0)}) | "
                     f"{s.get('exported_worker_lifetimes')} | {origins.get('initial', 0)} / {origins.get('added_during_run', 0)} | "
                     f"{s.get('diagnostic_files_hash_verified')} | {s.get('raw_nanny_messages_verified')} |")
    lines += ["", f"Integrity checks: **{'PASS' if verification['integrity_pass'] else 'FAIL — inspect verification.json'}**. "
              f"Rehashed {len(tracked)} original evidence/anchor files after reading; all unchanged.", "",
              "- Plan canonical hashes, exact published plans, cell identities, raw JSONL byte hashes and original completion counts/statuses checked. "
              "All declared diagnostic file byte sizes/SHA-256 hashes checked. Nanny messages checked against retained raw supervisor logs.",
              "- Hash anchors: Stage A is pinned by the frozen Stage B reference; Stage B by its published completion audit. "
              "These are integrity checks against saved evidence, not independent signatures. Full hashes and issues are in [verification.json](verification.json).", "",
              "## Files and interpretation", "",
              "- [workers.csv](workers.csv) and [workers.json](workers.json): identical worker-lifetime rows. "
              "[runs.json](runs.json) covers every run, including any run with no worker record, and preserves unmatched evidence.",
              "- Every lifetime has a stable per-cell ID, ordered by plugin start time. `initial` and `added_during_run` come from scheduler events. "
              "Added lifetimes stay separate; no worker-slot or parent/replacement pairing is inferred. PID/address/local paths are omitted. "
              "Snapshot and canonical worker/event hashes allow linkage to retained local evidence.",
              "- Missing measurements are JSON `null` / blank CSV cells, never substituted with zero. Empty event lists mean no matched retained event. "
              "Measured zeros and false/disabled thresholds remain intact. Parent-dataset hash is null for Stage A full inputs (not applicable). "
              "Counts of absent worker fields and missing/mismatched files appear below and in verification.json.",
              "- All memory sizes are bytes. Target config caps differ from Stage B's mapped effective caps; both are retained. "
              "Worker `effective_memory_limit_bytes` is the measured worker setting. `memory_settings` holds target/spill/pause/terminate fractions, "
              "monitor interval and max-spill. Nested CSV values are compact JSON.",
              "- Baseline RSS is the first plugin sample, not a guaranteed idle baseline. RSS/managed/spill peaks are per lifetime, "
              "not synchronized cluster peaks. Do not subtract unrelated peaks to infer unmanaged memory. Window includes graph build, execution and cleanup; "
              "sampling is 50 ms with snapshots persisted every 0.25 s. Abrupt deaths can leave incomplete snapshots and brief peaks can be missed.",
              "- Worker evidence is attributed by raw PID/address (and time when needed), then anonymized. Ambiguous/unmatched events remain at run level. "
              "A nanny memory-budget restart is not proof of OS OOM. Run success can coexist with worker restarts; no event is not proof that no event occurred.", "",
              "## Missing data / verification exceptions", ""]
    for s in stages:
        lines.append(f"- Stage {s['stage']}: missing worker fields {compact(s.get('missing_worker_fields', {}))}; "
                     f"diagnostic-only {s.get('diagnostic_only_lifetimes')}, telemetry-only {s.get('telemetry_only_lifetimes')}; "
                     f"unmatched evidence {s.get('unmatched_worker_evidence_count')}; verification issues {len(s['issues'])}.")
    lines += ["", "## Reproduce without executing workloads", "", "```powershell",
              ".\\.venv-research\\Scripts\\python.exe -m experiments.export_worker_memory --out reports/worker_memory_stage_a_b_new",
              ".\\.venv-research\\Scripts\\python.exe -m pytest -q tests/test_worker_memory_export.py", "```", "",
              "The destination must be empty. Only this exporter and synthetic exporter tests are invoked; "
              "raw inputs stay ignored and preserved locally. Dataset contents, frozen source/runtime compatibility and model quality are outside this export's verification scope.", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        verification = export(args.repo, args.out)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Export not completed: {exc}\n")
    print(compact({"integrity_pass": verification["integrity_pass"],
                   "stages": [{k: s.get(k) for k in ("stage", "recorded_runs", "exported_worker_lifetimes", "issues")}
                              for s in verification["stages"]]}))
    if not verification["integrity_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
