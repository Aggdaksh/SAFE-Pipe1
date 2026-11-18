# Ganant Work — Windows experiment PC log

**Updated:** 2026-11-18 (Asia/Kolkata)<br>
**Repository:** `Aggdaksh/SAFE-Pipe1`  
**Working branch:** `codex/partition-probe-research` (research development; `main` retains the original advisor)<br>
**Purpose:** Read this first when resuming on this PC or handing the work to another agent. The canonical project plan is [`context.md`](context.md); this file records what happened on Ganant's PC.

## Checkpoint 1 — Repository and environment

- Found the Mac-side implementation on `origin/cursor/context-and-microplan` and created `codex/windows-dask` from it. The local `main` branch was older.
- User selected this Windows PC as the physical Dask experiment host. Measured Windows 11 build 26200, 33,711,480,832 physical bytes (31.4 GiB), 16 logical CPUs, Python 3.14.6. ADR-005 records the change from the original 16 GB plan; worker caps stay 1–2 GB.
- Created ignored `.venv` and installed `.[dev,dask]` plus `.[ml]` (LightGBM 4.7.0, scikit-learn 1.9.1).
- The Mac branch's 20 tests passed here; the current full suite has **29 passing tests** with Dask and ML installed. Dask integration tests skip on machines without Dask.

## Checkpoint 2 — T0 and T0b

- T0 passed: one 512 MB Dask worker returned `49995000` for `sum(range(10000))`; startup-inclusive wall time 6.198 s. Evidence: [`reports/t0.md`](reports/t0.md).
- Implemented Dask DAGs for all four families and a one-cell Dask collector with client-side timeout. Tiny integration tests execute all four families and test a timeout.
- T0b pilot compared 1 GB and 2 GB caps on scan, group-by, join, and sort. The 136 MB sort took 10.579 s at 1 GB and 4.529 s at 2 GB. All pilot jobs succeeded. Dask logged worker memory pressure during some 1 GB sorts; no OOM or confirmed spill. Evidence: [`reports/t0b.md`](reports/t0b.md).
- Local commit: `8c8e00c` — Dask execution and T0 pilots.

## Checkpoint 3 — Frozen matrix inputs

- Generated four `main-v1` Parquet datasets: scan 198,446,552 B; group-by 198,487,831 B; skewed join 174,604,451 B; sort 178,382,606 B. Verified file hashes against [`configs/datasets_main_v1.json`](configs/datasets_main_v1.json). Large files stay under ignored `data/generated/main-v1/`.
- Ran three successful 2 GB pilots per family. Froze SLAs at 1.5 × median: scan **2.6 s**, group-by **7.9 s**, join **4.3 s**, sort **13.1 s**. Pilots are excluded from scored data. Evidence: [`configs/family_sla_main_v1.json`](configs/family_sla_main_v1.json).
- Froze a shuffled 96-cell order using seed 2026 in [`configs/matrix_plan_main_v1.json`](configs/matrix_plan_main_v1.json). Added a resumable runner that validates dataset hashes and skips already completed cells.
- Local commit: `7680811` — datasets, SLAs, and matrix order frozen **before** scoring. Preparation report: [`reports/matrix_preparation.md`](reports/matrix_preparation.md).

## Checkpoint 4 — Physical matrix and audit

- Executed all **96** Dask cells on this Windows PC, one fresh LocalCluster at a time. Raw rows are in ignored `data/runs/main_v1.jsonl`.
- Audit confirmed 96 unique planned cells, 24 per family, 96 successes, zero timeouts, zero OOMs, zero SLA misses, consistent configs/data version/SLAs, and no voided rows. The absence of failures prevents a measured failure model or failure-reduction claim.
- Exported [`data/curated/runs.csv`](data/curated/runs.csv) for collaboration and local `data/curated/runs.parquet`. The feature whitelist in [`safe_pipe/features.py`](safe_pipe/features.py) excludes post-run labels. Audit details and hashes: [`reports/audit.md`](reports/audit.md), [`data/curated/audit.json`](data/curated/audit.json).
- Froze a grouped split by `family + config_id` in [`configs/model_split_main_v1.json`](configs/model_split_main_v1.json), keeping all three repeats of each cell together. This was committed before model fitting.
- Local commit: `efb6bcc` — audited run table and grouped model split.

