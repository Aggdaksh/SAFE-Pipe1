# Worker memory review: continuous signal and retained-peak limits

Reviewed 2026-11-16 against worker export commit `c8872b4`. This is a post-hoc analysis of existing compact records, not another experiment, fitted model or final evaluation. The [script](analyze.py) imports only the standard library; reproduce with `python3 reports/worker_memory_review_20261116/analyze.py` from the repository root. It rewrites only [analysis.json](analysis.json). No project execution tests, data generation, Dask jobs or training ran on the Mac.

## Export completeness

The export contains all **144 attempts and 321 worker lifetimes**: Stage A has 48 runs / 129 lifetimes (96 initial, 33 added); Stage B has 96 runs / 192 initial lifetimes. Added lifetimes remain separate, without inferred worker-slot/replacement pairing.

The Mac review checks CSV/JSON equality, unique run/lifetime identities, frozen plan/raw-hash anchors, sample identities, caps, statuses, worker-count consistency and agreement between sums of individual lifetime summaries and the previously published aggregates. All checks pass; no requested worker fields or attributed events are missing in this export, and sampling-error counts are zero. Sums are used here only to reconcile exports, not to estimate concurrent RAM.

The [Windows verification](../worker_memory_stage_a_b_v1/verification.json) separately reports 1,507 diagnostic-file hashes checked and 1,515 original/anchor files unchanged after export. The Mac does not possess those raw Windows files and did not repeat that physical-file audit. Windows context reports eight synthetic exporter tests passed; this review did not run them.

## A continuous signal exists in this development table

The previous binary warning signal was constant: all Stage B probes were quiet. A continuous observation does vary. For each probe run, take the **maximum individual worker sampled RSS peak divided by that worker's effective memory cap**, then take the median across its three repeats. Stage B has exactly two initial workers per run and no added lifetimes.

The following ranges cover four workload-instance medians in each historical full-outcome group, at the **1 GB target**. The actual probe caps are 594,762,048 bytes for 1/8 and 652,653,184 bytes for 1/4; the denominator is the probe cap, not 1 GB.

| Fact sample fraction | Full input had no declared warning | Full input had a declared warning |
| --- | ---: | ---: |
| 1/8 | 35.6–41.9% | 45.9–50.8% |
| 1/4 | 41.8–47.0% | 62.3–67.1% |

The 1/4 sample shows a wider descriptive gap. Across individual 1/4 probe runs, ranges are 41.1–48.1% and 59.1–67.6%. The smaller sample's individual-run ranges nearly touch: 34.3–44.1% versus 44.2–51.8%. Do not count these repeats as independent workloads or infer classifier accuracy from post-hoc separation.

**The signal currently separates the same four imbalanced-file instances already identified by the file-metadata baseline.** It therefore supplies no demonstrated additional decision benefit. The pressure label also includes a groupby case that succeeded 3/3 with pressure; these are not four deterministic failure cases. The 2 GB full references all have no declared warnings, so pooling their differently scaled ratios with the 1 GB cases without conditioning on cap would be misleading.

The first Stage B worker RSS samples are about 74.78–75.68 MB. This is not a measurement of all fixed operator/cluster overhead, and cannot simply replace the 536.87 MB floor in the cap mapping. Join dimension memory, graph state and other allocations need not scale with fact rows. No new threshold or memory-extrapolation formula is validated here.

## Saved worker peaks can miss termination-time memory

There are **37 attributed nanny memory-termination events**, each on a distinct observed Stage A lifetime. This count is not 37 failed jobs: Stage A had seven failed jobs, and successful jobs can include worker terminations.

- In **33/37** terminated lifetimes, the last retained worker peak/cap is **below** the configured 95% nanny threshold. The median saved peak/cap across all 37 is 79.36%.
- The corresponding retained `nanny_memory_restart` event RSS is **above 95% in all 37**, with a median of 97.23% and a range of 95.05–113.56%.
- Event RSS exceeds the saved worker peak in 36/37 lifetimes; the largest difference is 360,710,144 bytes.
- The event occurs 0.016–0.419 seconds after the worker's last retained sample (median 0.165 seconds).

These discrepancies directly show that the persisted worker summary can omit a higher observed termination-time reading. Asynchronous sampling, persistence timing and abrupt termination are consistent explanations; this export does not isolate their individual contributions. Zero sampling errors does not mean every short-lived peak was observed or saved.

For future development analyses, preserve the worker peak and event RSS as **separate measurements with their sources**. A lower retained peak is not proof that the worker stayed below its memory limit. Do not train a full-memory target from the saved peak alone, subtract unsynchronized peaks to infer unmanaged memory, or turn a nanny termination into a claim of OS OOM. Even the event reading is an observation, not the true continuous-time maximum or a synchronized cluster peak.

## Decision and next work

The worker export was useful: it reveals a continuous development signal hidden by the binary rule, and a concrete limit of the saved peak measurements. It does **not** validate a new selector, establish novelty or resolve the 24.62/26.38-second six-probe cost versus a 4.96-second historical fixed-2-GB full comparator.

The next work is method/protocol design using this evidence, not automatic collection:

1. Preserve event-aware full-pressure labels and separate peak/event measurements. Keep these eight instances as development data.
2. Specify what additional information a cheaper probe would supply beyond file metadata. A threshold that reproduces the metadata split is insufficient. Consider how a proposed method would handle both successful-but-pressured and failed full jobs without learning from the selected full outcome itself.
3. Before scheduling another Windows job, define meaningful workload variations where metadata and the candidate signal could disagree, strong fixed/metadata/analytical baselines, a realistic probing budget and untouched validation groups. Revisit closest prior work before claiming a contribution. Longer jobs or amortized reuse are different use cases and need explicit, fair accounting.
4. If no plausible incremental information/cost advantage can be specified, revise this controller direction. Do not expand the old Stage C protocol, retune resource weights to force a win or add ML merely to fit this development separation.

No new experiment is scheduled by this review. The original quiet/warning selector remains unsupported; the continuous signal is a candidate for investigation, and the paper contribution remains unproven.
