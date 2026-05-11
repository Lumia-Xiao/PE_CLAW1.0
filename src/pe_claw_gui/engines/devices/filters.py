"""Device filtering helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ...libraries.semiconductors.mitsubishi.igbt_modules import MitsubishiIGBTModule
from ...libraries.semiconductors.metadata import (
    ANY_ACTIVE_SWITCH_CATEGORY,
    ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY,
    ANY_DIODE_CATEGORY,
    INTERNAL_MODULE_DIODE_CATEGORY,
    normalize_semiconductor_category,
)
from ...libraries.semiconductors.power_device import PowerDevice
from ...libraries.semiconductors.topology_roles import get_semiconductor_role_spec
from ...models.device_loss import DeviceLossResult

VOLTAGE_MARGIN_FACTOR = 1.20
CURRENT_MARGIN_FACTOR = 1.10

_ACTIVE_SWITCH_ROLE_NAMES = {
    "main_switch",
    "sync_switch",
    "high_side_switch",
    "low_side_switch",
    "switch",
}
_DIODE_ROLE_NAMES = {
    "diode",
    "rectifier",
    "rectifier_diode",
    "freewheel_diode",
    "boost_diode",
}


def allowed_device_types_for_role(role_name: str, topology_id: str | None = None) -> set[str]:
    """Return selection-device-type labels that are electrically compatible with a role."""

    spec = get_semiconductor_role_spec(role_name, topology_id=topology_id)
    if spec is not None:
        return set(spec.allowed_electrical_types)
    normalized_role = role_name.strip().casefold()
    if normalized_role in _ACTIVE_SWITCH_ROLE_NAMES or normalized_role.endswith("_switch"):
        return {"MOSFET", "IGBT"}
    if normalized_role in _DIODE_ROLE_NAMES or normalized_role.endswith("_diode"):
        return {"Diode"}
    return {"MOSFET", "IGBT", "Diode"}


def is_structure_compatible_with_role(device: PowerDevice, role_name: str, topology_id: str | None = None) -> tuple[bool, str | None]:
    """Return first-pass structure compatibility without enforcing topology-specific module matching."""

    spec = get_semiconductor_role_spec(role_name, topology_id=topology_id)
    normalized_role = role_name.strip().casefold()
    structure = device.device_structure_type
    if (spec is not None and spec.role_kind != "rectifier_diode") or normalized_role in _ACTIVE_SWITCH_ROLE_NAMES or normalized_role.endswith("_switch"):
        if structure in {"diode_module"} or device.module_internal_topology in {"single_diode", "diode_only"}:
            return False, f"{device.part_number}: diode-only structure is not compatible with active switch role {role_name}."
        if structure in {"six_pack_module", "three_phase_module"}:
            return True, f"{device.part_number}: multi-switch module structure is accepted for {role_name}; strict topology matching is future work."
        if structure == "unknown":
            return True, f"{device.part_number}: unknown structure accepted for {role_name}; topology matching is future work."
        return True, None
    if (spec is not None and spec.role_kind in {"rectifier_diode", "freewheel_diode"}) or normalized_role in _DIODE_ROLE_NAMES or normalized_role.endswith("_diode"):
        if device.selection_device_type == "Diode" or structure in {"diode_module"}:
            return True, None
        if structure == "mosfet_sbd_module":
            return True, f"{device.part_number}: MOSFET+SBD module accepted for diode role only as a future section-level selection placeholder."
        return False, f"{device.part_number}: structure {structure} is not compatible with diode role {role_name}."
    return True, None


def matches_semiconductor_category(device: PowerDevice, category: object, role_name: str, topology_id: str | None = None) -> bool:
    """Return whether a device matches a topology-aware role category."""

    normalized = normalize_semiconductor_category(category)
    role = role_name.strip().casefold()
    spec = get_semiconductor_role_spec(role_name, topology_id=topology_id)
    if normalized in {ANY_ACTIVE_SWITCH_CATEGORY, ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY}:
        return device.selection_device_type in {"MOSFET", "IGBT"} and device.module_internal_topology not in {"single_diode", "diode_only"}
    if normalized == ANY_DIODE_CATEGORY:
        return device.selection_device_type == "Diode" and device.module_section_role != "internal_diode"
    if normalized == INTERNAL_MODULE_DIODE_CATEGORY:
        return device.selection_device_type == "Diode" and device.module_section_role == "internal_diode"

    if (spec is not None and spec.role_kind != "rectifier_diode") or role in _ACTIVE_SWITCH_ROLE_NAMES or role.endswith("_switch"):
        return _matches_active_switch_category(device, normalized)
    if (spec is not None and spec.role_kind in {"rectifier_diode", "freewheel_diode"}) or role in _DIODE_ROLE_NAMES or role.endswith("_diode"):
        return _matches_diode_category(device, normalized)
    return True


def _matches_active_switch_category(device: PowerDevice, category: str) -> bool:
    if device.selection_device_type not in {"MOSFET", "IGBT"}:
        return False
    technology = (device.static.technology or "").casefold()
    family = (device.family or "").casefold()
    part = device.part_number.casefold()
    if category in {"Discrete MOSFET", "Discrete MOSFETs"}:
        return device.selection_device_type == "MOSFET" and device.device_structure_type == "discrete_single" and device.package_level == "discrete"
    if category == "Discrete SiC MOSFET":
        return (
            device.selection_device_type == "MOSFET"
            and device.device_structure_type == "discrete_single"
            and device.package_level == "discrete"
            and ("sic" in technology or family.startswith(("sc", "g3f")) or "coolsic" in family or "sic" in part)
        )
    if category == "GaN switch":
        return device.selection_device_type == "MOSFET" and ("gan" in technology or "gan" in family or "gan" in part or "igl" in part)
    if category in {"Discrete IGBT", "Discrete IGBTs", "IGBT"}:
        return device.selection_device_type == "IGBT" and device.device_structure_type == "discrete_single" and device.package_level == "discrete"
    if category == "MOSFET module":
        return device.selection_device_type == "MOSFET" and device.package_level == "power_module"
    if category == "IGBT module":
        return device.selection_device_type == "IGBT" and device.package_level == "power_module"
    if category == "MOSFET + SBD module":
        return (
            device.selection_device_type == "MOSFET"
            and device.device_structure_type in {"mosfet_sbd_module", "half_bridge_module", "chopper_module"}
            and device.has_internal_diode_section
            and device.internal_diode_model_available
        )
    if category == "IGBT + FWD module":
        return (
            device.selection_device_type == "IGBT"
            and device.package_level == "power_module"
            and device.has_internal_diode_section
            and device.internal_diode_model_available
            and device.diode_subtype in {"frd", "fwd", "module_diode"}
        )
    if category in {"Half-bridge module section", "Two half-bridge modules"}:
        return device.device_structure_type == "half_bridge_module" and device.package_level == "power_module"
    if category == "Chopper module section":
        return device.device_structure_type == "chopper_module" and device.package_level == "power_module"
    if category == "One full-bridge module":
        return device.device_structure_type == "full_bridge_module" and device.package_level == "power_module"
    if category == "Power module section":
        return device.package_level == "power_module" and device.selection_device_type in {"MOSFET", "IGBT"}
    return True


def _matches_diode_category(device: PowerDevice, category: str) -> bool:
    if device.selection_device_type != "Diode":
        return False
    if category == "Discrete SiC SBD":
        return device.diode_subtype in {"sic_sbd", "sbd"} and device.package_level == "discrete"
    if category == "Discrete Schottky diode":
        return device.diode_subtype in {"schottky", "sbd", "sic_sbd"} and device.package_level == "discrete"
    if category == "FRD / FWD":
        return device.diode_subtype in {"frd", "fwd"}
    if category == "JBS diode":
        return device.diode_subtype == "jbs"
    if category == "Diode module":
        return device.package_level == "power_module" or device.device_structure_type == "diode_module"
    return True


@dataclass(frozen=True)
class DeviceFilterCriteria:
    """Minimum ratings required for one normalized switch stress."""

    min_vdss_V: float
    min_continuous_current_A: float
    min_pulse_current_A: float
    reference_temp_C: float
    max_junction_temp_C: float


@dataclass(frozen=True)
class DeviceSelectionTrace:
    """Auditable filter/ranking trace for one candidate device."""

    candidate_part_number: str
    candidate_device_type: str
    candidate_manufacturer: str
    candidate_package: str
    candidate_structure_type: str
    candidate_internal_topology: str
    candidate_package_level: str
    candidate_diode_subtype: str
    candidate_module_group_id: str | None
    candidate_module_section_role: str
    candidate_voltage_rating_V: float
    required_voltage_rating_V: float
    passed_voltage_filter: bool
    candidate_continuous_current_rating_A: float | None
    candidate_continuous_current_rating_label: str
    datasheet_continuous_current_rating_A: float | None
    required_continuous_current_A: float
    passed_continuous_current_filter: bool
    candidate_pulse_current_rating_A: float | None
    datasheet_pulse_current_rating_A: float | None
    required_pulse_current_A: float
    passed_pulse_current_filter: bool
    passed_current_filter: bool
    passed_thermal_filter: bool
    rejection_reasons: list[str] = field(default_factory=list)
    design_point_p_total_W: float | None = None
    design_point_tj_ref_C: float | None = None
    design_point_required_sink_rth_k_per_w: float | None = None
    design_point_bare_reference_valid: bool | None = None
    design_point_thermal_feasible: bool | None = None
    advisory_notes: list[str] = field(default_factory=list)
    ranking_score: float | None = None
    ranking_notes: list[str] = field(default_factory=list)

    @property
    def passed_all_filters(self) -> bool:
        return self.passed_voltage_filter and self.passed_current_filter and self.passed_thermal_filter


def filter_devices(devices: Sequence[PowerDevice], criteria: DeviceFilterCriteria | None = None) -> list[PowerDevice]:
    """Compatibility helper that returns candidates passing electrical filters."""

    if criteria is None:
        return list(devices)

    filtered: list[PowerDevice] = []
    for device in devices:
        trace = evaluate_electrical_filters(device, criteria)
        if trace.passed_voltage_filter and trace.passed_current_filter:
            filtered.append(device)
    return filtered


def evaluate_electrical_filters(device: PowerDevice, criteria: DeviceFilterCriteria) -> DeviceSelectionTrace:
    """Evaluate hard voltage/current filters for one candidate."""

    rejection_reasons: list[str] = []
    ratings = device.static
    datasheet_continuous_current_a = None
    datasheet_pulse_current_a = None
    if isinstance(device.payload, MitsubishiIGBTModule):
        datasheet_continuous_current_a = device.payload.static.ic_cont_A
        datasheet_pulse_current_a = device.payload.static.ic_pulse_A

    passed_voltage = ratings.vdss_max_V >= criteria.min_vdss_V
    if not passed_voltage:
        rejection_reasons.append(
            f"voltage filter failed: Vdss {ratings.vdss_max_V:.3f} V < required {criteria.min_vdss_V:.3f} V"
        )

    continuous_limit_a = ratings.id_cont_100C_A
    current_rating_label = "Id_cont_100C"
    if continuous_limit_a is None:
        continuous_limit_a = ratings.id_cont_25C_A
        current_rating_label = "Id_cont_25C fallback"
        rejection_reasons.append("current filter used Id_cont_25C fallback because Id_cont_100C is unavailable")
    passed_continuous_current = continuous_limit_a >= criteria.min_continuous_current_A
    if not passed_continuous_current:
        rejection_reasons.append(
            f"current filter failed: {current_rating_label} {continuous_limit_a:.3f} A < required {criteria.min_continuous_current_A:.3f} A"
        )

    passed_pulse_current = ratings.id_pulse_A >= criteria.min_pulse_current_A
    if not passed_pulse_current:
        rejection_reasons.append(
            f"pulse current filter failed: Id_pulse {ratings.id_pulse_A:.3f} A < required {criteria.min_pulse_current_A:.3f} A"
        )

    passed_tj_rating = ratings.tj_max_C >= criteria.max_junction_temp_C
    if not passed_tj_rating:
        rejection_reasons.append(
            f"Tj rating filter failed: Tj,max {ratings.tj_max_C:.3f} C < required {criteria.max_junction_temp_C:.3f} C"
        )

    return DeviceSelectionTrace(
        candidate_part_number=device.part_number,
        candidate_device_type=device.selection_device_type,
        candidate_manufacturer=device.manufacturer,
        candidate_package=device.static.package,
        candidate_structure_type=device.device_structure_type,
        candidate_internal_topology=device.module_internal_topology,
        candidate_package_level=device.package_level,
        candidate_diode_subtype=device.diode_subtype,
        candidate_module_group_id=device.module_group_id,
        candidate_module_section_role=device.module_section_role,
        candidate_voltage_rating_V=ratings.vdss_max_V,
        required_voltage_rating_V=criteria.min_vdss_V,
        passed_voltage_filter=passed_voltage,
        candidate_continuous_current_rating_A=continuous_limit_a,
        candidate_continuous_current_rating_label=current_rating_label,
        datasheet_continuous_current_rating_A=datasheet_continuous_current_a,
        required_continuous_current_A=criteria.min_continuous_current_A,
        passed_continuous_current_filter=passed_continuous_current,
        candidate_pulse_current_rating_A=ratings.id_pulse_A,
        datasheet_pulse_current_rating_A=datasheet_pulse_current_a,
        required_pulse_current_A=criteria.min_pulse_current_A,
        passed_pulse_current_filter=passed_pulse_current,
        passed_current_filter=passed_continuous_current and passed_pulse_current and passed_tj_rating,
        passed_thermal_filter=False,
        rejection_reasons=rejection_reasons,
    )


def apply_thermal_filter(trace: DeviceSelectionTrace, loss_result: DeviceLossResult) -> DeviceSelectionTrace:
    """Attach design-point loss metrics and evaluate hard thermal validity."""

    rejection_reasons = list(trace.rejection_reasons)
    advisory_notes = list(trace.advisory_notes)
    passed_thermal = loss_result.thermal_feasible
    if not loss_result.bare_reference_valid:
        advisory_notes.append(
            f"bare-package reference Tj_ref {loss_result.tj_est_C:.3f} C exceeds datasheet limit; "
            "external sink / cooling path is required."
        )
    if not loss_result.thermal_feasible:
        rejection_reasons.append("thermal filter failed: target-junction sink backsolve is infeasible")

    return DeviceSelectionTrace(
        candidate_part_number=trace.candidate_part_number,
        candidate_device_type=trace.candidate_device_type,
        candidate_manufacturer=trace.candidate_manufacturer,
        candidate_package=trace.candidate_package,
        candidate_structure_type=trace.candidate_structure_type,
        candidate_internal_topology=trace.candidate_internal_topology,
        candidate_package_level=trace.candidate_package_level,
        candidate_diode_subtype=trace.candidate_diode_subtype,
        candidate_module_group_id=trace.candidate_module_group_id,
        candidate_module_section_role=trace.candidate_module_section_role,
        candidate_voltage_rating_V=trace.candidate_voltage_rating_V,
        required_voltage_rating_V=trace.required_voltage_rating_V,
        passed_voltage_filter=trace.passed_voltage_filter,
        candidate_continuous_current_rating_A=trace.candidate_continuous_current_rating_A,
        candidate_continuous_current_rating_label=trace.candidate_continuous_current_rating_label,
        datasheet_continuous_current_rating_A=trace.datasheet_continuous_current_rating_A,
        required_continuous_current_A=trace.required_continuous_current_A,
        passed_continuous_current_filter=trace.passed_continuous_current_filter,
        candidate_pulse_current_rating_A=trace.candidate_pulse_current_rating_A,
        datasheet_pulse_current_rating_A=trace.datasheet_pulse_current_rating_A,
        required_pulse_current_A=trace.required_pulse_current_A,
        passed_pulse_current_filter=trace.passed_pulse_current_filter,
        passed_current_filter=trace.passed_current_filter,
        passed_thermal_filter=passed_thermal,
        rejection_reasons=rejection_reasons,
        design_point_p_total_W=loss_result.p_total_W,
        design_point_tj_ref_C=loss_result.tj_est_C,
        design_point_required_sink_rth_k_per_w=loss_result.required_sink_rth_k_per_w,
        design_point_bare_reference_valid=loss_result.bare_reference_valid,
        design_point_thermal_feasible=loss_result.thermal_feasible,
        advisory_notes=advisory_notes,
        ranking_score=trace.ranking_score,
        ranking_notes=list(trace.ranking_notes),
    )


def apply_ranking_trace(trace: DeviceSelectionTrace, *, ranking_score: float, ranking_notes: list[str]) -> DeviceSelectionTrace:
    """Attach ranking score details to a passing trace."""

    return DeviceSelectionTrace(
        candidate_part_number=trace.candidate_part_number,
        candidate_device_type=trace.candidate_device_type,
        candidate_manufacturer=trace.candidate_manufacturer,
        candidate_package=trace.candidate_package,
        candidate_structure_type=trace.candidate_structure_type,
        candidate_internal_topology=trace.candidate_internal_topology,
        candidate_package_level=trace.candidate_package_level,
        candidate_diode_subtype=trace.candidate_diode_subtype,
        candidate_module_group_id=trace.candidate_module_group_id,
        candidate_module_section_role=trace.candidate_module_section_role,
        candidate_voltage_rating_V=trace.candidate_voltage_rating_V,
        required_voltage_rating_V=trace.required_voltage_rating_V,
        passed_voltage_filter=trace.passed_voltage_filter,
        candidate_continuous_current_rating_A=trace.candidate_continuous_current_rating_A,
        candidate_continuous_current_rating_label=trace.candidate_continuous_current_rating_label,
        datasheet_continuous_current_rating_A=trace.datasheet_continuous_current_rating_A,
        required_continuous_current_A=trace.required_continuous_current_A,
        passed_continuous_current_filter=trace.passed_continuous_current_filter,
        candidate_pulse_current_rating_A=trace.candidate_pulse_current_rating_A,
        datasheet_pulse_current_rating_A=trace.datasheet_pulse_current_rating_A,
        required_pulse_current_A=trace.required_pulse_current_A,
        passed_pulse_current_filter=trace.passed_pulse_current_filter,
        passed_current_filter=trace.passed_current_filter,
        passed_thermal_filter=trace.passed_thermal_filter,
        rejection_reasons=list(trace.rejection_reasons),
        design_point_p_total_W=trace.design_point_p_total_W,
        design_point_tj_ref_C=trace.design_point_tj_ref_C,
        design_point_required_sink_rth_k_per_w=trace.design_point_required_sink_rth_k_per_w,
        design_point_bare_reference_valid=trace.design_point_bare_reference_valid,
        design_point_thermal_feasible=trace.design_point_thermal_feasible,
        advisory_notes=list(trace.advisory_notes),
        ranking_score=ranking_score,
        ranking_notes=ranking_notes,
    )
