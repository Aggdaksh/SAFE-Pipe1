# Research probe development screen

Recorded 68 / 768 planned cells.

Statuses: `{'success': 66, 'timeout': 1, 'execution_error': 1}`.

**This report does not establish novelty, spill reduction, or online policy improvement.**

| Instance | Proxy | Aligned / inverted / unresolved pairs | Proxy choice | Full-engine regret |
| --- | --- | --- | --- | --- |
| groupby-1000000-balanced | uniform | Incomplete or failed | — | — |
| groupby-1000000-balanced | uniform_memory | Incomplete or failed | — | — |
| groupby-1000000-balanced | partition_tail | Incomplete or failed | — | — |
| groupby-1000000-uneven | uniform | Incomplete or failed | — | — |
| groupby-1000000-uneven | uniform_memory | Incomplete or failed | — | — |
| groupby-1000000-uneven | partition_tail | Incomplete or failed | — | — |
| groupby-2000000-balanced | uniform | Incomplete or failed | — | — |
| groupby-2000000-balanced | uniform_memory | Incomplete or failed | — | — |
| groupby-2000000-balanced | partition_tail | Incomplete or failed | — | — |
| groupby-2000000-uneven | uniform | Incomplete or failed | — | — |
| groupby-2000000-uneven | uniform_memory | Incomplete or failed | — | — |
| groupby-2000000-uneven | partition_tail | Incomplete or failed | — | — |
| groupby-500000-balanced | uniform | Incomplete or failed | — | — |
| groupby-500000-balanced | uniform_memory | Incomplete or failed | — | — |
| groupby-500000-balanced | partition_tail | Incomplete or failed | — | — |
| groupby-500000-uneven | uniform | Incomplete or failed | — | — |
| groupby-500000-uneven | uniform_memory | Incomplete or failed | — | — |
| groupby-500000-uneven | partition_tail | Incomplete or failed | — | — |
| skewed_join-1000000-balanced | uniform | Incomplete or failed | — | — |
| skewed_join-1000000-balanced | uniform_memory | Incomplete or failed | — | — |
| skewed_join-1000000-balanced | partition_tail | Incomplete or failed | — | — |
| skewed_join-1000000-uneven | uniform | Incomplete or failed | — | — |
| skewed_join-1000000-uneven | uniform_memory | Incomplete or failed | — | — |
| skewed_join-1000000-uneven | partition_tail | Incomplete or failed | — | — |
| skewed_join-2000000-balanced | uniform | Incomplete or failed | — | — |
| skewed_join-2000000-balanced | uniform_memory | Incomplete or failed | — | — |
| skewed_join-2000000-balanced | partition_tail | Incomplete or failed | — | — |
| skewed_join-2000000-uneven | uniform | Incomplete or failed | — | — |
| skewed_join-2000000-uneven | uniform_memory | Incomplete or failed | — | — |
| skewed_join-2000000-uneven | partition_tail | Incomplete or failed | — | — |
| skewed_join-500000-balanced | uniform | Incomplete or failed | — | — |
| skewed_join-500000-balanced | uniform_memory | Incomplete or failed | — | — |
| skewed_join-500000-balanced | partition_tail | Incomplete or failed | — | — |
| skewed_join-500000-uneven | uniform | Incomplete or failed | — | — |
| skewed_join-500000-uneven | uniform_memory | Incomplete or failed | — | — |
| skewed_join-500000-uneven | partition_tail | Incomplete or failed | — | — |

## Interpretation limits

- Development proxy-ranking screen, not an adaptive-policy evaluation or a novelty result.
- Ranks use execution time after cluster setup; all lifecycle timing remains in raw records.
- A decisive pair requires > tolerance median gap and nonoverlapping observed repeat ranges; not a statistical confidence interval.
- All candidates/repeats must succeed for a numerical ranking comparison; failures/incomplete groups are not silently dropped.
- Full and probe outcomes share instances: this is paired descriptive analysis, not held-out prediction accuracy.
- No end-to-end savings or deadline guarantee is computed from this matrix.
- Large input partitions are a heuristic for expensive work, not measured post-shuffle working sets.

Inspect worker telemetry, graph signatures, actual sample row/byte budgets and failures before interpreting any ranking change.
