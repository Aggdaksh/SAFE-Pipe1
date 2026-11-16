# Research plan after the completed screen

**Post-export decision (2026-11-16):** [individual-worker interpretation](../../reports/worker_memory_review_20261116/README.md) is complete. Continuous memory ratios separate the same development cases as metadata, and stored worker peaks miss higher nanny-event readings in many terminated lifetimes. No incremental method benefit is established. The next deliverable is a revised, affordable hypothesis/protocol with event-aware labels and independent validation; no further export or benchmark is scheduled. Earlier diagnostic stages below remain historical proposals.

Drafted 2026-11-14; updated 2026-11-16. Status: **Stage A/B collection and interpretation complete; the current Stage B information/economics gate did not pass.** Later stages remain conditional proposals, informed by a post-hoc development analysis. This is not a frozen final-test protocol. All execution tests, generation, physical runs and training belong on Windows; the Mac is for editing/static checks and reading existing evidence. Branch: `codex/partition-probe-research`; baseline evidence: `6c08ec9`.

Next action: follow the [completed Stage B review](STAGE_B_REVIEW.md) and inspect whether an affordable continuous signal adds information beyond metadata using the [completed read-only worker export](../../reports/worker_memory_stage_a_b_v1/README.md). All 321 lifetimes are preserved with verified plan/raw/diagnostic hashes; eight synthetic exporter tests passed and no jobs were rerun. Windows collection validation passed 74 targeted tests; 96 probes completed quietly with a passing audit. Quiet samples did not identify historical full pressure in eight groups, and the six-probe replay has no demonstrated benefit over the simple metadata baseline at the tested scale. The [Stage B handoff](STAGE_B_WINDOWS.md) preserves the procedure; no Stage C or training is scheduled. Older proposed stages below do not override this decision.

Read [the deep review](../../reports/research_screen_review_20261114/README.md) for recomputed results and [the original completed report](../../reports/research_probe_windows_mains_v1_complete/README.md) for collection provenance. The original 96-run LightGBM advisor remains a separate baseline project. No main merge is planned here.

## The recommendation

Continue only with a **bounded feasibility study of probe reliability and profiling cost**. Preserve partition-tail as a comparison and potential diagnostic; do not build the paper around it being a better runtime sampler. Do not start a failure classifier from nine unsuccessful attempts concentrated in two recipes.

Candidate research question:

> Can a budgeted decision rule recognize when a small-input probe is misleading, obtain additional evidence only when useful, and improve configuration reliability and balanced resource/time cost relative to strong simple baselines?

This broad question overlaps existing work. A paper would require a specific mechanism and evidence beyond generic adaptive sampling, memory extrapolation, or switching to Dask.

## What the current evidence changes

| Finding | Consequence for the plan |
| --- | --- |
| Scaled-memory uniform has 0.11% median engine regret on ten successful-reference recipes, but 4.09% mean and 17.37% maximum | Diagnose its failures and outliers; do not optimize an already tiny median as the sole goal |
| A fixed fast 1 GB setting has 0.08% median engine regret on the same recipes | Fixed configurations are mandatory baselines; profiling must justify itself |
| Scaled-memory choice selects settings with three unsuccessful full outcomes across two difficult recipes | Runtime-only rankings must be accompanied by reliability outcomes; success of a small probe is insufficient evidence |
| Every tested 2 GB target setting succeeds in its 24 full runs | A simple higher-memory baseline may already solve reliability; the method must earn any extra complexity through resource/time benefit |
| Eight-probe sweep estimate is ~31.20 s versus ~3.80 s for one fixed full job on the matched cohort | An eight-probe per-request policy is inappropriate for these short one-shot jobs |
| Two runtime repeats; one generation seed; skew and file imbalance coupled | Additional runs must vary independent workload instances and isolate mechanisms, not merely repeat the existing 768 rows |
| Tail sampling triggers some pressure warnings while being worse on speed ranking | A targeted diagnostic is a hypothesis worth testing, not a validated replacement objective |

## 1. Fix the task and evaluation objective first

Primary intended application remains a **single memory-capped Dask batch request**, with a user preference balancing time and configured resources. It is not yet a multi-node or cloud-price optimizer. Treat recurrent jobs as a separate explicitly declared experiment if studied.

The existing balanced preference supplies a transparent score. Let `P(c)` be configured total threads and `M(c)` configured total worker memory. For successful execution time `T(c)` and a predeclared positive reference `T_ref` shared by methods for that request:

`J(c) = T(c)/T_ref * [0.5 + 0.25 * P(c)/4 + 0.25 * M(c)/(4 GB)]`.

