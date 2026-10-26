"""Render LightGBM feature contributions for the sort workload recommendation."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from safe_pipe.models.ood import OODGate
from safe_pipe.models.runtime import RuntimePredictor, encoded_features
from safe_pipe.optimizer import recommend
from safe_pipe.policy import candidate_frame, estimate_candidates
from safe_pipe.schemas import DatasetManifest, ObjectiveSpec, WorkloadFamily
from safe_pipe.workloads.generate import workload_from_manifest


def main() -> int:
    model_dir = Path("artifacts/main_v1")
    output = Path("reports")
    meta = json.loads((model_dir / "runtime_meta.json").read_text(encoding="utf-8"))
    profiles = json.loads((model_dir / "ood_profiles.json").read_text(encoding="utf-8"))["bytes_by_family"]
    manifests = [DatasetManifest.model_validate(item) for item in json.loads(Path("configs/datasets_main_v1.json").read_text(encoding="utf-8"))]
    manifest = next(item for item in manifests if item.family is WorkloadFamily.SORT_MERGE)
    workload = workload_from_manifest(manifest, skew_score=0.1)
    predictor = RuntimePredictor(model_dir / "runtime_model.txt", meta["feature_names"], meta["upper_log_offset"])
    estimates = estimate_candidates(workload, predictor, OODGate(profiles))
    sla = json.loads(Path("configs/family_sla_main_v1.json").read_text(encoding="utf-8"))["families"]["sort_merge"]["sla_seconds"]
    decision = recommend(estimates, ObjectiveSpec(sla_seconds=sla))
    if decision.config_id is None:
        raise RuntimeError("sort workload unexpectedly abstained")
    row = candidate_frame(workload).loc[lambda frame: frame.config_id == decision.config_id]
    encoded = encoded_features(row).reindex(columns=meta["feature_names"], fill_value=0.0)
    contributions = predictor.booster.predict(encoded, pred_contrib=True)[0]
    point, _ = predictor.predict(row)
    if not np.isclose(contributions.sum(), np.log(point[0]), atol=1e-5):
        raise ValueError("LightGBM contributions do not sum to predicted log runtime")
    values = pd.Series(contributions[:-1], index=meta["feature_names"], name="contribution_log_seconds")
    values = values.loc[values.abs().sort_values(ascending=False).index]
    top = values.head(8)
    remainder = float(values.iloc[8:].sum())
    display = pd.concat([top, pd.Series({"other features": remainder})])
    display.to_csv(output / "shap_sort_merge.csv", header=True)

    ordered = display.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    colors = ["#2463a6" if value < 0 else "#d36b2d" for value in ordered]
    ax.barh(ordered.index, ordered.values, color=colors)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Contribution to predicted log runtime (seconds)")
    ax.set_title(f"Sort/merge: {decision.config_id} (predicted {point[0]:.2f} s)")
    fig.tight_layout()
    fig.savefig(output / "shap_sort_merge.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"config_id": decision.config_id, "point_seconds": float(point[0]), "base_log_seconds": float(contributions[-1]), "plot": str(output / "shap_sort_merge.png")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
