# Windows screen with continuous power monitoring: partial checkpoint

Recorded 2026-11-13 on the original Windows experiment PC, source revision `5516d1a`. This new plan is separate from the first 36-cell battery-uncertain diagnostic plan. It began with verified mains power and logged power, available RAM and free disk about every two seconds.

**68/768 cells recorded: 66 successes, one timeout, and one execution error.** The first batch stopped for a timeout and an observed mains disconnection. After charger confirmation, the next 32 cells had continuously observed mains power and recorded 31 successes plus one `KilledWorker` execution error. The monitor stopped again for inspection. No full method-ranking comparison is complete. No new model or adaptive policy was trained.

## Power transition and timeout

The full two-million-row uneven join at `w1_t2_1g`, repeat 1, ran from 15:24:21 to 15:27:21 UTC. During it, 23 power samples reported unplugged, from approximately 15:24:35 to 15:25:19 UTC. Mains power returned afterward. The attempt is therefore power-confounded: the recorded timeout cannot be attributed solely to memory pressure or used as a controlled mains comparison.

The supervisor retained a **180-second timeout**, at least **three worker restarts**, and about **1.365 GB summed sampled stored-spill peaks across worker lifetimes**. These sums are not concurrent process or disk peaks. Cleanup recorded **zero owned descendants**. Failed/timeout results remain visible and must not be overwritten or selectively retried in this plan.

Sampled available RAM stayed above 14.4 GiB and free disk above 59.3 GiB. The monitor's condition violation was power loss, not low disk. The new prepared datasets occupy about **3.39 GiB**; together with the previous diagnostic plan they occupy about **6.78 GiB**. Run logs and summaries are small relative to these inputs. Temporary spill requires additional working space.

## Evidence and next action

[Measurements](measurements.csv), [plan](plan.json), [summary](summary.json), [report](REPORT.md), [power/disk samples](conditions.jsonl), [batch controller](advance.py), [session notes](SESSION_NOTES.md), [packages](requirements.txt), and [source revision](revision.txt) preserve this checkpoint. Generated data and full raw run records remain local under ignored `data/probes/windows-screen-mains-v1/`.

The research source and package environment are unchanged. The separate environment previously passed all 43 targeted research tests and the full suite with three skips; this execution checkpoint adds no code change. Confirm a secure mains connection before further jobs. Preserve this development plan and its flagged power interval; any clean follow-up comparison must declare a new independent design rather than replace this timeout. Do not prepare another full dataset automatically merely to erase the observation.

## Second batch: stable power and worker deaths

The next 32 cells had no sampled power/disk violation. The full `skewed_join-2000000-uneven` case at `w2_t1_1g`, repeat 1, recorded `execution_error`: Dask's `KilledWorker` said a shuffle task lost four different workers. Telemetry observed at least five worker restarts and about 1.489 GB summed sampled stored-spill peaks across lifetimes. Cleanup left zero owned descendants. Worker death alone does not prove an OOM, so the original error label is retained.

The included controller adds system-awake handling and a batch-boundary pause marker for resumed execution; those convenience features were added after the first 36 cells and do not change the research runner or frozen plan. This export now contains all 68 recorded cells. Inspect worker-death evidence before another bounded batch, preserve failures and flagged power intervals, and do not retry those recorded cells in this plan.

After that review, `--continue-reviewed-failures` was added to the local controller to allow contained timeouts and `KilledWorker` outcomes with zero surviving descendants while continuing other cells. Its outcome guards were checked with synthetic success, timeout, worker-death, unknown-error, interruption and cleanup-leftover records. This convenience update does not alter the 68 exported measurements or research source fingerprints. See [next steps](../../docs/research/NEXT_STEPS.md). The latest launch check again reported unplugged power, so no further cells have started yet.
