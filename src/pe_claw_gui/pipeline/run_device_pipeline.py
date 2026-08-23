"""Device-stage runtime orchestration."""

from __future__ import annotations

from dataclasses import replace
import math
from typing import NamedTuple

from ..engines.devices.loss_evaluator import evaluate_switch_loss
from ..engines.devices.inverter_segmented_loss import evaluate_inverter_segmented_switch_loss
from ..engines.devices.selector import merge_switch_stresses, select_switch_device_with_audit
from ..engines.devices.filters import allowed_device_types_for_role, is_structure_compatible_with_role, matches_semiconductor_category
from ..engines.devices.stress_adapter import (
    build_current_operating_switch_stress_case,
    build_design_point_switch_stress_cases,
)
from ..engines.devices.thermal_backsolve import (
    DEFAULT_COOLING_MODE,
    estimate_sink_volume,
    estimate_reference_junction_temperature,
    required_sink_thermal_resistance,
    summarize_semiconductor_thermal_design,
)
from ..engines.devices.thermal_interface import resolve_thermal_interface_stack
from ..libraries.semiconductors.metadata import (
    DIODE_BINDING_POLICY_INPUT_KEY,
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY,
    SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY,
    SYNC_SWITCH_CATEGORY_INPUT_KEY,
    INTERNAL_MODULE_DIODE_CATEGORY,
    SemiconductorLibraryFilter,
    normalize_semiconductor_manufacturer,
)
from ..libraries.semiconductors.registry import build_default_semiconductor_registry
from ..libraries.semiconductors.topology_roles import get_semiconductor_role_spec, get_semiconductor_roles_for_topology
from ..models.design_report import DesignReport
from ..models.device_loss import DeviceLossResult, SwitchStress
from ..models.device_result import (
    DeviceSelectionResult,
    SemiconductorRoleSchemeResult,
    SemiconductorSchemeResult,
)
from ..topologies.base import TopologyPlugin
try:
    from ..topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import (
        assess_llc_fha_input_impedance,
    )
except ModuleNotFoundError:  # New LLC topology package is outside the 1.0 GUI scope.
    assess_llc_fha_input_impedance = None

try:
    from ..topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated.primary_current_model import (
        calculate_primary_current as _calculate_psfb_primary_current,
    )
except ModuleNotFoundError:  # New PSFB topology package is outside the 1.0 GUI scope.
    _calculate_psfb_primary_current = None
from ..models.stress_result import StressMetric, StressResult

_SCHEME_VARIANTS: tuple[tuple[str, str, int], ...] = (
    ("single", "Single Device", 1),
    ("parallel_2", "2 Devices in Parallel", 2),
    ("parallel_3", "3 Devices in Parallel", 3),
)
_LLC_DIODE_RECTIFIER_TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"
_LLC_SR_TOPOLOGY_ID = "llc_resonant_converter_synchronous_rectifier"
_PSFB_DIODE_RECTIFIER_TOPOLOGY_ID = "phase_shifted_full_bridge_diode_rectifier_isolated"
_SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
_SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID = "single_phase_totem_pole_bridgeless_pfc"
_SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY = "secondary_sync_switch_manufacturer"
_INDEPENDENT_SECONDARY_DIODE_TOPOLOGY_IDS = {
    _LLC_DIODE_RECTIFIER_TOPOLOGY_ID,
    "flyback_diode_rectified_isolated",
    _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID,
    _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID,
}


def _device_context_metadata(report: DesignReport) -> dict[str, object]:
    """Merge specification, synthesized-candidate, and operating-waveform metadata."""

    metadata = dict(report.spec.metadata)
    if report.candidate is not None:
        metadata.update(report.candidate.metadata)
    if report.waveform is not None and isinstance(report.waveform.metadata, dict):
        metadata.update(report.waveform.metadata)
    return metadata


def _is_llc_primary_switch_loss(role: str, topology_id: str | None, device) -> bool:
    return (
        topology_id == _LLC_DIODE_RECTIFIER_TOPOLOGY_ID
        and role.strip().casefold() == "main_switch"
        and getattr(device, "selection_device_type", None) == "MOSFET"
    )


def _llc_nominal_full_load_point(llc_fha: dict[str, object]) -> dict[str, object]:
    for result in llc_fha.get("coverage_results", []):
        if isinstance(result, dict) and result.get("label") == "Vin_nom, Vout_nom, Pout_max":
            return result
    nominal = llc_fha.get("current_estimates_nominal_full_load")
    return nominal if isinstance(nominal, dict) else {}


def _llc_zvs_assessment_from_metadata(
    metadata: dict[str, object],
    *,
    fs_hz: float,
) -> dict[str, object] | None:
    llc_fha = metadata.get("llc_fha")
    if not isinstance(llc_fha, dict):
        return None
    waveform = metadata.get("llc_fha_waveforms")
    operating = waveform if isinstance(waveform, dict) else _llc_nominal_full_load_point(llc_fha)
    try:
        assessment = assess_llc_fha_input_impedance(
            fs_hz=float(fs_hz),
            lr_h=float(llc_fha["lr_h"]),
            cr_f=float(llc_fha["cr_f"]),
            lm_h=float(llc_fha["lm_h"]),
            turns_ratio=float(llc_fha["turns_ratio"]),
            vout_v=float(operating.get("vout_op_v", operating.get("vout_v", llc_fha["vout_nom_v"]))),
            pout_w=float(operating.get("pout_op_w", operating.get("pout_w", llc_fha["pout_max_w"]))),
        )
    except (KeyError, TypeError, ValueError):
        return None
    return {
        "zin_real_ohm": assessment.zin_ohm.real,
        "zin_imag_ohm": assessment.zin_ohm.imag,
        "angle_rad": assessment.angle_rad,
        "angle_deg": assessment.angle_deg,
        "tank_characteristic": assessment.tank_characteristic,
        "zvs_assumed": assessment.zvs_assumed,
    }


def _apply_llc_primary_zvs_correction(
    loss_result: DeviceLossResult,
    device,
    stress: SwitchStress,
    metadata: dict[str, object],
) -> DeviceLossResult:
    assessment = _llc_zvs_assessment_from_metadata(metadata, fs_hz=stress.fsw_Hz)
    if assessment is None:
        return loss_result
    zvs_assumed = bool(assessment["zvs_assumed"])
    treatment = "suppressed to zero" if zvs_assumed else "retained"
    notes = [
        *loss_result.thermal_design_notes,
        (
            "LLC ZVS assessment: "
            f"zin_real_ohm={float(assessment['zin_real_ohm']):.6g}, "
            f"zin_imag_ohm={float(assessment['zin_imag_ohm']):.6g}, "
            f"impedance_angle_deg={float(assessment['angle_deg']):.6g}, "
            f"tank_characteristic={assessment['tank_characteristic']}, "
            f"zvs_assumed={'yes' if zvs_assumed else 'no'}, "
            f"turn_on_loss_treatment={treatment}, turn_off_loss_treatment=retained."
        ),
    ]
    if not zvs_assumed:
        return replace(loss_result, thermal_design_notes=_append_unique_list(notes))
    corrected_total_w = max(loss_result.p_total_W - loss_result.p_sw_on_W, 0.0)
    # Rebuild the thermal fields from the corrected total loss.  This keeps
    # candidate hard-filtering, ranking, and sink backsolve consistent with
    # the reported LLC ZVS loss treatment.
    ambient_temp_c = stress.ambient_temp_C if stress.ambient_temp_C is not None else 25.0
    target_junction_temp_c = (
        stress.target_junction_temp_C
        if stress.target_junction_temp_C is not None
        else device.static.tj_max_C
    )
    interface_stack = resolve_thermal_interface_stack(device, stress)
    thermal_reference = estimate_reference_junction_temperature(
        p_total_w=corrected_total_w,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_ja_k_per_w=device.static.rth_ja_K_per_W,
        ambient_temp_c=ambient_temp_c,
        case_temp_c=stress.case_temp_C,
    )
    sink_requirement = required_sink_thermal_resistance(
        p_total_w=corrected_total_w,
        ambient_temp_c=ambient_temp_c,
        target_junction_temp_c=target_junction_temp_c,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_cs_k_per_w=interface_stack.total_rth_k_per_w,
        cooling_mode=DEFAULT_COOLING_MODE,
    )
    warnings = list(thermal_reference.warnings)
    warnings.extend(warning for warning in sink_requirement.warnings if warning not in warnings)
    warnings.extend(warning for warning in interface_stack.warnings if warning not in warnings)
    thermal_notes = summarize_semiconductor_thermal_design(
        reference_estimate=thermal_reference,
        sink_requirement=sink_requirement,
        datasheet_tj_max_c=device.static.tj_max_C,
    )
    thermal_notes.extend(_interface_note_lines(interface_stack))
    return replace(
        loss_result,
        p_sw_on_W=0.0,
        p_total_W=corrected_total_w,
        tj_est_C=thermal_reference.tj_est_c,
        tj_est_method=thermal_reference.method,
        reference_thermal_warnings=list(thermal_reference.warnings),
        bare_reference_valid=thermal_reference.tj_est_c <= device.static.tj_max_C,
        target_junction_temp_c=target_junction_temp_c,
        required_total_rth_k_per_w=sink_requirement.required_total_rth_k_per_w,
        required_sink_rth_k_per_w=sink_requirement.required_sink_rth_k_per_w,
        estimated_sink_volume_cm3=sink_requirement.estimated_sink_volume_cm3,
        sink_volume_model=sink_requirement.sink_volume_model,
        cooling_mode_assumed=sink_requirement.cooling_mode_assumed,
        thermal_feasible=sink_requirement.feasible,
        thermal_design_notes=_append_unique_list([*thermal_notes, *notes]),
        thermal_source=thermal_reference.method,
        reference_temperature_label=thermal_reference.label,
        sink_requirement_label=sink_requirement.sink_requirement_label,
        sink_volume_estimate_label=sink_requirement.sink_volume_estimate_label,
        sink_estimate_model_label=sink_requirement.sink_estimate_model_label,
        thermal_interpretation_label=sink_requirement.thermal_interpretation_label,
        interface_model_name=interface_stack.model_name,
        interface_contact_area_mm2=interface_stack.contact_area_mm2,
        interface_rth_cs_k_per_w=interface_stack.total_rth_k_per_w,
        interface_layer_summary=interface_stack.layer_summary,
        interface_electrical_insulation=interface_stack.electrical_insulation,
        interface_source=interface_stack.source,
        interface_notes=list(interface_stack.notes),
        interface_warnings=list(interface_stack.warnings),
        warnings=_append_unique_list(warnings),
    )


def _evaluate_switch_loss_for_context(
    device,
    stress: SwitchStress,
    *,
    report: DesignReport,
    method: str = "accurate",
) -> DeviceLossResult:
    loss_result = evaluate_switch_loss(device, stress, method=method)
    if _is_llc_primary_switch_loss(stress.role, report.spec.topology_id, device):
        return _apply_llc_primary_zvs_correction(
            loss_result,
            device,
            stress,
            _device_context_metadata(report),
        )
    return loss_result


class _SchemeSelectionContext(NamedTuple):
    role: str
    case_id: str
    per_device_loss: DeviceLossResult
    total_loss_w: float
    topology_position_count: int
    total_physical_device_count: int
    sink_volume_cm3: float | None
    sink_model_label: str
    sink_requirement_label: str
    thermal_feasible: bool


def _is_switch_role(role: str) -> bool:
    spec = get_semiconductor_role_spec(role)
    if spec is not None:
        return spec.role_kind != "rectifier_diode"
    return role.endswith("switch")


def _is_rectifier_diode_role(role: str) -> bool:
    spec = get_semiconductor_role_spec(role)
    if spec is not None:
        return spec.role_kind == "rectifier_diode"
    return role.strip().casefold() in {"rectifier_diode", "diode", "rectifier"} or role.strip().casefold().endswith("_diode")


def _is_selectable_semiconductor_role(role: str) -> bool:
    return bool(allowed_device_types_for_role(role))


def _category_for_role(role: str, topology_id: str | None, metadata: dict[str, object]) -> object | None:
    normalized_role = role.strip().casefold()
    spec = get_semiconductor_role_spec(role, topology_id=topology_id)
    if normalized_role == "main_switch":
        if topology_id == "four_switch_buck_boost_simplified_four_mode":
            return metadata.get(SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY)
        return metadata.get(MAIN_SWITCH_CATEGORY_INPUT_KEY)
    if topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID and normalized_role in {
        "totem_pole_hf_switch",
        "totem_pole_lf_switch",
    }:
        return metadata.get(MAIN_SWITCH_CATEGORY_INPUT_KEY)
    if normalized_role == "sync_switch":
        return metadata.get(SYNC_SWITCH_CATEGORY_INPUT_KEY)
    if normalized_role == "secondary_sync_switch":
        return metadata.get(SYNC_SWITCH_CATEGORY_INPUT_KEY)
    if topology_id == "three_phase_three_level_npc_inverter" and normalized_role in {
        "npc_outer_switch",
        "npc_inner_switch",
    }:
        return metadata.get(MAIN_SWITCH_CATEGORY_INPUT_KEY)
    if topology_id == "three_phase_three_level_npc_inverter" and normalized_role == "npc_clamp_diode":
        return metadata.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY)
    if _is_rectifier_diode_role(role):
        return metadata.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY)
    if normalized_role.endswith("_switch") and topology_id == "four_switch_buck_boost_simplified_four_mode":
        return metadata.get(SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY)
    if spec is not None and spec.role_kind == "three_level_switch":
        return metadata.get(MAIN_SWITCH_CATEGORY_INPUT_KEY)
    return None


