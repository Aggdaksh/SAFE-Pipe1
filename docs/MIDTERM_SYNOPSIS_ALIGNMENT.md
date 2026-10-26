# SAFE-Pipe midterm status against the submitted synopsis

**Prepared:** 2026-10-26
**Purpose:** Evidence-backed progress and gap analysis for the DTU IT401 Project-I midterm evaluation. This is a team briefing, not a claim that a supervisor has approved a revised synopsis or that a department submission has occurred.

## 1. Documents and interpretation

- **Submitted baseline:** the user-supplied, three-page `SAFE-Pipe_Project_Synopsis_DTU-1.pdf` (pages 1–3). It is outside this Git repository. Its MD5 matches the synopsis previously assessed in [Phase 0 feasibility](PHASE0_FEASIBILITY.md). The PDF's text is a proposal; it is not evidence that every proposed feature has been implemented.
- **Internal scope decision:** [ADR-001](adr/ADR-001-blite-scope.md), [ADR-002](adr/ADR-002-primary-backend-dask.md), and the [Phase 1 decision](PHASE1_DECISION.md) selected a feasible **B-lite** Project-I study: one local Dask PC, four families, eight candidates and 96 scored runs. [ADR-005](adr/ADR-005-experiment-host-32gb.md) records the user-selected Windows experiment host. These are repository decisions; **supervisor/department acceptance of the reduced scope is not documented here**.
- **Current evidence:** [run audit](../reports/audit.md), [curated 96-row CSV](../data/curated/runs.csv), [runtime-model report](../reports/runtime_model.md), [policy report](../reports/policy.md), [technical results draft](../reports/project_i_results.md), [demo record](../reports/demo.md), and [Ganant PC log](../Ganant%20Work.md). The full local test suite passed **29 tests** on 2026-10-26.
- **Midterm rubric:** no official midterm scoring or required slide/report format was supplied. The statuses below are technical assessments, not an official percentage or a prediction of marks.

**How to read this review:** “Done” means implemented and backed by a linked artifact; “Partial” means some of the synopsis commitment is supported; “Changed scope” means the internal B-lite plan deliberately removed or reduced a submitted commitment; “Evidence-gated” means the synopsis itself says the feature should wait for enough observations; “Open” means no completed evidence was found.

## 2. Honest progress statement

SAFE-Pipe has a working, measured **local Dask prototype**. The team built the common schemas and optimizer, generated four synthetic Parquet workload families, executed **4 families × 8 settings × 3 repeats = 96** physical Dask jobs on one 31.4 GiB RAM Windows PC, audited the data, fitted a grouped LightGBM runtime model with a calibrated upper bound, and demonstrated a recommendation and a separate tiny live execution. All 96 scored jobs succeeded and met their frozen family SLAs.

This is substantial progress for the **reduced B-lite experiment**: its core data collection and first end-to-end recommendation path are complete. It is **not** completion of the broader submitted synopsis. The PDF proposes **176 Dask jobs**, **16 main-matrix candidates**, two regimes, near-failure and confirmation runs, a Glue adapter contract, retry-aware cost and SLA probability, a native adaptive baseline, and final deliverables that are absent or incomplete. Dividing 96 by 176 would misrepresent progress because the experimental design changed, not merely the number of jobs remaining.

For a midterm described informally as “half the progress,” present the completed **foundation + measured prototype** as the first major phase, and the **scope reconciliation + stronger evaluation + final reporting** as the remaining phase. Do not say the overall project is exactly 50% complete without a rubric or agreed scope.

| Workstream | Midterm position |
| --- | --- |
| Problem definition and B-lite architecture | Documented internally; reduced scope still needs supervisor agreement. |
| Local Dask execution and reduced physical matrix | **Complete:** 96/96 planned B-lite cells measured and audited. |
| First runtime model and recommendation path | **Implemented:** grouped test metrics, upper bound, CLI, OOD rules and demo exist. |
| Independent policy and failure validation | **Not established:** same-table cost comparison only; zero observed failures. |
| Original PDF extras and formal deliverables | **Open or removed by internal scope decision:** see the six-goal crosswalk below. |

## 3. Crosswalk to the six expected goals in the submitted PDF

### Goal 1 (PDF p. 3): working prototype and request-to-result flow

