# SAFE-Pipe project context

**Updated:** 2026-11-02. Canonical project memory: read this file first when resuming in another chat or on another PC. Update it after decisions, completed work or scope changes.

## Start here: current goal and execution constraints

The user's current objective is to develop and rigorously evaluate a **research-paper contribution** on top of SAFE-Pipe. Merely adding an ML library, calibrating an existing predictor, or changing from Spark to Dask is not sufficient novelty.

The candidate direction is **partition-aware adaptive probing for Dask configuration selection under memory pressure**. The question is whether cheap samples give misleading configuration rankings, whether simple memory scaling already resolves that, and whether better input probes plus a justified adaptive decision rule can improve configuration choices after paying their own overhead. This is a research hypothesis, not a proven unique algorithm.

- Active branch: **`codex/partition-probe-research`**, based on `origin/main` at `504f005`. Implementation/handoff checkpoint **`975b446`** was pushed and its remote SHA verified. Later documentation commits may follow it.
- The user's authorization is to investigate on a separate branch, then consider merging if evidence justifies the contribution. **No merge now.** The original advisor remains the baseline on main.
- **Latest explicit instruction:** large tests, benchmark generation/execution and any model training belong on the other laptop. This Mac is for code, research/design, documentation and small correctness checks. Do not restart the historical Mac matrices.
- Hardware available: Windows PC plus Mac. Earlier planning allowed 4–6 weeks; this is a planning horizon, not a confirmed submission date. Do not assume cloud spending is needed or authorized by the current work.
- The user's preferred advisor objective remains **balanced speed and resource use**. Research comparisons must state their objective and distinguish engine runtime from complete-request cost.
- No heavy research job or new training is currently scheduled by this branch. Windows compatibility and performance must still be checked on that laptop.

## Current research state

**Stage: development experiment framework ready; collecting the decisive evidence is next.** The adaptive controller and a learned probe-reliability model are not yet implemented. No new model was trained for this direction.

Implemented separately from production code:

- `safe_pipe/research/probe_workloads.py`: deterministic synthetic groupby/join inputs, data inventories/hashes, uniform and partition-weighted samples, plus a small pandas correctness oracle.
- `safe_pipe/research/probe_runner.py`: fresh supervised Dask clusters, worker RSS/managed-memory/spill samples, graph information, host-memory checks, wall-time limits and owned-process cleanup. Interruptions are explicit outcomes.
- `experiments/probe_pilot.py`: prepare/run/resume/analyze, frozen source/data/plan identities, randomized repeat blocks and four methods: full, uniform, uniform with scaled memory, and partition-weighted with the same scaled memory.
- `safe_pipe/research/probe_analysis.py` and `experiments/export_probe_evidence.py`: complete-group ranking comparisons, incomplete/failure retention and compact exports. These do not evaluate an online adaptive policy.
- [Protocol and closest prior work](docs/research/PROBE_PROTOCOL.md), [Windows instructions](docs/research/WINDOWS_HANDOFF.md) and [evidence ledger](reports/research_probe_v1/README.md).

Verified evidence must stay separated:

| Study/check | Observed state | What it supports |
| --- | --- | --- |
| Original main-v1 | 96 successful Dask jobs; 79-test baseline | Existing bounded advisor, with the limitations below |
| Research correctness | 120-test suite passed; 2 subsequently added interruption/source-change checks also passed | Implementation checks; not 122 benchmark jobs or training iterations |
| Research tiny smoke | 16/16 successes; scalar outputs checked against pandas | Small-input software diagnostics |
| Mac 64-cell development plan | 1 recorded success; next larger-cap cell refused before execution | Partial data only |
| Mac 32-cell limited plan | 10 recorded successes; study stopped at the user's instruction | Partial data only; 2 full groupby runs recorded sampled disk spill |
| Windows research screen | Not run; preset describes 768 jobs | Pending development study, not a final held-out evaluation |

The two observed groupby spill peaks were 71,066,898 and 92,031,812 bytes, with one worker lifetime observed in each. They show pressure in those particular runs, not a stable ranking or benefit from the proposed sampling method. One additional Mac-limited attempt was interrupted before the older runner wrote its row; the ledger names that evidence gap. Do not hide it or fabricate a replacement measurement.

The two partial plans cannot be pooled into a complete comparison. Historical source changed after their preparation, so **prepare a fresh Windows plan** instead of resuming or editing the old plans. The first smoke predates source fingerprints and some metadata. The ledger documents these provenance limits.

## What remains, in order

### Useful preparation without heavy computation

1. Specify the follow-up research hypotheses, primary metrics and stopping decisions before looking at larger results. The existing protocol defines the exploratory screen; final evaluation is still to be designed.
2. Draft a precise adaptive-policy specification: what input information it may use, when to enlarge a probe, how uncertainty triggers further measurement or abstention, and how every probe/preparation cost is charged. Keep this a proposed design until the screen shows a gap worth solving.
3. Plan ablations that separate input-partition imbalance, key skew, data size and seed. The current balanced/uneven recipes change multiple factors together, so they cannot identify each factor's effect.
4. Prepare a paper outline and contribution-versus-prior-work table. Keep results/conclusion placeholders empty and revisit nearest papers before claiming novelty.

### Work on the other laptop

