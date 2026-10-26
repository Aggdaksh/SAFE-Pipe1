# Task index

**Updated:** 2026-10-26. Measured status is in [`../PROGRESS.md`](../PROGRESS.md); detailed original cards remain in [`MICROPLAN.md`](MICROPLAN.md).

| ID | Task | Status |
| --- | --- | --- |
| T-CTX / T-ARCH / T-SCH / T-OPT / T-GRID / T-STORE | Context, design, contracts, optimizer, grid, store | DONE |
| T-HW / T0 / T0b | Actual host, Dask smoke, worker-cap pilots | DONE |
| T-GEN / T-COL | Four frozen datasets and Dask collector | DONE for main-v1 |
| T-MX1 / T-MX2 | 96 physical scored jobs | DONE; 24 per family |
| T-AUDIT | Label, hash, and feature audit | DONE |
| T-ML | LightGBM and grouped split-conformal | DONE; small-sample result |
| T-OOD | Leave-one-family gate | PARTIAL; deterministic unseen-family/size gate, no calibrated k-NN |
| T-POL | Fitted CLI recommendation | DONE |
| T-BASE | Default, conservative, random same-table comparison | DONE; descriptive |
| T-SHAP | Model explanation figure | DONE |
| T-TAB | Optional TabPFN comparison | DEFERRED |
| T-REP | Results report and demo | IN REVIEW; technical draft and live demo verified, formal submission pending |

All 96 jobs succeeded. Failure ML remains rules-only because the positive-count gate was not met. The selected Windows host has 32 GB marketed RAM (ADR-005); worker caps stay 1–2 GB.
