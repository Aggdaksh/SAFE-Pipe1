# ADR-001 — B-lite is the Project-I scope

- **Date:** 2026-10-25
- **Status:** Accepted

## Context

The DTU synopsis PDF specifies 176 Dask runs, 16 candidates, Glue adapters with 48–180 cloud jobs, and a 16-week plan. Constraints from the team: ~6 weeks, near-zero cost, MacBook M3 8 GB for coding, a second PC of unknown RAM (plan 8 GB), Colab available for training only.

## Decision

Implement **B-lite**: 4 families, 8 candidates, 72–96 runs, 50–300 MB Parquet, no Glue evidence.

## Alternatives

- PDF as written — infeasible.
- Option A (2 families, ~32 runs) — fallback if T0 or week 3 fails.

## Consequences

Synopsis must be rewritten before submission. Any table that still says 176 or Glue DPU is a defect.
