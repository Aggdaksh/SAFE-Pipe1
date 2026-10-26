# Model explanation for the sort recommendation

[`shap_sort_merge.png`](shap_sort_merge.png) shows LightGBM feature contributions for the selected `w1_t2_1g` configuration on the frozen sort workload. The predicted point runtime is **3.30 s**. The bars sum with the model's base value to the prediction in **log seconds**. The exact contribution values are in [`shap_sort_merge.csv`](shap_sort_merge.csv), produced by [`experiments/explain_recommendation.py`](../experiments/explain_recommendation.py).

The largest positive contribution in this one explanation is `estimated_rows`; `threads_per_worker` contributes negatively. These are model attributions, not causal effects. Input size, family, and configuration are correlated in this 96-row table, and only one dataset size was measured per family.
