# SAFE-Pipe midterm presentation handoff

**Prepared:** 2026-10-26

**For:** the agent preparing the DTU IT401 Project-I midterm PowerPoint.
**Status:** factual brief plus a **proposed** extension of final-project scope. This file is not a revised approved synopsis, a slide deck, or evidence that future experiments have been run.

## 1. The position to present

The team has built and measured a complete **first local Dask prototype**. The next meaningful phase is to test whether its choices hold up on **new input profiles**, add reliable resource telemetry and controlled stress evidence, and finish independent comparisons and the formal report. This is a defensible *roughly halfway* midterm story **if** the supervisor accepts that expanded final plan. Do not create a larger denominator merely to claim 50%. Do not state an exact 40–50% score: no official midterm rubric or agreed weighting has been supplied.

The [detailed alignment review](MIDTERM_SYNOPSIS_ALIGNMENT.md) compares every expected goal in the submitted three-page synopsis with the repository. It is the source for any question about “what was promised versus what exists.” The synopsis PDF itself was supplied by the user outside this Git repository; ask for it again if the presentation agent cannot access it.

## 2. Identity and title-slide facts

| Item | Text to use |
| --- | --- |
| Institution | Delhi Technological University, Department of Information Technology |
| Course / stage | IT401 B.Tech Project-I — Midterm Evaluation |
| Project | SAFE-Pipe |
| Submitted title | **SAFE-Pipe: Failure-Aware Cost and Runtime Optimization of Distributed Data Pipelines under SLA Constraints** |
| Accurate evidence subtitle | **Midterm prototype and single-PC, memory-capped Dask evaluation** |
| Group | 45 |
| Team | Daksh Aggarwal; Chaitanya Singh; Ganant Awasthi |
| Supervisor named in submitted synopsis | Dr. Dinesh Kumar Vishwakarma |

Use the submitted title if the department requires it, but keep the subtitle and spoken explanation precise: the **measured** backend is Dask `LocalCluster` on **one Windows PC**, not a multi-node system or AWS Glue. Check the exact student IDs, supervisor designation, and title-slide formatting against the supplied PDF before exporting the deck; those personal identifiers are not copied into this Git handoff. Confirm whether a revised title has been accepted before changing the submitted title.

## 3. Thirty-second project explanation

Batch data pipelines can run slowly or waste resources depending on input size, operation pattern, workers, threads and memory. SAFE-Pipe takes a **pre-run workload profile** and a deadline, estimates how long each of a fixed set of Dask settings will take, adds a cautious runtime upper bound, and recommends the lowest estimated **normalized local resource cost** among eligible settings. It can abstain when evidence is outside the measured scope or no candidate passes the deadline. The current implementation is a research prototype on synthetic Parquet data.

**Research question for the current evidence:** Can a bounded, uncertainty-aware configuration choice reduce normalized resource cost relative to fixed settings while respecting a job deadline on memory-capped local Dask? The current data permit a first descriptive answer, not an independent general improvement or failure-reduction claim.

## 4. Three versions of scope — keep them separate

| Version | What it says | Status |
| --- | --- | --- |
| **Submitted synopsis PDF** | Broad adapter-based Dask/Glue vision. Dask option describes 176 runs: 8 smoke, 128 main-matrix (four families × two regimes × 16 candidates), 24 near-failure and 16 confirmation. It also mentions retry-aware cost, SLA probability, fallback and native adaptive comparison. | Historical submitted proposal. These items are **not** all implemented. |
| **Current B-lite implementation** | Four families × eight declared settings × three repeats = **96 scored Dask jobs** at one input profile per family, on one Windows PC. Runtime model, conformal upper bound, rule-based OOD, bounded optimizer and demo are implemented. | **Measured and audited** for this reduced design. Internal scope decisions are in [ADR-001](adr/ADR-001-blite-scope.md), [Phase 1 decision](PHASE1_DECISION.md) and [ADR-005](adr/ADR-005-experiment-host-32gb.md). External approval is not recorded. |
| **Proposed expanded final phase** | New frozen workload profiles and a **separate, independent policy test**, reliable worker-memory/spill telemetry and controlled pressure checks, a fairer baseline/ablation study, then the formatted final report and reproducibility package. | **Proposal only.** Needs team/supervisor agreement, experiment design and new evidence. Do not draw future results on slides. |

Do **not** use `96 / 176` as a completion percentage. Those are different matrices, with different candidate counts and regimes. The extended phase should answer the most important weakness in the current result: the cost comparison used the same physical table from which some model cells were learned.

## 5. Verified progress available for slides