def _requires_internal_diode_binding(device) -> bool:
    return (
        getattr(device, "package_level", None) == "power_module"
        and getattr(device, "has_internal_diode_section", False)
        and getattr(device, "internal_diode_model_available", False)
        and getattr(device, "module_group_id", None) is not None
    )


def _declares_internal_diode_binding(device) -> bool:
    return (
        getattr(device, "package_level", None) == "power_module"
        and getattr(device, "has_internal_diode_section", False)
        and getattr(device, "module_group_id", None) is not None
    )


def _topology_requires_rectifier_diode(topology_id: str | None) -> bool:
    return "rectifier_diode" in set(get_semiconductor_roles_for_topology(topology_id or ""))


def _filter_unavailable_module_bound_switches(candidates, role: str, topology_id: str | None) -> tuple[list, list[str]]:
    if topology_id in _INDEPENDENT_SECONDARY_DIODE_TOPOLOGY_IDS:
        return list(candidates), []
    if not _is_switch_role(role) or not _topology_requires_rectifier_diode(topology_id):
        return list(candidates), []
    kept = []
    rejection_notes: list[str] = []
    for device in candidates:
        if _declares_internal_diode_binding(device) and not getattr(device, "internal_diode_model_available", False):
            rejection_notes.append(
                f"{device.part_number}: module-bound diode required but internal diode model is unavailable"
            )
            continue
        kept.append(device)
    return kept, rejection_notes


def _bound_internal_diode_candidates(candidates, switch_device) -> list:
    module_group_id = getattr(switch_device, "module_group_id", None)
    if module_group_id is None:
        return []
    return [
        device for device in candidates
        if device.selection_device_type == "Diode"
        and device.module_section_role == "internal_diode"
        and device.module_group_id == module_group_id
    ]


def _filter_candidates_for_role(candidates, role: str, topology_id: str | None, category: object | None = None) -> tuple[list, int, set[str]]:
    allowed_types = allowed_device_types_for_role(role, topology_id=topology_id)
    compatible = [device for device in candidates if device.selection_device_type in allowed_types]
    if category is not None:
        compatible = [device for device in compatible if matches_semiconductor_category(device, category, role, topology_id)]
    return compatible, len(candidates) - len(compatible), allowed_types


def _role_manufacturer_for_topology(role: str, topology_id: str | None, metadata: dict[str, object]) -> str:
    if topology_id not in {_LLC_DIODE_RECTIFIER_TOPOLOGY_ID, _LLC_SR_TOPOLOGY_ID, _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID}:
        return "Any"
    normalized_role = role.strip().casefold()
    if normalized_role == "main_switch":
        return normalize_semiconductor_manufacturer(metadata.get(PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY))
    if topology_id == _LLC_SR_TOPOLOGY_ID and normalized_role == "secondary_sync_switch":
        return normalize_semiconductor_manufacturer(metadata.get(_SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY))
    if _is_rectifier_diode_role(role):
        return normalize_semiconductor_manufacturer(metadata.get(RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY))
    return "Any"


def _filter_candidates_by_manufacturer(candidates, manufacturer: str) -> tuple[list, int]:
    if manufacturer == "Any":
        return list(candidates), 0
    filtered = [device for device in candidates if device.vendor == manufacturer]
    return filtered, len(candidates) - len(filtered)


def _topology_position_count_for_role(role: str, topology_id: str | None, metadata: dict[str, object]) -> int:
    if topology_id == "single_phase_full_bridge_inverter" and role.strip().casefold() == "main_switch":
        return 4
    if topology_id == "three_phase_two_level_voltage_source_inverter" and role.strip().casefold() == "main_switch":
        return 6
    if topology_id == "three_phase_three_level_npc_inverter" and role.strip().casefold() in {
        "npc_outer_switch",
        "npc_inner_switch",
        "npc_clamp_diode",
    }:
        return 6
    if topology_id == _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID and role.strip().casefold() in {
        "main_switch",
        "rectifier_diode",
    }:
        return 4
    if topology_id == _LLC_SR_TOPOLOGY_ID and role.strip().casefold() in {
        "main_switch",
        "secondary_sync_switch",
    }:
        return 4
    if topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID and role.strip().casefold() in {
        "totem_pole_hf_switch",
        "totem_pole_lf_switch",
    }:
        return 2
    if topology_id != _LLC_DIODE_RECTIFIER_TOPOLOGY_ID:
        return 1
    normalized_role = role.strip().casefold()
    if normalized_role == "main_switch":
        primary_bridge_type = str(metadata.get("primary_bridge_type", "full_bridge"))
        return 2 if primary_bridge_type == "half_bridge" else 4
    if _is_rectifier_diode_role(role):
        secondary_rectifier_type = str(metadata.get("secondary_rectifier_type", "full_bridge_rectifier"))
        return 2 if secondary_rectifier_type == "full_wave_center_tapped_rectifier" else 4
    return 1


def _scheme_label_for_topology(label: str, topology_id: str | None) -> str:
    if topology_id not in {_LLC_DIODE_RECTIFIER_TOPOLOGY_ID, _LLC_SR_TOPOLOGY_ID, _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID}:
        return label
    if label == "Single Device":
        return "Single Device per Position"
    return f"{label} per Position"


def _format_allowed_device_types(allowed_types: set[str]) -> str:
    ordered = [item for item in ("MOSFET", "IGBT", "Diode") if item in allowed_types]
    if not ordered:
        return "no device types"
    if len(ordered) == 1:
        return ordered[0]
    return " or ".join([", ".join(ordered[:-1]), ordered[-1]])


def run_device_pipeline(report: DesignReport, plugin: TopologyPlugin | None = None) -> DesignReport:
    """Attach the semiconductor design-point selection stage to a design report."""

    if report.candidate is None or report.stress is None:
        device_result = DeviceSelectionResult(
            notes=["Device stage skipped because the report has no candidate or stress result."],
        )
        return replace(report, device=device_result)

    registry = build_default_semiconductor_registry()
    design_cases = build_design_point_switch_stress_cases(report, plugin=plugin)
    if not design_cases:
        device_result = DeviceSelectionResult(
            notes=["Device stage could not derive any normalized design-point switch-stress cases."],
        )
        return replace(report, device=device_result)

    library_filter = SemiconductorLibraryFilter.from_raw(
        device_type=report.spec.metadata.get("semiconductor_device_type"),
        manufacturer=report.spec.metadata.get("semiconductor_manufacturer"),
    )
    registered_switch_candidates = registry.list_devices()
    switch_candidates = registry.search(
        vendor=library_filter.manufacturer,
        device_type=library_filter.device_type,
    )
    scheme_variants = _resolve_scheme_variants(library_filter)
    notes = [
        "Semiconductor selection and sink sizing are anchored to the 100% load design point.",
        f"Semiconductor library filter: {library_filter.describe()}.",
        f"Registered semiconductor candidates: {len(registered_switch_candidates)} total; {len(switch_candidates)} remain after the library prefilter.",
    ]
    if report.spec.topology_id == "llc_resonant_converter_diode_rectifier":
        primary_manufacturer = normalize_semiconductor_manufacturer(
            report.spec.metadata.get(PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY)
        )
        rectifier_manufacturer = normalize_semiconductor_manufacturer(
            report.spec.metadata.get(RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY)
        )
        notes.extend([
            (
                "Diode LLC role filters: "
                f"primary switch category={report.spec.metadata.get(MAIN_SWITCH_CATEGORY_INPUT_KEY, 'Any active switch')}, "
                f"manufacturer={primary_manufacturer}; "
                f"rectifier diode category={report.spec.metadata.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY, 'Any diode')}, "
                f"manufacturer={rectifier_manufacturer}."
            ),
            "Diode LLC device stress source is the worst-case FHA coverage-corner current stress.",
            "LLC primary MOSFET turn-on loss uses first-pass FHA inductive-ZVS suppression; turn-off loss remains modeled.",
        ])
    if report.spec.topology_id == _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        notes.extend([
            "Boost PFC role filters: main_switch selects the boost switch; rectifier_diode selects an independent boost diode.",
            "Input bridge rectifier hardware is selected by the AC-DC bridge-rectifier pipeline, not by the generic semiconductor role map.",
        ])
    if report.spec.topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID:
        notes.extend([
            "Totem-Pole PFC role filters: totem_pole_hf_switch selects the high-frequency active switch pair; totem_pole_lf_switch selects the line-frequency synchronous switch pair.",
            "No bridge rectifier, rectifier_diode, or boost diode role is selected for the bridgeless Totem-Pole PFC power path.",
        ])
    if report.spec.topology_id == "single_phase_full_bridge_inverter":
        notes.extend([
            "Single-phase full-bridge inverter selection uses one main_switch device repeated across four bridge positions.",
            "Design-point inverter switch loss is a first-pass per-position approximation; line-cycle segmented loss reports ZVS direction diagnostics but does not use them to reduce turn-on loss.",
        ])
    if len(scheme_variants) > 1:
        notes.append("Parallel-scheme comparison assumes ideal equal current sharing across paralleled devices.")
    else:
        notes.append("Parallel-scheme comparison was limited to the single-device scheme for the current semiconductor filter.")
    if not switch_candidates:
        notes.append(f"No semiconductor candidates match {library_filter.describe()}.")

    stresses_by_role: dict[str, list] = {}
    for case in design_cases:
        for stress in case.stresses:
            stresses_by_role.setdefault(stress.role, []).append(stress)

    scheme_results = tuple(
        _evaluate_parallel_scheme(
            registry=registry,
            switch_candidates=switch_candidates,
            registered_switch_candidates=registered_switch_candidates,
            design_cases=design_cases,
            stresses_by_role=stresses_by_role,
            scheme_id=scheme_id,
            label=_scheme_label_for_topology(label, report.spec.topology_id),
            parallel_count=parallel_count,
            library_filter=library_filter,
            topology_id=report.spec.topology_id,
            spec_metadata=report.spec.metadata,
            report=report,
        )
        for scheme_id, label, parallel_count in scheme_variants
    )
    notes.extend(_build_scheme_comparison_notes(scheme_results))

    active_scheme = _select_active_semiconductor_scheme(
        scheme_results,
        topology_id=report.spec.topology_id,
    )
    has_complete_active_scheme = bool(active_scheme.complete)
    (
        selected_device_vendors,
        selected_device_types,
        selected_device_structures,
        selected_device_package_levels,
        selected_device_internal_topologies,
        selected_device_diode_subtypes,
        selected_device_module_group_ids,
        selected_device_module_section_roles,
        selected_device_paired_switches,
        selected_device_paired_diodes,
        selected_device_thermal_sources,
        diode_binding_policies,
        diode_bound_to_roles,
        selected_device_packages,
    ) = _build_selected_device_metadata(active_scheme)

    active_scheme_id = active_scheme.scheme_id if has_complete_active_scheme else None
    active_scheme_label = active_scheme.label if has_complete_active_scheme else None
    active_parallel_count = active_scheme.parallel_count if has_complete_active_scheme else 1
    recommended_scheme_id = active_scheme.scheme_id if has_complete_active_scheme else None
    active_scheme_notes = [
        (
            "Active semiconductor scheme: "
            f"{active_scheme.label} ({active_scheme.scheme_id}, {active_scheme.parallel_count}x)."
        )
    ] if has_complete_active_scheme else ["No complete semiconductor scheme result is available."]

    device_result = DeviceSelectionResult(
        selected_device_type_filter=library_filter.device_type,
        selected_manufacturer_filter=library_filter.manufacturer,
        registered_candidate_counts=active_scheme.registered_candidate_counts,
        selected_devices=active_scheme.selected_devices,
        selected_device_vendors=selected_device_vendors,
        selected_device_types=selected_device_types,
        selected_device_structures=selected_device_structures,
        selected_device_package_levels=selected_device_package_levels,
        selected_device_internal_topologies=selected_device_internal_topologies,
        selected_device_diode_subtypes=selected_device_diode_subtypes,
        selected_device_module_group_ids=selected_device_module_group_ids,
        selected_device_module_section_roles=selected_device_module_section_roles,
        selected_device_paired_switches=selected_device_paired_switches,
        selected_device_paired_diodes=selected_device_paired_diodes,
        selected_device_thermal_sources=selected_device_thermal_sources,
        diode_binding_policies=diode_binding_policies,
        diode_bound_to_roles=diode_bound_to_roles,
        selected_device_packages=selected_device_packages,
        candidate_counts=active_scheme.candidate_counts,
        passed_candidate_counts=active_scheme.passed_candidate_counts,
        rejected_candidate_counts=active_scheme.rejected_candidate_counts,
        rejection_breakdowns=active_scheme.rejection_breakdowns,
        closest_rejected_candidates=active_scheme.closest_rejected_candidates,
        selection_summaries=active_scheme.selection_summaries,
        candidate_traces=active_scheme.candidate_traces,
        evaluated_losses=active_scheme.per_device_design_point_losses,
        operating_point_summaries=[case.notes[0] if case.notes else case.label for case in design_cases],
        design_point_losses=active_scheme.per_device_design_point_losses,
        design_point_summaries=[case.notes[0] if case.notes else case.label for case in design_cases],
        design_point_description="100% load nominal semiconductor design point.",
        current_operating_losses={},
        current_operating_summary=None,
        current_operating_point_key=None,
        scheme_results=scheme_results,
        active_scheme_id=active_scheme_id,
        active_scheme_label=active_scheme_label,
        active_parallel_count=active_parallel_count,
        recommended_scheme_id=recommended_scheme_id,
        notes=[
            *notes,
            *active_scheme_notes,
        ],
    )
    report_with_device = replace(report, device=device_result)
    report_with_device = _apply_psfb_selected_device_evidence(
        report_with_device,
        active_scheme=active_scheme,
        registry=registry,
    )
    return _apply_llc_sr_selected_device_readback(
        report_with_device,
        active_scheme=active_scheme,
        registry=registry,
    )


