# Stage B: Windows handoff and frozen diagnostic protocol

Prepared 2026-11-15 on `codex/partition-probe-research`. **Implementation/specification prepared; new Windows validation, sample generation and all 96 attempts are pending.** The Mac has only edited code and performed static syntax/document checks. No new tests, benchmarks or training have run there. The earlier 54 passing Windows tests validate Stage A's revision, not these changes.

## Purpose and fixed scope

Stage A observed memory-pressure differences across operators and file imbalance. Stage B asks whether small uniform probes warn about those full-input outcomes, whether warnings are misleading, and whether information beyond a simple metadata rule could repay its cost. This is a diagnostic matrix, not a trained classifier, an independently evaluated controller or a novelty result.

The [versioned specification](../../configs/research_stage_b_v1.json) fixes:

- The exact eight original Stage A instances and historical 48 outcomes, including all seven failures. The parent plan is pinned by canonical SHA-256. No full inputs are regenerated or rerun.
- Fractions **1/8 and 1/4 of fact rows**: 250,000 and 500,000 rows. Join probes keep all 1,000,000 dimension rows, so these fractions are not fractions of total job data/memory.
- Target configurations `w2_t1_1g` and `w2_t1_2g`. Worker/thread concurrency remains two workers, one thread each.
- Three runtime repeats: **8 instances × 2 fractions × 2 caps × 3 = 96 new attempts**.
- Sixteen sample directories, shared across both caps and repeats. Samples at different fractions are deterministic but **not nested**. Repeats do not resample the input. Comparisons across fractions therefore also involve different sample realizations.
- Sample seed 2026111601, derived per instance/method using a stable hash; order seed 20261116. Each repeat block shuffles all 32 cells.
- Fresh clusters and a 180-second supervised lifecycle limit, plus final cleanup/diagnostic overhead. No automatic retries, extra seeds, Stage C or training.

Worker caps use the predeclared heuristic `round(536870912 + fraction * (target_bytes - 536870912))`:

| Fact fraction | 1 GB target: actual probe cap/worker | 2 GB target: actual probe cap/worker |
| --- | ---: | ---: |
| 1/8 | 594,762,048 bytes | 719,762,048 bytes |
| 1/4 | 652,653,184 bytes | 902,653,184 bytes |

The floor is not measured idle headroom. Retaining the full join dimension while shrinking worker memory can create proxy-only pressure; that possibility must remain visible in the results.

## 1. Update and validate on Windows

Use the original Stage A Windows checkout/environment and repository root. Keep mains connected and background activity/power mode consistent. Record changes to the session. The Stage B CLI requests system-awake state during preparation and batches, restoring the previous request afterward; it does not change the power scheme.

```powershell
git status --short --branch
git switch codex/partition-probe-research
git pull --ff-only origin codex/partition-probe-research
$ResearchPython = ".\.venv-research\Scripts\python.exe"
& $ResearchPython -m pip check
& $ResearchPython -m pytest tests/test_probe_workloads.py tests/test_probe_analysis.py tests/test_probe_runner.py tests/test_probe_pilot.py tests/test_probe_supervisor.py tests/test_probe_diagnostics.py tests/test_probe_export.py tests/test_probe_stage_b.py
```

Stop on unexplained local changes or failing checks. Do not upgrade packages halfway through collection. New tests cover the 96-cell budget/mapping, Windows guard, immutable reference compatibility, retained failures on resume, unknown telemetry, mixed full outcomes, false reassurance/warning candidates, fallback cost accounting and sample result consistency. Several use mocked measurements to verify logic; they are not new physical evidence. Existing supervisor tests execute tiny real jobs on Windows.

## 2. Prepare samples once from the completed Stage A

```powershell
$StageAPlan = "data/probes/windows-stage-a-v1/plan.json"
$StageBDir = "data/probes/windows-stage-b-v1"
& $ResearchPython -m experiments.probe_stage_b prepare --stage-a-plan $StageAPlan --out-dir $StageBDir
& $ResearchPython -m pip freeze | Out-File -Encoding utf8 "$StageBDir/requirements.txt"
git rev-parse HEAD | Out-File -Encoding utf8 "$StageBDir/revision.txt"
```

Preparation requires the original full datasets, raw `runs.jsonl` and diagnostic files on Windows, not just the compact GitHub export. It verifies:

1. The exact pinned Stage A plan, 48 unique outcomes, measured configs/environment, and agreement with published status/time/pressure measurements.
2. All eight source dataset inventories/hashes and manifest bindings; all retained diagnostic hashes and claimed nanny events.
3. Unchanged collector, workload/operator and diagnostic source files against Stage A. New orchestration/analysis is allowed explicitly; changing execution semantics requires a new compatibility decision.
4. A new sibling output directory, clear Stage A lock/attempt markers, mains and at least 10 GiB free on output/temp drives.

Only then are uniform samples prepared. The new plan binds fraction, seed, effective cap, reference snapshot, sample hashes and current source/environment. Successful preparation reports **96 cells and 16 sample directories, zero jobs executed**. A preparation failure may leave a partial new directory; preserve it for inspection and use a new versioned destination after fixing the cause. Do not overwrite Stage A or edit its saved hashes. Windows CRLF source hashes are expected: preserve the original checkout's line-ending configuration.

