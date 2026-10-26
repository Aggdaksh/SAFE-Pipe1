# Main matrix preparation (before scored runs)

**Date:** 2026-10-26  
**Host:** Windows PC from [`t0.md`](t0.md).  
**Data version:** `main-v1`. Dataset manifests, SLA rules, and the randomized 96-cell order were frozen in `configs/` before starting scored runs.

| Family | Parquet bytes | Rows | Seed | SLA deadline |
| --- | ---: | ---: | ---: | ---: |
| scan_filter | 198,446,552 | 23,320,000 | 47 | 2.6 s |
| groupby | 198,487,831 | 14,970,000 | 48 | 7.9 s |
| skewed_join | 174,604,451 | 17,040,000 | 49 | 4.3 s |
| sort_merge | 178,382,606 | 12,770,000 | 50 | 13.1 s |

Each family uses 16 main Parquet parts (the join also has one dimension part). [`datasets_main_v1.json`](../configs/datasets_main_v1.json) contains full SHA-256 fingerprints; the matrix runner checks them against local files before a batch. All four physical datasets are within the planned 150–250 MB range. Parquet bytes are based on actual files, not logical dataframe sizes.

SLA deadlines use **1.5 × the median of three successful `w1_t1_2g` pilot engine times**, rounded up to 0.1 s. The 12 pilot runs were randomized, used a fresh LocalCluster for each run, and live only in ignored `data/probes/sla_main_v1/runs.jsonl`. Their times are committed in [`family_sla_main_v1.json`](../configs/family_sla_main_v1.json). They are excluded from the scored 96-row table. No family approached the 8 minute pilot threshold.

[`matrix_plan_main_v1.json`](../configs/matrix_plan_main_v1.json) fixes the 96-cell order with seed 2026. The runner executes one cell at a time, appends each result to ignored `data/runs/main_v1.jsonl`, and resumes by skipping completed cells. A batch defaults to 16 jobs. Worker limits remain 1–2 GB despite the 32 GB host.