def _apply_llc_sr_selected_device_readback(
    report: DesignReport,
    *,
    active_scheme: SemiconductorSchemeResult,
    registry,
) -> DesignReport:
    """Refresh LLC SR first-pass readback from selected semiconductor devices."""

    if report.spec.topology_id != _LLC_SR_TOPOLOGY_ID:
        return report
    if report.candidate is None or report.device is None:
        return report
    llc_sr = report.candidate.metadata.get("llc_sr") if isinstance(report.candidate.metadata, dict) else None
    llc_fha = report.candidate.metadata.get("llc_fha") if isinstance(report.candidate.metadata, dict) else None
    if not isinstance(llc_sr, dict) or not isinstance(llc_fha, dict):
        return report
    secondary_part = report.device.selected_devices.get("secondary_sync_switch")
    if not secondary_part:
        return report
    try:
        secondary_device = registry.get_device(secondary_part)
    except KeyError:
        return report

    from ..topologies.dc_dc.llc_resonant_converter_synchronous_rectifier.loss_readback import (
        build_llc_sr_loss_readback,
    )
    from ..topologies.dc_dc.llc_resonant_converter_synchronous_rectifier.report_audit_readback import (
        build_llc_sr_report_audit_readback,
    )
    from ..topologies.dc_dc.llc_resonant_converter_synchronous_rectifier.timing_readback import (
        build_llc_sr_timing_readback,
    )

    stress_readback = llc_sr.get("stress_readback", {})
    if not isinstance(stress_readback, dict):
        return report
    timing_mode = str(
        llc_sr.get("timing_readback", {}).get("timing_mode", "ideal_complementary_first_pass")
        if isinstance(llc_sr.get("timing_readback", {}), dict)
        else "ideal_complementary_first_pass"
    )
    deadtime_ns = _float_metadata(report.spec.metadata.get("secondary_sync_switch_deadtime_ns"), 100.0)
    gate_drive_v = _float_metadata(report.spec.metadata.get("secondary_sync_switch_gate_drive_v"), 10.0)
    body_diode_vf_v = _float_metadata(report.spec.metadata.get("secondary_sync_switch_body_diode_vf_v"), 1.5)
    v_block_v = (
        report.stress.rectifier.voltage_max_v
        if report.stress is not None
        else _llc_sr_stress_voltage(stress_readback)
    )
    eoss_j, eoss_source, eoss_warnings = _llc_sr_selected_device_eoss_j(secondary_device, v_block_v)
    selected_sr_switch = _llc_sr_selected_switch_payload(
        secondary_device,
        eoss_j=eoss_j,
        eoss_source=eoss_source,
        eoss_warnings=eoss_warnings,
    )
    timing_readback = build_llc_sr_timing_readback(
        stress_readback,
        timing_mode=timing_mode,
        deadtime_ns=deadtime_ns,
        fsw_hz=float(report.candidate.fs_hz),
    )
    selected_sr_loss = _selected_role_loss(active_scheme, "secondary_sync_switch")
    loss_readback = build_llc_sr_loss_readback(
        stress_readback,
        secondary_sync_switch_part_number=selected_sr_switch.get("part_number"),
        rds_on_ohm=_positive_float_or_none(secondary_device.static.rds_on_typ_25C_Ohm),
        qg_total_nc=_positive_float_or_none(secondary_device.static.qg_total_nC),
        coss_pf=_positive_float_or_none(secondary_device.static.coss_typ_pF),
        eoss_uj=eoss_j * 1e6 if eoss_source == "selected_device_eoss_energy_table" else None,
        deadtime_ns=deadtime_ns,
        body_diode_forward_drop_v=body_diode_vf_v,
        gate_drive_v=gate_drive_v,
        fsw_hz=float(report.candidate.fs_hz),
        selected_loss_result=selected_sr_loss,
    )
    report_audit_readback = build_llc_sr_report_audit_readback(
        stress_readback,
        loss_readback,
        selected_secondary_sync_switch=selected_sr_switch,
        timing_readback=timing_readback,
    )
    refreshed_llc_sr = dict(llc_sr)
    refreshed_llc_sr.update(
        {
            "selected_secondary_sync_switch": selected_sr_switch,
            "timing_readback": timing_readback,
            "loss_readback": loss_readback,
            "report_audit_readback": report_audit_readback,
            "selected_scheme_id": active_scheme.scheme_id,
            "selected_parallel_count": active_scheme.parallel_count,
        }
    )
    refreshed_metadata = dict(report.candidate.metadata)
    refreshed_metadata["llc_sr"] = refreshed_llc_sr
    refreshed_candidate = replace(
        report.candidate,
        notes=_append_unique(
            list(report.candidate.notes),
            "LLC SR selected-device loss/timing readback was refreshed from the selected secondary_sync_switch.",
        ),
        metadata=refreshed_metadata,
    )
    return replace(report, candidate=refreshed_candidate)


def _selected_role_loss(active_scheme: SemiconductorSchemeResult, role: str) -> DeviceLossResult | None:
    for key, loss_result in active_scheme.per_device_design_point_losses.items():
        if key.endswith(f":{role}"):
            return loss_result
    return None


def _llc_sr_selected_switch_payload(device, *, eoss_j: float, eoss_source: str, eoss_warnings: list[str]) -> dict[str, object]:
    return {
        "role": "secondary_sync_switch",
        "selection_source": "pe_claw_semiconductor_pipeline",
        "selection_status": "selected",
        "scalar_source": (
            "semiconductor_library_static_plus_xml_dynamic"
            if eoss_source == "selected_device_eoss_energy_table"
            else "semiconductor_library_static_plus_coss_proxy"
        ),
        "part_number": device.part_number,
        "manufacturer": device.manufacturer,
        "device_type": device.selection_device_type,
        "device_structure_type": device.device_structure_type,
        "package_level": device.package_level,
        "package": device.static.package,
        "voltage_rating_v": float(device.static.vdss_max_V),
        "current_rating_a": float(device.static.id_cont_100C_A),
        "pulse_current_rating_a": float(device.static.id_pulse_A),
        "rds_on_ohm": float(device.static.rds_on_typ_25C_Ohm),
        "qg_total_nc": float(device.static.qg_total_nC),
        "coss_pf": float(device.static.coss_typ_pF),
        "eoss_uj": eoss_j * 1e6 if eoss_source == "selected_device_eoss_energy_table" else None,
        "eoss_proxy_uj": eoss_j * 1e6 if eoss_source == "selected_device_coss_proxy" else None,
        "eoss_source": eoss_source,
        "dynamic_source_name": device.dynamic.source_name,
        "selection_notes": (
            "Selected by the shared PE-Claw semiconductor pipeline for the LLC SR secondary_sync_switch role.",
            *tuple(eoss_warnings),
        ),
    }


def _llc_sr_selected_device_eoss_j(device, v_block_v: float) -> tuple[float, str, list[str]]:
    warnings: list[str] = []
    if device.dynamic.eoss_energy is not None:
        try:
            return (
                max(device.dynamic.eoss_energy.evaluate(max(v_block_v, 0.0), 75.0, warnings), 0.0),
                "selected_device_eoss_energy_table",
                warnings,
            )
        except Exception as exc:
            warnings.append(f"{device.part_number}: Eoss table evaluation failed; using Coss proxy ({exc}).")
    return (
        0.5 * max(float(device.static.coss_typ_pF), 0.0) * 1e-12 * max(v_block_v, 0.0) * max(v_block_v, 0.0),
        "selected_device_coss_proxy",
        warnings,
    )


def _llc_sr_stress_voltage(stress_readback: dict[str, object]) -> float:
    role_stresses = stress_readback.get("role_stresses", {})
    if not isinstance(role_stresses, dict):
        return 0.0
    secondary = role_stresses.get("secondary_sync_switch", {})
    if not isinstance(secondary, dict):
        return 0.0
    return _float_metadata(secondary.get("v_block_v"), 0.0)


def _positive_float_or_none(value: object) -> float | None:
    number = _float_metadata(value, 0.0)
    return number if number > 0.0 else None


def _float_metadata(value: object, fallback: float) -> float:
    if value is None:
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _apply_psfb_selected_device_evidence(
    report: DesignReport,
    *,
    active_scheme: SemiconductorSchemeResult,
    registry,
) -> DesignReport:
    """Refresh PSFB device-dependent metadata from the selected semiconductors."""

    if report.spec.topology_id != _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID:
        return report
    if report.candidate is None or report.device is None:
        return report
    psfb = report.candidate.metadata.get("psfb") if isinstance(report.candidate.metadata, dict) else None
    if not isinstance(psfb, dict):
        return report
    primary_part = report.device.selected_devices.get("main_switch")
    rectifier_part = report.device.selected_devices.get("rectifier_diode")
    if not primary_part or not rectifier_part:
        return report

    try:
        primary_device = registry.get_device(primary_part)
        rectifier_device = registry.get_device(rectifier_part)
    except KeyError:
        return report

    v_block_v = report.stress.switch.voltage_max_v if report.stress is not None else report.candidate.vin_max
    rectifier_current_a = _psfb_rectifier_current_basis_a(active_scheme, report)
    eoss_j, eoss_source = _selected_device_eoss_j(primary_device, v_block_v)
    qoss_c, qoss_source = _selected_device_qoss_c(primary_device, v_block_v)
    diode_drop_v, diode_drop_source = _selected_diode_forward_voltage_v(rectifier_device, rectifier_current_a)

    refreshed_psfb = _refresh_psfb_electrical_metadata(
        report,
        dict(psfb),
        primary_part=primary_part,
        rectifier_part=rectifier_part,
        diode_drop_v=diode_drop_v,
        diode_drop_source=diode_drop_source,
        eoss_per_switch_j=eoss_j,
        eoss_source=eoss_source,
        qoss_per_switch_c=qoss_c,
        qoss_source=qoss_source,
    )
    refreshed_metadata = dict(report.candidate.metadata)
    refreshed_metadata["psfb"] = refreshed_psfb
    refreshed_candidate = replace(
        report.candidate,
        duty_nom=float(refreshed_psfb["command_duty_nom"]),
        inductance_h=max(float(refreshed_psfb["output_inductance_h"]), 0.0),
        delta_il=float(refreshed_psfb["output_inductor_current_ripple_predicted_pp_a"]),
        il_peak=float(refreshed_psfb["output_inductor_current_peak_a"]),
        il_valley=float(refreshed_psfb["output_inductor_current_valley_a"]),
        feasible=bool(refreshed_psfb["selected_device_feasible"]),
        failure_reason=None if bool(refreshed_psfb["selected_device_feasible"]) else "psfb_selected_device_margin_failed",
        notes=_append_unique(
            list(report.candidate.notes),
            "PSFB device-dependent ZVS and diode-drop evidence was refreshed from the selected primary switch and secondary rectifier diode.",
        ),
        metadata=refreshed_metadata,
    )
    refreshed_model = refreshed_psfb.get("primary_current_model")
    refreshed_model = refreshed_model if isinstance(refreshed_model, dict) else {}
    refreshed_switches = refreshed_model.get("switches")
    refreshed_switches = refreshed_switches if isinstance(refreshed_switches, dict) else {}
    refreshed_worst = refreshed_switches.get(
        refreshed_model.get("worst_switch_rms_position", "s1"), {}
    )
    refreshed_worst = refreshed_worst if isinstance(refreshed_worst, dict) else {}
    refreshed_peak_metric = refreshed_switches.get(
        refreshed_model.get("worst_switch_peak_position", "s1"), {}
    )
    refreshed_peak_metric = refreshed_peak_metric if isinstance(refreshed_peak_metric, dict) else {}
    refreshed_stress = report.stress
    if refreshed_stress is not None:
        refreshed_stress = StressResult(
            switch=StressMetric(
                voltage_max_v=refreshed_stress.switch.voltage_max_v,
                current_peak_a=float(
                    refreshed_peak_metric.get(
                        "branch_current_peak_a", refreshed_psfb["primary_peak_current_a"]
                    )
                ),
                current_rms_a=float(
                    refreshed_worst.get("branch_current_rms_a", refreshed_psfb["primary_rms_current_a"])
                ),
            ),
            rectifier=refreshed_stress.rectifier,
            notes=[
                *refreshed_stress.notes,
                "PSFB selected-device primary-current stress was refreshed from the analytic S1-S4 model.",
            ],
        )
    return replace(report, candidate=refreshed_candidate, stress=refreshed_stress)


