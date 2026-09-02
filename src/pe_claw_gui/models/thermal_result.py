"""Thermal-stage result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NpcThermalRoleResult:
    """Thermal result for one NPC semiconductor role in one scenario."""

    role: str
    part_number: str
    physical_device_count: int
    per_device_loss_w: float
    total_loss_w: float
    rth_jc_k_per_w: float
    rth_cs_k_per_w: float
    junction_temp_c: float
    case_temp_c: float
    interface_temperature_c: float
    target_junction_temp_c: float
    tj_max_c: float
    junction_margin_c: float
    thermal_passed: bool
    interface_model_name: str = ""
    interface_layer_summary: str = ""
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class NpcThermalScenarioResult:
    """Shared-sink thermal check for one NPC operating scenario."""

    scenario_id: str
    label: str
    load_ratio: float
    power_factor: float
    vdc_v: float
    ambient_temp_c: float
    total_semiconductor_loss_w: float
    required_sink_rth_k_per_w: float | None
    selected_sink_rth_k_per_w: float | None
    heatsink_model: str
    heatsink_volume_cm3: float | None
    required_airflow_m3_h: float | None
    design_airflow_m3_h: float | None
    airflow_derating: float
    thermal_coupling_factor: float
    worst_role: str | None
    worst_junction_temp_c: float | None
    minimum_junction_margin_c: float | None
    passed: bool
    roles: tuple[NpcThermalRoleResult, ...] = ()
    notes: tuple[str, ...] = ()


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
    llc_component_estimates: dict[str, ThermalComparisonEntry] = field(default_factory=dict)
    status: str = "not_evaluated"
    valid_loss_entry_count: int = 0
    unavailable_loss_entry_count: int = 0
    npc_scenarios: tuple[NpcThermalScenarioResult, ...] = ()
    npc_worst_case: NpcThermalScenarioResult | None = None
    npc_assumptions: dict[str, object] = field(default_factory=dict)

    @property
    def max_temperature_c(self) -> float | None:
        if self.recommended_estimate is None:
            return None
        return self.recommended_estimate.hotspot_proxy_temp_c
