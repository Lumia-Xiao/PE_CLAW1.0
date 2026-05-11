"""Device-stage runtime orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import NamedTuple

from ..engines.devices.loss_evaluator import evaluate_switch_loss
from ..engines.devices.selector import merge_switch_stresses, select_switch_device_with_audit
from ..engines.devices.filters import allowed_device_types_for_role, is_structure_compatible_with_role, matches_semiconductor_category
from ..engines.devices.stress_adapter import (
    build_current_operating_switch_stress_case,
    build_design_point_switch_stress_cases,
)
from ..engines.devices.thermal_backsolve import (
    DEFAULT_COOLING_MODE,
    estimate_sink_volume,
)
from ..libraries.semiconductors.metadata import (
    DIODE_BINDING_POLICY_INPUT_KEY,
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY,
    SYNC_SWITCH_CATEGORY_INPUT_KEY,
    INTERNAL_MODULE_DIODE_CATEGORY,
    SemiconductorLibraryFilter,
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

_SCHEME_VARIANTS: tuple[tuple[str, str, int], ...] = (
    ("single", "Single Device", 1),
    ("parallel_2", "2 Devices in Parallel", 2),
    ("parallel_3", "3 Devices in Parallel", 3),
)


class _SchemeSelectionContext(NamedTuple):
    role: str
    case_id: str
    per_device_loss: DeviceLossResult
    total_loss_w: float
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
    if normalized_role == "sync_switch":
        return metadata.get(SYNC_SWITCH_CATEGORY_INPUT_KEY)
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
            label=label,
            parallel_count=parallel_count,
            library_filter=library_filter,
            topology_id=report.spec.topology_id,
            spec_metadata=report.spec.metadata,
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
    return replace(report, device=device_result)


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
        role_source_candidates = switch_candidates
        diode_binding_policy = str(spec_metadata.get(DIODE_BINDING_POLICY_INPUT_KEY, "auto"))
        bound_to_role: str | None = None
        if _is_rectifier_diode_role(role) and diode_binding_policy in {"auto", "internal_module_diode"}:
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
        role_candidates, module_diode_rejection_notes = _filter_unavailable_module_bound_switches(
            role_candidates,
            role,
            topology_id,
        )
        role_incompatible_count += len(module_diode_rejection_notes)
        role_filter_message = (
            f"{label} {role}: role-compatible filter allows {_format_allowed_device_types(allowed_types)}; "
            f"{role_incompatible_count} of {len(role_source_candidates)} library-filtered candidates were removed; "
            f"category={role_category or 'legacy'}."
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
        selected_device, ranked_candidates, role_notes, audit = select_switch_device_with_audit(role_candidates, selection_stress)
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
                loss_result = evaluate_switch_loss(evaluated_device, scaled_stress, method="accurate")
                key = f"{case.case_id}:{role}"
                per_device_design_point_losses[key] = loss_result
                total_context = _build_scheme_selection_context(
                    role=role,
                    case_id=case.case_id,
                    device=evaluated_device,
                    per_device_loss=loss_result,
                    scaled_stress=scaled_stress,
                    parallel_count=parallel_count,
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
) -> _SchemeSelectionContext:
    total_loss_w = parallel_count * per_device_loss.p_total_W
    sink_summary = _estimate_parallel_scheme_sink(
        per_device_loss=per_device_loss,
        scaled_stress=scaled_stress,
        parallel_count=parallel_count,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
    )
    return _SchemeSelectionContext(
        role=role,
        case_id=case_id,
        per_device_loss=per_device_loss,
        total_loss_w=total_loss_w,
        sink_volume_cm3=sink_summary["sink_volume_cm3"],
        sink_model_label=sink_summary["sink_model_label"],
        sink_requirement_label=sink_summary["sink_requirement_label"],
        thermal_feasible=sink_summary["thermal_feasible"],
    )


def _estimate_parallel_scheme_sink(
    *,
    per_device_loss: DeviceLossResult,
    scaled_stress: SwitchStress,
    parallel_count: int,
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

    total_loss_w = parallel_count * per_device_loss.p_total_W
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
        target_junction_feasible=primary_context.thermal_feasible,
        sink_volume_cm3=primary_context.sink_volume_cm3,
        sink_model_label=primary_context.sink_model_label,
        sink_requirement_label=primary_context.sink_requirement_label,
        notes=[
            f"Primary case: {primary_context.case_id}.",
            audit.summary,
        ],
    )


def _build_scheme_comparison_notes(scheme_results: tuple[SemiconductorSchemeResult, ...]) -> list[str]:
    notes: list[str] = []
    for scheme in scheme_results:
        notes.append(
            f"{scheme.label}: total design-point semiconductor loss = "
            f"{scheme.total_scheme_loss_w:.6g} W across {scheme.parallel_count} device(s) per switch role."
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
        current_loss = evaluate_switch_loss(device, scaled_stress, method="accurate")
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