def _refresh_psfb_electrical_metadata(
    report: DesignReport,
    psfb: dict[str, object],
    *,
    primary_part: str,
    rectifier_part: str,
    diode_drop_v: float,
    diode_drop_source: str,
    eoss_per_switch_j: float,
    eoss_source: str,
    qoss_per_switch_c: float,
    qoss_source: str,
) -> dict[str, object]:
    candidate = report.candidate
    if candidate is None:
        return psfb

    fs_hz = candidate.fs_hz
    leakage_h = float(psfb["leakage_inductance_target_h"])
    magnetizing_h = float(psfb["magnetizing_inductance_h"])
    iout_a = candidate.iout
    diode_drop_total_v = 2.0 * diode_drop_v
    turns_ratio = _psfb_selected_device_turns_ratio(
        report,
        psfb,
        diode_drop_total_v=diode_drop_total_v,
    )
    nominal = _psfb_duty_point(
        vin_v=candidate.vin_nom,
        vout_v=candidate.vout_target,
        diode_drop_total_v=diode_drop_total_v,
        turns_ratio_np_ns=turns_ratio,
        leakage_h=leakage_h,
        iout_a=iout_a,
        fs_hz=fs_hz,
    )
    low_line = _psfb_duty_point(
        vin_v=candidate.vin_min,
        vout_v=candidate.vout_target,
        diode_drop_total_v=diode_drop_total_v,
        turns_ratio_np_ns=turns_ratio,
        leakage_h=leakage_h,
        iout_a=iout_a,
        fs_hz=fs_hz,
    )
    high_line = _psfb_duty_point(
        vin_v=candidate.vin_max,
        vout_v=candidate.vout_target,
        diode_drop_total_v=diode_drop_total_v,
        turns_ratio_np_ns=turns_ratio,
        leakage_h=leakage_h,
        iout_a=iout_a,
        fs_hz=fs_hz,
    )
    secondary_rectified_nom_v = candidate.vin_nom / max(turns_ratio, 1e-12) - diode_drop_total_v
    output_filter_voltage_v = secondary_rectified_nom_v - candidate.vout_target
    delta_il_target_a = float(
        psfb.get("output_inductor_current_ripple_target_pp_a", candidate.delta_il)
    )
    output_ripple_frequency_hz = float(psfb.get("output_ripple_frequency_hz", 2.0 * fs_hz))
    output_inductance_h = (
        output_filter_voltage_v * nominal["effective_duty"] / max(delta_il_target_a * fs_hz, 1e-12)
    )
    delta_il_predicted_a = output_filter_voltage_v * nominal["effective_duty"] / max(
        output_inductance_h * output_ripple_frequency_hz,
        1e-12,
    )
    output_inductor_peak_a = iout_a + 0.5 * delta_il_predicted_a
    output_inductor_valley_a = iout_a - 0.5 * delta_il_predicted_a
    primary_current = _calculate_psfb_primary_current(
        vin_v=candidate.vin_nom,
        vout_v=candidate.vout_target,
        diode_drop_total_v=diode_drop_total_v,
        iout_a=iout_a,
        output_inductor_ripple_pp_a=delta_il_predicted_a,
        turns_ratio_np_ns=turns_ratio,
        switching_frequency_hz=fs_hz,
        command_duty=nominal["command_duty"],
        effective_duty=nominal["effective_duty"],
        duty_loss=nominal["duty_loss"],
        magnetizing_inductance_h=magnetizing_h,
        leakage_inductance_h=leakage_h,
        output_inductance_h=output_inductance_h,
    )
    primary_rms_current_a = primary_current.switch_metric(
        primary_current.worst_switch_rms_position
    ).branch_current_rms_a
    primary_peak_current_a = primary_current.switch_metric(
        primary_current.worst_switch_peak_position
    ).branch_current_peak_a
    zvs = _psfb_zvs_evidence(
        i_commutation_a=max(output_inductor_valley_a / turns_ratio, 1e-12),
        leakage_h=leakage_h,
        magnetizing_h=magnetizing_h,
        vin_nom_v=candidate.vin_nom,
        command_duty_nom=nominal["command_duty"],
        fs_hz=fs_hz,
        eoss_per_switch_j=eoss_per_switch_j,
        qoss_per_switch_c=qoss_per_switch_c,
        deadtime_ns=float(psfb["zvs"].get("deadtime_available_ns", 0.0)) if isinstance(psfb.get("zvs"), dict) else 0.0,
        zvs_load_ratio_min=float(psfb.get("zvs_load_ratio_min", 0.50)),
    )
    zvs.update({
        "eoss_per_switch_j": eoss_per_switch_j,
        "eoss_source": eoss_source,
        "qoss_per_switch_c": qoss_per_switch_c,
        "qoss_source": qoss_source,
    })
    zvs_data_status = str(zvs.get("zvs_data_status", ""))
    zvs_hard_fail = zvs_data_status == "selected_device_data" and zvs.get("full_load_zvs_pass") is False
    selected_device_feasible = (
        low_line["effective_duty"] <= float(psfb["max_effective_duty"]) + 1e-9
        and low_line["command_duty"] <= float(psfb["max_command_duty"])
        and output_filter_voltage_v > 0.0
        and not zvs_hard_fail
    )

    psfb.update({
        "device_parameter_source": "selected_semiconductor_devices",
        "selected_primary_switch_part_number": primary_part,
        "selected_rectifier_diode_part_number": rectifier_part,
        "turns_ratio_np_ns": turns_ratio,
        "rectifier_diode_drop_v": diode_drop_v,
        "rectifier_diode_drop_total_v": diode_drop_total_v,
        "rectifier_diode_drop_source": diode_drop_source,
        "effective_duty_nom": nominal["effective_duty"],
        "duty_loss_nom": nominal["duty_loss"],
        "command_duty_nom": nominal["command_duty"],
        "effective_duty_at_vin_min": low_line["effective_duty"],
        "duty_loss_at_vin_min": low_line["duty_loss"],
        "command_duty_at_vin_min": low_line["command_duty"],
        "effective_duty_at_vin_max": high_line["effective_duty"],
        "duty_loss_at_vin_max": high_line["duty_loss"],
        "command_duty_at_vin_max": high_line["command_duty"],
        "secondary_rectified_nom_v": secondary_rectified_nom_v,
        "output_inductance_h": output_inductance_h,
        "output_inductor_current_ripple_target_pp_a": delta_il_target_a,
        "output_inductor_current_ripple_predicted_pp_a": delta_il_predicted_a,
        "effective_inductor_current_ripple_ratio": delta_il_predicted_a / max(iout_a, 1e-12),
        "output_inductor_current_peak_a": output_inductor_peak_a,
        "output_inductor_current_valley_a": output_inductor_valley_a,
        "primary_rms_current_a": primary_rms_current_a,
        "primary_peak_current_a": primary_peak_current_a,
        "primary_current_model": primary_current.as_metadata(
            blocking_voltage_peak_v=candidate.vin_max
        ),
        "rectifier_avg_current_a": 0.5 * iout_a,
        "diode_reverse_voltage_stress_v": candidate.vin_max / max(turns_ratio, 1e-12),
        "diode_reverse_voltage_stress_basis": "secondary_full_bridge_reflected_high_line_input",
        "zvs": zvs,
        "selected_device_feasible": selected_device_feasible,
    })
    return psfb


def _psfb_selected_device_turns_ratio(
    report: DesignReport,
    psfb: dict[str, object],
    *,
    diode_drop_total_v: float,
) -> float:
    """Resolve PSFB turns ratio after selected-device diode-drop evidence is known."""

    candidate = report.candidate
    if candidate is None:
        return float(psfb["turns_ratio_np_ns"])
    configured = report.spec.metadata.get("turns_ratio_np_ns")
    if isinstance(configured, str) and configured.strip().casefold() == "auto":
        return (
            float(psfb["max_effective_duty"])
            * candidate.vin_min
            / max(candidate.vout_target + diode_drop_total_v, 1e-12)
        )
    return float(psfb["turns_ratio_np_ns"])


def _psfb_rectifier_current_basis_a(active_scheme: SemiconductorSchemeResult, report: DesignReport) -> float:
    stress = active_scheme.per_device_selection_stresses.get("rectifier_diode")
    if stress is not None:
        return max(abs(stress.i_avg_A), abs(stress.i_rms_A), abs(stress.i_turn_on_A), abs(stress.i_turn_off_A))
    if report.stress is not None:
        return max(
            abs(report.stress.rectifier.current_avg_a or 0.0),
            abs(report.stress.rectifier.current_rms_a or 0.0),
            abs(report.stress.rectifier.current_peak_a or 0.0),
        )
    return abs(report.candidate.iout) if report.candidate is not None else 0.0


def _selected_device_eoss_j(device, v_block_v: float) -> tuple[float, str]:
    warnings: list[str] = []
    if device.dynamic.eoss_energy is not None:
        return (
            max(device.dynamic.eoss_energy.evaluate(v_block_v, 75.0, warnings), 0.0),
            "selected_device_eoss_energy_table",
        )
    return (
        0.5 * max(device.static.coss_typ_pF, 0.0) * 1e-12 * v_block_v * v_block_v,
        "selected_device_coss_proxy",
    )


def _selected_device_qoss_c(device, v_block_v: float) -> tuple[float, str]:
    return (
        max(device.static.coss_typ_pF, 0.0) * 1e-12 * max(v_block_v, 0.0),
        "selected_device_coss_proxy",
    )


def _selected_diode_forward_voltage_v(device, current_a: float) -> tuple[float, str]:
    warnings: list[str] = []
    current = max(abs(current_a), 1e-9)
    if device.dynamic.conduction_on_voltage_drop is not None:
        return (
            abs(device.dynamic.conduction_on_voltage_drop.evaluate(current, 75.0, warnings)),
            "selected_device_conduction_table",
        )
    return max(device.static.vsd_typ_V, 0.0), "selected_device_static_vsd_typ"


def _psfb_duty_point(
    *,
    vin_v: float,
    vout_v: float,
    diode_drop_total_v: float,
    turns_ratio_np_ns: float,
    leakage_h: float,
    iout_a: float,
    fs_hz: float,
) -> dict[str, float]:
    effective_duty = turns_ratio_np_ns * (vout_v + diode_drop_total_v) / max(vin_v, 1e-12)
    duty_loss = 4.0 * leakage_h * iout_a * fs_hz / max(turns_ratio_np_ns * vin_v, 1e-12)
    return {
        "effective_duty": effective_duty,
        "duty_loss": duty_loss,
        "command_duty": effective_duty + duty_loss,
    }


def _psfb_zvs_evidence(
    *,
    i_commutation_a: float,
    leakage_h: float,
    magnetizing_h: float,
    vin_nom_v: float,
    command_duty_nom: float,
    fs_hz: float,
    eoss_per_switch_j: float,
    qoss_per_switch_c: float,
    deadtime_ns: float,
    zvs_load_ratio_min: float,
) -> dict[str, float | bool | str | None]:
    magnetizing_current_a = vin_nom_v * command_duty_nom / max(4.0 * magnetizing_h * fs_hz, 1e-12)
    available_j = 0.5 * leakage_h * i_commutation_a * i_commutation_a
    available_j += 0.5 * magnetizing_h * magnetizing_current_a * magnetizing_current_a
    required_j = 4.0 * eoss_per_switch_j
    min_load_i_a = i_commutation_a * zvs_load_ratio_min
    min_load_available_j = 0.5 * leakage_h * min_load_i_a * min_load_i_a
    min_load_available_j += 0.5 * magnetizing_h * magnetizing_current_a * magnetizing_current_a
    total_qoss_c = 4.0 * qoss_per_switch_c
    deadtime_required_ns = total_qoss_c / max(i_commutation_a, 1e-12) * 1e9
    eoss_available = required_j > 0.0
    qoss_available = total_qoss_c > 0.0
    energy_margin = available_j / required_j - 1.0 if eoss_available else None
    min_load_energy_margin = min_load_available_j / required_j - 1.0 if eoss_available else None
    return {
        "commutation_current_a": i_commutation_a,
        "magnetizing_current_a": magnetizing_current_a,
        "available_energy_j": available_j,
        "required_energy_j": required_j,
        "energy_margin": energy_margin,
        "min_load_available_energy_j": min_load_available_j,
        "min_load_energy_margin": min_load_energy_margin,
        "deadtime_required_ns": deadtime_required_ns,
        "deadtime_available_ns": deadtime_ns,
        "deadtime_margin_ns": deadtime_ns - deadtime_required_ns,
        "full_load_zvs_pass": available_j >= required_j if eoss_available else None,
        "min_load_zvs_pass": min_load_available_j >= required_j if eoss_available else None,
        "eoss_data_available": eoss_available,
        "qoss_data_available": qoss_available,
        "zvs_data_status": "selected_device_data" if eoss_available and qoss_available else "selected_device_output_capacitance_missing",
    }


def _append_unique(values: list[str], value: str) -> list[str]:
    if value not in values:
        values.append(value)
    return values


