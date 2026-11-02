# Research preparation status

Updated 2026-11-02. Isolated branch: `codex/partition-probe-research`. Main and the production advisor/models have not been changed by this research work.

## Recorded work

| Export | Planned cells | Recorded outcomes | Interpretation |
| --- | ---: | --- | --- |
| [Tiny smoke](smoke/REPORT.md) | 16 | 16 successes | Software diagnostics; all 16 scalar results were checked against independent pandas calculations on the corresponding six datasets. |
| [Mac development, partial](mac_64_partial/REPORT.md) | 64 | 1 success | Next larger-memory cell was refused by the available-memory guard before execution. |
| [Mac limited, partial](mac_32_partial/REPORT.md) | 32 | 10 successes | Stopped when the user moved larger experiments to the other laptop. |

The partial studies are separate plans; their 11 completed rows must not be pooled into a complete comparison. No partial large-study comparison satisfies the analyzer's all-candidates/all-repeats requirement.

Two full groupby runs in the Mac-limited plan did record disk spill: `w1_t1_1g` repeat 1 had a sampled peak of 71,066,898 bytes, and `w1_t2_1g` repeat 1 had 92,031,812 bytes. Both observed one worker lifetime, so these values are that worker's sampled peak stored spill, not cumulative bytes written. The remaining completed rows had observed zero stored spill. This demonstrates pressure in those two executions only; one repeat does not establish a stable ranking or a benefit from the probe method. See the corresponding rows in [measurements](mac_32_partial/measurements.csv).

The Mac-limited study also had **one physical attempt interrupted without a JSONL result row**: cell `726c633522f5d7f81b23d33c`, groupby/uniform, `w1_t1_1g`, repeat 1. The older supervisor cleaned up its processes but propagated the interrupt before recording it. This is an explicit evidence gap, not an unattempted success or timeout observation. The current supervisor and CLI now retain an `interrupted` row and stop the batch; a small persistence/resume test covers the CLI behavior. The archived measurements are not rewritten to invent the missing observation.

An earlier directory `research-mac-20261031` was prepared but never run. It has no measurements and is not exported here. Source changes after preparation mean these historical Mac plans should not be resumed using the current implementation. Prepare a new plan on Windows.

## Provenance and limits

The current Mac reported 16 GiB physical RAM. Each export includes available environment/version information and plan hashes. The first tiny smoke predates the source-fingerprint and UTC-timestamp additions: it lacks those fields and is suitable only as a recorded software diagnostic. Later plans contain source hashes, but their measurements still describe partial development studies.

Exports exclude generated Parquet and per-worker addresses/PIDs. Complete raw records and data remain in ignored local experiment directories. `measurements.csv` is a compact view, not a replacement for all raw evidence. Source snapshots for the pre-commit pilot are not archived here; file hashes identify versions but cannot reconstruct them.

Validation on this Mac: the 120-test suite (79 original + 41 research checks at that point) passed before the final handoff additions. The two added tests also passed on 2026-11-02: they exercise interruption persistence/resume and refusal after source changes without running Dask jobs. CLI help checks passed. The core runner has not changed since the full-suite check; final changes add tests/docs and normalize exported CSV line endings.

**Not established:** a unique algorithm, an adaptive controller, a trained reliability model, statistically supported ranking improvements, end-to-end savings or a publication-ready result. No new model was trained. Larger experiments are deferred to the other laptop.

Next steps and commands: [Windows handoff](../../docs/research/WINDOWS_HANDOFF.md). Experimental design and nearest literature: [protocol](../../docs/research/PROBE_PROTOCOL.md).
