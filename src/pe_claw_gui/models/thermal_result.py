"""Thermal-stage result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ThermalEstimate:
    """One first-pass lumped thermal estimate for a magnetic design."""

    ambient_temp_c: float = 25.0
    core_loss_w: float | None = None
    copper_loss_w: float | None = None
    total_loss_w: float | None = None
    estimated_core_temp_rise_c: float | None = None
    estimated_winding_temp_rise_c: float | None = None
    estimated_core_temp_c: float | None = None
    estimated_winding_temp_c: float | None = None
    hotspot_proxy_temp_c: float | None = None
    total_temp_rise_maniktala_c: float | None = None
    rth_core_to_ambient_k_per_w: float | None = None
    rth_winding_to_ambient_k_per_w: float | None = None
    total_surface_area_proxy_m2: float | None = None
    core_surface_area_proxy_m2: float | None = None
    winding_surface_area_proxy_m2: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ThermalComparisonEntry:
    """Thermal summary for one magnetic design in the comparison set."""

    design_id: str
    stack_count: int = 1
    assembly_type: str | None = None
    loss_basis: str = ""
    estimate: ThermalEstimate | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ThermalResult:
    """Aggregate for simplified magnetic thermal-evaluation outputs."""

    summary: str = ""
    ambient_temp_c: float = 25.0
    recommended_design_id: str | None = None
    recommended_estimate: ThermalEstimate | None = None
    chosen_design_estimates: list[ThermalComparisonEntry] = field(default_factory=list)
    best_by_stack_count: dict[int, ThermalComparisonEntry] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    llc_component_thermal: dict[str, dict[str, object]] = field(default_factory=dict)
    status: str = "not_evaluated"
    valid_loss_entry_count: int = 0
    unavailable_loss_entry_count: int = 0

    @property
    def max_temperature_c(self) -> float | None:
        if self.recommended_estimate is None:
            return None
        return self.recommended_estimate.hotspot_proxy_temp_c
