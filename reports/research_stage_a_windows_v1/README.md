# Stage A: Windows mechanism study completed

Completed 2026-11-15 on the original Windows experiment PC, research revision `73de101`. The study follows the frozen [Stage A specification](../../configs/research_stage_a_v1.json): two families, four separate skew/imbalance patterns, two memory caps at fixed concurrency, and three runtime repeats. **All 48 attempts are retained: 41 successes and seven execution errors.** No Stage B runs or model training were launched.

## Windows validation and collection audit

The existing research environment passed `pip check` and **54 targeted tests** before preparation. See [validation output](WINDOWS_VALIDATION.md), [package snapshot](requirements.txt), [revision](revision.txt), and [session notes](SESSION_NOTES.md).

The [completion audit](completion_audit.json) verifies all 48 planned identities, all eight dataset directories and frozen manifest identities, source/environment/protocol identity, and **546 durable diagnostic file hashes**. It verifies **37 raw nanny memory messages** against their saved source logs. All per-run power flags are empty, all 336 retained condition samples report mains when a battery is present, no unresolved attempt marker or run lock remains, and every record reports zero owned descendants after cleanup. Successful scalar values agree within each instance across configurations/repeats; this is a consistency check, not an independent large-input correctness proof.

## Observed outcomes

Both settings use two workers and one thread per worker. Memory below is the decimal limit **per worker**. Each table entry represents three attempts on one generated instance.

| Family | Input pattern | Successes at 1 GB | Successes at 2 GB |
| --- | --- | ---: | ---: |
| Groupby | Balanced | 3/3 | 3/3 |
| Groupby | Key skew only | 3/3 | 3/3 |
| Groupby | File imbalance only | 0/3 | 3/3 |
| Groupby | Both | 3/3 | 3/3 |
| Join | Balanced | 3/3 | 3/3 |
| Join | Key skew only | 3/3 | 3/3 |
| Join | File imbalance only | 2/3 | 3/3 |
| Join | Both | 0/3 | 3/3 |

Every execution error has **Dask nanny memory-termination evidence before cleanup**, retained as `worker_death_with_nanny_memory_termination_evidence`. This is stronger diagnosis than the older screen's unknown worker-death labels, but it does not establish Windows OS OOM or that every worker death shared one cause.

Nine attempts had nanny memory-termination messages, including two jobs that ultimately succeeded. Twelve attempts sampled positive stored spill. All 24 attempts at 2 GB succeeded without sampled spill or nanny termination; balanced and skew-only patterns also succeeded at 1 GB without those observations. Missing and zero telemetry remain distinct in the [generated report](REPORT.md).

These observations are consistent with input-file imbalance contributing to pressure on this host, including without hot-key skew. They do not support a simple monotonic rule: groupby's combined pattern succeeded three times while imbalance alone failed three times, and the imbalance-only join had mixed outcomes. Keep family and factor interactions visible. One generation seed and three runtime repeats do not establish general failure probabilities, a portable memory predictor, or an adaptive-policy improvement.

## Evidence and storage

- [Measurements](measurements.csv), [plan](plan.json), [summary](summary.json), and [mechanism report](REPORT.md).
- [Audit output](completion_audit.json) and [reproducible audit script](audit_stage_a.py).
- [Windows validation](WINDOWS_VALIDATION.md), [environment](requirements.txt), [revision](revision.txt), and [session conditions](SESSION_NOTES.md).

Generated Parquet, complete raw records, and per-attempt logs/events/snapshots remain in ignored `data/probes/windows-stage-a-v1/`. Input data occupies **2.53 GiB**, reused for all attempts. Retained raw diagnostics occupy about **1.24 MB**. The compact export is not a raw-data backup. Original main-v1 data/models and the completed 768-attempt screen remain separate.

The included `run_batch.py` archives the local awake-state launcher. Its relative paths target the original ignored run directory; it should not be launched from this export. The completed plan has no pending attempts.

Reproduce the audit from the repository root with the original raw directory available:

```powershell
.\.venv-research\Scripts\python.exe reports/research_stage_a_windows_v1/audit_stage_a.py --run-dir data/probes/windows-stage-a-v1 --out-dir reports/research_stage_a_windows_v1
```

## Interpretation gate

Stage A collection and instrumentation checks are complete. Review whether these factor-specific outcomes motivate the proposed bounded probe study, identify what a cheap probe could observe before a full run, and account for its cost against strong fixed/metadata baselines. Stage B requires a declared plan after this interpretation; the larger 432-attempt ceiling is conditional. No automatic further experiments, classifier, or main merge are implied. See the [post-screen plan](../../docs/research/POST_SCREEN_PLAN.md).
