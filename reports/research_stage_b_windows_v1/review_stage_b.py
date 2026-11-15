"""Recompute descriptive findings from the compact completed Stage B summary."""
import json
from collections import Counter
from pathlib import Path
from statistics import median

def main():
    root=Path(__file__).resolve().parent
    s=json.loads((root/'summary.json').read_text(encoding='utf-8'))
    assert s['recorded_cells']==s['planned_cells']==96 and not s['missing_cells']
    policies={}
    for policy in sorted({r['policy'] for r in s['baseline_replays']}):
        rows=[r for r in s['baseline_replays'] if r['policy']==policy]
        assert len(rows)==8 and all(r['evaluable'] for r in rows)
        profiles=[r['profiling_seconds'] for r in rows if r['profiling_seconds'] is not None]
        full_times=[r['median_successful_full_end_to_end_seconds'] for r in rows
                    if r['median_successful_full_end_to_end_seconds'] is not None]
        policies[policy]=dict(instances=8,
            selected_config_counts=dict(Counter(r['selected_config'] for r in rows)),
            historical_full_statuses=dict(sum((Counter(r['selected_full_outcomes']['statuses']) for r in rows),Counter())),
            historical_full_signals=dict(sum((Counter(r['selected_full_outcomes']['signals']) for r in rows),Counter())),
            median_six_probe_and_preparation_seconds=median(profiles) if profiles else None,
            median_per_instance_successful_historical_full_seconds=median(full_times),
            instances_with_no_successful_historical_full_time=8-len(full_times),
            fallback_instances=sum(r['fallback_used'] is True for r in rows))
    result=dict(attempts=96,statuses=s['statuses'],
        probe_signals=dict(Counter(r['signal'] for r in s['probe_outcomes'])),
        comparisons=s['comparison_counts'],policies=policies,
        limitations=['Eight instances, one non-nested sample per fraction, three runtime repeats.',
            'Historical full outcomes were not rerun; discrepancy groups are not classifier error rates.',
            'Six paid probes plus sample preparation are a diagnostic-replay cost, not an executed online controller.',
            'Conditional successful full-time medians exclude failed outcomes from timing only; all statuses remain shown.',
            'Metadata threshold is development-derived; no independent reliability or savings claim.'])
    (root/'findings.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
