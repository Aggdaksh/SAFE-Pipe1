# Windows research screen session notes

- Date: 2026-11-13 (Asia/Kolkata).
- Source branch/revision: `codex/partition-probe-research` at `2419360`; exact revision saved in `revision.txt`.
- Environment: ignored `.venv-research`; package list saved in `requirements.txt` before execution.
- Host: original Windows experiment PC, 31.4 GiB physical RAM. Available RAM before the first batch was about 12.5 GiB.
- Power scheme: Windows `Balanced` (`381b4222-f694-41f0-9685-ff5bb260df2e`). Mains/battery state was not verified.
- Prepared datasets and probes: 3.39 GiB on disk after plan preparation; about 63.3 GiB free on C: at that point.
- Background activity and OS file-cache state were not controlled or flushed. Keep those limitations in comparisons.
- The 16-cell Windows smoke plan completed separately with 16 successes and no owned worker descendants remaining; smoke results are software diagnostics.

## First screen checkpoint

- Ran four cells, then one bounded 32-cell batch: 36/768 recorded successes.
- All 36 cells have sampled RSS telemetry and zero owned descendants after cleanup; no run lock remained.
- Three cells sampled positive stored spill. The largest was a full two-million-row uneven join at `w1_t2_1g`, with about 1.17 GB summed sampled spill peaks across worker lifetimes and at least two worker restarts. This is one exploratory run, not a ranking conclusion.
- After the batch, the prepared datasets were still 3.39 GiB and C: had about 63 GiB free. Top-level run files were under 1 MB. Temporary spill storage is additional and short lived.