New source fingerprints intentionally prevent resuming historical Stage A/screen plans under this orchestration. No Stage A job remains pending. Its archived audit can be reproduced at its original revision; Stage B's preparation performs the explicitly declared cross-stage compatibility checks.

## 3. Inspect four attempts, then resume in small batches

```powershell
& $ResearchPython -m experiments.probe_stage_b run --plan "$StageBDir/plan.json" --max-runs 4
& $ResearchPython -m experiments.probe_stage_b analyze --plan "$StageBDir/plan.json"
```

Inspect retained outcomes, raw diagnostics, sampled conditions, cleanup and the new report. Incomplete comparisons are expected. Lower probe caps can legitimately spill/fail; preserve these outcomes. Check that fractions, parent hashes and effective caps match the plan, successful scalar values agree within the **same sample**, and owned cleanup survivors are zero.

If collection is sound, repeat bounded batches on the same plan:

```powershell
& $ResearchPython -m experiments.probe_stage_b run --plan "$StageBDir/plan.json" --max-runs 8
& $ResearchPython -m experiments.probe_stage_b analyze --plan "$StageBDir/plan.json"
```

Do not launch a loop that ignores failures/flags. Infrastructure/power/log problems stop the batch; review before resuming. Recorded failed/timeout/interrupted attempts are completed cells and are not retried. An unresolved attempt marker after a hard interruption blocks silent retry and needs reconciliation from raw evidence. Unknown telemetry, condition flags and inconsistent results are not quiet successes. Keep all attempts, and version any amendment rather than replacing inconvenient rows.

## 4. What the report will calculate

Each attempt is **quiet**, **warning** or **unknown**:

- Warning: an execution error/timeout, or observed nanny termination, stored spill, paused samples or worker restart.
- Quiet: successful completion, complete clean diagnostics/conditions/telemetry and zero for all those signals.
- Unknown: incomplete/confounded diagnostics, conditions, cleanup or timing, invalid scalar result, or disagreement among successful outputs of the same sample. Observable statuses/signals remain in the record; unknown is not silently zero.

There are **32 comparison groups**, one per instance/target cap/fraction. Only groups with all three known probe repeats and all three known full references receive discrepancy flags:

- **False reassurance candidate:** at least one quiet probe and at least one full warning.
- **Unnecessary warning candidate:** at least one probe warning while all three full attempts are quiet.

Report the complete counts/statuses alongside flags. The full join setting with 2/3 successes remains mixed. Repeats from different sessions are not synchronous pairs; discrepancy counts are not calibrated classifier false-positive/negative rates. Eight instances do not become 96 independent workloads.

The report replays three simple baselines: fixed 1 GB, fixed 2 GB, and a file-metadata rule using 2 GB when the largest fact-file row share exceeds **0.25**, otherwise 1 GB. That threshold was chosen from Stage A development evidence and frozen before Stage B; its performance on Stage A is not independent validation.

For each fraction, a deliberately simple probe-choice baseline requires three quiet repeats for candidate eligibility, then selects the lowest median probe lifecycle multiplied by the declared balanced target-allocation weight. If no candidate is eligible it records a 2 GB fallback, with no safety guarantee. Unknown/incomplete samples suppress this replay. This is a declared screening baseline, not the proposed final adaptive method.

The weight is `0.5 + 0.25 * configured_threads/4 + 0.25 * configured_memory_bytes/4000000000`. These weights encode the user's balanced preference; they are not trained coefficients. Ties use config ID.

Cost accounting pays **all six probes** per instance/fraction (two caps × three repeats), including failures, and sample preparation **once**, since the sample is shared. It reports a constructed request estimate by adding the median successful historical selected full execution including preflight; failed/mixed selected outcomes remain visible and no successful latency is invented when all fail. It also reports configured GB-seconds/thread-seconds as allocation proxies, not actual utilization. Preparation resource use and metadata/controller overhead remain unmeasured; no online savings or deadline guarantee is claimed. Shared dataset/audit/persistence costs remain separate in plan/manifests/batch records.

## 5. Complete, audit and export

After all 96 unique planned attempts have been recorded:

```powershell
& $ResearchPython -m experiments.probe_stage_b analyze --plan "$StageBDir/plan.json"
& $ResearchPython -m experiments.probe_stage_b audit --plan "$StageBDir/plan.json"
& $ResearchPython -m experiments.export_probe_evidence --plan "$StageBDir/plan.json" --out reports/research_stage_b_windows_v1
```

The audit checks frozen source/environment, all sample data, outcome bindings, retained diagnostic hashes/nanny events, no pending markers/locks, result consistency and cleanup. Quality flags are reported even if file integrity passes; `quality_pass: false` requires interpretation, not replacement runs. The compact export carries the reference snapshot, sample provenance, costs and per-cell signal/quality labels; raw data/logs remain local. Use a new empty export destination for each checkpoint.

Publish the compact export with Windows test summary, requirements/revision and a session note after inspecting it; retain full raw data/logs separately. **Stop after Stage B for review.** The next question is whether probe information adds value beyond the metadata baseline and can repay its cost. Further seeds, longer workloads, a controller, model training and main merge all remain conditional.
