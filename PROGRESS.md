# Progress

**Updated:** 2026-10-26. Canonical project context: [`context.md`](context.md).

## Completed and verified

| Task | Evidence |
| --- | --- |
| B-lite scope, architecture, requirements | `docs/PHASE1_DECISION.md`, `docs/ARCHITECTURE.md`, `docs/REQUIREMENTS.md` |
| Schemas, optimizer, eight-config grid | Unit tests; `configs/dask_grid.json` |
| JSONL store, tiny four-family generators, pandas collector | Mac branch tests |
| Experiment host identified | Windows 11 PC, 31.4 GiB physical RAM; ADR-005 |
| Dependencies | `.[dev,dask]` in ignored Windows `.venv`, Python 3.14.6 |
| T0 LocalCluster smoke | PASS, `reports/t0.md` |
| T0b 1 GB versus 2 GB probe | Pilot measurements and scale decision, `reports/t0b.md` |
| Four Dask family DAGs and timed one-cell collector | 24 tests pass, including tiny Dask integration and timeout |

## In progress

- Scale/fingerprint all four Parquet families to the T0b target sizes.
- Pilot group-by and skewed join, and freeze an SLA for each family before matrix scoring.
- Prepare a resumable, randomized, one-job-at-a-time 96-cell collector.

## Not started

- Scored 96-run matrix and curated Parquet table.
- Label/leakage audit, LightGBM, conformal intervals, OOD, fitted CLI policy, baselines, SHAP, report.

## Constraints and known limits

- The selected experiment host is 32 GB, replacing the plan's earlier 16 GB assumption. Worker `memory_limit` remains 1–2 GB and the grid remains eight configs.
- T0b timings are one run per cell and are **pilot evidence only**. The slower 1 GB sort does not by itself prove spill.
- The pandas collector has only a post-run timeout check. The Dask collector uses `future.result(timeout=...)` and cancels on timeout; cluster shutdown still requires observation under difficult worker failures.
- Peak worker memory is not yet captured. `peak_memory_bytes=null` is honest until telemetry is implemented.
- The original `safe-pipe collect` command regenerates its pandas dataset; the Dask matrix must load frozen manifests instead.

## Immediate next steps

1. Commit and push the Windows Dask branch so the other PCs can pull it.
2. Calibrate and verify all four datasets and pilot group-by/join.
3. Freeze SLAs and start the scored matrix; save each completed row to ignored JSONL.
4. Audit the frozen table before model training.
