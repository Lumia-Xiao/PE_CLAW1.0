"""Shared duty policy for the isolated PSFB diode-rectifier topology."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal


DutyScope = Literal["design_point", "operating_point"]
_DUTY_TOLERANCE = 1e-9


@dataclass(frozen=True)
class PSFBDutyPolicyResult:
    """Auditable duty values and boundary status for one PSFB operating point."""

    scope: DutyScope
    effective_duty: float
    duty_loss: float
    command_duty: float
    max_effective_duty: float
    max_command_duty: float
    within_physical_range: bool
    duty_loss_consistent: bool
    within_configured_limits: bool
    status: str
    failure_reason: str | None

    @property
    def feasible(self) -> bool:
        """Return whether the duty values are physically and configurably valid."""

        return (
            self.within_physical_range
            and self.duty_loss_consistent
            and self.within_configured_limits
        )

    def as_dict(self) -> dict[str, object]:
        """Return stable metadata suitable for reports and structured output."""

        return {
            "scope": self.scope,
            "effective_duty": self.effective_duty,
            "duty_loss": self.duty_loss,
            "command_duty": self.command_duty,
            "max_effective_duty": self.max_effective_duty,
            "max_command_duty": self.max_command_duty,
            "within_physical_range": self.within_physical_range,
            "duty_loss_consistent": self.duty_loss_consistent,
            "within_configured_limits": self.within_configured_limits,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "feasible": self.feasible,
        }


def calculate_psfb_duty(
    *,
    vin_v: float,
    vout_v: float,
    diode_drop_total_v: float,
    turns_ratio_np_ns: float,
    leakage_h: float,
    iout_a: float,
    fs_hz: float,
    max_effective_duty: float,
    max_command_duty: float,
    scope: DutyScope,
) -> PSFBDutyPolicyResult:
    """Calculate and assess PSFB duty at a design or operating point.

    No duty value is clamped.  A point outside either the physical range or
    configured limits is returned with an explicit boundary status.
    """

    _require_positive("vin_v", vin_v)
    _require_positive("turns_ratio_np_ns", turns_ratio_np_ns)
    _require_positive("fs_hz", fs_hz)
    _require_nonnegative("vout_v", vout_v)
    _require_nonnegative("diode_drop_total_v", diode_drop_total_v)
    _require_nonnegative("leakage_h", leakage_h)
    _require_nonnegative("iout_a", iout_a)
    return assess_psfb_duty(
        effective_duty=turns_ratio_np_ns * (vout_v + diode_drop_total_v) / vin_v,
        duty_loss=4.0 * leakage_h * iout_a * fs_hz / (turns_ratio_np_ns * vin_v),
        max_effective_duty=max_effective_duty,
        max_command_duty=max_command_duty,
        scope=scope,
    )


def assess_psfb_duty(
    *,
    effective_duty: float,
    duty_loss: float,
    max_effective_duty: float,
    max_command_duty: float,
    scope: DutyScope,
    command_duty: float | None = None,
) -> PSFBDutyPolicyResult:
    """Assess duty values without silently changing caller-provided values."""

    _require_limit("max_effective_duty", max_effective_duty)
    _require_limit("max_command_duty", max_command_duty)
    if max_effective_duty > max_command_duty:
        raise ValueError("max_effective_duty must not exceed max_command_duty.")
    if command_duty is None:
        command_duty = effective_duty + duty_loss

    finite = all(
        math.isfinite(value)
        for value in (
            effective_duty,
            duty_loss,
            command_duty,
            max_effective_duty,
            max_command_duty,
        )
    )
    within_physical_range = finite and 0.0 <= effective_duty <= command_duty <= 1.0
    duty_loss_consistent = (
        finite
        and duty_loss >= 0.0
        and math.isclose(
            command_duty - effective_duty,
            duty_loss,
            rel_tol=1e-7,
            abs_tol=1e-10,
        )
    )
    within_configured_limits = (
        within_physical_range
        and effective_duty <= max_effective_duty + _DUTY_TOLERANCE
        and command_duty <= max_command_duty + _DUTY_TOLERANCE
    )

    reasons: list[str] = []
    if not within_physical_range:
        reasons.append("duty_order_or_physical_range_violation")
    if not duty_loss_consistent:
        reasons.append("duty_loss_mismatch")
    if within_physical_range and not within_configured_limits:
        reasons.append("configured_duty_limit_exceeded")
    status = "pass" if not reasons else _status_for(reasons)
    return PSFBDutyPolicyResult(
        scope=scope,
        effective_duty=effective_duty,
        duty_loss=duty_loss,
        command_duty=command_duty,
        max_effective_duty=max_effective_duty,
        max_command_duty=max_command_duty,
        within_physical_range=within_physical_range,
        duty_loss_consistent=duty_loss_consistent,
        within_configured_limits=within_configured_limits,
        status=status,
        failure_reason=None if not reasons else ";".join(reasons),
    )


def _status_for(reasons: list[str]) -> str:
    if "duty_order_or_physical_range_violation" in reasons:
        return "physical_boundary_failure"
    if "configured_duty_limit_exceeded" in reasons:
        return "configured_boundary_failure"
    return "invalid_duty"


def _require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and positive.")


def _require_nonnegative(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative.")


def _require_limit(name: str, value: float) -> None:
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between 0 and 1.")
