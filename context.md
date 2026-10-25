# context.md

**Role:** Canonical project memory. A new chat or teammate should read this first.  
**Updated:** 2026-10-25 (evening)  
**How to update:** After every accepted decision, completed task, or scope change, edit the **Status**, **Current task**, and any section that would otherwise be a lie. Do not leave superseded facts in place. Point to ADRs instead of rewriting history in place.

GitHub: https://github.com/Aggdaksh/SAFE-Pipe1  
Local: `/Users/dakshaggarwal/safe-pipe`

---

## One line

SAFE-Pipe recommends the cheapest **safe** memory-capped Dask config under an SLA, or **abstains**. Project-I evidence is one **16 GB** PC, not Glue and not a cluster.

## Problem

Batch Dask jobs change runtime and reliability with size, skew, partitions, and worker memory. Defaults waste RAM on easy scans and spill/timeout on joins. Students cannot buy Glue DPU hours. The system must pick from a **declared** set of eight configs, using uncertainty and an out-of-distribution gate.

## Users

| User | Job |
| --- | --- |
| Team (experimenter) | Generate Parquet, run matrix, train, evaluate |
| Examiner (demo) | Profile → recommend/abstain → run one job → predicted vs actual |

Not a multi-tenant SaaS.

## Frozen direction (do not silently expand)

- **Option B-lite.** Original DTU PDF (176 Dask runs + Glue) is **not** the spec. See `docs/PHASE0_FEASIBILITY.md` and `docs/PHASE1_DECISION.md`.
- **96** main runs: 4 families × 8 configs × **3 repeats** (16 GB buys repeats, not more knobs — ADR-004).
- Worker `memory_limit` stays **1 GB or 2 GB**. Host has 16 GB; workers do not get 8 GB.
- Models: LightGBM + split conformal + leave-one-family OOD. Failure **rules** unless ~30+ actionable positives. TabPFN on Colab is optional comparison, not the CLI brain.
- Cost is **normalized** (`vCPU-seconds + GB-seconds`), not USD.

**Out of Project-I:** Glue evidence, Spark, LLM, from-scratch DL policy, microservices, “distributed cluster” claims, 176-run tables.

## Hardware split

| Machine | RAM | Use |
| --- | --- | --- |
| MacBook M3 (coding) | 8 GB | git, pytest, docs, LightGBM on CSV |
| Experiment PC | **16 GB** (OS **unknown**) | T0, data gen, 96-run collector |

Do not run the main matrix on the Mac.

## What exists in code (verified)

| Piece | State | Evidence |
| --- | --- | --- |
| Pydantic schemas v0 | DONE | `safe_pipe/schemas.py` |
| Optimizer (upper-bound SLA, red OOD abstain, min cost) | DONE | `pytest` 8 passed 2026-10-25 |
| CLI `recommend` from JSON | DONE | `examples/estimates.json` |
| Dask LocalCluster helper + T0 script | WRITTEN, **not run** | `experiments/t0_smoke.py` |
| Generators, run store, models | NOT STARTED | — |

## Current task

**Micro-planning and architecture docs** (this update).  
**Next engineering task after docs:** T0 on the 16 GB PC (`python experiments/t0_smoke.py`) and record OS in this file.

## Immediate next steps

1. Keep this file honest after T0 (paste OS, Dask version, elapsed).
2. T0b: 50 MB scan, `w1_t1_1g` vs `w1_t1_2g`.
3. Implement generators only after T0b sets scale.

## Requirements pointer

Full MoSCoW and acceptance: [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md).

**Must (short):** schemas, memory-capped Dask adapter, optimizer with abstention, JSONL run store, grouped evaluation, synopsis matching the experiment.

## Architecture pointer

[`DESIGN.md`](DESIGN.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). One Python package, in-process CLI, `LocalCluster` behind an adapter. No queue, no microservices.

## Stack

Python 3.11+, Pydantic v2, Dask distributed LocalCluster, LightGBM, scikit-learn, pytest, Parquet/JSONL. TabPFN only on Colab.

## Experiment grid (declared)

Configs: `w{1,2}_t{1,2}_{1g,2g}` — workers × threads × memory_limit.  
Families: `scan_filter`, `groupby`, `skewed_join`, `sort_merge`.  
Data: ~150–250 MB Parquet after T0b; shrink to ~80 MB if 50 MB already takes > 8 minutes.

## Leakage and labels

- Features for a run: only information known **before** that run.
- Timeouts: censored lower bounds, never successful runtime.
- Repeats of the same family+config stay in the same split group.

## Success (Project-I)

- `safe-pipe recommend` uses fitted artifacts or clearly labeled demo JSON.
- Frozen `data/curated/runs.parquet` with 96 rows (or a documented slip to 2 repeats / Option A).
- Tables: MdAPE, 90% interval coverage, cost vs default/conservative/random, SLA misses, abstention on held-out family.
- Numbers in the report equal the parquet. No invented Glue or DL wins.

## Conventions

- Status words: `NOT STARTED` \| `IN PROGRESS` \| `BLOCKED` \| `IN REVIEW` \| `DONE` \| `DEFERRED`.
- `DONE` needs acceptance criteria **and** verification.
- Secrets never in git. `.env.example` names only.

## Doc map

| File | Purpose |
| --- | --- |
| `context.md` | **This file.** Living memory |
| `docs/REQUIREMENTS.md` | Functional / NFR / stories |
| `docs/ARCHITECTURE.md` | Components, data flow, contracts |
| `DESIGN.md` | Design goals, trade-offs, testing |
| `docs/MICROPLAN.md` | Task cards, dependencies, vertical slices |
| `docs/INVESTIGATIONS.md` | Experiments before we commit |
| `docs/PLAN_16GB.md` | Six-week calendar |
| `PROGRESS.md` | What is actually done |
| `DECISIONS.md` | ADR index |
| `docs/SYNOPSIS_BLITE.md` | Text for DTU |

`PROJECT_CONTEXT.md` is a stub that points here so old links do not fork the truth.
