# Task index

Full cards: [`MICROPLAN.md`](MICROPLAN.md). Status must match [`../PROGRESS.md`](../PROGRESS.md) and [`../context.md`](../context.md).

Statuses: `NOT STARTED` | `IN PROGRESS` | `BLOCKED` | `IN REVIEW` | `DONE` | `DEFERRED`.

| ID | Purpose | Depends | Priority | Effort | Status |
| --- | --- | --- | --- | --- | --- |
| T-CTX | Living `context.md` | — | P0 | 1 | IN REVIEW |
| T-ARCH | Requirements + architecture + microplan | — | P0 | 3–5 | IN REVIEW |
| T-HW | Record 16 GB + OS | — | P0 | 0.2 | IN PROGRESS |
| T0 | LocalCluster smoke | T-HW | P0 | 1–2 | NOT STARTED |
| T0b | 50 MB 1g vs 2g probe | T0 | P0 | 2–3 | NOT STARTED |
| T-GRID | Freeze 8 configs JSON | — | P0 | 1–2 | NOT STARTED |
| T-STORE | JSONL run store | T-SCH | P0 | 3–5 | NOT STARTED |
| T-GEN | Four Parquet generators | T0b | P0 | 8–12 | NOT STARTED |
| T-COL | Collector + timeout/OOM | T-GEN, T-STORE, T0, T-GRID | P0 | 8–12 | NOT STARTED |
| T-MX1 | 48 runs scan+groupby | T-COL | P0 | 10–16 | NOT STARTED |
| T-MX2 | 48 runs join+sort | T-MX1 | P0 | 10–16 | NOT STARTED |
| T-AUDIT | Label + leakage audit | T-MX2 | P0 | 3–4 | NOT STARTED |
| T-ML | LightGBM + conformal | T-AUDIT | P0 | 8–12 | NOT STARTED |
| T-OOD | Leave-one-family gate | T-ML | P0 | 4–6 | NOT STARTED |
| T-POL | Wire optimizer to models | T-OOD | P0 | 4–6 | NOT STARTED |
| T-BASE | Default/conservative/random | T-POL | P0 | 3–4 | NOT STARTED |
| T-SHAP | Demo explanations | T-ML | P1 | 3–4 | NOT STARTED |
| T-TAB | TabPFN Colab | T-AUDIT | P2 | 4–6 | NOT STARTED |
| T-REP | Report + synopsis match | T-BASE | P0 | 12–16 | NOT STARTED |
| T-SCH | Pydantic schemas v0 | — | P0 | — | DONE |
| T-OPT | Bounded optimizer v0 | T-SCH | P0 | — | DONE |

Mac-parallel now (no 16 GB PC): T-GRID, T-STORE, extra tests, synopsis paste.
