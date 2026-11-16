# Stage B interpretation and next decision

Reviewed 2026-11-16 against Windows evidence commit `3640874`, collected at source `beb8709`. This review recomputes existing CSV/JSON evidence only. No project execution tests, data generation, Dask jobs or model training occurred on the Mac.

**Decision: the current Stage B information/economics gate did not pass. Do not expand this protocol into Stage C or train a selector from these outcomes.** Preserve the negative finding and inspect already-retained worker-level evidence before proposing a different method.

**Windows follow-up completed (2026-11-16):** the [read-only worker export](../../reports/worker_memory_stage_a_b_v1/README.md) now contains 321 separate lifetimes from the original 144 attempts, with verified plan/raw/diagnostic hashes and no missing requested worker fields. Eight synthetic exporter tests passed; no workloads were rerun. The export action described below is complete; interpretation of continuous signals remains the next research decision.

## Independent compact-evidence check

The [review script](../../reports/research_stage_b_review_20261116/analyze.py) reads both Stage A/B CSVs and recomputes the declared selections/costs without importing the experiment code. Its [output](../../reports/research_stage_b_review_20261116/analysis.json) agrees with the published Stage B report:

- All 96 unique probe identities, measured caps, fractions, seeds, parent/sample fingerprints and recorded row budgets match the frozen plan.
- Canonical plan, protocol and reference hashes match. All ten source fingerprints match the working source when Windows CRLF checkout bytes are accounted for; saved hashes were not edited.
- The 48 full-reference outcomes match the Stage A export, including seven execution errors. The 96 probes are successful and quiet, with no exported quality/condition flags, warning signals, cleanup survivors or inconsistent sample results.
- All 32 comparison groups and all 40 instance/policy replay choices agree. Preparation is paid once per instance/fraction and all six probe attempts are charged.

This is a cross-check of committed compact evidence, **not a second physical-data audit**. The [Windows audit](../../reports/research_stage_b_windows_v1/completion_audit.json) reports verification of 16 sample directories and 961 diagnostic-file hashes. Those files and the raw per-worker records remain on Windows. The retained [test output](../../reports/research_stage_b_windows_v1/WINDOWS_TEST_OUTPUT.txt) reports 74 targeted tests passed, with 64 deprecation warnings.

## What the result means

All small probes looked quiet, including probes corresponding to full jobs with spill, memory termination or failure. The eight discrepancy groups are **four instance/1-GB combinations measured at two fractions**, not eight independent workloads:

| Full-input case at 1 GB per worker | Historical full successes | Small probes at both fractions |
| --- | ---: | --- |
| Groupby, file imbalance only | 0/3 | Quiet in all repeats |
| Groupby, both factors | 3/3, with pressure | Quiet in all repeats |
| Join, file imbalance only | 2/3, with pressure | Quiet in all repeats |
| Join, both factors | 0/3 | Quiet in all repeats |

Thus the **binary quiet/warning signal supplies no discrimination in this table**. Successful sample execution cannot be used as evidence that the full setting will complete without pressure. This does not establish that every continuous memory measurement, sampling scheme or adaptive policy is uninformative. Different-session repeats, one generated seed, one shared sample per fraction and eight instances also prevent interpreting these group counts as calibrated error rates.

The cap formula `floor + fraction × (target cap − floor)` is a fixed heuristic, not a learned pressure-preserving law. It does not establish that fixed process overhead, variable working memory, skew and join dimension memory scale together. The join retains its entire right dimension. We have not yet measured a decomposition that identifies why each proxy misses the full-scale behavior.

## Why the selector chose 1 GB

The declared score multiplies median probe lifecycle by a target-allocation weight:

`weight = 0.5 + 0.25 × total_threads/4 + 0.25 × total_memory_bytes/4e9`.

With two single-thread workers, the weights are **0.75 for 1 GB** and **0.875 for 2 GB**. Both configurations were eligible in every case. Therefore 1 GB wins when its median probe time divided by the 2 GB probe time is below `0.875/0.75 = 1.1667`. The observed ratios across all sixteen instance/fraction cases range from **0.8351 to 1.1563**, so every choice of 1 GB follows the frozen formula.

