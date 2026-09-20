"""Stress result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StressMetric:
    """Stress summary for one device class."""

    voltage_max_v: float
    current_peak_a: float
    current_rms_a: float | None = None
    current_avg_a: float | None = None


@dataclass(frozen=True)
class VoltageStressCheck:
    """Auditable NPC voltage-stress and device-rating check for one role."""

    role: str
    static_blocking_voltage_v: float
    dynamic_overvoltage_v: float
    worst_case_blocking_voltage_v: float
    required_device_rating_v: float
    neutral_point_stress_factor: float
    static_margin_target_ratio: float
    overvoltage_source: str
    overvoltage_validation_status: str
    candidate_voltage_rating_v: float | None = None
    static_margin_ratio: float | None = None
    dynamic_margin_ratio: float | None = None
    passed: bool | None = None


@dataclass(frozen=True)
class StressResult:
    """Electrical stress estimates derived from a topology candidate."""

    switch: StressMetric
    rectifier: StressMetric
    role_voltage_checks: dict[str, VoltageStressCheck] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
