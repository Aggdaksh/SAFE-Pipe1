# SAFE-Pipe project context

**Updated:** 2026-11-16. Canonical project memory: read this file first when resuming in another chat or on another PC. Update it after decisions, completed work or scope changes.

## Start here: current goal and execution constraints

The user's current objective is to develop and rigorously evaluate a **research-paper contribution** on top of SAFE-Pipe. Merely adding an ML library, calibrating an existing predictor, or changing from Spark to Dask is not sufficient novelty.

The candidate direction is **partition-aware adaptive probing for Dask configuration selection under memory pressure**. The question is whether cheap samples give misleading configuration rankings, whether simple memory scaling already resolves that, and whether better input probes plus a justified adaptive decision rule can improve configuration choices after paying their own overhead. This is a research hypothesis, not a proven unique algorithm.

- Active branch: **`codex/partition-probe-research`**, based on `origin/main` at `504f005`. Stage B collection checkpoint is **`3640874`**, followed by review **`bbdcb57`** and the read-only worker export described below. Earlier implementation/handoff checkpoint `975b446` remains historical.
- The user's authorization is to investigate on a separate branch, then consider merging if evidence justifies the contribution. **No merge now.** The original advisor remains the baseline on main.
- **Latest explicit instruction (2026-11-15): all runs are on Windows.** This includes execution tests, dataset generation, Dask benchmarks and training. This Mac is for code, research/design, documentation and static syntax/compile checks only. Do not run pytest here or restart the historical Mac matrices.
- Hardware available: Windows PC plus Mac. Earlier planning allowed 4–6 weeks; this is a planning horizon, not a confirmed submission date. Do not assume cloud spending is needed or authorized by the current work.
- The user's preferred advisor objective remains **balanced speed and resource use**. Research comparisons must state their objective and distinguish engine runtime from complete-request cost.
- The Windows experiment PC completed the development screen; the Mac has now performed a reproducible post-hoc review. No adaptive controller or new model has been trained.

## Current research state

**Stage: screen, Stage A/B and the individual-worker export/review are complete. The current Stage B selector's information/economics gate did not pass.** Read the [worker-memory review](reports/worker_memory_review_20261116/README.md) first. Continuous probe memory varies with historical pressure, but currently separates the same cases as file metadata; no incremental policy benefit is established. Hold Stage C and training until a revised method/use case and bounded protocol are justified. No overall benefit from partition-tail over matched-memory uniform sampling is established. The adaptive controller and a learned probe-reliability model are not yet implemented.

### Individual-worker review (2026-11-16)

Export checkpoint **`c8872b4`** contains all 144 Stage A/B attempts and 321 worker lifetimes. The Mac [recomputed review](reports/worker_memory_review_20261116/README.md) verifies CSV/JSON equality, identities, cap/sample provenance, raw-hash anchors and agreement with the earlier published aggregates. Raw Windows files were not rehashed here; Windows separately reports the full export audit and eight exporter tests. No project tests, benchmarks or training ran on the Mac.

- Stage A: 129 lifetimes, 96 initial and 33 added. Stage B: 192 initial lifetimes, no added workers. No requested export fields are missing.
- At the 1 GB target, 1/4 probes have group-median max-worker peak/effective-cap ratios of **41.8–47.0%** for four historically quiet instances and **62.3–67.1%** for four historically pressured instances. This is exploratory separation, not classifier accuracy; all four pressure cases are also the file-metadata escalation cases. No extra decision value over metadata is shown.
- **33/37** nanny-terminated worker lifetimes have stored sampled peaks below the configured 95% threshold, while all 37 corresponding nanny event RSS readings exceed it. Event readings exceed the saved peak in 36/37 cases. Preserve both sources: persisted peaks can miss higher termination-time readings and are not reliable uncensored full-memory targets. These are worker events, not 37 failed jobs; only seven Stage A jobs failed.
- Next work is a revised method/protocol design: identify a cheap signal/use case that can add information beyond metadata, retain event-aware labels and measurement limitations, define untouched validation groups and fair all-cost baselines, then revisit prior work. No new threshold/model is validated; no next-run protocol or main merge is scheduled. The current six-probe overhead remains unjustified at this scale.

