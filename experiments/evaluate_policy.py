"""Descriptive same-table policy/default/conservative/random comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from safe_pipe.models.ood import OODGate
from safe_pipe.models.runtime import RuntimePredictor
from safe_pipe.optimizer import recommend
from safe_pipe.policy import estimate_candidates
from safe_pipe.schemas import DatasetManifest, ObjectiveSpec, OODState, WorkloadFamily
from safe_pipe.workloads.generate import workload_from_manifest


def main() -> int:
    output = Path("reports")
    table = pd.read_csv("data/curated/runs.csv")
    manifests = {m.family: m for value in json.loads(Path("configs/datasets_main_v1.json").read_text(encoding="utf-8")) for m in [DatasetManifest.model_validate(value)]}
    sla = json.loads(Path("configs/family_sla_main_v1.json").read_text(encoding="utf-8"))["families"]
    model_dir = Path("artifacts/main_v1")
    meta = json.loads((model_dir / "runtime_meta.json").read_text(encoding="utf-8"))
    profiles = json.loads((model_dir / "ood_profiles.json").read_text(encoding="utf-8"))["bytes_by_family"]
    predictor = RuntimePredictor(model_dir / "runtime_model.txt", meta["feature_names"], meta["upper_log_offset"])
    gate = OODGate(profiles)
    table["normalized_cost"] = table.engine_seconds * (table.allocated_vcpus + table.allocated_gb)
    per_config = table.groupby(["family", "config_id"]).agg(
        median_cost=("normalized_cost", "median"),
        sla_misses=("sla_miss", "sum"),
    )
    rows = []
    for family in WorkloadFamily:
        workload = workload_from_manifest(manifests[family], skew_score=1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1)
        objective = ObjectiveSpec(sla_seconds=float(sla[family.value]["sla_seconds"]))
        decision = recommend(estimate_candidates(workload, predictor, gate), objective)
        if decision.config_id is None:
            raise RuntimeError(f"policy abstained on measured family {family.value}")
        family_costs = per_config.loc[family.value]
        selected = family_costs.loc[decision.config_id]
        rows.append(
            {
                "family": family.value,
                "policy_config": decision.config_id,
                "policy_median_cost": float(selected.median_cost),
                "default_config": "w1_t1_2g",
                "default_median_cost": float(family_costs.loc["w1_t1_2g"].median_cost),
                "conservative_config": "w2_t2_2g",
                "conservative_median_cost": float(family_costs.loc["w2_t2_2g"].median_cost),
                "random_expected_median_cost": float(family_costs.median_cost.mean()),
                "policy_any_sla_miss": bool(selected.sla_misses),
                "ood_state": gate.classify(workload).value,
            }
        )
    comparison = pd.DataFrame(rows)
    comparison.to_csv(output / "policy_comparison.csv", index=False)
    heldout_ood = {}
    for family in WorkloadFamily:
        holdout_gate = OODGate({name: size for name, size in profiles.items() if name != family.value})
        workload = workload_from_manifest(manifests[family], skew_score=1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1)
        heldout_ood[family.value] = holdout_gate.classify(workload).value
    metrics = {
        "data_version": "main-v1",
        "evaluation": "descriptive same-table comparison; fitted model trained on some cells in this table",
        "families": len(comparison),
        "policy_abstentions_on_known_families": 0,
        "policy_unsafe_families": int(comparison.policy_any_sla_miss.sum()),
        "mean_policy_median_cost": float(comparison.policy_median_cost.mean()),
        "mean_default_median_cost": float(comparison.default_median_cost.mean()),
        "mean_conservative_median_cost": float(comparison.conservative_median_cost.mean()),
        "mean_random_expected_median_cost": float(comparison.random_expected_median_cost.mean()),
        "policy_cost_change_vs_default_percent": float(100 * (comparison.policy_median_cost.mean() / comparison.default_median_cost.mean() - 1)),
        "heldout_family_gate_states": heldout_ood,
        "heldout_red_count": sum(state == OODState.RED.value for state in heldout_ood.values()),
        "failure_limit": "all 96 jobs succeeded; p_fail is a rule flag, not calibrated",
    }
    (output / "policy_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
