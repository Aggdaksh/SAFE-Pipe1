# ROADMAP.md

**Horizon:** six weeks to Project-I final (system + tables + report + demo).  
**Hardware:** experiment PC **16 GB**; coding Mac **8 GB**.  
**Detailed week plan:** [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md). Task cards: [`docs/MICROPLAN.md`](docs/MICROPLAN.md). Index: [`docs/TASKS.md`](docs/TASKS.md). Living memory: [`context.md`](context.md).  
**Estimates are estimates.** Critical path: T0 → generators → 96-run matrix → models → CLI demo → report.

## Milestones

| ID | Milestone | Exit criteria | Calendar | Depends |
| --- | --- | --- | --- | --- |
| M0 | Docs + contracts | Optimizer unit tests pass | done 2026-10-25; Mac pandas slice 2026-10-26 (**20 tests**) | — |
| M1 | T0 Dask smoke | Tiny job + 50 MB 1g vs 2g; OS recorded | **not started** (needs 16 GB PC) | 16 GB PC |
| M2 | Workload generators | Four families ~150–250 MB, fingerprints | Tiny **done** on Mac; full scale waits M1/T0b | M1 |
| M3 | Collector | JSONL + timeout/OOM labels | Pandas **done**; Dask collector waits M1 | M2 |
| M4 | Matrix | **4×8×3 = 96** runs frozen | Weeks 2–3 | M3, overnight PC |
| M5 | Models | LightGBM + conformal + OOD | Week 4 | M4 |
| M6 | Policy + demo | CLI + SHAP + same-table baselines | Week 5 | M5 |
| M7 | TabPFN (optional) | Colab table vs LightGBM | Week 6 | M5 |
| M8 | Report | Synopsis B-lite; numbers = parquet | Week 6 | M6 |

If M1 fails, Option A or stop. Do not invent Glue results.

## Candidate grid (declared, 8 configs)

Workers `{1, 2}` × threads `{1, 2}` × `memory_limit` `{1GB, 2GB}`. All eight fit on 16 GB. Worker caps stay **1–2 GB** so spill still exists (ADR-004).

## Slip rules

- By 15 Nov, < 64 rows → **2 repeats** (keep four families).
- < 32 rows → Option A (two families, 4 configs, rules-only, no TabPFN).
- Overnight impossible → 2 repeats before dropping a family.
