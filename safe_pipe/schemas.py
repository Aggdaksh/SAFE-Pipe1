from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class WorkloadFamily(str, Enum):
    SCAN_FILTER = "scan_filter"
    GROUPBY = "groupby"
    SKEWED_JOIN = "skewed_join"
    SORT_MERGE = "sort_merge"


class OODState(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class RunStatus(str, Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    OOM = "oom"
    SPILL_ABORT = "spill_abort"
    ERROR = "error"


class DecisionAction(str, Enum):
    RECOMMEND = "recommend"
    ABSTAIN = "abstain"


class WorkloadSpec(BaseModel):
    family: WorkloadFamily
    input_bytes: int = Field(gt=0)
    estimated_rows: int = Field(gt=0)
    file_count: int = Field(gt=0)
    partition_count: int = Field(gt=0)
    skew_score: float = Field(ge=0.0)
    format: str = "parquet"

    @field_validator("format")
    @classmethod
    def format_lower(cls, value: str) -> str:
        return value.lower()


class ObjectiveSpec(BaseModel):
    sla_seconds: float = Field(gt=0)
    failure_limit: float = Field(ge=0.0, le=1.0, default=0.1)
    retry_limit: int = Field(ge=0, default=1)


class DaskNativeConfig(BaseModel):
    n_workers: int = Field(ge=1, le=2)
    threads_per_worker: int = Field(ge=1, le=4)
    memory_limit: str
    processes: bool = True


class ConfigurationSpec(BaseModel):
    config_id: str
    native: DaskNativeConfig
    allocated_vcpus: float = Field(gt=0)
    allocated_gb: float = Field(gt=0)


class CandidateEstimate(BaseModel):
    config_id: str
    expected_runtime_s: float = Field(gt=0)
    runtime_upper_s: float = Field(gt=0)
    p_fail: float = Field(ge=0.0, le=1.0)
    expected_cost: float = Field(ge=0)
    ood_state: OODState

    @field_validator("runtime_upper_s")
    @classmethod
    def upper_at_least_point(cls, value: float, info: Any) -> float:
        point = info.data.get("expected_runtime_s")
        if point is not None and value < point:
            raise ValueError("runtime_upper_s must be >= expected_runtime_s")
        return value


class Decision(BaseModel):
    action: DecisionAction
    config_id: str | None = None
    reason: str
    feasible_config_ids: list[str] = Field(default_factory=list)


class RunResult(BaseModel):
    run_id: str
    workload: WorkloadSpec
    config: ConfigurationSpec
    status: RunStatus
    engine_seconds: float | None = None
    peak_memory_bytes: int | None = None
    notes: str = ""
