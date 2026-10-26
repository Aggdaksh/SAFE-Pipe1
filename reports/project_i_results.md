# SAFE-Pipe Project-I results (technical draft)

**Date:** 2026-10-26  
**Status:** Reproducible technical results draft, not a department-formatted final submission. Every number below comes from committed configuration/metric files or the audited physical run table.

## Research question and scope

SAFE-Pipe asks whether pre-run selection from a small declared set of Dask configurations can reduce a normalized resource cost under a deadline while exposing uncertainty and abstaining outside measured scope. Project-I evaluates four synthetic Parquet workload families on one Windows PC. It does not evaluate AWS Glue, Spark, a multi-node cluster, or cloud billing.

The selected host has 31.4 GiB physical RAM, but each Dask worker was capped at **1 GB or 2 GB**. The eight configurations are one or two workers × one or two threads per worker × the two memory limits. Extra host RAM was headroom for Windows and the scheduler; it did not expand the candidate set. The four generated datasets were 175–198 MB of Parquet. Exact seeds, bytes, and SHA-256 values are in [`datasets_main_v1.json`](../configs/datasets_main_v1.json).

## Method

T0 verified a one-worker `LocalCluster`. Pilots compared 1 GB and 2 GB worker caps, then three 2 GB pilot repeats per family fixed an SLA at **1.5 × median pilot runtime** before scored collection. The four deadlines were 2.6 s (scan/filter), 7.9 s (group-by), 4.3 s (skewed join), and 13.1 s (sort/merge). The physical matrix order was randomized with seed 2026 and committed before collection. A new cluster ran each cell, one job at a time. The matrix has four families × eight configurations × three repeats = **96 jobs**. Pilot rows were kept outside the scored JSONL.

The collector recorded workload metadata, native Dask configuration, status, actual engine runtime, SLA, and data version. The audit checked every row against the frozen order, configuration, dataset manifest, and SLA. The flat table and its hashes are in [`data/curated/`](../data/curated/) and [`reports/audit.md`](audit.md). Prediction features were restricted to values available before the run; actual runtime, status, and memory were excluded.

## Physical outcomes

| Check | Result |
| --- | ---: |
| Planned and unique physical cells | 96 / 96 |
| Successful jobs | 96 / 96 |
| SLA misses | 0 / 96 |
| Timeouts or OOMs | 0 / 96 |

During some 1 GB sort runs, Dask logged high unmanaged memory and worker pauses around 776 MiB process memory. Those jobs completed successfully. No reliable peak-memory telemetry or spill measurement was stored, so the report does not label them as spill or failure. The 1 GB worker cap changed some pilot sort timings, but this matrix cannot quantify failure-risk reduction.

## Runtime model and uncertainty

The grouped split kept all three repeats of a family/configuration cell together: 12 training cells (36 rows), 12 calibration cells (36 rows), and 8 test cells (24 rows). LightGBM predicted log successful runtime. The one-sided conformal upper bound used the largest residual among each calibration cell's repeats and the 90% finite-sample rank over 12 cells. A family-median baseline used the same training rows.

| Held-out result | Value |
| --- | ---: |
| LightGBM runtime MdAPE | 13.84% |
| Family-median baseline MdAPE | 23.01% |
| Upper-bound coverage | 24/24 rows; 8/8 cells |
| Mean point-to-upper width | 1.33 s |

The test contains only eight distinct cells from four workload profiles. Coverage and error are descriptive for this split; they do not establish performance on new workloads. Full hyperparameters, predictions, and artifact hashes are in [`runtime_model.md`](runtime_model.md) and [`artifacts/main_v1/`](../artifacts/main_v1/).

## Bounded policy and comparison

For each declared configuration, the fitted policy predicts point runtime and an upper bound. It computes expected normalized cost as `point runtime × (allocated vCPUs + allocated GB)`, checks the **upper bound** against the family SLA, and chooses the lowest expected cost among candidates passing OOD and deterministic memory guards. It abstains if none pass. The fitted CLI command is `safe-pipe recommend-model`.

| Mean median actual cost across four families | Value |
| --- | ---: |
| SAFE-Pipe selection | 7.524 |
| Declared default (`w1_t1_2g`) | 11.421 |
| Conservative (`w2_t2_2g`) | 10.366 |
| Uniform random among eight | 8.950 |

The policy selected `w1_t2_1g` for all four measured profiles. Its same-table normalized cost was **34.1% lower than the default**. This is **not an independent improvement estimate**: the model trained on some cells in the same physical table used for the cost comparison. Every configuration met the observed SLA, so the table cannot distinguish safety among policies. Detailed rows are in [`policy.md`](policy.md) and [`policy_comparison.csv`](policy_comparison.csv).

The OOD gate red-flags a family absent from its known profiles and yellow/red-flags declared input-size shifts. Four leave-one-family gate checks returned red for the held-out family. With one measured size per family, the size thresholds are heuristics and no k-NN threshold or new-family runtime accuracy was validated. There were zero actionable failures, below the planned positive-count gate, so the failure guard stayed rule-based; its `p_fail` field is **not** a calibrated probability.

## Reproducibility and remaining work

Install `.[dev,dask,ml]` on the experiment host. The code paths for generation, pilots, randomized collection, audit, grouped fitting, policy evaluation, and the LightGBM feature-contribution figure are under `experiments/`. The exact 96-row CSV, frozen metadata, model artifact, metrics, and figure are committed; large synthetic Parquet and raw JSONL remain local. [`Ganant Work.md`](../Ganant%20Work.md) gives the chronological PC log and [`docs/GIT_COLLABORATION.md`](../docs/GIT_COLLABORATION.md) explains the Git handoff.

This study needs new workload profiles and a separate held-out policy evaluation to support general cost claims. It needs actual actionable failures to study failure prediction, and reliable worker telemetry to quantify spill/peak memory. Optional TabPFN comparison was not run. The formal DTU submission should retain these limits and use the selected 32 GB Windows host description.
