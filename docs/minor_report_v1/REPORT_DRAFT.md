# SAFE-Pipe: Minor B.Tech Project Report

**Working prose draft v1 — 21 November 2026.** This is the first technical writing pass, not a signed or department-formatted submission. The figure book is [index.html](index.html); the reproducible asset inventory is [README.md](README.md). Chapter numbering and the proposed 28–34-page writing budget come from the earlier report blueprint, not a verified university rule.

**Submitted project title:** SAFE-Pipe: Failure-Aware Cost and Runtime Optimization of Distributed Data Pipelines under SLA Constraints.

**Measured-scope subtitle:** A bounded configuration advisor and memory-pressure investigation using single-PC, memory-capped Dask experiments.

The synopsis handoff names Daksh Aggarwal, Chaitanya Singh and Ganant Awasthi, supervised by Dr. Dinesh Kumar Vishwakarma. Confirm names, roll numbers, supervisor designation, department/course wording, submission session and approved title before producing the cover, declaration or certificate. No signatures or approval statements are supplied by this draft.

## Abstract — first draft

Configuration choices affect the runtime and resource allocation of batch data-processing jobs. SAFE-Pipe implements a bounded advisor that compares eight local Dask configurations using workload metadata, a fitted runtime predictor, a calibrated upper runtime estimate and explicit support checks. The original study measured four fixed synthetic workload profiles across eight configurations with three repetitions, producing 96 successful runs on one Windows PC. A grouped held-out evaluation reported median absolute percentage error of 13.84%, compared with 23.01% for a family-median baseline, on 24 test rows belonging to eight family/configuration groups. A historical resource-cost comparison reused the original table and is therefore descriptive rather than independent evidence of savings. Subsequent research examined whether small execution probes preserve memory-pressure information from full jobs. Stage A recorded 41 successful full attempts and seven execution errors. In a separate experiment, all 96 small-sample runs completed without a recorded memory-pressure warning. In eight of 32 paired comparisons, the full workload showed memory pressure that the sample did not reveal. A one-probe development replay added profiling cost without changing the stronger metadata-based choices. Probe admission consequently remains disabled. Fresh prospective validation remains pending. The contribution is an auditable, scope-limited advisor and an evidence-based investigation of profiling limits, not a universal safety guarantee or a validated failure classifier.

## 1. Introduction

### 1.1 Motivation

A data-processing job can perform the same logical operation under different resource settings. For example, a group-by may run with one worker or two workers, with different thread counts and memory caps. Increasing resources may shorten execution, but it may also increase configured resource-time. Reducing memory can expose pressure, spill or worker restarts. The useful configuration therefore depends on the workload, the deadline and the resource preference.

SAFE-Pipe addresses this configuration decision before execution. Its measured implementation uses Dask `LocalCluster` on one Windows computer. It compares a small declared grid rather than searching every possible setting. This limited scope makes the evidence and decision rules inspectable.

### 1.2 Objectives and contribution

The implemented objectives are to collect a reproducible local benchmark table; predict successful engine runtime from pre-run features; add a cautious upper estimate; compare supported configurations under a deadline; explain eligibility and selection; and retain auditable software and experimental records. A later research objective investigated the additional information and cost of execution-based probes.

The original project title describes a broader failure-aware vision. The implemented evidence is narrower: all original 96 runs succeeded, so those records do not support learning a failure classifier. Later research contains pressure and termination observations, but has not established a calibrated failure model or a beneficial deployed probing policy.

**Use F01 for the system boundary and F17 for the current checkpoint.**

## 2. Background and related work — technical background drafted

A **task** is a schedulable piece of work, such as processing one partition. A **task graph** describes dependencies among pieces of work. In this report, a **job** is the complete requested workload execution, which can contain many tasks. A **worker** is a Dask process that executes tasks, and each worker can use one or more threads. A **partition** is a portion of the dataset processed as part of the graph. A configured memory cap applies per worker; it does not mean that the entire computer has that amount of RAM.

Metadata profiling inspects descriptors such as input size, estimated rows, number of files and partition count. Execution profiling runs a smaller computation and observes its behaviour. Execution profiling can expose information that metadata misses, but sample preparation, cluster startup, execution and cleanup introduce costs. A probe can also alter the very pressure mechanism it is supposed to represent.

Key skew and partition imbalance are different. Key skew means that some key values occur much more frequently than others. Partition imbalance means that input partitions have different sizes. Both can affect distributed processing, but they should not be treated as interchangeable causes. F11 explains the distinction with an explicitly schematic cartoon.

