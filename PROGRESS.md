# Progress

**Updated:** 2026-10-28. Canonical memory: [`context.md`](context.md). Windows PC chronology: [`Ganant Work.md`](Ganant%20Work.md).

## Verified work

| Task | Status | Evidence |
| --- | --- | --- |
| Scope, architecture, schemas, optimizer, grid | DONE | `docs/`, `safe_pipe/`, unit tests |
| Windows experiment host, T0, T0b | DONE | ADR-005, `reports/t0.md`, `reports/t0b.md` |
| Four main-v1 Parquet datasets, hashes, SLAs, order | DONE | `configs/datasets_main_v1.json`, `configs/family_sla_main_v1.json`, `configs/matrix_plan_main_v1.json` |
| Dask executor and one-cell collector | DONE for measured path | Tiny integration tests and physical pilots |
| 96 scored Dask runs | DONE | 96 unique rows; `data/curated/runs.csv` |
| Label and pre-run feature audit | DONE | `reports/audit.md`, `data/curated/audit.json` |
| Grouped LightGBM and conformal upper | DONE, small-sample result | `reports/runtime_model.md`, `artifacts/main_v1/` |
| OOD gate | PARTIAL | Conservative family/size rules; no calibrated k-NN with one profile per family |
| Fitted CLI recommendation and same-table baselines | DONE, descriptive | `safe-pipe recommend-model`, `reports/policy.md` |
| Feature-contribution demo figure | DONE | `reports/shap_sort_merge.png`, `reports/shap.md` |
| Technical results draft and separate live Dask demo | DONE as repository draft | `reports/project_i_results.md`, `reports/demo.md` |
| Balanced speed/resource advisor with budgets, reasons and comparisons | IMPLEMENTED; independent physical evaluation pending | `safe_pipe/advisor.py`, `docs/CONFIG_SELECTION.md`, ADR-006 |
| Artifact/profile/grid binding and descriptive mode/weight replay | DONE for frozen main-v1 | `artifacts/main_v1/advisor_support.json`, `reports/advisor_v1/` |
| Worker failure labeling and cluster cleanup regressions | FIXED in code | `safe_pipe/classify.py`, `tests/test_classify.py`, `tests/test_cluster_cleanup.py` |

The original Windows checkpoint recorded **29 passing tests** with `.[dev,dask,ml]` installed. The newer advisor branch passed **79 tests on this Windows PC on 2026-10-28**; balanced, resource and fastest `advise` commands also succeeded here. The Mac regression review is in `reports/advisor_v1/VERIFICATION.md`. Dask tests skip on a coding machine without Dask.

## Measured outcomes

- The selected experiment PC is Windows 11 with 31.4 GiB physical RAM. Dask workers remained capped at 1–2 GB; four datasets were 175–198 MB.
- All **96/96** jobs succeeded and met their frozen family SLAs. This leaves **zero** actionable failure positives; no learned failure model or failure-reduction claim is supported.
- On 8 held-out family/config cells (24 rows), LightGBM MdAPE was **13.84%** versus **23.01%** for the family-median baseline. Conformal upper coverage was **24/24 rows**, with mean width **1.33 s**. These are descriptive small-sample results.
- Same-table policy median normalized cost averaged **7.524** versus **11.421** for default, a **34.1%** lower cost in this table. Some evaluated cells were used for model fitting, so this is not an independent improvement estimate.

## Remaining and limits

- Run the frozen advisor prospectively on the original Windows host. The new 20-scenario mode/weight replay uses existing records; it adds zero physical experiments. See `docs/INDEPENDENT_VALIDATION.md`.
- Broader profile support needs new size/partition/skew profiles, a versioned feature contract, retraining and calibration. The new exact descriptor gate deliberately abstains on changed profiles.
- Department formatting, supervisor review, and formal submission remain outside the verified repository draft.
- Optional TabPFN comparison remains unrun. The formal DTU synopsis/report submission and supervisor decision are outside this repository's verified work.
- The rule-based OOD thresholds are heuristics; only one dataset size per family was measured. Peak worker memory was not reliably collected (`null` in run records). Dask logged some memory warnings during successful 1 GB sort jobs.
- Physical Parquet and raw JSONL remain local and ignored; the audited flat CSV and preparation hashes are committed for collaboration.
- The original Windows branch `codex/windows-dask` and its descendant `codex/config-selection-policy` remain published as checkpoints. On 2026-10-28, `main` was fast-forwarded from `f474aae` to include both branches and pushed to `origin/main`. The merged code passed **79 tests on this Windows PC**. The PAT file `docs/Git.env` remains ignored. See [`docs/GIT_COLLABORATION.md`](docs/GIT_COLLABORATION.md).
