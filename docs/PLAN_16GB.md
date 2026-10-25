# Project-I execution plan (16 GB experiment PC)

**Frozen:** 2026-10-25  
**Hardware:** experiment PC **16 GB RAM** (OS still unrecorded); coding MacBook M3 **8 GB**.  
**Calendar:** six weeks from 2026-10-26 (Mon) through 2026-12-06. Adjust if the department deadline is earlier.  
**Rule:** 16 GB buys **3 repeats and CIs**, not more features (ADR-004).

## Experiment in one block

```
4 families × 8 configs × 3 repeats = 96 scored runs
+ 4 T0/pilot jobs
= 100 Dask jobs, one at a time, memory-capped workers
```

| Family | Stress | Target Parquet size |
| --- | --- | --- |
| scan_filter | I/O, partitions | ~200 MB |
| groupby | shuffle / reduction | ~200 MB |
| skewed_join | memory, stragglers | ~150–200 MB |
| sort_merge | spill | ~200–250 MB |

**Declared 8 configs** (all legal on 16 GB):

| id | workers | threads | memory_limit |
| --- | --- | --- | --- |
| w1_t1_1g | 1 | 1 | 1GB |
| w1_t2_1g | 1 | 2 | 1GB |
| w1_t1_2g | 1 | 1 | 2GB |
| w1_t2_2g | 1 | 2 | 2GB |
| w2_t1_1g | 2 | 1 | 1GB |
| w2_t2_1g | 2 | 2 | 1GB |
| w2_t1_2g | 2 | 1 | 2GB |
| w2_t2_2g | 2 | 2 | 2GB |

Host RAM is 16 GB; allocated worker RAM is at most 4 GB. That gap is intentional.

**SLA (for scoring, set after T0):** per family, `deadline = 1.5 × median(successful 2GB runs in pilot)` or a fixed cap from T0. Do not pick the SLA after seeing the optimizer’s score.

**Cost:** `allocated_vcpus * engine_s + allocated_gb * engine_s` (weights 1 and 1 unless we document otherwise).

**Held-out protocol:** train on three families, OOD-test the fourth; rotate (4 leave-one-family reports). Conformal calibration is a disjoint **repeat** slice, not the final test family.

## What runs where

| Machine | Does | Does not |
| --- | --- | --- |
| Mac M3 8 GB | git, tests, docs, LightGBM on CSV, SHAP, report | main Dask matrix |
| 16 GB PC | T0, data gen if disk is there, 96-run collector | model notebooks that pull TabPFN |
| Colab | optional TabPFN | Dask |

Copy the run JSONL back to the Mac after each night.

## Week plan

### Week 1 (26 Oct – 1 Nov) — make one job real

**Exit:** T0 log in `reports/t0.md`; generators produce four fingerprints; collector writes one JSONL row.

- **T0** on the 16 GB PC: `pip install -e ".[dev,dask]"`; `python experiments/t0_smoke.py`; record OS, CPU, RAM, Dask version.
- **T0b:** one 50 MB scan under `w1_t1_1g` and `w1_t1_2g`. If 1g does not spill or slow down vs 2g, **increase rows**, do not raise `memory_limit`.
- Generators + dataset manifest (`data/manifest.json`: bytes, row count, seed, sha256).
- Collector skeleton: start cluster, run workload, timeout, classify SUCCESS/TIMEOUT/OOM/ERROR, append JSONL.
- Submit B-lite synopsis.

**Pilot gate:** if 50 MB already takes > 8 minutes, freeze datasets at **~80 MB** and keep 3 repeats.

### Week 2 (2–8 Nov) — two families × full grid

**Exit:** 48 JSONL rows for `scan_filter` and `groupby` (8×3×2). Randomized order. No overlapping jobs.

- Nightly batches of ~16–24 jobs.
- After 16 jobs: sanity plot runtime vs config; kill the rest if the collector is mislabeling.

### Week 3 (9–15 Nov) — remaining families + freeze

**Exit:** 96-row curated table `data/curated/runs.parquet`; leakage audit; Option A **not** needed.

- `skewed_join` + `sort_merge` (48 runs).
- Label audit: timeouts are censored, not success.
- Freeze schema/version; no more generator tweaks without a new data version.

**Slip rule:** if < 64 rows by 15 Nov, drop to **2 repeats** (keep four families). If < 32 rows, Option A (two families). Never invent Glue.

### Week 4 (16–22 Nov) — models

**Exit:** LightGBM + median baseline + split conformal coverage table; OOD green/yellow/red rates per held-out family.

- Group splits by `family+config` so repeats do not leak across train/test.
- Calibration set = one repeat id, test = another, or leave-one-family as specified in DESIGN.
- Failure ML: count actionable positives. If < 30, **rules only** (valid outcome).

### Week 5 (23–29 Nov) — policy + demo

**Exit:** `safe-pipe recommend` uses fitted artifacts; demo script; vs default / conservative / random on the **same** table; SHAP screenshot notes.

- Wire estimates from the model, not `examples/estimates.json`.
- Conservative baseline = `w2_t2_2g`. Default baseline = `w1_t1_2g` (declare in the report).
- Unsafe-recommendation rate: recommended config actually missed SLA or failed.

### Week 6 (30 Nov – 6 Dec) — optional DL + report

**Exit:** report numbers match the parquet; demo rehearsal; TabPFN table **or** explicit “not run”.

- Colab TabPFN only if the CSV is < a few thousand rows (it will be).
- Limitations page: single PC, induced memory cap, 8 configs, no Glue.

## Critical path

```
T0 → generators → collector → 96 runs → freeze CSV → LightGBM/conformal/OOD → CLI demo → report
```

Parallel (not on the critical path): synopsis rewrite, unit tests on the Mac, SHAP notebook, TabPFN.

## Risks after 16 GB (still real)

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| PC sleeps / Windows updates | high | lost nights | disable sleep; log start/end; 2-repeat fallback |
| 1 GB cap does not fail | medium | weak failure chapter | grow sort/join until 1g fails or times out |
| 1 GB kills everything | medium | no runtime labels | keep 2g cells as the success population |
| Timing noise | high | wide intervals | 3 repeats; report coverage not a single MAE |
| Team edits generators mid-matrix | medium | invalid table | version + sha256; refuse mixed versions |

## Definition of a finished week-6 demo

1. Show workload spec + SLA.
2. Show eight candidates with predicted interval, cost, OOD colour.
3. Show recommend **or** abstain and the reason.
4. Run the chosen (or fallback) config on a **small** sample.
5. Show predicted vs actual from the frozen table, not from live luck.

## Immediate next step

T0 on the 16 GB PC. Until that log exists, do not start the 96-run loop.
