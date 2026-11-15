"""Post-hoc, read-only analysis of the completed screen's compact export.

No Dask jobs, dataset generation or model training. Run from the repository root:
  python reports/research_screen_review_20261114/analyze.py
Outputs descriptive JSON/Markdown here; original measurements are never modified.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "reports/research_probe_windows_mains_v1_complete"
OUT = Path(__file__).resolve().parent
METHODS = ("uniform", "uniform_memory", "partition_tail")


def stats(values):
    return {"n": len(values), "median": median(values), "mean": mean(values),
            "min": min(values), "max": max(values)} if values else None


def main():
    plan = json.loads((SOURCE / "plan.json").read_text())
    published = json.loads((SOURCE / "summary.json").read_text())
    audit = json.loads((SOURCE / "completion_audit.json").read_text())
    with (SOURCE / "measurements.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = {c["cell_id"]: c for c in plan["cells"]}
    assert len(rows) == len(expected) == len({r["cell_id"] for r in rows})
    assert {r["cell_id"] for r in rows} == set(expected)
    for r in rows:
        c = expected[r["cell_id"]]
        assert all(str(r[k]) == str(c[k]) for k in
                   ("instance_id", "method", "target_config_id", "repeat_id"))
        assert int(r["owned_descendants_alive_after_cleanup"]) == 0
    assert dict(Counter(r["status"] for r in rows)) == published["statuses"] == audit["statuses"]
    configs = {c["config_id"]: c for c in plan["configs"]}
    instances = sorted(plan["datasets"])
    groups = defaultdict(list)
    for r in rows:
        groups[r["instance_id"], r["method"], r["target_config_id"]].append(r)
    assert all(len(rs) == plan["repeats"] == 2 for rs in groups.values())

    def times(i, method, c, field="execution_seconds"):
        rs = groups[i, method, c]
        assert all(r["status"] == "success" for r in rs)
        values = [float(r[field]) for r in rs]
        assert all(v > 0 for v in values)
        return values

    def med(i, method, c, field="execution_seconds"):
        return median(times(i, method, c, field))

    def factor(c):
        cfg = configs[c]
        threads = cfg["n_workers"] * cfg["threads_per_worker"]
        memory = cfg["n_workers"] * int(cfg["memory_limit"])
        # Existing balanced preference with 0.5 latency and 0.5 resource weight;
        # the common time reference cancels within an instance. Target caps apply.
        return .5 + .25 * threads / 4 + .25 * memory / 4_000_000_000

    valid = [i for i in instances if all(r["status"] == "success"
             for c in configs for r in groups[i, "full", c])]
    comparisons = {(c["instance_id"], c["method"]): c for c in published["comparisons"]}
    methods = {}
    cases = []
    for method in METHODS:
        regrets, balanced_regrets, outcomes, sweep_ratios = [], [], [], []
        proxy_repeat_disagreements = 0
        decisive_choices = 0
        for i in instances:
            selected = min(configs, key=lambda c: (med(i, method, c), c))
            balanced_selected = min(configs, key=lambda c: (med(i, method, c) * factor(c), c))
            selected_outcomes = [r["status"] for r in sorted(groups[i, "full", selected], key=lambda r:r["repeat_id"])]
            per_repeat = []
            for repeat in (1, 2):
                def one(c):
                    return next(float(r["execution_seconds"]) for r in groups[i, method, c]
                                if int(r["repeat_id"]) == repeat)
                per_repeat.append(min(configs, key=lambda c:(one(c), c)))
            proxy_repeat_disagreements += per_repeat[0] != per_repeat[1]
            outcome = {"instance": i, "selected_config": selected, "full_repeat_statuses": selected_outcomes,
                       "balanced_proxy_config": balanced_selected,
                       "balanced_full_statuses": [r["status"] for r in groups[i, "full", balanced_selected]],
                       "proxy_repeat_winners": per_repeat}
            outcomes.append(outcome)
            if i not in valid:
                continue
            best = min(configs, key=lambda c:(med(i, "full", c), c))
            best_balanced = min(configs, key=lambda c:(med(i, "full", c)*factor(c), c))
            regret = med(i, "full", selected) / med(i, "full", best) - 1
            assert abs(regret - comparisons[i, method]["selected_full_engine_regret"]) < 1e-12
            regrets.append(100*regret)
            balanced_regret = med(i,"full",balanced_selected)*factor(balanced_selected) / (med(i,"full",best_balanced)*factor(best_balanced)) - 1
            balanced_regrets.append(100*balanced_regret)
            decisive_choices += bool(comparisons[i, method]["selection_distinguishable_from_best"])
            prep_values = {float(r["preparation_seconds_shared_per_dataset"])
                           for c in configs for r in groups[i, method, c]}
            assert len(prep_values) == 1
            prep = prep_values.pop()
            sweep = sum(med(i, method, c, "total_seconds") for c in configs)
            fixed = med(i, "full", "w2_t2_2g", "total_seconds")
            sweep_ratios.append((prep + sweep) / fixed)
            cases.append({"instance": i, "method": method, "selected": selected, "hindsight_best": best,
                          "engine_regret_percent": 100*regret,
                          "choice_decisive_under_existing_screen": comparisons[i,method]["selection_distinguishable_from_best"],
                          "balanced_proxy_config": balanced_selected, "balanced_hindsight_config": best_balanced,
                          "balanced_score_regret_percent": 100*balanced_regret,
                          "one_probe_per_config_sweep_lifecycle_seconds": sweep,
                          "shared_sample_preparation_seconds": prep,
                          "fixed_w2_t2_2g_full_lifecycle_seconds": fixed,
                          "sweep_plus_preparation_to_fixed_full_ratio": (prep+sweep)/fixed})
        methods[method] = {"engine_regret_percent": stats(regrets),
                           "posthoc_balanced_score_regret_percent": stats(balanced_regrets),
                           "selected_vs_best_decisive_cases": decisive_choices,
                           "proxy_winner_changes_between_two_repeats_out_of_12": proxy_repeat_disagreements,
                           "selected_full_replay_failures_out_of_24": sum(s != "success" for o in outcomes for s in o["full_repeat_statuses"]),
                           "balanced_selected_full_replay_failures_out_of_24": sum(s != "success" for o in outcomes for s in o["balanced_full_statuses"]),
                           "estimated_sweep_plus_prep_to_fixed_full_ratio": stats(sweep_ratios),
                           "selected_outcomes": outcomes}

    fixed = {}
    for c in configs:
        rs = [r for i in instances for r in groups[i, "full", c]]
        runtime_regrets, balanced_regrets = [], []
        for i in valid:
            runtime_regrets.append(100*(med(i,"full",c)/min(med(i,"full",x) for x in configs)-1))
            balanced_regrets.append(100*(med(i,"full",c)*factor(c)/min(med(i,"full",x)*factor(x) for x in configs)-1))
        fixed[c] = {"full_statuses_out_of_24": dict(Counter(r["status"] for r in rs)),
                    "engine_regret_percent_on_10_complete_instances": stats(runtime_regrets),
                    "posthoc_balanced_score_regret_percent_on_10_complete_instances": stats(balanced_regrets)}

    failures = [{k:r[k] for k in ("cell_id","instance_id","target_config_id","repeat_id","status","error",
                                  "spilled_disk_peak_bytes_sum","observed_restarts_lower_bound")}
                for r in rows if r["status"] != "success"]
    for r in failures:
        r["power_flagged"] = r["cell_id"] in audit["power_flagged_cells"]
    diagnostic = []
    for i in instances:
        for c in configs:
            full = groups[i,"full",c]
            tail = groups[i,"partition_tail",c]
            diagnostic.append({"instance":i,"config":c,
                               "full_any_failure":any(r['status']!='success' for r in full),
                               "full_execution_error":any(r['status']=='execution_error' for r in full),
                               "full_power_flag":any(r['cell_id'] in audit['power_flagged_cells'] for r in full),
                               "tail_any_sampled_spill":any(float(r['spilled_disk_peak_bytes_sum'] or 0)>0 for r in tail),
                               "tail_spill_positive_repeats":sum(float(r['spilled_disk_peak_bytes_sum'] or 0)>0 for r in tail)})
    timing = {}
    for method in ("full",) + METHODS:
        rs = [r for r in rows if r["method"] == method and r["status"] == "success"]
        timing[method] = {field: stats([float(r[field]) for r in rs])
                          for field in ("setup_seconds","execution_seconds","total_seconds")}
    repeat_gaps = {method: stats([100*(max(times(i,method,c))/min(times(i,method,c))-1)
                   for i in instances for c in configs
                   if all(r["status"] == "success" for r in groups[i,method,c])]) for method in ("full",)+METHODS}
    full_winner_changes = 0
    for i in valid:
        winners = [min(configs,key=lambda c:(next(float(r['execution_seconds']) for r in groups[i,'full',c]
                    if int(r['repeat_id']) == repeat),c)) for repeat in (1,2)]
        full_winner_changes += winners[0] != winners[1]

    analysis = {"role":"posthoc_development_analysis_not_policy_validation", "source_commit":"6c08ec9",
                "input_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                 [SOURCE/name for name in ("measurements.csv","summary.json","plan.json","completion_audit.json")]},
                "recorded":len(rows), "statuses":dict(Counter(r['status'] for r in rows)),
                "independent_recipe_count":len(instances), "recipe_seeds":sorted({r['seed'] for r in plan['recipes']}),
                "complete_instances": valid, "full_winner_changes_between_repeats_out_of_10":full_winner_changes,
                "methods":methods,"fixed_configs":fixed,"successful_timings":timing,
                "within_cell_two_repeat_relative_gap_percent":repeat_gaps,"failures":failures,"cases":cases,
                "posthoc_tail_spill_warning_by_instance_config":diagnostic,
                "limits":["Twelve recipes, one generation seed, two runtime repeats; not 768 independent workloads.",
                          "The hindsight winner and repeat ranges are noisy; no significance claim.",
                          "Selection replay uses existing full outcomes, not newly executed policy requests.",
                          "Balanced retrospective replay multiplies proxy runtime by target-resource weight; no calibrated full-runtime or deadline claim.",
                          "Sweep overhead sums median recorded lifecycles for one probe per config and one shared preparation; no actual online sweep was executed.",
                          "Two-repeat selection is charged only one probe/config in the overhead illustration, intentionally optimistic.",
                          "Successful-only timing summaries do not describe failure latency; failure records are retained separately."]}
    (OUT/'analysis.json').write_text(json.dumps(analysis,indent=2,allow_nan=False)+'\n')
    lines=['# Recomputed descriptive results','',
           'Generated by `analyze.py` from the completed screen. Post-hoc development analysis; see `analysis.json` for exact hashes and all cases.','',
           '| Method | Median / mean / maximum engine regret | Decisive selected-vs-best cases / 10 | Selected full replay failures / 24 |',
           '| --- | --- | ---: | ---: |']
    for method,report in methods.items():
        v=report['engine_regret_percent']
        lines.append(f"| {method} | {v['median']:.2f}% / {v['mean']:.2f}% / {v['max']:.2f}% | {report['selected_vs_best_decisive_cases']} | {report['selected_full_replay_failures_out_of_24']} |")
    lines += ['', 'The regret columns cover ten complete instances. The replay-failure column uses the selected configurations across all twelve instances and their two recorded full repeats; it is not a future failure probability.', '',
              '| Instance | Method | Selected config | Engine regret | Sweep + preparation / fixed full lifecycle |',
              '| --- | --- | --- | ---: | ---: |']
    for c in cases:
        lines.append(f"| {c['instance']} | {c['method']} | {c['selected']} | {c['engine_regret_percent']:.2f}% | {c['sweep_plus_preparation_to_fixed_full_ratio']:.2f}x |")
    lines += ['', 'Sweep ratios exclude the final selected job and controller time. They are estimates from recorded medians, not measured online requests. Fixed reference is `w2_t2_2g`.', '']
    (OUT/'RESULTS.md').write_text('\n'.join(lines))
    print(json.dumps({'recorded':len(rows),'complete_instances':len(valid),'full_winner_changes':full_winner_changes,
                      'method_summary':{m:{k:v for k,v in r.items() if k!='selected_outcomes'} for m,r in methods.items()},
                      'fixed_configs':fixed,'timings_median':{m:{k:v['median'] for k,v in r.items()} for m,r in timing.items()}},indent=2))


if __name__ == '__main__':
    main()
