# Partition-probe research branch

Started 2026-10-31; handoff updated 2026-11-02. Branch: `codex/partition-probe-research`, based on `origin/main` at `504f005`. Merge is deferred until evidence and implementation are reviewed. Existing production models, dataset manifests, advisor and the historical 96-row table remain separate.

**Current execution scope:** preparation and small correctness checks on this Mac only. Larger benchmarks and later training are deferred to the other laptop at the user's request. See [Windows handoff](WINDOWS_HANDOFF.md) for commands and [recorded status](../../reports/research_probe_v1/README.md) for the incomplete Mac studies.

## Question and initial scope

Can small input probes preserve configuration rankings for uneven dataflow jobs, and does partition-aware sampling add value beyond a simple memory-scaling baseline?

This first implementation is a **development proxy-validation matrix**. It implements neither the proposed adaptive controller nor a trained probe reliability model. It does not establish novelty, safe elimination, deadline guarantees or net request-time savings.

The candidate contribution is an eventual input/probe construction algorithm that handles misleading cheap tests. The code here creates the measurements needed to falsify or motivate that method.

## Nearest prior work

- [Spark MFTune](https://arxiv.org/abs/2603.16450), 2026: representative query subsets for configuration tuning. Data reduction can distort ranking. Changing the engine alone is not novelty.
- [SimCost](https://link.springer.com/article/10.1007/s10619-023-07436-y), online 2023/journal 2024: sampled resource prediction, memory sizing and task-wave scaling. The simple baseline here is not a full reproduction.
- [Less Is More](https://arxiv.org/abs/2608.00759), 2026 preprint: generic multidimensional fidelity discovery; its tuner is also called MFTune but is a different work.
- [Crispy](https://arxiv.org/abs/2206.13852) and [Ruya](https://arxiv.org/abs/2211.04240), 2022: sampled memory estimation/resource optimization.
- [Lynceus](https://research.ibm.com/publications/lynceus-cost-efficient-tuning-and-provisioning-of-data-analytic-jobs), 2020: budget-aware exploration and partial-run feedback.

## Workloads

Research workloads live in `safe_pipe/research/probe_workloads.py`. Generation is deterministic and partition-by-partition, with versioned manifests and SHA-256 file inventories. Parameters expose rows, files, cardinality, hot-key fraction, input-partition imbalance and payload width.

- Groupby consumes every payload column, declares multiple output partitions and task shuffle.
- Join consumes all fact payloads and dimension values, retains a multi-file unique-key dimension, and explicitly disables broadcast. The unique dimension avoids accidental quadratic output growth. These are operator benchmarks, not replacements for the old workload definitions.

The heavy-input-partition heuristic uses Parquet row-count metadata, never full-run memory or timing. It does **not** claim to identify costly post-shuffle partitions or preserve hot-key behavior. The first Mac cases combine key skew and input imbalance and cannot identify their separate causal effects.

## Matched methods

| Method | Input | Worker memory |
| --- | --- | --- |
| `full` | Complete reference input | Declared target cap |
| `uniform` | Exact random quarter of fact rows | Declared target cap |
| `uniform_memory` | Same files as `uniform` | Headroom-scaling heuristic |
| `partition_tail` | Same total fact-row count, preferentially sampled from larger input partitions | Same heuristic as `uniform_memory` |

The heuristic is `512 MiB + 0.25 * (target_cap - 512 MiB)`. The floor is a declared experimental parameter, not measured interpreter overhead or a physical equivalence theorem. Original and effective configurations are recorded. Both 1 GB and 2 GB refer to decimal bytes, while the floor is binary MiB.

The join dimension is retained in full to preserve matches. Thus the budget is matched **fact rows**, not total bytes. Manifests retain full dimension cost, actual row counts, partition allocations and compressed/encoded-byte totals. Encoded Parquet bytes are not peak working-set estimates.

Generation, verification, copying and sample preparation take real time; preparation is retained in manifests. It is not included in the per-cell execution timer. Actual online policy accounting is future work.

## Presets and execution

| Preset | Cases | Configs | Repeats | Methods | Cells |
| --- | ---: | ---: | ---: | ---: | ---: |
| smoke | 2 tiny cases | 2 | 1 | 4 | 16 |
| mac-limited | 2 million-row cases | 2 single-worker 1 GB thread settings | 2 | 4 | 32 |
| mac-development | 2 cases, 1 million fact rows / 16 payloads each | 4 single-worker caps/threads | 2 | 4 | 64 |
| windows-screen | 2 families × 3 sizes × 2 patterns | 8 | 2 | 4 | 768 |

The Windows screen contains 192 full-reference and 576 probe executions, including the preliminary tail method. It is not the historical 96-run study. All presets are development data, not an untouched final test set.

Plans freeze recipe, samples, hashes, effective configs and randomized order before running. Each repeat is a randomized block. Resume validates the frozen plan, sample fingerprints and all Parquet hashes. A completed physical failure remains a recorded cell; do not replace it selectively. A preflight host-budget refusal creates no misleading execution row and leaves the cell pending.

New plans also freeze source-file hashes. A changed research implementation requires a new plan, rather than mixing measurements across implementations. `mac-limited` is a separately labelled option when host headroom cannot support 2 GB caps. It does not evaluate the full memory-config grid. Its rows must not be spliced into another plan to fill missing cells.

```bash
python -m experiments.probe_pilot prepare --preset smoke --out-dir data/probes/new-smoke-v1
python -m experiments.probe_pilot run --plan data/probes/new-smoke-v1/plan.json --max-runs 16
python -m experiments.probe_pilot analyze --plan data/probes/new-smoke-v1/plan.json
```

Use `.venv/bin/python` on this Mac or `.venv\Scripts\python.exe` on Windows in place of `python`. Dependencies come from the repository's existing `.[dev,dask]` extras. A new output directory must be empty. No automatic regeneration/overwrite is performed.

On the Windows experiment PC, use `--preset windows-screen`; the runner refuses that preset on other OSes. Run a small `--max-runs` batch first and inspect resource use before continuing. `run` defaults to four new cells and is resumable. The Mac development presets remain available to describe historical plans, but no further large Mac jobs are scheduled. Windows compatibility must first pass the handoff's small checks.

## Timing, telemetry and containment

Each cell creates a fresh process-based local Dask cluster on loopback. A supervising process applies a wall-time limit across startup, execution and cleanup; forced process cleanup may add a short grace period after that limit. It terminates only its own descendants on timeout. Timeout values are censored outcomes, not successful completion times. Startup/process/cleanup failures are retained. An operator interruption during the supervised job is recorded and stops the batch; a later deliberate resume advances to other pending cells without retrying that outcome.

The collector records setup, execution, cleanup and total wall time, versions, task graph information and a scalar result. Input preparation is separate. Worker-local samples measure RSS, managed memory, spill bytes, pauses and observed worker lifetimes. Missing metrics remain null, distinct from observed zero. Sums of individual lifetime peaks are explicitly **not concurrent cluster peaks**. Brief peaks and crash-tail telemetry may be missed.

A fresh host-memory check requires worker caps plus at least max(2 GiB, 30% available RAM) headroom. Dask caps are targets, not hard OS reservations. The current machine reports 16 GiB physical RAM; old 8 GB Mac notes describe an earlier environment. All run files capture actual current host facts. No eight-configuration pressure matrix is run on this Mac.

Cache state is not controlled by flushing the OS cache. Samples/read audits can warm it; randomized order and fresh clusters do not imply a cold filesystem cache. Log this limitation and investigate it before attributing performance changes to information.

## Analysis and decision gates

The analyzer retains all statuses and incomplete groups. Numerical ranking comparisons require every planned candidate/repeat in both methods to succeed. Ranks use **engine execution time** after setup. They are not complete-request rankings.

A pair is provisionally decisive only if observed repeat ranges do not overlap and the median gap exceeds 5%. This is a noise screen, **not** a significance test or 95% confidence interval. Other pairs remain unresolved. Pair counts share workloads and are not independent samples. One-repeat smoke ranks are software diagnostics only.

The report gives aligned/inverted/unresolved pairs and the full-reference median regret of the proxy's selected configuration. It cannot show policy savings: a real policy must pay for its chosen probes and execute a fresh selected full job. Shared sample preparation is charged once per request, not once per candidate.

Proceed toward an algorithm only if repeatable, practically relevant proxy failures remain after memory scaling, input/task-plan/cache effects are understood, and a better probe could repay its construction/execution cost. Additional repeats are necessary for any apparent inversion. No observed spill/pressure means this pilot does not support a spill-preservation claim. A neutral or negative result stays in the report.

Before merge: review measured evidence and closest priors; run independent workload tests; implement/validate the adaptive controller only if justified; test compatibility; obtain the user's integration decision. Research branch publication is not a merge or a novelty claim.