## Checkpoint 5 — Grouped runtime model

- Installed the declared ML extras and implemented LightGBM on log successful runtime, using only the explicit pre-run feature whitelist. All three repeats of a family/config cell stay together: 36 training rows (12 cells), 36 calibration rows (12 cells), and 24 test rows (8 cells).
- Grouped split-conformal upper offset uses the maximum log residual from each calibration cell at the finite-sample 90% rank. The frozen split was committed before training.
- Held-out test MdAPE: **13.84%** for LightGBM versus **23.01%** for the family-median baseline. Upper-bound coverage: **24/24 rows and 8/8 cells**, with mean point-to-upper width **1.33 s**. This is descriptive evidence from only eight test cells, not a population guarantee.
- Model artifacts and detailed predictions are in `artifacts/main_v1/`. The model code is `safe_pipe/models/runtime.py` and `experiments/train_runtime.py`; the later CLI connection is recorded in Checkpoint 6.

## Checkpoint 6 — Fitted recommendations and explanation

- Implemented `safe-pipe recommend-model`: it reads a committed workload manifest or a supplied `WorkloadSpec`, predicts all eight candidate runtimes and upper bounds, applies the OOD/memory rules, and uses the existing bounded optimizer. A sort demo with SLA 13.1 s recommended `w1_t2_1g` and printed all eight candidates.
- The conservative OOD gate marks an unseen training family red; known-family size shifts over 25% yellow and over 2× red. With only one measured size per family these thresholds are **heuristics**, not calibrated k-NN. Leave-one-family gate checks returned red 4/4.
- Same-table descriptive cost comparison: policy mean normalized cost **7.524**, default **11.421**, conservative **10.366**, uniform random **8.950** across four families. The policy was 34.1% lower than default in this table, but the model trained on some cells in the table, so this is **not** an independent improvement claim. All 96 jobs met SLA; no safety advantage can be measured. See `reports/policy.md`.
- Rendered `reports/shap_sort_merge.png` from LightGBM feature contributions for the sort recommendation. See `reports/shap.md`. Matplotlib 3.11.2 was added to the ML dependencies.

## Checkpoint 7 — Results draft and integration check

- Wrote [`reports/project_i_results.md`](reports/project_i_results.md), a technical results draft tied to the audited table and metric files. Updated README, progress/task ledgers, architecture notes, and synopsis wording to identify the actual 32 GB Windows host and zero observed failures.
- Tested the fitted CLI end to end: the measured sort profile recommends `w1_t2_1g`; a threefold input-size shift abstains as red OOD. The complete suite passes **29 tests**.
- Cross-checked the committed metric files against `data/curated/runs.csv`: 96 rows, 96 successes, zero SLA misses, 13.84% test MdAPE, 24 covered test rows, and policy/default mean normalized costs 7.524/11.421. `git diff --check` found no whitespace errors.

## Checkpoint 8 — Live examiner demo path

- Added `safe-pipe profile` for the frozen pre-run workload and `safe-pipe execute` for one Dask demo job with manifest verification and a separate JSONL store.
- Ran `safe-pipe generate --dest data/demo --family sort_merge`, then executed the policy's `w1_t2_1g` configuration on the tiny sample. The live Dask job succeeded in **2.300 s** on 30,783 Parquet bytes. It is excluded from the 96 scored rows.
- Wrote [`reports/demo.md`](reports/demo.md) with the command sequence and an explicit distinction between the frozen main-v1 prediction/actual table and the tiny live job.
- Local commit: `83c1b06` — fitted policy, model artifact, technical results draft, demo flow, Git guide, and this PC log. Final suite: **29 passed**.

## Checkpoint 9 — Git PAT handoff attempt

