from safe_pipe.classify import classify_exception
from safe_pipe.schemas import FailureCategory, RunStatus


def test_timeout_token() -> None:
    status, category = classify_exception(TimeoutError("job timeout"))
    assert status is RunStatus.TIMEOUT
    assert category is FailureCategory.ACTIONABLE


def test_killed_worker_is_oom() -> None:
    status, category = classify_exception(RuntimeError("KilledWorker memory"))
    assert status is RunStatus.OOM
    assert category is FailureCategory.ACTIONABLE
