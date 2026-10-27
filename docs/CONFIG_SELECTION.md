# Configuration selection: balanced speed and resources

The `advise` command reuses the fitted main-v1 LightGBM runtime predictor. It ranks the eight measured Dask configurations, explains every candidate, and abstains when no candidate passes its checks. **No model was retrained for this policy.** The default follows the requested preference: balanced speed and resource use.

## Formula

For candidate `c`, let:

- `t(c)` be predicted engine runtime in seconds; `U(c)` its frozen calibrated upper estimate.
- `D` be the requested engine deadline. Cluster startup, profiling and advice time are excluded.
- `P(c)` be workers × threads per worker, a configured concurrency proxy.
- `M(c)` be total configured worker memory in bytes, using Dask's SI/IEC units.
- `lambda` be the thread share of the resource term (default 0.5).
- `beta` be the latency share: 0.5 for balanced, 0 for resource, 1 for fastest.

```text
Q(c) = lambda × P(c)/4 + (1 − lambda) × M(c)/4,000,000,000
R(c) = [t(c)/D] × Q(c)
J(c) = beta × [t(c)/D] + (1 − beta) × R(c)

Choose the eligible candidate with the smallest J(c).
Tie-break by smaller U(c), then configuration ID.
```

`J` is dimensionless. Its reference values (4 configured threads and 4 decimal GB) are fixed across the full grid, even when a budget removes candidates. Adding/removing an alternative cannot change another candidate's score. Changing `D` alone scales every score equally; it changes the winner only through deadline eligibility. Resource mode minimizes configured resource-time, not allocation alone.

The two 50/50 choices express preferences; they are not trained coefficients or evidence of a universally optimal formula. A faster configuration may win balanced mode even if it uses more resources. This score does not measure electricity, cloud prices, CPU utilization or peak RAM.

## Checks before selection

A candidate must pass all of the following:

1. The workload descriptors must exactly match one of the four frozen profiles. Modified size, row count, partitioning, format or skew tag produces abstention.
2. Model, metadata, metrics, profile index and configuration definitions must match the audited support manifest. Editing an index or reusing a config ID with different resource limits cannot silently broaden support.
3. `U(c) <= D × (1 − deadline_reserve)`. Reserve defaults to zero; 0.1 asks for 10% extra deadline headroom. It is not a failure probability.
4. Optional maximum configured thread and total-memory budgets must hold.
5. The coarse input-memory guard must pass (`input_bytes <= 4 × total_configured_memory_bytes`). This heuristic cannot establish peak per-worker memory safety from compressed input sizes.

A descriptor match does not verify the actual dataset contents or the calling computer. Predictions target the original Windows benchmark environment. The command runs inference only; it never launches a job, including after abstention. Dataset fingerprints are verified by the existing execution path.

The frozen upper estimate is `t × exp(0.523642...)`, approximately `1.688 × t`. It comes from a small calibration split of family/configuration cells. The recorded 24/24 test-row coverage does not establish 90% success for selected configurations or for unseen workload profiles. Multiplying all candidate costs by that same upper multiplier would leave their ranking unchanged; the upper estimate is therefore used for eligibility rather than a second uncertainty penalty.

## Run it

From the repository root after installing `.[ml]`:

```sh
python -m safe_pipe.cli advise --family sort_merge --sla 13.1
python -m safe_pipe.cli advise --family sort_merge --sla 13.1 --mode resource
python -m safe_pipe.cli advise --family sort_merge --sla 13.1 --mode fastest
python -m safe_pipe.cli advise --family sort_merge --sla 13.1 --max-threads 2 --max-memory-gb 2 --deadline-reserve 0.1
python -m safe_pipe.cli advise --family sort_merge --sla 0.01
```

The last command demonstrates abstention. Windows users can replace `python` with `.\.venv\Scripts\python.exe`. `--max-memory-gb` means decimal GB across all workers; `--thread-weight` changes the thread/memory preference. `--workload-json` accepts a `WorkloadSpec` instead of `--family`, but does not expand measured support. `--compare-to` defaults to the declared in-grid reference `w1_t1_2g`, not Dask's native default.

The JSON includes the chosen configuration, all eight point/upper predictions, resource quantities, score components, deadline headroom, eligibility/rejection reasons, and whole-configuration comparisons. Comparisons are model estimates, not causal effects or measured speedups. `failure_probability` is null: all 96 original jobs succeeded, so there is no fitted failure classifier.

## Reproduce and inspect the evidence

- `artifacts/main_v1/advisor_support.json` binds the original fitted files, index, grid and audited CSV. Text hashes normalize CRLF/LF to support Git checkouts on Windows and macOS.
- Model loading also normalizes CRLF/LF before passing text to LightGBM; `.gitattributes` keeps model files LF. This preserves the byte offsets stored in the model format without rewriting the artifact.
- `experiments/freeze_advisor_support.py` checks the original main-v1 table and refuses to overwrite an existing bundle. It does not fit a model and is deliberately scoped to this existing matrix.
- `python -m experiments.evaluate_advisor --output reports/advisor_replay_new` writes three modes plus two resource-weight variations per family (20 scenarios). The directory must not already exist. The CSV hash is checked before replay.
- `reports/advisor_v1/` contains the recorded replay from this change. These are reused measurements from the training/calibration/test source table, **not new physical jobs or independent validation**. Scenarios must not be counted as independent samples or used to choose weights for a subsequent claimed test.
- `recommend-model` remains available for historical main-v1 result reproduction; `advise` is the preferred explained, balanced selection interface. The new score's numerical values are not comparable with the old unnormalized cost values.

Memory accounting deliberately preserves the original model features: the old `parse_gb` calls interpreted `GB` with a binary multiplier. The new score interprets `1GB` as 1,000,000,000 bytes and `1GiB` as 1,073,741,824 bytes. Do not silently repair feature labels in already fitted artifacts. See [data dictionary](DATA_DICTIONARY.md).

## What needs training next?

No training is needed to use the new ranking, budgets, comparisons or rejection reasons for the existing profiles. New sizes, skew distributions, partitions or hardware need new benchmark data, a versioned feature contract, retraining and calibration, and a suitable independently assessed support rule. A credible failure classifier additionally needs real, correctly labeled actionable failures. See [independent validation plan](INDEPENDENT_VALIDATION.md).

The contribution is a transparent constrained advisor and controlled evaluation, not an unprecedented runtime predictor or a proven best formula. Relevant primary references are [Dask byte parsing](https://docs.dask.org/en/stable/_modules/dask/utils.html#parse_bytes), [Dask worker memory](https://distributed.dask.org/en/stable/worker-memory.html), [C3O](https://arxiv.org/abs/2107.13317), [conformal prediction introduction](https://arxiv.org/abs/2107.07511), and [selection-conditional conformal inference](https://arxiv.org/abs/2403.03868).
