"""Replay frozen profiles for descriptive policy/weight sensitivity, without fitting.

The source table overlaps model fitting. Output is NOT independent validation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from safe_pipe.advisor import Preferences, frozen_profiles, load_advice, sha256_lf
from safe_pipe.cost import resource_score
from safe_pipe.memory import dask_memory_bytes
from safe_pipe.grid import load_grid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/advisor_v1"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; use a new path to preserve the recorded replay")
    index = Path("configs/datasets_main_v1.json")
    profiles = frozen_profiles(index)
    slas = json.loads(Path("configs/family_sla_main_v1.json").read_text())["families"]
    table_path = Path("data/curated/runs.csv")
    bundle = json.loads(Path("artifacts/main_v1/advisor_support.json").read_text(encoding="utf-8"))
    if sha256_lf(table_path) != bundle["table_sha256_lf"]:
        raise ValueError("replay table differs from the frozen audited table")
    table = pd.read_csv(table_path)
    configs = {c.config_id: c for c in load_grid()}
    settings = [(mode, 0.5) for mode in ("balanced", "resource", "fastest")] + [("balanced", w) for w in (0.25, 0.75)]
    rows, reports = [], {}
    for family, workload in profiles.items():
        for mode, weight in settings:
            preferences = Preferences(mode=mode, thread_weight=weight)
            sla = float(slas[family]["sla_seconds"])
            report = load_advice(workload=workload, index=index, model_dir=Path("artifacts/main_v1"),
                                 sla_seconds=sla, preferences=preferences)
            decision = report["decision"]
            selected = decision["config_id"]
            if mode == "balanced" and weight == 0.5:
                reports[family] = report
            row = {"family": family, "mode": mode, "thread_weight": weight,
                   "action": decision["action"], "config_id": selected, "engine_sla_seconds": sla}
            if selected:
                measured = table[(table.family == family) & (table.config_id == selected)]
                if len(measured) != 3 or measured.repeat_id.nunique() != 3:
                    raise ValueError("expected three recorded repeats for selected cell")
                config = configs[selected]
                threads = config.native.n_workers * config.native.threads_per_worker
                memory = config.native.n_workers * dask_memory_bytes(config.native.memory_limit)
                median = float(measured.engine_seconds.median())
                observed = resource_score(median, threads, memory, time_reference_s=sla, thread_weight=weight)
                speed_weight = {"balanced": 0.5, "resource": 0, "fastest": 1}[mode]
                candidate = next(c for c in report["candidates"] if c["config_id"] == selected)
                row.update({"predicted_runtime_s": candidate["predicted_runtime_s"],
                            "runtime_upper_s": candidate["runtime_upper_s"],
                            "predicted_score": candidate["score"],
                            "recorded_median_runtime_s": median,
                            "recorded_repeats": len(measured),
                            "recorded_violations": int(((measured.status != "success") | (measured.engine_seconds > sla)).sum()),
                            "recorded_median_score": (1-speed_weight)*observed["resource_score"]+speed_weight*observed["time_ratio"]})
            rows.append(row)
    args.output.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(args.output / "sensitivity.csv", index=False)
    (args.output / "balanced_examples.json").write_text(json.dumps(reports, indent=2) + "\n")
    (args.output / "summary.json").write_text(json.dumps({
        "evaluation": "descriptive same-table replay; no fitting or independent improvement claim",
        "table_sha256_lf": bundle["table_sha256_lf"],
        "distinct_workload_profiles": len(profiles), "scenarios": len(rows),
        "accepted_scenarios": sum(r["action"] == "recommend" for r in rows),
        "note": "Weight/mode scenarios reuse the same measurements and are not independent experiments. No weights were tuned against these outcomes.",
    }, indent=2) + "\n")
    print(f"Wrote {len(rows)} descriptive scenarios to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
