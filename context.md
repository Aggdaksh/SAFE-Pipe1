# SAFE-Pipe project context

**Updated:** 2026-10-28. Read this file first when working from another PC.

## Purpose and scope

SAFE-Pipe recommends a configuration from eight declared local Dask configurations under an engine deadline, or abstains. The preferred `advise` command balances predicted speed and configured resource-time. Project-I measured four synthetic workload profiles on one Windows PC with worker memory caps of 1 GB and 2 GB: four families × eight configs × three repeats = 96 runs. LightGBM, upper estimates, support checks, baselines, and reports use that frozen run table. No general safety guarantee or multi-node result is established.

## Machines and Git branches

| Machine | Role |
| --- | --- |
| MacBook M3, 8 GB | Earlier coding, tiny pandas jobs, docs, unit tests |
| Windows 11 PC, 31.4 GiB physical RAM | User-selected physical Dask experiment host (ADR-005) |

The original 16 GB plan is a conservative sizing reference. The actual host has 32 GB marketed RAM; **worker caps and the eight-config grid stay unchanged**. The earlier Mac, Windows and advisor work is now included in `main` after a 2026-10-28 fast-forward merge. Their original branches remain as checkpoints. Pull `main` before editing on another PC. Generated Parquet, JSONL runs, and `.venv` are gitignored.

## Verified implementation

- Schemas, optimizer, eight-config grid, JSONL store, tiny four-family Parquet generators, pandas collector, and 96-cell planner came from the Mac branch.
- Windows `.venv` has `.[dev,dask,ml]` installed under Python 3.14.6. The merged `main` suite has **79 passing tests** on this PC, including tiny Dask executions, advisor regressions and the model-loading compatibility checks.
- T0 passed on the selected Windows PC: one 512 MB Dask worker returned the expected sum. See [`reports/t0.md`](reports/t0.md).
- T0b pilot compared 1 GB and 2 GB workers on two scan sizes and one sort size. The 136 MB sort took 10.58 s at 1 GB versus 4.53 s at 2 GB; both succeeded. See [`reports/t0b.md`](reports/t0b.md). No spill or OOM has been confirmed.
- Dask execution and one-cell collection are implemented; the scored matrix is complete (96 jobs below).
- Four `main-v1` datasets (175–198 MB) are generated, fingerprinted, and ignored by Git. The committed index is `configs/datasets_main_v1.json`.
- Twelve 2 GB SLA pilot runs succeeded. Deadlines and the randomized 96-cell order were frozen in `configs/` before scored collection. See `reports/matrix_preparation.md`.
- All 96 Dask cells were measured and audited: 96 successes, zero SLA misses. The curated CSV is committed at `data/curated/runs.csv`; raw JSONL and Parquet remain local.
- Grouped LightGBM plus conformal, a conservative rule-based OOD gate, fitted CLI recommendation, descriptive same-table baselines, and a feature-contribution figure are implemented. See `reports/runtime_model.md`, `reports/policy.md`, and `reports/shap.md`.
- New `advise` policy defaults to balanced speed/resources, with hard upper-runtime deadlines, optional budgets, exact frozen descriptors, bound grid/artifact checks and per-candidate comparisons. It reuses the model without training. See `docs/CONFIG_SELECTION.md` and `reports/advisor_v1/`.

## Current task

The balanced selection implementation and the original Windows study are now merged into `main` and published. The technical results draft and separate tiny live Dask demo are complete. Remaining experimental work is prospective evaluation on the original Windows host; broader profiles need new data and a revised model/support policy. See `docs/INDEPENDENT_VALIDATION.md`. Formal submission remains pending. Optional TabPFN remains unrun; no failure classifier is supported because all 96 measured jobs succeeded.

## Design rules

- Use pre-run features only for inference. A job's actual runtime, memory, status, and spill cannot enter its prediction vector.
- Optimize the declared balanced dimensionless score using point runtime; test deadlines against the frozen upper estimate. Use explicit hard checks and abstain when none pass. Preserve historical cost/model features for old report reproduction.
- Keep memory caps at 1 GB and 2 GB despite the larger host. State that results come from a single Windows PC with induced worker caps.
- Failure handling stays deterministic until enough correctly labeled independent failure data supports training and held-out evaluation. A fixed number of positives alone does not establish classifier quality.
- Every reported number must come from the frozen Dask run table. No Glue, 176-run, or unmeasured improvement claims.

## Documents

[`PROGRESS.md`](PROGRESS.md) is the status ledger; [`docs/MICROPLAN.md`](docs/MICROPLAN.md) has task cards; [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines component contracts; [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) lists acceptance criteria; [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md) is the conservative six-week schedule. ADR-005 records the actual host change.
