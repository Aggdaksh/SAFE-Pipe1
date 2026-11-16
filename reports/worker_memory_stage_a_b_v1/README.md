# Stage A/B worker memory export

Read-only export of the existing Windows attempts. No benchmarks, datasets, models or main merge.

| Stage | Runs (success/error) | Worker lifetimes | Initial / added | Verified diagnostic files | Nanny messages |
| --- | --- | --- | --- | --- | --- |
| A | 48 (41/7) | 129 | 96 / 33 | 546 | 37 |
| B | 96 (96/0) | 192 | 192 / 0 | 961 | 0 |

Integrity checks: **PASS**. Rehashed 1515 original evidence/anchor files after reading; all unchanged.

- Plan canonical hashes, exact published plans, cell identities, raw JSONL byte hashes and original completion counts/statuses checked. All declared diagnostic file byte sizes/SHA-256 hashes checked. Nanny messages checked against retained raw supervisor logs.
- Hash anchors: Stage A is pinned by the frozen Stage B reference; Stage B by its published completion audit. These are integrity checks against saved evidence, not independent signatures. Full hashes and issues are in [verification.json](verification.json).

## Files and interpretation

- [workers.csv](workers.csv) and [workers.json](workers.json): identical worker-lifetime rows. [runs.json](runs.json) covers every run, including any run with no worker record, and preserves unmatched evidence.
- Every lifetime has a stable per-cell ID, ordered by plugin start time. `initial` and `added_during_run` come from scheduler events. Added lifetimes stay separate; no worker-slot or parent/replacement pairing is inferred. PID/address/local paths are omitted. Snapshot and canonical worker/event hashes allow linkage to retained local evidence.
- Missing measurements are JSON `null` / blank CSV cells, never substituted with zero. Empty event lists mean no matched retained event. Measured zeros and false/disabled thresholds remain intact. Parent-dataset hash is null for Stage A full inputs (not applicable). Counts of absent worker fields and missing/mismatched files appear below and in verification.json.
- All memory sizes are bytes. Target config caps differ from Stage B's mapped effective caps; both are retained. Worker `effective_memory_limit_bytes` is the measured worker setting. `memory_settings` holds target/spill/pause/terminate fractions, monitor interval and max-spill. Nested CSV values are compact JSON.
- Baseline RSS is the first plugin sample, not a guaranteed idle baseline. RSS/managed/spill peaks are per lifetime, not synchronized cluster peaks. Do not subtract unrelated peaks to infer unmanaged memory. Window includes graph build, execution and cleanup; sampling is 50 ms with snapshots persisted every 0.25 s. Abrupt deaths can leave incomplete snapshots and brief peaks can be missed.
- Worker evidence is attributed by raw PID/address (and time when needed), then anonymized. Ambiguous/unmatched events remain at run level. A nanny memory-budget restart is not proof of OS OOM. Run success can coexist with worker restarts; no event is not proof that no event occurred.

## Missing data / verification exceptions

- Stage A: missing worker fields {}; diagnostic-only 0, telemetry-only 0; unmatched evidence 0; verification issues 0.
- Stage B: missing worker fields {}; diagnostic-only 0, telemetry-only 0; unmatched evidence 0; verification issues 0.

## Reproduce without executing workloads

```powershell
.\.venv-research\Scripts\python.exe -m experiments.export_worker_memory --out reports/worker_memory_stage_a_b_new
.\.venv-research\Scripts\python.exe -m pytest -q tests/test_worker_memory_export.py
```

The destination must be empty. Only this exporter and synthetic exporter tests are invoked; raw inputs stay ignored and preserved locally. Dataset contents, frozen source/runtime compatibility and model quality are outside this export's verification scope.
