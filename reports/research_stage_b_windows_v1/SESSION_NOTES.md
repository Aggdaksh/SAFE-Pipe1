# Stage B Windows session

- Started 2026-11-16 on the original Windows PC at source revision `beb8709`; full Git revision and packages saved before physical collection.
- Existing research environment retained unchanged. `pip check` passed and 74 targeted tests passed (64 existing pandas/Dask deprecation warnings). Full captured test output is retained in `WINDOWS_TEST_OUTPUT.txt`.
- Before preparation: mains connected, battery 100%, about 44.7 GiB free disk and 6.9 GiB available RAM. Windows power scheme is recorded separately. Background workload and filesystem cache are not controlled; source/sample verification may warm caches.
- Preparation verified the exact pinned Stage A plan, all 48 full outcomes including failures, source/operator compatibility, input hashes and retained diagnostic evidence. No Stage A full job was rerun or data regenerated.
- Prepared 16 deterministic, non-nested samples shared across two target caps and three repeats: 96 planned probe attempts. Join samples retain the full dimension relation; fact-row fractions are not total memory fractions.
- The Stage B CLI requests system-awake state during preparation/run, restoring it afterward, and preserves its per-cell resource/source/environment/power/diagnostic safeguards.
- Inspect first four attempts, then batches of at most eight. Preserve every failure/unknown and stop for infrastructure, condition or logging issues. Stop after 96 for interpretation; no Stage C, extra seeds or training is scheduled.

## Completion

- Finished all 96 planned probes on 2026-11-16 at 00:20:51 IST. Every attempt succeeded and was classified quiet, with no unknown/quality-flagged rows or scalar inconsistencies. No cells were selectively rerun.
- Reviewed the first four, then batches of eight and a final four. All gates remained clean. Later console output was retained in timestamped local `console_*.txt` files; per-attempt raw diagnostics are independently retained by the collector.
- Final analyze/audit passed: 16 sample directories, 961 diagnostic-file hashes, zero quality flags and zero owned cleanup survivors; no pending markers or run lock. Raw nanny-memory message count is zero for these probes.
- All 32 reference/probe comparison groups are eligible. Eight are false-reassurance candidates; none are unnecessary-warning candidates. These are correlated development groups, not calibrated classifier rates.
- Both fraction-specific probe-choice replays selected the 1 GB target setting on all eight instances, mapping to 17/24 successful historical full outcomes. Fixed 2 GB and file-metadata replays each map to 24/24 successes. These full jobs were not executed again.
- Median profiling cost (six probes plus preparation once) is 24.62 s for 1/8 and 26.38 s for 1/4. Same-cohort fixed-2-GB historical full lifecycle plus preflight has a median per-instance value of 4.96 s; controller/metadata overhead is unmeasured. No online saving is established.
- Samples remain 1.04 GiB; retained raw diagnostics about 1.81 MB. About 43.6 GiB remained free on C:. Stopped after Stage B; no Stage C, extra seeds, model training or main merge.
