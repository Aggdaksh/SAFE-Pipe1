# SAFE-Pipe (Project-I, B-lite)

Repository: [https://github.com/Aggdaksh/SAFE-Pipe1](https://github.com/Aggdaksh/SAFE-Pipe1)

Failure-aware **pre-run** configuration selection for **memory-capped local Dask**.

Given a batch workload profile, SLA deadline, and failure-risk limit, SAFE-Pipe ranks a **small declared candidate set** and returns the cheapest configuration that is predicted to finish on time — or **abstains**.

This repository is the DTU IT401 Group 45 implementation. The original synopsis PDF claimed AWS Glue depth and 176 Dask runs. **That experiment is not what this repo implements.** See [`docs/SYNOPSIS_BLITE.md`](docs/SYNOPSIS_BLITE.md) and [`docs/PHASE1_DECISION.md`](docs/PHASE1_DECISION.md).

## What is in scope (Project-I)

- One primary backend: **Dask** on a single PC, with worker `memory_limit` set low enough to induce spill/timeout.
- Four synthetic Parquet workload families: scan/filter, group-by, skewed join, sort/merge.
- **96** physical runs (4 families × 8 candidates × 3 repeats) on a **16 GB** PC, **150–250 MB** datasets. Worker memory stays 1–2 GB.
- Models: **LightGBM** runtime + **split conformal** upper bound + **leave-one-family OOD**.
- Failure handling: **deterministic rules** unless ~30+ credible actionable failures appear.
- Optional Colab chapter: **TabPFN** on the exported CSV (comparison, not the live policy).

## What is out of scope

AWS Glue evidence, Spark, LLM agents, from-scratch deep learning as the policy, microservices, and any claim of a real cluster.

## Setup (8 GB Mac — tests and tiny data)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
safe-pipe recommend --estimates examples/estimates.json --sla 20
safe-pipe generate --dest data/generated
safe-pipe collect --family scan_filter
```

As of 2026-10-26: **20 pytest tests passed** on the Mac. That is **not** Dask evidence.

## Setup (16 GB experiment PC — official T0)

```bash
pip install -e ".[dev,dask]"
python experiments/t0_smoke.py
```

Full steps: [`reports/HANDOFF_16GB.md`](reports/HANDOFF_16GB.md). Do not run the 8-config Dask matrix on the 8 GB Mac.

## Documents

| File | Purpose |
| --- | --- |
| [`context.md`](context.md) | **Living project memory — update this first** |
| [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) | MoSCoW requirements and stories |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Components, data flow, contracts |
| [`DESIGN.md`](DESIGN.md) | Design goals and trade-offs |
| [`docs/MICROPLAN.md`](docs/MICROPLAN.md) | Task cards and vertical slices |
| [`docs/INVESTIGATIONS.md`](docs/INVESTIGATIONS.md) | Experiments before committing |
| [`DECISIONS.md`](DECISIONS.md) | ADR index |
| [`PROGRESS.md`](PROGRESS.md) | Actual status |
| [`ROADMAP.md`](ROADMAP.md) | Six-week calendar |
| [`docs/PHASE0_FEASIBILITY.md`](docs/PHASE0_FEASIBILITY.md) | Why the PDF was not feasible |
| [`docs/SYNOPSIS_BLITE.md`](docs/SYNOPSIS_BLITE.md) | Text to paste into the DTU synopsis |
| [`reports/HANDOFF_16GB.md`](reports/HANDOFF_16GB.md) | What to run on the experiment PC |
| [`docs/SESSION_STATUS.md`](docs/SESSION_STATUS.md) | Snapshot for the next coding session |

Do not commit secrets. Do not write Glue run counts into the report.