| Completed item | Exact evidence / wording |
| --- | --- |
| Working software | Typed schemas, eight-setting [grid](../configs/dask_grid.json), Dask workloads and collector, JSONL storage, LightGBM artifact, [optimizer](../safe_pipe/optimizer.py), CLI `profile`, `recommend-model`, and `execute`. The full Windows test suite passed **29 tests** on 2026-10-26. |
| Experiment host and bounds | User-selected Windows 11 PC with **31.4 GiB physical RAM**; each Dask worker remained capped at **1 GB or 2 GB**. Four synthetic Parquet input families were about **175–198 MB**. [Hardware ADR](adr/ADR-005-experiment-host-32gb.md), [matrix preparation](../reports/matrix_preparation.md). |
| Frozen physical matrix | **4 families × 8 settings × 3 repeats = 96** unique scored cells, one fresh LocalCluster at a time. Data hashes, SLAs and randomized run order were frozen before scoring. [Plan](../configs/matrix_plan_main_v1.json), [audit](../reports/audit.md), [curated CSV](../data/curated/runs.csv). |
| Outcomes | **96/96 successes, 0 SLA misses, 0 timeouts, 0 OOMs.** Memory warnings on some successful 1 GB sort jobs do not prove spill or failure. Peak worker memory was not reliably captured. [Audit](../reports/audit.md). |
| Runtime model | Grouped split: **36 train**, **36 calibration**, **24 test** rows; all three repeats of each family/setting pair stay together. LightGBM held-out MdAPE **13.84%** versus family-median **23.01%**. One-sided upper bound covered **24/24 test rows** from eight groups, with mean width **1.33 s**. This is a small sample, not a general coverage guarantee. [Model report](../reports/runtime_model.md). |
| First policy comparison | Mean median actual normalized cost across four families: policy **7.524**, declared default **11.421**, conservative **10.366**, uniform random **8.950**. Policy was **34.1% lower than default in the same table**. This is descriptive, **not** an independent improvement estimate. All choices succeeded, so safety differences cannot be measured. [Policy report](../reports/policy.md). |
| Explainability and demo | One LightGBM [feature-contribution figure](../reports/shap_sort_merge.png). The frozen sort profile recommends `w1_t2_1g`; its point/upper estimates are about **3.30/5.57 s** for a **13.1 s** SLA. A separate **30,783-byte tiny live Dask job** succeeded in **2.300 s**; it is not a scored main-v1 run. [Demo notes](../reports/demo.md). |

The four measured operation families are `scan_filter`, `groupby`, `skewed_join` and `sort_merge`. In the current code, `sort_merge` performs a key shuffle and reduction; it **does not merge two tables**. Use the [beginner explainer](../PROJECT_EXPLAINER.html) for simple operation examples, but take slide numbers from the audited files above.

## 6. A feasible expanded final phase (proposal, not accomplished work)

These additions strengthen the research question instead of adding unrelated features. Freeze a separate `main-v2` design and keep its rows apart from the existing `main-v1` 96-row evidence.

| Phase gate | Intended deliverable and acceptance check | Current state |
| --- | --- | --- |
| **A. Problem, architecture and bounded grid** | Approved internal B-lite decision, schemas and eight legal Dask configurations. | Implemented internally; supervisor agreement on changed scope still open. |
| **B. First physical experiment** | Four versioned inputs and all 96 main-v1 cells audited with no leakage from post-run labels. | **Complete.** |
| **C. First model and decision prototype** | Grouped runtime model, upper bound, OOD rules, CLI recommendation and separate demo. | **Implemented for the four measured profiles.** |
| **D. Independent generalization test** | Pre-register new seeds/input sizes and family SLAs, run a new held-out Dask matrix, then evaluate the already fitted policy without using those new cells for fitting. A bounded option is **one new size per family × eight configs × three repeats = 96 additional scored runs**, subject to a pilot and PC/time budget. Record abstentions and all baselines. | **Not started.** The exact size and run count must be frozen before collection; do not show these as completed. |
| **E. Reliability and stronger baselines** | Capture trustworthy worker memory/spill telemetry; run a separate controlled pressure pilot; compare at least one additional defensible baseline or ablation if time permits. Keep failure ML rule-only unless the synopsis's positive-count gate is met. | **Not started.** Failures are not guaranteed, and a native adaptive baseline is conditional on a fair local protocol. |
| **F. Final synthesis** | Data dictionary, reproducibility instructions, department-formatted final report, supervisor review and final demonstration. | Technical report and demo drafts exist; formal package/submission remain open. |

**Halfway framing:** A–C represent the completed first-phase **technical work**; supervisor agreement on A's changed scope remains open. D–F are the remaining evaluation and delivery gates. This is a **milestone narrative**, not six equal units of effort or an official 50% measurement. Say “approximately halfway through the proposed expanded plan” only after the team and supervisor accept D–F as the intended final scope. Until then, say “the first measured prototype is complete, and the next validation phase is proposed.”

**Feasibility boundaries:** a second 96-cell local run campaign is plausible on the same selected PC because the first completed, but its duration, memory behavior and outcome are unknown until piloted. Do not promise near-failures, a trained failure classifier, a probability of SLA success, Glue billing results, or a particular cost saving. The original PDF's Glue adapter, 16-candidate/two-regime design, retry-inclusive cost and automatic fallback remain **unimplemented** unless separately approved and resourced.

## 7. Suggested slide sequence for the PowerPoint agent

