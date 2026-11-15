"""Run on the Windows experiment host; these fixtures do not imply physical OOM."""
import json
import logging

from safe_pipe.research import probe_diagnostics as diagnostics


def write_log(path, message, phase="execution"):
    with path.open("a") as stream:
        stream.write(json.dumps({"utc": "fixture", "logger": "distributed.nanny.memory",
                                 "phase": phase, "message": message}) + "\n")


def test_killed_worker_alone_does_not_become_oom(tmp_path):
    result = diagnostics.summarize_diagnostics(tmp_path, {"status": "execution_error", "error": "KilledWorker"})
    assert result["failure_category"] == "worker_death_unknown_cause"
    assert result["nanny_memory_termination_count"] == 0


def test_evidence_and_exit_codes_are_preserved_but_cleanup_is_excluded(tmp_path):
    path = tmp_path / "supervisor.jsonl"
    write_log(path, "Worker tcp://local (pid=1) exceeded 95% memory budget. Restarting...")
    write_log(path, "Worker process 1 exited with status 15")
    write_log(path, "Worker process 2 was killed by signal 9", "cleanup")
    result = diagnostics.summarize_diagnostics(tmp_path, {"status": "execution_error", "error": "KilledWorker"})
    assert result["nanny_memory_termination_count"] == 1
    assert result["failure_category"] == "worker_death_with_nanny_memory_termination_evidence"
    assert [e["exit_status"] for e in result["worker_exit_events"]] == [15]
    assert len(result["files"][0]["sha256"]) == 64
    timeout = diagnostics.summarize_diagnostics(tmp_path, {"status": "timeout"})
    assert timeout["failure_category"] == "timeout"
    assert timeout["nanny_memory_termination_count"] == 1


def test_signal_alone_is_unknown_and_truncated_tail_is_explicit(tmp_path):
    path = tmp_path / "supervisor.jsonl"
    write_log(path, "Worker process 12 was killed by signal 9")
    with path.open("a") as stream:
        stream.write('{"incomplete":')
    result = diagnostics.summarize_diagnostics(tmp_path, {"status": "execution_error"})
    assert result["failure_category"] == "worker_death_unknown_cause"
    assert result["malformed_log_lines"] == 1


def test_durable_logger_is_not_console_handler_and_marks_size_limit(tmp_path, monkeypatch):
    path = tmp_path / "bounded.jsonl"
    monkeypatch.setattr(diagnostics, "MAX_LOG_BYTES", 10)
    handler = diagnostics.DiagnosticLog(path)
    assert not isinstance(handler, logging.StreamHandler)
    handler.handle(logging.LogRecord("distributed.nanny", logging.INFO, "", 0, "long enough message", (), None))
    handler.close()
    assert json.loads(path.read_text())["event"] == "log_truncated"
