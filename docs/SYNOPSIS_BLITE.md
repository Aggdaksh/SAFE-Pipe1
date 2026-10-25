# SAFE-Pipe — Project-I synopsis text (B-lite)

Paste into the DTU IT401 template. Do not paste the old 176-run / Glue paragraphs.

**Title.** SAFE-Pipe: Failure-Aware Cost and Runtime Optimization of Memory-Capped Dask Pipelines under SLA Constraints

**Subtitle.** Implementation on single-PC Dask (Project-I)

## Introduction

Batch dataframe pipelines on Dask change runtime and reliability with input size, partitioning, skew, and worker memory. A default configuration can finish a light scan cheaply and still spill or time out on a skewed join. Exhaustive cloud search is expensive; native adaptive scheduling does not encode a job-specific deadline and a cost objective.

SAFE-Pipe is a pre-run decision system. It takes a workload profile, a deadline, a failure-risk limit, and a **declared** candidate set. It estimates successful runtime with uncertainty, applies safety guards, derives a retry-aware normalized cost, and returns the cheapest configuration that is predicted to meet the SLA — or abstains.

Project-I evaluates this idea on **one personal computer** using Dask workers whose `memory_limit` is set below physical RAM so that spill and timeout can be observed without a cluster or a cloud bill.

## Problem statement

Given a batch pipeline, pre-run features, eight candidate Dask configurations, an SLA deadline, and a risk limit, recommend the configuration with the lowest expected retry-inclusive **normalized** cost that is likely to finish on time. Handle noisy timings, scarce failures, and an unseen workload family by abstaining. Distinguish configuration-actionable failures (OOM, spill, timeout, skew) from code or permission errors.

**Research question.** Does bounded, uncertainty-aware selection reduce normalized cost relative to default, conservative, and random configurations without increasing SLA violations on memory-capped Dask?

**Scope.** Scan/filter, group-by, skewed join, and sort/merge over synthetic Parquet (50–300 MB). AWS Glue, Spark, and multi-node Dask are out of Project-I.

## Motivation

Under-provisioning misses deadlines; over-provisioning wastes cores and memory on a constrained student PC. A useful system must expose when evidence is insufficient. Project-I therefore uses a small configuration space, reproducible synthetic data, and an explicit abstention path. Failure machine learning is evidence-gated: fewer than about 30 credible actionable positives keeps deterministic rules as the valid result.

## Literature (keep short)

Li et al., PVLDB 2023 (constrained Spark tuning); Karthikeyan et al., NSDI 2023 (SelfTune); Freischuetz et al., EuroSys 2025 (TUNA, noisy cloud evaluation); Zhu et al., SIGMOD 2025 (Rockhopper). SAFE-Pipe does not claim to invent these methods. The contribution is a bounded Dask evaluation of constrained selection, conformal uncertainty, and OOD abstention under a student hardware budget.

## Expected goals

1. Prototype with shared schemas (workload, objective, configuration, result), a Dask adapter, a versioned run store, training, ranking, and explainable output (including SHAP for the demo).
2. Validate memory-capped Dask in depth on a **16 GB** PC: **96** main runs (four families × eight configs × three repeats) plus a few smoke jobs. Worker `memory_limit` stays 1–2 GB so spill/timeout remain observable. Glue is an adapter contract only and is **not evaluated**.
3. Train LightGBM (and a simple baseline) on successful log-runtime, add a split-conformal upper interval, and apply a leave-one-family OOD green/yellow/red gate. Timeouts are censored lower bounds, not successful runtimes.
4. Keep deterministic safety rules. Activate exploratory failure ML only if the positive-count gate is met.
5. Compare against Dask default, a conservative fixed config, and random selection on the same run table. Report runtime error, interval coverage, normalized cost, SLA misses, failures, unsafe recommendations, and abstention. Label unsupported improvements inconclusive.
6. Optional comparison: TabPFN trained on Colab/Kaggle on the exported feature CSV. This is a tabular foundation-model baseline, not the deployed policy.
7. Deliver code, data dictionary, curated records, limitations, reproducibility notes, report, and demonstration.

## Explicit non-claims

- Not a Glue cost-optimization study.
- Not a distributed cluster study.
- Not a claim that deep learning outperforms gradient boosting on this table until that comparison is actually run.