The 0.5/0.25/0.25 weights encode the already chosen preference; they are not learned facts about hardware. Counts are configured allocations, not CPU utilization, energy or money. Always report raw time, thread-seconds and GB-seconds too.

For online evaluation, charge the complete lifecycle:

`T_request = T_profile + sum(T_prepare + T_probe_lifecycle) + T_decision + T_selected_lifecycle`.

Count a shared sample once, failed/timed-out probes in full, and actual cluster reuse/setup once. Record phase-specific configured resource-time. If resource exposure during client-only preparation is not measured, report it as unmeasured and retain its wall time; do not silently assign zero total overhead. Any persistent-cluster variant must give baselines the same reuse conditions and separate its cache/state effects.

Report completion/failure/abstention first, then successful-request latency and balanced cost at matched coverage. A method cannot win by refusing most difficult jobs. If a deadline is included, predeclare whether it is engine-only or complete-request; use the same scope for all experimental policies. The old model's upper bound is not valid automatically for these new workloads.

## 2. Finish instrumentation before new pressure experiments

Code and static checks can be done on the Mac; all runtime validation stays on Windows. Durable logs/events, conservative cause summaries, explicit phase accounting, condition sampling and interrupted-attempt protection are implemented and Windows-validated through Stage A/B. The historical data remains unchanged. The checklist below records the original instrumentation contract; individual-worker summaries still need a compact export for the current review.

- Persist worker and nanny logs, restart events, exit codes where available, timestamps and the active memory-threshold settings. Separate confirmed nanny memory termination, confirmed OS termination, unknown worker death, execution timeout and user interruption. Never relabel archived `KilledWorker` records as OOM without evidence.
- Record per-worker baseline RSS before workload execution and individual worker peak/lifetime data. Do not use summed lifetime peaks as one worker's headroom or concurrent cluster use.
- Record executed graph/partition structure and cheap estimates of key cardinality, key concentration and input imbalance. Charge any data scan/sketch used for decisions. Parquet encoded bytes and input-file row counts are not post-shuffle working-set measurements.
- Preserve operation semantics and result checks; avoid optimizer-eliminated work. Separate sample preparation, cluster lifecycle and execution timing.
- Keep power/host conditions and all physical outcomes. The source change requires a new versioned plan. Existing data can only be reused through an explicitly declared compatible manifest; no silent hash editing or retrying old failures.

Acceptance: small success and controlled termination checks yield usable diagnostics and no owned leftovers; unsupported/missing telemetry stays explicit. Windows source and packages must be pinned before collection.

## 3. A bounded diagnostic study, with early stopping

Stages A/B are complete. The [Stage A review](STAGE_A_REVIEW.md) motivated B, but the [Stage B review](STAGE_B_REVIEW.md) does not support expanding the current rule into C. The design below is retained as protocol history; C is not scheduled. This is mechanism discovery, not an unseen final benchmark.

First fix two families (groupby, unique-dimension join), 2M fact rows, eight input files, sixteen payload columns and key cardinality 1M. At each family use the four combinations:

| Pattern | Hot-key fraction | Input imbalance |
| --- | ---: | ---: |
| Balanced | 0 | 0 |
| Key skew only | 0.25 | 0 |
| Input imbalance only | 0 | 0.60 |
| Both | 0.25 | 0.60 |

Use target settings `w2_t1_1g` and `w2_t1_2g`. They hold worker/thread concurrency fixed while changing per-worker capacity. This is a mechanism test, not a substitute for later eight-config evaluation. Stage A fixes generation seed 911 and random order seed 20261115; candidate later seeds are 1223 and 1709. Independent column RNG streams ensure changing file boundaries preserves the ordered row values, while hot-key changes preserve payloads and the join dimension. This generator differs from the legacy interleaved mode; test those invariants on Windows. Randomize the 16 cells within each repeat block and keep library/host conditions consistent.

**Stage A: 48 full-input attempts.** Two families × four patterns × two caps × three repeats, using seed 911. Stop for interpretation before proceeding: are failures/pressure reproducible and diagnosable, and does the skew/imbalance separation explain anything? Three repeats are a diagnostic start, not statistically conclusive.

**Stage B: at most 96 probe attempts on the same declared instances.** If Stage A is informative, compare uniform probes at fractions 1/8 and 1/4 using the declared headroom mapping, with the same two caps and three repeats. These fractions are a proposed starting menu, not evidence of optimal fidelity. Full plus both probe levels gives 144 total attempts for the first seed. Charge all preparation and setup. Reject infeasible caps before physical execution.