| Synopsis component | Current status | Evidence and precise limit |
| --- | --- | --- |
| Typed workload, objective, configuration and result schemas; bounded candidates | **Done** | [schemas](../safe_pipe/schemas.py), frozen [eight-setting grid](../configs/dask_grid.json), and tests. |
| Pre-run profiling | **Partial** | `profile` reads a **frozen dataset manifest**, and `recommend-model` accepts a declared `WorkloadSpec`; there is no demonstrated general profiler that inspects an arbitrary new dataset. See [CLI](../safe_pipe/cli.py). |
| Dask and AWS Glue adapters | **Dask done; Glue changed scope** | [LocalCluster adapter](../safe_pipe/adapters/dask_local.py) and [Dask workloads](../safe_pipe/workloads/execute_dask.py) are exercised. No Glue adapter or Glue contract test is evidenced. The B-lite decision excludes Glue evaluation. |
| Versioned run store and execution monitoring | **Partial** | Append-only JSONL collection, `data_version`, status and runtime are implemented; the [audit](../reports/audit.md) exports shareable CSV. Reliable peak worker memory and spill telemetry were **not** captured. |
| Runtime model, ranking and explanation | **Done for four measured profiles** | [runtime report](../reports/runtime_model.md), [optimizer](../safe_pipe/optimizer.py), fitted [CLI](../safe_pipe/cli.py), and one [feature-contribution explanation](../reports/shap.md). Explanations are model attributions, not causal effects. |
| Abstention plus declared conservative fallback | **Partial** | The optimizer returns `abstain` when no candidate passes. A conservative configuration exists for comparison, but the decision path does **not** automatically run or return a declared fallback after abstention. |

### Goal 2 (PDF p. 3): primary-backend evaluation and reproducible data

| Synopsis commitment | Current status | Evidence and precise limit |
| --- | --- | --- |
| One primary backend evaluated in depth | **Done for reduced Dask scope** | One Windows PC ran [96 audited Dask jobs](../reports/audit.md), one fresh LocalCluster per job. Worker limits remained 1–2 GB despite 31.4 GiB host RAM. |
| PDF's Dask design: 176 total; 128 main cells across 4 families × 2 regimes × 16 candidates; plus smoke, near-failure and confirmation runs | **Changed scope** | B-lite froze [4 × 8 × 3 = 96 scored cells](../configs/matrix_plan_main_v1.json), with one approximately 175–198 MB profile per family. T0/T0b and SLA pilots were separate. There was no second size regime, 16-candidate matrix, 24 near-failure set, or 16 confirmation set. Do not present 96 as 96 of the PDF's 176 planned cells. |
| Reproducible workload, configuration and outcome data | **Done within the measured scope** | Versioned [dataset hashes/seeds](../configs/datasets_main_v1.json), [family SLAs](../configs/family_sla_main_v1.json), [randomized order](../configs/matrix_plan_main_v1.json), [audit](../data/curated/audit.json), and [curated CSV](../data/curated/runs.csv) are committed. Large generated Parquet and raw JSONL remain local/ignored. |
| Other backend receives contract tests; cross-backend claims only after both are measured | **Open / changed scope** | No Glue contract-test result or Glue measurements. **No cross-backend claim is supportable.** |

### Goal 3 (PDF p. 3): successful-runtime prediction, uncertainty and OOD

| Synopsis component | Current status | Evidence and precise limit |
| --- | --- | --- |
| Gradient-boosted model and simple runtime baseline | **Done** | LightGBM plus family-median baseline on a frozen grouped split: 36 train rows, 36 calibration rows and 24 test rows, keeping all three repeats of each family/setting pair together. Held-out MdAPE: **13.84%** versus **23.01%**. [Model report](../reports/runtime_model.md). |
| Split-conformal upper bound | **Done with limited evidence** | Observed upper coverage was **24/24 test rows** (8/8 groups), mean point-to-upper width **1.33 s**. Only eight test groups and four workload profiles were available; 100% observed coverage is **not** a universal guarantee. |
| OOD green/yellow/red gate | **Partial** | Implemented [family/size rules](../safe_pipe/models/ood.py); withholding each family from the gate yielded red **4/4** times. Thresholds are heuristic, with only one measured input size per family; no calibrated new-workload transfer result. |
| Timeout observations treated as censored rather than successful runtime | **Implemented policy, unexercised by scored data** | The [collector](../safe_pipe/collector.py) labels timeout separately and runtime training uses successful rows. The 96 scored jobs contained **zero timeouts**, so censoring behavior has no physical example in this table. |

### Goal 4 (PDF p. 3): evidence-gated failure modelling

