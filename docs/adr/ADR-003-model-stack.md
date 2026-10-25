# ADR-003 — Model stack

- **Date:** 2026-10-25
- **Status:** Accepted

## Context

Need technical depth (ML/DL) without pretending ~100 tabular rows need a custom net. Examiners can sink “we trained a transformer on 96 runs.”

## Decision

- Default policy model: **LightGBM** on log successful runtime.
- Uncertainty: **split conformal** upper interval.
- OOD: leave-one-family plus k-NN in standardized workload features.
- Failure: **rules** unless ≥ ~30 actionable positives.
- DL/AI chapter: **TabPFN** on Colab using the exported CSV; not loaded in the CLI policy path.
- Explanations: SHAP on the LightGBM model for the demo.

## Alternatives

- XGBoost — interchangeable; LightGBM is enough.
- From-scratch MLP — rejected as policy.
- LLM job parser — rejected.

## Consequences

If TabPFN is not run, the report simply omits that comparison. The project remains valid.
