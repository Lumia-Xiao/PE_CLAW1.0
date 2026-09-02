"""Normalized semiconductor device stress and loss models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SwitchStress:
    """Normalized switch stress for one role, operating point, and mode."""

    role: str
    mode: str
    v_block_V: float
    i_rms_A: float
    i_avg_A: float
    i_turn_on_A: float
    i_turn_off_A: float
    fsw_Hz: float
    duty: float
    conduction_time_s: float
    dead_time_s: float = 0.0
    body_diode_conduction_time_s: float = 0.0
    rg_on_Ohm: float = 10.0
    rg_off_Ohm: float = 10.0
    v_drive_on_V: float = 10.0
    v_drive_off_V: float = 0.0
    case_temp_C: float | None = None
    ambient_temp_C: float | None = None
    target_junction_temp_C: float | None = None
    interface_rth_cs_K_per_W: float | None = None
    voltage_margin_ratio: float = 0.20
    static_voltage_basis_V: float | None = None
    neutral_point_stress_factor: float | None = None
    dynamic_overvoltage_V: float = 0.0
    overvoltage_source: str = "not_applicable"
    overvoltage_validation_status: str = "not_applicable"


@dataclass(frozen=True)
class DeviceLossResult:
    """Loss breakdown for one selected power device in one operating case."""

    part_number: str
    role: str
    mode: str
    p_cond_W: float
    p_sw_on_W: float
    p_sw_off_W: float
    p_rr_W: float
    p_eoss_W: float
    p_gate_W: float
    p_total_W: float
    tj_est_C: float
    tj_est_method: str = "ambient_only"
    reference_thermal_warnings: list[str] = field(default_factory=list)
    bare_reference_valid: bool = True
    target_junction_temp_c: float | None = None
    required_total_rth_k_per_w: float | None = None
    required_sink_rth_k_per_w: float | None = None
    estimated_sink_volume_cm3: float | None = None
    sink_volume_model: str = ""
    cooling_mode_assumed: str = "natural"
    thermal_feasible: bool = False
    thermal_design_notes: list[str] = field(default_factory=list)
    thermal_source: str = ""
    reference_temperature_label: str = ""
    sink_requirement_label: str = ""
    sink_volume_estimate_label: str = ""
    sink_estimate_model_label: str = ""
    thermal_interpretation_label: str = ""
    interface_model_name: str = ""
    interface_contact_area_mm2: float | None = None
    interface_rth_cs_k_per_w: float | None = None
    interface_layer_summary: str = ""
    interface_electrical_insulation: bool | None = None
    interface_source: str = ""
    interface_notes: list[str] = field(default_factory=list)
    interface_warnings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    method: str = "accurate"
    p_reverse_conduction_W: float = 0.0
    p_deadtime_W: float = 0.0