### Post-Stage B review (2026-11-16)

The Mac review independently recomputed 96 compact CSV identities, source/protocol/reference hashes, 32 comparison groups and 40 instance/policy replay choices against Windows evidence `3640874`. All reported choices and costs match; see [reproducible analysis](reports/research_stage_b_review_20261116/README.md). Raw Windows datasets/logs were not independently re-audited on the Mac. No project tests, Dask jobs or training ran here.

- All 96 probes were quiet, so the binary warning signal cannot distinguish full-pressure cases in this table. Eight discrepancy groups are four workload/cap cases at two fractions, not independent classifier examples.
- Both fractions choose 1 GB for all eight instances, replaying 17/24 full successes. Fixed 2 GB and the development-derived metadata baseline replay 24/24. This is historical evidence, not fresh policy validation.
- Selection matches the frozen balanced formula: target weights 0.75/0.875; low/high median probe-lifecycle ratios 0.8351–1.1563 all favor 1 GB. Retuning weights after seeing failures would not establish a new result.
- Median profiling costs 24.62/26.38 s before a selected full job, versus 4.96 s for the matched historical fixed-2-GB full comparator. The current six-probe replay has not justified its cost.
- **Worker export completed on Windows:** [worker-level evidence](reports/worker_memory_stage_a_b_v1/README.md) preserves all 129 Stage A and 192 Stage B lifetimes, including 33 added Stage A lifetimes. The read-only exporter verifies both frozen plan/raw-record hashes and all 1,507 retained diagnostic-file hashes; all 321 worker summaries match their snapshots, with no missing requested worker fields. Eight synthetic exporter tests passed. No benchmark, dataset generation, training or main merge occurred. Next inspect these continuous observations and metadata before proposing a new hypothesis/protocol; no automatic Stage C or classifier. A paper contribution remains unproven.

### Completed Stage B Windows execution (2026-11-16)

The user requested starting Stage B on Windows. **74 targeted tests passed**, then preparation verified the exact Stage A reference and produced 16 shared samples. All **96/96 probes succeeded and were quiet**, with zero quality flags. The completion audit verified 16 sample directories and 961 diagnostic-file hashes. Read [completed Stage B evidence](reports/research_stage_b_windows_v1/README.md); the Mac did not execute tests or probes.

- `experiments/probe_stage_b.py` prepares samples from the exact completed Stage A plan/raw data/diagnostics and published outcomes, verifies unchanged collector/operator/diagnostic sources and the same environment, and provides Windows preparation/run/audit commands.
- [Stage B specification](configs/research_stage_b_v1.json): 8 original instances × 2 fact fractions (1/8, 1/4) × 2 target caps × 3 repeats = 96 new probe attempts. Only 16 sample directories are prepared; samples are non-nested and shared across caps/repeats. Full inputs/dimension semantics are unchanged. Fraction, effective memory, sample seed and reference provenance are frozen per cell/plan.
- `safe_pipe/research/probe_fidelity.py` retains quiet/warning/unknown evidence and mixed full outcomes, reports 32 group comparisons, fixed/file-metadata baselines, and a declared balanced probe-choice replay. Costs charge all six probes and shared preparation once per instance/fraction. Historical replay is not fresh online validation or a calibrated classifier.
- Runner/source checks, resumable failed attempts, sample validation, compact export and a final raw-evidence audit are integrated. No main merge or model training.
- Result: 32 eligible comparison groups, eight false-reassurance candidates and zero unnecessary-warning candidates. Both fraction-specific probe-choice replays selected 1 GB on all instances, mapping to 17/24 successful historical full outcomes; fixed 2 GB and metadata each map to 24/24. Median six-probe plus preparation cost is 24.62/26.38 s versus 4.96 s for the same-cohort historical fixed-2-GB full comparator. No fresh selected full jobs were run. Interpret these negative fidelity/economics results before a revised plan; no Stage C, extra seeds, training or main merge.

