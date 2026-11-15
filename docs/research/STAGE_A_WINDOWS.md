# Stage A: Windows execution handoff

Updated 2026-11-15. Branch: `codex/partition-probe-research`.

**Current status: Windows validation, all 48 attempts and the completion audit are finished.** Results: 41 successes and seven execution errors, all seven with Dask nanny memory-termination evidence; all 24 attempts at 2 GB succeeded. No power flags or cleanup survivors were recorded. See the [completed Stage A evidence](../../reports/research_stage_a_windows_v1/README.md). The commands below document the completed procedure; do not rerun its recorded cells. Stage B and training remain pending interpretation. The Mac is for editing and static syntax checks only. Do not run pytest, generate Parquet, execute Dask jobs or train models on the Mac. Do not merge this research branch yet.

## What this stage answers

Does key skew, input-file imbalance, or their combination produce repeatable pressure/worker death at fixed concurrency? The previous 768-attempt screen coupled these factors. Its `KilledWorker` errors do not prove OS OOM.

The frozen design is [research_stage_a_v1.json](../../configs/research_stage_a_v1.json). It specifies:

| Factor | Values |
| --- | --- |
| Families | Groupby; unique-dimension join |
| Fact rows / files / payload columns | 2,000,000 / 8 / 16 |
| Key-space size | 1,000,000 possible keys; not measured distinct count |
| Pattern | Balanced; key skew only; file imbalance only; both |
| Hot-key probability | 0 or 0.25 |
| File-imbalance parameter | 0 or 0.60; not literally “60% of all rows in one file” |
| Configurations | `w2_t1_1g`, `w2_t1_2g`; decimal GB per worker |
| Repeats | 3 runtime repeats, one data seed (911) |
| Method | Full input only; **no probes** |
| Random ordering | Seed 20261115; shuffle all 16 cells within each repeat block |
| Budget | **2 × 4 × 2 × 3 = 48 attempts** |
| Per-attempt supervision | 180 s including child setup, graph/execution and child cleanup; final forced cleanup/diagnostics may extend observed wall time |

New independent random streams keep ordered payload/key rows identical when only file boundaries change. Changing hot-key probability changes only the designated keys; the join dimension is unchanged. This is a new generator mode, not an exact rerun of the historical recipes. The legacy mode remains available. Small Windows tests must verify these invariants before collection.

The JSON is a **design specification**, not a generated dataset manifest. Windows `prepare` creates the actual 48-cell plan, source hashes, dataset inventories/hashes and frozen environment. Both preparation and execution of the Stage A preset are refused on non-Windows systems. Existing source-frozen experiments cannot resume under this changed collector; preserve the completed 768-run study as historical evidence.

## 1. Update and verify on Windows

Run from the Windows repository root, using the existing research virtual environment. Keep mains connected, power mode fixed, sleep disabled during batches, and background applications quiet. Record power mode and relevant background activity in a session note. No battery detected is logged separately from confirmed plugged-in battery power; a desktop needs its power setup documented.

```powershell
git status --short --branch
git switch codex/partition-probe-research
git pull --ff-only origin codex/partition-probe-research
$ResearchPython = ".\.venv-research\Scripts\python.exe"
& $ResearchPython -m pip check
& $ResearchPython -m pytest tests/test_probe_workloads.py tests/test_probe_analysis.py tests/test_probe_runner.py tests/test_probe_pilot.py tests/test_probe_supervisor.py tests/test_probe_diagnostics.py tests/test_probe_export.py
```

Stop if the working tree has unexplained changes, the environment is missing, or checks fail. Keep the existing environment if it works; do not reinstall the archived requirements verbatim because its editable Git line points to an old revision. If setup/package changes are needed, complete them and rerun the checks before preparing Stage A.

The tests include tiny real Dask success and forced timeout checks, durable evidence after cleanup, scalar correctness, paired-data invariants, resume protection, and log classification fixtures. **Fixtures do not prove physical nanny-memory termination detection.** Check the raw nanny log against the first actual pressure/restart observation during Stage A. If capture is broken, pause and fix it in a separately versioned experiment; keep the partial evidence.

No tests in this update have been executed on the Mac. Earlier passing test counts refer to earlier code, not this update.

## 2. Prepare once, on Windows

At least 10 GiB must be free on both the experiment drive and Windows temporary drive before preparation and each new cell. Worker-memory/headroom checks are additional safeguards. Free-space checks are prerequisites, not a worst-case spill reservation.

```powershell
$StageADir = "data/probes/windows-stage-a-v1"
& $ResearchPython -m experiments.probe_pilot prepare --preset windows-stage-a --out-dir $StageADir
& $ResearchPython -m pip freeze | Out-File -Encoding utf8 "$StageADir/requirements.txt"
git rev-parse HEAD | Out-File -Encoding utf8 "$StageADir/revision.txt"
```

Confirm preparation reports exactly **48 cells**, eight instances, `methods: ["full"]`, seed 911 in recipes and order seed 20261115. The output directory must be new/empty. Do not overwrite or edit a prepared plan. The runner refuses changed research source or changed recorded Python/platform/package versions on resume. Save the full package snapshot too; the automatic environment comparison covers the principal runtime/generator packages, not every dependency or Windows power setting.

## 3. First batch, inspect, then resume

