"""Typed T-type engineering handoff; selection references are not system losses."""

from __future__ import annotations
from dataclasses import dataclass, field
from .inductor import FixedInductorDesignCandidate, InductorDesignRequest, InductorOperatingPointRequest, InductorOperatingEvaluation
from .capacitor import CapacitorSelectionEntry

LOSS_SCOPE_ID = "t_type_conduction_magnetics_capacitors_v1"
EXCLUDED_COMPONENTS = (
    "switching_on",
    "switching_off",
    "reverse_recovery",
    "output_capacitance",
    "gate_drive",
    "control_auxiliary",
    "fan",
    "snubber",
    "equalizer",
    "precharge",
)


@dataclass(frozen=True)
class TTypeDesignBasis:
    topology_id: str
    run_id: str | None
    candidate_fingerprint: str
    cases: tuple[tuple[float, float, float], ...]
    phase: str
    ambient_temp_c: float
    target_junction_temp_c: float
    reference_curve_temp_c: float
    rated_output_power_w: float
    vac_ll_rms_v: float
    f_line_hz: float
    fsw_hz: float
    design_inductance_h: float
    voltage_margin_ratio: float
    current_margin_ratio: float
    selection_policy: str = "legacy_envelope"


@dataclass(frozen=True)
class TTypeSelectedDevice:
    role: str
    part_number: str
    parallel_count: int
    position_ids: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class TTypeSelectedPackage:
    package_instance_id: str
    part_number: str
    member_position_ids: tuple[str, ...]
    section_bindings: tuple[str, ...]


@dataclass(frozen=True)
class TTypeRoleSelectionReference:
    role: str
    part_number: str
    parallel_count: int
    case: tuple[float, float, float]
    position_id: str
    per_device_channel_w: float
    per_device_diode_w: float
    reference_tj_c: float
    source: str


@dataclass(frozen=True)
class TTypePhaseInductor:
    instance_id: str
    design: FixedInductorDesignCandidate
    design_request: InductorDesignRequest
    operating_request: InductorOperatingPointRequest | None
    reference_evaluation: InductorOperatingEvaluation
    evaluation: InductorOperatingEvaluation | None
    reference_request: InductorOperatingPointRequest | None = None


@dataclass(frozen=True)
class TTypeMagneticResult:
    candidate_fingerprint: str
    run_id: str | None
    target_inductance_h: float
    selected_inductance_h: float | None = None
    selected_library_design_id: str | None = None
    status: str = "unavailable"
    phase_instances: tuple[TTypePhaseInductor, ...] = ()
    total_copper_loss_w: float | None = None
    total_core_loss_w: float | None = None
    total_loss_w: float | None = None
    total_volume_m3: float | None = None
    operating_basis: dict[str, float | str] = field(default_factory=dict)
    library_provenance: dict[str, object] = field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class TTypeCapacitorResult:
    candidate_fingerprint: str
    run_id: str | None
    status: str = "unavailable"
    selected_upper: CapacitorSelectionEntry | None = None
    selected_lower: CapacitorSelectionEntry | None = None
    current_upper: CapacitorSelectionEntry | None = None
    current_lower: CapacitorSelectionEntry | None = None
    equivalent_link_capacitance_f: float | None = None
    total_loss_w: float | None = None
    total_volume_cm3: float | None = None
    operating_basis: dict[str, float | str] = field(default_factory=dict)
    port_metrics: dict[str, object] = field(default_factory=dict)
    voltage_ripple: dict[str, object] = field(default_factory=dict)
    library_provenance: dict[str, object] = field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()
    ripple_model: str = "fixed_bus_ripple_estimate"


@dataclass(frozen=True)
class TTypeHardwareSnapshot:
    hardware_id: str
    run_id: str | None
    candidate_fingerprint: str
    loss_scope_id: str
    devices: tuple[TTypeSelectedDevice, ...]
    packages: tuple[TTypeSelectedPackage, ...]
    magnetic_design_id: str
    magnetic_design_fingerprint: str
    inductance_h: float
    upper_part_number: str
    lower_part_number: str
    upper_series_parallel: tuple[int, int]
    lower_series_parallel: tuple[int, int]
    upper_capacitance_f: float
    lower_capacitance_f: float
    upper_esr_ohm: float
    lower_esr_ohm: float
    ambient_temp_c: float
    reference_curve_temp_c: float
    thermal_configuration_fingerprint: str


@dataclass(frozen=True)
class TTypePositionOperatingResult:
    position_id: str
    role: str
    part_number: str
    parallel_count: int
    per_device_channel_w: float
    per_device_diode_w: float
    position_loss_w: float
    source: str


@dataclass(frozen=True)
class TTypeThermalConfiguration:
    """Engineering assumptions, shared with the NPC method, not a measured sink."""

    sink_rth_k_per_w: float = 0.12
    design_airflow_m3_h: float = 120.0
    airflow_derating: float = 0.8
    coupling_factor: float = 1.15
    contact_pressure_mpa: float = 0.35
    model: str = "forced_air_shared_extrusion_proxy_v1"


@dataclass(frozen=True)
class TTypePositionThermal:
    position_id: str
    part_number: str
    physical_device_count: int
    per_device_loss_w: float
    rth_jc_k_per_w: float
    rth_cs_k_per_w: float
    interface_model: str
    sink_temp_c: float
    case_temp_c: float
    junction_temp_c: float
    junction_margin_c: float


@dataclass(frozen=True)
class TTypeSystemResult:
    """Current scope totals; generic LossResult remains a magnetic subtotal."""

    hardware_id: str | None
    run_id: str | None
    candidate_fingerprint: str
    operating_basis: dict[str, float | str]
    loss_scope_id: str = LOSS_SCOPE_ID
    excluded_components: tuple[str, ...] = EXCLUDED_COMPONENTS
    loss_status: str = "unavailable"
    loss_components_w: dict[str, float] = field(default_factory=dict)
    role_losses_w: dict[str, float] = field(default_factory=dict)
    total_loss_w: float | None = None
    output_power_w: float | None = None
    efficiency_ratio: float | None = None
    thermal_status: str = "unavailable"
    position_thermal: tuple[TTypePositionThermal, ...] = ()
    required_sink_rth_k_per_w: float | None = None
    required_airflow_m3_h: float | None = None
    thermal_passed: bool | None = None
    geometry_status: str = "unavailable"
    component_volumes_cm3: dict[str, float] = field(default_factory=dict)
    total_component_volume_cm3: float | None = None
    geometry_sources: dict[str, str] = field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class TTypeEngineeringResult:
    design_basis: TTypeDesignBasis
    schema_version: int = 1
    loss_scope_id: str = LOSS_SCOPE_ID
    excluded_components: tuple[str, ...] = EXCLUDED_COMPONENTS
    selected_devices: tuple[TTypeSelectedDevice, ...] = ()
    packages: tuple[TTypeSelectedPackage, ...] = ()
    role_selection_reference: dict[str, TTypeRoleSelectionReference] = field(
        default_factory=dict
    )
    stage_status: dict[str, str] = field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()
    magnetics: TTypeMagneticResult | None = None
    capacitors: TTypeCapacitorResult | None = None
    hardware: TTypeHardwareSnapshot | None = None
    current_hardware_id: str | None = None
    current_basis: dict[str, float | str] = field(default_factory=dict)
    current_positions: tuple[TTypePositionOperatingResult, ...] = ()
    refresh_status: str = "not_started"
    refresh_diagnostics: tuple[str, ...] = ()
    thermal_configuration: TTypeThermalConfiguration = field(default_factory=TTypeThermalConfiguration)
    system: TTypeSystemResult | None = None
