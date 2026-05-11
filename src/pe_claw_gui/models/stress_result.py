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
class StressResult:
    """Electrical stress estimates derived from a topology candidate."""

    switch: StressMetric
    rectifier: StressMetric
    notes: list[str] = field(default_factory=list)
