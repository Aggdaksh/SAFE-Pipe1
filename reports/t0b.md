# T0b: worker memory-cap pilot

**Date:** 2026-10-26  
**Host:** Windows experiment PC, 31.4 GiB physical RAM (see [`t0.md`](t0.md)).  
**Setup:** One Dask worker, one thread, memory limits 1 GB and 2 GB. Each job used a fresh LocalCluster. Times below cover Dask execution and exclude cluster startup. Parquet is synthetic and local. These are single pilot runs, not scored matrix rows.

| Family | Actual Parquet size | Rows | 1 GB | 2 GB | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| scan_filter | 44,547,517 B | 4,939,194 | 1.780 s | 1.255 s | both succeeded |
| scan_filter | 169,453,589 B | 19,756,775 | 2.056 s | 1.577 s | both succeeded |
| sort_merge | 136,434,035 B | 9,678,506 | 10.579 s | 4.529 s | both succeeded; 1 GB was 2.34× slower |

The 1 GB and 2 GB sort runs returned the same scalar (`8.084620051692642`). No OOM or measured spill was observed; the timing difference alone does not prove spill. The scan does not meaningfully stress the cap at these sizes.

**Scale decision:** Keep the declared 1–2 GB worker caps and three repeats. Target about 200 MB of Parquet for scan/filter and group-by, and 150–200 MB for sort/merge and skewed join. Calibrate each family from actual Parquet bytes and check one 2 GB pilot per family before starting the 96-run matrix. The 8 minute pilot threshold was not approached.

Raw probe JSONL and generated Parquet live under ignored `data/probes/`. Commands used `experiments/t0b_probe.py --experiment-host`, first at 50 MB scan, then 200 MB scan, then `--family sort_merge --target-mb 150` with separate output directories. Generator compression yielded actual sizes below the requested targets.
