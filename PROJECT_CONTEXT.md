# PROJECT_CONTEXT.md

**Project:** SAFE-Pipe (B-lite)  
**One line:** Pre-run, SLA-constrained Dask config selection with conformal uncertainty and abstention, evaluated on a memory-capped personal computer.  
**Updated:** 2026-10-25

## Problem and motivation

Default Dask settings waste capacity on easy jobs and fail on skewed or memory-heavy ones. Cloud search is out of budget. The system must pick a cheap **safe** config or refuse.

## Users and use cases

- Experimenter: generate data, run matrix, train, evaluate.
- Examiner demo: profile → recommend/abstain → execute one job → predicted vs actual.

## Objectives and outcomes

See [`docs/PHASE1_DECISION.md`](docs/PHASE1_DECISION.md). Project-I outcome is a working optimizer plus honest tables, not a SaaS.

## Finalized idea and scope

Accepted: **Option B (B-lite)**. Original synopsis PDF is a historical document, not the spec.

**In:** local Dask on a **16 GB** PC, 4 families, 8 candidates, **96** runs (3 repeats), LightGBM + split conformal + OOD, rules-gated failure, optional TabPFN comparison, SHAP for explanation.

**Out:** Glue evidence, Spark, LLM, from-scratch DL policy, microservices, “176 runs”, cluster claims.

## Requirements (MoSCoW)

**Must**

- Typed schemas for workload, objective, configuration, run result.
- Dask adapter that starts a LocalCluster with an explicit `memory_limit`.
- Optimizer: cheapest candidate whose conformal upper bound ≤ SLA and who passes safety rules; else abstain.
- Run store as JSONL/Parquet records (no secrets).
- Tests for optimizer and schema validation.

**Should**

- Four workload generators.
- Grouped train/calibration/test split; leave-one-family OOD report.
- SHAP explanation of the recommended config’s runtime model.

**Could**

- TabPFN Colab notebook on exported CSV.
- Tiny Streamlit/CLI demo UI.

**Won’t (Project-I)**

- AWS Glue jobs, billed DPU, CloudWatch evaluation.
- Adaptive Dask as a trained policy (it may be a **baseline**, if time).

## Architecture summary

```
WorkloadSpec + ObjectiveSpec
        │
        ▼
  Profiler (pre-run features only)
        │
        ▼
  OOD gate (green / yellow / red)
        │
        ▼
  Runtime model + conformal upper
  + rule-based failure guard
        │
        ▼
  Cost/SLA derivation + argmin
        │
        ▼
  Recommendation | Abstention
        │
        ▼
  Dask adapter execute + RunResult store
```

MacBook M3 (8 GB) is for code, tests, and docs. Physical Dask matrix runs on the second PC (**16 GB RAM**, OS still unrecorded) with worker `memory_limit` 1–2 GB and 1–2 workers. Host RAM is not given to workers.

## Stack and why

| Choice | Why |
| --- | --- |
| Python 3.11+ | Team language; Dask ecosystem. |
| Pydantic v2 | Explicit contracts; viva-friendly schemas. |
| Dask distributed LocalCluster | Real scheduler/worker memory behavior without AWS. |
| LightGBM | Strong tabular default; small data; explainable. |
| Split conformal | Distribution-free upper bound students can defend. |
| scikit-learn | Baselines, scaling, metrics. |
| TabPFN (Colab only) | Honest “AI” comparison; too heavy for 8 GB laptop training. |
| pytest | Optimizer must be correct without a cluster. |
| Parquet + JSONL | Reproducible, cheap, grep-able. |

## Algorithms and data

- Runtime: LightGBM on log-runtime of **successful** runs.
- Uncertainty: split conformal residual quantile on a held-out calibration set.
- OOD: standardized k-NN distance in workload-feature space, family-aware; held-out family is the stress test.
- Cost (local): `w1 * allocated_core_seconds + w2 * allocated_gb_seconds` (weights declared, not fitted).
- Failure: rules (memory_limit vs estimated peak, timeout vs SLA) unless the 30-positive gate trips.

Leakage rule: no post-run metric may enter the feature vector of that same run.

## Repository structure

```
safe_pipe/           library
experiments/         T0 smoke and later collectors
tests/               unit tests (no cluster required)
docs/                phase records and ADRs
data/                generated locally, mostly gitignored
```

## External services

None required for Project-I. Optional: Google Colab/Kaggle for TabPFN. No AWS keys in this repo.

## Status

Documentation system: **written**.  
Optimizer/schemas: **unit-tested** (`pytest` 8 passed, 2026-10-25).  
Executor / model training: **not started**.  
T0 Dask smoke: **script added, not executed on the experiment PC**.  
Hardware: experiment PC RAM **16 GB** (2026-10-25); OS not yet recorded. Plan: [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md).

## Setup

See README. Required env vars are names only in `.env.example`.

## Success criteria

Match [`docs/PHASE1_DECISION.md`](docs/PHASE1_DECISION.md) minimum acceptance. Metrics must be computed from the run store, never invented.

## Conventions

- Time in seconds, bytes as integers, memory as Dask strings (`1.5GB`) plus a parsed byte count.
- Status vocabulary in PROGRESS.md: `NOT STARTED` | `IN PROGRESS` | `BLOCKED` | `IN REVIEW` | `DONE` | `DEFERRED`.
- `DONE` requires acceptance criteria and verification evidence.

## Related docs

DESIGN.md, DECISIONS.md, PROGRESS.md, ROADMAP.md, docs/PHASE0_FEASIBILITY.md, docs/PHASE1_DECISION.md, docs/SYNOPSIS_BLITE.md.