**Related-work writing remains incomplete.** The final chapter needs a checked comparison of primary sources on configuration/runtime prediction, uncertainty-aware decisions and profiling. Existing repository documents provide source leads, but this draft does not invent citations, novelty claims or experimental comparisons. The seniors’ reports guide document structure; their medical models and figures are not technical evidence for SAFE-Pipe.

## 3. Problem formulation and objectives

### 3.1 Inputs, candidates and output

The advisor receives a supported workload descriptor, an engine deadline and optional preferences or budgets. The original grid contains one or two workers, one or two threads per worker, and a per-worker memory cap of 1 GB or 2 GB. These three binary choices yield eight configurations, shown in F02. The output is an explained recommendation or abstention, with all candidate estimates and rejection reasons.

The model feature whitelist is: family, input bytes, estimated rows, file count, partition count, skew score, configuration ID, workers, threads per worker, memory-limit feature, allocated-vCPU feature and allocated-memory feature. Actual runtime, status, failure category, SLA miss and peak memory are outcome labels, not prediction inputs. The SLA is a policy constraint, rather than a LightGBM runtime feature.

### 3.2 Current balanced objective

For candidate `c`, let `t(c)` be predicted engine seconds, `U(c)` the frozen upper estimate, `D` the requested engine deadline, `P(c)` the total configured threads and `M(c)` the total configured worker memory in bytes. The current `advise` objective is:

```text
Q(c) = lambda * P(c)/4 + (1 - lambda) * M(c)/4,000,000,000
R(c) = [t(c)/D] * Q(c)
J(c) = beta * [t(c)/D] + (1 - beta) * R(c)
```

The default `lambda` is 0.5. `beta` is 0.5 for balanced mode, zero for resource mode and one for fastest mode. These are declared preferences, not trained coefficients or a proven universally optimal formula. The score is dimensionless and uses configured resource proxies. It does not measure cloud prices, electricity, CPU utilization or peak RAM.

Candidates must pass exact frozen-profile and artifact/grid support checks, the upper-runtime deadline check, optional thread/memory budgets and a coarse input-memory rule. The effective deadline is `D * (1 - deadline_reserve)`. If no candidate is eligible, the advisor abstains. The coarse memory rule and descriptor support do not guarantee execution safety or independently verify the calling machine and actual input contents.

The original model features retain their historical unit contract. The newer score distinguishes decimal GB from binary GiB. Do not silently change fitted feature values to make the unit labels look more convenient; refer to `docs/DATA_DICTIONARY.md`.

## 4. System architecture and design

The original offline path consists of frozen synthetic datasets, randomized collection, append-only raw records, an audited curated table, grouped training/calibration/test splits, a fitted LightGBM artifact and artifact support bindings. The online advice path checks the declared profile, predicts candidates, applies constraints and ranks eligible choices. Advice is inference-only and does not launch a Dask job.

The research path is separate. It investigates pressure mechanisms, sample fidelity and total profiling cost. Reading its compact evidence for this report does not merge the research implementation into the original advisor. The research prototype’s probe admission gate remains disabled (F16).

The completion branch adds prospective-study infrastructure: immutable study identity, pre-run saved advice, attempt journaling and a fresh-results evaluator. Its Windows software suite passed. The study has not been prepared or collected. Exact-dataset recommendation-to-execution binding and the small local interface are subsequent delivery milestones, not completed product features.

**Use F01 as the main architecture figure. Keep F16 in the research subsection or appendix.**

## 5. Experimental methodology

### 5.1 Original environment and data

The selected Windows PC has 33,711,480,832 physical RAM bytes (approximately 31.4 GiB), with the experiment environment reporting 16 logical CPUs and Python 3.14.6. Per-worker caps remain 1 GB or 2 GB despite the larger host. The package versions and Windows platform are retained in the verification receipt. Results target this local host and do not establish multi-node or cross-hardware behaviour.

The four fixed original datasets represent scan/filter, group-by, skewed join and the repository’s `sort_merge` workload. The latter uses a key-based shuffle/index operation with a scalar partition result; it should not be described as a measured second-table merge-sort implementation. Compressed Parquet sizes range from about 174.6 to 198.5 decimal MB (F03). Those disk sizes are not decompressed RAM requirements. Three repetitions use the same fixed profile data, not newly generated workload instances.

The original matrix contains four profiles, eight configurations and three repetitions, for 96 scored physical runs. The deadlines were frozen from separate pilot work: 2.6 s for scan/filter, 7.9 s for group-by, 4.3 s for skewed join and 13.1 s for `sort_merge`. The randomized order and input identities were recorded before scored collection. Pilots are outside the 96 scored rows.

### 5.2 Fitting, calibration and held-out evaluation