def _prefer_psfb_zvs_capable_main_switch(
    *,
    topology_id: str | None,
    role: str,
    selected_device,
    ranked_candidates: list,
    role_notes: list[str],
    audit,
) -> tuple[object | None, list, list[str], object]:
    """Prefer PSFB primary switches with dynamic switching data and Coss for ZVS evidence."""

    if topology_id != _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID:
        return selected_device, ranked_candidates, role_notes, audit
    if role.strip().casefold() != "main_switch" or not ranked_candidates:
        return selected_device, ranked_candidates, role_notes, audit
    if selected_device is not None and _has_psfb_zvs_capable_switch_data(selected_device):
        return selected_device, ranked_candidates, role_notes, audit

    zvs_capable_candidates = [
        ranked_candidate
        for ranked_candidate in ranked_candidates
        if _has_psfb_zvs_capable_switch_data(ranked_candidate.device)
    ]
    if not zvs_capable_candidates:
        return selected_device, ranked_candidates, role_notes, audit

    preferred = min(
        zvs_capable_candidates,
        key=lambda ranked_candidate: (
            ranked_candidate.score,
            ranked_candidate.loss_result.p_total_W,
            ranked_candidate.loss_result.tj_est_C,
            ranked_candidate.device.part_number,
        ),
    )
    reordered_candidates = [preferred]
    reordered_candidates.extend(
        ranked_candidate
        for ranked_candidate in ranked_candidates
        if ranked_candidate.device.part_number != preferred.device.part_number
    )
    note = (
        "PSFB ZVS data preference selected "
        f"{preferred.device.part_number} because it has XML-backed Eon/Eoff data and Coss > 0; "
        "the original hard filters and loss/thermal ranking still limit eligible candidates."
    )
    preferred_audit = replace(
        audit,
        selected_part_number=preferred.device.part_number,
        summary=(
            f"{role}: selected {preferred.device.part_number} from {audit.considered_count} candidates; "
            f"{audit.passed_count} passed hard filters; PSFB ZVS data preference applied."
        ),
    )
    return preferred.device, reordered_candidates, [*role_notes, note], preferred_audit


def _has_psfb_zvs_capable_switch_data(device) -> bool:
    dynamic = device.dynamic
    source_name = str(getattr(dynamic, "source_name", "") or "").casefold()
    has_xml_source = source_name.endswith(".xml")
    has_eon = dynamic.turn_on_energy is not None or dynamic.eon_rg_on_i_v is not None
    has_eoff = dynamic.turn_off_energy is not None or dynamic.eoff_rg_off_i_v is not None
    return has_xml_source and has_eon and has_eoff and max(device.static.coss_typ_pF, 0.0) > 0.0


def scale_switch_stress_for_parallel(stress: SwitchStress, parallel_count: int) -> SwitchStress:
    """Scale current-driven per-device stress for an ideal N-way parallel assembly."""

    if parallel_count <= 0:
        raise ValueError("parallel_count must be positive.")
    if parallel_count == 1:
        return stress
    return replace(
        stress,
        i_rms_A=stress.i_rms_A / parallel_count,
        i_avg_A=stress.i_avg_A / parallel_count,
        i_turn_on_A=stress.i_turn_on_A / parallel_count,
        i_turn_off_A=stress.i_turn_off_A / parallel_count,
    )


def _evaluate_parallel_scheme(
    *,
    registry,
    switch_candidates,
    registered_switch_candidates,
    design_cases,
    stresses_by_role: dict[str, list[SwitchStress]],
    scheme_id: str,
    label: str,
    parallel_count: int,
    library_filter: SemiconductorLibraryFilter,
    topology_id: str | None,
    spec_metadata: dict[str, object],
    report: DesignReport,
) -> SemiconductorSchemeResult:
    registered_candidate_counts: dict[str, int] = {}
    selected_devices: dict[str, str] = {}
    candidate_counts: dict[str, int] = {}
    passed_candidate_counts: dict[str, int] = {}
    rejected_candidate_counts: dict[str, int] = {}
    rejection_breakdowns: dict[str, dict[str, int]] = {}
    closest_rejected_candidates: dict[str, list[dict[str, object]]] = {}
    selection_summaries: dict[str, str] = {}
    candidate_traces: dict[str, list[dict[str, object]]] = {}
    per_device_selection_stresses: dict[str, SwitchStress] = {}
    per_device_design_point_losses: dict[str, DeviceLossResult] = {}
    total_scheme_loss_by_key: dict[str, float] = {}
    role_results: list[SemiconductorRoleSchemeResult] = []
    selected_device_objects: dict[str, object] = {}
    notes: list[str] = [
        f"{label}: per-device current stresses are scaled by 1/{parallel_count} with blocking voltage unchanged.",
    ]

    for role, role_stresses in stresses_by_role.items():
        registered_candidate_counts[role] = len(registered_switch_candidates)
        if not _is_selectable_semiconductor_role(role):
            candidate_counts[role] = 0
            passed_candidate_counts[role] = 0
            rejected_candidate_counts[role] = 0
            rejection_breakdowns[role] = _empty_rejection_breakdown()
            closest_rejected_candidates[role] = []
            notes.append(f"{label} {role}: no semiconductor role-compatibility rule is available, so this role was not selected.")
            role_results.append(
                SemiconductorRoleSchemeResult(
                    role=role,
                    parallel_count=parallel_count,
                    registered_candidate_count=len(registered_switch_candidates),
                    candidate_count=0,
                    passed_candidate_count=0,
                    rejected_candidate_count=0,
                    notes=["No switch-role candidate evaluation was performed for this role."],
                )
            )
            continue

        role_category = _category_for_role(role, topology_id, spec_metadata)
        topology_position_count = _topology_position_count_for_role(role, topology_id, spec_metadata)
        role_source_candidates = switch_candidates
        diode_binding_policy = str(spec_metadata.get(DIODE_BINDING_POLICY_INPUT_KEY, "auto"))
        bound_to_role: str | None = None
        if _is_rectifier_diode_role(role) and topology_id in _INDEPENDENT_SECONDARY_DIODE_TOPOLOGY_IDS:
            diode_binding_policy = "independent"
        elif _is_rectifier_diode_role(role) and diode_binding_policy in {"auto", "internal_module_diode"}:
            main_device = selected_device_objects.get("main_switch")
            if main_device is not None and _requires_internal_diode_binding(main_device):
                role_source_candidates = _bound_internal_diode_candidates(registered_switch_candidates, main_device)
                role_category = INTERNAL_MODULE_DIODE_CATEGORY
                diode_binding_policy = "internal_module_diode"
                bound_to_role = "main_switch"
            elif main_device is not None and _declares_internal_diode_binding(main_device):
                role_source_candidates = []
                role_category = INTERNAL_MODULE_DIODE_CATEGORY
                diode_binding_policy = "internal_module_diode"
                bound_to_role = "main_switch"
            elif main_device is not None and diode_binding_policy == "auto":
                diode_binding_policy = "independent"
            elif diode_binding_policy == "internal_module_diode":
                role_source_candidates = []
                role_category = INTERNAL_MODULE_DIODE_CATEGORY
        role_candidates, role_incompatible_count, allowed_types = _filter_candidates_for_role(
            role_source_candidates,
            role,
            topology_id,
            role_category,
        )
        role_manufacturer = _role_manufacturer_for_topology(role, topology_id, spec_metadata)
        role_manufacturer_removed_count = 0
        if bound_to_role is None:
            role_candidates, role_manufacturer_removed_count = _filter_candidates_by_manufacturer(
                role_candidates,
                role_manufacturer,
            )
        role_candidates, module_diode_rejection_notes = _filter_unavailable_module_bound_switches(
            role_candidates,
            role,
            topology_id,
        )
        role_incompatible_count += role_manufacturer_removed_count + len(module_diode_rejection_notes)
        role_filter_message = (
            f"{label} {role}: role-compatible filter allows {_format_allowed_device_types(allowed_types)}; "
            f"{role_incompatible_count} of {len(role_source_candidates)} library-filtered candidates were removed; "
            f"category={role_category or 'legacy'}, manufacturer={role_manufacturer}."
        )
        notes.append(role_filter_message)
        for rejection_note in module_diode_rejection_notes:
            notes.append(f"{label} {role}: {rejection_note}.")
        for device in role_candidates:
            _, structure_warning = is_structure_compatible_with_role(device, role, topology_id=topology_id)
            if structure_warning is not None:
                notes.append(f"{label} {role}: {structure_warning}")

        if not role_source_candidates:
            candidate_counts[role] = 0
            passed_candidate_counts[role] = 0
            rejected_candidate_counts[role] = 0
            rejection_breakdowns[role] = _empty_rejection_breakdown()
            closest_rejected_candidates[role] = []
            no_candidate_message = f"No semiconductor candidates match {library_filter.describe()}."
            selection_summaries[role] = f"{role}: {no_candidate_message}"
            candidate_traces[role] = []
            notes.append(f"{label} {role}: {no_candidate_message}")
            role_results.append(
                SemiconductorRoleSchemeResult(
                    role=role,
                    parallel_count=parallel_count,
                    registered_candidate_count=len(registered_switch_candidates),
                    candidate_count=0,
                    passed_candidate_count=0,
                    rejected_candidate_count=0,
                    diode_binding_policy=diode_binding_policy if _is_rectifier_diode_role(role) else None,
                    bound_to_role=bound_to_role,
                    notes=[no_candidate_message],
                )
            )
            continue

        if not role_candidates:
            candidate_counts[role] = 0
            passed_candidate_counts[role] = 0
            rejected_candidate_counts[role] = 0
            rejection_breakdowns[role] = _empty_rejection_breakdown(
                after_library_prefilter=len(role_source_candidates),
                role_incompatible=role_incompatible_count,
            )
            closest_rejected_candidates[role] = []
            if topology_id in {_LLC_DIODE_RECTIFIER_TOPOLOGY_ID, _PSFB_DIODE_RECTIFIER_TOPOLOGY_ID}:
                no_candidate_message = (
                    f"No role-compatible semiconductor candidates: role {role} requires "
                    f"{_format_allowed_device_types(allowed_types)}, category={role_category or 'legacy'}, "
                    f"manufacturer={role_manufacturer}."
                )
            else:
                no_candidate_message = (
                    f"No role-compatible semiconductor candidates: role {role} requires "
                    f"{_format_allowed_device_types(allowed_types)}, but selected device type is {library_filter.device_type}."
                )
            selection_summaries[role] = f"{role}: {no_candidate_message}"
            candidate_traces[role] = []
            notes.append(f"{label} {role}: {no_candidate_message}")
            role_results.append(
                SemiconductorRoleSchemeResult(
                    role=role,
                    parallel_count=parallel_count,
                    registered_candidate_count=len(registered_switch_candidates),
                    candidate_count=0,
                    passed_candidate_count=0,
                    rejected_candidate_count=0,
                    diode_binding_policy=diode_binding_policy if _is_rectifier_diode_role(role) else None,
                    bound_to_role=bound_to_role,
                    notes=[role_filter_message, no_candidate_message],
                )
            )
            continue

        selection_stress = scale_switch_stress_for_parallel(merge_switch_stresses(role_stresses), parallel_count)
        per_device_selection_stresses[role] = selection_stress
        selected_device, ranked_candidates, role_notes, audit = select_switch_device_with_audit(
            role_candidates,
            selection_stress,
            loss_evaluator=lambda candidate, candidate_stress: _evaluate_switch_loss_for_context(
                candidate,
                candidate_stress,
                report=report,
            ),
        )
        selected_device, ranked_candidates, role_notes, audit = _prefer_psfb_zvs_capable_main_switch(
            topology_id=topology_id,
            role=role,
            selected_device=selected_device,
            ranked_candidates=ranked_candidates,
            role_notes=role_notes,
            audit=audit,
        )
        candidate_counts[role] = audit.considered_count
        passed_candidate_counts[role] = audit.passed_count
        rejected_candidate_counts[role] = audit.rejected_count
        selection_summaries[role] = audit.summary
        candidate_traces[role] = [_trace_to_dict(trace) for trace in audit.traces]
        rejection_breakdowns[role] = _build_rejection_breakdown(
            candidate_traces[role],
            after_library_prefilter=len(role_source_candidates),
            role_incompatible=role_incompatible_count,
        )
        closest_rejected_candidates[role] = _select_closest_rejected_candidates(candidate_traces[role])
        for note in role_notes:
            notes.append(f"{label} {role}: {note}")
        if audit.passed_count == 0:
            notes.append(f"{label} {role}: No {library_filter.short_label()} candidates passed the hard filters at this design point.")
            notes.extend(
                _build_rejection_breakdown_notes(
                    label=label,
                    role=role,
                    breakdown=rejection_breakdowns[role],
                    closest_rejected=closest_rejected_candidates[role],
                )
            )
        if selected_device is None and not ranked_candidates:
            role_results.append(
                SemiconductorRoleSchemeResult(
                    role=role,
                    parallel_count=parallel_count,
                    per_device_stress=selection_stress,
                    registered_candidate_count=len(registered_switch_candidates),
                    candidate_count=audit.considered_count,
                    passed_candidate_count=audit.passed_count,
                    rejected_candidate_count=audit.rejected_count,
                    diode_binding_policy=diode_binding_policy if _is_rectifier_diode_role(role) else None,
                    bound_to_role=bound_to_role,
                    notes=["No candidate passed the existing selection logic for this scheme."],
                )
            )
            continue

        evaluated_device = selected_device or ranked_candidates[0].device
        role_contexts: list[_SchemeSelectionContext] = []
        for case in design_cases:
            for stress in case.stresses:
                if stress.role != role:
                    continue
                scaled_stress = scale_switch_stress_for_parallel(stress, parallel_count)
                loss_result = _evaluate_role_loss(evaluated_device, report, scaled_stress, case.operating_point)
                key = f"{case.case_id}:{role}"
                per_device_design_point_losses[key] = loss_result
                total_context = _build_scheme_selection_context(
                    role=role,
                    case_id=case.case_id,
                    device=evaluated_device,
                    per_device_loss=loss_result,
                    scaled_stress=scaled_stress,
                    parallel_count=parallel_count,
                    topology_position_count=topology_position_count,
                )
                total_scheme_loss_by_key[key] = total_context.total_loss_w
                role_contexts.append(total_context)

        if selected_device is None:
            notes.append(
                f"{label} {role}: {evaluated_device.part_number} was evaluated at the design point, "
                "but no candidate passed the selection criteria."
            )
        else:
            selected_devices[role] = selected_device.part_number
            selected_device_objects[role] = selected_device

        if any(not loss_result.bare_reference_valid for loss_result in (context.per_device_loss for context in role_contexts)):
            notes.append(
                f"{label} {role}: {evaluated_device.part_number} bare-package reference exceeded Tj,max at the design point; "
                "this is advisory because the sink feasibility check remains based on the target-junction backsolve."
            )

        role_results.append(
            _summarize_scheme_role(
                role=role,
                device=evaluated_device,
                parallel_count=parallel_count,
                selection_stress=selection_stress,
                audit=audit,
                contexts=role_contexts,
                registered_candidate_count=len(registered_switch_candidates),
                topology_position_count=topology_position_count,
                diode_binding_policy=diode_binding_policy if _is_rectifier_diode_role(role) else None,
                bound_to_role=bound_to_role,
            )
        )

    role_results = list(_annotate_module_bound_role_results(tuple(role_results)))
    total_scheme_loss_w = 0.0
    feasible = False
    switch_role_results = [role_result for role_result in role_results if _is_selectable_semiconductor_role(role_result.role)]
    if switch_role_results:
        total_scheme_loss_w = sum(role_result.total_loss_w or 0.0 for role_result in switch_role_results if role_result.selected_part_number is not None)
        selected_required_roles = {role_result.role for role_result in switch_role_results if role_result.selected_part_number is not None}
        required_roles = set(get_semiconductor_roles_for_topology(topology_id or ""))
        if required_roles:
            missing_required_roles = sorted(required_roles - selected_required_roles)
            if missing_required_roles:
                missing_text = ", ".join(missing_required_roles)
                notes.append(
                    f"{label}: incomplete semiconductor scheme; missing selected required role(s): {missing_text}."
                )
        else:
            missing_required_roles = []
        feasible = (
            not missing_required_roles
            and all(role_result.selected_part_number is not None for role_result in switch_role_results)
            and all(bool(role_result.target_junction_feasible) for role_result in switch_role_results)
        )
    scheme_result = SemiconductorSchemeResult(
        scheme_id=scheme_id,
        label=label,
        parallel_count=parallel_count,
        registered_candidate_counts=registered_candidate_counts,
        selected_devices=selected_devices,
        candidate_counts=candidate_counts,
        passed_candidate_counts=passed_candidate_counts,
        rejected_candidate_counts=rejected_candidate_counts,
        rejection_breakdowns=rejection_breakdowns,
        closest_rejected_candidates=closest_rejected_candidates,
        selection_summaries=selection_summaries,
        candidate_traces=candidate_traces,
        per_device_selection_stresses=per_device_selection_stresses,
        per_device_design_point_losses=per_device_design_point_losses,
        total_scheme_loss_by_key=total_scheme_loss_by_key,
        role_results=tuple(role_results),
        total_scheme_loss_w=total_scheme_loss_w,
        feasible=feasible,
        notes=notes,
    )
    return validate_scheme_required_roles(scheme_result, topology_id)


