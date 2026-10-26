from __future__ import annotations

import argparse
import json
from pathlib import Path

from safe_pipe import __version__
from safe_pipe.grid import load_grid
from safe_pipe.optimizer import recommend
from safe_pipe.schemas import CandidateEstimate, ObjectiveSpec, WorkloadFamily
from safe_pipe.workloads.generate import generate_family, write_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="safe-pipe")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="cmd")

    rec = sub.add_parser("recommend", help="Rank candidate estimates from a JSON file")
    rec.add_argument("--estimates", required=True, help="JSON list of CandidateEstimate")
    rec.add_argument("--sla", type=float, required=True)
    rec.add_argument("--failure-limit", type=float, default=0.1)

    fitted = sub.add_parser("recommend-model", help="Predict eight candidates from the fitted Dask artifacts")
    source = fitted.add_mutually_exclusive_group(required=True)
    source.add_argument("--family", choices=[f.value for f in WorkloadFamily])
    source.add_argument("--workload-json", type=Path)
    fitted.add_argument("--sla", type=float, required=True)
    fitted.add_argument("--failure-limit", type=float, default=0.1)
    fitted.add_argument("--index", type=Path, default=Path("configs/datasets_main_v1.json"))
    fitted.add_argument("--model-dir", type=Path, default=Path("artifacts/main_v1"))

    profile = sub.add_parser("profile", help="Print a frozen pre-run workload profile")
    profile.add_argument("--family", required=True, choices=[f.value for f in WorkloadFamily])
    profile.add_argument("--index", type=Path, default=Path("configs/datasets_main_v1.json"))

    execute = sub.add_parser("execute", help="Execute one Dask workload and append a demo run record")
    execute.add_argument("--family", required=True, choices=[f.value for f in WorkloadFamily])
    execute.add_argument("--config-id", required=True)
    execute.add_argument("--data-dir", type=Path, default=Path("data/demo"))
    execute.add_argument("--store", type=Path, default=Path("data/runs/demo.jsonl"))
    execute.add_argument("--timeout", type=float, default=60.0)
    execute.add_argument("--sla", type=float)

    sub.add_parser("grid", help="Print the frozen 8 Dask configs")

    gen = sub.add_parser("generate", help="Write tiny Parquet families (8GB-Mac safe)")
    gen.add_argument("--dest", default="data/generated")
    gen.add_argument("--family", choices=[f.value for f in WorkloadFamily], action="append")

    col = sub.add_parser("collect", help="Run one tiny pandas cell and append JSONL")
    col.add_argument("--family", required=True, choices=[f.value for f in WorkloadFamily])
    col.add_argument("--config-id", default="w1_t1_1g")
    col.add_argument("--data-dir", default="data/generated")
    col.add_argument("--store", default="data/runs/runs.jsonl")
    col.add_argument("--timeout", type=float, default=30.0)

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if args.cmd == "recommend":
        with open(args.estimates, encoding="utf-8") as fh:
            raw = json.load(fh)
        estimates = [CandidateEstimate.model_validate(row) for row in raw]
        decision = recommend(estimates, ObjectiveSpec(sla_seconds=args.sla, failure_limit=args.failure_limit))
        print(decision.model_dump_json(indent=2))
        return 0
    if args.cmd == "recommend-model":
        from safe_pipe.models.ood import OODGate
        from safe_pipe.models.runtime import RuntimePredictor
        from safe_pipe.policy import estimate_candidates
        from safe_pipe.schemas import DatasetManifest, WorkloadSpec
        from safe_pipe.workloads.generate import workload_from_manifest

        if args.workload_json:
            workload = WorkloadSpec.model_validate_json(args.workload_json.read_text(encoding="utf-8"))
        else:
            manifests = [DatasetManifest.model_validate(item) for item in json.loads(args.index.read_text(encoding="utf-8"))]
            manifest = next(item for item in manifests if item.family.value == args.family)
            workload = workload_from_manifest(manifest, skew_score=1.2 if manifest.family is WorkloadFamily.SKEWED_JOIN else 0.1)
        meta = json.loads((args.model_dir / "runtime_meta.json").read_text(encoding="utf-8"))
        ood = json.loads((args.model_dir / "ood_profiles.json").read_text(encoding="utf-8"))
        predictor = RuntimePredictor(args.model_dir / "runtime_model.txt", meta["feature_names"], meta["upper_log_offset"])
        estimates = estimate_candidates(workload, predictor, OODGate(ood["bytes_by_family"]))
        objective = ObjectiveSpec(sla_seconds=args.sla, failure_limit=args.failure_limit)
        decision = recommend(estimates, objective)
        print(json.dumps({
            "workload": workload.model_dump(mode="json"),
            "objective": objective.model_dump(mode="json"),
            "candidates": [item.model_dump(mode="json") for item in estimates],
            "decision": decision.model_dump(mode="json"),
            "risk_note": "p_fail is a deterministic guard flag; all 96 measured jobs succeeded, so failure probabilities are not calibrated",
        }, indent=2))
        return 0
    if args.cmd == "profile":
        from safe_pipe.schemas import DatasetManifest
        from safe_pipe.workloads.generate import workload_from_manifest

        manifests = [DatasetManifest.model_validate(item) for item in json.loads(args.index.read_text(encoding="utf-8"))]
        manifest = next(item for item in manifests if item.family.value == args.family)
        workload = workload_from_manifest(manifest, skew_score=1.2 if manifest.family is WorkloadFamily.SKEWED_JOIN else 0.1)
        print(workload.model_dump_json(indent=2))
        return 0
    if args.cmd == "execute":
        from safe_pipe.collector import collect_dask
        from safe_pipe.grid import get_config
        from safe_pipe.schemas import DatasetManifest, RunStatus
        from safe_pipe.store.jsonl import append_run
        from safe_pipe.workloads.generate import verify_manifest, workload_from_manifest

        family = WorkloadFamily(args.family)
        dataset_dir = args.data_dir / family.value
        manifest = DatasetManifest.model_validate_json((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
        if manifest.family is not family:
            raise ValueError("dataset manifest family does not match requested family")
        verify_manifest(manifest, dataset_dir)
        result = collect_dask(
            family=family,
            dataset_dir=dataset_dir,
            workload=workload_from_manifest(manifest, skew_score=1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1),
            config=get_config(args.config_id),
            timeout_s=args.timeout,
            data_version=manifest.data_version,
            sla_seconds=args.sla,
        )
        append_run(args.store, result)
        print(result.model_dump_json(indent=2))
        return 0 if result.status is RunStatus.SUCCESS else 1
    if args.cmd == "grid":
        print(json.dumps([c.model_dump() for c in load_grid()], indent=2))
        return 0
    if args.cmd == "generate":
        families = [WorkloadFamily(f) for f in (args.family or [x.value for x in WorkloadFamily])]
        dest = Path(args.dest)
        manifests = [generate_family(family, dest) for family in families]
        write_index(dest, manifests)
        print(json.dumps([m.model_dump() for m in manifests], indent=2))
        return 0
    if args.cmd == "collect":
        from safe_pipe.collector import collect_pandas
        from safe_pipe.grid import get_config
        from safe_pipe.store.jsonl import append_run
        from safe_pipe.workloads.generate import workload_from_manifest

        family = WorkloadFamily(args.family)
        dest = Path(args.data_dir)
        manifest = generate_family(family, dest)
        skew = 1.2 if family is WorkloadFamily.SKEWED_JOIN else 0.1
        result = collect_pandas(
            family=family,
            dataset_dir=Path(manifest.path),
            workload=workload_from_manifest(manifest, skew_score=skew),
            config=get_config(args.config_id),
            timeout_s=args.timeout,
        )
        append_run(Path(args.store), result)
        print(result.model_dump_json(indent=2))
        return 0 if result.status.value == "success" else 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
