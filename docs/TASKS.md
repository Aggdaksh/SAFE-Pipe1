# Task breakdown (dependency order)

Statuses: `NOT STARTED` | `IN PROGRESS` | `BLOCKED` | `IN REVIEW` | `DONE` | `DEFERRED`.  
`DONE` requires verification. Effort is a range in person-hours.

| ID | Purpose | Depends | Priority | Effort | Status | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| T-HW | Record 16 GB + OS | — | P0 | 0.2 | IN PROGRESS | RAM in PROGRESS.md; OS still missing |
| T0 | LocalCluster smoke | T-HW | P0 | 1–2 | NOT STARTED | `t0_smoke.py` prints ok; `reports/t0.md` has OS/CPU/Dask |
| T0b | 50 MB 1g vs 2g probe | T0 | P0 | 2–3 | NOT STARTED | one family, two configs; decide dataset scale |
| T-GEN | Four Parquet generators | T0b | P0 | 8–12 | NOT STARTED | manifest with seed, bytes, sha256; tests on tiny data |
| T-STORE | JSONL/Parquet run store | T-SCH | P0 | 3–5 | NOT STARTED | append-only; load back 1 fixture |
| T-COL | Collector + timeout/OOM | T-GEN, T-STORE, T0 | P0 | 8–12 | NOT STARTED | one job → one valid `RunResult` |
| T-MX1 | 48 runs scan+groupby | T-COL | P0 | 10–16 | NOT STARTED | 48 rows, randomized, one-at-a-time |
| T-MX2 | 48 runs join+sort | T-MX1 | P0 | 10–16 | NOT STARTED | 96 total; freeze `runs.parquet` |
| T-AUDIT | Label + leakage audit | T-MX2 | P0 | 3–4 | NOT STARTED | no post-run features; timeouts censored |
| T-ML | LightGBM + conformal | T-AUDIT | P0 | 8–12 | NOT STARTED | MdAPE + 90% coverage on grouped split |
| T-OOD | Leave-one-family gate | T-ML | P0 | 4–6 | NOT STARTED | green/yellow/red rates documented |
| T-POL | Wire optimizer to models | T-OOD | P0 | 4–6 | NOT STARTED | CLI recommend uses artifacts |
| T-BASE | Default/conservative/random | T-POL | P0 | 3–4 | NOT STARTED | same-table comparison |
| T-SHAP | Demo explanations | T-ML | P1 | 3–4 | NOT STARTED | one plot per viva |
| T-TAB | TabPFN Colab | T-AUDIT | P2 | 4–6 | NOT STARTED | table or “not run” |
| T-REP | Report + synopsis match | T-BASE | P0 | 12–16 | NOT STARTED | numbers = parquet |

Independent of the cluster: T-SCH, T-OPT (done), synopsis paste, extra unit tests.