```powershell
& $ResearchPython -m experiments.probe_pilot run --plan "$StageADir/plan.json" --max-runs 4
& $ResearchPython -m experiments.probe_pilot analyze --plan "$StageADir/plan.json"
```

After the first four attempts inspect `REPORT.md`, `summary.json`, raw `runs.jsonl`, and `diagnostics/<cell-id>/<run-id>/`. Expected software conditions:

- Every attempted cell has one retained outcome, including failures and interruptions.
- `owned_descendants_alive_after_cleanup` is zero; no other experiment is running.
- Successful jobs have worker samples, active memory thresholds, graph information, phase times, and logs. Raw evidence remains after temporary spill files are deleted.
- Nanny memory messages, worker exit codes/signals and scheduler add/remove events are available when emitted. Missing/partial logs stay explicit. A signal or `KilledWorker` alone stays an unknown cause.
- Power-condition flags, startup/cleanup errors, log write errors or truncation trigger review. The batch stops on these conditions; a workload execution error or timeout remains an outcome, not an automatic retry.

When collection is sound, resume the **same** plan in bounded batches:

```powershell
& $ResearchPython -m experiments.probe_pilot run --plan "$StageADir/plan.json" --max-runs 8
& $ResearchPython -m experiments.probe_pilot analyze --plan "$StageADir/plan.json"
```

Repeat after review until 48 outcomes are recorded. `--max-runs` counts only new cells. Failed/timeout/interrupted recorded cells are skipped on resume. Ctrl+C is recorded when the supervisor can handle it. If the terminal/host is killed before row persistence, an `attempts/<cell-id>.json` marker blocks silent retry. Preserve the marker and raw evidence for reconciliation; do not simply delete the marker or stale lock and relaunch. A marker may also represent a preflight rejection before spawn: establish that from evidence before deciding whether any physical attempt occurred.

Power/RAM/disk snapshots are sampled around every second plus before/after each run; short changes can be missed. The collector does not automatically change Windows power settings or prevent OS sleep. Condition-affected attempts remain visible; replacement runs require a declared amendment, not overwriting.

## 4. Evidence and accounting contract

Each physical run stores `attempt.json`, progress/outcome snapshots, supervisor/nanny and worker JSONL logs, scheduler events, host conditions and per-worker lifetime measurements. File hashes are recorded after cleanup. These are **local raw evidence**, potentially containing paths, addresses and process IDs; keep them under ignored `data/probes/` and review before sharing. Worker logs begin at plugin registration; earlier worker startup messages may be absent. Supervisor/nanny logging starts before cluster setup. Abrupt death can truncate evidence. Logs are capped at 16 MiB per process with explicit truncation.

`failure_category` is a conservative evidence summary; original `status` and error remain. `worker_death_with_nanny_memory_termination_evidence` means a nanny memory-termination message occurred before cleanup in that attempt with `KilledWorker`; it does not establish that every worker death had the same cause. OS OOM requires external Windows evidence and is never inferred from an exit code alone. Successful attempts can still have memory terminations/restarts.

Timing fields:

- `execution_seconds` preserves the old graph-build-plus-compute scope; `graph_build_seconds` and `compute_seconds` are **nested components**, not extra time to add.
- Setup, telemetry flush, child cleanup, supervisor finalization and scratch cleanup are separate. Finalization includes forced termination and diagnostic summarization.
- `unattributed_seconds` retains spawn/import/bookkeeping and any unreported partial phase after forced termination. It is not “pure spawn time.”
- `total_seconds` is the supervised lifecycle plus finalization; `end_to_end_seconds` adds per-run preflight. Failed attempts still incur their measured elapsed cost.
- Dataset preparation is shared, in the plan/manifests; verification and row persistence are shared collection costs in `batches.jsonl`. Do not charge a shared cost once per repeat, add nested timing twice, or treat collected timing as an executed online controller.
- Per-worker baseline RSS is before workload submission, after plugin setup; it is not a true idle/empty-process baseline. Summed lifetime peaks are not concurrent cluster memory or one worker's headroom.

## 5. Complete, export, then decide

```powershell
& $ResearchPython -m experiments.probe_pilot analyze --plan "$StageADir/plan.json"
& $ResearchPython -m experiments.export_probe_evidence --plan "$StageADir/plan.json" --out reports/research_stage_a_windows_v1
```

The export directory must be empty. Preserve full local raw evidence. Publish the compact export, package/revision snapshot, Windows test output and a short session note; inspect content before committing. The report includes all 16 recipe/config groups, missing attempts, statuses, spill-positive versus unknown observations, nanny evidence and power flags. Successful scalar results must agree across configurations/repeats for a given instance; agreement is not a large-input correctness proof.

Review these questions with the results:

1. Are pressure/deaths reproducible within a setting, with useful evidence and stable conditions?
2. Does skew or file imbalance change outcomes at fixed concurrency? Does the 2 GB setting remove the issue?
3. Are signals observable cheaply before a full run, or are they only retrospective explanations?

**Stop after Stage A for interpretation.** No automatic Stage B, classifier or training. A repeatable mechanism permits proposing up to 96 probe attempts on these same declared instances; a useful fidelity signal and plausible economics are further gates. Two additional seeds (at most 288 further attempts) are conditional. An adaptive controller still needs to beat fixed/metadata and generic staged-probing baselines at matched completion, after paying all profiling costs. The broader decision framework is in [POST_SCREEN_PLAN.md](POST_SCREEN_PLAN.md).
