"""Audit completed Stage A against original local data and durable diagnostics."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path.cwd()))
from experiments.probe_pilot import load_plan, load_records, source_fingerprints, canonical_hash
from safe_pipe.research.probe_analysis import summarize
from safe_pipe.research.probe_runner import _environment
from safe_pipe.research.probe_workloads import load_manifest

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args(); root=args.run_dir.resolve()
    plan,fingerprint=load_plan(root/'plan.json')
    rows=load_records(root/'runs.jsonl',fingerprint)
    summary=summarize(plan,rows)
    assert len(rows)==48 and not summary['missing_cells']
    assert len(plan['datasets'])==8 and plan['methods']==['full'] and plan['repeats']==3
    assert plan['source_fingerprints']==source_fingerprints()
    assert plan['frozen_environment']==_environment()
    assert canonical_hash(plan['protocol'])==plan['protocol_sha256']
    assert plan['protocol']==json.loads(Path('configs/research_stage_a_v1.json').read_text())
    assert not (root/'.running.lock').exists() and not list((root/'attempts').glob('*.json'))
    assert not summary['mechanism']['inconsistent_successful_results']
    for instance,methods in plan['datasets'].items():
        for method,relative in methods.items():
            manifest=load_manifest(root/relative,verify=True)
            assert canonical_hash(manifest)==plan['dataset_fingerprints'][instance][method]
    planned={c['cell_id']:c for c in plan['cells']}; checked=0; nanny_messages=0
    power_samples=0; min_disk=None; min_ram=None
    for row in rows:
        assert row['run_config']==planned[row['cell_id']]['run_config']
        assert row['environment']==plan['frozen_environment']
        assert row['owned_descendants_alive_after_cleanup']==0 and not row['conditions']['flags']
        d=row['diagnostics']; folder=(root/d['directory']).resolve()
        assert folder.is_relative_to(root) and d['retained']
        assert not any(d.get(k) for k in ['summary_error','log_write_errors','log_truncated','malformed_log_lines'])
        assert row['telemetry']['samples_total']>0
        for file in d['files']:
            target=folder/file['file']; assert target.resolve().is_relative_to(folder)
            assert target.stat().st_size==file['bytes']
            assert hashlib.sha256(target.read_bytes()).hexdigest()==file['sha256']; checked+=1
        for event in d['nanny_memory_termination_events']:
            events=[json.loads(x) for x in (folder/event['source']).read_text(encoding='utf-8').splitlines()]
            assert any(e.get('message')==event['message'] and e.get('phase')==event['phase'] for e in events)
            nanny_messages+=1
        for line in (folder/'conditions.jsonl').read_text().splitlines():
            c=json.loads(line); assert not c['battery_present'] or c['power_plugged'] is True
            power_samples+=1; disk=min(c['free_disk_bytes'],c['temp_free_disk_bytes'])
            min_disk=disk if min_disk is None else min(min_disk,disk)
            min_ram=c['available_bytes'] if min_ram is None else min(min_ram,c['available_bytes'])
    result=dict(planned=48,recorded=48,statuses=summary['statuses'],missing=0,
        dataset_directories_verified=8,diagnostic_files_hash_verified=checked,
        raw_nanny_memory_messages_verified=nanny_messages,source_environment_protocol_match=True,
        cleanup_survivors=0,unresolved_attempt_markers=0,power_flagged=0,
        sampled_conditions_checked=power_samples,min_sampled_free_disk_bytes=min_disk,
        min_sampled_available_ram_bytes=min_ram,successful_scalar_inconsistencies=[],
        failure_categories=dict(Counter(r['diagnostics']['failure_category'] for r in rows)),
        nanny_memory_positive_attempts=sum(r['diagnostics']['nanny_memory_termination_count']>0 for r in rows),
        completed_utc=max(r['finished_utc'] for r in rows))
    (args.out_dir/'completion_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
