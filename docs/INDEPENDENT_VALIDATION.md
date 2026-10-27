# Validation plan: repeatability now, broader support later

The current advisor is a policy layer over the frozen main-v1 runtime model. It requires an exact match to one of four frozen workload descriptors. A changed byte count, row count, file/partition count, skew tag, or format causes abstention. Its prediction target is the original Windows experiment environment. Existing commands do not establish support for new profiles or other hosts.

The 96 historical executions are four profiles × eight configurations × three repeats. The existing model test split holds out configuration cells, not workload profiles. [evaluate_advisor.py](../experiments/evaluate_advisor.py) reuses the historical table for preference/mode sensitivity; its output is descriptive replay, not independent validation. It does not accept a fresh-run table or implement the aggregation planned below.

No retraining is needed to use or test the current scoring, preference modes, budget/deadline checks, abstention, or explanation output. Retraining is needed when replacing feature definitions or supporting a broader workload population. There is no trained failure model: all 96 historical jobs succeeded, and every peak-memory field is missing.

## A. Feasible now: fresh executions of the frozen profiles

This tests whether the frozen advisor's predictions and choices remain useful on new executions of the same data and host. It provides evidence about repeatability over time, not unseen-workload generalization. No new training is involved.

1. Use the original Windows PC and original hashed main-v1 Parquet datasets. Record the commit, model/support artifact hashes, OS, CPU, RAM, dependency versions, power mode, background workload, and run dates. Verify the dataset manifests. The original host had 31.4 GiB RAM and 16 logical processors; see [T0](../reports/t0.md). A different host is a transfer experiment and must be labeled separately.
2. Before running anything, save all four advisor reports. Freeze the primary mode (`balanced` by default), thread weight, resource budgets, reserve, eight-config grid, and four SLAs. Declare other modes as secondary comparisons. Do not pick the winning preference setting after reading the new runtimes.
3. Run all eight configurations for each profile, three times, one LocalCluster at a time. Use a new raw log and a new export directory. Preserve all successes, timeouts, and other failures. The existing runner supports this 96-execution layout and verifies input hashes. Its frozen randomized order can be reused; record that order and consistent cache/background-load conditions.
4. Link the new run set to the saved predictions by family/configuration. Keep the original model, calibration, SLAs, and `data/curated/runs.csv` unchanged. If the new results motivate a policy change, use these runs as development evidence and collect another untouched evaluation set afterward.

For example, from the repository root on the original Windows PC, after the original datasets are available, the existing collection/export commands are:

```powershell
.\.venv\Scripts\python.exe -m safe_pipe.cli advise --family scan_filter --sla 2.6 --mode balanced
.\.venv\Scripts\python.exe -m safe_pipe.cli advise --family groupby --sla 7.9 --mode balanced
.\.venv\Scripts\python.exe -m safe_pipe.cli advise --family skewed_join --sla 4.3 --mode balanced
.\.venv\Scripts\python.exe -m safe_pipe.cli advise --family sort_merge --sla 13.1 --mode balanced

.\.venv\Scripts\python.exe experiments/run_matrix.py --store data/runs/repeatability_v1.jsonl --max-jobs 16 --timeout 120
.\.venv\Scripts\python.exe experiments/audit_runs.py --store data/runs/repeatability_v1.jsonl --output data/curated/repeatability_v1
```

Save the four printed JSON reports before collection. Run the `run_matrix.py` command repeatedly until the new log contains all 96 cells; it resumes without repeating completed cells. Run the audit only after completion. The example paths must be new for a new experiment; an existing completed log will simply resume with no jobs remaining. These commands retain the input `data_version=main-v1` because the datasets are unchanged; record `repeatability_v1` separately as the evaluation/run-set identifier. The export script labels the host `windows_32gb`, so it must not be used unchanged to claim another host's provenance.

These commands collect and audit fresh executions. **They do not compute an independent advisor-comparison report.** That analysis still needs an evaluator accepting the fresh table plus the saved, pre-run advisor reports. Running `evaluate_advisor.py` afterward would still read the old main-v1 table.

Predeclare that evaluator's outputs:

| Measure | Report |
| --- | --- |
| Acceptance | Recommended and abstained profiles out of four, with reasons. Never treat abstention as a successfully completed job. |
| Deadline behavior | Successes within the engine deadline, misses, timeouts, and other failures for each selected configuration's three fresh repeats. Also report the effective reserved deadline separately if a reserve is used. |
| Prediction quality | Predicted point/upper versus every fresh runtime; row counts and per-profile/configuration results. Failed/timeout runs must remain visible, not be silently discarded. |
| Resource tradeoff | Measured configured-thread-seconds and configured-decimal-GB-seconds, plus the predeclared normalized score. These remain resource proxies, not CPU usage, memory peaks, or currency. |
| Baselines | The declared in-grid reference `w1_t1_2g` and any other baseline fixed before collection. This reference is not the native Dask default. Compare the same accepted profiles; report each baseline's failures/misses alongside cost. |
| Oracle comparison | Best observed feasible in-grid configuration under a predeclared aggregation rule, such as success within deadline in all three repeats followed by minimum median score. Label it a noisy hindsight reference, not a deployable policy. |

