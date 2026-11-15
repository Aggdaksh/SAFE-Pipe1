# Windows validation before Stage A preparation

Date: 2026-11-15. Research source revision: `73de101` (full revision saved separately).

`python -m pip check` returned exit code 0: `No broken requirements found.`

Executed using `.venv-research/Scripts/python.exe`:

```text
-m pytest tests/test_probe_workloads.py tests/test_probe_analysis.py tests/test_probe_runner.py tests/test_probe_pilot.py tests/test_probe_supervisor.py tests/test_probe_diagnostics.py tests/test_probe_export.py -o addopts='' -q
```

Result (captured console summary): **54 passed, 64 warnings in 16.41s**, exit code 0. Warnings concern Dask's deprecated pandas `reset_index(inplace=...)` call. No dependencies were changed. This is the targeted execution validation required by the new handoff, not a claim that every optional project test ran.
