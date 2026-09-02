"""Device-stage result model."""

from __future__ import annotations

from dataclasses import dataclass, field

from .device_loss import DeviceLossResult, SwitchStress


@dataclass(frozen=True)
class SemiconductorRoleSchemeResult:
    """Comparison-ready outcome for one role under one parallel-device scheme."""

    role: str
    parallel_count: int
    registered_candidate_count: int = 0
    selected_part_number: str | None = None
    selected_voltage_rating_v: float | None = None
    vendor: str | None = None
    device_type: str | None = None
    device_structure_type: str | None = None
    package_level: str | None = None
    module_internal_topology: str | None = None
    diode_subtype: str | None = None
    module_group_id: str | None = None
    module_section_role: str | None = None
    paired_switch_part_number: str | None = None
    paired_diode_part_number: str | None = None
    diode_binding_policy: str | None = None
    bound_to_role: str | None = None
    thermal_source: str | None = None
    package: str | None = None
    per_device_stress: SwitchStress | None = None
    candidate_count: int = 0
    passed_candidate_count: int = 0
    rejected_candidate_count: int = 0
    per_device_loss_w: float | None = None
    total_loss_w: float | None = None
    topology_position_count: int = 1
    total_physical_device_count: int = 1
    target_junction_feasible: bool | None = None
    sink_volume_cm3: float | None = None
    sink_model_label: str = ""
    sink_requirement_label: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SemiconductorSchemeResult:
    """Evaluation output for one explicit semiconductor parallelization scheme."""

    scheme_id: str
    label: str
    parallel_count: int
    registered_candidate_counts: dict[str, int] = field(default_factory=dict)
    selected_devices: dict[str, str] = field(default_factory=dict)
    candidate_counts: dict[str, int] = field(default_factory=dict)
    passed_candidate_counts: dict[str, int] = field(default_factory=dict)
    rejected_candidate_counts: dict[str, int] = field(default_factory=dict)
    rejection_breakdowns: dict[str, dict[str, int]] = field(default_factory=dict)
    closest_rejected_candidates: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    selection_summaries: dict[str, str] = field(default_factory=dict)
    candidate_traces: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    per_device_selection_stresses: dict[str, SwitchStress] = field(default_factory=dict)
    per_device_design_point_losses: dict[str, DeviceLossResult] = field(default_factory=dict)
    total_scheme_loss_by_key: dict[str, float] = field(default_factory=dict)
    role_results: tuple[SemiconductorRoleSchemeResult, ...] = ()
    total_scheme_loss_w: float | None = None
    complete: bool = True
    incomplete_reason: str | None = None
    feasible: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeviceSelectionResult:
    """Aggregate for semiconductor device-selection outputs."""

    selected_device_type_filter: str = "Any"
    selected_manufacturer_filter: str = "Any"
    registered_candidate_counts: dict[str, int] = field(default_factory=dict)
    selected_devices: dict[str, str] = field(default_factory=dict)
    selected_device_vendors: dict[str, str] = field(default_factory=dict)
    selected_device_types: dict[str, str] = field(default_factory=dict)
    selected_device_structures: dict[str, str] = field(default_factory=dict)
    selected_device_package_levels: dict[str, str] = field(default_factory=dict)
    selected_device_internal_topologies: dict[str, str] = field(default_factory=dict)
    selected_device_diode_subtypes: dict[str, str] = field(default_factory=dict)
    selected_device_module_group_ids: dict[str, str] = field(default_factory=dict)
    selected_device_module_section_roles: dict[str, str] = field(default_factory=dict)
    selected_device_paired_switches: dict[str, str] = field(default_factory=dict)
    selected_device_paired_diodes: dict[str, str] = field(default_factory=dict)
    selected_device_thermal_sources: dict[str, str] = field(default_factory=dict)
    diode_binding_policies: dict[str, str] = field(default_factory=dict)
    diode_bound_to_roles: dict[str, str] = field(default_factory=dict)
    selected_device_packages: dict[str, str] = field(default_factory=dict)
    candidate_counts: dict[str, int] = field(default_factory=dict)
    passed_candidate_counts: dict[str, int] = field(default_factory=dict)
    rejected_candidate_counts: dict[str, int] = field(default_factory=dict)
    rejection_breakdowns: dict[str, dict[str, int]] = field(default_factory=dict)
    closest_rejected_candidates: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    selection_summaries: dict[str, str] = field(default_factory=dict)
    candidate_traces: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    evaluated_losses: dict[str, DeviceLossResult] = field(default_factory=dict)
    operating_point_summaries: list[str] = field(default_factory=list)
    design_point_losses: dict[str, DeviceLossResult] = field(default_factory=dict)
    design_point_summaries: list[str] = field(default_factory=list)
    design_point_description: str = ""
    current_operating_losses: dict[str, DeviceLossResult] = field(default_factory=dict)
    current_operating_summary: str | None = None
    current_operating_point_key: str | None = None
    scheme_results: tuple[SemiconductorSchemeResult, ...] = ()
    active_scheme_id: str | None = None
    active_scheme_label: str | None = None
    active_parallel_count: int = 1
    recommended_scheme_id: str | None = None
    voltage_checks: dict[str, dict[str, object]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
