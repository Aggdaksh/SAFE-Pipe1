# Completed Windows development screen

**Completed:** 14 November 2026, 00:08 IST, on Ganant's original Windows experiment PC. **Recorded:** all **768/768 planned attempts**, with **759 successes, one timeout and eight execution errors**. No benchmark remains running. This is a completed development experiment; independent final evaluation and any adaptive policy remain future work.

## Completion and integrity

The matrix is 12 input instances (two families, three sizes, two patterns), eight configurations, four methods, and two repeats. The [completion audit](completion_audit.json) verified all planned identities exactly once, no missing cells, matching research source hashes, the frozen manifest identities, and file hashes for all 36 physical dataset/probe directories. Every record reports zero owned descendants after cleanup; no run lock remains. Source revision, package list, and the controller are retained with this export.

All nine unsuccessful outcomes occurred on **full inputs** at **1 GB per worker**, within the two largest uneven instances. The eight execution errors contain Dask `KilledWorker` after repeated worker deaths; this is not confirmation of OOM. Their original labels remain. The timeout is a censored outcome, not a 180-second successful runtime. All three probe methods completed their jobs successfully, so these small probes did not reveal the full inputs' observed failures in this screen. This is an exploratory reliability observation, not an independently validated risk predictor.

The first timeout overlaps the known power interruption. The [condition audit](condition_audit.csv) conservatively flags that one cell using adjacent power samples within five seconds of execution; all runs had condition-sampling coverage under a ten-second maximum-gap check. Later batches reported stable sampled mains. Sampling cannot prove that no shorter transient occurred. The failed full-reference group is already unevaluable under the original analysis rule; the power flag is preserved explicitly.

## What the ranking comparison shows

Ten of 12 instances meet the original all-candidates/all-repeats success requirement. The two largest uneven instances remain **unevaluable for numerical rankings**, with every failure retained. Each row below summarizes the same ten eligible instances.

| Probe method | Median selected full-engine regret |
| --- | ---: |
| Uniform sample, target worker memory | 3.87% |
| Uniform sample, scaled worker memory | 0.11% |
| Partition-tail sample, same scaled worker memory | 8.17% |

Regret is the selected configuration's median full-input engine runtime divided by the best observed configuration's median runtime, minus one. A lower value is better. The best observed setting uses only two repeats and is a noisy hindsight reference. These are engine-time results; preparation, paid probes and a fresh selected full execution have not been evaluated as an online request.

Against matched-memory uniform sampling, partition-tail has lower selected full-engine regret on **two** instances, equal regret on **three**, and higher regret on **five**. This screen provides **no basis to claim that the partition heuristic is better overall**. Many pair orders are unresolved under the original range/gap rule. Pair counts share workloads and are not independent statistical samples; these results do not establish significance, a universal winner, cost savings or novelty.

Worker telemetry sampled positive stored spill in **30/768 cells** and observed restarts in **13/768 cells**. Stored-spill and RSS peak sums span worker lifetimes; they are not concurrent cluster peaks. Pressure is demonstrated in particular executions, while the proposed sampling benefit remains unproven.

## Evidence and storage

- [Measurements](measurements.csv), [frozen plan](plan.json), [generated report](REPORT.md), and [summary](summary.json).
- [Conditions](conditions.jsonl), [per-cell condition audit](condition_audit.csv), [completion audit](completion_audit.json), and [audit script](audit_completion.py).
- [Requirements](requirements.txt), [source revision](revision.txt), [session notes](SESSION_NOTES.md), and [batch controller](advance.py).

Full raw JSONL and generated Parquet remain under ignored `data/probes/windows-screen-mains-v1/`. This compact export is not a raw-data backup. Current prepared inputs use about **3.39 GiB**; the separate earlier diagnostic plan uses another **3.39 GiB**. These fixed inputs were reused for all 768 attempts. Approximately 59.5 GiB remained free on C: at the completion check. The original main-v1 96-run data and LightGBM artifacts are unchanged.

Reproduce the audit from the repository root with the original local raw directory available:

```powershell
.\.venv-research\Scripts\python.exe reports/research_probe_windows_mains_v1_complete/audit_completion.py --run-dir data/probes/windows-screen-mains-v1 --out-dir reports/research_probe_windows_mains_v1_complete
```

## Next decision

Review failure/restart evidence and repeat noise before proposing an algorithm. A focused, independently declared follow-up should separate key skew, input imbalance, size and seed, and test the full/probe reliability mismatch with better worker-termination diagnostics. If a repeatable gap remains, specify an adaptive probe policy and evaluate its complete request cost on untouched instances. Keep a neutral or negative sampler result in the report. See [next steps](../../docs/research/NEXT_STEPS.md). No new model training, main merge, or paper-ready contribution follows automatically from finishing collection.
