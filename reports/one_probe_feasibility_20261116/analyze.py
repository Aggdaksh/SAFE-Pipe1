"""Descriptive single-probe replay of committed evidence; standard library only.

No SAFE-Pipe imports, parameter fitting, execution tests, jobs or training.
One observation per decision; separate-session full repeats are not paired.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    spec_path = ROOT / "configs/research_one_probe_v1.json"
    spec = read_json(spec_path)
    a_root, b_root = [ROOT / f"reports/research_stage_{s}_windows_v1" for s in ("a", "b")]
    a, b = read_csv(a_root / "measurements.csv"), read_csv(b_root / "measurements.csv")
    a_plan, b_plan = read_json(a_root / "plan.json"), read_json(b_root / "plan.json")
    worker_path = ROOT / "reports/worker_memory_stage_a_b_v1/workers.json"
    workers = read_json(worker_path)
    by_cell = defaultdict(list)
    for worker in workers:
        by_cell[worker["cell_id"]].append(worker)
    recipes = {r["instance_id"]: r for r in a_plan["recipes"]}
    obj = spec["objective"]

    def score(row):
        active, wall = float(row["total_seconds"]), float(row["end_to_end_seconds"])
        count, threads, memory = int(row["n_workers"]), int(row["threads_per_worker"]), int(row["effective_memory_bytes"])
        return (obj["time_weight"] * wall + obj["threads_weight"] * count * threads * active / obj["normalization_threads"]
                + obj["memory_weight"] * count * memory * active / obj["normalization_memory_bytes"])

    def outcomes(instance, config):
        rows = [r for r in a if r["instance_id"] == instance and r["target_config_id"] == config]
        ref = [r for r in b_plan["reference"]["outcomes"] if r["instance_id"] == instance and r["target_config_id"] == config]
        assert len(rows) == len(ref) == 3
        assert {r["cell_id"] for r in rows} == {r["cell_id"] for r in ref}
        return {"statuses": dict(Counter(r["status"] for r in rows)), "signals": dict(Counter(r["signal"] for r in ref)),
                "median_all_attempt_wall_seconds": median(float(r["end_to_end_seconds"]) for r in rows),
                "median_all_attempt_proxy_score": median(score(r) for r in rows)}

    details = []
    for instance, descriptor in sorted(b_plan["reference"]["datasets"].items()):
        recipe = recipes[instance]
        row_bytes = spec["numeric_column_bytes"] * (1 + recipe["payload_columns"])
        total_bytes = descriptor["fact_rows"] * row_bytes + descriptor["dimension_rows"] * 2 * spec["numeric_column_bytes"]
        largest_bytes = max(descriptor["source_partition_rows"]) * row_bytes
        common = spec["metadata_reserve_bytes"] + total_bytes / spec["n_workers"]
        estimates = [common + spec[k] * largest_bytes for k in ("metadata_lower_copy_factor", "metadata_upper_copy_factor")]
        low, high = spec["low_config_id"], spec["high_config_id"]
        metadata_choice = low if estimates[1] <= spec["metadata_capacity_fraction"] * spec["low_memory_bytes"] else high
        assert estimates[1] <= spec["metadata_capacity_fraction"] * spec["high_memory_bytes"]
        ambiguous = estimates[0] <= spec["metadata_capacity_fraction"] * spec["low_memory_bytes"] < estimates[1]
        full = {config: outcomes(instance, config) for config in (low, high)}
        probes = [r for r in b if r["instance_id"] == instance and r["target_config_id"] == low and float(r["fraction"]) == spec["probe_fraction"]]
        assert len(probes) == 3 and {int(r["repeat_id"]) for r in probes} == {1, 2, 3}
        preparation = b_plan["sample_metadata"][instance]["uniform_memory_f0250"]["preparation_seconds"]
        probe_decisions = []
        for probe in probes:
            records = by_cell[probe["cell_id"]]
            assert len(records) == 2 and all(r["stage"] == "B" and not r["missing_worker_fields"] and r["sampling_errors"] == 0 for r in records)
            assert probe["fidelity_signal"] == "quiet" and probe["status"] == "success"
            assert int(probe["effective_memory_bytes"]) == spec["probe_effective_memory_bytes"]
            ratio = max(r["peak_rss_bytes"] / r["effective_memory_limit_bytes"] for r in records)
            probe_decisions.append({"probe_cell_id": probe["cell_id"], "repeat_id": int(probe["repeat_id"]),
                "peak_ratio": ratio, "selected_config": low if ratio < spec["probe_peak_ratio_cutoff"] else high,
                "profile_wall_seconds": preparation + float(probe["end_to_end_seconds"]),
                "profile_proxy_score_lower_bound": score(probe) + obj["time_weight"] * preparation})
        # Do not choose a favorable repeat or let the decision see another probe.
        # All three happen to agree here; keep each observation in the artifact.
        choices = {r["selected_config"] for r in probe_decisions}
        assert len(choices) == 1
        probe_choice = next(iter(choices))
        profile_wall = median(r["profile_wall_seconds"] for r in probe_decisions)
        profile_score = median(r["profile_proxy_score_lower_bound"] for r in probe_decisions)
        row_choice = high if descriptor["largest_file_row_share"] > b_plan["protocol"]["metadata_baseline_max_file_share_threshold"] else low
        policies = {}
        for name, choice, paid in (("fixed_1gb", low, False), ("fixed_2gb", high, False),
                ("file_share_metadata", row_choice, False), ("dense_bytes_metadata", metadata_choice, False),
                ("always_one_probe_counterfactual", probe_choice, True),
                ("ambiguous_only_counterfactual", probe_choice if ambiguous else metadata_choice, ambiguous),
                ("guarded_default_admission_disabled", metadata_choice, False)):
            policies[name] = {"selected_config": choice, "historical_full": full[choice], "paid_one_probe": paid,
                "median_profile_wall_seconds": profile_wall if paid else 0.0,
                "median_profile_proxy_lower_bound": profile_score if paid else 0.0,
                "constructed_all_attempt_wall_seconds": full[choice]["median_all_attempt_wall_seconds"] + (profile_wall if paid else 0),
                "constructed_all_attempt_proxy_lower_bound": full[choice]["median_all_attempt_proxy_score"] + (profile_score if paid else 0)}
        base_score = full[metadata_choice]["median_all_attempt_proxy_score"]
        success_candidates = [r["median_all_attempt_proxy_score"] for r in full.values() if r["statuses"] == {"success": 3}]
        quiet_candidates = [r["median_all_attempt_proxy_score"] for r in full.values() if r["statuses"] == {"success": 3} and r["signals"] == {"quiet": 3}]
        saving = max(0, base_score - min(success_candidates))
        quiet_saving = max(0, base_score - min(quiet_candidates))
        details.append({"instance_id": instance, "dense_total_input_bytes": total_bytes,
            "dense_largest_fact_partition_bytes": largest_bytes, "metadata_scenario_bytes": estimates,
            "metadata_ambiguous_at_low_cap": ambiguous, "probe_decisions": probe_decisions, "policies": policies,
            "oracle_success_only_saving_upper_bound_proxy": saving,
            "oracle_quiet_only_saving_upper_bound_proxy": quiet_saving,
            "single_probe_minimum_observed_proxy_lower_bound": min(r["profile_proxy_score_lower_bound"] for r in probe_decisions),
            "even_cheapest_observed_probe_exceeds_success_oracle_saving": min(r["profile_proxy_score_lower_bound"] for r in probe_decisions) > saving})
    totals = {}
    for name in details[0]["policies"]:
        rows = [r["policies"][name] for r in details]
        totals[name] = {"selected_config_counts": dict(Counter(r["selected_config"] for r in rows)),
            "unique_selected_historical_full_statuses": dict(sum((Counter(r["historical_full"]["statuses"]) for r in rows), Counter())),
            "unique_selected_historical_full_signals": dict(sum((Counter(r["historical_full"]["signals"]) for r in rows), Counter())),
            "instances_paying_one_probe": sum(r["paid_one_probe"] for r in rows),
            "median_per_instance_profile_wall_seconds": median(r["median_profile_wall_seconds"] for r in rows),
            "median_per_instance_constructed_all_attempt_wall_seconds": median(r["constructed_all_attempt_wall_seconds"] for r in rows),
            "median_per_instance_constructed_proxy_lower_bound": median(r["constructed_all_attempt_proxy_lower_bound"] for r in rows)}
    assert len(details) == 8 and all(r["even_cheapest_observed_probe_exceeds_success_oracle_saving"] for r in details)
    assert totals["dense_bytes_metadata"]["unique_selected_historical_full_statuses"] == {"success": 24}
    result = {"scope": "Post-hoc same-table replay, not new policy executions or independent validation.",
        "input_sha256_lf_text": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in
            (spec_path, a_root / "measurements.csv", b_root / "measurements.csv", a_root / "plan.json", b_root / "plan.json", worker_path,
             worker_path.with_name("runs.json"), worker_path.with_name("verification.json"), b_root / "summary.json")},
        "policy_id": spec["policy_id"], "current_admission_enabled": spec["admission_enabled"],
        "objective": obj, "policies": totals, "instances": details,
        "gate": {"incremental_information_demonstrated": False, "single_request_economics_demonstrated": False,
                 "instances_where_even_cheapest_probe_exceeds_success_oracle_saving": 8,
                 "new_48_attempt_pilot_enabled": False},
        "limitations": ["Each decision sees one probe; three decisions share a sample. No independent repetitions of workload generation.",
            "All probe choices agree here, so each selected full reference is counted once in the 24-outcome summary.",
            "Wall/proxy medians include all attempted outcomes; failures are not ranked as successful cheap completions.",
            "Full references occurred in a different session; costs are constructed, not measured online end-to-end requests.",
            "Preparation is charged for every hypothetical one-shot request, not divided by three repeats. Controller/metadata cost is unmeasured.",
            "Preparation RAM/CPU resource exposure is unmeasured, so profiling proxy scores are lower-bound accounting, not total actual utilization.",
            "The oracle uses full outcomes only as an optimistic retrospective comparison, never as an input to the candidate decision.",
            "Metadata scenarios and the 0.55 probe threshold are development heuristics, not calibrated or validated safety bounds."]}
    Path(__file__).with_name("analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"policies": totals, "gate": result["gate"]}, indent=2))


if __name__ == "__main__":
    main()