For complete successful triples, report median and range as well as the three individual timings. Three repeats cannot support precise tail estimates. A fresh zero-failure result would still not establish zero risk. Cluster startup is excluded from the trained target; measure and report it separately if demonstrating end-to-end user waiting time.

## B. Future work: fresh workload profiles and model support

The current descriptor whitelist deliberately abstains on these profiles. Do not bypass that gate, replace frozen manifests, or describe a fresh workload as supported merely because its family name is familiar. A generalized profile identity/collection pipeline, revised support rule, and new versioned model must be implemented and evaluated before such recommendations become supported behavior.

A small feasible first collection is **eight new profiles: two per family**, using the existing generator's row-count, file-count, and seed arguments. Start on the same Windows host with the same eight configurations, worker limits, and one-job-at-a-time procedure.

| New profile in each family | Rows relative to its main-v1 profile | Requested files | Seed plan | Purpose |
| --- | ---: | ---: | --- | --- |
| A | 0.75×, rounded to an integer | 8 | New fixed seed, recorded before generation | Smaller input with fewer declared input partitions. |
| B | 1.25×, rounded to an integer | 32 | A different new fixed seed | Larger input with more declared input partitions. |

These eight profiles × eight configurations × three repeats require 192 executions. Generate profiles sequentially and keep separate versioned directories/manifests. Size in compressed bytes must be measured after generation; it is not exactly proportional to row count. Run bounded feasibility pilots before the scored matrix, then freeze deadlines and timeout rules separately. This is a practical data-expansion pilot, **not enough by itself to establish reliable new-workload coverage**. Jointly changing size and file count tests combined variation; it does not isolate either variable's causal effect.

Before collecting that matrix, implement these data changes:

- Add a unique `workload_instance_id` and a separate `run_set_id`. Preserve seed, generator version/parameters, dataset hashes, and hardware/software provenance. The current runner/index/auditor assume one manifest per family and exactly 96 cells; they need an explicitly versioned extension for multiple profiles.
- Version the feature schema. Record actual configured memory bytes and label configured threads correctly. For joins, record both inputs' rows/files/bytes; separate true input-file counts from observed Dask partition counts. Preserve the old feature schema only for replaying the old model.
- Replace the fixed skew tag with a defined, reproducible pre-run descriptor. Changing the Zipf distribution requires exposing a generator parameter first; the current generator hardcodes `1.5`. Do not claim that a different seed alone establishes skew generalization.
- If memory-related prediction becomes a goal, add per-worker peak/process-memory telemetry and distinguish normal spilling/pauses from failures. Keep failed executions and their reason/timeout limit. No memory predictor can be validated from the current null peak labels.

Use the first expansion pilot for development and feasibility. For a later evaluation, freeze distinct workload-instance groups into training/development, calibration, and untouched final testing. **All configurations and repeats of one workload instance must remain in its one group.** Repeated seeds and similar parameter settings are still related; state how instances were sampled and the limited target population.

One bounded expansion example, if the pilot is affordable, is 32 fresh profiles: eight per family, with 12 instances for development/training, 12 for calibration, and eight for final testing, balanced across families. This is 768 executions at the current eight-config/three-repeat design. It is a planning example, not an already collected dataset or a guarantee of adequate accuracy. Keep outcomes from the untouched eight out of feature, model, weight, threshold, and support-policy choices. Prefer a narrow same-host supported region before attempting host transfer.

Fit a new runtime model and calibrate it using the new workload grouping. If the goal is a bound that remains valid after choosing among configurations, the calibration/evaluation design must explicitly address selection; ordinary marginal row coverage is insufficient. A possible research direction is a workload-level score taking the maximum residual across the fixed candidate set, with assumptions and sample size assessed before claiming coverage. This is future methodology, not implemented in the frozen model. See [conformal prediction background](https://arxiv.org/abs/2107.07511) and [selection-conditional coverage research](https://arxiv.org/abs/2403.03868).

Only then define a new support policy with explicit descriptor ranges, tested configuration coverage, host scope, and abstention conditions. Evaluate it on untouched new profiles with the acceptance, deadline, resource, and failure reporting above. Extra repeat counts cannot substitute for more distinct workload profiles. Learn failure probabilities only after collecting appropriate failure and success evidence; absence of failures cannot establish a useful classifier.

## Claims the current evidence supports

The project has an executed local Dask benchmark, a trained runtime predictor, and an explainable configuration-selection policy for four frozen workload descriptors. Its preference modes and resource/deadline tradeoffs can be demonstrated without retraining. A fresh frozen-host run set can assess repeatability now. Broader workload support, calibrated failure risk, peak-memory prediction, host transfer, and independent cost/safety improvement remain work to be demonstrated.
