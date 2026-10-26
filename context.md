# context.md

**Role:** Canonical project memory. A new chat or teammate should read this first.  
**Updated:** 2026-10-26  
**How to update:** After every accepted decision, completed task, or scope change, edit **Status**, **Current task**, and any section that would otherwise be a lie.

GitHub: https://github.com/Aggdaksh/SAFE-Pipe1  
Local: `/Users/dakshaggarwal/safe-pipe`  
Branch with the latest code+docs (if not yet merged): `cursor/context-and-microplan`

---

## One line

SAFE-Pipe recommends the cheapest **safe** memory-capped Dask config under an SLA, or **abstains**. Project-I evidence must come from one **16 GB** PC. The 8 GB Mac only has tests, tiny pandas stand-ins, and docs.

## Problem

Batch Dask jobs change runtime and reliability with size, skew, partitions, and worker memory. Defaults waste RAM on easy scans and spill/timeout on joins. The system picks from a **declared** set of eight configs, using uncertainty and an OOD gate.

## Frozen direction (do not silently expand)

- **B-lite.** The DTU PDF (176 Dask runs + Glue) is **not** the spec.
- **96** main runs: 4 families × 8 configs × **3 repeats** (ADR-004).
- Worker `memory_limit` stays **1 GB or 2 GB**. Host 16 GB is not given to workers.
- Models (not started): LightGBM + split conformal + leave-one-family OOD. Failure **rules** unless ~30+ positives. TabPFN on Colab optional.
- Cost: normalized vCPU-seconds + GB-seconds.

**Out:** Glue evidence, Spark, LLM, from-scratch DL policy, microservices, cluster claims.

## Hardware

| Machine | RAM | Use |
| --- | --- | --- |
| MacBook M3 (this coding laptop) | 8 GB | git, pytest, docs, tiny pandas generators |
| Experiment PC | **16 GB**, OS **unknown** | Official T0, T0b, 96 Dask runs |

Do not run the 8-config Dask matrix on the Mac.

## What exists in code (verified 2026-10-26)

`pytest`: **20 passed** on the Mac (`.venv`, 2026-10-26).

| Piece | State | Evidence |
| --- | --- | --- |
| Schemas + optimizer | DONE | upper-bound SLA, red OOD abstain |
| Frozen 8-config grid | DONE | `configs/dask_grid.json`; `safe-pipe grid` |
| JSONL run store | DONE | `tests/test_store.py` |
| Tiny 4-family Parquet generators | DONE | `--tiny` default 2000 rows; CI uses 400 |
| Pandas execute + collector | DONE | CLI `collect` wrote `success pandas_local w1_t1_1g` |
| 96-cell planner | DONE | `planned_cells() == 96` |
| Failure classifier | DONE | timeout → TIMEOUT; KilledWorker → OOM |
| T0 Dask smoke script | WRITTEN, **not run on 16 GB PC** | `experiments/t0_smoke.py` |
| T0b | GUARD only | exits 2 without `--i-am-on-16gb`; Dask body **not implemented** |
| LightGBM / conformal / OOD / SHAP | NOT STARTED | — |
| Glue | OUT OF SCOPE | — |

## Current task

**Next engineering that produces Project-I evidence:** T0 on the 16 GB PC. Follow [`reports/HANDOFF_16GB.md`](reports/HANDOFF_16GB.md).

Mac-side slice 0–3 (pandas) is implemented and tested. It is **not** a substitute for Dask results.

## Immediate next steps

1. Merge or push `cursor/context-and-microplan` if this session’s files are not on GitHub yet.
2. On the 16 GB PC: clone, `pip install -e ".[dev,dask]"`, `python experiments/t0_smoke.py`, write `reports/t0.md` (OS, RAM, Dask version).
3. Implement T0b Dask body (still behind `--i-am-on-16gb`).
4. Only then generate 150–250 MB (or 80 MB if slow) and collect 96 Dask runs.

## Requirements / architecture

[`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) · [`DESIGN.md`](DESIGN.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/MICROPLAN.md`](docs/MICROPLAN.md)

## Experiment grid (declared)

`w1_t1_1g` … `w2_t2_2g` as in `configs/dask_grid.json`.  
Families: `scan_filter`, `groupby`, `skewed_join`, `sort_merge`.

## CLI (Mac, no Dask)

```bash
pip install -e ".[dev]"
pytest
safe-pipe recommend --estimates examples/estimates.json --sla 20
safe-pipe grid
safe-pipe generate --dest data/generated
safe-pipe collect --family scan_filter
```

## Leakage and labels

Pre-run features only. Timeouts are censored, not success. Repeats of family+config stay in one split group.

## Success (Project-I) — still unmet

Need frozen `data/curated/runs.parquet` from **Dask** on the 16 GB PC, then models and a report whose numbers equal that parquet.

## Doc map

| File | Purpose |
| --- | --- |
| `context.md` | **This file** |
| `docs/SESSION_STATUS.md` | 2026-10-26 snapshot for the next chat |
| `reports/HANDOFF_16GB.md` | Exact steps for the experiment PC |
| `PROGRESS.md` | Status ledger |
| `docs/MICROPLAN.md` | Task cards |
| `docs/SYNOPSIS_BLITE.md` | DTU paste text |
