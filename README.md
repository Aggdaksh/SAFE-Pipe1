# SAFE-Pipe

**A bounded configuration advisor for local Dask data pipelines.** SAFE-Pipe predicts the runtime of eight declared worker settings for a known batch workload, checks a deadline and resource limits, then recommends a setting or abstains with an explanation.

This is Delhi Technological University IT401 Group 45's Project-I prototype. The evaluated backend is a memory-capped Dask `LocalCluster` on one Windows PC. The broader distributed and AWS Glue ideas in the submitted synopsis are not measured outcomes of this prototype.

## At a glance

| Area | Current state |
| --- | --- |
| Workloads | Four frozen synthetic Parquet profiles: scan/filter, group-by, skewed join, and sort/merge |
| Candidate settings | Eight combinations of 1-2 workers, 1-2 threads per worker, and 1-2 GB per worker |
| Physical experiment | 4 profiles x 8 settings x 3 repeats = **96 scored Dask jobs** on a 31.4 GiB RAM Windows PC |
| Runtime estimate | LightGBM point prediction plus a split-conformal upper estimate |
| Advisor | `balanced` (default), `resource`, and `fastest` preference modes; support, deadline, memory, and optional budget checks |
| Evidence status | First measured prototype complete; fresh-run and new-profile validation remain open |

For an introduction to the concepts and project history, open the [beginner-friendly explainer](PROJECT_EXPLAINER.html). For the midterm presentation, use the [synopsis-to-evidence review](docs/MIDTERM_SYNOPSIS_ALIGNMENT.md).

## How it works

```text
Offline: frozen datasets -> 96 Dask runs -> audited results -> runtime model + upper estimate

Request: workload profile + engine deadline + preferences
           -> create eight candidate feature rows
           -> predict runtime and upper estimate for each
           -> check exact profile support, budgets, memory rule, and deadline
           -> score eligible candidates -> recommendation or abstention
```

The model uses only information available before execution. The advisor does not execute a job; `execute` is a separate command. Its deadline concerns **Dask engine runtime**, excluding cluster startup, profiling, and advice time. See the [feature list](safe_pipe/features.py), [configuration-selection design](docs/CONFIG_SELECTION.md), and [data dictionary](docs/DATA_DICTIONARY.md).

## Quick start