### Stage A implementation and completed collection (2026-11-15)

The user requested code improvements and a concrete plan, with all execution on Windows. Read [STAGE_A_WINDOWS.md](docs/research/STAGE_A_WINDOWS.md) next. Windows validation and all **48 Stage A attempts are now complete: 41 success, seven execution errors**, with 54 targeted tests and pip check passed. All seven errors have retained Dask nanny memory-termination evidence; all 24 attempts at 2 GB succeeded. Read the [Stage A results and audit](reports/research_stage_a_windows_v1/README.md). Stage A itself included no probes or training; Stage B was completed in the later Windows session described above.

- Durable per-attempt worker/nanny logs, scheduler events, active memory thresholds, timestamps, observed exit codes/signals and evidence hashes survive temporary-spill cleanup. Unknown worker death remains unknown; nanny termination evidence is not an OS OOM claim.
- Expanded phase accounting retains nested graph/compute time, telemetry flush, supervisor/scratch cleanup, preflight, unaccounted time and shared preparation/audit/persistence costs. Failed attempts retain their incurred cost.
- Power/RAM/free-disk snapshots accompany runs. Batches stop for condition/infrastructure or diagnostic-write issues. A persistent attempt marker blocks silent retries after a crash before row persistence.
- Stage A fixes two families, four independently varied skew/imbalance patterns, two memory caps at fixed concurrency, three repeats and seed 911: 48 full-input attempts. Independent RNG streams preserve the same ordered rows when only file boundaries change. Order seed: 20261115. No probes in this stage.
- Windows-only preparation/run guards and frozen environment/source/data checks are implemented. Stage A has a mechanism report and compact diagnostic export; tests are added/extended for Windows execution.
- Next action: interpret the completed Stage A. Audit verified 48 identities, eight datasets, 546 diagnostic hashes and 37 raw nanny messages; all power/cleanup checks passed. Nine attempts had memory-termination evidence, including two eventual successes. Groupby imbalance-only failed 3/3 at 1 GB while both-pattern groupby succeeded 3/3; join both failed 3/3. Preserve these interactions and the single-seed limitation. Stage B is now complete; later stages remain conditional. No new model, paper result or merge is claimed.

### Deep review and proposed next direction (2026-11-15)

**Post-Stage A interpretation:** [STAGE_A_REVIEW.md](docs/research/STAGE_A_REVIEW.md) cross-checks the committed compact evidence. Within-seed memory-pressure/repeatability is supported; cross-seed generality and an adaptive-policy benefit remain open. A post-hoc file-imbalance rule selects 24/24 successful recorded outcomes (12 at 1 GB, 12 at 2 GB); this is a mandatory simple baseline, not independent validation or actual memory-use savings. Successful jobs still have a pooled median lifecycle of 4.869 s. Recommend preparing the bounded 96-probe Stage B protocol on the same immutable eight inputs, with false reassurance, unnecessary warnings, metadata comparisons and complete overhead declared before collection. No Stage B implementation/execution or training was started by this review. Full raw diagnostics remain on Windows; the Mac review checked compact records and source/protocol consistency only.

The prior request was deep analysis and a clear plan. The [reproducible review](reports/research_screen_review_20261114/README.md) recomputes the published metrics and adds fixed-config, overhead, repeat-variation and balanced-objective sensitivity checks. The [follow-up plan](docs/research/POST_SCREEN_PLAN.md) now has a concrete Stage A specification; later stages remain proposed. No new pressure experiments or training were launched.

