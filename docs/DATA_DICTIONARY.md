# Main-v1 data dictionary

This document describes the committed [run table](../data/curated/runs.csv), its frozen model inputs, and the newer advisor's resource accounting. It does not redefine the historical data.

## What was measured

There are **96 physical executions of four synthetic workload profiles**: four families × eight configurations × three repeats. There are 32 distinct `(family, config_id)` cells, with three repeated executions per cell. The audit's `unique_cells=96` counts `(family, config_id, repeat_id)` triples; it does not mean 96 independent workloads.

All rows use `data_version=main-v1`, `backend=dask_local`, and `hardware_class=windows_32gb`. All 96 statuses are `success`, all 96 `sla_miss` values are false, and all 96 `peak_memory_bytes` values are missing. Failure outcomes were recorded as success; there are no observed failures from which to fit a failure classifier and no measured peak-memory labels.

The physical host was Windows 11 build 26200, with 16 logical processors and 33,711,480,832 bytes of RAM (31.4 GiB). Recorded versions were Python 3.14.6, Dask/distributed 2026.8.0, pandas 3.1.0, and pyarrow 26.0.0. See [T0 evidence](../reports/t0.md) and [host decision](adr/ADR-005-experiment-host-32gb.md). These measurements do not establish performance on the coding Mac or another PC. `hardware_class` is assigned by the audit exporter, not discovered from each CSV row; the original raw log contains the host/OS string.

## The four frozen profiles

The complete manifests, including dataset hashes, are in [datasets_main_v1.json](../configs/datasets_main_v1.json). `input_bytes` is the total compressed Parquet file size on disk.

| Family | Manifest rows | Input bytes | Manifest files | Seed | Frozen engine SLA |
| --- | ---: | ---: | ---: | ---: | ---: |
| `scan_filter` | 23,320,000 | 198,446,552 | 16 | 47 | 2.6 s |
| `groupby` | 14,970,000 | 198,487,831 | 16 | 48 | 7.9 s |
| `skewed_join` | 17,040,000 | 174,604,451 | 16 | 49 | 4.3 s |
| `sort_merge` | 12,770,000 | 178,382,606 | 16 | 50 | 13.1 s |

The operations in [execute_dask.py](../safe_pipe/workloads/execute_dask.py) are a filtered mean, grouped sum followed by a mean, an inner join followed by a payload sum, and a `set_index` shuffle with per-partition scalar extraction respectively. `sort_merge` is the project's family label; its implementation does not perform a second-table merge. The scan operation filters `value > 0.5`; the generated `flag` column is not used in that filter.

## CSV columns

“Feature” below means the column is in the explicit [pre-run whitelist](../safe_pipe/features.py). Other columns are provenance, objectives, or post-run observations and must not be silently added to the training feature matrix.

| Column | Meaning and units | Role / caveat |
| --- | --- | --- |
| `run_id` | UUID of one execution | Provenance; not a model feature. |
| `family` | One of the four workload-family names | Feature; not a unique workload-instance identifier in a future expanded dataset. |
| `config_id` | For example, `w2_t1_2g` means two workers, one thread each, `2GB` per worker | Feature; identifies one of eight frozen configurations. |
| `repeat_id` | Integer 1, 2, or 3 within a family/configuration cell | Provenance; repeats share the same dataset. |
| `data_version` | `main-v1` | Provenance; does not distinguish later repetitions of the same input data. Use a separate evaluation/run-set identifier for those. |
| `hardware_class` | Exported label `windows_32gb` | Provenance; not a hardware benchmark or a portable performance guarantee. |
| `backend` | `dask_local` | Provenance; local processes on one machine. |
| `input_bytes` | Sum of compressed Parquet file sizes, in bytes | Feature; includes both join inputs. Not decoded memory size or peak resident memory. |
| `estimated_rows` | Manifest `n_rows` | Feature; exact generated row count for single-table families; left-table rows only for the join. |
| `file_count` | Manifest `n_files` | Feature; 16 in all historical rows. Omits the join's additional right-table file. |
| `partition_count` | Copied from manifest `n_files` | Feature; declared input descriptor, not a measured execution-graph partition count. |
| `skew_score` | Fixed tag: `1.2` for `skewed_join`, `0.1` otherwise | Feature; not a statistic calculated from the data. See the skew caveat below. |
| `dataset_sha256` | Hash from the frozen family manifest | Provenance; refers to Parquet contents, not the run table. |
| `n_workers` | 1 or 2 worker processes | Feature; `processes=True` in the frozen grid. |
| `threads_per_worker` | 1 or 2 configured worker threads | Feature; does not measure CPU utilization. |
| `memory_limit` | Native Dask string, `1GB` or `2GB`, per worker | Provenance/resource setting; Dask interprets these as decimal GB. |
| `memory_limit_gb` | Historical numeric encoding, 1.0 or 2.0 | Feature; produced by the legacy parser, which interprets `GB` as binary then divides by 2^30. Preserve this encoding for the frozen model. |
| `allocated_vcpus` | `n_workers × threads_per_worker`, values 1, 2, or 4 | Feature; historical name for configured threads, not dedicated/reserved vCPUs. |
| `allocated_gb` | `n_workers × memory_limit_gb`, values 1.0, 2.0, or 4.0 | Feature; legacy nominal resource encoding, not measured memory consumption. |
| `sla_seconds` | Frozen engine deadline for the family | Objective; chosen from separate pilots, not a runtime feature. |
| `status` | Execution outcome; all historical values are `success` | Post-run label. Schema also permits timeout/OOM/spill-abort/error; those outcomes are absent here. |
| `failure_category` | Classified failure type; all historical values are `none` | Post-run label, not a predicted probability. |
| `engine_seconds` | Elapsed seconds from graph construction to completed scalar result | Runtime label; starts after `LocalCluster` and client creation, and excludes cluster startup/teardown and data generation/profiling. |
| `sla_miss` | True if status is not success or engine runtime exceeds the frozen SLA | Derived post-run label; all historical values are false. |
| `peak_memory_bytes` | Intended peak-memory observation | Missing in every row. Missing does not mean zero memory use. |

