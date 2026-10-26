# PROGRESS.md

**Updated:** 2026-10-26 (docs freeze for next session)

## Completed and verified

- Phase 0/1 docs, B-lite freeze, GitHub `https://github.com/Aggdaksh/SAFE-Pipe1.git`.
- Optimizer + schemas: originally 8 tests (2026-10-25).
- **2026-10-26 Mac:** `pytest` **20 passed**. CLI `collect` on tiny scan_filter → `success pandas_local w1_t1_1g`.
- T-GRID: `configs/dask_grid.json` eight ids, allocated vCPU/GB tests.
- T-STORE: JSONL append/read.
- T-GEN (tiny only): four families via pandas/pyarrow. Full 150–250 MB **not** generated (waits T0b).
- T-COL (pandas only): success + timeout (`timeout_s=0`) unit tests. Dask collector **not** implemented.
- T-CTX / T-ARCH: living `context.md` + architecture/requirements/microplan.
- T0b guard: missing `--i-am-on-16gb` returns exit 2.

## In progress

- T-HW: RAM=16 GB recorded; **OS unknown**.
- T0: script exists; **not executed on the 16 GB PC**. Not run on the 8 GB Mac (would swap / is not official evidence).

## Next tasks

1. Commit/push remaining uncommitted code+docs on `cursor/context-and-microplan` if still dirty.
2. T0 on 16 GB PC → `reports/t0.md` (`reports/HANDOFF_16GB.md`).
3. Implement T0b Dask body; freeze dataset MB.
4. Dask execute + 96-run collector on that PC.
5. New chat: start from `context.md` + `docs/SESSION_STATUS.md`.

## Blocked

- Official Dask matrix, models, SHAP, TabPFN: waiting on T0 on the 16 GB PC.

## Known issues

- Worker caps stay 1–2 GB despite 16 GB host (ADR-004).
- Pandas collector timeout is a **post-hoc wall-clock check**, not a preemptive kill. Fine for tiny data; Dask path needs a real timeout.
- `safe-pipe collect` always regenerates the family under `--data-dir`.

## Deferred

- Glue. TabPFN until a Dask CSV exists. Streamlit.

## Testing and validation status

- Unit (Mac, no Dask): **20 passed**, 2026-10-26.
- T0 Dask: **not executed**.
- 96-run matrix: **not started**.

## Immediate next actions

On the 16 GB PC: `pip install -e ".[dev,dask]"` then `python experiments/t0_smoke.py`.

## Task register

| ID | Task | Status | Evidence |
| --- | --- | --- | --- |
| T-DOC / T-CTX / T-ARCH | Docs system | DONE | `context.md`, `docs/*` |
| T-SCH / T-OPT | Schemas + optimizer | DONE | pytest |
| T-GRID | 8 configs | DONE | `configs/dask_grid.json` |
| T-STORE | JSONL | DONE | `tests/test_store.py` |
| T-GEN | Tiny generators | DONE (tiny) | `tests/test_workloads.py`; scale DEFERRED until T0b |
| T-COL | Pandas collector | DONE (pandas) | CLI collect success; Dask DEFERRED |
| T-HW | RAM/OS | IN PROGRESS | 16 GB; OS unknown |
| T0 | Dask smoke | NOT STARTED | needs 16 GB PC |
| T0b | 50 MB 1g vs 2g | NOT STARTED | guard only |
| T-MX1 / T-MX2 | 96 Dask runs | NOT STARTED | planner exists (`planned_cells==96`) |
| T-ML … T-REP | Models/report | NOT STARTED | — |
