"""Reproduce the completion/condition audit from local raw records; run at repo root."""
import argparse
from bisect import bisect_right
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path.cwd()))
from experiments.probe_pilot import load_plan, load_records, source_fingerprints, canonical_hash
from safe_pipe.research.probe_analysis import summarize
from safe_pipe.research.probe_workloads import load_manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    plan, fingerprint = load_plan(args.run_dir/'plan.json')
    rows = load_records(args.run_dir/'runs.jsonl', fingerprint)
    summary = summarize(plan, rows)
    assert not summary['missing_cells'] and len(rows) == len(plan['cells']) == 768
    assert plan['source_fingerprints'] == source_fingerprints()
    assert all(r['owned_descendants_alive_after_cleanup'] == 0 for r in rows)
    assert not (args.run_dir/'.running.lock').exists()
    datasets = {args.run_dir/p for methods in plan['datasets'].values() for p in methods.values()}
    for dataset in datasets:
        load_manifest(dataset, verify=True)
    for instance, methods in plan['datasets'].items():
        for method, relative in methods.items():
            assert canonical_hash(load_manifest(args.run_dir/relative)) == plan['dataset_fingerprints'][instance][method]
    planned = {c['cell_id']:c for c in plan['cells']}
    assert all(r['run_config'] == planned[r['cell_id']]['run_config'] for r in rows)
    conditions = [json.loads(x) for x in (args.run_dir/'conditions.jsonl').read_text().splitlines() if x.strip()]
    conditions.sort(key=lambda c: c['utc'])
    times = [datetime.fromisoformat(c['utc']) for c in conditions]
    flags = []
    for r in rows:
        start, end = [datetime.fromisoformat(r[k]) for k in ('started_utc','finished_utc')]
        lo = max(0, bisect_right(times,start)-1)
        hi = min(len(times), bisect_right(times,end)+1)
        window = conditions[lo:hi]
        # Conservative: include adjacent samples within five seconds of execution.
        selected = [c for c in window if start-timedelta(seconds=5) <= datetime.fromisoformat(c['utc']) <= end+timedelta(seconds=5)]
        observed_unplugged = any(c['plugged'] is False for c in selected)
        in_run = [t for t in times[lo:hi] if start<=t<=end]
        gaps = [b-a for a,b in zip([start]+in_run,in_run+[end])]
        covered = bool(selected) and max(gaps,default=timedelta.max).total_seconds() <= 10
        flags.append(dict(cell_id=r['cell_id'],instance_id=r['instance_id'],method=r['method'],
            target_config_id=r['target_config_id'],repeat_id=r['repeat_id'],status=r['status'],
            observed_unplugged=observed_unplugged,condition_sampling_covered=covered))
    with (args.out_dir/'condition_audit.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(flags[0])); w.writeheader(); w.writerows(flags)
    method_stats={}
    for method in plan['methods'][1:]:
        comparisons=[c for c in summary['comparisons'] if c['method']==method and c['evaluable']]
        method_stats[method]=dict(evaluable_instances=len(comparisons),
            median_selected_full_engine_regret=statistics.median(c['selected_full_engine_regret'] for c in comparisons),
            pair_counts=dict(sum((Counter(c['pair_counts']) for c in comparisons),Counter())))
    result=dict(planned=768,recorded=len(rows),statuses=summary['statuses'],missing_cells=0,
        source_fingerprints_match=True,dataset_directories_verified=len(datasets),
        cleanup_survivors=0,run_lock_absent=True,
        first_started_utc=min(r['started_utc'] for r in rows),last_finished_utc=max(r['finished_utc'] for r in rows),
        last_finished_ist=datetime.fromisoformat(max(r['finished_utc'] for r in rows)).astimezone(timezone(timedelta(hours=5,minutes=30))).isoformat(),
        power_flagged_cells=[f['cell_id'] for f in flags if f['observed_unplugged']],
        condition_sampling_uncovered_cells=[f['cell_id'] for f in flags if not f['condition_sampling_covered']],
        spill_positive_cells=sum((r['telemetry'].get('spilled_disk_peak_bytes_sum') or 0)>0 for r in rows),
        restart_positive_cells=sum((r['telemetry'].get('observed_restarts_lower_bound') or 0)>0 for r in rows),
        method_summary=method_stats,
        notes=['Descriptive engine-runtime rankings; not total request savings.',
               'Pair counts share instances; they are not independent statistical samples.',
               'Power flags conservatively include samples within five seconds of run boundaries.',
               'Lifetime peak sums are not concurrent cluster peaks.'])
    (args.out_dir/'completion_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