The grouped split keeps all repetitions of a family/configuration pair together. It has 12 training groups (36 rows), 12 calibration groups (36 rows) and eight test groups (24 rows), as shown in F05. It prevents repetitions of the same cell from crossing splits, but the four workload profiles remain represented across splits. It is not a test on unseen workload families or sizes.

LightGBM predicts log successful engine runtime using 120 trees, seven leaves, learning rate 0.05, minimum child count three and L2 penalty one. Calibration uses the maximum log residual over each group’s repetitions. The nominal 90% finite-sample rank over 12 calibration groups selects the largest calibration score. The stored upper log offset is 0.523642, giving `U = t * exp(0.523642)`, approximately `1.688 * t`.

The artifact preserves held-out predictions and metrics, but no saved epoch-by-epoch training history or training-accuracy metric. No model was retrained to build this report. F06–F08 use the saved test predictions.

### 5.3 Later research studies

Stage A separated key skew and partition imbalance in group-by and skewed join. The four patterns per family produced eight instances, each examined at two memory caps with three full repetitions: 48 full attempts. Stage B reused those instances with two probe fractions (0.125 and 0.25), two target configurations and three repetitions: 96 probes. Effective sample caps and target full-job caps must be distinguished when interpreting the research plans.

These are development studies with one generation seed and shared samples. They are not independent reliability estimates or a new training set for the original LightGBM artifact. Three timing repetitions do not replace independent workload generation.

### 5.4 Timing and resource contracts

The original predictor targets engine runtime. Research lifecycle and constructed request totals include additional phases. Input preparation, preflight, startup, execution, cleanup and unmeasured controller/metadata overhead must remain distinguishable. Do not add separately reported component medians and present the result as the median complete request. Configured thread-time and cap-time are allocation proxies, not actual consumption or currency.

The previously discussed approximately 6.78 GiB referred to prepared Parquet/sample storage across two screen directories. It was not the size of one original training dataset or the saved LightGBM model.

## 6. Implementation and verification

The feature whitelist is in `safe_pipe/features.py`; runtime loading and prediction are under `safe_pipe/models/`; configuration eligibility, scoring and explanation are implemented in `safe_pipe/advisor.py`; the CLI exposes advice separately from execution. Configuration definitions, profiles and artifact bindings make the supported scope explicit. Collection and audit modules retain measured outcomes separately from pre-run features.

Four current inference-only examples are preserved in `advisor_capture/`: balanced, resource, fastest and abstention under a tight deadline. F10 shows the balanced candidate comparison. The `advisor_demo.html` page is a viewer for those saved outputs, not a screenshot of a finished product interface. The full JSON exposes the decision rather than only a winning label.

The latest original-advisor implementation, `d6f906a`, passed the full Windows software verifier: **143 passed, zero failed, zero errors and zero skipped in 36.89 seconds**. `pip check` passed in the existing original `.venv`, with no dependency upgrades or implementation fixes. The report is committed in `caa8a8a`. These checks include tiny Dask integration fixtures and do not run the fresh 96-cell study.

On the separate research branch, 38 targeted synthetic tests passed, with eight default decisions, 24 single-observation counterfactual decisions and 37 termination-memory records checked. The two suites have different scopes and must not be combined into one undifferentiated test count (F17).

## 7. Results and discussion

### 7.1 Original runtime results

All 96 original scored jobs succeeded, with zero recorded SLA misses. F04 shows medians and observed minimum–maximum ranges over three repetitions for each family/configuration pair. These ranges are not confidence intervals. Original reliable peak-memory and spill labels were absent; later research telemetry does not fill those historical gaps.

On the 24 saved held-out rows, the LightGBM model has **13.84% MdAPE**, compared with **23.01%** for the family-median baseline. MdAPE is the median of absolute prediction error divided by actual runtime, multiplied by 100. It is not classification accuracy, and `100 - MdAPE` is not a valid accuracy claim.

The stored upper estimates covered 24/24 test rows and 8/8 test groups, with mean point-to-upper width about 1.33 s. This observed coverage is a small-split result, not a universal 100% coverage claim or a calibrated selected-job success guarantee.

### 7.2 Historical descriptive cost comparison

The older `recommend-model` policy selected `w1_t2_1g` for all four original profiles. The mean median normalized cost was 7.524, compared with 11.421 for the declared in-grid reference `w1_t1_2g`, 10.366 for the conservative setting and 8.950 for uniform random selection (F09). The 34.1% lower cost relative to the reference reuses the same physical table that supplied some model training cells. It is descriptive, not independent savings or cloud billing reduction. It also uses an older objective and is not the measured performance of the newer balanced `advise` score.

### 7.3 Earlier probe-ranking screen

