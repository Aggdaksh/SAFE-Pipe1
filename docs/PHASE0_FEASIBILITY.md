# Phase 0 — Feasibility of the submitted synopsis PDF

**Date:** 2026-10-25  
**Sources:** `SAFE-Pipe_Project_Synopsis_DTU.pdf` (identical copy in Downloads), `SAFE-Pipe_Revised_Detailed_Implementation_Plan.pdf` (2 Sep 2026), and the prior QnA in `btp.txt`.  
**Status:** Complete. Idea not invented here; the PDF already existed. This document records why the PDF experiment is not the Project-I experiment.

## 1. Reconstruction of the proposal

### Explicitly stated (from the PDF)

1. **Problem.** Batch ETL on distributed platforms (Dask, AWS Glue) has runtime, cost, and reliability that depend on input size, partitioning, skew, transformation complexity, and configuration. A fixed setting wastes resources on light work and fails (spill, OOM, timeout, SLA miss) when conditions change.

2. **Who.** Organisations running batch pipelines. The academic user is DTU IT401 Group 45 (Daksh Aggarwal, Chaitanya Singh, Ganant Awasthi) under Dr. Dinesh Kumar Vishwakarma.

3. **Proposed solution.** An adapter-based pre-run decision system: workload profile + deadline + failure-risk limit + bounded candidates → estimate runtime/uncertainty → safety guards → retry-aware cost and SLA probability → cheapest safe candidate, or abstain.

4. **Users / workflow / outputs.** Client submits pipeline, dataset, backend, SLA, risk limit. System profiles, scores candidates, recommends or abstains, monitors execution, stores an auditable result.

5. **Technologies.** Shared schemas; Dask and AWS Glue adapters; gradient-boosted runtime model; split conformal interval; OOD green/yellow/red; evidence-gated failure ML; versioned run store.

6. **Stated experiment size.** Dask: **176 runs** (8 smoke + 128 main + 24 near-failure + 16 confirmation), 16 candidates in the main matrix, 4 families × 2 regimes. Glue: 48 / 48–60 / 120–180 depending on history. Scope: scan/filter, group-by, skewed join, sort/merge.

### Interpretation (not in the PDF)

- “Distributed” in the title will be read by examiners as a cluster or cloud. Local Dask with two workers is still Dask, but it is **not** a cluster evaluation.
- The literature (Li/PVLDB Spark tuner, SelfTune, TUNA, Rockhopper) is real prior art. The PDF correctly says it does not invent those methods. The contribution is integration + evaluation. That only holds if the evaluation actually happens.

### Ambiguous or missing

- Hardware RAM of the Dask PC (8 vs 16 GB) is still unknown. Plan as **8 GB**.
- Whether the Dask PC can stay awake overnight, and OS (Windows vs Linux), is unknown.
- AWS account, Glue history, and budget are unspecified. Prior QnA: **no paid Glue campaign**.
- Project-I calendar: prior QnA locked **~6 weeks** to a full Project-I final, not the PDF’s 16-week plan.
- Coding machine: MacBook M3 **8 GB**. That machine is not the Dask experiment host.

### Assumptions that can invalidate the project

| Assumption | If false |
| --- | --- |
| You can run 176 Dask jobs with 16 configs on available hardware | Main-matrix chapter is fiction |
| Glue runs are fundable and logged | Glue chapter must be deleted, not “future work” with invented numbers |
| Failures will appear in useful volume | Failure ML must stay rules-only |
| Tabular DL is a good policy on ~100 rows | Examiners can dismiss the DL chapter |
| “Distributed” will be accepted for single-PC Dask | Title/synopsis must say **memory-capped local Dask** |

## 2. Feasibility assessment

Scoring: 1 = blocks Project-I, 3 = painful but workable, 5 = comfortable. Method: score the **PDF as written**, then **B-lite**.

