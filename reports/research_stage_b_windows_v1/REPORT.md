# Stage B probe fidelity diagnosis

Recorded 96 / 96 attempts; statuses: {'success': 96}.

| Instance | Cap | Fraction | Full outcomes | Probe quiet / warning / unknown | Comparison |
| --- | --- | --- | --- | --- | --- |
| groupby-2000000-balanced-s911 | w2_t1_1g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-balanced-s911 | w2_t1_1g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-balanced-s911 | w2_t1_2g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-balanced-s911 | w2_t1_2g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-both-s911 | w2_t1_1g | 0.125 | {'success': 3} | 3 / 0 / 0 | false reassurance candidate |
| groupby-2000000-both-s911 | w2_t1_1g | 0.25 | {'success': 3} | 3 / 0 / 0 | false reassurance candidate |
| groupby-2000000-both-s911 | w2_t1_2g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-both-s911 | w2_t1_2g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-key_skew_only-s911 | w2_t1_1g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-key_skew_only-s911 | w2_t1_1g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-key_skew_only-s911 | w2_t1_2g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-key_skew_only-s911 | w2_t1_2g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-partition_imbalance_only-s911 | w2_t1_1g | 0.125 | {'execution_error': 3} | 3 / 0 / 0 | false reassurance candidate |
| groupby-2000000-partition_imbalance_only-s911 | w2_t1_1g | 0.25 | {'execution_error': 3} | 3 / 0 / 0 | false reassurance candidate |
| groupby-2000000-partition_imbalance_only-s911 | w2_t1_2g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| groupby-2000000-partition_imbalance_only-s911 | w2_t1_2g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-balanced-s911 | w2_t1_1g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-balanced-s911 | w2_t1_1g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-balanced-s911 | w2_t1_2g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-balanced-s911 | w2_t1_2g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-both-s911 | w2_t1_1g | 0.125 | {'execution_error': 3} | 3 / 0 / 0 | false reassurance candidate |
| skewed_join-2000000-both-s911 | w2_t1_1g | 0.25 | {'execution_error': 3} | 3 / 0 / 0 | false reassurance candidate |
| skewed_join-2000000-both-s911 | w2_t1_2g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-both-s911 | w2_t1_2g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-key_skew_only-s911 | w2_t1_1g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-key_skew_only-s911 | w2_t1_1g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-key_skew_only-s911 | w2_t1_2g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-key_skew_only-s911 | w2_t1_2g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-partition_imbalance_only-s911 | w2_t1_1g | 0.125 | {'success': 2, 'execution_error': 1} | 3 / 0 / 0 | false reassurance candidate |
| skewed_join-2000000-partition_imbalance_only-s911 | w2_t1_1g | 0.25 | {'success': 2, 'execution_error': 1} | 3 / 0 / 0 | false reassurance candidate |
| skewed_join-2000000-partition_imbalance_only-s911 | w2_t1_2g | 0.125 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |
| skewed_join-2000000-partition_imbalance_only-s911 | w2_t1_2g | 0.25 | {'success': 3} | 3 / 0 / 0 | no declared discrepancy |

## Baseline and probe-choice replay

No new selected full jobs were executed by this report. See summary.json for all costs and mixed outcomes.

