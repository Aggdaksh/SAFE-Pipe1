from safe_pipe.optimizer import recommend
from safe_pipe.schemas import CandidateEstimate, DecisionAction, ObjectiveSpec, OODState


def _est(**kwargs) -> CandidateEstimate:
    base = dict(
        config_id="a",
        expected_runtime_s=10.0,
        runtime_upper_s=12.0,
        p_fail=0.02,
        expected_cost=5.0,
        ood_state=OODState.GREEN,
    )
    base.update(kwargs)
    return CandidateEstimate.model_validate(base)


def test_picks_lowest_cost_feasible() -> None:
    estimates = [
        _est(config_id="cheap_slow", expected_cost=1.0, runtime_upper_s=40.0, expected_runtime_s=30.0),
        _est(config_id="mid", expected_cost=3.0, runtime_upper_s=12.0),
        _est(config_id="pricey_fast", expected_cost=9.0, runtime_upper_s=11.0, expected_runtime_s=9.0),
    ]
    decision = recommend(estimates, ObjectiveSpec(sla_seconds=15, failure_limit=0.1))
    assert decision.action is DecisionAction.RECOMMEND
    assert decision.config_id == "mid"


def test_uses_conformal_upper_not_point_estimate() -> None:
    estimates = [
        _est(
            config_id="optimistic_point",
            expected_runtime_s=8.0,
            runtime_upper_s=25.0,
            expected_cost=1.0,
        )
    ]
    decision = recommend(estimates, ObjectiveSpec(sla_seconds=10, failure_limit=0.1))
    assert decision.action is DecisionAction.ABSTAIN


def test_red_ood_never_recommended() -> None:
    estimates = [
        _est(config_id="red", ood_state=OODState.RED, expected_cost=0.1, runtime_upper_s=5.0, expected_runtime_s=4.0)
    ]
    decision = recommend(estimates, ObjectiveSpec(sla_seconds=30, failure_limit=0.5))
    assert decision.action is DecisionAction.ABSTAIN


def test_yellow_may_still_be_recommended() -> None:
    estimates = [_est(config_id="y", ood_state=OODState.YELLOW, expected_cost=2.0)]
    decision = recommend(estimates, ObjectiveSpec(sla_seconds=15, failure_limit=0.1))
    assert decision.action is DecisionAction.RECOMMEND
    assert decision.config_id == "y"


def test_empty_abstains() -> None:
    decision = recommend([], ObjectiveSpec(sla_seconds=10))
    assert decision.action is DecisionAction.ABSTAIN