def _select_active_semiconductor_scheme(
    scheme_results: tuple[SemiconductorSchemeResult, ...],
    *,
    topology_id: str | None,
) -> SemiconductorSchemeResult:
    """Pick the scheme used for global selected-device metadata and refresh losses."""

    if not scheme_results:
        raise ValueError("At least one semiconductor scheme result is required.")

    required_roles = set(get_semiconductor_roles_for_topology(topology_id or ""))
    if not required_roles:
        return next((scheme for scheme in scheme_results if scheme.scheme_id == "single"), scheme_results[0])

    def has_complete_required_roles(scheme: SemiconductorSchemeResult) -> bool:
        return bool(scheme.complete) and required_roles.issubset(set(scheme.selected_devices))

    complete_feasible = [scheme for scheme in scheme_results if has_complete_required_roles(scheme) and scheme.feasible]
    if complete_feasible:
        return min(complete_feasible, key=lambda scheme: (scheme.parallel_count, scheme.total_scheme_loss_w or float("inf")))

    complete = [scheme for scheme in scheme_results if has_complete_required_roles(scheme)]
    if complete:
        return min(complete, key=lambda scheme: (scheme.parallel_count, scheme.total_scheme_loss_w or float("inf")))

    return next((scheme for scheme in scheme_results if scheme.scheme_id == "single"), scheme_results[0])


def validate_scheme_required_roles(scheme: SemiconductorSchemeResult, topology_id: str | None) -> SemiconductorSchemeResult:
    """Mark a semiconductor scheme incomplete when topology-required roles are not selected."""

    required_roles = tuple(get_semiconductor_roles_for_topology(topology_id or ""))
    if not required_roles:
        return replace(scheme, complete=True, incomplete_reason=None)

    role_results_by_name = {role_result.role: role_result for role_result in scheme.role_results}
    missing_roles = [
        role
        for role in required_roles
        if role not in role_results_by_name or role_results_by_name[role].selected_part_number is None
    ]
    if not missing_roles:
        return replace(scheme, complete=True, incomplete_reason=None)

    if len(missing_roles) == 1:
        incomplete_reason = "missing selected semiconductor role: " + missing_roles[0]
    else:
        incomplete_reason = "missing selected semiconductor roles: " + ", ".join(missing_roles)
    notes = list(scheme.notes)
    scheme_note = f"{scheme.label}: incomplete semiconductor scheme; {incomplete_reason}."
    if scheme_note not in notes:
        notes.append(scheme_note)
    return replace(
        scheme,
        complete=False,
        incomplete_reason=incomplete_reason,
        feasible=False,
        notes=notes,
    )


def _build_scheme_selection_context(
    *,
    role: str,
    case_id: str,
    device,
    per_device_loss: DeviceLossResult,
    scaled_stress: SwitchStress,
    parallel_count: int,
    topology_position_count: int = 1,
) -> _SchemeSelectionContext:
    total_physical_device_count = max(int(topology_position_count), 1) * max(int(parallel_count), 1)
    total_loss_w = total_physical_device_count * per_device_loss.p_total_W
    sink_summary = _estimate_parallel_scheme_sink(
        per_device_loss=per_device_loss,
        scaled_stress=scaled_stress,
        total_physical_device_count=total_physical_device_count,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
    )
    return _SchemeSelectionContext(
        role=role,
        case_id=case_id,
        per_device_loss=per_device_loss,
        total_loss_w=total_loss_w,
        topology_position_count=max(int(topology_position_count), 1),
        total_physical_device_count=total_physical_device_count,
        sink_volume_cm3=sink_summary["sink_volume_cm3"],
        sink_model_label=sink_summary["sink_model_label"],
        sink_requirement_label=sink_summary["sink_requirement_label"],
        thermal_feasible=sink_summary["thermal_feasible"],
    )


def _estimate_parallel_scheme_sink(
    *,
    per_device_loss: DeviceLossResult,
    scaled_stress: SwitchStress,
    total_physical_device_count: int,
    rth_jc_k_per_w: float,
) -> dict[str, float | bool | None | str]:
    ambient_temp_c = scaled_stress.ambient_temp_C if scaled_stress.ambient_temp_C is not None else 25.0
    target_junction_temp_c = per_device_loss.target_junction_temp_c
    if target_junction_temp_c is None:
        return {
            "sink_volume_cm3": None,
            "sink_model_label": "",
            "sink_requirement_label": "No target-junction temperature was available for sink aggregation.",
            "thermal_feasible": False,
        }

    if target_junction_temp_c <= ambient_temp_c:
        return {
            "sink_volume_cm3": None,
            "sink_model_label": "",
            "sink_requirement_label": "Target junction temperature is not above ambient, so the shared-sink backsolve is invalid.",
            "thermal_feasible": False,
        }

    total_loss_w = max(int(total_physical_device_count), 1) * per_device_loss.p_total_W
    if total_loss_w <= 0.0:
        return {
            "sink_volume_cm3": 0.0,
            "sink_model_label": "shared_parallel_sink_no_sink_required",
            "sink_requirement_label": "Combined scheme loss is nonpositive, so no shared sink is required.",
            "thermal_feasible": True,
        }

    rth_cs_k_per_w = _resolve_loss_interface_rth_cs(
        per_device_loss=per_device_loss,
        rth_jc_k_per_w=rth_jc_k_per_w,
    )
    allowed_sink_rth_k_per_w = (
        target_junction_temp_c
        - ambient_temp_c
        - per_device_loss.p_total_W * (rth_jc_k_per_w + rth_cs_k_per_w)
    ) / total_loss_w
    if allowed_sink_rth_k_per_w <= 0.0:
        return {
            "sink_volume_cm3": None,
            "sink_model_label": "",
            "sink_requirement_label": (
                "Shared-sink backsolve indicates the per-device package plus interface path already consumes the junction budget."
            ),
            "thermal_feasible": False,
        }

    estimated_sink_volume_cm3, sink_model_label = estimate_sink_volume(
        allowed_sink_rth_k_per_w,
        cooling_mode=DEFAULT_COOLING_MODE,
    )
    return {
        "sink_volume_cm3": estimated_sink_volume_cm3,
        "sink_model_label": sink_model_label,
        "sink_requirement_label": (
            f"Shared-sink backsolve: required sink-to-ambient thermal resistance <= {allowed_sink_rth_k_per_w:.3f} K/W."
        ),
        "thermal_feasible": True,
    }


def _resolve_loss_interface_rth_cs(
    *,
    per_device_loss: DeviceLossResult,
    rth_jc_k_per_w: float,
) -> float:
    if per_device_loss.interface_rth_cs_k_per_w is not None:
        return per_device_loss.interface_rth_cs_k_per_w
    if per_device_loss.required_total_rth_k_per_w is None:
        return 0.0
    required_sink_rth_k_per_w = per_device_loss.required_sink_rth_k_per_w or 0.0
    return per_device_loss.required_total_rth_k_per_w - required_sink_rth_k_per_w - rth_jc_k_per_w


def _annotate_module_bound_role_results(
    role_results: tuple[SemiconductorRoleSchemeResult, ...],
) -> tuple[SemiconductorRoleSchemeResult, ...]:
    by_role = {role_result.role: role_result for role_result in role_results}
    replacements: dict[str, SemiconductorRoleSchemeResult] = {}
    for role_result in role_results:
        if role_result.bound_to_role is None or role_result.selected_part_number is None:
            continue
        source = by_role.get(role_result.bound_to_role)
        if source is None or source.selected_part_number is None:
            continue
        replacements[role_result.role] = replace(
            role_result,
            paired_switch_part_number=source.selected_part_number,
        )
        replacements[source.role] = replace(
            replacements.get(source.role, source),
            diode_binding_policy="provides_internal_module_diode",
            paired_diode_part_number=role_result.selected_part_number,
        )
    return tuple(replacements.get(role_result.role, role_result) for role_result in role_results)


def _summarize_scheme_role(
    *,
    role: str,
    device,
    parallel_count: int,
    selection_stress: SwitchStress,
    audit,
    contexts: list[_SchemeSelectionContext],
    registered_candidate_count: int,
    topology_position_count: int = 1,
    diode_binding_policy: str | None = None,
    bound_to_role: str | None = None,
) -> SemiconductorRoleSchemeResult:
    primary_context = max(
        contexts,
        key=lambda context: (
            context.sink_volume_cm3 if context.sink_volume_cm3 is not None else -1.0,
            context.total_loss_w,
        ),
    )
    return SemiconductorRoleSchemeResult(
        role=role,
        parallel_count=parallel_count,
        registered_candidate_count=registered_candidate_count,
        selected_part_number=device.part_number,
        vendor=device.vendor,
        device_type=device.selection_device_type,
        device_structure_type=device.device_structure_type,
        package_level=device.package_level,
        module_internal_topology=device.module_internal_topology,
        diode_subtype=device.diode_subtype,
        module_group_id=device.module_group_id,
        module_section_role=device.module_section_role,
        paired_switch_part_number=device.paired_switch_part_number,
        paired_diode_part_number=device.paired_diode_part_number,
        diode_binding_policy=diode_binding_policy,
        bound_to_role=bound_to_role,
        thermal_source=primary_context.per_device_loss.thermal_source or primary_context.per_device_loss.method,
        package=device.static.package,
        per_device_stress=selection_stress,
        candidate_count=audit.considered_count,
        passed_candidate_count=audit.passed_count,
        rejected_candidate_count=audit.rejected_count,
        per_device_loss_w=primary_context.per_device_loss.p_total_W,
        total_loss_w=primary_context.total_loss_w,
        topology_position_count=max(int(topology_position_count), 1),
        total_physical_device_count=max(int(topology_position_count), 1) * max(int(parallel_count), 1),
        target_junction_feasible=primary_context.thermal_feasible,
        sink_volume_cm3=primary_context.sink_volume_cm3,
        sink_model_label=primary_context.sink_model_label,
        sink_requirement_label=primary_context.sink_requirement_label,
        notes=[
            f"Primary case: {primary_context.case_id}.",
            (
                f"Topology positions: {max(int(topology_position_count), 1)}; "
                f"parallel per position: {parallel_count}; "
                f"total physical devices: {max(int(topology_position_count), 1) * max(int(parallel_count), 1)}."
            ),
            audit.summary,
        ],
    )


