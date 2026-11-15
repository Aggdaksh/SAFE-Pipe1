"""Isolated, timeout-bounded collector for the research probe pilot.

This module deliberately does not change the production collector's timing target.
Worker peaks are sampled, and a sum of individual peaks is NOT a concurrent peak.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import platform
import tempfile
import time
import uuid
from typing import Any

import psutil

from safe_pipe.research.probe_diagnostics import (
    SchedulerEvents, append_event, attach_log, detach_log, host_conditions,
    memory_settings, summarize_diagnostics, utc_now,
)

GIB = 2**30
SAMPLE_INTERVAL_MS = 50
PERSIST_INTERVAL_S = 0.25


def _write_json(path: Path, value: dict[str, Any]) -> None:
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")
    pending.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def validate_host_budget(config: dict[str, Any], reserve_bytes: int = 2 * GIB) -> dict[str, int]:
    """Check explicit aggregate worker caps against current available host memory.

    These caps are Dask targets, not hard OS reservations. The additional headroom
    is for the client, scheduler, task transients, and unrelated applications.
    """
    from dask.utils import parse_bytes

    for key in ("n_workers", "threads_per_worker"):
        value = config.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{key} must be a positive integer")
    memory = config.get("memory_limit")
    if not isinstance(memory, str) or memory.lower() == "auto":
        raise ValueError("research runs require an explicit memory_limit string")
    cap = int(parse_bytes(memory))
    if cap <= 0 or reserve_bytes < 0:
        raise ValueError("memory limit must be positive and reserve nonnegative")
    host = psutil.virtual_memory()
    reserve = max(int(reserve_bytes), math.ceil(0.30 * host.available))
    allocation = cap * config["n_workers"]
    if allocation + reserve > host.available:
        raise ValueError(
            f"insufficient available RAM: worker caps={allocation}, "
            f"required headroom={reserve}, available={host.available} bytes"
        )
    return {
        "physical_bytes": int(host.total), "available_bytes": int(host.available),
        "worker_cap_bytes": cap, "aggregate_worker_cap_bytes": allocation,
        "reserved_headroom_bytes": reserve,
    }


def _environment() -> dict[str, Any]:
    versions = {}
    for package in ("dask", "distributed", "numpy", "pandas", "pyarrow", "psutil", "cloudpickle", "tornado"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {"platform": platform.platform(), "machine": platform.machine(),
            "python": platform.python_version(), "logical_cpus": psutil.cpu_count(),
            "versions": versions}


def _number_or_none(value: Any) -> int | None:
    return int(value) if isinstance(value, (int, float)) and math.isfinite(value) else None


class _MemorySampler:
    """Duck-typed WorkerPlugin; measurements stay local to each worker."""

    idempotent = False

    def __init__(self, folder: str):
        self.folder = folder

    def setup(self, worker: Any) -> None:
        from tornado.ioloop import PeriodicCallback

        self.worker = worker
        self.process = psutil.Process()
        self.path = Path(self.folder) / f"worker-{os.getpid()}-{uuid.uuid4().hex}.json"
        self.log_handler = attach_log(self.path.with_suffix(".jsonl"))
        self.started = time.monotonic()
        self.persisted = 0.0
        self.record: dict[str, Any] = {
            "pid": os.getpid(), "address": worker.address,
            "started_utc": utc_now(), "memory_settings": memory_settings(),
            "effective_memory_limit_bytes": worker.memory_manager.memory_limit,
            "samples": 0, "paused_samples": 0,
            "baseline_rss_bytes": None, "peak_rss_bytes": None,
            "peak_managed_total_bytes": None, "peak_managed_in_memory_bytes": None,
            "peak_spilled_memory_bytes": None, "peak_spilled_disk_bytes": None,
            "cumulative_spill_write_bytes": None, "cumulative_spill_write_count": None,
            "sampling_errors": 0, "status_counts": {},
            "measurement_window_s": 0.0,
        }
        self.sample(force=True)
        self.callback = PeriodicCallback(self.sample, SAMPLE_INTERVAL_MS)
        self.callback.start()

    def sample(self, force: bool = False) -> None:
        r = self.record
        try:
            rss = self.process.memory_info().rss
            managed = _number_or_none(getattr(self.worker.state, "nbytes", None))
            spilled = getattr(self.worker.data, "spilled_total", None)
            spill_memory = _number_or_none(getattr(spilled, "memory", None))
            spill_disk = _number_or_none(getattr(spilled, "disk", None))
            in_memory = max(0, managed - spill_memory) if managed is not None and spill_memory is not None else None
            for name, value in (
                ("peak_rss_bytes", rss), ("peak_managed_total_bytes", managed),
                ("peak_managed_in_memory_bytes", in_memory),
                ("peak_spilled_memory_bytes", spill_memory), ("peak_spilled_disk_bytes", spill_disk),
            ):
                if value is not None:
                    r[name] = max(r[name] or 0, value)
            if r["baseline_rss_bytes"] is None:
                r["baseline_rss_bytes"] = rss
            metrics = getattr(self.worker.data, "cumulative_metrics", None)
            if metrics is not None:
                r["cumulative_spill_write_bytes"] = _number_or_none(metrics.get(("disk-write", "bytes"), 0))
                r["cumulative_spill_write_count"] = _number_or_none(metrics.get(("disk-write", "count"), 0))
            status = getattr(self.worker.status, "name", str(self.worker.status))
            r["status_counts"][status] = r["status_counts"].get(status, 0) + 1
            r["paused_samples"] += int(status == "paused")
            r["samples"] += 1
        except Exception:
            r["sampling_errors"] += 1
        r["measurement_window_s"] = time.monotonic() - self.started
        r["last_sample_utc"] = utc_now()
        if force or time.monotonic() - self.persisted >= PERSIST_INTERVAL_S:
            _write_json(self.path, r)
            self.persisted = time.monotonic()

    def transition(self, key: Any, start: str, finish: str, **kwargs: Any) -> None:
        if finish in {"memory", "error"}:
            self.sample()

    def teardown(self, worker: Any) -> None:
        self.callback.stop()
        self.sample(force=True)
        detach_log(self.log_handler)


def _flush_sampler(dask_worker: Any) -> None:
    dask_worker.plugins["research-memory-sampler"].sample(force=True)


def _summarize_telemetry(folder: Path, expected_workers: int) -> dict[str, Any]:
    workers = [_read_json(p) for p in sorted(folder.glob("worker-*.json"))]
    workers = [w for w in workers if w.get("samples", 0) > 0]

    def total(field: str) -> int | None:
        values = [w.get(field) for w in workers]
        return sum(values) if values and all(v is not None for v in values) else None

    return {
        "sample_interval_ms": SAMPLE_INTERVAL_MS,
        "snapshot_persist_interval_s": PERSIST_INTERVAL_S,
        "window": "plugin registration through worker cleanup; includes graph build and execution",
        "aggregation": "sum of each observed worker lifetime's sampled peak; NOT a concurrent cluster peak",
        "expected_workers": expected_workers, "worker_count_observed": len(workers),
        "observed_restarts_lower_bound": max(0, len(workers) - expected_workers),
        "missing_initial_worker_records": max(0, expected_workers - len(workers)),
        "rss_peak_bytes_sum": total("peak_rss_bytes"),
        "managed_peak_bytes_sum": total("peak_managed_in_memory_bytes"),
        "spilled_disk_peak_bytes_sum": total("peak_spilled_disk_bytes"),
        "cumulative_spill_write_bytes_observed": total("cumulative_spill_write_bytes"),
        "paused_samples": total("paused_samples"), "samples_total": total("samples"), "workers": workers,
        "limitations": "Sampling can miss brief peaks. Restart/crash snapshots may be incomplete. Zero spill is observed zero, not proof of absence.",
    }


def _graph_info(graph: Any) -> dict[str, Any]:
    from dask.utils import key_split

    tasks = graph.__dask_graph__()
    keys = sorted(map(str, tasks.keys()))
    prefixes = Counter(key_split(key) for key in tasks)
    return {"task_count": len(keys), "key_sha256": hashlib.sha256("\n".join(keys).encode()).hexdigest(),
            "task_prefix_counts": dict(sorted(prefixes.items())),
            "scope": "collection graph snapshot; scheduler may still cull tasks"}


def _execute(folder: str, dataset_dir: str, config: dict[str, Any], scratch: str) -> None:
    """Spawn target; parent supervises all phases, including startup and cleanup."""
    from distributed import Client, LocalCluster, SchedulerPlugin, WorkerPlugin
    from safe_pipe.research.probe_workloads import build_probe_result

    # Explicit subclass avoids relying on the deprecated duck-typed plugin path.
    class SamplerPlugin(_MemorySampler, WorkerPlugin):
        pass

    class EventPlugin(SchedulerEvents, SchedulerPlugin):
        pass

    path = Path(folder) / "progress.json"
    started = time.monotonic()
    record: dict[str, Any] = {"phase": "setup", "status": "running", "result_value": None,
                              "timings": {"setup_seconds": None, "execution_seconds": None,
                                          "graph_build_seconds": None, "compute_seconds": None,
                                          "telemetry_flush_seconds": None, "cleanup_seconds": None},
                              "error": None, "graph": None}
    record["memory_settings"] = memory_settings()
    record["child_started_utc"] = utc_now()
    handler = attach_log(Path(folder) / "supervisor.jsonl", lambda: record["phase"])
    _write_json(path, record)
    cluster = client = None
    phase_started = started
    try:
        cluster = LocalCluster(n_workers=config["n_workers"], threads_per_worker=config["threads_per_worker"],
                               memory_limit=config["memory_limit"], processes=True,
                               host="127.0.0.1", dashboard_address=None, worker_dashboard_address=None,
                               local_directory=scratch, silence_logs=40)
        client = Client(cluster)
        client.register_plugin(EventPlugin(folder), name="research-events")
        client.register_plugin(SamplerPlugin(folder), name="research-memory-sampler")
        record["timings"]["setup_seconds"] = time.monotonic() - phase_started
        record["phase"] = "execution"
        phase_started = time.monotonic()
        _write_json(path, record)
        graph_started = time.monotonic()
        graph = build_probe_result(Path(dataset_dir))
        record["unoptimized_graph"] = _graph_info(graph)
        graph = graph.optimize()
        record["graph"] = _graph_info(graph)
        record["graph"]["scope"] = "optimized collection submitted with optimize_graph=False; scheduler may still cull tasks"
        record["timings"]["graph_build_seconds"] = time.monotonic() - graph_started
        _write_json(path, record)
        compute_started = time.monotonic()
        try:
            value = float(client.compute(graph, optimize_graph=False).result())
        finally:
            record["timings"]["compute_seconds"] = time.monotonic() - compute_started
        if not math.isfinite(value):
            raise ValueError("probe result is not finite")
        record["result_value"] = value
        record["timings"]["execution_seconds"] = time.monotonic() - phase_started
        record["status"] = "success"
    except BaseException as exc:
        record["status"] = "startup_error" if record["phase"] == "setup" else "execution_error"
        record["timings"]["setup_seconds" if record["phase"] == "setup" else "execution_seconds"] = time.monotonic() - phase_started
        record["error"] = f"{type(exc).__name__}: {exc}"[:1000]
    finally:
        record["phase"] = "telemetry_flush"
        _write_json(path, record)
        flush_started = time.monotonic()
        if client is not None:
            try:
                client.run(_flush_sampler)
            except Exception as exc:
                record["telemetry_flush_error"] = f"{type(exc).__name__}: {exc}"[:500]
        record["timings"]["telemetry_flush_seconds"] = time.monotonic() - flush_started
        record["phase"] = "cleanup"
        _write_json(path, record)
        cleanup_started = time.monotonic()
        errors = []
        for resource in (client, cluster):
            if resource is not None:
                try:
                    resource.close(timeout=5)
                except Exception as exc:
                    errors.append(f"{type(exc).__name__}: {exc}"[:500])
        record["timings"]["cleanup_seconds"] = time.monotonic() - cleanup_started
        if errors:
            record["cleanup_errors"] = errors
            if record["status"] == "success":
                record["status"] = "cleanup_error"
        record["phase"] = "complete"
        record["child_wall_s"] = time.monotonic() - started
        record["child_finished_utc"] = utc_now()
        _write_json(path, record)
        detach_log(handler)


def _terminate_tree(pid: int, known_descendants: list[psutil.Process] | None = None) -> None:
    """Stop only this spawned job's process tree, never unrelated Dask processes."""
    victims = list(known_descendants or [])
    try:
        root = psutil.Process(pid)
        root.suspend()
        victims.extend(root.children(recursive=True))
        victims.append(root)
    except psutil.NoSuchProcess:
        pass
    unique = {(p.pid, p.create_time()): p for p in victims if p.is_running()}
    for process in unique.values():
        try:
            process.suspend()
        except psutil.NoSuchProcess:
            pass
    for process in unique.values():
        try:
            process.terminate()
            process.resume()
        except psutil.NoSuchProcess:
            pass
    # multiprocessing owns waitpid() for its direct child. Letting psutil reap
    # that PID would leave Process.exitcode unset and break join()/close().
    descendants = [p for p in unique.values() if p.pid != pid]
    _, alive = psutil.wait_procs(descendants, timeout=2)
    alive.extend(p for p in unique.values() if p.pid == pid and _still_running(p))
    for process in alive:
        try:
            process.kill()
        except psutil.NoSuchProcess:
            pass
    psutil.wait_procs([p for p in alive if p.pid != pid], timeout=2)


