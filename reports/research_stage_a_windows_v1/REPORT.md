# Stage A mechanism diagnosis

Recorded 48 / 48 planned attempts.

All statuses and condition flags are retained. No probe ranking or controller benefit is inferred.

| Instance | Config | Observed / planned | Statuses | Spill positive / unknown | Nanny memory positive | Condition flags |
| --- | --- | --- | --- | --- | --- | --- |
| groupby-2000000-balanced-s911 | w2_t1_1g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| groupby-2000000-balanced-s911 | w2_t1_2g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| groupby-2000000-key_skew_only-s911 | w2_t1_1g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| groupby-2000000-key_skew_only-s911 | w2_t1_2g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| groupby-2000000-partition_imbalance_only-s911 | w2_t1_1g | 3 / 3 | {'execution_error': 3} | 3 / 0 | 3 | 0 |
| groupby-2000000-partition_imbalance_only-s911 | w2_t1_2g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| groupby-2000000-both-s911 | w2_t1_1g | 3 / 3 | {'success': 3} | 3 / 0 | 1 | 0 |
| groupby-2000000-both-s911 | w2_t1_2g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| skewed_join-2000000-balanced-s911 | w2_t1_1g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| skewed_join-2000000-balanced-s911 | w2_t1_2g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| skewed_join-2000000-key_skew_only-s911 | w2_t1_1g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| skewed_join-2000000-key_skew_only-s911 | w2_t1_2g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| skewed_join-2000000-partition_imbalance_only-s911 | w2_t1_1g | 3 / 3 | {'success': 2, 'execution_error': 1} | 3 / 0 | 2 | 0 |
| skewed_join-2000000-partition_imbalance_only-s911 | w2_t1_2g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |
| skewed_join-2000000-both-s911 | w2_t1_1g | 3 / 3 | {'execution_error': 3} | 3 / 0 | 3 | 0 |
| skewed_join-2000000-both-s911 | w2_t1_2g | 3 / 3 | {'success': 3} | 0 / 0 | 0 | 0 |

Inconsistent successful scalar results: []

MANUAL REVIEW REQUIRED; no automatic Stage B or model training

One generation seed and three runtime repeats. This isolates declared factors; it is not an independent final study or proof of general failure probability. Result agreement across configs is a consistency check, not a large-input correctness oracle.
