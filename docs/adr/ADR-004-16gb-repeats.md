# ADR-004 — 16 GB host buys repeats, not a bigger feature set

- **Date:** 2026-10-25
- **Status:** Accepted

## Context

The experiment PC has **16 GB RAM**. The coding Mac remains **8 GB**. The Phase 0 rule was: if the Dask PC is 16 GB, add repeats for error bars, not extra knobs, families, or Glue.

Extra physical RAM is **host headroom** (OS, Python, one LocalCluster). Worker `memory_limit` stays **1 GB and 2 GB** so spill/timeout still happen. Raising worker caps to 8 GB would hide the failure modes the project is about.

## Decision

- Keep **8** candidates: `n_workers ∈ {1,2}` × `threads_per_worker ∈ {1,2}` × `memory_limit ∈ {1GB, 2GB}`.
- Run **3 independent repeats** per family×config cell, randomized order, one job at a time.
- Main matrix: **4 × 8 × 3 = 96** physical runs, plus **4** T0/pilot jobs. Confirmation vs default is computed from those 96 (no extra 16-run confirmation campaign).
- Dataset size: target **150–250 MB** per family (still inside 50–300 MB). Shrink after T0 if median job > ~8 minutes.
- Do **not** add configs, backends, or a 24-run dedicated failure grid. Induced failures from the 1 GB cells are the failure sample.

## Alternatives rejected

- 16 configs / 176 runs — still too much for six weeks.
- `memory_limit` {4GB, 8GB} — uses the RAM, kills the failure instrument.
- 2 workers × 8 GB — host contention and no spill story.

## Consequences

Evaluation can report **mean ± interval** over repeats (bootstrap over cells). If overnight running is impossible, drop to **2 repeats** (64 main runs) before dropping a family.