The SLAs were frozen as 1.5 times the median of three `w1_t1_2g` pilot engine times, rounded up to 0.1 seconds. Those pilot executions are separate from the 96 scored rows. See [family_sla_main_v1.json](../configs/family_sla_main_v1.json).

## Descriptor and unit limitations

**Join dimensions:** the join generator creates 17,040,000 left rows and `max(32, n_rows // 20) = 852,000` right rows. It writes 16 left files and one right file: 17 physical files and 17,892,000 total input rows. The frozen descriptor still says 16 files/partitions and 17,040,000 rows, while its byte count includes both sides. Do not present those descriptor fields as complete join dimensions or silently correct the frozen model's inputs. A future feature version should record left/right rows, files, and bytes separately.

**Skew:** the generator samples left join keys with NumPy's Zipf parameter `1.5`; the recorded `skew_score=1.2` is a manually assigned family tag. These numbers describe different things. A future version should record the generator parameter separately from a defined measured statistic, such as maximum key frequency divided by row count. Other families' `0.1` tags are also not measured skew statistics.

**Memory:** Dask's `1GB` is 1,000,000,000 bytes, approximately 0.9313 GiB; `1GiB` is 1,073,741,824 bytes. The frozen numeric features retain the old nominal values for compatibility. The advisor uses [dask_memory_bytes](../safe_pipe/memory.py) for new resource accounting, reports actual configured bytes and decimal `total_memory_gb`, and interprets `--max-memory-gb` in decimal GB. Neither legacy nor new resource totals measure actual memory consumption. The coarse input-bytes guard cannot establish per-worker peak-memory safety. See [Dask's unit definitions](https://docs.dask.org/en/stable/_modules/dask/utils.html#parse_bytes) and [worker memory behavior](https://distributed.dask.org/en/stable/worker-memory.html).

**Identity:** a `WorkloadSpec` contains family, bytes, rows, file/partition counts, skew tag, and format, but no dataset hash or hardware fingerprint. The advisor compares all of those descriptor values against the four frozen profiles and rejects mismatches. Matching descriptors alone do not prove matching contents or host compatibility. For execution, verify the actual manifest and dataset bytes as well.

## Model and advisor evidence

The historical split contains 36 training rows, 36 calibration rows, and 24 test rows. All three repeats of each family/configuration cell stay together, giving 12 training, 12 calibration, and eight test cells. All splits still share the same four workload profiles. This evaluates configuration-cell interpolation within those profiles; it is not a held-out-workload or held-out-host experiment.

The frozen predictor models log successful runtime. Its point output is an exponentiated model prediction, not a guaranteed arithmetic expected runtime. Its upper estimate is the point multiplied by approximately 1.688 for every candidate. Observed coverage of 24/24 test rows is descriptive and does not establish a 90% guarantee for future selected recommendations. The advisor reports `failure_probability=null`, and policy weights are declared preferences rather than trained coefficients.

The new policy, resource normalization, explanations, and preference modes do **not** require retraining the existing runtime model. Correcting historical feature semantics or expanding workload/hardware support does require a versioned dataset, new fitting/calibration, and separate evaluation. See [the validation plan](INDEPENDENT_VALIDATION.md).
