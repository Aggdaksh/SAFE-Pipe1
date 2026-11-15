# Stage A Windows session

- Date: 2026-11-15. Source revision `73de101`; exact Git revision and package snapshot saved before execution.
- Original Windows experiment PC; 31.4 GiB physical RAM. Mains verified before preparation; battery was 56%, free disk about 49.3 GiB, available RAM about 7.9 GiB.
- Windows power scheme: Balanced. Background activity and filesystem cache are not controlled. Dataset generation and hash verification can warm the cache.
- Targeted validation: 54 tests passed; `pip check` passed. Existing research environment retained unchanged.
- A new Stage A directory was prepared; historical frozen experiments remain intact and must not resume under this collector revision.
- `run_batch.py` requests system-awake state during each bounded batch, restoring the setting afterward. It invokes the unchanged Stage A CLI, which records per-run conditions and enforces disk, memory, source/environment and diagnostic safeguards. It does not alter Windows power settings.
- Stop after the 48 declared Stage A attempts for interpretation. No later stage or model training is scheduled.

## Completion and review

- All 48 planned attempts completed on 2026-11-15 at approximately 21:21 IST: 41 success, seven execution errors. No failures were retried or replaced.
- The first four attempts verified retained raw nanny evidence: source messages explicitly reported workers exceeding the Dask memory budget before restarting. Continued in batches of at most eight after reviewing diagnostics, conditions and cleanup.
- Completion audit verified all eight input directories, 546 diagnostic-file hashes and 37 raw nanny messages. All 336 retained condition samples showed mains when a battery was present; no per-run condition flags, log write/truncation errors, unresolved attempt markers, scalar inconsistencies or cleanup survivors were found.
- All seven execution errors had nanny memory-termination evidence. Two successful jobs also had such evidence. OS OOM was not established.
- All 24 attempts at 2 GB per worker succeeded. At 1 GB: imbalance-only groupby failed 3/3; both-pattern join failed 3/3; imbalance-only join failed 1/3. Other groups succeeded, including both-pattern groupby with one observed memory-restart run. Keep these differences and the one-seed limitation explicit.
- Paused after Stage A as specified. No Stage B/C, classifier, adaptive controller or model fitting was started. Local dataset footprint is 2.53 GiB and raw diagnostics about 1.24 MB.
- One invocation using PowerShell console redirection returned a nonzero shell result after eight normally completed, persisted cells. Inspected the saved console log, records, diagnostic/condition checks and absence of unresolved markers before advancing; no cells were retried. Subsequent batches used direct invocation and exited successfully. The redirected console is retained as `batch_004.log` locally.
