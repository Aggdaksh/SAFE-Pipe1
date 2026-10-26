# SAFE-Pipe project context

**Updated:** 2026-10-26. Read this file first when working from another PC.

## Purpose and scope

SAFE-Pipe recommends the cheapest safe configuration from eight declared local Dask configurations under an SLA, or abstains. Project-I evaluates four synthetic workload families on one physical PC with worker memory caps of 1 GB and 2 GB. The planned matrix is four families × eight configs × three repeats = 96 runs. LightGBM, split conformal bounds, OOD, baselines, and the report follow a frozen run table. Glue and multi-node claims are out of scope.

## Machines and Git branches

| Machine | Role |
| --- | --- |
| MacBook M3, 8 GB | Earlier coding, tiny pandas jobs, docs, unit tests |
| Windows 11 PC, 31.4 GiB physical RAM | User-selected physical Dask experiment host (ADR-005) |

The original 16 GB plan is a conservative sizing reference. The actual host has 32 GB marketed RAM; **worker caps and the eight-config grid stay unchanged**. Mac-side work was pushed to `cursor/context-and-microplan`; Windows Dask work is on `codex/windows-dask`. Pull the latest branch before editing on another PC. Generated Parquet, JSONL runs, and `.venv` are gitignored.

## Verified implementation

- Schemas, optimizer, eight-config grid, JSONL store, tiny four-family Parquet generators, pandas collector, and 96-cell planner came from the Mac branch.
- Windows `.venv` has `.[dev,dask]` installed under Python 3.14.6. The full suite has **24 passing tests**, including tiny Dask executions for all four families and a Dask collector timeout.
- T0 passed on the selected Windows PC: one 512 MB Dask worker returned the expected sum. See [`reports/t0.md`](reports/t0.md).
- T0b pilot compared 1 GB and 2 GB workers on two scan sizes and one sort size. The 136 MB sort took 10.58 s at 1 GB versus 4.53 s at 2 GB; both succeeded. See [`reports/t0b.md`](reports/t0b.md). No spill or OOM has been confirmed.
- Dask execution and one-cell collection are implemented; the scored matrix has **not** started.
- Four `main-v1` datasets (175–198 MB) are generated, fingerprinted, and ignored by Git. The committed index is `configs/datasets_main_v1.json`.
- Twelve 2 GB SLA pilot runs succeeded. Deadlines and the randomized 96-cell order were frozen in `configs/` before scored collection. See `reports/matrix_preparation.md`.
- All 96 Dask cells were measured and audited: 96 successes, zero SLA misses. The curated CSV is committed at `data/curated/runs.csv`; raw JSONL and Parquet remain local.
- Grouped LightGBM plus conformal, a conservative rule-based OOD gate, fitted CLI recommendation, descriptive same-table baselines, and a feature-contribution figure are implemented. See `reports/runtime_model.md`, `reports/policy.md`, and `reports/shap.md`.

## Current task

The technical results draft and separate tiny live Dask demo are complete in the repository. Push the Windows branch when GitHub write access works, then get team review and formal DTU submission. The optional TabPFN comparison remains unrun. No failure classifier can be supported because all 96 jobs succeeded.

## Design rules

- Use pre-run features only for inference. A job's actual runtime, memory, status, and spill cannot enter its prediction vector.
- Optimize expected cost using point runtime, but test the SLA against the conformal upper bound. Abstain for red OOD or no feasible candidate.
- Keep memory caps at 1 GB and 2 GB despite the larger host. State that results come from a single Windows PC with induced worker caps.
- Failure prediction stays rule-based unless about 30 credible actionable positives are observed.
- Every reported number must come from the frozen Dask run table. No Glue, 176-run, or unmeasured improvement claims.

## Documents

[`PROGRESS.md`](PROGRESS.md) is the status ledger; [`docs/MICROPLAN.md`](docs/MICROPLAN.md) has task cards; [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines component contracts; [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) lists acceptance criteria; [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md) is the conservative six-week schedule. ADR-005 records the actual host change.