The PDF says **fewer than 30 credible actionable failures means rules only**. The audited table has **zero** timeouts, OOMs or other scored failures. Keeping [deterministic guards](../safe_pipe/policy.py) and **not training a failure classifier is compliant with that gate**, not a missing model to invent for midterm. The output field `p_fail` is a **0/1 rule flag**, not a calibrated probability. An optional two-model runtime ensemble was not run. Some successful 1 GB sort jobs logged memory pressure, but there is no reliable spill or peak-memory record to relabel them as failures.

### Goal 5 (PDF p. 3): least-cost safe policy and baselines

| Synopsis component | Current status | Evidence and precise limit |
| --- | --- | --- |
| Enumerate supported candidates and return lowest-cost feasible choice | **Done for eight local Dask choices** | [Policy code](../safe_pipe/policy.py) estimates all eight; [optimizer](../safe_pipe/optimizer.py) checks upper runtime ≤ SLA, red OOD and a deterministic guard, then selects lowest expected normalized cost or abstains. |
| Retry-aware expected cost and SLA probability | **Open relative to PDF** | Current cost is **point runtime × (allocated vCPUs + allocated GB)**, a normalized local resource measure, not USD or retry-inclusive cost. SLA feasibility uses a calibrated **upper bound**, not an explicit probability of meeting the SLA. No calibrated failure probability exists. |
| Compare default, native adaptive, conservative and random | **Partial** | [Same-table comparison](../reports/policy.md) covers declared default, conservative and uniform random; **native adaptive/autoscaling was not evaluated**. Policy mean median cost was **7.524** versus **11.421** for default, a **34.1% descriptive same-table difference**. This is **not** an independent policy improvement estimate because some comparison cells informed model fitting. |
| Report failures, SLA misses, unsafe recommendations, confidence intervals | **Partial / uninformative where no events occurred** | The [audit](../reports/audit.md) reports 96 successes, **0 SLA misses**, **0 timeouts**, **0 OOMs**. With no observed failures or misses, no failure-reduction or safety advantage can be measured. The model has a conformal upper bound; uncertainty intervals for the policy-cost difference and a separate held-out policy comparison are not provided. |

### Goal 6 (PDF p. 3): deliverables

| Deliverable | Current status | Evidence and next step |
| --- | --- | --- |
| Source, configs, curated records, limitations, reproduction notes | **Mostly done** | Code and versioned artifacts are on `origin/codex/windows-dask`; see [README](../README.md), [audit](../reports/audit.md), and [technical results draft](../reports/project_i_results.md). The [data README](../data/README.md) is a short storage note, **not a full field-by-field data dictionary**. |
| Baseline and ablation results | **Partial** | Runtime family-median and policy default/conservative/random baselines exist. A formal ablation study is not documented. |
| Final report and demonstration | **Draft + verified demo, formal submission open** | [Technical report](../reports/project_i_results.md) is explicitly a draft; [demo instructions](../reports/demo.md) include a separate **tiny 30,783-byte** live run. The live sample is not one of the 96 scored jobs. Department formatting, supervisor review and formal submission are not verified. |
| Manuscript | **Conditional, not a midterm requirement** | The synopsis says to prepare one only if evidence is strong; no publication or manuscript claim is made. |

## 4. What the team can safely demonstrate at midterm

