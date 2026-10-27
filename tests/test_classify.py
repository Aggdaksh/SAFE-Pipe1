import pytest

from safe_pipe.classify import classify_exception
from safe_pipe.schemas import FailureCategory, RunStatus


def test_timeout_token() -> None:
    status, category = classify_exception(TimeoutError("job timeout"))
    assert status is RunStatus.TIMEOUT
    assert category is FailureCategory.ACTIONABLE


@pytest.mark.parametrize(
    "exc",
    [
        MemoryError("allocation failed"),
        RuntimeError("Worker exceeded 95% memory budget. Restarting worker"),
        RuntimeError("Nanny: worker terminated due to memory_limit"),
        RuntimeError("Worker killed because of exceeded memory limit"),
    ],
)
def test_oom_requires_memory_failure_evidence(exc: BaseException) -> None:
    status, category = classify_exception(exc)
    assert status is RunStatus.OOM
    assert category is FailureCategory.ACTIONABLE


@pytest.mark.parametrize(
    "message",
    [
        "KilledWorker memory",
        "KilledWorker: task failed on 4 workers",
        "Nanny restarting worker after a crash",
        "Worker exceeded retry budget",
        "Worker terminated while spilling to disk",
        "Worker killed; configured memory limit is 1GB",
        "Worker terminated due to network failure; memory limit is 1GB",
        "Worker died unexpectedly",
        "Worker disconnected",
    ],
)
def test_worker_loss_does_not_establish_oom(message: str) -> None:
    assert classify_exception(RuntimeError(message)) == (
        RunStatus.ERROR,
        FailureCategory.TRANSIENT,
    )


@pytest.mark.parametrize("message", ["spill_abort: budget reached", "Spill aborted", "Run aborted due to excessive spilling"])
def test_explicit_spill_abort(message: str) -> None:
    assert classify_exception(RuntimeError(message)) == (
        RunStatus.SPILL_ABORT,
        FailureCategory.ACTIONABLE,
    )


@pytest.mark.parametrize(
    "message",
    ["Could not open spill directory", "Invalid spill configuration", "memory limit unavailable", "MemoryError is the name of a metric"],
)
def test_resource_mention_alone_is_not_actionable(message: str) -> None:
    assert classify_exception(RuntimeError(message)) == (
        RunStatus.ERROR,
        FailureCategory.NON_CONFIGURATION,
    )
