# DESIGN.md

**Updated:** 2026-10-25  
**Status:** Approved design for B-lite. Implementation status is per component, not implied by this document.  
**Canonical diagrams and contracts:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)  
**Requirements:** [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md)

## Goals and constraints

- Recommend or abstain **before** execution.
- Evidence from one 16 GB PC; workers memory-capped **on purpose** (1–2 GB).
- Prediction uses only pre-run features.
- Complexity budget: one process, one library, no message bus, no Glue runtime.

## Architecture overview

Single Python package. CLI in-process. Dask `LocalCluster` is an adapter detail.

See mermaid diagrams in `docs/ARCHITECTURE.md`. Short path:

`WorkloadSpec + ObjectiveSpec → profile → OOD → runtime+conformal + rules → cost/SLA → optimizer → Decision → optional execute → run store`

## Proposed vs implemented

| Component | Responsibility | Implemented? |
| --- | --- | --- |
| `schemas` | Pydantic contracts | Yes (v0) — extend `RunResult` before collector |
| `optimizer` | Feasible set + argmin cost / abstain | Yes (v0, supplied estimates) |
| `adapters.dask` | LocalCluster factory | Partial (T0 helper, not run on PC) |
| `configs/dask_grid.json` | Eight native configs | No |
| `workloads` | Four generators + DAGs | No |
| `features` | Pre-run profiler | No |
| `models` | LightGBM, conformal, OOD | No |
| `run_store` | JSONL/Parquet append-only | No |
| `cli` | profile/train/recommend/execute | recommend stub only |
| Glue adapter | — | Out of Project-I |

## Interfaces (stable)

```
recommend(estimates: list[CandidateEstimate], objective: ObjectiveSpec) -> Decision
```

- SLA constraint uses **`runtime_upper_s`**, not the point estimate.
- Red OOD is never feasible.
- Yellow may be recommended if constraints pass.
- Cost tie-break: `expected_cost`, then `runtime_upper_s`, then `config_id`.

**Cost vs SLA (decision):** point estimate drives `expected_cost`; conformal upper drives the SLA check. Do not optimize the upper bound as if it were mean cost.

## Data model

v0 in `safe_pipe/schemas.py`. Collector must add (still proposed): `repeat_id`, `data_version`, `hardware`, `sla_seconds`, `predicted_upper_s`, `failure_category`, `voided`.

## Failure taxonomy

- **Actionable:** OOM/nanny, excessive spill, timeout, skew/stragglers.
- **Transient:** worker lost — record; do not auto-mean “needs more RAM”.
- **Non-configuration:** user code, missing files.

## Error handling

See table in `docs/ARCHITECTURE.md`. Always close the cluster. One job at a time. Corrupt jobs are voided, not edited.

## Auth / trust

No auth. Synthetic data. The academic trust boundary is **report honesty**.

## Performance

Optimizer < 1 s for 8 candidates. Physical jobs may take minutes. Bottleneck is wall-clock collection, not ranking.

## Testing

- Unit (Mac, no Dask extras required): schemas, optimizer, store, grid size, leakage helpers.
- T0/T0b: manual on 16 GB PC, evidence in `reports/`.
- Later: grouped-split tests on frozen CSV; evaluation scripts.

## Deployment

None. Demo = pytest + one live Dask job + frozen tables.

## Trade-offs

- Local Dask ≠ Glue.
- Induced failures via `memory_limit` must be labeled induced.
- “Best in the declared set of eight”, never globally optimal.
- 3 repeats on 16 GB instead of more knobs (ADR-004).