Python 3.11+ is required. From the repository root on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,dask,ml]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m safe_pipe.cli advise --family sort_merge --sla 13.1
```

The final command prints a JSON report with all eight candidates, their predictions, eligibility and rejection reasons, scores, and the selected setting. The frozen sort/merge example chooses `w2_t2_1g` in balanced mode. Explore other preferences and a resource budget:

```powershell
.\.venv\Scripts\python.exe -m safe_pipe.cli advise --family sort_merge --sla 13.1 --mode resource
.\.venv\Scripts\python.exe -m safe_pipe.cli advise --family sort_merge --sla 13.1 --mode fastest
.\.venv\Scripts\python.exe -m safe_pipe.cli advise --family sort_merge --sla 13.1 --max-threads 2 --max-memory-gb 2
```

On macOS or Linux, create and activate a local virtual environment, install `.[dev,ml]`, and replace the Windows Python path with `python`. Install `.[dask]` as well for Dask execution tests. Predictions still describe the original Windows experiment environment; running inference on another computer does not validate transfer to that host.

`advise` is the current explained advisor. The older `recommend-model` command remains available to reproduce the original lowest-estimated-cost policy and its published comparison; the two commands use different selection objectives.

## Verified results

The [audited run table](data/curated/runs.csv) contains **96 successes, zero SLA misses, zero timeouts, and zero OOMs**. Input hashes, family deadlines, and shuffled run order were frozen before scoring. Worker limits were 1 GB or 2 GB per worker even though the host had 31.4 GiB physical RAM.

| Measure | Observed result | Interpretation |
| --- | ---: | --- |
| LightGBM test MdAPE | 13.84% | Median absolute percentage error across 24 held-out runs |
| Family-median baseline MdAPE | 23.01% | Simpler runtime predictor on the same split |
| Upper-estimate coverage | 24/24 test runs | Observed on eight held-out family/configuration cells; not a future guarantee |
| Historical policy vs declared default | 7.524 vs 11.421 mean normalized cost | 34.1% lower **in the same table**, not an independent saving estimate |

The split kept each family/configuration cell's three repeats together: 36 training, 36 calibration, and 24 test rows. All four workload profiles are represented in the study, so it does not test entirely unseen profiles. The cost comparison reuses rows from the model's source table. See the [run audit](reports/audit.md), [runtime-model report](reports/runtime_model.md), and [policy report](reports/policy.md).

## Scope and limitations

- The advisor supports **exactly four frozen workload descriptors**. A different size, file count, partition count, format, or skew tag causes abstention. Matching descriptors alone do not verify dataset contents or another computer's performance.
- All 96 scored jobs succeeded. SAFE-Pipe therefore has deterministic guards, **not a trained failure-probability model** or evidence of failure reduction.
- Peak worker memory and disk spill were not reliably measured. Configured memory is not actual memory usage; memory-pressure warnings do not establish that spilling occurred.
- The normalized resource scores are not currency, electricity use, CPU utilization, or cloud bills. The current `sort_merge` workload shuffles by key; it does not merge a second table.
- The 20-scenario [advisor replay](reports/advisor_v1/summary.json) reuses historical measurements. It is descriptive, not a new physical experiment or independent validation.

The original 176-run/Glue synopsis and the reduced B-lite experiment have different designs; **96/176 is not a meaningful completion percentage**. Internal scope decisions are documented in [Phase 1](docs/PHASE1_DECISION.md). Supervisor acceptance of a revised scope is not recorded here.

## Next work

1. Save the frozen advisor's recommendations, then perform fresh runs on the same profiles and host to assess repeatability without retraining on those results.
2. Build an evaluator that compares saved predictions and decisions with fresh runtimes, deadline outcomes, and predeclared baselines. The existing replay does not perform this fresh-run evaluation.
3. Add reliable per-worker peak-memory and spill telemetry, with controlled checks that verify the measurements.
4. Design separate new workload profiles, version the data/features and support rule, retrain and calibrate a new model, and test on untouched profiles before claiming broader support.
5. Complete the department-formatted report and final demonstration.

See the [independent-validation plan](docs/INDEPENDENT_VALIDATION.md) for the distinction between fresh repeats of the existing profiles and genuinely new-profile evaluation.

## Repository guide

| Location | Purpose |
| --- | --- |
| [`safe_pipe/`](safe_pipe/) | Schemas, workload execution, runtime inference, advisor, and CLI |
| [`configs/`](configs/) | Frozen grid, dataset manifests, SLAs, run order, and split |
| [`experiments/`](experiments/) | Preparation, execution, auditing, training, and replay scripts |
| [`artifacts/main_v1/`](artifacts/main_v1/) | Fitted model and frozen support artifacts |
| [`data/curated/runs.csv`](data/curated/runs.csv) | Shareable audited run table |
| [`reports/`](reports/) | Experiment evidence, model results, policy comparison, and demo |
| [`docs/`](docs/) | Architecture, decisions, data dictionary, validation plan, and midterm review |

To reproduce the physical experiment, start with the [matrix preparation report](reports/matrix_preparation.md) and [PC work log](Ganant%20Work.md). Use new run stores for new experiments; do not append to the frozen `main-v1` records. The [demo record](reports/demo.md) explains the separate tiny live execution.

For work across PCs, pull `main` and follow the [Git collaboration guide](docs/GIT_COLLABORATION.md). The Windows study and advisor are already on `origin/main`; earlier feature branches remain checkpoints. Generated Parquet, raw JSONL, virtual environments, and local credentials are not shared through Git. Current status is tracked in [PROGRESS](PROGRESS.md) and the [PC work log](Ganant%20Work.md).