1. Pull **the research branch**, install its separate environment and run the small Windows tests/smoke checks in the handoff. Record package versions, commit and host conditions.
2. Prepare a fresh `windows-screen` plan: 12 instances × 8 configurations × 4 methods × 2 repeats = **768 physical jobs**. Run bounded batches; preserve failures/interruption and inspect telemetry. Do not launch this matrix on the current Mac.
3. Analyze whether proxy-ranking errors persist after the matched uniform-memory baseline. Confirm pressure and repeatability; two repeats are exploratory, not strong statistical evidence.
4. If a useful gap remains, implement and test the adaptive policy; otherwise revise or abandon the candidate. Training a reliability model is conditional on the design and sufficient independent data, not an automatic next step.
5. Evaluate the final method on independent instances, with predeclared baselines and total request cost: preparation + all paid probes + a fresh selected full run. Preserve separate development and final-test data; do not tune on the latter.
6. Write supported findings, limitations and reproducible artifacts; then seek the user's integration decision. A prepared framework alone is not paper readiness or proof of novelty.

The original advisor still needs prospective validation on its original Windows host. That is a separate pending task; the new research pilot does not complete it.

## Purpose and scope

SAFE-Pipe recommends a configuration from eight declared local Dask configurations under an engine deadline, or abstains. The preferred `advise` command balances predicted speed and configured resource-time. Project-I measured four synthetic workload profiles on one Windows PC with worker memory caps of 1 GB and 2 GB: four families × eight configs × three repeats = 96 runs. LightGBM, upper estimates, support checks, baselines, and reports use that frozen run table. No general safety guarantee or multi-node result is established.

## Machines and Git branches

| Machine | Role |
| --- | --- |
| Earlier Mac environment described as 8 GB | Historical coding/docs/tiny checks; not the current measured hardware fact |
| Current Mac, 16 GiB observed in research run records | Code, research/design, documentation and small correctness checks only |
| Windows 11 PC, 31.4 GiB physical RAM in the original study | Physical experiment host (ADR-005); intended research laptop, environment to be verified again |

The original 16 GB plan is a conservative historical sizing reference. The original Windows host has 32 GB marketed RAM; **production worker caps and the eight-config grid stay unchanged**. The earlier Mac, Windows and advisor work is included in `main` after a 2026-10-28 fast-forward merge. Their original branches remain checkpoints. Pull `main` for baseline work, but pull **`codex/partition-probe-research` for the current research task**. Generated Parquet, raw JSONL runs and virtual environments are gitignored.

## Verified baseline implementation (separate from research)

- Schemas, optimizer, eight-config grid, JSONL store, tiny four-family Parquet generators, pandas collector, and 96-cell planner came from the Mac branch.
- Windows `.venv` has `.[dev,dask,ml]` installed under Python 3.14.6. The merged `main` suite has **79 passing tests** on this PC, including tiny Dask executions, advisor regressions and the model-loading compatibility checks.
- T0 passed on the selected Windows PC: one 512 MB Dask worker returned the expected sum. See [`reports/t0.md`](reports/t0.md).
- T0b pilot compared 1 GB and 2 GB workers on two scan sizes and one sort size. The 136 MB sort took 10.58 s at 1 GB versus 4.53 s at 2 GB; both succeeded. See [`reports/t0b.md`](reports/t0b.md). That historical study did not confirm spill or OOM; the separate research spill observations above must not be attributed to it.
- Dask execution and one-cell collection are implemented; the scored matrix is complete (96 jobs below).
- Four `main-v1` datasets (175–198 MB) are generated, fingerprinted, and ignored by Git. The committed index is `configs/datasets_main_v1.json`.
- Twelve 2 GB SLA pilot runs succeeded. Deadlines and the randomized 96-cell order were frozen in `configs/` before scored collection. See `reports/matrix_preparation.md`.
- All 96 Dask cells were measured and audited: 96 successes, zero SLA misses. The curated CSV is committed at `data/curated/runs.csv`; raw JSONL and Parquet remain local.
- Grouped LightGBM plus conformal, a conservative rule-based OOD gate, fitted CLI recommendation, descriptive same-table baselines, and a feature-contribution figure are implemented. See `reports/runtime_model.md`, `reports/policy.md`, and `reports/shap.md`.
- New `advise` policy defaults to balanced speed/resources, with hard upper-runtime deadlines, optional budgets, exact frozen descriptors, bound grid/artifact checks and per-candidate comparisons. It reuses the model without training. See `docs/CONFIG_SELECTION.md` and `reports/advisor_v1/`.

## Original project deliverables still pending

The balanced selection implementation and the original Windows study are now merged into `main` and published. The technical results draft and separate tiny live Dask demo are complete. Remaining experimental work is prospective evaluation on the original Windows host; broader profiles need new data and a revised model/support policy. See `docs/INDEPENDENT_VALIDATION.md`. Formal submission remains pending. Optional TabPFN remains unrun; no failure classifier is supported because all 96 measured jobs succeeded.

## Design rules

- Use pre-run features only for baseline inference. A target job's actual runtime, memory, status and spill cannot enter its own prediction vector. A future adaptive research policy may use already-completed probe observations available before its decision, with their cost charged; it must not use the selected full run's outcome to choose that same run.
- Optimize the declared balanced dimensionless score using point runtime; test deadlines against the frozen upper estimate. Use explicit hard checks and abstain when none pass. Preserve historical cost/model features for old report reproduction.
- Keep the production target caps at 1 GB and 2 GB despite the larger host. Research proxies use explicitly recorded scaled caps from their protocol. State the actual machine and cap mapping for each study.
- Failure handling stays deterministic until enough correctly labeled independent failure data supports training and held-out evaluation. A fixed number of positives alone does not establish classifier quality.
- Every reported number must be traceable to its named study and artifact. Keep the original frozen 96-run table separate from the research pilot and future evaluations. No Glue, 176-run, unmeasured improvement, or unverified novelty claims.

## Documents

[`PROGRESS.md`](PROGRESS.md) is the status ledger; [`docs/MICROPLAN.md`](docs/MICROPLAN.md) has task cards; [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines component contracts; [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) lists acceptance criteria; [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md) is the conservative six-week schedule. ADR-005 records the actual host change.
