# Stage B: completed Windows probe-fidelity study

**Completed:** 2026-11-16, 00:20:51 IST, on the original Windows experiment PC at source revision `beb8709`. All **96/96 probe attempts succeeded** and were classified **quiet**. There were no warning/unknown probes, quality flags or inconsistent successful results. No benchmark remains active. This is a completed development diagnostic study, not an independently evaluated online policy.

## Validation and provenance

The unchanged research environment passed `pip check` and **74 targeted Windows tests**; the actual [test output](WINDOWS_TEST_OUTPUT.txt) is retained. Preparation verified the exact pinned Stage A plan, all 48 historical outcomes (including seven errors), all full-data inventories, source/environment compatibility and retained diagnostic hashes/nanny events. No full Stage A job was rerun and no full input was regenerated.

Sixteen sample directories were shared across two target caps and three repeats: eight instances x two fractions x two caps x three repeats = 96 attempts. Fractions are 1/8 and 1/4 of fact rows, with non-nested deterministic samples. Join samples retain the entire dimension, so the fractions are not fractions of total working memory. Caps follow the frozen mapping in the [specification](../../configs/research_stage_b_v1.json).

The [completion audit](completion_audit.json) passed: 16 sample directories and **961 retained diagnostic-file hashes** verified, no missing outcomes, pending markers, run lock, cleanup survivors or quality-flagged cells. No nanny memory-termination messages were observed in these probes. Timing, condition, sampling and logging limitations remain those of the protocol; absence of sampled signals does not establish zero risk.

## Quiet samples did not warn about full-scale pressure

All **32 comparison groups** have the required three known probes and three known full references. **Eight groups** are false-reassurance candidates; none are unnecessary-warning candidates. These eight groups represent four instance/1-GB-target combinations at two fractions:

- Groupby with both factors: full jobs succeeded, but recorded spill/memory pressure.
- Groupby with file imbalance only: all three full jobs failed.
- Join with both factors: all three full jobs failed.
- Join with file imbalance only: full outcomes were mixed, two successes and one error, with pressure.

Thus a quiet small probe was insufficient to identify the historical full-input pressure under this sampling/cap rule. The groups share instances, and the full/probe repeats occurred in different sessions. These counts are not calibrated classifier false-negative rates or independent samples. See the [full comparison report](REPORT.md).

## Baselines and profiling cost

| Replay rule | Chosen target settings across eight instances | Successful historical full outcomes |
| --- | --- | ---: |
| Fixed 1 GB | 1 GB for all eight | 17/24 |
| Fixed 2 GB | 2 GB for all eight | 24/24 |
| File-metadata rule | 1 GB for four, 2 GB for four | 24/24 |
| Probe choice at 1/8 | 1 GB for all eight | 17/24 |
| Probe choice at 1/4 | 1 GB for all eight | 17/24 |

Both probe-choice replays found both candidates eligible and selected the lower target cap; no fallback was used. Those choices did not improve historical completion over fixed 1 GB. Full outcomes remain mixed or unsuccessful where observed; successful-time medians do not erase the seven errors. For two selected instances all historical full jobs failed, so no successful full/request latency is invented.

Across the same eight instances, median profiling cost is **24.62 s** for 1/8 and **26.38 s** for 1/4. This pays six probe attempts and sample preparation once, before a selected full execution. For context, the median of per-instance median successful historical full lifecycle-plus-preflight times at fixed 2 GB is **4.96 s**. Controller/metadata overhead and preparation resource use are unmeasured. The six-probe diagnostic-sweep replay does not demonstrate economic payback at this scale; it does not test every possible cheaper adaptive policy or a longer-job use case.

The metadata threshold was chosen from Stage A development evidence and frozen before Stage B. Its 24/24 replay is not independent validation, a reliability guarantee or measured online savings. Resource weights express a preference; allocation proxies are not actual RAM use, electricity or currency.

## Evidence and reproduction

[Measurements](measurements.csv), [plan with reference snapshot](plan.json), [summary](summary.json), [report](REPORT.md), [audit](completion_audit.json), [derived findings](findings.json), [review script](review_stage_b.py), [requirements](requirements.txt), [revision](revision.txt), [session notes](SESSION_NOTES.md), and [Windows test output](WINDOWS_TEST_OUTPUT.txt) are included. The review script reads the compact summary and recomputes the descriptive findings; run it with the research Python environment.

Full raw records/logs remain under ignored `data/probes/windows-stage-b-v1/`. Samples occupy **1.04 GiB**, reused for all 96 attempts; raw diagnostics occupy about **1.81 MB**. About 43.6 GiB remained free on C: after collection. This export is not a full raw-data backup.

## Decision gate

The current quiet/warning rule adds no discrimination between these full-pressure cases, and the declared six-probe replay shows no advantage over the strong simple baselines after paying profiling cost. Interpret these findings before declaring any additional experiment. A different signal, cheaper probing scheme or longer-job use case would require a revised, predeclared design and independent evidence. **No Stage C, extra seeds, classifier, model training or main merge was launched.** See the [post-screen decision framework](../../docs/research/POST_SCREEN_PLAN.md).