This computation is consistent with the implementation. It does not validate the proxy as a predictor of full-scale completion. Changing the weights after seeing the failures would produce a newly tuned development rule, not an independently demonstrated improvement. Keep the user's balanced objective fixed while investigating the missing information.

## Baselines and economics

| Rule | Historical full successes selected | Median profiling cost before a selected full job |
| --- | ---: | ---: |
| Fixed 1 GB | 17/24 | No executed probes; rule overhead unmeasured |
| Fixed 2 GB | 24/24 | No executed probes; rule overhead unmeasured |
| File-metadata threshold | 24/24 | No executed probes; metadata overhead unmeasured |
| Probe choice, fraction 1/8 | 17/24 | 24.62 s |
| Probe choice, fraction 1/4 | 17/24 | 26.38 s |

The fixed-2-GB comparator's median of per-instance median successful full lifecycle-plus-preflight times is **4.96 s**, over the same eight instances. Profiling alone costs more than a full job in this diagnostic replay, before executing the selected full job. Two instances selected at 1 GB have no successful historical full outcome; do not invent a successful request latency or hide their failures in an average.

The six-probe cost is the declared diagnostic replay, not the measured cost of an online controller. It does not rule out fewer probes, reuse across repeated jobs, or meaningful longer workloads. Each alternative needs its own predeclared use case and cost accounting. A persistent-cluster comparison must grant baselines the same reuse; artificial delays or dummy work cannot justify a saving.

The file-metadata threshold was derived from Stage A and frozen before Stage B. Since the replay still selects from Stage A outcomes, **24/24 is not independent validation**. Configured memory caps are not measured RAM utilization, monetary savings or a safety guarantee.

## Concrete next step: use existing evidence before buying more runs

1. **On Windows, export retained worker summaries for the completed Stage A/B attempts.** Read existing `runs.jsonl` and manifests only; do not regenerate inputs or repeat jobs. Preserve plan/cell/sample identity, worker lifetime, effective cap, initial sampled RSS, peak sampled RSS, managed/spill peaks, sampling-error/count/window fields and active memory settings. Keep missing/restarted records explicit. Recheck raw-record hashes against the audits. Strip PID/address/path values from public exports; a per-cell lifetime index is enough.
2. **Inspect continuous observations and metadata as development evidence.** Compare individual worker peak/cap and peak-minus-initial-RSS measurements with the historical full-pressure groups, stratified by family, fraction and cap. The initial RSS is the first plugin sample, not a guaranteed clean idle baseline; a sampled lifetime peak can include cleanup and miss a short spike. Do not subtract unrelated aggregate peaks to infer simultaneous unmanaged memory. The current CSV's sum of lifetime peaks cannot recover individual headroom or concurrent cluster RAM, particularly after restarts.
3. **Require a specific reason to continue.** A candidate signal must be available before the full decision and potentially distinguish cases beyond file imbalance/cap alone, with an affordable measurement path. Exploratory thresholds fitted here remain development choices. If no candidate emerges, stop this controller direction and consider whether a narrower measurement study or a different workload/use case warrants a new research plan. Repetition alone will not make the current constant warning signal informative.
4. **Only then declare a revised, bounded Windows protocol.** Specify hypothesis, cheaper decision rule, objective, simple baselines, all profiling/setup costs, failure handling, new workload groups and stop criteria before collection. Keep validation groups untouched; adding seeds to the already-examined recipes alone does not establish broad generalization. Execute fresh selected full jobs for final policy claims.

The immediate missing artifact is the worker-level export, not another 96/288-job sweep. No exporter or revised execution protocol is implemented by this review. No new model, Stage C run or main merge is scheduled.

## Paper status

We now have a reproducible negative development finding: at this scale and under this mapping, quiet samples miss historical full-scale pressure, and the six-probe selector does not beat simple baselines. That can inform a paper's motivation and limitations. **It is not yet a validated novel algorithm or sufficient evidence for a publishable contribution.** A new method would need both an additional useful signal and independent evidence of benefit; a measurement-paper framing would need deeper mechanism evidence, broader validation and a renewed closest-work check.