def _build_scheme_comparison_notes(scheme_results: tuple[SemiconductorSchemeResult, ...]) -> list[str]:
    notes: list[str] = []
    for scheme in scheme_results:
        has_topology_multiplier = any(
            role_result.topology_position_count > 1
            for role_result in scheme.role_results
        )
        count_basis = (
            f"{scheme.parallel_count} device(s) in parallel per topology position"
            if has_topology_multiplier
            else f"{scheme.parallel_count} device(s) per switch role"
        )
        notes.append(
            f"{scheme.label}: total design-point semiconductor loss = "
            f"{scheme.total_scheme_loss_w:.6g} W across {count_basis}."
        )
        for role_result in scheme.role_results:
            if role_result.selected_part_number is None:
                notes.append(f"{scheme.label} {role_result.role}: no selected device.")
                continue
            notes.append(
                f"{scheme.label} {role_result.role}: {role_result.selected_part_number}, "
                f"vendor={role_result.vendor or '-'}, "
                f"type={role_result.device_type or '-'}, "
                f"structure={role_result.device_structure_type or '-'}, "
                f"internal_topology={role_result.module_internal_topology or '-'}, "
                f"package_level={role_result.package_level or '-'}, "
                f"diode_subtype={role_result.diode_subtype or '-'}, "
                f"module_group_id={role_result.module_group_id or '-'}, "
                f"diode binding={role_result.diode_binding_policy or '-'}, "
                f"paired switch={role_result.paired_switch_part_number or '-'}, "
                f"paired diode={role_result.paired_diode_part_number or '-'}, "
                f"thermal source={role_result.thermal_source or '-'}, "
                f"positions={role_result.topology_position_count}, "
                f"parallel per position={role_result.parallel_count}, "
                f"total devices={role_result.total_physical_device_count}, "
                f"per-device P={_fmt_optional_float(role_result.per_device_loss_w)} W, "
                f"scheme P={_fmt_optional_float(role_result.total_loss_w)} W, "
                f"sink={_fmt_optional_float(role_result.sink_volume_cm3)} cm^3."
            )
    return notes


def _fmt_optional_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6g}"


def _trace_to_dict(trace) -> dict[str, object]:
    return {
        "candidate_part_number": trace.candidate_part_number,
        "candidate_device_type": trace.candidate_device_type,
        "candidate_manufacturer": trace.candidate_manufacturer,
        "candidate_package": trace.candidate_package,
        "candidate_structure_type": trace.candidate_structure_type,
        "candidate_internal_topology": trace.candidate_internal_topology,
        "candidate_package_level": trace.candidate_package_level,
        "candidate_diode_subtype": trace.candidate_diode_subtype,
        "candidate_module_group_id": trace.candidate_module_group_id,
        "candidate_module_section_role": trace.candidate_module_section_role,
        "candidate_voltage_rating_V": trace.candidate_voltage_rating_V,
        "required_voltage_rating_V": trace.required_voltage_rating_V,
        "passed_voltage_filter": trace.passed_voltage_filter,
        "candidate_continuous_current_rating_A": trace.candidate_continuous_current_rating_A,
        "candidate_continuous_current_rating_label": trace.candidate_continuous_current_rating_label,
        "datasheet_continuous_current_rating_A": trace.datasheet_continuous_current_rating_A,
        "required_continuous_current_A": trace.required_continuous_current_A,
        "passed_continuous_current_filter": trace.passed_continuous_current_filter,
        "candidate_pulse_current_rating_A": trace.candidate_pulse_current_rating_A,
        "datasheet_pulse_current_rating_A": trace.datasheet_pulse_current_rating_A,
        "required_pulse_current_A": trace.required_pulse_current_A,
        "passed_pulse_current_filter": trace.passed_pulse_current_filter,
        "passed_current_filter": trace.passed_current_filter,
        "passed_thermal_filter": trace.passed_thermal_filter,
        "rejection_reasons": list(trace.rejection_reasons),
        "design_point_p_total_W": trace.design_point_p_total_W,
        "design_point_tj_ref_C": trace.design_point_tj_ref_C,
        "design_point_required_sink_rth_k_per_w": trace.design_point_required_sink_rth_k_per_w,
        "design_point_bare_reference_valid": trace.design_point_bare_reference_valid,
        "design_point_thermal_feasible": trace.design_point_thermal_feasible,
        "advisory_notes": list(trace.advisory_notes),
        "ranking_score": trace.ranking_score,
        "ranking_notes": list(trace.ranking_notes),
    }


def _resolve_scheme_variants(library_filter: SemiconductorLibraryFilter) -> tuple[tuple[str, str, int], ...]:
    if library_filter.device_type == "IGBT":
        return (_SCHEME_VARIANTS[0],)
    return _SCHEME_VARIANTS


def _build_selected_device_metadata(
    scheme: SemiconductorSchemeResult,
) -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    vendors: dict[str, str] = {}
    device_types: dict[str, str] = {}
    structures: dict[str, str] = {}
    package_levels: dict[str, str] = {}
    internal_topologies: dict[str, str] = {}
    diode_subtypes: dict[str, str] = {}
    module_group_ids: dict[str, str] = {}
    module_section_roles: dict[str, str] = {}
    paired_switches: dict[str, str] = {}
    paired_diodes: dict[str, str] = {}
    thermal_sources: dict[str, str] = {}
    diode_binding_policies: dict[str, str] = {}
    diode_bound_to_roles: dict[str, str] = {}
    packages: dict[str, str] = {}
    for role_result in scheme.role_results:
        if role_result.selected_part_number is None:
            continue
        if role_result.vendor:
            vendors[role_result.role] = role_result.vendor
        if role_result.device_type:
            device_types[role_result.role] = role_result.device_type
        if role_result.device_structure_type:
            structures[role_result.role] = role_result.device_structure_type
        if role_result.package_level:
            package_levels[role_result.role] = role_result.package_level
        if role_result.module_internal_topology:
            internal_topologies[role_result.role] = role_result.module_internal_topology
        if role_result.diode_subtype:
            diode_subtypes[role_result.role] = role_result.diode_subtype
        if role_result.module_group_id:
            module_group_ids[role_result.role] = role_result.module_group_id
        if role_result.module_section_role:
            module_section_roles[role_result.role] = role_result.module_section_role
        if role_result.paired_switch_part_number:
            paired_switches[role_result.role] = role_result.paired_switch_part_number
        if role_result.paired_diode_part_number:
            paired_diodes[role_result.role] = role_result.paired_diode_part_number
        if role_result.thermal_source:
            thermal_sources[role_result.role] = role_result.thermal_source
        if role_result.diode_binding_policy:
            diode_binding_policies[role_result.role] = role_result.diode_binding_policy
        if role_result.bound_to_role:
            diode_bound_to_roles[role_result.role] = role_result.bound_to_role
        if role_result.package:
            packages[role_result.role] = role_result.package
    return (
        vendors,
        device_types,
        structures,
        package_levels,
        internal_topologies,
        diode_subtypes,
        module_group_ids,
        module_section_roles,
        paired_switches,
        paired_diodes,
        thermal_sources,
        diode_binding_policies,
        diode_bound_to_roles,
        packages,
    )


def _empty_rejection_breakdown(*, after_library_prefilter: int = 0, role_incompatible: int = 0) -> dict[str, int]:
    return {
        "after_library_prefilter": after_library_prefilter,
        "role_incompatible": role_incompatible,
        "after_role_filter": max(after_library_prefilter - role_incompatible, 0),
        "rejected_voltage": 0,
        "rejected_continuous_current": 0,
        "rejected_pulse_current": 0,
        "rejected_thermal": 0,
        "passed_hard_filters": 0,
    }


def _build_rejection_breakdown(
    candidate_traces: list[dict[str, object]],
    *,
    after_library_prefilter: int | None = None,
    role_incompatible: int = 0,
) -> dict[str, int]:
    breakdown = _empty_rejection_breakdown(
        after_library_prefilter=len(candidate_traces) if after_library_prefilter is None else after_library_prefilter,
        role_incompatible=role_incompatible,
    )
    breakdown["after_role_filter"] = len(candidate_traces)
    for trace in candidate_traces:
        if not bool(trace.get("passed_voltage_filter")):
            breakdown["rejected_voltage"] += 1
        if bool(trace.get("passed_voltage_filter")) and not bool(trace.get("passed_continuous_current_filter")):
            breakdown["rejected_continuous_current"] += 1
        if bool(trace.get("passed_voltage_filter")) and not bool(trace.get("passed_pulse_current_filter")):
            breakdown["rejected_pulse_current"] += 1
        if bool(trace.get("passed_voltage_filter")) and bool(trace.get("passed_current_filter")) and not bool(trace.get("passed_thermal_filter")):
            breakdown["rejected_thermal"] += 1
        if bool(trace.get("passed_voltage_filter")) and bool(trace.get("passed_current_filter")) and bool(trace.get("passed_thermal_filter")):
            breakdown["passed_hard_filters"] += 1
    return breakdown


def _trace_closeness_key(trace: dict[str, object]) -> tuple[float, float, float]:
    if bool(trace.get("passed_voltage_filter")) and bool(trace.get("passed_current_filter")) and not bool(trace.get("passed_thermal_filter")):
        required_sink = trace.get("design_point_required_sink_rth_k_per_w")
        required_sink_value = float(required_sink) if isinstance(required_sink, (int, float)) else float("-inf")
        return (3.0, required_sink_value, -float(trace.get("design_point_p_total_W") or 0.0))
    if bool(trace.get("passed_voltage_filter")) and not bool(trace.get("passed_current_filter")):
        continuous_margin = float(trace.get("candidate_continuous_current_rating_A") or 0.0) - float(trace.get("required_continuous_current_A") or 0.0)
        pulse_margin = float(trace.get("candidate_pulse_current_rating_A") or 0.0) - float(trace.get("required_pulse_current_A") or 0.0)
        return (2.0, max(continuous_margin, pulse_margin), 0.0)
    voltage_margin = float(trace.get("candidate_voltage_rating_V") or 0.0) - float(trace.get("required_voltage_rating_V") or 0.0)
    return (1.0, voltage_margin, 0.0)


def _select_closest_rejected_candidates(candidate_traces: list[dict[str, object]], *, limit: int = 5) -> list[dict[str, object]]:
    rejected = [
        trace
        for trace in candidate_traces
        if not (bool(trace.get("passed_voltage_filter")) and bool(trace.get("passed_current_filter")) and bool(trace.get("passed_thermal_filter")))
    ]
    rejected.sort(key=_trace_closeness_key, reverse=True)
    return rejected[:limit]


def _build_rejection_breakdown_notes(
    *,
    label: str,
    role: str,
    breakdown: dict[str, int],
    closest_rejected: list[dict[str, object]],
) -> list[str]:
    notes = [
        (
            f"{label} {role}: rejection breakdown after library prefilter = {breakdown['after_library_prefilter']}, "
            f"role-incompatible rejects = {breakdown.get('role_incompatible', 0)}, "
            f"after role filter = {breakdown.get('after_role_filter', 0)}, "
            f"voltage rejects = {breakdown['rejected_voltage']}, "
            f"continuous-current rejects = {breakdown['rejected_continuous_current']}, "
            f"pulse-current rejects = {breakdown['rejected_pulse_current']}, "
            f"thermal rejects = {breakdown['rejected_thermal']}."
        )
    ]
    for trace in closest_rejected:
        reasons = "; ".join(str(reason) for reason in trace.get("rejection_reasons", [])) or "unspecified rejection"
        notes.append(
            f"{label} {role}: closest rejected candidate {trace['candidate_part_number']} ({trace.get('candidate_package', '-')}) -> {reasons}."
        )
    return notes