| Dimension | PDF | B-lite | Notes |
| --- | --- | --- | --- |
| Technical feasibility | 2 | 4 | Local Dask + LightGBM is standard. Glue + 176 runs is not, on 8 GB. |
| Time (6 weeks) | 1 | 4 | PDF week plan is 16 weeks. |
| Scope | 1 | 4 | Two backends + 176 + 16 candidates is the failure mode. |
| Learning curve | 3 | 4 | Dask memory + conformal + OOD is enough depth. |
| Data / APIs | 2 | 4 | Synthetic Parquet is free. Glue APIs need money and an account. |
| Cost | 1 | 5 | Glue DPU-hours for 48–180 jobs is not “little/no cost”. |
| Integration | 2 | 4 | One adapter. |
| Security / privacy | 5 | 5 | Synthetic data. |
| Testing | 2 | 4 | PDF volume cannot be repeated for CI. |
| Demo | 3 | 4 | Recommend → run → predicted vs actual is a viva-friendly demo. |
| Academic depth | 4 | 4 | Constrained optimization + uncertainty + abstention is enough. PDF over-claims. |
| Maintainability | 3 | 4 | Smaller surface. |
| Third-party dependency | 1 | 4 | Glue/Spark/LLM removed. TabPFN is optional Colab. |
| Failure scenarios | 2 | 4 | Induced spill via `memory_limit` is the honest failure generator. |

**Critical blockers (PDF):** Glue evidence; 176-run matrix on 8 GB; from-scratch DL as policy; 16-week plan squeezed into 6.

**Manageable difficulties (B-lite):** Dask on Windows; noise in single-PC timings; too few natural failures; 8 GB coding laptop swapping if you run Dask there.

## 3. Research notes (verified vs estimated)

Verified from the PDFs themselves (not from re-running jobs):

- Synopsis and Downloads copy are **byte-identical** (MD5 `6cdda9c5f0dda56ccdf01be8e6cbc5b7`, 3 pages).
- Revised plan dated 2 Sep 2026 already contains a week-2 Glue-or-Dask gate and says local simulation cannot validate Glue billing.

Not verified in this session: Dask PC RAM, overnight uptime, Glue account, any physical run.

Primary sources listed in the plan remain the right citations if the evaluation matches the claim ([Dask worker memory](https://distributed.dask.org/en/stable/worker-memory.html), [Dask Adaptive](https://docs.dask.org/en/latest/adaptive.html), Li et al. PVLDB 2023, TUNA EuroSys 2025). Do not cite Glue Auto Scaling as evaluated.

## 4. Improvements that matter

Keep: pre-run bounded selection, SLA + risk constraints, conformal uncertainty, OOD abstention, auditable run store, four workload families.

Cut: Glue as evidence, 16-candidate exhaustive language, “distributed pipelines” without a qualifier, LLM, Spark, 176-run tables.

Add: explicit **memory cap** as the experimental instrument; **TabPFN on Colab** as a comparison on the same CSV; SHAP for the demo; Option A fallback (drop one family, fewer repeats) if week 3 slips.

## 5. Alternatives

**Option A — MVP.** Two families, 4 candidates, ~32 runs, rules-only failure, linear/GBDT runtime, no TabPFN. Solves the same problem with less viva surface.

**Option B — B-lite (recommended).** Four families, 8 candidates, 72–96 runs, LightGBM + conformal + OOD, rules-gated failure, TabPFN comparison, SHAP. See Phase 1.

**Option C — Ambitious.** PDF as written. Not feasible in 6 weeks at near-zero cost on 8 GB.

Option B is strictly better than C for this team. A is the official fallback, not the opening bid.

## 6. Verdict

1. **PDF as written:** not currently feasible.  
2. **B-lite:** feasible with modifications (already specified).  
3. Strongest aspects: clear constrained-decision problem; honest prior-art stance; adapter-shaped design; abstention as a first-class output.  
4. Weakest aspects: experiment size, Glue, title overclaim, DL-as-policy temptation.  
5. Blockers: Glue budget; 176 runs; unknown Dask-PC RAM (mitigate by planning 8 GB).  
6. Highest-impact change: rewrite the synopsis to memory-capped Dask before anyone signs it.  
7. Recommendation: **B-lite**. Justification: it preserves the research question and the ML stack that can be defended, and it can actually be run.  
8. Unresolved questions that would change this: Dask PC is 16 GB (add repeats, not features); PC cannot stay up overnight (shrink to Option A); supervisor insists on Glue (then the project is not no-cost).