1. **Problem and honest scope.** Show the submitted PDF's problem statement, then explain that the internal feasibility review selected memory-capped **single-PC Dask** as the primary evidence. The submitted 176-run/Glue breadth and the B-lite reduction must be acknowledged openly.
2. **Working system.** Show the [grid](../configs/dask_grid.json), [architecture](ARCHITECTURE.md) as a design snapshot, and the current [CLI](../safe_pipe/cli.py). Say that older architecture/task text contains pre-experiment statuses; use this document and [PROGRESS](../PROGRESS.md) for current status.
3. **Physical evidence.** Show [matrix preparation](../reports/matrix_preparation.md), the [audit](../reports/audit.md), and a few rows of the [curated CSV](../data/curated/runs.csv). Explain 4 × 8 × 3 = 96, fresh cluster per cell, frozen data/SLA/order, and zero failures.
4. **Model evidence.** Show the [grouped split](../configs/model_split_main_v1.json) and [runtime metrics](../reports/runtime_model.md). State the sample size next to MdAPE and observed upper coverage.
5. **Decision and limitations.** Run the read-only prediction command below. Show the eight candidates, selected setting or abstention, and the [same-table policy comparison](../reports/policy.md). If running the separate tiny Dask demo, follow [demo.md](../reports/demo.md) and do not present its runtime as a main-v1 measurement.
6. **Next phase.** Ask for supervisor agreement on the revised Project-I scope, then explain the plan for independent policy validation, better telemetry, a data dictionary, and final report/submission. If the original PDF's extra goals remain mandatory, budget and schedule them explicitly instead of treating them as already delivered.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m safe_pipe.cli profile --family sort_merge
.\.venv\Scripts\python.exe -m safe_pipe.cli recommend-model --family sort_merge --sla 13.1
```

The fitted sort example recommends `w1_t2_1g` with about **3.30 s** point runtime and **5.57 s** upper runtime under the **13.1 s** SLA. The three scored runtimes for that family/setting were **5.083, 5.566 and 5.342 s**; this illustration uses the same measured table from which some model cells were fitted or calibrated. Do not call it a fresh independent prediction test.

### Suggested concise response to “Why does the synopsis say 176 runs and Glue?”

> The submitted synopsis described a broader design. Our documented feasibility decision reduced Project-I to one measurable backend: local, memory-capped Dask. We completed its frozen 96-run matrix and a first runtime-aware recommendation prototype. We have not measured Glue or the original 176-run design. We are presenting the actual evidence and seeking agreement that this revised scope is appropriate for the remaining project work.

## 5. Remaining work, ordered by decision

### Before or at the midterm

1. **Resolve scope with the supervisor.** Present both the submitted PDF and the [B-lite synopsis draft](SYNOPSIS_BLITE.md). Confirm whether the revised title/scope and omission of Glue, the 176-run layout and native adaptive baseline are accepted. The B-lite draft itself still uses phrases such as “retry-aware cost” and “Glue adapter contract” that exceed the current implementation; revise those claims before any formal submission.
2. **Prepare the evidence packet.** Use the committed audit, split, metrics, policy table, figure and demo. Keep the limitation statements next to each number. Do not rerun the 96 physical jobs for a presentation.
3. **Rehearse the live path.** Use `profile` and `recommend-model`; run the separate tiny `execute` example only if desired. Keep the scored experiment and tiny demo clearly separate.

### For the rest of the approved B-lite project

1. **Independent evaluation:** collect additional workload sizes/profiles and hold out an entire policy-evaluation set before claiming general cost improvement. The current 34.1% same-table result is descriptive.
2. **Telemetry and safety evidence:** capture reliable worker memory/spill measurements. Actual actionable failures would be needed to evaluate failure prediction or any claimed reduction; follow the synopsis's 30/50-positive gates if such data ever exist.
3. **Documentation and submission:** write a field-by-field data dictionary, close any chosen baseline/ablation gaps, format the final DTU report, get supervisor review and document the formal submission.
4. **Optional research comparison:** TabPFN was proposed but not run. Do it only if it fits the approved scope and helps interpretation.

### Only if the supervisor requires the original PDF scope

The current repository does **not** satisfy these submitted commitments: a Glue adapter and contract tests, the 16-candidate/two-regime/near-failure/confirmation Dask design, a native adaptive baseline, retry-inclusive cost, explicit SLA probability, and an automatic conservative fallback. These require a new agreed plan, resources and evidence. Never describe them as completed or promise that the existing 96 rows test them.

## 6. Claims to keep precise

| Safe phrasing | Avoid saying |
| --- | --- |
| “We evaluated eight memory-capped Dask settings on one Windows PC.” | “We evaluated a distributed cluster or AWS Glue.” |
| “All 96 scored jobs succeeded and met the frozen SLAs.” | “We reduced failure rates” or “we observed spill/OOM.” |
| “Test MdAPE was 13.84% on 24 held-out rows from eight groups; observed upper coverage was 24/24.” | “The model is 100% reliable on future workloads.” |
| “The selected settings had 34.1% lower normalized cost than default in the same measured table.” | “We proved a 34.1% independent or production cost saving.” |
| “The optimizer abstains on red OOD or no feasible setting.” | “It uses calibrated failure probabilities, retry-aware cost, or an automatic fallback.” |
| “The `sort_merge` code shuffles by key and reduces partition values.” | “That workload merges two tables.” |

**Assessment for the team:** the reduced physical experiment and prototype are real and demonstrable. The midterm's main risk is a **scope mismatch between the submitted PDF and the implemented B-lite study**, followed by limited independent validation. The evaluation should show both the progress and that gap plainly.