def run_device_operating_point_refresh(
    report: DesignReport,
    plugin: TopologyPlugin | None = None,
) -> DesignReport:
    """Reevaluate semiconductor losses at the current operating point without reselection."""

    device_result = report.device
    if report.candidate is None or report.stress is None:
        if device_result is None:
            return report
        return replace(
            report,
            device=replace(
                device_result,
                current_operating_losses={},
                current_operating_summary=None,
                current_operating_point_key=None,
                notes=[
                    *device_result.notes,
                    "Current semiconductor operating-point refresh was skipped because no candidate or stress result was available.",
                ],
            ),
        )

    if device_result is None or (not device_result.selected_devices and not device_result.design_point_losses):
        report = run_device_pipeline(report, plugin=plugin)
        device_result = report.device
        if device_result is None:
            return report

    current_case = build_current_operating_switch_stress_case(report, plugin=plugin)
    if current_case is None:
        return replace(
            report,
            device=replace(
                device_result,
                current_operating_losses={},
                current_operating_summary=None,
                current_operating_point_key=None,
            ),
        )

    active_scheme = _find_active_scheme(device_result)
    if device_result.scheme_results and active_scheme is None:
        notes = list(device_result.notes)
        refresh_note = "Current semiconductor operating-point refresh skipped because no complete semiconductor scheme is active."
        if refresh_note not in notes:
            notes.append(refresh_note)
        return replace(
            report,
            device=replace(
                device_result,
                current_operating_losses={},
                current_operating_summary=None,
                current_operating_point_key=current_case.case_id,
                notes=notes,
            ),
        )
    if active_scheme is not None and not active_scheme.complete:
        reason = active_scheme.incomplete_reason or "missing selected semiconductor role(s)."
        notes = list(device_result.notes)
        refresh_note = (
            "Current semiconductor operating-point refresh skipped because the active semiconductor scheme is incomplete: "
            f"{reason}"
        )
        if refresh_note not in notes:
            notes.append(refresh_note)
        return replace(
            report,
            device=replace(
                device_result,
                current_operating_losses={},
                current_operating_summary=None,
                current_operating_point_key=current_case.case_id,
                notes=notes,
            ),
        )

    registry = build_default_semiconductor_registry()
    design_point_loss_by_role = _role_loss_map(device_result.design_point_losses or device_result.evaluated_losses)
    evaluation_devices_by_role = _resolve_devices_by_role(
        device_result=device_result,
        registry=registry,
        design_point_loss_by_role=design_point_loss_by_role,
    )

    current_operating_losses: dict[str, DeviceLossResult] = {}
    active_parallel_count = max(int(getattr(device_result, "active_parallel_count", 1) or 1), 1)
    for stress in current_case.stresses:
        device = evaluation_devices_by_role.get(stress.role)
        if device is None:
            continue
        scaled_stress = scale_switch_stress_for_parallel(stress, active_parallel_count)
        current_loss = _evaluate_role_loss(device, report, scaled_stress, current_case.operating_point)
        design_reference = design_point_loss_by_role.get(stress.role)
        if design_reference is not None:
            current_loss = _apply_design_sink_reference(current_loss, design_reference)
        current_operating_losses[f"{current_case.case_id}:{stress.role}"] = current_loss

    notes = list(device_result.notes)
    refresh_note = "Semiconductor operating-point refresh reused the design-point device choice and sink sizing."
    if refresh_note not in notes:
        notes.append(refresh_note)

    refreshed_device_result = replace(
        device_result,
        current_operating_losses=current_operating_losses,
        current_operating_summary=current_case.notes[0] if current_case.notes else current_case.label,
        current_operating_point_key=current_case.case_id,
        notes=notes,
    )
    return replace(report, device=refreshed_device_result)


def _evaluate_role_loss(device, report: DesignReport, stress: SwitchStress, operating_point=None) -> DeviceLossResult:
    if report.spec.topology_id == "single_phase_full_bridge_inverter" and stress.role == "main_switch":
        segmented = evaluate_inverter_segmented_switch_loss(
            device,
            report,
            stress,
            operating_point=operating_point,
        )
        return segmented.per_switch_loss
    if report.spec.topology_id == _LLC_SR_TOPOLOGY_ID and stress.role == "secondary_sync_switch":
        return _evaluate_llc_sr_secondary_sync_switch_loss(device, stress)
    if report.spec.topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID and stress.role == "totem_pole_lf_switch":
        return _evaluate_totem_pole_lf_switch_loss(device, stress)
    return _evaluate_switch_loss_for_context(device, stress, report=report, method="accurate")


def _evaluate_conduction_only_switch_loss(
    device,
    stress: SwitchStress,
    *,
    method: str,
    note_prefix: str,
) -> DeviceLossResult:
    ambient_temp_c = stress.ambient_temp_C if stress.ambient_temp_C is not None else 25.0
    junction_temp_c = 75.0
    p_cond_w = 0.0
    thermal_reference = estimate_reference_junction_temperature(
        p_total_w=0.0,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_ja_k_per_w=device.static.rth_ja_K_per_W,
        ambient_temp_c=ambient_temp_c,
        case_temp_c=stress.case_temp_C,
    )
    for _ in range(8):
        rds_on_ohm = _interpolate_sr_rds_on(device, junction_temp_c)
        p_cond_w = stress.i_rms_A * stress.i_rms_A * rds_on_ohm
        thermal_reference = estimate_reference_junction_temperature(
            p_total_w=p_cond_w,
            rth_jc_k_per_w=device.static.rth_jc_K_per_W,
            rth_ja_k_per_w=device.static.rth_ja_K_per_W,
            ambient_temp_c=ambient_temp_c,
            case_temp_c=stress.case_temp_C,
        )
        updated_junction_temp_c = thermal_reference.tj_est_c
        if abs(updated_junction_temp_c - junction_temp_c) < 0.25:
            junction_temp_c = updated_junction_temp_c
            break
        junction_temp_c = updated_junction_temp_c

    target_junction_temp_c = (
        stress.target_junction_temp_C
        if stress.target_junction_temp_C is not None
        else device.static.tj_max_C
    )
    interface_stack = resolve_thermal_interface_stack(device, stress)
    sink_requirement = required_sink_thermal_resistance(
        p_total_w=p_cond_w,
        ambient_temp_c=ambient_temp_c,
        target_junction_temp_c=target_junction_temp_c,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_cs_k_per_w=interface_stack.total_rth_k_per_w,
        cooling_mode=DEFAULT_COOLING_MODE,
    )
    thermal_design_notes = summarize_semiconductor_thermal_design(
        reference_estimate=thermal_reference,
        sink_requirement=sink_requirement,
        datasheet_tj_max_c=device.static.tj_max_C,
    )
    thermal_design_notes.extend(_interface_note_lines(interface_stack))
    warnings = list(thermal_reference.warnings)
    warnings.extend(warning for warning in sink_requirement.warnings if warning not in warnings)
    warnings.extend(warning for warning in interface_stack.warnings if warning not in warnings)
    bare_reference_valid = junction_temp_c <= device.static.tj_max_C
    if not bare_reference_valid:
        warnings.append(
            f"Estimated junction temperature {junction_temp_c:.3f} C exceeds datasheet Tj,max {device.static.tj_max_C:.3f} C."
        )
    thermal_design_notes.append(
        f"{note_prefix} first-pass loss uses conduction only: I_rms^2 * Rds(on)."
    )
    thermal_design_notes.append(
        f"{note_prefix} turn-on, turn-off, gate, and output-capacitance losses are intentionally omitted."
    )
    return DeviceLossResult(
        part_number=device.part_number,
        role=stress.role,
        mode=stress.mode,
        p_cond_W=p_cond_w,
        p_sw_on_W=0.0,
        p_sw_off_W=0.0,
        p_rr_W=0.0,
        p_eoss_W=0.0,
        p_gate_W=0.0,
        p_total_W=p_cond_w,
        tj_est_C=junction_temp_c,
        tj_est_method=thermal_reference.method,
        reference_thermal_warnings=list(thermal_reference.warnings),
        bare_reference_valid=bare_reference_valid,
        target_junction_temp_c=target_junction_temp_c,
        required_total_rth_k_per_w=sink_requirement.required_total_rth_k_per_w,
        required_sink_rth_k_per_w=sink_requirement.required_sink_rth_k_per_w,
        estimated_sink_volume_cm3=sink_requirement.estimated_sink_volume_cm3,
        sink_volume_model=sink_requirement.sink_volume_model,
        cooling_mode_assumed=sink_requirement.cooling_mode_assumed,
        thermal_feasible=sink_requirement.feasible,
        thermal_design_notes=_append_unique_list(thermal_design_notes),
        thermal_source=thermal_reference.method,
        reference_temperature_label=thermal_reference.label,
        sink_requirement_label=sink_requirement.sink_requirement_label,
        sink_volume_estimate_label=sink_requirement.sink_volume_estimate_label,
        sink_estimate_model_label=sink_requirement.sink_estimate_model_label,
        thermal_interpretation_label=sink_requirement.thermal_interpretation_label,
        interface_model_name=interface_stack.model_name,
        interface_contact_area_mm2=interface_stack.contact_area_mm2,
        interface_rth_cs_k_per_w=interface_stack.total_rth_k_per_w,
        interface_layer_summary=interface_stack.layer_summary,
        interface_electrical_insulation=interface_stack.electrical_insulation,
        interface_source=interface_stack.source,
        interface_notes=list(interface_stack.notes),
        interface_warnings=list(interface_stack.warnings),
        warnings=_append_unique_list(warnings),
        method=method,
    )


def _evaluate_totem_pole_lf_switch_loss(device, stress: SwitchStress) -> DeviceLossResult:
    """Evaluate Totem-Pole line-frequency switch first-pass conduction loss only."""

    return _evaluate_conduction_only_switch_loss(
        device,
        stress,
        method="totem_pole_lf_conduction_only",
        note_prefix="Totem-Pole line-frequency switch",
    )


def _evaluate_llc_sr_secondary_sync_switch_loss(device, stress: SwitchStress) -> DeviceLossResult:
    """Evaluate LLC SR secondary switch first-pass conduction loss only."""

    return _evaluate_conduction_only_switch_loss(
        device,
        stress,
        method="llc_sr_conduction_only",
        note_prefix="LLC SR secondary_sync_switch",
    )


def _interpolate_sr_rds_on(device, junction_temp_c: float) -> float:
    bounded_temp_c = max(25.0, min(float(junction_temp_c), 150.0))
    temp_ratio = (bounded_temp_c - 25.0) / 125.0
    return float(device.static.rds_on_typ_25C_Ohm) + temp_ratio * (
        float(device.static.rds_on_typ_150C_Ohm) - float(device.static.rds_on_typ_25C_Ohm)
    )


def _interface_note_lines(interface_stack) -> list[str]:
    lines = [
        (
            "Thermal interface: "
            f"model={interface_stack.model_name}, "
            f"Rth_cs={interface_stack.total_rth_k_per_w:.6g} K/W, "
            f"contact_area={_fmt_optional_float(interface_stack.contact_area_mm2)} mm^2, "
            f"insulated={'yes' if interface_stack.electrical_insulation else 'no'}."
        )
    ]
    if interface_stack.layer_summary != "-":
        lines.append(f"Thermal interface layers: {interface_stack.layer_summary}.")
    lines.extend(interface_stack.notes)
    lines.extend(interface_stack.warnings)
    return _append_unique_list(lines)


def _append_unique_list(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped


def _find_active_scheme(device_result: DeviceSelectionResult) -> SemiconductorSchemeResult | None:
    active_scheme_id = device_result.active_scheme_id or device_result.recommended_scheme_id
    for scheme in device_result.scheme_results:
        if scheme.scheme_id == active_scheme_id:
            return scheme
    return None


def _role_loss_map(losses: dict[str, DeviceLossResult]) -> dict[str, DeviceLossResult]:
    role_map: dict[str, DeviceLossResult] = {}
    for loss_result in losses.values():
        role_map.setdefault(loss_result.role, loss_result)
    return role_map


def _resolve_devices_by_role(*, device_result: DeviceSelectionResult, registry, design_point_loss_by_role: dict[str, DeviceLossResult]):
    devices_by_role = {}
    for role, part_number in device_result.selected_devices.items():
        devices_by_role[role] = registry.get_device(part_number)
    for role, loss_result in design_point_loss_by_role.items():
        devices_by_role.setdefault(role, registry.get_device(loss_result.part_number))
    return devices_by_role


def _apply_design_sink_reference(current_loss: DeviceLossResult, design_reference: DeviceLossResult) -> DeviceLossResult:
    return replace(
        current_loss,
        target_junction_temp_c=design_reference.target_junction_temp_c,
        required_total_rth_k_per_w=design_reference.required_total_rth_k_per_w,
        required_sink_rth_k_per_w=design_reference.required_sink_rth_k_per_w,
        estimated_sink_volume_cm3=design_reference.estimated_sink_volume_cm3,
        sink_volume_model=design_reference.sink_volume_model,
        cooling_mode_assumed=design_reference.cooling_mode_assumed,
        thermal_feasible=design_reference.thermal_feasible,
        thermal_source=current_loss.thermal_source or design_reference.thermal_source,
        sink_requirement_label=design_reference.sink_requirement_label,
        sink_volume_estimate_label=design_reference.sink_volume_estimate_label,
        sink_estimate_model_label=design_reference.sink_estimate_model_label,
        thermal_interpretation_label=design_reference.thermal_interpretation_label,
        interface_model_name=design_reference.interface_model_name,
        interface_contact_area_mm2=design_reference.interface_contact_area_mm2,
        interface_rth_cs_k_per_w=design_reference.interface_rth_cs_k_per_w,
        interface_layer_summary=design_reference.interface_layer_summary,
        interface_electrical_insulation=design_reference.interface_electrical_insulation,
        interface_source=design_reference.interface_source,
        interface_notes=list(design_reference.interface_notes),
        interface_warnings=list(design_reference.interface_warnings),
    )


def run_scheme_pipeline(*args, **kwargs):
    """Compatibility shim for the former scheme-stage API."""
    from ..models.pipeline import DeviceCandidateSet, SchemePipelineResult

    if len(args) < 3:
        raise ValueError("run_scheme_pipeline expects core_design, waveform_set, and stress_report.")
    core_design, waveform_set, stress_report = args[:3]
    strategy = kwargs.get("strategy", "default")
    return SchemePipelineResult(
        core_design=core_design,
        waveform_set=waveform_set,
        stress_report=stress_report,
        device_candidates=DeviceCandidateSet(notes=["Legacy scheme pipeline is deprecated."]),
        ranked_schemes=[],
        notes=[f"Placeholder legacy scheme pipeline invoked with strategy={strategy}."],
    )
