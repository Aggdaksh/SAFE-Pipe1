# Ganant Work — Windows experiment PC log

**Updated:** 2026-11-22 (Asia/Calcutta)<br>
**Repository:** `Aggdaksh/SAFE-Pipe1`  
**Working branch:** `codex/main-advisor-completion` (Windows software-verification checkpoint)<br>
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

## Checkpoint 17 - Original-advisor completion verification

- On 2026-11-21, preserved existing unrelated untracked `output/` and `tools/` directories; there were no tracked local edits to stash. Fetched origin, switched from the research branch to tracking `codex/main-advisor-completion`, and pulled with `--ff-only` (already current at `d6f906a6f69ea6893d8ebab3d38b6dd1a0ced8eb`). Research-specific checkpoints remain preserved on `codex/partition-probe-research`; that branch is separate from this main-derived completion branch.
- Read `context.md` and `docs/WINDOWS_MAIN_VALIDATION.md`. Ran the requested verifier once in the existing original `.venv`, Python 3.14.6 on Windows 11. Dependency check passed. Full software suite, including tiny Dask integration tests: **143 passed, 0 failed, 0 errors, 0 skipped, 36.89 s**. No implementation fixes, installs or dependency upgrades were needed.
- Saved the unchanged receipt, complete test output and JUnit XML in [`reports/main_validation_windows_checks_v1/`](reports/main_validation_windows_checks_v1/). Cross-checked all 78 receipt source/evidence hashes, environment and JUnit counts. Before/after byte hashes matched for 14 original project/model/curated/manifest files; all 70 original dataset files retained identical paths, sizes and modification timestamps. The inventory check is not a new full Parquet content-hash audit.
- Updated completion status, handoff and context documents. This checkpoint contains software evidence only: no fresh-study preparation, 96-cell run, original dataset regeneration, model training or main merge. Publish this report on the same completion branch and stop for user review.

## Checkpoint 18 - Minor B.Tech Project report evidence and first draft

- On 2026-11-21, began the user-authorized report-production work on `codex/main-advisor-completion`. Read the earlier eight-chapter report blueprint and compact research evidence from pinned research Git objects without switching branches or merging research code. Revisited the supplied seniors' report front matter/contents for the document structure; their source PDFs remain outside Git.
- Built `docs/minor_report_v1/`: 18 measured-data/schematic figures in high-resolution PNG and editable-text SVG, 13 compact CSV tables, source/hash provenance, recomputed key facts and four actual inference-only CLI examples (balanced/resource/fastest/abstain). No package install or project-environment upgrade was required; plotting uses the existing system Python.
- Added an offline HTML evidence book, a saved-output viewer, two actual browser screenshots and a printable 24-page PDF under `output/pdf/safe_pipe_minor_report_v1/`. The first eight-chapter prose draft records the original predictor, distinct research studies, latest verification and remaining work. Academic front matter, checked primary-source literature and official department formatting remain unfinished.
- The pack checks source hashes, held-out MdAPE, group denominators, Stage A/B counts, 37 individual termination-memory comparisons, saved inference outputs, links and PDF pagination. Full PDF pages are rendered for visual review; diagram labels were adjusted after print-size inspection. The original 78 verified source/evidence hashes remain unchanged. The existing 143-test checkpoint is reused, not presented as a new test run.
- No new benchmark, original dataset generation, training, fresh-study preparation, probe admission, Stage C or main merge occurred. Existing unrelated `output/` and `tools/` material remains untouched and excluded from this report commit. Continue report revisions from the pack's README and keep physical study authorization separate.

## Checkpoint 19 - Actual DTU academic Word report