- The 0.11% median scaled-memory engine regret covers ten complete recipes; mean is 4.09%, maximum 17.37%. A fixed `w2_t2_1g` has comparable speed results (0.08% median) but full-run failures. All 2 GB settings succeeded in their 24 observed full attempts each. Simple fixed/metadata baselines are mandatory.
- Replaying the scaled-memory method's choices over all twelve recipes selects configurations with three unsuccessful recorded full outcomes across two recipes. This is descriptive replay, not a calibrated failure probability. Stable probe timings can share full-scale bias.
- Full successful engine median is 1.636 s; scaled-memory probe median is 1.327 s. A constructed one-probe-per-config sweep plus sample-preparation estimate costs median 31.20 s versus 3.80 s for a fixed full job on the matched ten-recipe cohort. This excludes the selected final run and is not a measured online policy. A per-request eight-probe policy is unjustified at this tested scale.
- Current published rankings optimize engine speed. The user's objective remains balanced speed/resources. A post-hoc balanced-score sensitivity analysis changes the ordering; do not select an objective after seeing which favors the method. Predeclare the objective and charge total request cost in the follow-up.
- 768 attempts contain only twelve recipes, one generation seed and two repeats. The current data is insufficient for a general failure classifier. The original partition-tail speed claim remains unsupported; its occasional pressure signal is only a diagnostic hypothesis.
- Recommendation: first improve diagnostics, then a bounded mechanism study (48 full attempts; add 96 probes only if informative; at most 288 further attempts across two new seeds if justified). Maximum 432 is a conditional budget, not a scheduled matrix. Keep key skew and input imbalance separate. All heavy work stays on Windows.
- Build an adaptive controller only if mechanism, pre-decision information, profiling economics and baseline-comparison gates pass. Generic adaptive sampling/trust filtering overlaps Crispy, Ruya, MFTune, TUNA and Lynceus. A specific useful fidelity signal remains an open research question. If the gates fail, revise the use case/direction rather than force a novelty claim.

Implemented separately from production code:

- `safe_pipe/research/probe_workloads.py`: deterministic synthetic groupby/join inputs, data inventories/hashes, uniform and partition-weighted samples, plus a small pandas correctness oracle.
- `safe_pipe/research/probe_runner.py`: fresh supervised Dask clusters, worker RSS/managed-memory/spill samples, graph information, host-memory checks, wall-time limits and owned-process cleanup. Interruptions are explicit outcomes.
- `experiments/probe_pilot.py`: prepare/run/resume/analyze, frozen source/data/plan identities, randomized repeat blocks and four methods: full, uniform, uniform with scaled memory, and partition-weighted with the same scaled memory.
- `safe_pipe/research/probe_analysis.py` and `experiments/export_probe_evidence.py`: complete-group ranking comparisons, incomplete/failure retention and compact exports. These do not evaluate an online adaptive policy.
- [Protocol and closest prior work](docs/research/PROBE_PROTOCOL.md), [Windows instructions](docs/research/WINDOWS_HANDOFF.md) and [evidence ledger](reports/research_probe_v1/README.md).

Verified evidence must stay separated:

| Study/check | Observed state | What it supports |
| --- | --- | --- |
| Original main-v1 | 96 successful Dask jobs; 79-test baseline | Existing bounded advisor, with the limitations below |
| Research correctness | 120-test suite passed; 2 subsequently added interruption/source-change checks also passed | Implementation checks; not 122 benchmark jobs or training iterations |
| Research tiny smoke | 16/16 successes; scalar outputs checked against pandas | Small-input software diagnostics |
| Mac 64-cell development plan | 1 recorded success; next larger-cap cell refused before execution | Partial data only |
| Mac 32-cell limited plan | 10 recorded successes; study stopped at the user's instruction | Partial data only; 2 full groupby runs recorded sampled disk spill |
| Windows research smoke | 16/16 successful tiny cells on 2026-11-13; memory samples present and zero owned descendants after cleanup | Windows software/cleanup diagnostic only |
| Windows research screen | 36/768 cells recorded, all successful; three cells sampled positive stored spill; one full join cell showed at least two worker restarts. Post-batch power check reported unplugged battery | Diagnostic development evidence only; power state was not controlled before each cell, so a fresh mains-powered plan is needed for comparable rankings |
| Second Windows screen, initially verified mains | **768/768 complete:** 759 success, one timeout, eight KilledWorker execution errors; zero cleanup survivors | Ten evaluable instances; two large uneven full-reference failures. Thirty spill-positive and thirteen restart-positive cells. The timeout retains its power flag. Median regret: uniform 3.87%, scaled-memory uniform 0.11%, partition-tail 8.17%; descriptive results only |

