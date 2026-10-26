# SAFE-Pipe (Project-I, B-lite)

New to this project? Open the standalone [beginner's HTML lesson](PROJECT_EXPLAINER.html) in a browser. It explains the problem, the Git and experiment history, the measured results, and what remains.

Preparing the Project-I midterm? Read the [synopsis-to-evidence status review](docs/MIDTERM_SYNOPSIS_ALIGNMENT.md) for completed work, scope changes, remaining commitments, and a presentation-ready evidence path.

SAFE-Pipe selects the lowest expected normalized-cost configuration from eight declared memory-capped local Dask configurations that is predicted to meet a job deadline, or abstains. It is a DTU IT401 Group 45 project on **one PC**, not a Glue or multi-node study. The original 176-run/Glue synopsis is historical; see [`docs/PHASE1_DECISION.md`](docs/PHASE1_DECISION.md).

## Current measured state

On the user-selected Windows experiment PC (31.4 GiB physical RAM), four synthetic Parquet families were run across eight configurations with three repeats: **96 physical Dask jobs**. Worker limits remained 1–2 GB. The audited table has **96 successes, zero SLA misses, and zero failures**. The curated shareable data is [`data/curated/runs.csv`](data/curated/runs.csv); large Parquet inputs and raw JSONL stay local. Dataset hashes, frozen SLAs, and randomized run order are in `configs/`.

LightGBM on a grouped split gave 13.84% test MdAPE versus 23.01% for a family-median baseline; the conformal upper bound covered 24/24 held-out rows. The policy had 34.1% lower normalized cost than the declared default in a **descriptive same-table** comparison. The model trained on some cells in that table, and there were no failures, so these results do not establish independent cost or safety improvement. See [`reports/runtime_model.md`](reports/runtime_model.md), [`reports/policy.md`](reports/policy.md), and [`reports/audit.md`](reports/audit.md).

## Set up and verify

Python 3.11+ is required. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,dask,ml]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m safe_pipe.cli recommend-model --family sort_merge --sla 13.1
```

On the coding Mac, `pip install -e ".[dev]"` runs the unit and tiny-data tests; Dask integration tests skip without the Dask extra. Existing model artifacts can be used after installing `.[ml]`. The `recommend-model` command prints eight candidate estimates, the selected configuration or abstention, and a note that failure probabilities are not calibrated.

## Reproduce the physical experiment on an authorized host

Read [`reports/matrix_preparation.md`](reports/matrix_preparation.md), [`reports/t0.md`](reports/t0.md), and [`Ganant Work.md`](Ganant%20Work.md) first. `experiments/prepare_matrix_data.py` creates versioned synthetic inputs and refuses to replace frozen files. `experiments/pilot_sla.py` and `experiments/prepare_matrix_plan.py` freeze deadlines and order before scoring. `experiments/run_matrix.py` appends one Dask result at a time and can resume without repeating cells. `experiments/audit_runs.py` validates all 96 rows and exports CSV/Parquet. Do not rerun those commands into the existing `main-v1` records or treat pilot jobs as scored rows.

## Scope and limitations

The four families are scan/filter, group-by, skewed join, and sort/merge. LightGBM predicts successful runtime; split conformal supplies an upper bound; a conservative rule-based OOD gate abstains outside measured scope. Failure handling remains deterministic because all 96 physical runs succeeded. TabPFN on Colab is optional and not run. Glue, Spark, LLM agents, and real-cluster claims are out of scope.

For current tasks and cross-PC handoff, read [`context.md`](context.md), [`PROGRESS.md`](PROGRESS.md), [`Ganant Work.md`](Ganant%20Work.md), and [`docs/GIT_COLLABORATION.md`](docs/GIT_COLLABORATION.md). The Windows branch is published at `origin/codex/windows-dask` for team review.

The verified `profile → recommend-model → execute` sequence and its separate tiny live run are documented in [`reports/demo.md`](reports/demo.md). A technical results draft is in [`reports/project_i_results.md`](reports/project_i_results.md).