The earlier development screen retained 768 attempts across twelve recipes, with 759 successes, one timeout and eight execution errors. On the ten complete eligible instances, median selected-full engine regret was 3.87% for uniform sampling, 0.11% for memory-mapped uniform and 8.17% for partition-tail sampling (F18). These are retrospective engine-only selection comparisons, not prediction accuracies or complete-request savings. The screen used one generation seed and two runtime repetitions; failures remain in the study record even when a timing metric requires complete successful comparisons.

### 7.4 Stage A and Stage B findings

Stage A recorded **41 successful attempts and seven execution errors out of 48**. The seven errors have nanny memory-termination evidence. Successful jobs may also show spill or worker restarts; success must not be equated with a quiet memory history. F12 keeps statuses explicit.

Stage B recorded **96 quiet successful probes**. However, eight of 32 paired comparison groups showed full-input pressure without a corresponding probe warning (F13). These cells are four low-cap instance cases at two fractions. They do not establish a calibrated 25% false-negative rate, and quietness on the smaller sample does not certify full-job safety.

### 7.5 One-probe cost and the disabled gate

The existing one-probe development replay found that stronger metadata and probe heuristics chose the same configurations for the eight instances. Their selected historical full outcomes were all successful (24/24 unique selected references), but the probing variants added cost. The median constructed request total was **4.79 s** for size-aware metadata, **10.37 s** for always-one-probe and **7.38 s** for ambiguous-only probing (F14).

These totals are constructed from historical references in different sessions, not newly executed online policy requests. The 4.79 s is not metadata-read time. Metadata/controller overhead and sample-preparation resource exposure remain unmeasured. Probe admission stays disabled because incremental information and single-request economic benefit were not demonstrated for this use case. A negative finding is useful evidence; it should not be hidden by changing the objective or opening the gate.

### 7.6 Worker-memory evidence

The existing export preserves 321 worker lifetimes across 144 Stage A/B runs, including lifetimes added after worker restarts. Among 37 lifetimes with termination evidence, 33 retained sampled RSS peaks were below the recorded termination threshold and 36 event readings exceeded the retained peak (F15). Brief peaks can occur between retained samples or before abrupt death.

These are distinct observations: retained sampled RSS, termination-event RSS, managed memory, spill and configured cap. None should be substituted silently for another. Thirty-seven terminated lifetimes are not 37 failed jobs. Asynchronous worker peaks must not be summed as if measured simultaneously. Missing values remain missing, rather than being changed to zero. These limitations prevent treating retained peaks as exact memory-demand training targets.

### 7.7 Threats to validity

The original model is supported by only four fixed profiles, and its test contains eight family/configuration groups. Research uses one generation seed and shared samples. Runtime repetitions are not independent new workloads. Some costs are historical replays, not online executions; resource terms are configured proxies. Worker death and snapshot timing can censor telemetry. No cross-machine generalization, AWS Glue evaluation, multi-node experiment, calibrated failure classifier or publishable novel selector is established by these records.

## 8. Conclusion and future work

SAFE-Pipe demonstrates a reproducible, bounded configuration-advice workflow with an explicit predictor, upper runtime estimates, support checks, preference-based selection and abstention. The original dataset supports a small held-out runtime result and descriptive configuration comparisons. Later research shows why small execution probes can lose pressure information and cost more than they add on short jobs. The current evidence supports keeping the probe gate closed.

The immediate experimental next step is user review of the published Windows verification checkpoint. Fresh prospective study preparation and collection have not started. Any subsequent collection should preserve pre-run advice, frozen identities, failed/aborted attempts and independent evaluation. It should report unfavorable as well as favorable outcomes. Exact-dataset advice/execution integration, a local interface and final delivery documents remain subsequent tasks. Broader-profile support needs a separate versioned data/model design and untouched evaluation.

For report production, the next writing pass should complete the checked related-work chapter, select the main-text figures, confirm the academic template and identities, and prepare genuine front-matter forms. Fresh measurements, if later authorized and completed, belong to a new evidence version. They must not overwrite the original results or be implied by a passing software test suite.

## Evidence and reference worklist

This draft uses repository evidence, not a completed academic bibliography. Every figure caption names its source; `source_manifest.json` pins source revisions and LF-normalized hashes. The exact original runtime results are in `artifacts/main_v1/runtime_metrics.json` and `runtime_test_predictions.csv`; physical outcomes are in `data/curated/runs.csv`; advisor contracts are in `docs/CONFIG_SELECTION.md`. Research results are read from pinned revision `edef1cd` without merging its implementation.

Before final submission, complete numbered in-text citations and verified reference entries for the actual primary papers and official implementation documentation used. Do not import an unverified bibliography from the seniors’ unrelated projects.
