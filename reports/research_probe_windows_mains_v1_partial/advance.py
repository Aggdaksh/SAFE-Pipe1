"""Advance the frozen screen in bounded batches and record host conditions."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import psutil

RUN = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PLAN = RUN / 'plan.json'

def records():
    p = RUN / 'runs.jsonl'
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []

def condition():
    b = psutil.sensors_battery()
    return dict(utc=datetime.now(timezone.utc).isoformat(),
                plugged=b.power_plugged if b else None,
                battery_percent=b.percent if b else None,
                disk_free_bytes=psutil.disk_usage(str(RUN)).free,
                available_ram_bytes=psutil.virtual_memory().available)

def emit(value):
    print(json.dumps(value), flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--until', type=int, required=True)
    args = parser.parse_args()
    with (RUN / 'conditions.jsonl').open('a') as conditions:
        while len(records()) < args.until:
            if (RUN / 'pause.requested').exists():
                emit(dict(stopped='pause_requested_at_batch_boundary')); return
            before = records()
            c = condition()
            conditions.write(json.dumps(c) + '\n'); conditions.flush()
            if c['plugged'] is not True or c['disk_free_bytes'] < 15 * 2**30:
                emit(dict(stopped='power_or_disk_preflight', condition=c)); return
            count = min(4 if not before else 32, args.until-len(before))
            log_path = RUN / f'batch_{len(before):03d}.log'
            emit(dict(starting_batch=len(before), new_cells=count))
            violation = False
            with log_path.open('w', encoding='utf-8') as log:
                child = subprocess.Popen([sys.executable, '-m', 'experiments.probe_pilot', 'run',
                    '--plan', str(PLAN), '--max-runs', str(count)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                try:
                    while child.poll() is None:
                        c = condition()
                        conditions.write(json.dumps(c) + '\n'); conditions.flush()
                        violation |= c['plugged'] is not True or c['disk_free_bytes'] < 15 * 2**30
                        time.sleep(2)
                except KeyboardInterrupt:
                    # The child shares this console and receives the same interrupt.
                    child.wait(timeout=200)
                    emit(dict(stopped='operator_interrupt')); return
            result = subprocess.run([sys.executable, '-m', 'experiments.probe_pilot', 'analyze',
                '--plan', str(PLAN)], cwd=ROOT, capture_output=True, text=True)
            after = records()
            new = after[len(before):]
            bad = [r['cell_id'] for r in new if r['status'] != 'success' or r['owned_descendants_alive_after_cleanup']]
            emit(dict(completed=len(after), planned=768, new_statuses={s:sum(r['status']==s for r in new)
                for s in {r['status'] for r in new}}, power_or_disk_violation=violation,
                restarts=sum(r['telemetry'].get('observed_restarts_lower_bound',0) for r in new),
                spill_cells=sum((r['telemetry'].get('spilled_disk_peak_bytes_sum') or 0)>0 for r in new)))
            if child.returncode or result.returncode or bad or violation or len(after)==len(before):
                emit(dict(stopped='inspection_required', run_exit=child.returncode,
                          analyze_exit=result.returncode, bad_cells=bad, analyze_error=result.stderr[-1000:])); return
        emit(dict(reached=len(records())))

if __name__ == '__main__':
    import ctypes
    if not ctypes.windll.kernel32.SetThreadExecutionState(0x80000001):
        raise RuntimeError('Could not request system-awake state')
    try:
        main()
    finally:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
