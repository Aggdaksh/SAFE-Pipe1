# Runtime model and uncertainty (main-v1)

**Date:** 2026-10-26. Code: [`safe_pipe/models/runtime.py`](../safe_pipe/models/runtime.py) and [`experiments/train_runtime.py`](../experiments/train_runtime.py). Artifact and exact metrics: [`artifacts/main_v1/`](../artifacts/main_v1/).

The audited 96-row table has 32 distinct family/config cells, each with three physical repeats. The split was frozen in [`configs/model_split_main_v1.json`](../configs/model_split_main_v1.json) before fitting: 12 training cells (36 rows), 12 calibration cells (36 rows), and 8 test cells (24 rows). No cell's repeats cross splits. Only the explicit pre-run columns in [`safe_pipe/features.py`](../safe_pipe/features.py) enter the model.

LightGBM predicts log successful engine runtime. Hyperparameters were fixed at 120 trees, 7 leaves, learning rate 0.05, minimum child 3, and L2 penalty 1. A family-median runtime from the same training split is the baseline. The one-sided conformal score is the **maximum** log residual over each calibration cell's repeats; the 90% finite-sample rank over 12 cells is the largest score. The resulting upper bound is the point prediction multiplied by `exp(0.523642)`.

| Held-out metric | Result |
| --- | ---: |
| LightGBM runtime MdAPE | 13.84% |
| Family-median baseline MdAPE | 23.01% |
| Upper bound coverage, rows | 24 / 24 |
| Upper bound coverage, cells | 8 / 8 |
| Mean point-to-upper width | 1.33 s |

These results describe **eight** held-out family/config cells drawn from only **four** workload profiles. The 100% observed coverage is not evidence of 100% population coverage. All physical runs succeeded, so the model cannot learn failure risk from this table. Predictions and metrics are saved in the artifact directory for reproducibility.