- On 2026-11-22, the user clarified that the deliverable must be the actual Minor BTech report, following the senior samples with the DTU logo, rather than another evidence pack. Used the supplied Information Technology and BTech sample PDFs for layout/front-matter structure. Extracted only the DTU logo region; source PDFs remain unchanged and no senior-project prose, signatures or results were copied.
- Used the user's confirmed details: Daksh Aggarwal 23/IT/047, Ganant Awasthi 23/IT/055, Chaitanya Singh 23/IT/045; B.Tech VII Semester 2026-2027; guide Prof. Dinesh Kumar Vishwakarma, Head of Department, Department of Information Technology, DTU. Declaration and certificate signature/date lines remain blank.
- Created `output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx`: 36 pages, eight technical chapters, seven numbered references, 14 figures, nine native tables, four editable Word equations, contents/figure/table lists, Roman front matter, Arabic main pagination, and three appendices. Related-work material was checked against primary Dask, Ernest, C3O, LightGBM, conformal-prediction and Dask memory documentation sources.
- Used installed Word 16's native automation because the managed document runtime/loader was unavailable. No project package/environment changes occurred. The first PDF export method stalled; only the identified report-owned hidden Word process was stopped, preserving the user's pre-existing Word documents. Direct PDF save worked. Early attempts and repair helpers are archived under ignored `reports/_scratch/minor_actual_report_v1/`, outside the deliverable.
- Fixed native caption placement outside SEQ fields and authored the MdAPE fraction explicitly in OMML after visual review found a linear-math conversion problem. Checked the saved DOCX archive, 23 titled captions, 15 embedded images including the logo, equation denominator, student/guide details, front/main numbering and all 78 original source/evidence hashes. Native Word PDF pages were rasterized and reviewed; `report_quality.json` records the final artifact hashes.
- Added production sources and instructions in `docs/minor_report_v1/academic_report/`; the DOCX is editable, not a set of page screenshots. No fresh benchmark, original dataset generation, model training, probe admission, Stage C or main merge occurred. Keep subsequent manual Word edits before any rebuild. Department/supervisor review and genuine signatures are still required.

## Current work and next steps

### Checkpoint 20 - Report similarity and AI-writing research

- On 2026-11-22, the user requested detailed research on plugins/open-source repositories and Turnitin, and confirmed both similarity and AI-writing limits apply. Exact cutoffs and department wording remain unknown. Reviewed current official Turnitin/OpenAI guidance, official tool repositories and detector research; did not substitute old postgraduate thresholds for this Minor BTech evaluation.
- Added `docs/report_integrity_review_v1/index.html`, a detailed offline guide with linked sources, two-score examples, character/watermark distinctions, practical tool options and a chapter-by-chapter authorship/citation workflow. Plugin-directory search returned no Turnitin match; Scite was offered as a citation-research option but was not installed, connected or used. No claim of a guaranteed detector bypass or passing score is made.
- Ran the new read-only local audit against the actual DOCX and the two supplied senior PDFs. All eight technical chapters were identified. Selected zero-width/bidirectional characters, Cyrillic characters and nonempty directly hidden `vanish` runs were absent. The 55 nonempty `webHidden` results were numeric TOC/figure/table navigation references, with no unexpected narrative text in that set. Scope limitations are explicit.
- Exact normalized >=12-word comparison found two front-matter spans against the BTech sample and one against the Minor sample, all institutional/degree wording; no qualifying technical-chapter spans matched either sample. No overall similarity percentage or AI score was computed. This comparison excludes sources outside the two PDFs and does not establish plagiarism-free content. Seven bibliography entries were inventoried; claim-by-claim attribution review remains incomplete.
- Preserved the report byte-for-byte at SHA-256 `8df622f1c106665459e34cd72d060a1f1350f228e3a45f1d011e2a0370f62a1b`. No external checker received it, and no dependency install, report rewrite, benchmark, dataset generation, training or main merge occurred. Continue on this completion branch; obtain institutional reports and exact rules before assessing acceptance.

1. Review the Windows software-verification receipt on `codex/main-advisor-completion`. Do not merge into main or start experiment preparation automatically.
2. After explicit user review, follow the original-advisor handoff for a separately frozen fresh study. Software verification does not establish fresh advisor accuracy or generalization. Keep research work on its separate branch.
3. Review `output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx` with the team and guide; confirm department-specific submission requirements and sign/date the genuine front-matter forms. Preserve manual Word edits. Production and quality notes are in `docs/minor_report_v1/academic_report/README.md`.

## Resume commands on this PC

```powershell
git status --short --branch
git log -4 --oneline
Get-Content reports/main_validation_windows_checks_v1/README.md
Get-Content reports/main_validation_windows_checks_v1/SESSION_NOTES.md
```

Report analysis, inference examples and rendering are authorized. Fresh-study preparation and collection still await review. Do not regenerate original curated data or rerun the verifier into its existing output folder. Any later software verification must use a new output directory.
