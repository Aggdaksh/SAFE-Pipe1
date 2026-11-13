# Research probe development screen

Recorded 768 / 768 planned cells.

Statuses: `{'success': 759, 'timeout': 1, 'execution_error': 8}`.

**This report does not establish novelty, spill reduction, or online policy improvement.**

| Instance | Proxy | Aligned / inverted / unresolved pairs | Proxy choice | Full-engine regret |
| --- | --- | --- | --- | --- |
| groupby-1000000-balanced | uniform | 16 / 1 / 11 | w2_t2_2g | 6.82% |
| groupby-1000000-balanced | uniform_memory | 12 / 2 / 14 | w2_t2_2g | 6.82% |
| groupby-1000000-balanced | partition_tail | 17 / 0 / 11 | w2_t2_2g | 6.82% |
| groupby-1000000-uneven | uniform | 8 / 0 / 20 | w2_t2_2g | 10.50% |
| groupby-1000000-uneven | uniform_memory | 11 / 1 / 16 | w2_t2_2g | 10.50% |
| groupby-1000000-uneven | partition_tail | 7 / 2 / 19 | w2_t1_1g | 18.99% |
| groupby-2000000-balanced | uniform | 19 / 0 / 9 | w2_t2_1g | 1.54% |
| groupby-2000000-balanced | uniform_memory | 14 / 0 / 14 | w2_t2_2g | 0.00% |
| groupby-2000000-balanced | partition_tail | 20 / 0 / 8 | w2_t2_2g | 0.00% |
| groupby-2000000-uneven | uniform | Incomplete or failed | — | — |
| groupby-2000000-uneven | uniform_memory | Incomplete or failed | — | — |
| groupby-2000000-uneven | partition_tail | Incomplete or failed | — | — |
| groupby-500000-balanced | uniform | 10 / 4 / 14 | w2_t1_2g | 6.90% |
| groupby-500000-balanced | uniform_memory | 14 / 0 / 14 | w2_t2_2g | 0.00% |
| groupby-500000-balanced | partition_tail | 13 / 3 / 12 | w2_t1_1g | 20.65% |
| groupby-500000-uneven | uniform | 7 / 2 / 19 | w2_t2_2g | 0.34% |
| groupby-500000-uneven | uniform_memory | 9 / 2 / 17 | w2_t1_2g | 0.00% |
| groupby-500000-uneven | partition_tail | 8 / 3 / 17 | w1_t2_1g | 9.51% |
| skewed_join-1000000-balanced | uniform | 12 / 0 / 16 | w2_t2_2g | 6.20% |
| skewed_join-1000000-balanced | uniform_memory | 12 / 1 / 15 | w2_t2_1g | 0.00% |
| skewed_join-1000000-balanced | partition_tail | 17 / 0 / 11 | w2_t2_1g | 0.00% |
| skewed_join-1000000-uneven | uniform | 7 / 0 / 21 | w2_t2_1g | 0.00% |
| skewed_join-1000000-uneven | uniform_memory | 15 / 1 / 12 | w2_t2_2g | 5.94% |
| skewed_join-1000000-uneven | partition_tail | 5 / 0 / 23 | w2_t2_1g | 0.00% |
| skewed_join-2000000-balanced | uniform | 7 / 1 / 20 | w2_t2_1g | 17.37% |
| skewed_join-2000000-balanced | uniform_memory | 13 / 1 / 14 | w2_t2_1g | 17.37% |
| skewed_join-2000000-balanced | partition_tail | 15 / 1 / 12 | w2_t1_1g | 11.09% |
| skewed_join-2000000-uneven | uniform | Incomplete or failed | — | — |
| skewed_join-2000000-uneven | uniform_memory | Incomplete or failed | — | — |
| skewed_join-2000000-uneven | partition_tail | Incomplete or failed | — | — |
| skewed_join-500000-balanced | uniform | 7 / 1 / 20 | w2_t2_1g | 0.23% |
| skewed_join-500000-balanced | uniform_memory | 8 / 0 / 20 | w2_t2_1g | 0.23% |
| skewed_join-500000-balanced | partition_tail | 12 / 0 / 16 | w2_t1_1g | 6.75% |
| skewed_join-500000-uneven | uniform | 7 / 0 / 21 | w2_t2_1g | 0.00% |
| skewed_join-500000-uneven | uniform_memory | 11 / 2 / 15 | w2_t2_1g | 0.00% |
| skewed_join-500000-uneven | partition_tail | 3 / 0 / 25 | w2_t1_1g | 23.78% |

## Interpretation limits

- Development proxy-ranking screen, not an adaptive-policy evaluation or a novelty result.
- Ranks use execution time after cluster setup; all lifecycle timing remains in raw records.
- A decisive pair requires > tolerance median gap and nonoverlapping observed repeat ranges; not a statistical confidence interval.
- All candidates/repeats must succeed for a numerical ranking comparison; failures/incomplete groups are not silently dropped.
- Full and probe outcomes share instances: this is paired descriptive analysis, not held-out prediction accuracy.
- No end-to-end savings or deadline guarantee is computed from this matrix.
- Large input partitions are a heuristic for expensive work, not measured post-shuffle working sets.

Inspect worker telemetry, graph signatures, actual sample row/byte budgets and failures before interpreting any ranking change.
