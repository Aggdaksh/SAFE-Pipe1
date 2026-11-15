# Stage A interpretation and next decision

Reviewed 2026-11-15 against Windows evidence commit `77362b6`, collected with research source `73de101`. This review reads existing compact records only. No new tests, dataset generation, Dask execution or training occurred on the Mac.

## What was checked

The [48-row export](../../reports/research_stage_a_windows_v1/measurements.csv) matches all 48 unique frozen cell identities, configuration settings and repeat labels. Canonical plan/protocol hashes match. Research source hashes match the committed source after accounting for Windows CRLF checkout line endings; do not edit the saved hashes. Status, nanny-message, spill and condition-sample counts below were recomputed from the export.

The [Windows completion audit](../../reports/research_stage_a_windows_v1/completion_audit.json) additionally reports verification of eight physical datasets, 546 diagnostic-file hashes, 37 raw nanny messages and zero unresolved attempts/cleanup survivors. Those raw datasets and diagnostic files remain on Windows and were **not independently rehashed on the Mac**. [Windows validation](../../reports/research_stage_a_windows_v1/WINDOWS_VALIDATION.md) reports 54 targeted tests passed before collection.

## Results and interpretation

- 48 attempts: **41 successful, seven execution errors**. At 1 GB per worker: 17/24 successes; at 2 GB: 24/24.
- All seven errors have pre-cleanup Dask nanny memory-termination evidence. Nine attempts have such evidence in total, including two eventual successes; 37 nanny messages were recorded. This identifies a Dask memory-limit action, not Windows OS OOM or the cause of every individual worker death.
- Twelve attempts have sampled stored spill. All are the four imbalanced recipe/config combinations at 1 GB, with three repeats each. No sampled spill or nanny termination appears in the 2 GB rows.
- All per-run condition flags are empty and all rows report zero cleanup survivors. There are 336 retained condition samples. Background activity/cache were not controlled.

| Family / pattern | 1 GB successes | 2 GB successes |
| --- | ---: | ---: |
| Groupby / balanced | 3/3 | 3/3 |
| Groupby / key skew only | 3/3 | 3/3 |
| Groupby / file imbalance only | 0/3 | 3/3 |
| Groupby / both | 3/3 | 3/3 |
| Join / balanced | 3/3 | 3/3 |
| Join / key skew only | 3/3 | 3/3 |
| Join / file imbalance only | 2/3 | 3/3 |
| Join / both | 0/3 | 3/3 |

The instrumentation and **within-seed repeatability** gate is supported: large-file inputs produce repeatable pressure, and two settings fail all three attempts. Generality across seeds/hosts remains untested.

The groupby interaction is important: adding hot-key skew to the imbalanced case coincides with success, while the same combination fails for join. A plausible explanation is that repeated keys reduce groupby's intermediate aggregation state, whereas a unique-dimension join retains fact-row multiplicity. This is a **hypothesis based on operator semantics**, not a measured decomposition of peak working memory. Task-level evidence and new instances would be needed to establish it. A monotonic “more skew means more failure” formula is unsupported.

## A strong simple baseline already exists in this table

Illustrative **post-hoc replay**: select `w2_t1_1g` for the balanced-file recipes and `w2_t1_2g` for the imbalanced-file recipes, regardless of key skew. This selects 24 recorded full outcomes, all successful: 12 at each cap. Mean configured cap is 1.5 GB per worker, versus 2 GB for the fixed higher-memory setting.

This is a 25% reduction in **mean configured memory cap in this replay**, not measured RAM consumption, financial savings, an online policy result or a future reliability guarantee. It uses the declared development factor; a real metadata baseline must compute available file-size/row-count descriptors and freeze its threshold before independent evaluation. It is a mandatory comparator, not a discovered paper contribution.

All 48 attempted lifecycles sum to 276.546 seconds, excluding shared preparation/audit and human gaps. Among the 41 successful attempts, median graph-plus-execution time is 2.174 seconds and median full lifecycle is 4.869 seconds. These are pooled descriptive medians, not paired policy comparisons. The jobs remain short; additional probing still has to justify its overhead.

## Next decision

**Recommend preparing the bounded Stage B diagnostic protocol. Do not launch later stages automatically.** The 48 runs demonstrate a mechanism worth investigating; they do not establish a novel controller or justify model training.

Stage B's proposed ceiling remains **96 probe attempts**: the same eight immutable Stage A inputs × two target caps × fractions 1/8 and 1/4 × three repeats. Reuse the exact Stage A datasets with their provenance; do not regenerate them under a changed seed or mix in the historical 768-screen inputs. Record fraction/memory mapping in each frozen identity, verify source/data integrity, and account for preparation, setup and failed-probe costs. All validation and execution remain on Windows.

Before collection, freeze a protocol that distinguishes:

1. **False reassurance:** small probe completes quietly, but the corresponding full setting fails or suffers memory termination.
2. **Unnecessary warning:** probe flags/fails while the corresponding full setting completes without observed pressure.
3. **Useful additional information:** probe signals distinguish cases beyond the fixed-2-GB and file-imbalance baselines, with repeat variation and unknown telemetry retained.
4. **Economics:** whether the information can plausibly repay its complete cost for the declared use case. Stage B is a diagnostic matrix, not a four-probe-per-request policy.

The mixed 2/3-success join setting must retain all outcomes; do not assign an invented deterministic safe/unsafe label from one selected repeat. No classifier performance or calibrated failure probability can be claimed from these eight instances.

The existing memory mapping is a heuristic. Join probes retain the complete right dimension while shrinking only fact rows; its fixed memory cost does not shrink proportionally. A failed scaled-memory probe can therefore be an artifact of the mapping. Preserve that possibility in the protocol and interpretation rather than automatically treating every warning as predictive success.

Continue toward a controller only if a repeatable, pre-decision signal adds value beyond the simple baselines. Additional seeds, longer meaningful workloads and independent evaluation remain conditional. If the metadata baseline suffices or profiling economics fails, revise the method/use case instead of adding ML to force a novelty claim. Stage C, training and main merge remain pending.
