# ADR-003 — Model stack

- **Date:** 2026-10-25
- **Status:** Historical design; implementation status clarified 2026-11-22

## Context

The original design selected a tabular runtime predictor for a small local benchmark table. The earlier presentation-oriented rationale is not evidence that a model is appropriate or superior. The implementation and empirical limits below govern current claims.

## Implemented scope and evidence

LightGBM fits log successful runtime with the fixed settings recorded in `experiments/train_runtime.py`: 120 trees, seven leaves, learning rate 0.05, minimum child count three, L2 penalty one, seed 2026 and one training thread. The recorded comparison is a family-median baseline. There is no archived hyperparameter search or alternative learned-model comparison establishing these settings as optimal. Suitability for structured features is an engineering reason for using a tree model; superiority over XGBoost or another learner is untested.

Grouped maximum log residuals construct the upper estimate. Grouping repetitions prevents repeat leakage but does not establish exchangeability of calibration and future workloads. The nominal calibration level and observed test coverage must not be interpreted as a universal safety guarantee.

The deployed advisor checks exact frozen descriptors and artifact identities, as specified in ADR-006. The leave-one-family/k-NN support design below is historical, not the current advisor contract. TabPFN was not run. All 96 original jobs succeeded, so no learned failure classifier is supported. A threshold count of failures alone would not establish classifier quality. These status notes supersede the corresponding provisional items below.

## Original provisional decision

- Default policy model: **LightGBM** on log successful runtime.
- Uncertainty: **split conformal** upper interval.
- OOD: leave-one-family plus k-NN in standardized workload features.
- Failure: **rules** unless ≥ ~30 actionable positives.
- DL/AI chapter: **TabPFN** on Colab using the exported CSV; not loaded in the CLI policy path.
- Explanations: SHAP on the LightGBM model for the demo.

## Alternatives

- XGBoost — considered as an alternative; no comparative evaluation was recorded.
- From-scratch MLP — rejected as policy.
- LLM job parser — rejected.

## Consequences

If TabPFN is not run, the report simply omits that comparison. The project remains valid.