| Slide | Main message | Evidence / visual to use |
| --- | --- | --- |
| 1. Title | Submitted title, qualified local-Dask subtitle, group and supervisor. | Identity table in §2. Verify title-slide IDs against synopsis. |
| 2. Problem | Fixed resources can be slow or wasteful; choose before a batch job starts under an SLA. | Simple pipeline illustration. Distinguish normalized local cost from money. |
| 3. Scope decision | Submitted proposal was broad; first prototype focuses on memory-capped single-PC Dask. | Three-version scope table in §4. Label planned work clearly. |
| 4. System flow | Profile → eight candidates → runtime/upper estimate → guards → lowest-cost feasible choice or abstain → optional execution/log. | [Current code](../safe_pipe/cli.py), [optimizer](../safe_pipe/optimizer.py); avoid older architecture's stale “proposed” status labels. |
| 5. Experiment design | Four families, eight configs, three repeats, frozen inputs/SLAs/order. | `4 × 8 × 3 = 96` grid; [preparation report](../reports/matrix_preparation.md). |
| 6. Physical findings | 96/96 success, 0 SLA misses; no measured failure advantage. | [Audit](../reports/audit.md) and curated table. Do not fabricate spill or OOM bars. |
| 7. Model and uncertainty | 13.84% MdAPE vs 23.01% baseline; observed upper coverage 24/24 with small-sample caveat. | [Runtime model report](../reports/runtime_model.md); name test sample size. |
| 8. Recommendation example | Sort: choose `w1_t2_1g`, point 3.30 s, upper 5.57 s, deadline 13.1 s. | [Demo](../reports/demo.md); explain that this is within measured profile. |
| 9. Policy comparison | Same-table normalized costs; 34.1% lower than default is **descriptive only**. | [Policy comparison CSV](../reports/policy_comparison.csv) or [report](../reports/policy.md). |
| 10. Midterm checkpoint | First prototype done; independent validation, telemetry and final report are the proposed next phase. | Gates A–F in §6. Use a clear “done / proposed / conditional” legend, not a false numeric progress meter. |
| 11. Limits and supervisor decision | One PC, one size per family, zero failures, scope mismatch with submitted PDF. Ask for acceptance of the revised final plan. | [Alignment review](MIDTERM_SYNOPSIS_ALIGNMENT.md). |
| 12. Demo / questions | Read-only CLI recommendation; optional separate tiny live job if setup permits. | [Demo commands](../reports/demo.md). Never mix tiny job time with 175–198 MB results. |

The deck may be shorter if the allotted duration is limited; no official slide count or presentation length was provided. Put citations/source labels in speaker notes or slide footers. Use actual figures and tables from this repo; never invent experiment plots or “before/after” savings.

## 8. Safe speaker wording and likely questions

**Opening:** “Our first phase is a measured prototype of SAFE-Pipe on one memory-capped Dask PC. We froze four synthetic workload profiles and tested all eight declared settings three times. The prototype now predicts runtime with an upper bound and recommends a configuration or abstains. The next phase will test it on new profiles and strengthen reliability evidence.”

**Why only 96 when the PDF says 176?** “The original synopsis proposed a broader matrix. A documented feasibility decision reduced the first experiment to four families, eight settings and three repeats. We completed that frozen matrix. We are proposing a separate independent validation phase, not claiming the original 176 cells were run.”

**Have you proved lower cost?** “The selected settings were 34.1% lower than the declared default in a descriptive comparison on the current table. Some cells in that table informed model fitting, so an independent follow-up is needed before a general improvement claim.”

**Where is the ‘failure-aware’ model?** “All 96 jobs succeeded. The synopsis explicitly gates learned failure modelling on at least 30 credible positives, so the current implementation keeps deterministic guards. We cannot claim failure reduction from zero failures.”

**Is this AWS Glue or cloud-cost optimization?** “No. The measured result is single-PC local Dask and a normalized resource score, not AWS billing. Glue would need separate access, budget, implementation and evidence.”

**What about the 40–50% requirement?** “The first measured prototype and its evidence are complete. We propose a second, independent validation and final-delivery phase of comparable importance. We would describe this as around the midpoint of that agreed plan, not as a precise percentage or completion of the original PDF.”

## 9. Handoff rules and files

- Build the PowerPoint from this brief and the [goal-by-goal review](MIDTERM_SYNOPSIS_ALIGNMENT.md). Check every numeric slide against its linked CSV, JSON or report before export.
- Do not copy stale “not started” labels from older [architecture](ARCHITECTURE.md), [micro-plan](MICROPLAN.md) or Mac [session status](SESSION_STATUS.md); those are dated snapshots. [PROGRESS](../PROGRESS.md) and [Ganant Work](../Ganant%20Work.md) record the measured Windows state.
- The branch is `codex/windows-dask`, published on `origin`; `main` has not been merged with it in this handoff. Follow the [Git collaboration guide](GIT_COLLABORATION.md). Generated Parquet, raw JSONL and the ignored PAT file are not in Git.
- If the presentation needs exact student IDs, department template, official midterm rubric, duration, or proof of supervisor approval, obtain those from the user or the submitted PDF. They are not established by the repository.

**Presentation agent deliverable requested by the user:** a clear midterm deck grounded in this brief, with completed work and proposed work visually separate, quantitative caveats visible, and a final slide asking the supervisor to confirm the revised scope.
