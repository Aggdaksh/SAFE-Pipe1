# Examiner demo on the Windows experiment PC

This demo keeps the **frozen main-v1 prediction/table** separate from a **tiny live Dask sample**. Run from the repository root with `.[dev,dask,ml]` installed in `.venv`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m safe_pipe.cli profile --family sort_merge
.\.venv\Scripts\python.exe -m safe_pipe.cli recommend-model --family sort_merge --sla 13.1
```

The main-v1 sort profile has 178,382,606 Parquet bytes. The fitted policy recommends `w1_t2_1g` for its 13.1 s frozen SLA. Its **point prediction is 3.30 s** and its **upper bound is 5.57 s**. The frozen physical table reports three actual engine times of **5.083, 5.566, and 5.342 s** (median **5.342 s**) for that family/configuration. These rows are in [`data/curated/runs.csv`](../data/curated/runs.csv); the interval calibration used some cells from the same table, so this is an illustration, not an independent test.

For a live execution, use a separate tiny dataset and demo log:

```powershell
.\.venv\Scripts\python.exe -m safe_pipe.cli generate --dest data/demo --family sort_merge
.\.venv\Scripts\python.exe -m safe_pipe.cli execute --family sort_merge --config-id w1_t2_1g --data-dir data/demo --store data/runs/demo.jsonl --timeout 60
```

The verified demo run on 2026-10-26 succeeded in **2.300 s** with one 1 GB worker and two threads. Its input was only **30,783 bytes** of Parquet, so compare it with the frozen main-v1 prediction only as a workflow demonstration, not as a runtime accuracy check. `data/demo/` and `data/runs/demo.jsonl` are ignored by Git and excluded from the 96 scored jobs. If the demo dataset already exists, skip the generate command; the generator can overwrite it.

To demonstrate abstention, pass a `WorkloadSpec` JSON for `sort_merge` with input bytes over twice the measured main-v1 size using `recommend-model --workload-json <path> --sla 13.1`. The conservative OOD gate returns red for that size shift. The full gate behavior is also covered by `tests/test_fitted_cli.py`.