- On 2026-10-26, the user placed `docs/Git.env` for PAT authentication. At inspection it was **0 bytes**, so no token could be used. The file was untracked and is now explicitly ignored by Git. Commit `b623a74` contains only that `.gitignore` rule; it does not contain a credential.
- Asked the user to save the PAT and reply when ready. Authentication and push have **not** been attempted with this new PAT. The previous push blocker (HTTP 403 for `JEENERDS`) still applies until a valid token with repository write access is supplied.

## Checkpoint 10 — GitHub connection and first successful push

- The user saved a PAT in ignored `docs/Git.env`. The line included a label before `=`; the first login attempt passed the full line and GitHub rejected it. Retrying with **only the value after `=`**, sent to `gh auth login --with-token` through stdin, succeeded. The token was never printed or added to Git.
- Verified that the authenticated GitHub account is `Aggdaksh` and that repository push permission is `true`. Configured Git to use the GitHub CLI credential for `github.com`.
- `git push -u origin codex/windows-dask` succeeded. The remote branch now contains the Windows implementation, 96-row curated CSV, fitted artifacts, reports, demo, and this log through commit `98f989e`. The branch tracks `origin/codex/windows-dask`.
- This checkpoint replaces the earlier HTTP 403 blocker below. Teammates can fetch the branch now; a pull request into `main` is available for review.

## Git publication status

**Published:** `codex/windows-dask` is now on `origin` under the authorized `Aggdaksh` account. The earlier `JEENERDS` HTTP 403 was resolved using the PAT value from ignored `docs/Git.env`. Do not add that file to Git. Follow [`docs/GIT_COLLABORATION.md`](docs/GIT_COLLABORATION.md) for cross-PC fetch and review steps.

## Checkpoint 11 — Beginner project lesson

- Created [`PROJECT_EXPLAINER.html`](PROJECT_EXPLAINER.html), a standalone browser lesson for a reader with theoretical ETL knowledge. It explains the problem, core terms, initial `main` and Mac snapshots, this PC's Dask work, the frozen 96-run experiment, results and limits, Git handoff, and remaining tasks.
- Added a small interactive, clearly illustrative SLA/cost selection example. Its resource arithmetic and optimizer rule match the code; its predicted runtimes are invented for teaching and separate from measured results.
- Linked the lesson from README. It contains no secret values or local raw data.

## Checkpoint 12 — Worked examples in the lesson

- Expanded [`PROJECT_EXPLAINER.html`](PROJECT_EXPLAINER.html) with hand-calculated scan/filter, group-by, and join examples; clarified that the current `sort_merge` Dask DAG shuffles by key but does not merge a second table.
- Added a configuration/resource-cost calculation, one exact audited CSV row, the real sort-family median-cost comparison, grouped model-split and uncertainty examples, OOD/abstention cases, a verified CLI-output excerpt, cross-PC Git commands, and three self-check questions.
- Kept invented teaching values explicitly separate from the frozen physical measurements and linked examples to the implementation or reports.

## Checkpoint 13 — Midterm synopsis alignment

- Reviewed the user-supplied three-page DTU synopsis PDF against the implemented branch. Its checksum matches the original synopsis considered in the repository's Phase 0 feasibility analysis; the PDF itself remains outside Git.
- Wrote [`docs/MIDTERM_SYNOPSIS_ALIGNMENT.md`](docs/MIDTERM_SYNOPSIS_ALIGNMENT.md): a goal-by-goal evidence and gap review covering the original 176-run/Glue proposal, the reduced 96-run Dask study, the model and policy results, and the limitations that must be stated at midterm.
- Re-ran the full Windows test suite (29 passed) and checked the committed CSV (96 unique cells, all success, zero SLA misses) plus the model/policy metric files. The review explicitly does not assign an official completion percentage or claim supervisor approval of the reduced scope.

## Checkpoint 14 — Midterm PowerPoint-agent handoff

