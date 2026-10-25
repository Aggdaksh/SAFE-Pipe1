# Technical investigations

Run these **before** locking generators at 200 MB or fitting models. Each row is a small experiment, not the 96-run matrix.

| ID | Question | Why it matters | Experiment | Evidence | Decision it informs | Fallback |
| --- | --- | --- | --- | --- | --- | --- |
| I-0 | Does Dask `LocalCluster` start on the 16 GB PC? | Nothing else runs if this fails | `python experiments/t0_smoke.py` | `reports/t0.md`: OS, RAM, Dask version, elapsed, `ok: true` | Proceed vs Option A on Mac tiny data | If fail: debug OS; do not invent results |
| I-1 | Does `memory_limit=1GB` behave differently from `2GB` on ~50 MB scan? | If not, the failure instrument is dead | T0b: same data, two configs | Runtime ratio, spill/logs | Grow rows until 1g is slower or fails; **never** raise worker cap | Switch family to sort_merge earlier |
| I-2 | How large can a job be and still finish in < 8 min on 2g? | Sets dataset size and night batch size | One scan + one sort at 80, 150, 250 MB | Median wall time | Freeze 80 vs 150–250 MB | Shrink; keep 3 repeats |
| I-3 | Can we classify OOM vs timeout vs Python error from Dask exceptions? | Labels for the run store | Force 1g + oversized sort | Exception type → `RunStatus` map in code | Collector taxonomy | Manual notes field + rules |
| I-4 | Does the PC stay awake for 16+ jobs? | Weeks 2–3 | Overnight 8-job subset | Start/end timestamps | 3 vs 2 repeats | 2-repeat slip rule |
| I-5 | Peak memory telemetry available without Prometheus? | Nice-to-have for rules | Read worker memory from `client.scheduler_info` / `get_worker_logs` | Field present or not | Store peak or skip | Rules from config only |
| I-6 | LightGBM vs median on a **toy** 64-row synthetic table | Pipeline, not accuracy claim | Unit/integration on fake CSV | Script runs, metrics finite | Train script shape | Median-only policy still valid |
| I-7 | TabPFN installs on Colab with our CSV width | Optional DL chapter | After freeze, one notebook cell | Completes or OOM | Run or write “not run” | Skip T-TAB |

**Rule:** I-0 and I-1 gate T-GEN scale. I-2 gates T-MX1. I-4 gates 3 vs 2 repeats. Do not start T-ML until T-AUDIT.