**Stage C: at most 288 additional attempts across seeds 1223 and 1709.** Proceed only if the first seed shows a useful, observable gap. This brings the diagnostic study to a maximum of 432 attempts. Stop earlier if simple baselines suffice or signals are uninformative. A tail-diagnostic extension must be a separately versioned amendment with its own budget; it is not hidden in these counts.

Keep the two original outlier recipes as labelled diagnostic reproductions if needed, not as the only evidence. A larger-size or genuinely longer ETL case may be needed to test economics. Define meaningful workload semantics and host limits first; do not insert dummy loops to manufacture an overhead advantage. The short-job results remain in the paper as a boundary condition.

## 4. Decide using evidence, not sunk effort

| Gate | Continue when | Stop or revise when |
| --- | --- | --- |
| Mechanism | Pressure/failure mismatch recurs on new seeds with usable diagnostics | It was a one-off environment issue or the cause remains unidentifiable |
| Information | Pre-decision descriptors/probe observations distinguish misleading cases better than a simple size/cap rule on held-out development groups | Only the full result reveals the problem, or a fixed 2 GB/metadata rule performs equally well |
| Economics | Measured profiling can plausibly repay its cost for the declared workload/use case | Small jobs are already faster/cheaper with a fixed setting and no profiling |
| Benefit | A proposed controller reduces failures or balanced cost against matched baselines at comparable coverage | Improvements vanish across seeds/repeats or are only from changing the objective |
| Novelty | A precise mechanism differs from nearest systems and its ablation adds value | It is a generic existing tuning method with new naming or engine alone |

Before a final test, numerical thresholds must be fixed from development evidence and the intended operational tolerance. Do not invent a safety level from nine failures or choose thresholds after inspecting final results. If economics fails for one-shot jobs, an amortized use case is allowed only as an explicit scope revision. For a stable recurring workload, break-even reuse count is `ceil(profiling_cost / positive_per_run_saving)` in the same cost units; no positive saving means no finite break-even.

## 5. Candidate controller if the gates pass

Start with an explainable rule-based controller; use ML only if it adds validated information.

```text
Known workload descriptors + resource/deadline preferences
    -> choose fixed baseline or limited profiling budget
    -> cheap probe(s), with preparation and lifecycle cost recorded
    -> assess ranking uncertainty AND full-scale fidelity risk
       -> insufficient evidence: larger/diagnostic probe if budget permits
       -> sufficient evidence: select candidate using the declared objective
       -> exhausted budget: predeclared fallback or abstention
    -> fresh full execution; evaluate all outcomes and total request cost
```

Possible inputs include individually measured headroom, change in runtime/memory between probe fractions, partition/key descriptors, and disagreement between simple extrapolations. These are candidate features to falsify, not an already working risk score. Stable rankings across small probes alone cannot guarantee full-scale validity; both may share the same bias.

A max-two-probe mode is a reasonable budgeted prototype to compare, but exact scheduling and stopping thresholds should follow the pilot. If online observations cannot identify invalid probes economically, do not force a controller. A deterministic metadata rule can be the correct result.

If an ML risk/fidelity model is later justified, split by complete workload instances/recipes and seeds, keeping all related configurations, probe levels and repeats together. The current 768 rows and nine failures are not a sufficient basis for a general failure classifier. Compare to analytical/headroom rules and a small linear/tree model before a complex predictor. Recalibration or a frozen LightGBM artifact alone is not the research contribution.

## 6. Required comparisons and independent evaluation

Keep these baselines in scope:

1. Fixed `w2_t2_2g` (fast higher-memory reference), `w1_t2_2g` (lower allocation reference), and the fixed 1 GB speed comparator with its failures retained.
2. A declared metadata/headroom rule that requires no executed probes.
3. Uniform probing and uniform with memory scaling, under the same total profiling budget and objective.
4. A straightforward staged/multi-fidelity baseline with the same candidate set and access to measurements.
5. The candidate controller and ablations removing its fidelity signal or adaptive escalation. Retain tail sampling as the original comparison where relevant.

Do not feed the old four-profile LightGBM model these new workloads and call abstention or extrapolation a fair trained baseline. An added runtime predictor needs new grouped training and its own declared budget.

Freeze the algorithm, thresholds, feature access, budgets, baselines and primary balanced objective before final evaluation. Use fresh independent instances with several seeds, separate sizes/skew/partition combinations, both operator families and a realistic data/pipeline case if feasible. Real data alone does not establish generality. Keep development, calibration (if needed) and final groups separate; count effective workload units, not repeat rows, when discussing uncertainty.

