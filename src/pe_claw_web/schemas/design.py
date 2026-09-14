from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
class DesignJobStatus(StrEnum):
    queued = "queued"; running = "running"; succeeded = "succeeded"; failed = "failed"; cancelled = "cancelled"; expired = "expired"
class BuckDesignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topology: Literal["buck_diode_rectified_unidirectional"] = "buck_diode_rectified_unidirectional"
    vin_min: float = Field(gt=0); vin_max: float = Field(gt=0); vout: float = Field(gt=0); pout: float = Field(gt=0); fs_khz: float = Field(gt=0)
    ripple_current_ratio: float = Field(gt=0); ripple_voltage_ratio_percent: float = Field(gt=0); options: dict[str, Any] = Field(default_factory=dict)
    @field_validator("vin_max")
    @classmethod
    def validate_voltage_window(cls, value: float, info: Any) -> float:
        vin_min = info.data.get("vin_min")
        if vin_min is not None and value < vin_min: raise ValueError("vin_max must be greater than or equal to vin_min")
        return value
class DesignJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request: BuckDesignRequest; client_request_id: str | None = Field(default=None, max_length=128)
class DesignError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str; message: str; correlation_id: str | None = None
class DesignJobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"; job_id: str; topology: str; status: DesignJobStatus; progress: int = Field(ge=0, le=100); stage: str | None = None; created_at: datetime; started_at: datetime | None = None; finished_at: datetime | None = None; error: DesignError | None = None; result_url: str | None = None; artifacts_url: str | None = None
class DesignResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"; job_id: str; topology: str; summary: dict[str, Any]; warnings: list[str] = Field(default_factory=list); artifacts: list[dict[str, Any]] = Field(default_factory=list)
