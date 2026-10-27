from __future__ import annotations

from safe_pipe.schemas import (
    CandidateEstimate,
    Decision,
    DecisionAction,
    ObjectiveSpec,
    OODState,
)


def is_feasible(estimate: CandidateEstimate, objective: ObjectiveSpec) -> bool:
    """Apply supplied upper/risk estimates and an unconditional hard guard."""
    if not estimate.guard_pass:
        return False
    if estimate.ood_state is OODState.RED:
        return False
    if estimate.runtime_upper_s > objective.sla_seconds:
        return False
    if estimate.p_fail > objective.failure_limit:
        return False
    return True


def recommend(estimates: list[CandidateEstimate], objective: ObjectiveSpec) -> Decision:
    if not estimates:
        return Decision(
            action=DecisionAction.ABSTAIN,
            reason="empty candidate set",
            feasible_config_ids=[],
        )

    feasible = [e for e in estimates if is_feasible(e, objective)]
    ids = [e.config_id for e in feasible]
    if not feasible:
        return Decision(
            action=DecisionAction.ABSTAIN,
            reason="no candidate satisfies SLA upper bound, failure limit, and OOD policy",
            feasible_config_ids=[],
        )

    best = min(feasible, key=lambda e: (e.expected_cost, e.runtime_upper_s, e.config_id))
    return Decision(
        action=DecisionAction.RECOMMEND,
        config_id=best.config_id,
        reason="lowest supplied cost among candidates passing guards and runtime upper <= SLA",
        feasible_config_ids=ids,
    )