The two observed groupby spill peaks were 71,066,898 and 92,031,812 bytes, with one worker lifetime observed in each. They show pressure in those particular runs, not a stable ranking or benefit from the proposed sampling method. One additional Mac-limited attempt was interrupted before the older runner wrote its row; the ledger names that evidence gap. Do not hide it or fabricate a replacement measurement.

The two partial Mac plans cannot be pooled into a complete comparison. Historical source changed after their preparation. The first Windows plan is preserved at `data/probes/windows-screen-v1/` as a diagnostic checkpoint; its 36 rows should not be mixed with a later mains-powered plan. A compact [36-cell checkpoint](reports/research_probe_windows_v1_partial/README.md) is committed separately. The first Mac smoke predates source fingerprints and some metadata. The ledger documents these provenance limits.

## What remains, in order

### Useful preparation without heavy computation

1. Stage A/B Windows validation, collection, audits and compact-evidence reviews are complete. The Mac is for code, documentation, static checks and reading existing evidence; all project execution remains on Windows.
2. Worker export and [continuous-signal review](reports/worker_memory_review_20261116/README.md) are complete. Use the observed memory/metadata overlap and retained-peak limitations to define a distinct, affordable hypothesis before any new experiment; no additional export is currently required.
3. The current Stage B information/economics gate did not pass. Refine a controller only if a revised hypothesis identifies additional affordable information beyond simple metadata. Keep original speed findings and balanced sensitivity analysis distinct; preserve the negative result.
4. Draft the paper outline with factual pilot findings and explicit pending-method/final-evaluation sections. Closest-prior work must be revisited before making a novelty claim.

### Work on the other laptop

1. Collection is **complete**, ending 2026-11-14 at 00:08 IST. Preserve the existing 768 raw records and datasets; no benchmark remains active. All planned identities, source hashes, dataset hashes and cleanup checks passed. The first diagnostic plan and partial exports stay historical.
2. Review the [completed report and audit](reports/research_probe_windows_mains_v1_complete/README.md), failure labels, flagged power interval and repeat noise. Follow [next decisions](docs/research/NEXT_STEPS.md); another collection needs a declared follow-up design rather than automatic repetition.
3. Analyze whether proxy-ranking errors persist after the matched uniform-memory baseline. Confirm pressure and repeatability; two repeats are exploratory, not strong statistical evidence.
4. If a useful gap remains, implement and test the adaptive policy; otherwise revise or abandon the candidate. Training a reliability model is conditional on the design and sufficient independent data, not an automatic next step.
5. Evaluate the final method on independent instances, with predeclared baselines and total request cost: preparation + all paid probes + a fresh selected full run. Preserve separate development and final-test data; do not tune on the latter.
6. Write supported findings, limitations and reproducible artifacts; then seek the user's integration decision. A prepared framework alone is not paper readiness or proof of novelty.

The original advisor still needs prospective validation on its original Windows host. That is a separate pending task; the new research pilot does not complete it.

## Purpose and scope

SAFE-Pipe recommends a configuration from eight declared local Dask configurations under an engine deadline, or abstains. The preferred `advise` command balances predicted speed and configured resource-time. Project-I measured four synthetic workload profiles on one Windows PC with worker memory caps of 1 GB and 2 GB: four families × eight configs × three repeats = 96 runs. LightGBM, upper estimates, support checks, baselines, and reports use that frozen run table. No general safety guarantee or multi-node result is established.

## Machines and Git branches

| Machine | Role |
| --- | --- |
| Earlier Mac environment described as 8 GB | Historical coding/docs/tiny checks; not the current measured hardware fact |
| Current Mac, 16 GiB observed in historical research records | Code, research/design, documentation and static checks only; all execution tests now belong on Windows |
| Windows 11 PC, 31.4 GiB physical RAM in the original study | Physical experiment host (ADR-005); intended research laptop, environment to be verified again |

