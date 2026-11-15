"""Run one bounded Stage A batch with a temporary Windows awake request."""
import ctypes
from pathlib import Path
import runpy
import sys

if __name__ == '__main__':
    count = int(sys.argv[1])
    if not 1 <= count <= 8:
        raise ValueError('Stage A batches must have 1-8 new attempts')
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    if not ctypes.windll.kernel32.SetThreadExecutionState(0x80000001):
        raise RuntimeError('Could not request awake state')
    try:
        sys.argv = ['experiments.probe_pilot','run','--plan',
                    str(Path(__file__).resolve().parent/'plan.json'),'--max-runs',str(count)]
        runpy.run_module('experiments.probe_pilot',run_name='__main__')
    finally:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
