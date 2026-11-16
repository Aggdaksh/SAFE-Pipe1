# One-probe feasibility: no single-request payback on current jobs

Prepared 2026-11-16 from Stage A/B and worker exports already committed through `0bdac0f`. No new project execution tests, Dask jobs, dataset generation or training ran on the Mac. The [standard-library script](analyze.py) reads existing data and the development [policy specification](../../configs/research_one_probe_v1.json); [analysis.json](analysis.json) retains every observation/choice and input hashes normalized to LF text for cross-platform checkout compatibility.

## Decision

**The proposed 48-attempt pilot remains disabled.** Even reducing the earlier six-probe replay to a single quarter-size low-cap probe does not add decisions beyond metadata or repay profiling cost on these eight short jobs. Code for a gated research prototype and a Windows checks-only handoff is prepared; it is not an implemented physical experiment runner, a trained model or a production advisor change.

## Comparison

Every probe decision uses one observed run, never another repeat or a full-job outcome. All three per-instance decisions agree in this development table. Each selected historical full outcome is counted once below (24 unique references), rather than treating 72 repeated exposures as independent jobs. Timing is a constructed per-instance median, using historical full references from another session; it is not measured online request latency.

| Rule | Selected full successes | Instances paying for a probe | Median constructed request wall seconds | Median partial balanced proxy |
| --- | ---: | ---: | ---: | ---: |
| Fixed 1 GB | 17/24 | 0 | 5.12, including failed-attempt times | 3.83, including failed attempts |
| Fixed 2 GB | 24/24 | 0 | 4.96 | 4.32 |
| File-share metadata | 24/24 | 0 | 4.79 | 3.87 |
| Total-size + largest-partition metadata | 24/24 | 0 | 4.79 | 3.87 |
| Always one quarter-size probe, counterfactual | 24/24 | 8 | 10.37 | 7.41 |
| Probe only for ambiguous metadata, counterfactual | 24/24 | 4 | 7.38 | 5.56 |
| Checked-in guarded default | 24/24 | 0 | 4.79 | 3.87 |

Both metadata heuristics and both probe heuristics select 1 GB for the same four instances and 2 GB for the other four. Their selected historical outcomes all have no declared pressure warnings. This agreement is development evidence, not independent reliability validation. The size-aware metadata comparator is stronger than file share alone: it changes its estimate with absolute rows/schema width/largest partition, even when file-share ratios are unchanged.

Median single-probe preparation plus execution lifecycle/preflight is **5.47 s**, charged before a selected full job. A shared sample's preparation is paid once for **each hypothetical request**, not amortized across the three diagnostic repeats. Metadata/controller wall overhead is unmeasured; the hypothetical probing policy uses the same metadata first. Full-input generation and research-wide integrity audits are experimental setup, not an online profiling cost.

## Accounting and optimistic headroom

Keep the declared weights 0.5 time, 0.25 threads, 0.25 memory. For each measured attempt:

`J = 0.5 × end_to_end_seconds + 0.25 × total_threads × lifecycle_seconds / 4 + 0.25 × total_worker_cap_bytes × lifecycle_seconds / 4e9`.

For a probe add `0.5 × sample_preparation_seconds`. Preparation CPU/RAM exposure and controller/metadata overhead are unmeasured, so the resulting profile score is **partial/lower-bound accounting**, not actual utilization or monetary cost. No resource normalization or objective was selected to favor the candidate. Wall time includes preflight; allocated resource-time uses the recorded lifecycle proxy. These are allocation proxies even during startup/cleanup.

An optimistic retrospective oracle chooses the lowest median full score among configurations whose three historical full attempts succeeded. Relative to size-aware metadata, it finds potential score reduction only for groupby with both factors: about **0.99 proxy seconds**, by tolerating its observed full-input pressure. All other instances have zero observed headroom. Even the **cheapest observed single probe** for each instance costs more than its oracle headroom, before including unmeasured preparation resource exposure or controller work.

If the oracle also requires all historical full outcomes to be quiet, **headroom is zero on all eight instances**. This uses full outcomes only for an optimistic descriptive comparison, never as a feature supplied to the candidate. It is not a universal mathematical bound for future workloads or a guarantee from three repeats. Failed attempts keep their status and incurred time; a short failed attempt cannot win as a cheap successful request.

## Limits and what is ready

- The metadata copy factors/reserve and 0.55 probe ratio cutoff are hand-set development heuristics. The cutoff was chosen after inspecting Stage B; no fitted model, calibrated guarantee or independent accuracy claim is made.
- One generated seed and eight instances do not justify a general failure classifier. Probe samples are reused across repeats.
- Nanny events and sampled worker peaks remain separate observations. No saved peak is automatically promoted to an exact full-memory training target.
- The [research decision code](../../safe_pipe/research/one_probe.py) validates shape/provenance, separates admission from diagnostic classification, retains unknown/failure/budget outcomes and limits each transition to one observation. The checked-in admission gate is closed.
- [Windows verification](../../docs/research/ONE_PROBE_WINDOWS.md) is pending: targeted synthetic tests plus comparison of the implementation with this independent descriptive script. The Mac performed static syntax checks only on that implementation.
- The [48-attempt matrix](../../configs/research_one_probe_pilot_draft_v1.json) is a disabled draft, not an executable or scheduled study. No new dataset, benchmark, training or main merge is needed now.

Next, complete the Windows software verification. A physical study requires a revised research hypothesis/use case with plausible incremental information and total-cost benefit. A longer meaningful job or recurring-job reuse would change the use case and need its own fair baselines, amortization assumptions and independent evaluation; neither is demonstrated by this artifact.
