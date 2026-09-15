"""Frozen contract for post-design web actions.

The action contract is intentionally independent of Celery and Pipeline
objects.  It is the boundary used by future Capacitor, Magnetics, Waveforms
and Efficiency Sweep endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .design import DesignError


class DesignAction(StrEnum):
    capacitor = "capacitor"
    magnetics = "magnetics"
    waveforms = "waveforms"
    efficiency_sweep = "efficiency_sweep"


class ActionStatus(StrEnum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    expired = "expired"


class OperatingPointRequest(BaseModel):
    """Operating-point inputs used by waveform refresh."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    vin_v: float = Field(gt=0, description="Operating input voltage, V")
    load_ratio: float = Field(ge=0, description="Per-unit load ratio")


class DesignActionRequest(BaseModel):
    """Request envelope shared by all post-design action endpoints."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    job_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    action: DesignAction
    operating_point: OperatingPointRequest | None = None
    options: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_action_inputs(self) -> "DesignActionRequest":
        if self.action is DesignAction.waveforms and self.operating_point is None:
            raise ValueError("operating_point is required for waveforms")
        if self.action is not DesignAction.waveforms and self.operating_point is not None:
            raise ValueError("operating_point is only supported for waveforms")
        for key, value in self.options.items():
            if key != "llc_search_mode":
                raise ValueError(f"Unsupported action option: {key}")
            if self.action is not DesignAction.magnetics:
                raise ValueError("llc_search_mode is only supported for magnetics")
            if not isinstance(value, str) or value not in {"fast", "full"}:
                raise ValueError("llc_search_mode must be fast or full")
        return self


class DesignActionResponse(BaseModel):
    """Persisted action status returned by the API."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    action_id: str
    job_id: str
    action: DesignAction
    status: ActionStatus
    progress: int = Field(ge=0, le=100)
    stage: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: DesignError | None = None
    result_url: str | None = None
    artifacts_url: str | None = None


ACTION_DEPENDENCIES: dict[DesignAction, frozenset[str]] = {
    DesignAction.capacitor: frozenset({"design"}),
    DesignAction.magnetics: frozenset({"design"}),
    DesignAction.waveforms: frozenset({"design"}),
    DesignAction.efficiency_sweep: frozenset({"design"}),
}

ACTION_STAGES: dict[DesignAction, tuple[str, ...]] = {
    DesignAction.capacitor: ("validate", "capacitor", "geometry", "report", "finalize"),
    DesignAction.magnetics: ("validate", "magnetic_search", "ranking", "geometry", "report", "finalize"),
    DesignAction.waveforms: ("validate", "operating_point", "waveform", "loss_refresh", "report", "finalize"),
    DesignAction.efficiency_sweep: ("validate", "fixed_hardware", "sweep", "summarize", "report", "finalize"),
}


def action_dependencies(action: DesignAction) -> frozenset[str]:
    return ACTION_DEPENDENCIES[action]


def action_stages(action: DesignAction) -> tuple[str, ...]:
    return ACTION_STAGES[action]


_ALLOWED_TRANSITIONS: dict[ActionStatus, frozenset[ActionStatus]] = {
    ActionStatus.queued: frozenset({ActionStatus.running, ActionStatus.failed, ActionStatus.cancelled, ActionStatus.expired}),
    ActionStatus.running: frozenset({ActionStatus.succeeded, ActionStatus.failed, ActionStatus.cancelled}),
    ActionStatus.succeeded: frozenset({ActionStatus.expired}),
    ActionStatus.failed: frozenset({ActionStatus.expired}),
    ActionStatus.cancelled: frozenset({ActionStatus.expired}),
    ActionStatus.expired: frozenset(),
}


def validate_action_transition(current: ActionStatus, target: ActionStatus) -> None:
    """Raise ValueError unless an action state transition is allowed."""

    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Invalid action status transition: {current} -> {target}")
