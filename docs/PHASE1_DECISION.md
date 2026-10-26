# Phase 1 — Selected direction: B-lite

**Hardware update (ADR-005, 2026-10-26):** The user selected a Windows PC with 31.4 GiB RAM for the physical experiment. The four-family/eight-config/three-repeat design and 1–2 GB worker caps remained unchanged. All 96 scored runs completed; see [`../reports/audit.md`](../reports/audit.md).

**Date:** 2026-10-25  
**Status:** Accepted for Project-I unless the supervisor rejects the reduced experiment size.  
**Gate:** Do not expand back to Glue or 176 runs without a new ADR.

## Decision matrix

Weights sum to 1.00. Scores are 1–5. Justification is qualitative; numbers are not lab measurements.

| Criterion | Weight | A MVP | B-lite | C PDF |
| --- | --- | --- | --- | --- |
| Problem significance | 0.10 | 4 | 5 | 5 |
| Technical depth | 0.15 | 3 | 5 | 5 |
| Feasibility (6 weeks, 8 GB, ~$0) | 0.20 | 5 | 4 | 1 |
| Differentiation | 0.10 | 3 | 4 | 4 |
| Demonstration value | 0.10 | 3 | 5 | 3 |
| Learning value | 0.10 | 3 | 5 | 4 |
| Evaluation quality | 0.10 | 3 | 4 | 2 |
| Time/cost efficiency | 0.10 | 5 | 4 | 1 |
| Integration risk | 0.05 | 5 | 4 | 1 |
| **Weighted** | | **3.70** | **4.45** | **2.80** |

B-lite wins because C’s depth is fictional under the constraints, and A drops the leave-one-family OOD story that makes the viva interesting.

## Frozen statement

**Problem.** Choose, before a Dask batch job starts, the cheapest **safe** configuration from a declared set under an SLA, or abstain.

**Users.** The team during experiments; the examiner during demo. Not a production multi-tenant SaaS.

**Objectives.**

1. Generate four synthetic Parquet families at 50–300 MB.
2. Execute a memory-capped Dask matrix on the **16 GB** PC: **4 families × 8 configs × 3 repeats = 96** runs (plus 4 T0/pilot jobs). Extra RAM is for repeats and CIs, not extra knobs (ADR-004).
3. Train LightGBM on successful runtimes; attach a split-conformal upper bound.
4. Apply OOD (leave-one-family) green/yellow/red; abstain on red.
5. Recommend argmin cost subject to conformal upper ≤ SLA and rule-based failure guard.
6. Compare against default, conservative, and random selection on the **same** run table.
7. Optional: TabPFN on Colab vs LightGBM on the exported features.

**Value.** Cost (normalized core-seconds × GB-seconds) down versus default **without** raising SLA violations, with a documented abstention rate.

**Differentiators.** Memory cap as a controlled failure instrument; conformal + OOD abstention; honest single-PC claim.

**Boundaries.** No Glue evidence. No Spark. No LLM. No from-scratch DL policy. No claim of cluster-scale Dask.

**Minimum acceptance.**

- `safe-pipe recommend` returns a candidate or abstention with reasons.
- At least one family fully measured on 8 configs.
- Grouped validation numbers exist (even if they are mediocre).
- Synopsis language matches the experiment.

**Success metrics (to be measured, not pre-filled).** MdAPE of runtime; 90% interval coverage and width; cost per successful run vs default; SLA miss rate; unsafe-recommendation rate; abstention rate on held-out family.

**Open uncertainties.** Experiment PC OS (Windows vs Linux) and overnight stability; whether ~30 actionable failures appear (if not, rules-only is the valid result). RAM is **16 GB** (recorded 2026-10-25).
