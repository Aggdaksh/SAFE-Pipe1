# Research probe development screen

Recorded 16 / 16 planned cells.

Statuses: `{'success': 16}`.

**This report does not establish novelty, spill reduction, or online policy improvement.**

| Instance | Proxy | Aligned / inverted / unresolved pairs | Proxy choice | Full-engine regret |
| --- | --- | --- | --- | --- |
| groupby-2048-uneven | uniform | 0 / 1 / 0 | w1_t1_1g | 5.32% |
| groupby-2048-uneven | uniform_memory | 0 / 0 / 1 | w1_t2_1g | 0.00% |
| groupby-2048-uneven | partition_tail | 0 / 0 / 1 | w1_t2_1g | 0.00% |
| skewed_join-2048-uneven | uniform | 1 / 0 / 0 | w1_t2_1g | 0.00% |
| skewed_join-2048-uneven | uniform_memory | 0 / 0 / 1 | w1_t2_1g | 0.00% |
| skewed_join-2048-uneven | partition_tail | 0 / 0 / 1 | w1_t2_1g | 0.00% |

## Interpretation limits

- Development proxy-ranking screen, not an adaptive-policy evaluation or a novelty result.
- Ranks use execution time after cluster setup; all lifecycle timing remains in raw records.
- A decisive pair requires > tolerance median gap and nonoverlapping observed repeat ranges; not a statistical confidence interval.
- All candidates/repeats must succeed for a numerical ranking comparison; failures/incomplete groups are not silently dropped.
- Full and probe outcomes share instances: this is paired descriptive analysis, not held-out prediction accuracy.
- No end-to-end savings or deadline guarantee is computed from this matrix.
- Large input partitions are a heuristic for expensive work, not measured post-shuffle working sets.

Inspect worker telemetry, graph signatures, actual sample row/byte budgets and failures before interpreting any ranking change.