- Created [`docs/MIDTERM_PRESENTATION_HANDOFF.md`](docs/MIDTERM_PRESENTATION_HANDOFF.md) with project/title-slide facts, verified evidence, exact quantitative caveats, a suggested slide sequence, speaker answers, and source links for another agent preparing the PowerPoint.
- Proposed a substantive second phase: new held-out workload profiles and independent policy evaluation, reliable resource telemetry and controlled pressure checks, stronger baselines, then final documentation. This is a **proposal**, not completed work or supervisor-approved scope. The document avoids treating the old 176-run design as a percentage denominator and uses a milestone-based halfway narrative only conditionally.

## Checkpoint 15 — Main sync and newer advisor branch on this PC

- On 2026-10-28, fetched `origin` and verified live remote `main` remained at `f474aae`. Switched to local `main`, ran `git pull --ff-only origin main` (Already up to date), then created local `codex/config-selection-policy` tracking its remote. The new branch descends directly from `codex/windows-dask`; no newer commits came from `main` and no merge into `main` was performed.
- Inspected feature commits `c3e328a` and `0d17438`: the explained balanced/resource/fastest advisor, exact frozen-profile support, artifact binding, data dictionary, independent-validation plan, cleanup/label regression tests, and cross-platform LightGBM text-loading fix. The original scored CSV/model and 96-job count remain unchanged; the 20-scenario replay is descriptive reuse of old rows.
- Ran the full suite on this Windows checkout: **79 tests passed**. Verified `advise --family sort_merge --sla 13.1` locally: balanced chose `w2_t2_1g`, resource chose `w1_t2_1g`, and fastest chose `w2_t2_2g`.
- Updated [`PROJECT_EXPLAINER.html`](PROJECT_EXPLAINER.html), the branch-sync guide and status docs so current code, branch locations and remaining independent validation are clear. The earlier `codex/windows-dask` branch remains a published historical checkpoint.

## Checkpoint 16 — Integrated and published on main

- On 2026-10-28, verified `origin/main` was an ancestor of `codex/config-selection-policy`, switched to `main`, and fast-forwarded it from `f474aae` to `abb21f7`. No merge conflict or rewritten history occurred.
- Ran the full Windows suite on merged `main`: **79 tests passed**. Pushed the integrated commit to central `origin/main` (`f474aae..abb21f7`). The 96 physical runs and model results did not change in this integration.
- Updated the explainer, README, Git collaboration guide, and midterm handoff to point teammates at integrated `main`. The older topic branches remain historical checkpoints, already contained in `main`.

## Checkpoint 17 — Windows research pilot and disk check

- On 2026-11-13, fetched `origin`; central `main` was still at `504f005` with no new commits. The new work was on `origin/codex/partition-probe-research` at `2419360`; checked out that tracking branch. The ignored PAT file was not read or staged.
- Created ignored `.venv-research` with `.[dev,dask]` and known-working package versions. All **43 targeted research tests passed** on this Windows PC; the full suite also exited successfully with three skips. A fresh research smoke plan completed **16/16 successful cells**, sampled worker memory, and left zero owned worker descendants.
- Prepared `data/probes/windows-screen-v1/` on this PC: 12 dataset instances, eight configurations, four methods and two repeats, or **768 planned cells**. The prepared Parquet/probe files occupy **3.39 GiB**. The first four plus one 32-cell batch recorded **36/768 successes**, sampled telemetry for every cell, zero owned descendants and no stale lock. Run files were under 1 MB; about 63 GiB remained free on C: after the batch.
- Three of the 36 screen cells had sampled positive stored spill. The full `skewed_join-2000000-uneven` run at `w1_t2_1g` reported about **1.17 GB summed spill peaks across worker lifetimes** and at least **two worker restarts**, though the final job status was success. This does not establish a stable ranking, spill reduction or a policy improvement; the plan remains incomplete.
- A post-batch power check reported 100% battery but `power_plugged=False`. Power source was not recorded before each of the 36 cells. Preserve this as a diagnostic plan; prepare a new independent plan after connecting mains power for comparable method rankings. Do not silently mix battery-uncertain rows with later mains-powered rows.
- Saved package versions, original revision and host/session notes with the ignored run data. Exported a [compact partial checkpoint](reports/research_probe_windows_v1_partial/README.md) for the team. Raw logs and generated Parquet remain local; continue the same plan only on this PC.

