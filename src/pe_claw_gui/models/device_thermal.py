"""Semiconductor thermal result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReferenceJunctionTemperatureEstimate:
    """Bare-package junction-temperature estimate for one operating point."""

    tj_est_c: float
    method: str
    label: str = ""
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SinkThermalRequirement:
    """Backsolved sink requirement for a target semiconductor junction temperature."""

    target_junction_temp_c: float
    ambient_temp_c: float
    p_total_w: float
    rth_jc_k_per_w: float
    rth_cs_k_per_w: float
    required_total_rth_k_per_w: float | None
    required_sink_rth_k_per_w: float | None
    estimated_sink_volume_cm3: float | None
    sink_volume_model: str
    cooling_mode_assumed: str
    feasible: bool
    classification: str
    sink_requirement_label: str = ""
    sink_volume_estimate_label: str = ""
    sink_estimate_model_label: str = ""
    thermal_interpretation_label: str = ""
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
