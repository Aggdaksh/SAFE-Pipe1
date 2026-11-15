"""Local durable evidence; a worker death is never automatically labelled OS OOM.

Logs may contain local paths, process IDs and addresses. Only the compact summary
belongs in a public export. Dask messages are version-dependent evidence, not a
stable API: unfamiliar messages remain raw evidence and unknown causes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import re
import tempfile
import time

import psutil

MAX_LOG_BYTES = 16 * 2**20  # Per process; truncation remains explicit.


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def host_conditions(folder: Path) -> dict:
    battery = psutil.sensors_battery()
    return {"utc": utc_now(), "power_plugged": battery.power_plugged if battery else None,
            "battery_present": battery is not None,
            "power_scope": "battery sensor; no battery detected is recorded separately from confirmed mains",
            "available_bytes": psutil.virtual_memory().available,
            "free_disk_bytes": psutil.disk_usage(str(folder)).free,
            "temp_free_disk_bytes": psutil.disk_usage(tempfile.gettempdir()).free}


def append_event(path: Path, event: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event) + "\n")


class DiagnosticLog(logging.Handler):
    """Not a StreamHandler: Dask's console silencing must not suppress this log."""

    def __init__(self, path: Path, phase=None):
        super().__init__(logging.INFO)
        self.path = path
        self.phase = phase or (lambda: "worker_lifetime")
        self.stream = path.open("a", encoding="utf-8")
        self.bytes_written = path.stat().st_size
        self.truncated = False

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self.truncated:
                return
            event = {"utc": utc_now(), "created_epoch_s": record.created,
                     "monotonic_s": time.monotonic(), "logger": record.name,
                     "level": record.levelname, "pid": record.process,
                     "phase": self.phase(), "message": record.getMessage()}
            if record.exc_info:
                event["exception"] = logging.Formatter().formatException(record.exc_info)
            line = json.dumps(event) + "\n"
            if self.bytes_written + len(line.encode()) > MAX_LOG_BYTES:
                self.truncated = True
                line = json.dumps({"utc": utc_now(), "event": "log_truncated",
                                   "limit_bytes": MAX_LOG_BYTES}) + "\n"
            self.stream.write(line)
            self.stream.flush()
            self.bytes_written += len(line.encode())
        except Exception:
            # A broken evidence sink must remain visible to the supervisor.
            self.handleError(record)
            try:
                self.path.with_suffix(".error").write_text("Diagnostic log write failed\n")
            except OSError:
                pass

    def close(self) -> None:
        self.acquire()
        try:
            self.stream.close()
            super().close()
        finally:
            self.release()


def attach_log(path: Path, phase=None) -> DiagnosticLog:
    handler = DiagnosticLog(path, phase)
    logger = logging.getLogger("distributed")
    logger.setLevel(logging.INFO)
    # Nanny exit-code messages are INFO; some user configs raise these levels.
    for name in ("distributed.nanny", "distributed.nanny.memory", "distributed.worker"):
        logging.getLogger(name).setLevel(logging.INFO)
    logger.addHandler(handler)
    return handler


def detach_log(handler: DiagnosticLog) -> None:
    logging.getLogger("distributed").removeHandler(handler)
    handler.close()


def memory_settings() -> dict:
    import dask
    return {key: dask.config.get("distributed.worker.memory." + key, default=None)
            for key in ("target", "spill", "pause", "terminate", "monitor-interval", "max-spill")}


class SchedulerEvents:
    """Mixed into a SchedulerPlugin in the spawned child; no parent open handles."""

    def __init__(self, folder: str):
        self.folder = folder

    def _record(self, kind: str, **details) -> None:
        try:
            phase = json.loads((Path(self.folder) / "progress.json").read_text())["phase"]
        except (OSError, ValueError, KeyError):
            phase = "unknown"
        event = {"utc": utc_now(), "monotonic_s": time.monotonic(),
                 "kind": kind, "phase": phase, **details}
        with (Path(self.folder) / "scheduler-events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, default=str) + "\n")

    async def start(self, scheduler) -> None:
        for worker in scheduler.workers:
            self._record("initial_worker", worker=worker)

    def add_worker(self, scheduler, worker, **kwargs) -> None:
        self._record("worker_added", worker=worker)

    def remove_worker(self, scheduler, worker, *, stimulus_id=None, **kwargs) -> None:
        self._record("worker_removed", worker=worker, stimulus_id=stimulus_id)

    def log_event(self, topic, msg) -> None:
        if topic == "worker-restart-memory":
            self._record("nanny_memory_restart", details=msg)


def summarize_diagnostics(folder: Path, progress: dict) -> dict:
    memory_events = []
    exits = []
    removals = 0
    truncated = False
    malformed = 0
    files = []
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        files.append({"file": path.name, "bytes": path.stat().st_size, "sha256": digest.hexdigest()})
        if path.suffix != ".jsonl":
            continue
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except ValueError:
                    malformed += 1
                    continue
                truncated |= event.get("event") == "log_truncated"
                before_cleanup = event.get("phase") in {"setup", "execution", "telemetry_flush"}
                if event.get("kind") == "worker_removed" and before_cleanup:
                    removals += 1
                message = event.get("message", "")
                if before_cleanup and event.get("logger", "").startswith("distributed.nanny"):
                    if re.search(r"exceeded \d+% memory budget\. Restarting", message):
                        memory_events.append({"source": path.name, "utc": event.get("utc"),
                                              "phase": event["phase"], "message": message})
                    match = re.search(r"Worker process (\d+) (?:exited with status (\d+)|was killed by signal (\d+))", message)
                    if match:
                        exits.append({"pid": int(match[1]), "exit_status": int(match[2]) if match[2] else None,
                                      "signal": int(match[3]) if match[3] else None,
                                      "utc": event.get("utc"), "phase": event["phase"]})
    # Do not count scheduler and log copies of the same memory event twice.
    status = progress.get("status")
    if status in {"timeout", "interrupted"}:
        cause = status
    elif status == "success":
        cause = "completed"  # A completed job may still have memory restarts.
    elif status == "execution_error" and memory_events and "KilledWorker" in (progress.get("error") or ""):
        cause = "worker_death_with_nanny_memory_termination_evidence"
    elif "KilledWorker" in (progress.get("error") or "") or exits:
        cause = "worker_death_unknown_cause"
    else:
        cause = "unclassified_" + str(status)
    return {"failure_category": cause, "nanny_memory_termination_count": len(memory_events),
            "nanny_memory_termination_events": memory_events, "worker_exit_events": exits,
            "worker_removals_before_cleanup": removals, "log_truncated": truncated,
            "malformed_log_lines": malformed, "log_write_errors": len(list(folder.glob("*.error"))),
            "files": files,
            "limitations": "Observed memory termination is a Dask nanny action, not proof of OS OOM. "
                           "Exit codes/signals alone do not establish OS OOM. Startup before worker plugin "
                           "registration and abrupt death can leave missing evidence. Cleanup exits are excluded."}
