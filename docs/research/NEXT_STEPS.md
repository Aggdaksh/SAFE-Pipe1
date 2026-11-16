# Research screen completion and next decisions

**Latest (2026-11-16): Stage B review is complete; its information/economics gate did not pass.** All 96 probes were quiet successes, yet eight groups gave false-reassurance candidates against Stage A pressure. The declared probe-choice replay maps to 17/24 historical full successes versus 24/24 for metadata, while paying 24.62/26.38 s median profiling cost per instance. The [independent compact review](STAGE_B_REVIEW.md) reproduced these numbers. Next: prepare a read-only Windows export of already-retained individual worker summaries, then inspect continuous signals and metadata before declaring another design. The exporter remains to be implemented; no new benchmark runs are required for the export. Hold Stage C, more seeds and training. The sections below preserve earlier decisions and chronology.

Updated 2026-11-14. The development screen is **complete: 768/768 attempts, 759 success, one timeout, eight execution errors**. The earlier diagnostic plan remains separate. No benchmark is running. See the [completed evidence](../../reports/research_probe_windows_mains_v1_complete/README.md).

**2026-11-15 update:** the detailed [post-screen plan](POST_SCREEN_PLAN.md) defines diagnostic stages and decision gates. Its [recomputed analysis](../../reports/research_screen_review_20261114/README.md) adds fixed baselines, selected-setting failures, repeat variation, overhead and objective sensitivity. Diagnosis/accounting code passed 54 targeted Windows tests, and Stage A completed all 48 attempts: 41 successes and seven execution errors with nanny memory-termination evidence. See [results and audit](../../reports/research_stage_a_windows_v1/README.md). Next: interpret factor-specific outcomes before declaring Stage B. All runtime checks, generation and physical runs belong on Windows. Do not automatically launch later stages or train a model.

## 1. Collection and integrity completed

**Stage A interpretation completed:** see [STAGE_A_REVIEW.md](STAGE_A_REVIEW.md). The compact evidence supports within-seed memory-pressure repeatability and motivates preparing a bounded 96-probe Stage B protocol. A simple file-imbalance rule also selects only successful recorded outcomes, so it is a mandatory baseline; this post-hoc replay is not independent validation. No additional jobs or training were launched. The sections below preserve the original screen chronology.

All planned identities are present exactly once. Frozen source and all 36 dataset/probe directory hashes match; cleanup left zero owned descendants and no run lock. Preserve the raw JSONL, inputs, condition samples and environment records. Do not rerun recorded failures.

The condition audit flags the original timeout's power interruption. Nine failures occurred on full inputs at 1 GB per worker within the largest uneven groupby/join instances; all probes succeeded. Worker deaths remain execution errors because their exact cause was not established.

The initial descriptive comparison covers ten eligible instances. Median selected full-engine regret is 3.87% for uniform, 0.11% for uniform with scaled memory, and 8.17% for partition-tail. Against matched-memory uniform, partition-tail is better on two instances, equal on three and worse on five. Two repeats do not establish significance or a universal winner. The two failed full-reference instances remain unevaluable.

## 2. Analyze the research question

For complete eligible groups, compare full execution rankings against uniform, uniform with scaled memory, and partition-tail with that same scaled memory. Report aligned, inverted and unresolved pairs, selected-configuration regret, all failures, spill and restarts. Keep condition-affected outcomes visible; do not silently exclude rows to improve a result. Two repeats and the current coupled patterns provide exploratory evidence only.

Decide whether uniform-probe errors exceed repeat noise, whether memory scaling already solves them, and whether the partition heuristic improves on the matched-memory baseline. Pressure alone does not prove better recommendations. Numerical ranking comparisons require the full candidate/repeat sets to succeed under the declared protocol; other groups stay unevaluable.

## 3. Choose a justified follow-up

If a useful gap remains, declare independent follow-up instances and additional repeats, separating input imbalance, key skew, size and seed. Specify the adaptive policy before evaluating it: what it observes, when it expands a probe, and how it chooses or abstains. If simple baselines solve the problem or the heuristic gives no repeatable benefit, report that result and revise the direction.

## 4. Evaluate a final method and write the findings

Freeze development, calibration (if needed) and untouched final workload groups. Charge total request cost: sample preparation, every paid probe and a fresh selected full execution. Compare against predeclared baselines, retain failures and report resource/time tradeoffs and limitations. Train a reliability model only if the design needs one and independent labelled data supports it. Finish reproducible artifacts and the paper, then obtain the integration decision before merging this research branch into main.

The original LightGBM advisor's prospective validation remains a separate task. This research screen does not retrain that model or validate its cost-saving claim.
