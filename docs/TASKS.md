# Task index

**Updated:** 2026-10-26. Detailed cards: [`MICROPLAN.md`](MICROPLAN.md). Actual host change: ADR-005.

| ID | Purpose | Status | Evidence / next gate |
| --- | --- | --- | --- |
| T-CTX / T-ARCH | Context, architecture, requirements | DONE | `context.md`, `docs/` |
| T-SCH / T-OPT | Schemas and bounded optimizer | DONE | Unit tests |
| T-GRID | Declared eight configurations | DONE | `configs/dask_grid.json` |
| T-STORE | JSONL run store | DONE | Round-trip test |
| T-HW | Experiment host RAM and OS | DONE | Windows, 31.4 GiB; `reports/t0.md` |
| T0 | LocalCluster smoke | DONE | `reports/t0.md` |
| T0b | 1 GB versus 2 GB pilot | DONE | `reports/t0b.md` |
| T-GEN | Four Parquet generators | IN PROGRESS | Tiny complete; scale and freeze four physical datasets |
| T-COL | One-cell collector | IN PROGRESS | Pandas complete; Dask tiny success/timeout tested; verify physical pilot and manifest hashes |
| T-MX1 | 48 scan/group-by scored runs | NOT STARTED | Requires frozen datasets, SLAs, collector |
| T-MX2 | 48 join/sort scored runs | NOT STARTED | Requires T-MX1 |
| T-AUDIT | Labels and leakage | NOT STARTED | Requires frozen 96-row table |
| T-ML | LightGBM and conformal | NOT STARTED | Requires audit |
| T-OOD | Leave-one-family gate | NOT STARTED | Requires model |
| T-POL | Fitted CLI recommendation | NOT STARTED | Requires OOD |
| T-BASE | Default, conservative, random | NOT STARTED | Same-table comparison |
| T-SHAP | Demo explanations | NOT STARTED | Requires model |
| T-TAB | Optional TabPFN comparison | NOT STARTED | Requires frozen table |
| T-REP | Report and demo | NOT STARTED | Numbers must match curated table |

The Mac-side branch remains available. The Windows Dask work is on `codex/windows-dask`; pull it before continuing on another PC.
