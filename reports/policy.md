# Policy and baseline comparison (main-v1)

**Date:** 2026-10-26. Inputs: audited [`runs.csv`](../data/curated/runs.csv), fitted runtime artifact, frozen family SLAs. Per-family rows and exact metrics: [`policy_comparison.csv`](policy_comparison.csv), [`policy_metrics.json`](policy_metrics.json).

`safe-pipe recommend-model` profiles a declared workload, predicts all eight candidate point runtimes and conformal upper bounds, applies a conservative OOD gate and a deterministic memory rule, then selects the lowest **expected** normalized cost among candidates whose upper bound meets the SLA. Expected cost is point runtime × (allocated vCPUs + allocated GB); the SLA uses the upper bound. The cost is a local normalized resource measure, not USD.

On each of the four measured families, the policy selected `w1_t2_1g`. The table below uses the **median actual cost over three repeats** of the selected configuration. The default is `w1_t1_2g`, conservative is `w2_t2_2g`, and random is the expected cost of a uniform draw from the same eight configurations.

| Mean across four families | Normalized cost |
| --- | ---: |
| Policy | 7.524 |
| Default | 11.421 |
| Conservative | 10.366 |
| Uniform random | 8.950 |

The policy cost is **34.1% lower than default in this same table**. Every one of the 96 measured jobs succeeded and met its SLA, so no difference in failures or SLA misses can be measured. The model was trained on some cells in this table, and the selected configurations are not an independent policy test set; the cost difference is **descriptive**, not a validated improvement claim.

The OOD gate returns red for an unseen family and yellow/red for declared input-size shifts. Leaving each family out of the gate's known profiles in turn produced four red decisions out of four. This is a deterministic scope check, not a calibrated k-NN distance model; only one size was measured per family. Because there were **zero actionable failures**, `p_fail` in the candidate output is a rule flag (0 or 1), not a learned or calibrated probability. No failure classifier was fitted.