## Checkpoint 18 — Monitored mains plan and preserved timeout

- Verified the user's mains connection and prepared `data/probes/windows-screen-mains-v1/` at source revision `5516d1a`. Saved environment/revision, and sampled power, free disk and available RAM about every two seconds. The new data adds about 3.39 GiB; both local screen datasets together occupy about 6.78 GiB.
- The initial four plus 32-cell batch recorded **35 successes and one 180-second execution timeout**. The full two-million-row uneven join at `w1_t2_1g` observed at least three worker restarts and about 1.365 GB summed sampled stored-spill peaks across lifetimes; cleanup left zero owned descendants.
- Monitoring caught about 44 seconds unplugged during that timeout. Available RAM remained above 14.4 GiB and disk above 59.3 GiB. Retained the power interval and timeout as a confounded development observation, without attributing its cause solely to memory.
- Exported a [monitored partial checkpoint](reports/research_probe_windows_mains_v1_partial/README.md). The user confirmed the charger connection, and execution resumed in bounded batches on the same plan. The local controller requests system-awake state while active and supports a `pause.requested` file at batch boundaries. The exported count is a snapshot; local raw records may advance.
- The next 32 cells kept stable sampled mains and produced 31 successes plus one `KilledWorker` execution error on a full uneven two-million-row join at `w2_t1_1g`. Telemetry observed at least five restarts and about 1.489 GB summed sampled stored-spill peaks across lifetimes; cleanup left zero owned descendants. Preserved the ambiguous error without calling it confirmed OOM. The monitor stopped with **68/768 cells: 66 successes, one timeout, one execution error**; the compact export was updated to all 68 rows.

## Checkpoint 19 — Completion request and resume preparation

- The user requested finishing the screen. Rechecked the existing 68-cell plan, absent run lock, about 60 GiB free disk and available RAM. The PC again reported unplugged power; no further jobs were launched while awaiting a secure mains connection.
- Reviewed the retained timeout and ambiguous `KilledWorker` as legitimate measured outcomes. Added local controller option `--continue-reviewed-failures` so those outcomes can remain while later cells proceed, provided cleanup reports zero survivors. Unknown errors, interruptions, cleanup leftovers, power/disk problems and command errors still stop execution. Checked the outcome guards with synthetic cases; frozen research source and model remain unchanged.
- Wrote [completion and next decisions](docs/research/NEXT_STEPS.md): 700 planned attempts remain, rough runtime extrapolation is about 83 minutes before extra overhead/timeouts, followed by ranking/noise/baseline analysis and a conditional independent follow-up. The full screen is pending mains power, not a request to rerun failed cells.

## Checkpoint 20 — Completed and audited research screen

- The monitored controller finished **768/768 attempts** at **2026-11-14 00:08:24 IST**: 759 success, one timeout, eight KilledWorker execution errors. All planned identities are present once; failures were preserved without selective retry. No benchmark remains active.
- Verified frozen research source hashes, manifest identities and file hashes across all 36 physical dataset/probe directories. Every run reports zero owned descendants after cleanup; no run lock remains. Condition sampling covers all runs under the audit's ten-second-gap check; only the known timeout was flagged for observed unplugged power.
- Sampled positive stored spill occurred in 30 cells; observed restarts in 13. All nine unsuccessful outcomes were full-input 1 GB worker configurations in the two largest uneven instances. The eight worker-death errors are not confirmed OOMs. All sampled-probe runs succeeded, which motivates reliability investigation without establishing a learned risk model.
- Ten of twelve instances support descriptive ranking analysis; two failed full-reference instances remain unevaluable. Median selected full-engine regret: uniform 3.87%, uniform with scaled memory 0.11%, partition-tail 8.17%. Partition-tail was better/equal/worse than matched-memory uniform on 2/3/5 instances. These two-repeat development results do not establish a sampler benefit or statistical significance.
- Created the [completed export and reproducible audit](reports/research_probe_windows_mains_v1_complete/README.md), retaining earlier partial snapshots separately. Updated canonical context, status and next decisions. Fixed dataset storage remains 3.39 GiB per plan (about 6.78 GiB for both); about 59.5 GiB remained free on C:. No model was retrained or research branch merged into main.

