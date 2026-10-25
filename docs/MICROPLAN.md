# Micro-plan

**Updated:** 2026-10-25  
**Calendar:** [`PLAN_16GB.md`](PLAN_16GB.md)  
**Requirements:** [`REQUIREMENTS.md`](REQUIREMENTS.md)  
**Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md)

Do not start a task whose dependencies are not `DONE`.  
Do not mark `DONE` without the acceptance check.

## Implementation strategy (vertical slices)

| Slice | What “done” looks like | Risk it kills |
| --- | --- | --- |
| 0 | CLI recommend from JSON estimates + unit tests | Wrong SLA logic | **DONE** 2026-10-25 |
| 1 | T0 LocalCluster on 16 GB PC | Dask/OS | **next** |
| 2 | T0b 50 MB 1g vs 2g | Dead failure instrument |
| 3 | One family generator + one collector row | Data/exec path |
| 4 | 48-run half matrix | Collector at night |
| 5 | 96 freeze + leakage audit | Bad labels |
| 6 | LightGBM + conformal on frozen table | Model/split bugs |
| 7 | CLI recommend from artifacts + baselines + SHAP | Demo |
| 8 | Report numbers = parquet | Academic honesty |

First technically risky component: **I-0 / T0**.  
First useful demonstration: **T0b timing table** (even without ML).  
Hardening: T-AUDIT + tests.  
Evaluation/presentation: T-BASE, T-REP, T-SHAP.

## Critical path

```
T0 → T0b → T-GEN → T-COL → T-MX1 → T-MX2 → T-AUDIT → T-ML → T-OOD → T-POL → T-BASE → T-REP
```

Can proceed in parallel on the Mac: extra unit tests, synopsis paste, SHAP notebook scaffolding, `T-STORE` (no Dask), `configs/dask_grid.json`.

## Task cards

### T-CTX — Living context.md

- **Purpose:** Portable memory across chats.
- **Files:** `context.md` (this process).
- **Acceptance:** File exists; `PROJECT_CONTEXT.md` points to it; README lists it first.
- **Status:** `IN REVIEW` (written this session).
- **Effort:** 1 h.

### T-ARCH — Architecture + requirements + microplan

- **Purpose:** Phase 2 design before more code.
- **Files:** `docs/REQUIREMENTS.md`, `docs/ARCHITECTURE.md`, `docs/INVESTIGATIONS.md`, `docs/MICROPLAN.md`, `DESIGN.md`.
- **Acceptance:** Components, contracts, investigations, and task cards exist; optimizer already matches FR-05 tests.
- **Status:** `IN REVIEW`.
- **Effort:** 3–5 h.

### T-HW — Hardware card

- **Purpose:** Stop planning against unknown RAM.
- **Depends:** —
- **Acceptance:** RAM and OS in `context.md`.
- **Status:** `IN PROGRESS` (RAM=16 GB; OS missing).
- **Effort:** 0.2 h.

### T0 — Dask smoke

- **Purpose:** Prove LocalCluster on the experiment PC.
- **Depends:** T-HW (RAM known).
- **Files:** `experiments/t0_smoke.py`, `reports/t0.md` (create).
- **Approach:** `pip install -e ".[dev,dask]"`; run script; paste output into `reports/t0.md` and `context.md`.
- **Tests:** script prints `ok: True`; sum of 0..9999 = 49995000.
- **Risks:** Windows Python, firewall on dashboard (dashboard is disabled).
- **Status:** `NOT STARTED`.
- **Effort:** 1–2 h.

### T0b — 50 MB probe (I-1, I-2 start)

- **Purpose:** See whether 1 GB vs 2 GB matters; pick dataset scale.
- **Depends:** T0.
- **Files:** `experiments/t0b_probe.py` (to add), `reports/t0b.md`.
- **Approach:** Generate ~50 MB parquet; run `w1_t1_1g` and `w1_t1_2g`; record wall time.
- **Acceptance:** Written decision: freeze ~80 MB or ~200 MB; **do not** raise memory_limit.
- **Status:** `NOT STARTED`.
- **Effort:** 2–3 h.

### T-GRID — Freeze eight configs on disk

- **Purpose:** Single source for config ids.
- **Depends:** —.
- **Files:** `configs/dask_grid.json`, tests for 8 ids.
- **Acceptance:** Matches ADR-004 table; parser fills `allocated_*`.
- **Status:** `NOT STARTED`.
- **Effort:** 1–2 h.
- **Can run on Mac now.**

### T-STORE — Run store

- **Purpose:** Append-only records.
- **Depends:** T-SCH (done).
- **Files:** `safe_pipe/store/jsonl.py`, `tests/test_store.py`.
- **Approach:** Write `RunResult.model_dump()` lines; read back.
- **Acceptance:** Fixture round-trip; concurrent write not required (one job at a time).
- **Status:** `NOT STARTED`.
- **Effort:** 3–5 h.
- **Can run on Mac now.**

### T-GEN — Four workload generators

- **Purpose:** Versioned Parquet + DAGs.
- **Depends:** T0b (scale freeze).
- **Files:** `safe_pipe/workloads/*.py`, `data/manifest.json` (generated, gitkeep only in git).
- **Approach:** pandas/pyarrow write; Dask read in execute path; fixed seeds.
- **Acceptance:** Tiny-data unit tests (MBs not 200 MB in CI); manifest schema documented.
- **Risks:** Mac 8 GB swapping if someone generates 250 MB locally — use `--tiny` in CI.
- **Status:** `NOT STARTED`.
- **Effort:** 8–12 h.

### T-COL — Collector

- **Purpose:** One matrix cell → one `RunResult`.
- **Depends:** T0, T-GEN, T-STORE, T-GRID.
- **Files:** `experiments/collect.py`, classification helper.
- **Approach:** subprocess or client-side timeout; always `cluster.close()`.
- **Acceptance:** One successful row and one timeout row in tests (timeout can be fake clock / tiny timeout).
- **Status:** `NOT STARTED`.
- **Effort:** 8–12 h.

### T-MX1 / T-MX2 — Matrix

- **Depends:** T-COL, I-4 preferably.
- **Files:** `experiments/matrix.json`, JSONL on the PC, copy to Mac.
- **Acceptance:** 48 then 96 rows; shuffled order logged.
- **Status:** `NOT STARTED`.
- **Effort:** 10–16 h each (mostly wait time).

### T-AUDIT — Labels and leakage

- **Depends:** T-MX2.
- **Acceptance:** Checklist in `reports/audit.md`; timeouts not in success training set.
- **Status:** `NOT STARTED`.

### T-ML / T-OOD / T-POL / T-BASE / T-SHAP / T-TAB / T-REP

See [`TASKS.md`](TASKS.md) for effort and acceptance. Do not flesh file lists until T-AUDIT is in progress — the CSV columns must exist first.

## What not to do this week

- Glue stubs that look like measured results.
- LightGBM on dummy data presented as Project-I accuracy.
- Raising `memory_limit` to “use the 16 GB”.
- Streamlit.
- Expanding to 16 configs.
