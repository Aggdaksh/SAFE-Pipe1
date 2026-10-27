from __future__ import annotations

import re

from safe_pipe.schemas import FailureCategory, RunStatus


def classify_exception(exc: BaseException) -> tuple[RunStatus, FailureCategory]:
    text = f"{type(exc).__name__} {exc}".lower().replace("_", " ").replace("-", " ")
    if isinstance(exc, MemoryError):
        return RunStatus.OOM, FailureCategory.ACTIONABLE
    if "timeout" in text:
        return RunStatus.TIMEOUT, FailureCategory.ACTIONABLE
    # Worker death alone does not establish an OOM: nannies also restart workers
    # after unrelated crashes. Require an explicit memory-limit termination cause.
    termination = re.search(r"\b(?:killed|terminated|terminating|restarted|restarting)\b", text)
    limit_violation = re.search(
        r"\b(?:exceed(?:ed|s|ing)?|reached)\b[^.;\n]{0,40}\bmemory\s+(?:limit|budget)\b", text
    )
    limit_cause = re.search(
        r"\b(?:due to|because of)\s+(?:(?:its|the|a|configured)\s+)*memory\s+(?:limit|budget)\b", text
    )
    if termination and (limit_violation or limit_cause):
        return RunStatus.OOM, FailureCategory.ACTIONABLE
    if re.search(r"\bspill(?:ing)?\s+abort(?:ed|ing)?\b", text) or re.search(
        r"\babort(?:ed|ing)?\s+due to\s+(?:excessive\s+)?spill(?:ing)?\b", text
    ):
        return RunStatus.SPILL_ABORT, FailureCategory.ACTIONABLE
    if any(
        token in text
        for token in (
            "killedworker", "nanny", "worker exceeded", "worker died", "worker killed",
            "worker terminated", "lost", "disconnected", "cancelled",
        )
    ):
        return RunStatus.ERROR, FailureCategory.TRANSIENT
    return RunStatus.ERROR, FailureCategory.NON_CONFIGURATION


def category_for_status(status: RunStatus) -> FailureCategory:
    if status is RunStatus.SUCCESS:
        return FailureCategory.NONE
    if status in {RunStatus.TIMEOUT, RunStatus.OOM, RunStatus.SPILL_ABORT}:
        return FailureCategory.ACTIONABLE
    return FailureCategory.NON_CONFIGURATION
