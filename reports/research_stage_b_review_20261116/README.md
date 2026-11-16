# Post-Stage B compact-evidence review

Reviewed 2026-11-16 against the completed Windows evidence in `3640874`.

- [Interpretation and decision](../../docs/research/STAGE_B_REVIEW.md)
- [Recomputed checks and selections](analysis.json)
- [Read-only input analysis](analyze.py)

Reproduce from the repository root with `python3 reports/research_stage_b_review_20261116/analyze.py` (Windows: use the installed Python command). It uses only the standard library to read committed CSV/JSON/source files and write `analysis.json`. It does not import SAFE-Pipe, run execution tests, generate data, start Dask or train a model. Frozen source checks accept either exact checkout bytes or the recorded Windows CRLF representation; changed experiment source must be reviewed at the evidence revision rather than bypassing the checks.

The analysis independently recomputes selections and costs from CSV rather than trusting the generated summary. It checks compact identities/provenance and agreement with both the Stage A references and Stage B summaries/findings. It cannot re-audit raw Windows diagnostics, physical datasets, sampled worker histories or unexported quality fields.

All 96 probes are quiet successes. Eight of 32 comparison groups disagree with full-scale pressure. Both probe-choice replays select 1 GB for all eight instances (17/24 successful historical full outcomes), while fixed 2 GB and file metadata each select 24/24 successes. Median six-probe plus preparation cost is 24.62/26.38 seconds; the matched fixed-2-GB historical full comparator is 4.96 seconds. These are descriptive development replays, not executed online policies or independent reliability estimates.

The current Stage B gate did not pass. Inspect already-retained individual worker summaries before any revised experiment; no automatic Stage C, training or merge.
