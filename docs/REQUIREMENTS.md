# Requirements (Project-I, B-lite)

**Updated:** 2026-10-26  
**Priority labels:** Must / Should / Could / Out of scope.

A requirement is accepted only if its **acceptance criteria** can be checked. Metrics are measured from the run store, never pre-filled.

## Actors

- **Experimenter:** generates data, runs collector, trains, evaluates.
- **Demo operator:** examiner or student running the viva path.
- **System:** CLI + library. No login.

## Functional requirements

| ID | Priority | Requirement | Acceptance |
| --- | --- | --- | --- |
| FR-01 | Must | Typed workload, objective, configuration, estimate, decision, run-result contracts | Invalid payloads raise validation errors; tests exist |
| FR-02 | Must | Enumerate the **declared 8** Dask configs only | No 9th config in the scorer without an ADR |
| FR-03 | Must | Start `LocalCluster` with explicit `n_workers`, `threads_per_worker`, `memory_limit` | T0 log shows those values — **open** (script exists, not run on 16 GB) |
| FR-04 | Must | Execute one workload to completion, timeout, or OOM and persist a `RunResult` | Pandas JSONL **yes**; Dask persist **open** |
| FR-05 | Must | Recommend cheapest feasible candidate using **conformal upper ≤ SLA**, `p_fail ≤ limit`, OOD ≠ red | Unit tests: upper-bound, red abstain, min cost |
| FR-06 | Must | Abstain when the feasible set is empty | `action=abstain`, `config_id=null` |
| FR-07 | Must | Four synthetic Parquet families with seeds and sha256 | Tiny manifests **yes**; 150–250 MB **open** |
| FR-08 | Must | Store only pre-run features on the prediction path | Leakage audit script or checklist signed in T-AUDIT |
| FR-09 | Must | Treat timeout duration as censored, not success | Status `timeout`; runtime model training drops or censors it |
| FR-10 | Must | Compare policy vs default, conservative, random on the **same** table | Evaluation script; no extra physical runs required |
| FR-11 | Should | Leave-one-family OOD green/yellow/red | Four rotation reports |
| FR-12 | Should | SHAP explanation of LightGBM runtime for the demo | One saved figure + caption |
| FR-13 | Should | CLI: `profile`, `recommend`, `execute` (execute may wrap collector) | `--help` and one happy path |
| FR-14 | Could | TabPFN on Colab vs LightGBM | Table **or** explicit “not run” |
| FR-15 | Could | Streamlit screen | Not required for Project-I pass |
| FR-16 | Out | Glue JobRun / DPU cost | Must not appear as measured results |
| FR-17 | Out | LLM parser / Spark | — |

## User stories

1. **As experimenter**, I run T0 so I know Dask starts on the 16 GB PC.  
   *Done when:* `reports/t0.md` has OS, RAM, Dask version, elapsed.
2. **As experimenter**, I generate four versioned datasets.  
   *Done when:* manifest fingerprints match files on disk.
3. **As experimenter**, I collect 96 runs one-at-a-time in random order.  
   *Done when:* parquet row count = 96 (or documented slip).
4. **As demo operator**, I pass a workload profile and SLA and get recommend or abstain with a reason.  
   *Done when:* CLI prints `Decision` JSON from fitted artifacts (or labeled fixture if models missing).
5. **As demo operator**, I execute the recommended (or fallback) config on a **small** sample and see predicted vs actual from the **frozen** table for the full matrix.

## Inputs, outputs, errors

| Flow | Input | Output | Error behavior |
| --- | --- | --- | --- |
| recommend | estimates JSON or fitted models + WorkloadSpec + ObjectiveSpec | `Decision` | Empty set → abstain; invalid JSON → exit 1 |
| execute | config_id + workload id | `RunResult` | Timeout → status timeout; worker death → oom/error classified |
| train | curated parquet | model artifacts + metrics JSON | Too few successes → refuse to fit, keep baseline |

Hard job timeout: wall clock from T0b (default proposal **1.5 × median 2g success**, frozen **before** scoring the optimizer).

## Non-functional

| ID | Priority | NFR | Target |
| --- | --- | --- | --- |
| NFR-01 | Must | Optimizer latency | < 1 s for 8 candidates after load |
| NFR-02 | Must | Isolation | One Dask job at a time on the experiment PC |
| NFR-03 | Must | Reproducibility | Seeds in manifest; pinned deps in `pyproject.toml` |
| NFR-04 | Must | Privacy | Synthetic data only; no AWS keys |
| NFR-05 | Must | Honesty | Report language matches single-PC memory-capped Dask |
| NFR-06 | Should | Host stability | Disable sleep during matrix; log start/end |
| NFR-07 | Should | Testability | Collector logic unit-tested without a cluster where possible |

## Security / privacy

No production data. No cloud credentials in the repo. `.env` gitignored.

## Explicit non-goals

Glue evaluation, multi-node Dask, live adaptive control as the learned policy, claiming optimality outside the eight configs.
