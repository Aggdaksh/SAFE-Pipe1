# Session status — 2026-10-26 (coding Mac)

Read this plus [`../context.md`](../context.md) in a new chat. Do not assume Dask results exist.

## What this session / repo actually is

SAFE-Pipe B-lite: cheapest **safe** memory-capped Dask config under an SLA, or abstain. Official evidence = **16 GB experiment PC**. This Mac is **8 GB** and must not run the 8-config Dask matrix.

GitHub: https://github.com/Aggdaksh/SAFE-Pipe1  
Work may sit on branch `cursor/context-and-microplan` until merged to `main`.

## Verified on this Mac (2026-10-26)

`pytest`: **20 passed** (`.venv`, Python 3.14).

Implemented:

- Optimizer (`runtime_upper_s` for SLA; red OOD abstain; min cost)
- `configs/dask_grid.json` — eight ids `w1_t1_1g` … `w2_t2_2g`
- JSONL store
- Tiny 4-family Parquet generators (default 2000 rows; tests use 400)
- Pandas execute + pandas collector (success + timeout-after-the-fact)
- 96-cell planner `planned_cells() == 96`
- Exception classifier (string matching)
- CLI: `recommend`, `grid`, `generate`, `collect`
- T0 script **not executed** on 16 GB PC; refused on 8 GB unless override
- T0b: guard only (`--i-am-on-16gb`); Dask body **not written**

## Explicitly not done (do not mark DONE)

| Item | Why |
| --- | --- |
| T0 on 16 GB PC | No access this session; OS still unknown |
| T0b 1g vs 2g timings | Needs T0 + Dask body |
| 150–250 MB datasets | Gated on T0b |
| Dask execute of four families | Not implemented |
| 96-run JSONL from Dask | Not started |
| LightGBM, conformal fit, OOD, SHAP, TabPFN | No Dask table |
| Glue | Out of scope |

## Next chat — do this in order

1. Confirm git: commit/push uncommitted grid/store/workloads if still dirty.
2. On **16 GB PC**: [`../reports/HANDOFF_16GB.md`](../reports/HANDOFF_16GB.md) — T0 first.
3. Implement `execute_dask` + T0b body behind `--i-am-on-16gb`.
4. Freeze MB from T0b; then 96 runs one-at-a-time.
5. Only then T-ML.

## Do not

- Invent Glue, 176-run, or DL accuracy numbers.
- Raise worker `memory_limit` to “use 16 GB”.
- Call pandas collector results “Dask evaluation”.
- Run T0 on the 8 GB Mac as official evidence.

## Commands (Mac)

```bash
pip install -e ".[dev]"
pytest
safe-pipe recommend --estimates examples/estimates.json --sla 20
safe-pipe grid
safe-pipe generate --dest data/generated
safe-pipe collect --family scan_filter
```
