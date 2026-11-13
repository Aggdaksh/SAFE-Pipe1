# Windows research screen: partial checkpoint

**Recorded:** 2026-11-13 on Ganant's original Windows experiment PC. **Branch/source revision:** `codex/partition-probe-research` at `2419360`. This is the **development** screen, separate from the original main-v1 96-run study and from any future untouched final evaluation.

The prepared plan has **12 instances × 8 configurations × 4 methods × 2 repeats = 768 cells**. The first four plus a bounded 32-cell batch recorded **36 successes**. The plan and local raw log remain in ignored `data/probes/windows-screen-v1/` on this PC. The prepared datasets and probes occupy **3.39 GiB**; `runs.jsonl` and the other top-level run files were under 1 MB at this checkpoint. About **63 GiB** remained free on C: after the batch. Temporary Dask spill files may require additional space during individual jobs and are not represented by the retained dataset size.

**Power-state limitation discovered after the batch:** the PC reported 100% battery with `power_plugged=False`. Power source was not recorded before each of these 36 cells. Preserve them as Windows diagnostics, but do not combine them with later mains-powered cells into a controlled ranking comparison. A fresh independent plan should be prepared after mains power is verified. This will generate another set of data files; the old directory stays intact for provenance.

The [measurements](measurements.csv), [frozen plan](plan.json), [summary](summary.json), [generated report](REPORT.md), [package list](requirements.txt), [revision](revision.txt) and [session notes](SESSION_NOTES.md) preserve this checkpoint. The compact export excludes generated Parquet, raw JSONL and worker addresses/PIDs; it is not a full backup. Do not combine these rows with the separate incomplete Mac plans to make a complete comparison.

## Observed checks

- The separate `.venv-research` environment passed **43 targeted research tests** on Windows; the full suite also exited successfully with three skips. A separate tiny Windows smoke plan completed **16/16 successful cells** with worker memory samples and zero owned descendants after cleanup.
- All **36 screen cells** succeeded, had non-null sampled worker RSS telemetry, and reported zero owned descendants after cleanup. The run lock was absent after the batch.
- **Three cells** sampled positive stored disk spill. The largest was `skewed_join-2000000-uneven`, `full`, `w1_t2_1g`, repeat 1: about **1.17 GB summed sampled spill peaks across observed worker lifetimes**. The run returned success but showed **at least two worker restarts** (three worker lifetimes observed for a one-worker configuration). Its summed RSS peaks are not a concurrent cluster peak. Two group-by partition-tail cells showed about 1-2 MB sampled spill.
- The [generated report](REPORT.md) marks every method-ranking comparison incomplete. No proxy fidelity, spill reduction, adaptive-policy saving, novelty or deadline guarantee follows from these partial cells.

## Continue on the same PC

The command below resumes the existing plan for **diagnostic work only**. For a comparable full study, connect mains power, verify `power_plugged=True`, choose a new empty output directory, prepare a new plan, and record power state before and during each batch. Do not silently replace the first 36 rows.

```powershell
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot run --plan data/probes/windows-screen-v1/plan.json --max-runs 32
.\.venv-research\Scripts\python.exe -m experiments.probe_pilot analyze --plan data/probes/windows-screen-v1/plan.json
```

Inspect all new statuses, sampled spill, worker restarts, available host memory and cleanup before the next batch. Preserve failures and interruptions. Re-export into a **new empty directory** at a later checkpoint; the exporter does not overwrite this snapshot. See the [Windows handoff](../../docs/research/WINDOWS_HANDOFF.md) and [research protocol](../../docs/research/PROBE_PROTOCOL.md).