Primary outputs: successful completion and abstention/coverage, total request wall time, configured resource-time, and balanced cost at comparable completion. Secondary: runtime ranking regret, worst-case outcomes, probe count/cost, false reassurance and unnecessary escalation, spill/restarts and failure causes. For timeouts, retain censoring and predeclare any utility penalty; never treat the timeout threshold as a successful runtime. Show paired per-instance outcomes, spread across seeds and confidence intervals only with a method justified by the final sample design. Two repeats do not support strong confidence claims.

Do not silently drop failed groups. Runtime-only ranking can remain undefined, while reliability outcomes and cost of attempted policies remain reportable. Final selected jobs must be freshly executed; replay of the same benchmark table is only development analysis.

## 7. Closest prior work and the novelty boundary

These are primary sources checked on 2026-11-14. The descriptions identify overlap, not claims that we have reproduced each system.

| Work | Relevant existing idea | Consequence for our claim |
| --- | --- | --- |
| [Crispy, IC2E 2022](https://arxiv.org/abs/2206.13852) | Small-sample profiling extrapolates memory to select resources | Sample-based memory prediction is already established |
| [Ruya, IEEE Big Data 2022](https://arxiv.org/abs/2211.04240) | Memory profiling narrows configuration search before Bayesian optimization | Memory-aware adaptive search alone is not a new contribution |
| [SimCost, online 2023 / journal 2024](https://link.springer.com/article/10.1007/s10619-023-07436-y) | Models sampled workloads, memory and I/O behavior for resource recommendations | Jointly shrinking data/resources is not enough; use a serious analytical baseline |
| [Spark SQL MFTune, 2026 preprint](https://arxiv.org/html/2603.16450v1) | Explains data-volume proxy failures and uses representative query subsets | Observing small/full rank mismatch is not new by itself; query-subset approach needs a compatible workload for fair reproduction |
| [Less Is More / MFTune, 2026 preprint](https://arxiv.org/abs/2608.00759) | Searches multiple fidelity factors and balances proxy usefulness/cost | Choosing sample size or fidelity adaptively is already covered broadly |
| [TUNA, EuroSys 2025](https://www.microsoft.com/en-us/research/uploads/prod/2025/02/TUNA_EuroSys_2025_Submitted-1.pdf) | Combines multi-fidelity sampling, unstable-configuration detection and noise mitigation across machines | Generic trust/noise filtering also overlaps existing work; full-scale fidelity bias must be distinguished from runtime noise |
| [Lynceus, ICDCS 2020](https://research.ibm.com/publications/lynceus-cost-efficient-tuning-and-provisioning-of-data-analytic-jobs) | Budget-aware exploration and useful information from aborted runs | Stopping expensive probes or charging a tuning budget is not sufficient novelty |

A plausible narrower contribution would be a specific, cheaply observable signal of **input-scale fidelity failure under per-worker memory limits**, coupled to a budgeted correction that beats fixed/headroom and generic multi-fidelity baselines. Whether such a signal exists at useful cost remains open. A Dask implementation and this pilot alone do not settle that question.

## 8. Work products and schedule

These are planning allowances from the next active work period, not a promised submission date. The old 4–6 week availability should be reconfirmed when scheduling long experiments.

| Phase | Deliverable | Where | Rough allowance / decision |
| --- | --- | --- | --- |
| Completed now | Recomputed review, reproducible analysis, figure and this plan | Mac, existing records | Done; no new training/runs |
| Instrumentation | Persistent diagnosis and phase-cost contract; targeted tests | Windows validation complete: 54 tests; retained diagnostics audited | Done for Stage A |
| Bounded diagnosis | Stage A, then gated B/C; evidence against simple baselines | Windows only | 2–4 working days including interpretation; stop after each gate |
| Conditional method | Controller, simple comparisons and ablations | Mac code; small Windows development | Roughly one week if a gap survives |
| Independent evaluation | Frozen methods on new groups; all costs/outcomes | Windows only | Roughly one week, budget fixed after pilot |
| Paper/artifact | Methods and evidence-driven results, limitations, reproducibility | Both | Begin outline now; finish after evaluation |

Do not begin a full classifier, a larger neural model, or another undirected 768-job sweep merely to demonstrate activity. Stages A/B are complete and interpreted. Next: inspect the completed individual-worker export under the [Stage B decision](STAGE_B_REVIEW.md) before declaring a revised plan. Do not assume extra seeds or training will resolve an uninformative warning signal or profiling overhead. All execution remains on Windows. Merge into main only after review and the user's integration decision.
