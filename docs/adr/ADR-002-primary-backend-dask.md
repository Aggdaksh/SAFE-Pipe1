# ADR-002 — Memory-capped local Dask is the primary backend

- **Date:** 2026-10-25
- **Status:** Accepted

## Context

The revised plan allows Dask or Glue. Glue needs an AWS account and DPU spend. Local simulation cannot validate Glue billing or Auto Scaling.

## Decision

Primary evidence: `distributed.LocalCluster` on the **16 GB** experiment PC with 1–2 workers and `memory_limit` **1–2 GB** to induce spill/timeout. Host RAM is not assigned to workers (ADR-004). Cost is normalized core-seconds and GB-seconds, not USD.

## Alternatives

- Glue-Lite — rejected for Project-I (cost and access).
- Multi-node Dask — no second machine we can treat as a cluster.

## Consequences

Title and talk track must say “single-PC, memory-capped”. Dask Adaptive may be a baseline later, not the learned policy.
