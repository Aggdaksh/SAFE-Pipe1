"""Frozen prospective study and durable attempt journal for the original advisor.

Preparation and physical execution are Windows-only. Loading/auditing saved JSON
never imports a model, regenerates advice, or accesses physical datasets.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from importlib import metadata
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = ("scan_filter", "groupby", "skewed_join", "sort_merge")
CONFIG_IDS = tuple(f"w{w}_t{t}_{m}g" for w in (1, 2) for t in (1, 2) for m in (1, 2))
INDEX = "configs/datasets_main_v1.json"
SLA = "configs/family_sla_main_v1.json"
PLAN = "configs/matrix_plan_main_v1.json"
MODELS = "artifacts/main_v1"
PACKAGES = ("dask", "distributed", "numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "pydantic", "psutil")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO string")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _json(path: Path):
    def invalid(value):
        raise ValueError(f"non-finite JSON value: {value}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid)


def _positive(value, name: str, *, zero: bool = False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (value < 0 if zero else value <= 0):
        raise ValueError(f"invalid {name}")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def seal_manifest(payload: dict) -> dict:
    """Return a JSON-copy with a self-consistency digest (not a digital signature)."""
    result = json.loads(_canonical({k: v for k, v in payload.items() if k != "study_id"}))
    result["study_id"] = hashlib.sha256(_canonical(result)).hexdigest()
    return result


def cell_key(cell: dict) -> tuple[str, str, int]:
    if not isinstance(cell, dict) or set(cell) != {"family", "config_id", "repeat_id"}:
        raise ValueError("invalid cell identity")
    if type(cell["repeat_id"]) is not int or cell["repeat_id"] not in (1, 2, 3):
        raise ValueError("invalid repeat identity")
    return cell["family"], cell["config_id"], cell["repeat_id"]


def validate_manifest(manifest: dict, *, verify_digest: bool = True) -> None:
    """Validate frozen layout without loading the predictor or dataset files."""
    if manifest.get("schema_version") != 1 or manifest.get("data_version") != "main-v1":
        raise ValueError("unsupported prospective study version")
    if verify_digest and manifest.get("study_id") != seal_manifest(manifest)["study_id"]:
        raise ValueError("study manifest digest mismatch")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", manifest.get("run_set_id", "")):
        raise ValueError("run_set_id must be a short filename-safe identifier")
    _time(manifest["created_at"])
    if manifest.get("host_scope") not in ("original-host", "transfer"):
        raise ValueError("host scope must be explicitly declared")
    if not isinstance(manifest.get("host_attestation"), str) or not manifest["host_attestation"].strip():
        raise ValueError("host attestation is required")
    env = manifest["environment"]
    if env.get("system") != "Windows" or not env.get("node") or not env.get("platform"):
        raise ValueError("study must be prepared on an identified Windows host")
    _positive(manifest["timeout_s"], "timeout")
    if manifest.get("baseline_config_id") not in CONFIG_IDS:
        raise ValueError("invalid frozen baseline")
    if manifest.get("retry_policy") != "no retries; one terminal attempt per planned cell":
        raise ValueError("unsupported retry policy")
    expected = {(f, c, r) for f in FAMILIES for c in CONFIG_IDS for r in (1, 2, 3)}
    keys = [cell_key(cell) for cell in manifest["plan"]]
    if len(keys) != 96 or set(keys) != expected:
        raise ValueError("plan must contain each original 96 cell exactly once")
    configs = manifest["configurations"]
    if len(configs) != 8 or {c["config_id"] for c in configs} != set(CONFIG_IDS):
        raise ValueError("study must bind the eight configurations")
    for key in ("profiles", "dataset_manifests", "advice"):
        if set(manifest[key]) != set(FAMILIES):
            raise ValueError(f"study {key} must bind all four profiles")
    for family in FAMILIES:
        profile = manifest["profiles"][family]
        dataset = manifest["dataset_manifests"][family]
        advice = manifest["advice"][family]
        if profile["family"] != family or dataset["family"] != family or dataset["data_version"] != "main-v1":
            raise ValueError("profile/dataset identity mismatch")
        if advice["workload"] != profile or advice["preferences"]["mode"] != "balanced":
            raise ValueError("primary advice must match the profile and balanced mode")
        _positive(advice["engine_sla_seconds"], "engine SLA")
        _positive(advice["effective_deadline_seconds"], "effective deadline")
        candidates = advice["candidates"]
        if len(candidates) != 8 or {c["config_id"] for c in candidates} != set(CONFIG_IDS):
            raise ValueError("saved advice must contain every candidate exactly once")
        for candidate in candidates:
            _positive(candidate["predicted_runtime_s"], "predicted runtime")
            _positive(candidate["runtime_upper_s"], "runtime upper")
            if candidate["runtime_upper_s"] < candidate["predicted_runtime_s"]:
                raise ValueError("upper runtime below point estimate")
        decision = advice["decision"]
        if decision["action"] == "abstain":
            if decision["config_id"] is not None:
                raise ValueError("abstention must not select a configuration")
        elif decision["action"] == "recommend":
            selected = next((c for c in candidates if c["config_id"] == decision["config_id"]), None)
            if selected is None or not selected["eligible"]:
                raise ValueError("recommendation must select an eligible candidate")
        else:
            raise ValueError("unknown recommendation action")
    for field in ("source_sha256_lf", "input_sha256_lf"):
        hashes = manifest[field]
        if not hashes:
            raise ValueError(f"missing {field}")
        for relative, value in hashes.items():
            p = Path(relative)
            if p.is_absolute() or ".." in p.parts or "\\" in relative or not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError("invalid provenance path or hash")
    _canonical(manifest)  # disallow non-finite numbers anywhere in the snapshot


def load_study(study_dir: Path) -> dict:
    manifest = _json(Path(study_dir) / "manifest.json")
    validate_manifest(manifest)
    return manifest


def read_events(study_dir: Path) -> list[dict]:
    path = Path(study_dir) / "attempts.jsonl"
    if not path.is_file():
        raise ValueError("study attempt journal is missing")
    def invalid(value):
        raise ValueError(f"non-finite journal value: {value}")
    text = path.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        raise ValueError("journal has an incomplete final write; preserve it for explicit recovery")
    return [json.loads(line, parse_constant=invalid) for line in text.splitlines() if line.strip()]


def audit_journal(manifest: dict, events: list[dict]) -> dict:
    """Return completed/pending/missing without discarding failed attempts."""
    validate_manifest(manifest)
    plan = manifest["plan"]
    plan_keys = {cell_key(cell) for cell in plan}
    config_map = {c["config_id"]: c for c in manifest["configurations"]}
    starts, terminals, used_cells, run_ids, acknowledged = {}, {}, set(), set(), set()
    previous = _time(manifest["created_at"])
    for event in events:
        if event.get("study_id") != manifest["study_id"] or event.get("run_set_id") != manifest["run_set_id"]:
            raise ValueError("journal belongs to a different frozen study")
        timestamp = _time(event["timestamp"])
        if timestamp < previous:
            raise ValueError("journal timestamps precede study or are out of order")
        previous = timestamp
        key = cell_key(event["cell"])
        if key not in plan_keys:
            raise ValueError("unexpected journal cell")
        aid = event.get("attempt_id")
        if not isinstance(aid, str) or not aid:
            raise ValueError("missing attempt identity")
        if event.get("event") == "started":
            if aid in starts or key in used_cells:
                raise ValueError("duplicate attempt or repeated planned cell")
            if set(starts) != set(terminals):
                raise ValueError("another attempt is still pending")
            if any(e["kind"] in ("infrastructure_error", "aborted") and previous_id not in acknowledged for previous_id, e in terminals.items()):
                raise ValueError("cleanup must be acknowledged before another planned attempt")
            expected = cell_key(plan[len(starts)])
            if key != expected:
                raise ValueError("attempt order differs from the frozen randomized plan")
            starts[aid] = event
            used_cells.add(key)
        elif event.get("event") == "finished":
            if aid not in starts or aid in terminals or event["cell"] != starts[aid]["cell"]:
                raise ValueError("orphaned, duplicated or mismatched terminal event")
            if event.get("lifecycle_seconds") is not None:
                _positive(event["lifecycle_seconds"], "lifecycle duration", zero=True)
            kind, result = event.get("kind"), event.get("result")
            if kind == "engine":
                if not isinstance(result, dict):
                    raise ValueError("engine attempt requires a result")
                family, config_id, repeat_id = key
                if result.get("workload") != manifest["profiles"][family] or result.get("config") != config_map[config_id]:
                    raise ValueError("result profile/configuration differs from study")
                if result.get("repeat_id") != repeat_id or result.get("data_version") != manifest["data_version"] or result.get("backend") != "dask_local" or result.get("voided", False):
                    raise ValueError("result identity/backend/version mismatch")
                if result.get("sla_seconds") != manifest["advice"][family]["engine_sla_seconds"]:
                    raise ValueError("result SLA differs from frozen advice")
                hardware = f"{manifest['environment']['node']} | {manifest['environment']['platform']}"
                if result.get("hardware") != hardware:
                    raise ValueError("result host differs from frozen environment")
                rid = result.get("run_id")
                if not isinstance(rid, str) or not rid or rid in run_ids:
                    raise ValueError("missing or duplicate engine run identity")
                run_ids.add(rid)
                if result.get("status") not in ("success", "timeout", "oom", "spill_abort", "error"):
                    raise ValueError("unknown engine outcome")
                if result.get("failure_category") not in ("none", "actionable", "transient", "non_configuration"):
                    raise ValueError("unknown failure category")
                duration = result.get("engine_seconds")
                if duration is not None:
                    _positive(duration, "engine duration")
                if result["status"] == "success" and (duration is None or result.get("failure_category") != "none"):
                    raise ValueError("successful result needs duration and no failure category")
                if event.get("lifecycle_seconds") is None:
                    raise ValueError("engine attempt needs lifecycle duration")
                if duration is not None and duration > event["lifecycle_seconds"] + 0.1:
                    raise ValueError("engine duration exceeds the measured lifecycle")
                if result["status"] == "timeout" and duration != manifest["timeout_s"]:
                    raise ValueError("timeout duration must retain the frozen wait limit")
            elif kind in ("infrastructure_error", "aborted"):
                if result is not None or not isinstance(event.get("error"), str) or not event["error"].strip():
                    raise ValueError("non-engine attempt requires reason and null result")
            else:
                raise ValueError("unknown terminal outcome kind")
            terminals[aid] = event
        elif event.get("event") == "cleanup_acknowledged":
            if aid not in terminals or aid in acknowledged or terminals[aid]["kind"] not in ("infrastructure_error", "aborted"):
                raise ValueError("cleanup acknowledgement requires one unacknowledged interrupted/error attempt")
            if event["cell"] != starts[aid]["cell"] or event.get("workers_stopped") is not True or not event.get("reason", "").strip():
                raise ValueError("cleanup acknowledgement must name the attempt, reason and stopped-worker confirmation")
            acknowledged.add(aid)
        else:
            raise ValueError("unknown journal event")
    return {
        "completed": [terminals[aid] for aid in starts if aid in terminals],
        "pending": [start for aid, start in starts.items() if aid not in terminals],
        "missing": [cell for cell in plan if cell_key(cell) not in used_cells],
        "cleanup_required": [event for aid, event in terminals.items() if event["kind"] in ("infrastructure_error", "aborted") and aid not in acknowledged],
    }


def require_windows() -> None:
    if platform.system() != "Windows":
        raise RuntimeError("Preparation, execution and journal recovery must run on Windows; no Mac project runs.")


def environment_snapshot() -> dict:
    import psutil
    return {
        "system": platform.system(), "node": platform.node(), "platform": platform.platform(),
        "processor": platform.processor(), "machine": platform.machine(),
        "logical_cpus": psutil.cpu_count(), "physical_cpus": psutil.cpu_count(logical=False),
        "ram_bytes": psutil.virtual_memory().total, "python": sys.version,
        "packages": {name: metadata.version(name) for name in PACKAGES},
    }


def power_snapshot() -> dict:
    import psutil
    battery = psutil.sensors_battery()
    if battery is None:
        return {"status": "battery_not_reported", "power_plugged": None, "percent": None}
    return {"status": "reported", "power_plugged": bool(battery.power_plugged), "percent": battery.percent}


def _power_check() -> dict:
    power = power_snapshot()
    if power["power_plugged"] is False:
        raise RuntimeError("Windows laptop is unplugged; reconnect power before starting a scored attempt")
    return power


def source_hashes(root: Path = ROOT) -> dict:
    from experiments.verify_main_validation import fingerprints
    return fingerprints(root)


def input_hashes(root: Path = ROOT) -> dict:
    paths = [root / p for p in (INDEX, SLA, PLAN)]
    paths.extend(sorted((root / MODELS).glob("*.json")))
    paths.append(root / MODELS / "runtime_model.txt")
    return {p.relative_to(root).as_posix(): _hash(p) for p in paths}


def verify_datasets(manifest: dict) -> None:
    from safe_pipe.schemas import DatasetManifest
    from safe_pipe.workloads.generate import verify_manifest
    base = Path(manifest["data_dir"])
    for family, raw in manifest["dataset_manifests"].items():
        original = DatasetManifest.model_validate(raw)
        folder = base / family
        actual = DatasetManifest.model_validate(_json(folder / "manifest.json"))
        # Path records can vary between checkouts. Everything describing the
        # physical content must retain the original frozen identity.
        if actual.model_dump(exclude={"path"}) != original.model_dump(exclude={"path"}):
            raise ValueError(f"dataset manifest differs from frozen original: {family}")
        verify_manifest(original, folder)


def verify_compatible(manifest: dict, *, check_datasets: bool = True) -> None:
    require_windows()
    validate_manifest(manifest)
    if environment_snapshot() != manifest["environment"]:
        raise ValueError("Windows host or software environment changed since study preparation")
    if source_hashes() != manifest["source_sha256_lf"] or input_hashes() != manifest["input_sha256_lf"]:
        raise ValueError("source or frozen input files changed since study preparation")
    if check_datasets:
        verify_datasets(manifest)


@contextmanager
def writer_lock(study_dir: Path):
    """OS advisory lock is automatically released if the process dies."""
    path = Path(study_dir) / ".writer.lock"
    with path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("another process is writing this study") from exc
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:  # Allows synthetic lock tests on a future permitted POSIX host.
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError("another process is writing this study") from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _append(study_dir: Path, event: dict) -> None:
    payload = _canonical(event) + b"\n"
    with (Path(study_dir) / "attempts.jsonl").open("ab") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def prepare_study(*, study_dir: Path, run_set_id: str, data_dir: Path,
                  host_scope: str, host_attestation: str, verification: Path,
                  timeout_s: float = 120.0) -> dict:
    require_windows()  # Before loading a model, hashing data, or creating files.
    from safe_pipe.advisor import Preferences, frozen_profiles, load_advice
    from safe_pipe.grid import load_grid
    study_dir = Path(study_dir)
    if study_dir.exists():
        raise FileExistsError("study directory already exists; use a new evaluation identifier")
    _positive(timeout_s, "timeout")
    env = environment_snapshot()
    receipt = _json(Path(verification))
    if receipt.get("verification_pass") is not True or receipt.get("source_sha256_lf") != source_hashes() or receipt.get("environment") != env:
        raise ValueError("a passing Windows verification receipt for these exact sources and environment is required")
    if _time(receipt["created_utc"]) > _time(_utc()):
        raise ValueError("verification receipt timestamp is in the future")
    initial_power = _power_check()
    manifests = _json(ROOT / INDEX)
    slas = _json(ROOT / SLA)
    plan = _json(ROOT / PLAN)
    if plan.get("data_version") != "main-v1" or slas.get("data_version") != "main-v1":
        raise ValueError("plan and SLA must retain original main-v1 identity")
    profiles = frozen_profiles(ROOT / INDEX)
    dataset_map = {m["family"]: m for m in manifests}
    verify_datasets({"data_dir": str(Path(data_dir).resolve()), "dataset_manifests": dataset_map})
    env = environment_snapshot()
    sources, inputs = source_hashes(), input_hashes()
    if receipt["environment"] != env or receipt["source_sha256_lf"] != sources:
        raise ValueError("verified environment or sources changed while checking datasets")
    advice = {family: load_advice(
        workload=profiles[family], index=ROOT / INDEX, model_dir=ROOT / MODELS,
        sla_seconds=float(slas["families"][family]["sla_seconds"]),
        preferences=Preferences(), compare_to="w1_t1_2g",
    ) for family in FAMILIES}
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        revision = "unavailable; source hashes are recorded"
    snapshot = seal_manifest({
        "schema_version": 1, "run_set_id": run_set_id, "created_at": _utc(),
        "data_version": "main-v1", "host_scope": host_scope,
        "host_attestation": host_attestation,
        "host_scope_note": "Operator attestation, not automatic proof of original-host identity. Changed software is reported as environment drift.",
        "environment": env, "prepare_power": initial_power, "revision": revision,
        "verification": receipt, "verification_sha256_lf": _hash(Path(verification)),
        "original_environment_comparison": compare_original_environment(env),
        "data_dir": str(Path(data_dir).resolve()), "dataset_manifests": dataset_map,
        "profiles": {k: v.model_dump(mode="json") for k, v in profiles.items()},
        "configurations": [c.model_dump(mode="json") for c in load_grid()],
        "plan": plan["cells"], "plan_shuffle_seed": plan["shuffle_seed"],
        "advice": advice, "baseline_config_id": "w1_t1_2g", "timeout_s": timeout_s,
        "retry_policy": "no retries; one terminal attempt per planned cell",
        "source_sha256_lf": sources, "input_sha256_lf": inputs,
        "evaluation_scope": "Fresh executions of four original fixed profiles; not unseen-workload validation.",
        "timing_scope": "Model target is engine time; lifecycle timing includes cluster startup and cleanup, not prior dataset hashing or preparation.",
        "timeout_scope": "Client future-result wait timeout; graph construction, cluster startup and cleanup have no hard lifecycle time limit in the original collector.",
    })
    validate_manifest(snapshot)
    if source_hashes() != sources or input_hashes() != inputs or environment_snapshot() != env:
        raise ValueError("inputs/source/environment changed during preparation")
    study_dir.mkdir(parents=True, exist_ok=False)
    with (study_dir / "manifest.json").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(snapshot, indent=2, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    (study_dir / "attempts.jsonl").touch(exist_ok=False)
    return snapshot


def study_status(study_dir: Path) -> dict:
    manifest = load_study(study_dir)
    audit = audit_journal(manifest, read_events(study_dir))
    return {
        "run_set_id": manifest["run_set_id"], "study_id": manifest["study_id"],
        "planned_cells": len(manifest["plan"]), "terminal_attempts": len(audit["completed"]),
        "pending_attempts": [event["attempt_id"] for event in audit["pending"]],
        "cleanup_required": [event["attempt_id"] for event in audit["cleanup_required"]],
        "unstarted_cells": len(audit["missing"]),
        "complete": len(audit["completed"]) == len(manifest["plan"]) and not audit["pending"] and not audit["cleanup_required"],
        "successful_engine_jobs": sum(e["kind"] == "engine" and e["result"]["status"] == "success" for e in audit["completed"]),
        "quality_flagged_attempts": sum(bool(e.get("quality_flags")) for e in audit["completed"]),
        "note": "Terminal attempts include errors and explicit aborted attempts; completeness does not imply performance success.",
    }


def run_batch(study_dir: Path, *, max_jobs: int = 16) -> dict:
    require_windows()
    if type(max_jobs) is not int or not 1 <= max_jobs <= 96:
        raise ValueError("max_jobs must be an integer from 1 to 96")
    from safe_pipe.collector import collect_dask
    from safe_pipe.schemas import ConfigurationSpec, WorkloadFamily, WorkloadSpec
    study_dir = Path(study_dir)
    execution_lock_dir = ROOT / "data" / "runs" / ".advisor-validation-lock"
    execution_lock_dir.mkdir(parents=True, exist_ok=True)
    # Prevent overlap between different study directories in this checkout.
    # Other tools/checkouts and unrelated host workloads remain operator-controlled.
    with writer_lock(execution_lock_dir), writer_lock(study_dir):
        manifest = load_study(study_dir)
        verify_compatible(manifest)
        audit = audit_journal(manifest, read_events(study_dir))
        if audit["pending"]:
            raise ValueError("pending attempt requires explicit resolve; it must not be silently rerun")
        if audit["cleanup_required"]:
            raise ValueError("interrupted/infrastructure attempt requires explicit stopped-worker acknowledgement before another job")
        configs = {c["config_id"]: c for c in manifest["configurations"]}
        for cell in audit["missing"][:max_jobs]:
            verify_compatible(manifest, check_datasets=False)
            power_before = _power_check()
            start = {
                "event": "started", "study_id": manifest["study_id"], "run_set_id": manifest["run_set_id"],
                "attempt_id": str(uuid.uuid4()), "cell": cell, "timestamp": _utc(), "power": power_before,
            }
            _append(study_dir, start)
            started = time.perf_counter()
            family = cell["family"]
            terminal = {**start, "event": "finished", "result": None, "error": None}
            interrupted = False
            try:
                result = collect_dask(
                    family=WorkloadFamily(family), dataset_dir=Path(manifest["data_dir"]) / family,
                    workload=WorkloadSpec.model_validate(manifest["profiles"][family]),
                    config=ConfigurationSpec.model_validate(configs[cell["config_id"]]),
                    timeout_s=manifest["timeout_s"], repeat_id=cell["repeat_id"],
                    data_version=manifest["data_version"],
                    sla_seconds=manifest["advice"][family]["engine_sla_seconds"],
                )
                terminal.update(kind="engine", result=result.model_dump(mode="json"))
            except KeyboardInterrupt:
                interrupted = True
                terminal.update(kind="aborted", error="Operator interruption; engine outcome may be unknown.")
            except Exception as exc:
                terminal.update(kind="infrastructure_error", error=f"Collection/infrastructure exception; engine outcome and cleanup may be unknown. {type(exc).__name__}: {exc}"[:2000])
            terminal["lifecycle_seconds"] = time.perf_counter() - started
            terminal["timestamp"] = _utc()
            try:
                terminal["power"] = power_snapshot()
            except Exception as exc:
                terminal["power"] = {"status": "measurement_error", "error": str(exc), "power_plugged": None}
            terminal["quality_flags"] = []
            integrity_failed = False
            try:
                verify_compatible(manifest, check_datasets=False)
            except Exception as exc:
                integrity_failed = True
                terminal["quality_flags"].append("source_or_environment_changed_during_attempt")
                terminal["integrity_error"] = f"{type(exc).__name__}: {exc}"[:2000]
            if terminal["power"]["power_plugged"] is False:
                terminal["quality_flags"].append("unplugged_at_attempt_end")
            if terminal["power"]["power_plugged"] is None or power_before["power_plugged"] is None:
                terminal["quality_flags"].append("power_state_unverified")
            _append(study_dir, terminal)
            # Check immediately, before another physical job. A malformed result
            # remains in the journal as evidence; it is never silently dropped.
            audit_journal(manifest, read_events(study_dir))
            print(json.dumps({"cell": cell, "kind": terminal["kind"], "status": terminal["result"]["status"] if terminal["result"] else None}), flush=True)
            if interrupted:
                raise KeyboardInterrupt
            if integrity_failed or terminal["kind"] == "infrastructure_error" or terminal["power"]["power_plugged"] is False:
                break
    return study_status(study_dir)


def resolve_pending(study_dir: Path, *, attempt_id: str, reason: str, workers_stopped: bool = False) -> dict:
    require_windows()
    if not reason.strip() or workers_stopped is not True:
        raise ValueError("explicit recovery reason and stopped-worker confirmation are required")
    with writer_lock(study_dir):
        manifest = load_study(study_dir)
        # Recovery must remain possible after software updates, but another host
        # cannot attest that the original worker processes have stopped.
        if environment_snapshot()["node"] != manifest["environment"]["node"]:
            raise ValueError("resolve the interrupted attempt on its original Windows host")
        audit = audit_journal(manifest, read_events(study_dir))
        pending = next((e for e in audit["pending"] if e["attempt_id"] == attempt_id), None)
        if pending is None:
            raise ValueError("attempt is not pending")
        _append(study_dir, {**pending, "event": "finished", "timestamp": _utc(),
            "kind": "aborted", "result": None, "lifecycle_seconds": None,
            "error": f"Explicit recovery: {reason.strip()}",
            "quality_flags": ["interrupted_outcome_unknown"],
        })
        _append_cleanup_ack(study_dir, pending, reason)
    return study_status(study_dir)


def _append_cleanup_ack(study_dir: Path, attempt: dict, reason: str) -> None:
    _append(study_dir, {"event": "cleanup_acknowledged", "study_id": attempt["study_id"],
        "run_set_id": attempt["run_set_id"], "attempt_id": attempt["attempt_id"],
        "cell": attempt["cell"], "timestamp": _utc(), "workers_stopped": True,
        "reason": reason.strip()})


def acknowledge_cleanup(study_dir: Path, *, attempt_id: str, reason: str, workers_stopped: bool = False) -> dict:
    require_windows()
    if not reason.strip() or workers_stopped is not True:
        raise ValueError("cleanup requires a reason and explicit stopped-worker confirmation")
    with writer_lock(study_dir):
        manifest = load_study(study_dir)
        if environment_snapshot()["node"] != manifest["environment"]["node"]:
            raise ValueError("confirm cleanup on the original Windows host")
        audit = audit_journal(manifest, read_events(study_dir))
        attempt = next((e for e in audit["cleanup_required"] if e["attempt_id"] == attempt_id), None)
        if attempt is None:
            raise ValueError("attempt is not awaiting cleanup acknowledgement")
        _append_cleanup_ack(study_dir, attempt, reason)
    return study_status(study_dir)


def compare_original_environment(environment: dict) -> dict:
    """Historical T0 facts do not uniquely identify a machine; retain deviations."""
    expected = {"logical_cpus": 16, "ram_bytes": 33_711_480_832,
        "processor_prefix": "Intel64 Family 6 Model 197 Stepping 2",
        "windows_build": "26200", "python_version": "3.14.6", "dask": "2026.8.0", "distributed": "2026.8.0",
        "pandas": "3.1.0", "pyarrow": "26.0.0"}
    observed = {"logical_cpus": environment.get("logical_cpus"),
        "ram_bytes": environment.get("ram_bytes"), "processor_prefix": environment.get("processor", ""),
        "windows_build": environment.get("platform", "").split(".")[-1].split("-")[0],
        "python_version": environment.get("python", "").split()[0] if environment.get("python") else None,
        **{name: environment.get("packages", {}).get(name) for name in ("dask", "distributed", "pandas", "pyarrow")}}
    differences = [{"field": key, "historical": value, "current": observed[key]}
        for key, value in expected.items()
        if not (str(observed[key]).startswith(value) if key == "processor_prefix" else observed[key] == value)]
    return {"source": "reports/t0.md", "historical": expected, "differences": differences,
        "note": "Matching recorded fields is not proof of the original machine. Host scope is operator-attested; differences limit repeatability interpretation."}
