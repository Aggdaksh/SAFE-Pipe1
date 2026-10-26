# Task index

Full cards: [`MICROPLAN.md`](MICROPLAN.md). Must match [`../PROGRESS.md`](../PROGRESS.md) and [`../context.md`](../context.md).

Updated: 2026-10-26.

| ID | Purpose | Depends | Priority | Effort | Status |
| --- | --- | --- | --- | --- | --- |
| T-CTX | Living `context.md` | — | P0 | 1 | DONE |
| T-ARCH | Requirements + architecture + microplan | — | P0 | 3–5 | DONE |
| T-HW | Record 16 GB + OS | — | P0 | 0.2 | IN PROGRESS |
| T0 | LocalCluster smoke on **16 GB PC** | T-HW | P0 | 1–2 | NOT STARTED |
| T0b | 50 MB 1g vs 2g Dask probe | T0 | P0 | 2–3 | NOT STARTED |
| T-GRID | Freeze 8 configs JSON | — | P0 | 1–2 | DONE |
| T-STORE | JSONL run store | T-SCH | P0 | 3–5 | DONE |
| T-GEN | Four Parquet generators | T0b for **scale** | P0 | 8–12 | DONE (tiny); scale blocked on T0b |
| T-COL | Collector | T-GEN, T-STORE, T-GRID | P0 | 8–12 | DONE (pandas); Dask blocked on T0 |
| T-MX1 | 48 runs scan+groupby | T-COL Dask | P0 | 10–16 | NOT STARTED |
| T-MX2 | 48 runs join+sort | T-MX1 | P0 | 10–16 | NOT STARTED |
| T-AUDIT | Label + leakage audit | T-MX2 | P0 | 3–4 | NOT STARTED |
| T-ML | LightGBM + conformal | T-AUDIT | P0 | 8–12 | NOT STARTED |
| T-OOD | Leave-one-family gate | T-ML | P0 | 4–6 | NOT STARTED |
| T-POL | Wire optimizer to models | T-OOD | P0 | 4–6 | NOT STARTED |
| T-BASE | Default/conservative/random | T-POL | P0 | 3–4 | NOT STARTED |
| T-SHAP | Demo explanations | T-ML | P1 | 3–4 | NOT STARTED |
| T-TAB | TabPFN Colab | T-AUDIT | P2 | 4–6 | NOT STARTED |
| T-REP | Report + synopsis match | T-BASE | P0 | 12–16 | NOT STARTED |
| T-SCH | Pydantic schemas | — | P0 | — | DONE |
| T-OPT | Bounded optimizer | T-SCH | P0 | — | DONE |

Next: T0 on the 16 GB PC (`reports/HANDOFF_16GB.md`).