## Checkpoint 21 — Pulled new tasks and completed Stage A

- On 2026-11-15, fetched and fast-forwarded `codex/partition-probe-research` from `6c08ec9` to `73de101`, receiving the deep review and Windows-only diagnostic/mechanism-study handoff. Central `main` remains the baseline at `504f005`; no merge was performed.
- Kept the existing research environment. `pip check` found no broken requirements; all **54 targeted Windows tests passed**. Prepared the frozen Stage A plan: eight instances, full inputs only, generation seed 911, order seed 20261115, two worker-memory settings and three repeats, for **48 attempts**.
- Verified the first four attempts' raw nanny logs against the diagnostic summary, then continued in batches of at most eight. All **48/48 attempts** are retained: **41 success, seven execution errors**, each error carrying nanny memory-termination evidence. All 24 attempts at 2 GB per worker succeeded. Nine attempts had nanny evidence, including two eventual successes. OS OOM remains unproven.
- Audited frozen source/environment/protocol, eight datasets, 546 durable diagnostic-file hashes, and 37 raw nanny memory messages. No unresolved attempt markers, power flags, log-write/truncation problems or owned cleanup survivors were found. Successful scalar results are consistent across configurations and repeats for each instance.
- At 1 GB: groupby imbalance-only failed 3/3, combined join failed 3/3, and imbalance-only join failed 1/3. Combined groupby succeeded 3/3. Preserve the family interactions and single-seed limitation; these observations do not validate a general failure probability or adaptive policy.
- Published the [Stage A evidence and audit](reports/research_stage_a_windows_v1/README.md), validation record, packages/revision and session notes. Raw records/logs and 2.53 GiB of generated data stay ignored locally. Stopped at the explicit interpretation gate; no Stage B/C, training or main merge.

## Checkpoint 22 — Pulled Stage A review and Stage B assignment

- Fetched and fast-forwarded the research branch from `77362b6` to `c623a36`, receiving `02de929` (Stage A interpretation) and `c623a36` (bounded Stage B implementation/specification). Local tracked files matched the remote after the pull; earlier untracked viva artifacts remained local.
- Read the Stage A review, Stage B specification and Windows handoff. Stage A interpretation supports investigating probe fidelity, with fixed/metadata baselines and total profiling costs retained. The new assignment is 96 probe attempts: eight exact Stage A instances, two fact-row fractions, two mapped worker caps and three repeats. Full Stage A inputs/outcomes are reused and not rerun.
- Remaining work: new Windows targeted tests (including `test_probe_stage_b.py`), compatibility/source/data/diagnostic verification, sample preparation, four initial attempts and reviewed batches, then Stage B analyze/audit/export and interpretation. The earlier 54 tests validate Stage A's revision only. No Stage B runtime tests or attempts were run during this pull/check.
- Confirmed the local Stage A plan/raw outcomes exist, the Stage B output directory does not yet exist, mains is connected, and about 45.6 GiB is free on C:. The preparation command still needs its full pinned-parent compatibility audit; file existence alone does not establish it.
- Stage C, extra seeds, training, final controller and main merge remain conditional. Read [`docs/research/STAGE_B_WINDOWS.md`](docs/research/STAGE_B_WINDOWS.md) before execution.

## Checkpoint 23 — Stage B started on Windows

- On 2026-11-16, verified the research branch at `beb8709`, no active benchmark, stable mains, about 44.7 GiB free disk and 6.9 GiB available RAM. Stage B had no existing output directory.
- Kept the existing environment: `pip check` passed and **74 targeted Windows tests passed**. Captured the actual test output before preparation; no packages changed.
- Prepared `data/probes/windows-stage-b-v1/` after the prescribed pinned Stage A provenance/source/data/diagnostic compatibility checks. This created **16 samples and 96 planned attempts**, reusing Stage A full inputs/outcomes without rerunning them. Samples occupy **1.04 GiB**.
- Recorded package/revision/session conditions, inspected four initial quiet successful probes, and continued reviewed batches of eight with source/environment/power/diagnostic/cleanup checks. Every outcome is retained; no Stage C or training is scheduled. Live counts and raw diagnostics are in the ignored run directory until export.

