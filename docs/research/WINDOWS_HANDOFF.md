# Research experiments on the Windows PC

Prepared 2026-11-02; Windows checkpoint added 2026-11-13. Branch: `codex/partition-probe-research`.

The current Mac is for preparation and small correctness checks. Larger benchmarks and any later model training are deferred to the other laptop at the user's request. **Do not merge this branch yet.**

## What is ready

- Reproducible synthetic groupby/join inputs, uniform probes and an experimental partition-weighted probe.
- Four matched methods, frozen plans and data/source hashes, randomized run order and resumable batches.
- Fresh local Dask processes, memory/spill telemetry, host-memory guard, timeout cleanup and explicit failure records.
- Descriptive comparisons and compact evidence export.

This is an experiment framework. The adaptive probe-selection algorithm and reliability model are not implemented or trained. Existing production models are unchanged. See [protocol](PROBE_PROTOCOL.md) and [current evidence](../../reports/research_probe_v1/README.md).

## Current Windows checkpoint (2026-11-13)

This PC pulled the research branch at `2419360`, installed a separate ignored `.venv-research`, and passed all **43 targeted research tests**. A new Windows smoke plan recorded **16/16 successes**, memory samples and zero owned descendants after cleanup. A `windows-screen-v1` plan was prepared on this PC; its datasets and probes occupy **3.39 GiB**. The first four and next 32 cells recorded **36/768 successes** with zero owned descendants and no stale run lock. Three cells showed sampled positive stored spill; one full two-million-row join at `w1_t2_1g` showed at least two worker restarts despite a successful final result. A later power check reported the laptop unplugged, and power source was not recorded per cell. These are diagnostic observations, not comparable method rankings. See the [compact checkpoint](../../reports/research_probe_windows_v1_partial/README.md).

The second plan, `data/probes/windows-screen-mains-v1/`, began after mains was verified and records power/RAM/disk about every two seconds. It now has **68/768 cells: 66 successes, one 180-second timeout and one execution error**. The timeout had a sampled 44-second unplugged interval. After charger confirmation, the next 32 cells had stable sampled mains, but a full uneven two-million-row join at `w2_t1_1g` ended with `KilledWorker` after repeated worker deaths. Cleanup completed. The monitor stopped for inspection; keep the ambiguous `execution_error` label and inspect it before another batch. See the [monitored checkpoint](../../reports/research_probe_windows_mains_v1_partial/README.md). Do not overwrite failures or create another dataset merely to erase them.

On this PC, resume the existing second plan with its saved environment and `advance.py` controller. It limits batches to 32, samples conditions, keeps Windows awake during execution, and stops between batches on unreviewed failures, cleanup leftovers, power loss or low disk. Creating `pause.requested` in the run directory requests a stop at the next batch boundary. Remove that marker only when deliberately resuming. Full screen completion and independent final evaluation remain pending; any clean follow-up must declare a separate design and retain the flagged power interval in this study.

After review of the recorded timeout and `KilledWorker`, the controller now accepts `--continue-reviewed-failures` to retain those contained outcomes and advance other cells. It still stops on interruptions, unknown errors, cleanup leftovers, power/disk violations and command failures. See [completion and next decisions](NEXT_STEPS.md) for the resume command, completion audit and research decision gates. Stable mains is required before starting.

## 1. Get the branch and environment

Use PowerShell on Windows. Run these commands yourself on the experiment laptop; they are instructions, not jobs already launched remotely.

For a new checkout:

```powershell
git clone --branch codex/partition-probe-research https://github.com/Aggdaksh/SAFE-Pipe1.git
cd SAFE-Pipe1
```

For an existing checkout, first check `git status`. Preserve any local changes before switching:

```powershell
git fetch origin
git switch codex/partition-probe-research
git pull --ff-only origin codex/partition-probe-research
```

Create a separate environment using an installed Python 3.11 or newer:

```powershell
py -3 -m venv .venv-research
.\.venv-research\Scripts\python.exe -m pip install -e ".[dev,dask]"
```

This environment needs no LightGBM training or GPU. `.venv-research/` is ignored by Git. Do not update code or packages halfway through a plan. The runner checks research source hashes; it does not enforce a package lock or identical machine state. Keep one plan on one machine and environment. Save the environment below.

Windows execution is now verified for the targeted tests, tiny smoke and first 36 screen cells recorded above. On any different Windows checkout or after changing research source files, start with small checks again and prepare a new plan. The old Mac results are not Windows validation.

## 2. Small checks first

```powershell
.\.venv-research\Scripts\python.exe -m pytest tests/test_probe_workloads.py tests/test_probe_analysis.py tests/test_probe_runner.py tests/test_probe_pilot.py tests/test_probe_supervisor.py

$SmokeDir = "data/probes/windows-smoke-v1"
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot prepare --preset smoke --out-dir $SmokeDir
.\.venv-research\Scripts\python.exe -m pip freeze | Out-File -Encoding utf8 "$SmokeDir/requirements.txt"
git rev-parse HEAD | Out-File -Encoding utf8 "$SmokeDir/revision.txt"
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot run --plan "$SmokeDir/plan.json" --max-runs 16
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot analyze --plan "$SmokeDir/plan.json"
```

