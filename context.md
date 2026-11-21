# SAFE-Pipe project context

**Updated:** 2026-11-21. Read this file first when working from another PC.

## Active work: original-advisor completion

The user authorized implementing the completion plan on **one separate branch**, with merging deferred. This worktree uses **`codex/main-advisor-completion`**, based on `main` at `504f005`. Keep the research branch `codex/partition-probe-research` separate. The full release sequence and acceptance criteria are in [`docs/MAIN_COMPLETION_PLAN.md`](docs/MAIN_COMPLETION_PLAN.md).

Current deliverable implemented: a frozen prospective-study package, append-only attempt recording, fresh-results evaluator and Windows verification handoff. Static review and syntax/compile checks passed; **no new Windows test pass or fresh physical run is claimed**. The original 96-run table/model/grid remain unchanged. Next external step is software verification on the original Windows environment, then preparation and fresh collection using [`docs/WINDOWS_MAIN_VALIDATION.md`](docs/WINDOWS_MAIN_VALIDATION.md). No model training is needed.

**Execution constraint:** all project tests, Dask jobs, dataset generation and training belong on Windows. This Mac is for code/docs/review and static syntax checks only. Historical Mac-test descriptions below are not current authorization to run tests here.

After evidence review: bind saved advice to exact dataset execution, implement the small local interface and finish delivery. Broader profile support requires a separate versioned model/data design. Research-paper novelty remains a separate objective; none is established by this validation infrastructure.

## Purpose and scope

SAFE-Pipe recommends a configuration from eight declared local Dask configurations under an engine deadline, or abstains. The preferred `advise` command balances predicted speed and configured resource-time. Project-I measured four synthetic workload profiles on one Windows PC with worker memory caps of 1 GB and 2 GB: four families × eight configs × three repeats = 96 runs. LightGBM, upper estimates, support checks, baselines, and reports use that frozen run table. No general safety guarantee or multi-node result is established.

## Machines and Git branches

| Machine | Role |
| --- | --- |
| MacBook M3, 8 GB | Earlier coding, tiny pandas jobs, docs, unit tests |
| Windows 11 PC, 31.4 GiB physical RAM | User-selected physical Dask experiment host (ADR-005) |

The original 16 GB plan is a conservative sizing reference. The actual host has 32 GB marketed RAM; **worker caps and the eight-config grid stay unchanged**. The earlier Mac, Windows and advisor work is included in `main` after a 2026-10-28 fast-forward merge. Their original branches remain as checkpoints. For this completion task use `codex/main-advisor-completion`; use the research branch only for that separate study. Generated Parquet, JSONL runs, validation study directories and `.venv` are gitignored.

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

## Original project checkpoint

The balanced selection implementation and the original Windows study are now merged into `main` and published. The technical results draft and separate tiny live Dask demo are complete. Remaining experimental work is prospective evaluation on the original Windows host; broader profiles need new data and a revised model/support policy. See `docs/INDEPENDENT_VALIDATION.md`. Formal submission remains pending. Optional TabPFN remains unrun; no failure classifier is supported because all 96 measured jobs succeeded.

## Design rules

- Use pre-run features only for inference. A job's actual runtime, memory, status, and spill cannot enter its prediction vector.
- Optimize the declared balanced dimensionless score using point runtime; test deadlines against the frozen upper estimate. Use explicit hard checks and abstain when none pass. Preserve historical cost/model features for old report reproduction.
- Keep memory caps at 1 GB and 2 GB despite the larger host. State that results come from a single Windows PC with induced worker caps.
- Failure handling stays deterministic until enough correctly labeled independent failure data supports training and held-out evaluation. A fixed number of positives alone does not establish classifier quality.
- Every reported number must identify its source study. Keep original measurements, fresh validation and research results separate. No Glue, 176-run, or unmeasured improvement claims.

## Documents

[`PROGRESS.md`](PROGRESS.md) is the status ledger; [`docs/MICROPLAN.md`](docs/MICROPLAN.md) has task cards; [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines component contracts; [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) lists acceptance criteria; [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md) is the conservative six-week schedule. ADR-005 records the actual host change.