## Checkpoint 24 — Completed and audited Stage B

- Finished the frozen 96-attempt Stage B plan on 2026-11-16 at **00:20:51 IST**. All 96 attempts succeeded and were classified quiet, with no warning/unknown probes or successful-scalar inconsistencies. The reference Stage A outcomes, including seven errors, were not rerun or replaced.
- Final source/environment/sample/diagnostic audit passed: 16 sample directories, 961 diagnostic-file hashes, zero quality flags, no unresolved markers/lock and zero owned cleanup survivors. Actual Windows test output (74 passed), packages/revision, raw session notes and the audit are retained in the [completed export](reports/research_stage_b_windows_v1/README.md).
- All 32 comparison groups are eligible. Eight are false-reassurance candidates: quiet probes paired with historical full warnings in four instance/1-GB-target combinations at both fractions. None are unnecessary-warning candidates. These correlated development groups are not calibrated classifier error rates.
- Both probe-choice replays selected 1 GB on all eight instances, mapping to 17/24 historical full successes; fixed 2 GB and file-metadata replays each map to 24/24. No selected full jobs were newly executed. Median six-probe plus preparation cost is 24.62 s at 1/8 and 26.38 s at 1/4, versus 4.96 s for the same-cohort historical fixed-2-GB full comparator. This does not establish online savings or independent reliability.
- Preserved the negative fidelity/economics findings and updated canonical context, progress and handoff. Generated samples remain local (1.04 GiB), raw diagnostics about 1.81 MB; about 43.6 GiB remained free disk. Stopped after Stage B for interpretation, with no Stage C, extra seeds, classifier, training or main merge.

## Checkpoint 25 — Exported existing worker memory evidence

- Fast-forwarded the research branch from `3640874` to the Stage B review at `bbdcb57`. The user's current scope is existing-record export only; no benchmarks, dataset generation, training or main merge.
- Added the standard-library-only `experiments/export_worker_memory.py` and [worker memory export](reports/worker_memory_stage_a_b_v1/README.md). All **48 Stage A runs / 129 lifetimes** and **96 Stage B probes / 192 lifetimes** are represented. Stage A's 33 added worker lifetimes remain separate from its 96 initial workers; Stage B has 192 initial workers and no added lifetimes.
- Exported configuration/target and effective caps, fractions/repeats, first/peak RSS, managed/spill peaks, sampling counts/errors/window, thresholds, run status and sanitized lifetime-specific scheduler/nanny/exit evidence. Public artifacts omit PID/address/local paths. Missing values stay null/blank; all requested worker fields were present. Stage A parent-dataset hashes are not applicable and remain null.
- Verified frozen Stage A/B canonical plan hashes, raw JSONL byte hashes, published plans, unique run/cell identities and original completion counts/statuses. All **1,507 retained diagnostic-file hashes** and **37 raw nanny memory messages** matched. All **321 snapshots exactly match telemetry**; no unmatched worker evidence or missing diagnostic files. Rehashed 1,515 original evidence/anchor files after reading; unchanged.
- **Eight synthetic exporter tests passed**, covering separate lifetimes/PID reuse, ambiguous evidence, privacy filtering, null versus measured zero, failed hashes, missing snapshots and read-only destination protection. CSV/JSON parity and export identities were checked separately. No physical workload tests ran and no packages changed.
- Preserve original ignored raw directories on this PC. The export is a handoff artifact for subsequent continuous-memory/metadata analysis, not a new policy validation or proof of OS OOM. Research remains on `codex/partition-probe-research`.

## Checkpoint 26 — Verified one-probe code on Windows

