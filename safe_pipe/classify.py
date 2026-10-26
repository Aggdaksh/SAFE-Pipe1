from __future__ import annotations

from safe_pipe.schemas import FailureCategory, RunStatus


def classify_exception(exc: BaseException) -> tuple[RunStatus, FailureCategory]:
    text = f"{type(exc).__name__} {exc}".lower()
    if "timeout" in text:
        return RunStatus.TIMEOUT, FailureCategory.ACTIONABLE
    if any(token in text for token in ("killedworker", "memoryerror", "nanny", "worker exceeded")):
        return RunStatus.OOM, FailureCategory.ACTIONABLE
    if "spill" in text:
        return RunStatus.SPILL_ABORT, FailureCategory.ACTIONABLE
    if any(token in text for token in ("lost", "disconnected", "cancelled")):
        return RunStatus.ERROR, FailureCategory.TRANSIENT
    return RunStatus.ERROR, FailureCategory.NON_CONFIGURATION


def category_for_status(status: RunStatus) -> FailureCategory:
    if status is RunStatus.SUCCESS:
        return FailureCategory.NONE
    if status in {RunStatus.TIMEOUT, RunStatus.OOM, RunStatus.SPILL_ABORT}:
        return FailureCategory.ACTIONABLE
    return FailureCategory.NON_CONFIGURATION
