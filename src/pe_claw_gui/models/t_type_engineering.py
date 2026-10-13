"""Typed T-type engineering handoff; selection references are not system losses."""

from __future__ import annotations
from dataclasses import dataclass, field

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
