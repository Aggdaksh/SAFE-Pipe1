# PROGRESS.md

**Updated:** 2026-10-25

## Completed and verified

- Phase 0 feasibility write-up from the DTU PDFs and prior QnA (`docs/PHASE0_FEASIBILITY.md`).
- Phase 1 freeze: B-lite (`docs/PHASE1_DECISION.md`).
- Repository created at `/Users/dakshaggarwal/safe-pipe` (this Mac). Remote: `https://github.com/Aggdaksh/SAFE-Pipe1.git`. The earlier Windows path `C:\Users\hp\Projects\safe-pipe` is **not** used.
- Optimizer unit tests written and executed on this Mac: `pytest` **8 passed** (2026-10-25). CLI `safe-pipe recommend` selected `w1_t1_1gb` on `examples/estimates.json` with SLA=20s.

## In progress

- T0 Dask smoke script (`experiments/t0_smoke.py`) — code present, **not** executed on the experiment PC.

## Next tasks

1. Record experiment PC **OS** (Windows vs Linux) in this file.
2. On the 16 GB PC: `pip install -e ".[dev,dask]"` and `python experiments/t0_smoke.py`; write `reports/t0.md`.
3. Submit [`docs/SYNOPSIS_BLITE.md`](docs/SYNOPSIS_BLITE.md) language to Dr. Vishwakarma.
4. Follow [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md) week 1 (T0b + generators).

## Blocked

- Physical Dask matrix: waiting on T0 on the 16 GB PC.

## Known issues

- Experiment PC RAM is **16 GB** (user-reported 2026-10-25). OS and overnight sleep behavior still unknown.
- Coding laptop is M3 8 GB; do not run the main matrix there.
- Worker caps stay 1–2 GB despite 16 GB host (ADR-004).

## Deferred

- Glue adapter implementation.
- TabPFN until a CSV exists.

## Recently completed milestones

- M0 docs/contracts: **DONE** (8 pytest tests passed on this Mac, 2026-10-25).

## Testing and validation status

- Optimizer/schema tests: **DONE** (`8 passed` in `.venv`).
- T0 Dask smoke: not executed (reserved for the experiment PC).

## Immediate next actions

T0 on the 16 GB experiment PC. Then T0b (50 MB, 1g vs 2g).

## Task register

| ID | Task | Status | Evidence |
| --- | --- | --- | --- |
| T-DOC | Phase 0/1 docs + ADRs | DONE | files in `docs/` |
| T-SCH | Pydantic schemas v0 | DONE | `safe_pipe/schemas.py` |
| T-OPT | Bounded optimizer v0 | DONE | `pytest` 8 passed, 2026-10-25 |
| T0 | Dask LocalCluster smoke | NOT STARTED | needs 16 GB PC |
| T-HW | Record RAM/OS | IN PROGRESS | RAM=16 GB; OS unknown |
