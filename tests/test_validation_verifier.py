"""Boundary checks for the Windows verification handoff; executed on Windows."""
import pytest

from experiments import verify_main_validation as verifier


def test_non_windows_guard_precedes_writes_or_subprocesses(tmp_path, monkeypatch):
    monkeypatch.setattr(verifier.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(verifier.subprocess, "run", lambda *a, **k: pytest.fail("subprocess started"))
    out = tmp_path / "never-created"
    with pytest.raises(ValueError, match="Windows"):
        verifier.verify(out)
    assert not out.exists()


def test_junit_keeps_failed_and_skipped_tests_visible(tmp_path):
    path = tmp_path / "tests.xml"
    path.write_text(
        '<testsuites><testsuite><testcase name="pass"/>'
        '<testcase name="bad"><failure/></testcase>'
        '<testcase name="broken"><error/></testcase>'
        '<testcase name="absent"><skipped/></testcase></testsuite></testsuites>',
        encoding="utf-8",
    )
    assert verifier.test_counts(path) == {
        "collected": 4, "passed": 1, "failed": 1, "errors": 1, "skipped": 1,
    }


def test_fingerprints_bind_tests_and_frozen_evidence_normalizing_newlines(tmp_path):
    for relative in ("safe_pipe/a.py", "experiments/b.py", "tests/c.py", "pyproject.toml",
                     "data/curated/runs.csv", "configs/grid.json", "artifacts/main_v1/runtime_model.txt"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"one\r\ntwo\r\n")
    baseline = verifier.fingerprints(tmp_path)
    (tmp_path / "tests/c.py").write_bytes(b"one\ntwo\n")
    assert verifier.fingerprints(tmp_path) == baseline
    (tmp_path / "tests/c.py").write_bytes(b"changed test\n")
    assert verifier.fingerprints(tmp_path) != baseline
    assert "data/curated/runs.csv" in baseline
    assert "artifacts/main_v1/runtime_model.txt" in baseline


def test_verification_refuses_existing_report_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(verifier.platform, "system", lambda: "Windows")
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    out = tmp_path / "reports/checks"
    out.mkdir(parents=True)
    marker = out / "keep.txt"
    marker.write_text("original", encoding="utf-8")
    with pytest.raises(ValueError, match="NEW"):
        verifier.verify(out)
    assert marker.read_text(encoding="utf-8") == "original"