Expected: 16 recorded successes, sampled worker memory and no owned worker descendants after cleanup. The tests compare tiny Dask results against independent pandas results and check timeout containment. Smoke rankings are not paper results. Stop and investigate any failed check before scaling up.

## 3. Prepare the development screen on Windows

The screen has 12 instances × 8 configurations × 4 methods × 2 repeats = **768 physical jobs**. This is a substantial benchmark, not 768 training iterations. Preparation also generates and reads data: do it on the experiment laptop.

The eight target configurations combine workers `{1, 2}`, threads per worker `{1, 2}` and worker caps `{1 GB, 2 GB}`. Each job starts a fresh cluster. Largest aggregate target cap is 4 GB, plus required host headroom. Local disk space is needed for generated Parquet, sample copies, logs and temporary spill files.

```powershell
$RunDir = "data/probes/windows-screen-mains-v1"
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot prepare --preset windows-screen --out-dir $RunDir
.\.venv-research\Scripts\python.exe -m pip freeze | Out-File -Encoding utf8 "$RunDir/requirements.txt"
git rev-parse HEAD | Out-File -Encoding utf8 "$RunDir/revision.txt"
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot run --plan "$RunDir/plan.json" --max-runs 4
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot analyze --plan "$RunDir/plan.json"
```

Inspect `REPORT.md`, `summary.json` and `runs.jsonl`. Incomplete comparisons are expected after four jobs. Check statuses, measured telemetry, errors and cleanup. If the host is suitable and the checks pass, continue in bounded batches:

```powershell
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot run --plan "$RunDir/plan.json" --max-runs 32
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot analyze --plan "$RunDir/plan.json"
```

Repeat that pair to advance the same frozen plan. `--max-runs` means new cells in this invocation. Do not run two invocations against one plan concurrently. Use mains power and keep power mode/background activity consistent; record the conditions in `$RunDir/SESSION_NOTES.md`. Avoid sleep during a batch.

## 4. Stop, resume and keep the evidence intact

- Prefer letting a small batch finish. Ctrl+C during a supervised job is handled as an interrupted attempt: owned children are stopped, a row is saved, and the batch stops. Avoid repeated Ctrl+C during cleanup.
- A later `run` continues pending cells. It never silently retries a recorded failure/interruption. Those outcomes stay in the analysis, and a comparison needing the failed cell remains unevaluable. If a rerun is justified, declare a new independent plan and retain the original.
- Host-memory refusal happens before execution and leaves that cell pending. Close unrelated memory-heavy apps and resume; do not bypass the guard.
- A code/data hash mismatch requires a fresh output directory and newly prepared plan. Do not edit hashes, merge rows from different plans or try to resume the archived Mac plans with newer code.
- A hard crash/power loss can leave `.running.lock` or a partial last JSONL line. The runner stops rather than guessing. Preserve the files and investigate. Remove a stale lock only after confirming its recorded process and owned workers are gone; check the PID's command because PIDs can be reused. Do not broadly kill unrelated Python processes or silently delete failure evidence.

## 5. Export and return results

Use a new empty export directory each time:

```powershell
.\.venv-research\Scripts\python.exe -m experiments.export_probe_evidence --plan "$RunDir/plan.json" --out reports/research_probe_windows_v1
Copy-Item "$RunDir/requirements.txt" reports/research_probe_windows_v1/requirements.txt
Copy-Item "$RunDir/revision.txt" reports/research_probe_windows_v1/revision.txt
```

Also retain the original `runs.jsonl`, manifests and datasets locally. The compact export contains measurements, plan and summary; it is not a complete raw-data backup. Include any session notes when sharing results. Review the small export before committing it; generated data stays under ignored `data/probes/`.

## Research decision after the screen

1. Check whether full runs show meaningful memory pressure/spill. Without that, do not claim a memory-pressure contribution.
2. Check whether uniform sampling changes configuration rankings beyond repeat noise, and whether simple memory scaling already fixes it.
3. Check whether the partition heuristic helps relative to the **same-memory, same-fact-row-budget** uniform baseline. It uses input file size, not measured post-shuffle cost.
4. Investigate promising or contradictory cases with a declared follow-up design separating input imbalance, key skew, size and seed. Two repeats and coupled patterns are exploratory evidence.
5. Only if a useful gap remains, implement the adaptive policy. Evaluate total request cost including sample preparation, probes and a fresh selected full run on separate instances. Train a reliability model only if the design needs it and sufficient independent data exists.

The branch may produce a negative result. Novelty and paper readiness require evidence and another comparison against the closest literature; the framework alone is not the contribution.