def _still_running(process: psutil.Process) -> bool:
    try:
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def run_probe(dataset_dir: Path, config: dict[str, Any], timeout_s: float,
              repeat_id: int = 1, session_id: str = "", diagnostics_dir: Path | None = None,
              require_mains: bool = False) -> dict[str, Any]:
    """Run one physical probe with a total wall-time limit and complete outcome row.

    Call from an importable module protected by ``if __name__ == '__main__'`` on
    spawn platforms. Invalid inputs raise before starting a child; physical run
    failures return labelled rows rather than being silently discarded.
    """
    preflight_started = time.monotonic()
    if not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("timeout_s must be finite and positive")
    if isinstance(repeat_id, bool) or not isinstance(repeat_id, int) or repeat_id < 1:
        raise ValueError("repeat_id must be a positive integer")
    budget = validate_host_budget(config)
    # Fail before spawning if this environment cannot inspect/contain owned descendants.
    try:
        psutil.Process().children(recursive=True)
    except (psutil.AccessDenied, PermissionError) as exc:
        raise ValueError("process inspection permission is required for supervised Dask runs") from exc
    from safe_pipe.research.probe_workloads import load_manifest

    manifest = load_manifest(Path(dataset_dir))
    environment = _environment()
    initial_conditions = host_conditions(Path(dataset_dir))
    if require_mains and initial_conditions["battery_present"] and initial_conditions["power_plugged"] is not True:
        raise ValueError("Connect the Windows experiment laptop to mains before starting a cell")
    run_id = str(uuid.uuid4())
    durable = Path(diagnostics_dir).resolve() / run_id if diagnostics_dir is not None else None
    if durable is not None:
        durable.mkdir(parents=True, exist_ok=False)
        _write_json(durable / "attempt.json", {"run_id": run_id, "session_id": session_id,
                    "repeat_id": repeat_id, "config": config, "created_utc": utc_now(),
                    "environment": environment})
    preflight_seconds = time.monotonic() - preflight_started
    started_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    known: dict[tuple[int, float], psutil.Process] = {}
    condition_flags = set()
    conditions_count = 0
    with tempfile.TemporaryDirectory(prefix="safe-pipe-probe-") as temporary:
        folder = durable or Path(temporary)
        append_event(folder / "conditions.jsonl", initial_conditions)
        conditions_count += 1
        last_conditions = time.monotonic()
        child = mp.get_context("spawn").Process(target=_execute, args=(str(folder), str(Path(dataset_dir).resolve()), config, temporary))
        child.start()
        interrupted = False
        try:
            while child.is_alive() and time.monotonic() - started < timeout_s:
                if time.monotonic() - last_conditions >= 1.0:
                    conditions = host_conditions(folder)
                    append_event(folder / "conditions.jsonl", conditions)
                    conditions_count += 1
                    if conditions["battery_present"] and conditions["power_plugged"] is not True:
                        condition_flags.add("mains_lost_or_unknown")
                    last_conditions = time.monotonic()
                try:
                    for process in psutil.Process(child.pid).children(recursive=True):
                        known[(process.pid, process.create_time())] = process
                except psutil.NoSuchProcess:
                    pass
                child.join(timeout=min(0.05, max(0, timeout_s - (time.monotonic() - started))))
        except KeyboardInterrupt:
            interrupted = True
            finalize_started = time.monotonic()
            _terminate_tree(child.pid, list(known.values()))
            child.join(timeout=3)
        except BaseException:
            # An interrupted supervisor must not remove the scratch directory while its job survives.
            _terminate_tree(child.pid, list(known.values()))
            child.join(timeout=3)
            if not child.is_alive():
                child.close()
            raise
        if not interrupted:
            finalize_started = time.monotonic()
        progress = _read_json(folder / "progress.json")
        if interrupted:
            progress.update(status="interrupted", interrupted_phase=progress.get("phase", "spawn"),
                            error="operator interrupted this physical attempt; do not treat as runtime completion")
        elif child.is_alive():
            timed_out_phase = progress.get("phase", "spawn")
            _terminate_tree(child.pid, list(known.values()))
            child.join(timeout=3)
            progress.update(status="timeout", timeout_phase=timed_out_phase,
                            error=f"supervised lifecycle limit of {timeout_s}s reached; completion time is censored; final cleanup/diagnostics add overhead")
        elif child.exitcode != 0 or progress.get("phase") != "complete":
            _terminate_tree(child.pid, list(known.values()))
            progress.update(status="process_error", error=f"supervised child exited without a complete record (exitcode={child.exitcode})")
        # Any surviving descendants of a completed supervisor are also our own.
        survivors = [p for p in known.values() if _still_running(p)]
        if survivors:
            _terminate_tree(child.pid, survivors)
            progress["orphan_cleanup_required"] = True
            if progress.get("status") == "success":
                progress["status"] = "cleanup_error"
        progress["owned_descendants_alive_after_cleanup"] = sum(_still_running(p) for p in known.values())
        if progress["owned_descendants_alive_after_cleanup"]:
            progress["status"] = "cleanup_error"
        telemetry = _summarize_telemetry(folder, config["n_workers"])
        final_conditions = host_conditions(folder)
        append_event(folder / "conditions.jsonl", final_conditions)
        conditions_count += 1
        if final_conditions["battery_present"] and final_conditions["power_plugged"] is not True:
            condition_flags.add("mains_lost_or_unknown")
        exitcode = child.exitcode
        child.close()
        _write_json(folder / "supervisor-outcome.json", progress)
        try:
            diagnostics = summarize_diagnostics(folder, progress)
        except Exception as exc:
            diagnostics = {"failure_category": "diagnostics_unavailable", "summary_error": f"{type(exc).__name__}: {exc}"[:500]}
        diagnostics["retained"] = durable is not None
        diagnostics["directory"] = str(durable) if durable else None
        finalize_seconds = time.monotonic() - finalize_started
        scratch_cleanup_started = time.monotonic()
    elapsed = time.monotonic() - started
    scratch_cleanup_seconds = time.monotonic() - scratch_cleanup_started
    progress.setdefault("timings", {"setup_seconds": None, "execution_seconds": None, "cleanup_seconds": None})
    progress["timings"]["total_seconds"] = elapsed
    timings = progress["timings"]
    timings.update(preflight_seconds=preflight_seconds, supervisor_finalize_seconds=finalize_seconds,
                   scratch_cleanup_seconds=scratch_cleanup_seconds,
                   end_to_end_seconds=preflight_seconds + elapsed)
    accounted = sum(timings.get(k) or 0 for k in ("setup_seconds", "execution_seconds", "telemetry_flush_seconds",
                    "cleanup_seconds", "supervisor_finalize_seconds", "scratch_cleanup_seconds"))
    timings["unattributed_seconds"] = max(0.0, elapsed - accounted)
    return {
        "schema_version": "probe-run-v2", "run_id": run_id,
        "started_utc": started_utc, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id, "repeat_id": repeat_id,
        "config": dict(config), "dataset": manifest, "timeout_s": timeout_s,
        "environment": environment, "host_budget": budget, "telemetry": telemetry,
        "child_exitcode": exitcode, "diagnostics": diagnostics,
        "conditions": {"initial": initial_conditions, "final": final_conditions,
                       "samples": conditions_count, "flags": sorted(condition_flags),
                       "sampling_interval_seconds": 1.0},
        "timing_contract": "total includes spawn/startup, graph build, execution, telemetry flush, cleanup and diagnostic summary. "
                           "graph_build/compute are nested inside execution, not additional phases. "
                           "unattributed includes spawn/imports/bookkeeping and unreported partial phases after forced termination. "
                           "end_to_end adds preflight. Dataset preparation and batch verification/persistence are separate shared costs.",
        **progress,
    }
