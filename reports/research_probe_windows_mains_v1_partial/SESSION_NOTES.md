# Mains-powered Windows development screen

- Started 2026-11-13 (Asia/Kolkata), research source commit `5516d1a`; exact revision and packages saved before execution.
- Original Windows PC: 31.4 GiB physical RAM; about 15.5 GiB available before preparation.
- Mains connection verified after the user plugged in the PC. Windows power scheme: Balanced. `conditions.jsonl` samples mains/battery, available RAM and free disk about every two seconds during batches.
- Prepared in a new directory; the earlier 36-cell power-uncertain diagnostic plan remains intact and is excluded from this study.
- Filesystem cache and background activity are not controlled. Preparation and hash checks may warm the cache. This remains an exploratory development screen, with two repeats per cell.
- `advance.py` invokes the unchanged runner in batches (four initially, then at most 32). It stops between batches on non-success outcomes, cleanup leftovers, observed power disconnection, low disk, or command errors. Individual jobs retain the original supervisor timeout and host-memory checks.

## First bounded checkpoint

- Recorded 36/768 cells: 35 successes and one execution timeout. The monitor then stopped as designed; no job remains active.
- During the full `skewed_join-2000000-uneven` / `w1_t2_1g` / repeat 1 attempt, 23 condition samples reported unplugged power, from 15:24:35 to 15:25:19 UTC (about 44 seconds between first and last observed samples). Power was connected again afterward. This attempt is power-confounded; do not attribute its timeout solely to memory or compare it as a controlled mains run.
- That job hit the 180-second wall limit, observed at least three worker restarts, and reported about 1.365 GB summed sampled stored-spill peaks across worker lifetimes. Cleanup recorded zero owned descendants. Preserve the timeout as a censored failure outcome.
- Available RAM stayed above 14.4 GiB and free disk above 59.3 GiB in the sampled interval. No disk/memory-host refusal occurred.
- This is a partial development checkpoint with a power-state limitation. Confirm a stable charger before further batches; keep all recorded cells and power samples intact.

## Resumed batch

- The user confirmed charger stability. The controller added temporary system-awake handling and a batch-boundary `pause.requested` marker, then ran 32 further cells with no sampled power/disk violation.
- Total is now 68/768: 66 successes, one timeout, one execution error. The new error is the full uneven two-million-row join at `w2_t1_1g`: Dask reported `KilledWorker` after a shuffle task lost four workers; observed restart lower bound was five. Stored-spill lifetime peaks summed to about 1.489 GB. Cleanup left zero owned descendants.
- The controller stopped for inspection. Keep the ambiguous worker-death label as `execution_error`; do not infer confirmed OOM or silently retry the cell.
