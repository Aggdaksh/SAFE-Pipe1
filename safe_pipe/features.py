"""Explicit pre-run feature whitelist for model fitting and inference."""

PRE_RUN_COLUMNS = (
    "family",
    "input_bytes",
    "estimated_rows",
    "file_count",
    "partition_count",
    "skew_score",
    "config_id",
    "n_workers",
    "threads_per_worker",
    "memory_limit_gb",
    "allocated_vcpus",
    "allocated_gb",
)

LABEL_COLUMNS = ("engine_seconds", "status", "failure_category", "sla_miss", "peak_memory_bytes")

assert not set(PRE_RUN_COLUMNS) & set(LABEL_COLUMNS)
