# Ganant Work — Windows experiment PC log

**Updated:** 2026-10-26 (Asia/Kolkata)  
**Repository:** `Aggdaksh/SAFE-Pipe1`  
**Working branch:** `codex/windows-dask`, based on `origin/cursor/context-and-microplan`  
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

## Git publication status

The four implementation commits (`8c8e00c`, `7680811`, `efb6bcc`, `83c1b06`) exist **locally** on `codex/windows-dask`. A push retry after `83c1b06` again returned HTTP 403: the current credential is for `JEENERDS` and lacks write access to `Aggdaksh/SAFE-Pipe1`; `gh auth status` also reports that account's token is invalid. The optional GitHub connection is not installed. **No Windows commits have been pushed yet.** Follow [`docs/GIT_COLLABORATION.md`](docs/GIT_COLLABORATION.md) once an account with write access is available. Do not reset or switch away from this branch before preserving the commits.

## Current work and next steps

1. Restore GitHub write access with an authorized account, then run `git push -u origin codex/windows-dask`. Teammates can then pull the branch or merge it to `main` through review.
2. Optional TabPFN/Colab comparison and formal DTU synopsis submission still need team decisions. Do not train a failure classifier or claim failure improvement from zero failures.

## Resume commands on this PC

```powershell
git status --short --branch
git log -4 --oneline
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe experiments/audit_runs.py
```

Running `audit_runs.py` regenerates local curated Parquet and CSV from ignored raw JSONL. It should reproduce 96 rows and zero SLA misses. The script does not rerun physical Dask jobs.
