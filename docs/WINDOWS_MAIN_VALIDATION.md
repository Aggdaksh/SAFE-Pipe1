# Windows handoff: original advisor validation

Branch: **`codex/main-advisor-completion`**. This work is separate from the research branch and is not merged into main. Current status: **Windows software verification passed on 2026-11-21 at `d6f906a`: 143 passed, 0 failed, 0 errors, 0 skipped (36.89 s)**. `pip check` passed in the existing original `.venv` (Python 3.14.6); no fixes or dependency upgrades were needed. See [`../reports/main_validation_windows_checks_v1/`](../reports/main_validation_windows_checks_v1/).

**Stop for evidence review:** this checkpoint only completed step 1 below. The fresh 96-cell study has not been prepared or started. Steps 2 onward describe future work and require the user's go-ahead after reviewing this evidence. No original data regeneration or model training was performed. Preserve the original receipt and choose a new suffixed report directory if verification is run again.

## 1. Switch to the branch and verify software

Use the original Windows checkout and its existing original-advisor environment. Save or commit unrelated changes before switching; do not overwrite local research results. The original Parquet files must remain in `data/generated/main-v1/` (or supply their actual directory later).

```powershell
git fetch origin
git switch codex/main-advisor-completion
git pull --ff-only
.\.venv\Scripts\python.exe -m experiments.verify_main_validation --out reports/main_validation_windows_checks_v1
```

For a newly created checkout, `git switch --track origin/codex/main-advisor-completion` creates the local branch if automatic tracking is unavailable. Do not run installation upgrades routinely in the original environment. If dependencies are missing, fix and record that environment change, then rerun verification into a **new** output directory.

The verifier runs `pip check` and the full test suite, including tiny synthetic Dask integration checks. It requires zero failed or skipped tests. It saves the exact test output, JUnit counts, source/evidence fingerprints and environment in `verification.json`. These tests do not run the 96-cell matrix, regenerate the original datasets or train a model.

**First checkpoint:** retain and share `reports/main_validation_windows_checks_v1/`. If verification fails, stop here and fix the reported issue. Do not claim a passed test count before seeing this receipt.

## 2. Freeze the study before any scored attempt

After the software checkpoint passes, use the original PC on mains power, prevent sleep, close unrelated heavy applications and keep cache/background-load conditions consistent. Verify that this is the original experiment host. Host identity is an operator statement, checked against recorded hardware/software details; it is not inferred merely because a directory says `main-v1`.

```powershell
.\.venv\Scripts\python.exe -m experiments.validate_advisor prepare --study-dir data/validation/repeatability_v1 --run-set-id repeatability_v1 --data-dir data/generated/main-v1 --verification reports/main_validation_windows_checks_v1/verification.json --host-scope original-host --host-attestation "Original October Windows experiment PC; mains power; no unrelated heavy jobs; sleep disabled; original main-v1 datasets retained."
```

Make that attestation accurate for the actual setup. For a different PC use `--host-scope transfer` and describe the difference; the result is then a host-transfer study. Do not silently regenerate missing original datasets or loosen their hashes. Preparation refuses a changed input, an existing study directory, or a verification receipt that does not match current code and environment.

Preparation hashes the original data, verifies the frozen model support, saves four balanced advice reports (all eight predictions each) and the original randomized 96-cell plan. It records the original four deadlines: 2.6, 7.9, 4.3 and 13.1 seconds for scan/filter, group-by, skewed join and sort/merge respectively. No physical benchmark cell runs during preparation; no model is trained.

`manifest.json` and `attempts.jsonl` live in the ignored study directory. Preserve them. Do not edit the manifest or journal to change a decision, discard a failure or make a stopped job look complete.

## 3. Collect bounded batches

```powershell
.\.venv\Scripts\python.exe -m experiments.validate_advisor run --study-dir data/validation/repeatability_v1 --max-jobs 16
.\.venv\Scripts\python.exe -m experiments.validate_advisor status --study-dir data/validation/repeatability_v1
```

Repeat the run command until all 96 planned cells have a terminal record and there are no pending attempts or cleanup requirements. In an uninterrupted collection, six batches of 16 cover the plan. Failed attempts count as attempted cells; they are retained and are not automatically retried. Do not change the branch, code, environment, model, datasets or deadlines mid-study.

The runner records a start before invoking Dask, then the outcome and total collector-call duration. A missing engine runtime remains unknown. Collection/infrastructure exceptions stop the batch because cluster cleanup may be uncertain. A laptop observed unplugged after an attempt is flagged and collection stops; before/after power readings do not continuously establish power stability.

The 120-second timeout is the original collector's future-result wait timeout. It is **not** a hard bound on graph construction, cluster startup, cleanup or total user waiting time. Do not leave a stuck process unexamined on the assumption that this parameter supervises the entire process tree.

## 4. Recover explicitly after interruption

Inspect `status`. Verify that this study's Dask processes have actually stopped before using either command below. Do not terminate unrelated jobs.

If a start has no terminal event (for example, process termination), preserve the unknown outcome as aborted:

```powershell
.\.venv\Scripts\python.exe -m experiments.validate_advisor resolve --study-dir data/validation/repeatability_v1 --attempt-id ACTUAL_PENDING_ID --reason "Describe the interruption and how this study's workers were confirmed stopped" --workers-stopped
```

If the journal already recorded an infrastructure error or abort, acknowledge cleanup:

```powershell
.\.venv\Scripts\python.exe -m experiments.validate_advisor acknowledge-cleanup --study-dir data/validation/repeatability_v1 --attempt-id ACTUAL_REPORTED_ID --reason "Describe how this study's workers were confirmed stopped" --workers-stopped
```

These commands retain the unsuccessful attempt and let collection proceed to the next planned cell. They do not retry the same cell or fabricate its runtime. A malformed/truncated journal write is intentionally refused: preserve the original bytes and request review rather than deleting the last line. Recovery is for a well-formed pending start; automatic torn-write repair is not implemented.

## 5. Export independent results

Once complete:

```powershell
.\.venv\Scripts\python.exe -m experiments.evaluate_fresh_advisor --study-dir data/validation/repeatability_v1 --output reports/advisor_repeatability_v1
```

For an intermediate snapshot, choose a different new report path and add `--allow-partial`. It will explicitly say incomplete. Report directories are never overwritten.

The report exports the frozen manifest and exact journal snapshot along with `summary.json`, `cells.csv` and `README.md`. Keep all of these together. The evaluator uses the saved pre-run recommendations; it does not refit the model, regenerate advice or silently compare against the historical training table. The exported snapshot can be evaluated again using its report directory as `--study-dir` and a separate new output path.

Report acceptance out of four profiles, selected-configuration outcomes out of at most twelve attempts, and all 96 planned-cell outcomes separately. Error and upper coverage use successful engine timings with their denominators; failures, timeouts, missing values and power flags remain visible. Configured thread-seconds and GB-seconds are resource proxies. Original-host software differences limit the interpretation and are retained in the manifest/report.

## Return to the Mac for review

Commit the verification report and the compact evaluation export on **this same branch** after checking they contain only intended study evidence. Do not commit ignored Parquet files, virtual environments, secrets or unrelated raw research logs. Do not merge into main yet.

An unfavorable performance comparison is still a valid experimental result. Review the evidence before changing the policy. If tuning is needed, preserve this study as development evidence and collect another untouched evaluation afterward. The local UI and exact-input execution workflow are the next product milestones, not outcomes claimed by these tests.
