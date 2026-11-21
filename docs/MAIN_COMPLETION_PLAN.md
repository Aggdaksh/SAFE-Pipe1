# Main advisor completion plan

Updated: 2026-11-21. Implementation branch: `codex/main-advisor-completion`, based on main `504f005`. Do not merge before Windows verification and review. The separate `codex/partition-probe-research` branch is not part of this integration.

## Objective

Finish a bounded, evidence-backed advisor for the original four workload profiles on the original Windows host. The intended flow is: select a supported workload, specify deadline/preferences, compare eight candidates, optionally execute the exact recommended configuration, and inspect predicted versus actual results.

The original 96-row table, fitted model, calibration, configuration grid and published results remain the historical baseline. No new training is needed for this release. Fresh repeatability evidence does not establish generalization to other workloads or machines.

## Milestones and acceptance

| Milestone | Work and acceptance | Current state |
| --- | --- | --- |
| A. Prepare trustworthy validation | Immutable pre-run study; model, input, environment and source identities; explicit fresh attempt journal; evaluator consuming saved advice and fresh records; meaningful Windows tests | Software verification passed at `d6f906a`: 143 passed, 0 failed/errors/skipped; receipt in `reports/main_validation_windows_checks_v1/`. Actual study preparation awaits user evidence review |
| B. Collect fresh evidence | Original hashed datasets, original host, declared balanced objective; 4 profiles × 8 configurations × 3 attempts = 96 planned cells; keep failures, aborted attempts and missing cells visible | Not started |
| C. Interpret results | Acceptance, selected outcomes, point error/upper coverage, resource proxies, fixed baseline, feasible hindsight reference; distinguish complete collection from favorable policy performance | Awaiting B |
| D. Bind recommendation to execution | Verify actual input fingerprints and intended environment, run exactly the saved selected configuration, refuse after abstention; retain decision/result linkage and separate engine/lifecycle timing | Pending after validation review |
| E. Local interface and delivery | Supported-profile selector, deadline/preferences/budgets, all-candidate comparison and reasons, execution status, saved/downloadable report; Windows installation/demo instructions and final report | Pending after D |
| F. Broader-profile model v2 | Versioned instance IDs/features, feasibility collection, whole-instance training/calibration/test groups, new model/support policy and untouched final evaluation | Conditional subsequent scope |

Estimates for A–E are roughly 2–3 working weeks including Windows coordination. This is a planning estimate, not a measured matrix runtime or promised delivery date. F may need another 2–3 weeks or more depending on collection and evaluation. A research-paper contribution has a separate evidence requirement and cannot be scheduled as a guaranteed result.

## Fresh-study rules

- Save all four primary balanced advice reports, including all eight candidate estimates, before the first attempted cell. Keep thread weight 0.5, zero deadline reserve and the original deadlines for the primary study. The comparison reference is the in-grid `w1_t1_2g`, not a claim about Dask defaults.
- Reuse the frozen randomized 96-cell order. Each planned cell has one attempt; do not silently replace a failed/aborted cell with a favorable retry. An additional study or explicitly versioned future retry protocol is separate evidence.
- Keep each start and terminal outcome. Startup/collection/cleanup exceptions may leave the engine outcome unknown; do not invent a zero or timeout-length engine runtime. An interrupted process requires explicit resolution and cleanup before continuing.
- Finish the software verification on Windows before preparation. The receipt must match source and environment. Changing code/model/environment midway requires a new study, not silently combining results.
- Preserve the original data and model. New logs live in a separate ignored `data/validation/` directory; export compact final reports to a new `reports/` directory.
- An engine wait timeout is not a hard end-to-end deadline. Report observed lifecycle time separately. Input verification, inference and startup overhead must not be mislabelled as the model's engine target.
- Same-host intent is explicitly attested and the actual machine/environment are recorded. A different machine is a transfer study; it does not validate the original target environment.
- An unfavorable comparison is still a valid completed experiment. If results inspire tuning, the tuned policy needs another untouched evaluation set.

## Reporting contract

Recommendations/abstentions have denominator four workload profiles. Primary selected executions have at most twelve outcomes (three per accepted profile). The full matrix contains 96 planned cells; these are not 96 independent workload instances.

Use successful measured engine outcomes for runtime errors and upper-estimate coverage, and state that denominator. Keep failures, unknown engine outcomes and incomplete cells alongside those numbers. Report three timings and median/range per cell group, not precise tail reliability. Preserve original versus reserved-deadline counts separately.

Configured thread-seconds and decimal-GB-seconds are resource proxies, not measured CPU consumption, peak RAM, electricity or money. The hindsight reference uses only configurations that satisfy the declared constraints and succeed within the declared effective deadline on all three attempts, then minimizes median observed balanced score. It is not a deployable policy.

## Research and execution boundaries

All project execution tests, dataset generation, Dask jobs and training run on Windows. Mac work is editing, documentation, code review and static syntax checks only.

The completed research studies and disabled one-probe candidate remain separate. Their jobs do not replace this original-advisor validation; their current findings do not establish a beneficial probe policy. A new paper method needs a specific hypothesis, closest-prior-work comparison, useful evidence beyond strong baselines and untouched evaluation before integration.

The first Windows handoff is [software verification and fresh-study preparation](WINDOWS_MAIN_VALIDATION.md). The original scientific scope is in [independent validation](INDEPENDENT_VALIDATION.md).