The original 16 GB plan is a conservative historical sizing reference. The original Windows host has 32 GB marketed RAM; **production worker caps and the eight-config grid stay unchanged**. The earlier Mac, Windows and advisor work is included in `main` after a 2026-10-28 fast-forward merge. Their original branches remain checkpoints. Pull `main` for baseline work, but pull **`codex/partition-probe-research` for the current research task**. Generated Parquet, raw JSONL runs and virtual environments are gitignored.

## Verified baseline implementation (separate from research)

- Schemas, optimizer, eight-config grid, JSONL store, tiny four-family Parquet generators, pandas collector, and 96-cell planner came from the Mac branch.
- Windows `.venv` has `.[dev,dask,ml]` installed under Python 3.14.6. The merged `main` suite has **79 passing tests** on this PC, including tiny Dask executions, advisor regressions and the model-loading compatibility checks.
- T0 passed on the selected Windows PC: one 512 MB Dask worker returned the expected sum. See [`reports/t0.md`](reports/t0.md).
- T0b pilot compared 1 GB and 2 GB workers on two scan sizes and one sort size. The 136 MB sort took 10.58 s at 1 GB versus 4.53 s at 2 GB; both succeeded. See [`reports/t0b.md`](reports/t0b.md). That historical study did not confirm spill or OOM; the separate research spill observations above must not be attributed to it.
- Dask execution and one-cell collection are implemented; the scored matrix is complete (96 jobs below).
- Four `main-v1` datasets (175–198 MB) are generated, fingerprinted, and ignored by Git. The committed index is `configs/datasets_main_v1.json`.
- Twelve 2 GB SLA pilot runs succeeded. Deadlines and the randomized 96-cell order were frozen in `configs/` before scored collection. See `reports/matrix_preparation.md`.
- All 96 Dask cells were measured and audited: 96 successes, zero SLA misses. The curated CSV is committed at `data/curated/runs.csv`; raw JSONL and Parquet remain local.
- Grouped LightGBM plus conformal, a conservative rule-based OOD gate, fitted CLI recommendation, descriptive same-table baselines, and a feature-contribution figure are implemented. See `reports/runtime_model.md`, `reports/policy.md`, and `reports/shap.md`.
- New `advise` policy defaults to balanced speed/resources, with hard upper-runtime deadlines, optional budgets, exact frozen descriptors, bound grid/artifact checks and per-candidate comparisons. It reuses the model without training. See `docs/CONFIG_SELECTION.md` and `reports/advisor_v1/`.

## Original project deliverables still pending

The balanced selection implementation and the original Windows study are now merged into `main` and published. The technical results draft and separate tiny live Dask demo are complete. Remaining experimental work is prospective evaluation on the original Windows host; broader profiles need new data and a revised model/support policy. See `docs/INDEPENDENT_VALIDATION.md`. Formal submission remains pending. Optional TabPFN remains unrun; no failure classifier is supported because all 96 measured jobs succeeded.

## Design rules

- Use pre-run features only for baseline inference. A target job's actual runtime, memory, status and spill cannot enter its own prediction vector. A future adaptive research policy may use already-completed probe observations available before its decision, with their cost charged; it must not use the selected full run's outcome to choose that same run.
- Optimize the declared balanced dimensionless score using point runtime; test deadlines against the frozen upper estimate. Use explicit hard checks and abstain when none pass. Preserve historical cost/model features for old report reproduction.
- Keep the production target caps at 1 GB and 2 GB despite the larger host. Research proxies use explicitly recorded scaled caps from their protocol. State the actual machine and cap mapping for each study.
- Failure handling stays deterministic until enough correctly labeled independent failure data supports training and held-out evaluation. A fixed number of positives alone does not establish classifier quality.
- Every reported number must be traceable to its named study and artifact. Keep the original frozen 96-run table separate from the research pilot and future evaluations. No Glue, 176-run, unmeasured improvement, or unverified novelty claims.

## Documents

[`PROGRESS.md`](PROGRESS.md) is the status ledger; [`docs/MICROPLAN.md`](docs/MICROPLAN.md) has task cards; [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines component contracts; [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) lists acceptance criteria; [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md) is the conservative six-week schedule. ADR-005 records the actual host change.