- Checked the working tree and preserved the existing untracked `output/` and `tools/` artifacts. Fetched and fast-forwarded the research branch from `c8872b4` to expected commit **`82d40af`**, receiving the worker-memory review, one-probe feasibility analysis, guarded decision prototype and checks-only handoff. Read the latest `context.md`, `ONE_PROBE_WINDOWS.md` and policy/specification before execution.
- Used the existing `.venv-research` environment unchanged and ran exactly `python -m experiments.verify_one_probe --out reports/one_probe_windows_checks_v1` from the repository root. This was a new output directory; no earlier report was overwritten and no retry was necessary.
- **Verification PASS:** actual captured pytest output is **38 passed in 0.23 s**. Existing-data checks verified **eight default decisions**, **24 single-observation counterfactual decisions** and **37 worker-termination memory representations**. These are software replays, not fresh probes or statistically independent workload observations.
- **No implementation fixes were required.** Thresholds, evidence, policy and gate stayed unchanged. All 1,513 protected Stage A/B plan/raw/diagnostic and policy/draft-file hashes matched before and after the command. All eight default decisions requested zero probes; checked-in admission and the pilot remain disabled, and no physical attempts ran.
- Saved [verification/test output and session notes](reports/one_probe_windows_checks_v1/README.md), updated the canonical context and handoff statuses, and prepared the results for the same research branch. No Dask jobs, 48-run pilot, Stage C, dataset generation, model training, credential staging or main merge.

## Checkpoint 27 — Created the extensive visual learning guide

- On 18 November 2026, checked the tracked working tree and fetched the connected remote. Research local/remote evidence remained at `7f9c1b0`, main at `504f005`; existing untracked `output/` and `tools/` remained untouched.
- Created [SAFE_PIPE_LEARNING_GUIDE.html](SAFE_PIPE_LEARNING_GUIDE.html), a self-contained offline English guide with 28 chapters, about 10,900 words, six explanatory SVG diagrams, result charts, worked examples, three interactive teaching tools, a glossary/viva section and a five-question self-check. Added discovery links from README and the earlier explainer, preserving the old lesson.
- Covered the initial documented checkout, 96-run original prototype, midterm scope, feature inputs, LightGBM training/split/calibration, exact test MdAPE, policy objectives, research screen/Stage A/Stage B, worker-memory limits, one-probe feasibility and the current closed research gate. Explicitly reported that training-set accuracy is not in the saved metrics and that no new research model was fitted.
- Recorded the scoped Git history through `7f9c1b0`: 39 reachable commits, 20 through main plus 19 research commits. Distinguished commits from network push events, authorship identities from individual contribution, software tests from physical jobs, and replays from independent validation. The guide publication itself is excluded from those frozen counts.
- [Fact snapshot](docs/learning_guide_facts.json) preserves 16 normalized source-file hashes, saved prediction examples, metrics and commit identities. Recomputed the held-out MdAPE from the existing 24 prediction rows; checked local links, unique IDs and interactive arithmetic against saved artifacts. No benchmarks, training or original report regeneration.
- Browser review was blocked because Computer Use could not establish the current browser URL; no further UI actions were attempted. Local structural/data/JavaScript checks were used, and visual browser inspection is not claimed. Research admission/pilot remain disabled; no main merge.

## Current work and next steps

1. Stage B, worker-memory review/export and one-probe Windows verification are complete. The current single-request information/economics gate still fails despite software verification passing. Propose a distinct useful signal/use case with credible total-cost economics and closest-work comparison before any further physical experiment; keep admission/pilot disabled. Preserve every raw result and provenance record. Research stays separate from `main`.
2. After complete matched cells exist, assess whether proxy ranking errors persist beyond repeat noise and the uniform-memory baseline. Any adaptive controller or reliability model remains conditional on that evidence. The original advisor's prospective validation and formal submission remain separate pending work.

## Resume commands on this PC

```powershell
git status --short --branch
git log -4 --oneline
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe experiments/audit_runs.py

.\.venv-research\Scripts\python.exe -m experiments.probe_pilot analyze --plan data/probes/windows-screen-v1/plan.json
```

Running `audit_runs.py` regenerates local curated Parquet and CSV from ignored raw JSONL. It should reproduce 96 rows and zero SLA misses. The script does not rerun physical Dask jobs.