| Instance | Rule | Choice | Full successes / attempts | Profiling seconds |
| --- | --- | --- | --- | --- |
| groupby-2000000-balanced-s911 | fixed_1gb | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-balanced-s911 | fixed_2gb | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-balanced-s911 | file_metadata | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-balanced-s911 | uniform_memory_f0125 | w2_t1_1g | 3 / 3 | 25.121 |
| groupby-2000000-balanced-s911 | uniform_memory_f0250 | w2_t1_1g | 3 / 3 | 24.277 |
| groupby-2000000-both-s911 | fixed_1gb | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-both-s911 | fixed_2gb | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-both-s911 | file_metadata | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-both-s911 | uniform_memory_f0125 | w2_t1_1g | 3 / 3 | 24.278 |
| groupby-2000000-both-s911 | uniform_memory_f0250 | w2_t1_1g | 3 / 3 | 26.255 |
| groupby-2000000-key_skew_only-s911 | fixed_1gb | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-key_skew_only-s911 | fixed_2gb | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-key_skew_only-s911 | file_metadata | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-key_skew_only-s911 | uniform_memory_f0125 | w2_t1_1g | 3 / 3 | 23.597 |
| groupby-2000000-key_skew_only-s911 | uniform_memory_f0250 | w2_t1_1g | 3 / 3 | 24.122 |
| groupby-2000000-partition_imbalance_only-s911 | fixed_1gb | w2_t1_1g | 0 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-partition_imbalance_only-s911 | fixed_2gb | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-partition_imbalance_only-s911 | file_metadata | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| groupby-2000000-partition_imbalance_only-s911 | uniform_memory_f0125 | w2_t1_1g | 0 / 3 | 24.650 |
| groupby-2000000-partition_imbalance_only-s911 | uniform_memory_f0250 | w2_t1_1g | 0 / 3 | 26.614 |
| skewed_join-2000000-balanced-s911 | fixed_1gb | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-balanced-s911 | fixed_2gb | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-balanced-s911 | file_metadata | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-balanced-s911 | uniform_memory_f0125 | w2_t1_1g | 3 / 3 | 25.267 |
| skewed_join-2000000-balanced-s911 | uniform_memory_f0250 | w2_t1_1g | 3 / 3 | 26.714 |
| skewed_join-2000000-both-s911 | fixed_1gb | w2_t1_1g | 0 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-both-s911 | fixed_2gb | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-both-s911 | file_metadata | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-both-s911 | uniform_memory_f0125 | w2_t1_1g | 0 / 3 | 25.114 |
| skewed_join-2000000-both-s911 | uniform_memory_f0250 | w2_t1_1g | 0 / 3 | 25.222 |
| skewed_join-2000000-key_skew_only-s911 | fixed_1gb | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-key_skew_only-s911 | fixed_2gb | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-key_skew_only-s911 | file_metadata | w2_t1_1g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-key_skew_only-s911 | uniform_memory_f0125 | w2_t1_1g | 3 / 3 | 23.988 |
| skewed_join-2000000-key_skew_only-s911 | uniform_memory_f0250 | w2_t1_1g | 3 / 3 | 27.298 |
| skewed_join-2000000-partition_imbalance_only-s911 | fixed_1gb | w2_t1_1g | 2 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-partition_imbalance_only-s911 | fixed_2gb | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-partition_imbalance_only-s911 | file_metadata | w2_t1_2g | 3 / 3 | no executed probes; rule overhead unmeasured |
| skewed_join-2000000-partition_imbalance_only-s911 | uniform_memory_f0125 | w2_t1_1g | 2 / 3 | 24.597 |
| skewed_join-2000000-partition_imbalance_only-s911 | uniform_memory_f0250 | w2_t1_1g | 2 / 3 | 26.502 |

Scalar inconsistencies within the same sample: []

- One generated seed, one non-nested sample per fraction, three runtime repeats; eight workload instances.
- Full references are historical Stage A executions; no synchronous repeat pairing or independent policy evaluation.
- Warning includes failure, nanny termination, spill, pauses or restarts; quality gaps are unknown, never quiet.
- Mixed full outcomes remain mixed; group discrepancy counts are not calibrated false-positive/negative rates.
- Join samples retain the entire dimension; scaled memory may create proxy-only pressure.
- Probe preparation is charged once per instance/fraction; three repeats per candidate are all charged in diagnostic replay.
- Configured GB-seconds/thread-seconds are lifecycle allocation proxies, not measured utilization; preparation resource use is unmeasured.
- Replays use historical full outcomes, exclude unmeasured controller/metadata overhead, and do not establish online savings.
- Stop after Stage B for review; no automatic training, Stage C or main merge.
