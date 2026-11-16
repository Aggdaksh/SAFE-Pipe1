# One-probe research prototype specification

Version `one-probe-development-v1`, prepared 2026-11-16. [Machine-readable policy](../../configs/research_one_probe_v1.json), [feasibility result](../../reports/one_probe_feasibility_20261116/README.md), [Windows handoff](ONE_PROBE_WINDOWS.md).

**Current gate: closed.** The existing single-request information/economics test fails. Default requests select from the metadata heuristic or abstain, with no probe request. This is a pure research decision module; it is not wired into the original `advise` command, does not load a model, and cannot start Dask or generate data. No novelty or safety guarantee is claimed.

## Pre-decision inputs and support

`Workload` takes only dataset identity, operator family, fact/dimension row counts, number of numeric payload columns and fact-file row counts. It cannot receive the target full job's measured runtime, memory or outcome. The supported research shape is groupby or unique-dimension join, two single-thread workers, eight fact files, sixteen float64 payload columns plus an int64 key, 1–3 million fact rows, and a zero/groupby or one-million-row/join dimension. This is a declared design domain, **not** evidence of generalization to its unmeasured sizes/skews. Unsupported/inconsistent metadata abstains.

## Stronger metadata comparator

Let `N` be fact rows, `R` dimension rows, `P` payload columns, `Nmax` largest fact-file rows and `W=2` workers. Use input-layout estimates:

- Dense total bytes: `D = 8(P+1)N + 16R`.
- Dense largest fact partition: `L = 8(P+1)Nmax`.
- Lower scenario: `Mlo = 128 MiB + D/W + L`.
- Upper scenario: `Mhi = 128 MiB + D/W + 3L`.

Choose 1 GB if `Mhi <= 0.7 × 1 GB`; otherwise choose 2 GB if `Mhi <= 0.7 × 2 GB`; otherwise abstain. These reserve/copy multipliers are hand-set development scenarios, not a fitted memory model, measured RSS, confidence interval or guaranteed upper bound. The 0.7 factor is a conservative design threshold, not a proven failure boundary. The right dimension is included in total input bytes; this does not establish its physical working-set contribution.

The possible one-probe region is `Mlo <= 0.7 × 1 GB < Mhi`, when metadata chooses the higher cap. Clear lower-cap decisions do not require a probe. Scenarios exceeding both caps abstain.

## Admission contract

`plan_request` returns `select`, `abstain` or a single `probe` request. The checked-in `admission_enabled=false` blocks that last action regardless of optimistic caller estimates. A future reviewed specification could enable it only with an explicit `EconomicCase`:

1. A named source for pre-decision estimates, evidence of incremental information, and no use of the target full outcome.
2. Positive finite estimates of potential balanced-score saving and total profile score; estimated saving must exceed profile cost.
3. Estimated profile wall time must fit the declared wall budget.

The current table supplies no such supported case. Caller estimates are not magically verified or statistically guaranteed by the module. Reusing a same-table oracle as a live economic input is forbidden. There is no CLI flag to force physical probes, and no physical execution runner is implemented for this draft.

## Single-observation decision contract

For diagnostic replay, `probe_evidence_choice` consumes one quarter-size uniform probe at the low target's mapped **652,653,184-byte** cap, with two single-thread workers. Join keeps the full dimension. Bind parent dataset/feature identity, uniform method, deterministic seed, fraction, sample row budgets, cap and concurrency; require a sample fingerprint and reject mismatches. The seed follows Stage B's canonical hash of `[2026111601, instance_id, "uniform_memory_f0250"]`. A future runner must verify sample bytes/manifests against that fingerprint; the pure helper does not read Parquet. Require a successful finite scalar, complete declared quality, exactly two initial worker lifetimes, no missing memory fields/sampling errors and no spill/pause/restart/termination evidence. Unknown or warning evidence cannot enable a lower-cap override; keep the metadata choice and retain paid cost.

For clean observations compute `q = max_worker(sampled_peak_RSS / effective_worker_cap)`. Choose 1 GB if `q < 0.55`; otherwise 2 GB. A numerical tie at the cutoff uses 2 GB. **0.55 was chosen post hoc from the development separation**; it is not calibrated or independent validation. This method currently repeats the metadata split while adding overhead.

`finish_request` accepts exactly one observation for a bound, unmodified pending admission and produces a terminal result. It rejects a second observation, wrong request/data/config or altered policy/admission record. An exceeded/unknown wall charge preserves the metadata recommendation and incurred cost. These are pure decision contracts: a future execution supervisor must actually enforce wall limits, persist requests and prevent duplicate physical execution. The helper does not claim to enforce a runtime deadline by checking cost after completion.

## Memory evidence and resource accounting

Keep sampled lifetime peaks and nanny-event RSS separately. `observed_memory` provides a largest observed value with source fields, marks termination evidence and explicitly sets `exact_peak_known=false` and `automatic_regression_target=false`. Missing readings stay missing. Sampling/abrupt-death gaps and unsynchronized peaks prevent treating the maximum as an exact uncensored regression label or concurrent cluster RAM.

Use the unchanged 0.5/0.25/0.25 objective and 4-thread/4-GB normalizers. Charge preparation once per request, every paid probe, failed attempts and the selected full attempt. The feasibility artifact separately identifies unmeasured preparation resource exposure and metadata/controller costs. Repeat medians are for analysis only; an actual decision cannot see another repeat. Current cost comparisons are historical replays, not new online evaluations.

## Research boundary and future experiments

Memory profiling/extrapolation already appears in [Crispy](https://arxiv.org/abs/2206.13852), and memory-guided search in [Ruya](https://arxiv.org/abs/2211.04240). [MFTune](https://arxiv.org/abs/2603.16450) discusses fidelity loss from reducing data volume and uses query-based proxies; its revised arXiv entry reports VLDB 2026 acceptance. These primary-source descriptions establish overlap, not an implementation-level reproduction or exhaustive novelty review. Adding a ratio threshold, a cost gate or a Dask backend alone does not establish a contribution.

The [disabled pilot draft](../../configs/research_one_probe_pilot_draft_v1.json) preserves the proposed 8-instance / 48-attempt budget (32 full, 16 probe), with new sizes/skew values. It is not generated, not executable and not the old Stage C. Before collection, revise the hypothesis/use case, demonstrate plausible advantage over fixed and size-aware metadata/analytical baselines, define hard execution budgets and fresh final validation, and perform a deeper closest-work comparison. If the gates remain negative, abandon this selector/use case rather than expanding the matrix.
