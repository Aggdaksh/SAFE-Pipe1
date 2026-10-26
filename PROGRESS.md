# Progress

**Updated:** 2026-10-26. Canonical memory: [`context.md`](context.md). Windows PC chronology: [`Ganant Work.md`](Ganant%20Work.md).

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

The full Windows suite currently passes **29 tests** with `.[dev,dask,ml]` installed. Dask tests skip on a coding machine without Dask.

## Measured outcomes

- The selected experiment PC is Windows 11 with 31.4 GiB physical RAM. Dask workers remained capped at 1–2 GB; four datasets were 175–198 MB.
- All **96/96** jobs succeeded and met their frozen family SLAs. This leaves **zero** actionable failure positives; no learned failure model or failure-reduction claim is supported.
- On 8 held-out family/config cells (24 rows), LightGBM MdAPE was **13.84%** versus **23.01%** for the family-median baseline. Conformal upper coverage was **24/24 rows**, with mean width **1.33 s**. These are descriptive small-sample results.
- Same-table policy median normalized cost averaged **7.524** versus **11.421** for default, a **34.1%** lower cost in this table. Some evaluated cells were used for model fitting, so this is not an independent improvement estimate.

## Remaining and limits

- Department formatting, supervisor review, and formal submission remain outside the verified repository draft.
- Optional TabPFN comparison remains unrun. The formal DTU synopsis/report submission and supervisor decision are outside this repository's verified work.
- The rule-based OOD thresholds are heuristics; only one dataset size per family was measured. Peak worker memory was not reliably collected (`null` in run records). Dask logged some memory warnings during successful 1 GB sort jobs.
- Physical Parquet and raw JSONL remain local and ignored; the audited flat CSV and preparation hashes are committed for collaboration.
- The Windows branch `codex/windows-dask` was pushed successfully to `origin` using the authorized `Aggdaksh` account. The PAT file `docs/Git.env` remains ignored. Team review and merge to `main` are still pending. See [`docs/GIT_COLLABORATION.md`](docs/GIT_COLLABORATION.md).
