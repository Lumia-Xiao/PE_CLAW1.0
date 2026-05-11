"""Semiconductor geometry pipeline."""

from __future__ import annotations

from dataclasses import replace

from ..libraries.semiconductors.registry import build_default_semiconductor_registry
from ..libraries.semiconductors.topology_roles import (
    get_required_semiconductor_roles_for_topology,
    get_semiconductor_role_spec,
    topology_role_note,
)
from ..models.design_report import DesignReport
from ..models.device_loss import DeviceLossResult
from ..models.device_result import DeviceSelectionResult, SemiconductorRoleSchemeResult, SemiconductorSchemeResult
from ..models.semiconductor_geometry_result import (
    SemiconductorGeometryResult,
    SemiconductorGeometryRoleLayout,
    SemiconductorGeometryTarget,
)
from ..visualization.semiconductors.layout_builder import build_semiconductor_geometry_layout

_SHARED_SCALE_AVAILABLE_PANEL_WIDTH_UNITS = 1.0
_SHARED_SCALE_AVAILABLE_PANEL_HEIGHT_UNITS = 1.0
_PANEL_MARGIN_MM = 14.0
_INFO_BAND_HEIGHT_MM = 34.0
_ROLE_GAP_MM = 8.0


def run_semiconductor_geometry_pipeline(report: DesignReport) -> DesignReport:
    """Attach comparison-ready semiconductor package and heatsink geometry artifacts."""

    device_result = report.device
    if device_result is None:
        return replace(
            report,
            semiconductor_geometry=SemiconductorGeometryResult(
                summary="Semiconductor geometry is unavailable because the device stage has not run.",
                placeholder_message="Run device selection first to view semiconductor geometry.",
            ),
        )

    scheme_results = device_result.scheme_results
    if not scheme_results:
        design_losses = device_result.design_point_losses or device_result.evaluated_losses
        if not device_result.selected_devices and not design_losses:
            return replace(
                report,
                semiconductor_geometry=SemiconductorGeometryResult(
                    summary="Semiconductor geometry is unavailable because no device was selected.",
                    placeholder_message="No selected semiconductor is available for geometry display.",
                    notes=device_result.notes,
                ),
            )
        registry = build_default_semiconductor_registry()
        target = _build_legacy_single_target(
            registry=registry,
            device_result=device_result,
            topology_id=report.spec.topology_id,
        )
        targets = _apply_shared_physical_scale((target,))
        target = targets[0]
        return replace(
            report,
            semiconductor_geometry=SemiconductorGeometryResult(
                summary="Semiconductor geometry prepared from the legacy single-scheme device result.",
                part_number=target.part_number,
                package=target.package,
                normalized_package=target.normalized_package,
                canonical_package=target.canonical_package,
                renderer_template_id=target.renderer_template_id,
                package_fallback_warning=target.package_fallback_warning,
                role=target.role,
                case_id=target.case_id,
                sink_volume_cm3=target.sink_volume_cm3,
                sink_model_label=target.sink_model_label,
                estimated_sink_dims_mm=target.estimated_sink_dims_mm,
                layout=target.layout,
                targets=targets,
                global_mm_to_unit=target.global_mm_to_unit,
                panel_mm_bbox=target.panel_mm_bbox,
                rendered_unit_bbox=target.rendered_unit_bbox,
                recommended_scheme_id="single",
                notes=target.notes,
                placeholder_message=target.error_message,
            ),
        )

    registry = build_default_semiconductor_registry()
    targets = tuple(
        _build_geometry_target(
            registry=registry,
            topology_id=report.spec.topology_id,
            scheme=scheme,
        )
        for scheme in scheme_results
    )
    targets = _apply_shared_physical_scale(targets)
    primary_target = next(
        (target for target in targets if target.scheme_id == device_result.recommended_scheme_id),
        next((target for target in targets if target.scheme_id == "single"), targets[0]),
    )
    notes = [
        "Semiconductor geometry comparison uses one shared sink per parallel scheme.",
        "Each panel shows all semiconductor roles selected for that topology and scheme.",
    ]
    topology_note = topology_role_note(report.spec.topology_id)
    if topology_note:
        notes.append(topology_note)
    for target in targets:
        notes.extend(target.notes[:3])

    return replace(
        report,
        semiconductor_geometry=SemiconductorGeometryResult(
            summary=(
                "Semiconductor geometry comparison prepared for the single, 2-parallel, and 3-parallel "
                "device schemes using all selected semiconductor roles for each topology."
            ),
            part_number=primary_target.part_number,
            package=primary_target.package,
            normalized_package=primary_target.normalized_package,
            canonical_package=primary_target.canonical_package,
            renderer_template_id=primary_target.renderer_template_id,
            package_fallback_warning=primary_target.package_fallback_warning,
            role=primary_target.role,
            case_id=primary_target.case_id,
            sink_volume_cm3=primary_target.sink_volume_cm3,
            sink_model_label=primary_target.sink_model_label,
            estimated_sink_dims_mm=primary_target.estimated_sink_dims_mm,
            layout=primary_target.layout,
            targets=targets,
            global_mm_to_unit=primary_target.global_mm_to_unit,
            panel_mm_bbox=primary_target.panel_mm_bbox,
            rendered_unit_bbox=primary_target.rendered_unit_bbox,
            recommended_scheme_id=device_result.recommended_scheme_id,
            notes=notes,
            placeholder_message=None if any(target.layout is not None for target in targets) else "No semiconductor geometry artifact is available.",
        ),
    )


def _build_geometry_target(*, registry, topology_id: str, scheme: SemiconductorSchemeResult) -> SemiconductorGeometryTarget:
    ordered_roles, role_map_note = _resolve_target_roles(topology_id=topology_id, scheme=scheme)
    role_results_by_name = {role_result.role: role_result for role_result in scheme.role_results}
    role_layouts: list[SemiconductorGeometryRoleLayout] = []
    missing_role_messages: list[str] = []

    for role_name in ordered_roles:
        role_result = role_results_by_name.get(role_name)
        if role_result is None:
            missing_role_messages.append(f"Missing selected semiconductor role: {role_name}")
            continue
        role_layout = _build_role_layout(
            registry=registry,
            topology_id=topology_id,
            scheme=scheme,
            role_result=role_result,
        )
        if role_layout.part_number is None:
            missing_role_messages.append(f"Missing selected semiconductor role: {role_name}")
            continue
        role_layouts.append(role_layout)

    if not role_layouts:
        incomplete_message = _format_incomplete_target_message(scheme)
        return SemiconductorGeometryTarget(
            scheme_id=scheme.scheme_id,
            label=scheme.label,
            parallel_count=scheme.parallel_count,
            topology_id=topology_id,
            topology_note=topology_role_note(topology_id),
            error_message=incomplete_message or "No selected semiconductor roles are available for this semiconductor scheme.",
            notes=[*scheme.notes, role_map_note] if role_map_note else list(scheme.notes),
        )

    primary_role_layout = next((role_layout for role_layout in role_layouts if role_layout.layout is not None), role_layouts[0])
    primary_layout = primary_role_layout.layout
    sink_dims_mm = (
        None
        if primary_layout is None or primary_layout.sink_width_mm is None or primary_layout.sink_height_mm is None or primary_layout.sink_depth_mm is None
        else (primary_layout.sink_width_mm, primary_layout.sink_height_mm, primary_layout.sink_depth_mm)
    )
    notes = [
        f"Scheme: {scheme.label}.",
        "Each panel shows all semiconductor roles selected for that topology and scheme.",
    ]
    topology_specific_note = topology_role_note(topology_id)
    if topology_specific_note:
        notes.append(topology_specific_note)
    if role_map_note:
        notes.append(role_map_note)
    incomplete_message = _format_incomplete_target_message(scheme)
    if incomplete_message:
        notes.append(incomplete_message)
    notes.extend(missing_role_messages)
    notes.extend(scheme.notes[:2])
    for role_layout in role_layouts:
        notes.append(
            f"Role {role_layout.role_name}: part={role_layout.part_number or '-'}, package={role_layout.package or '-'}, "
            f"module_group_id={role_layout.module_group_id or '-'}."
        )

    return SemiconductorGeometryTarget(
        scheme_id=scheme.scheme_id,
        label=scheme.label,
        parallel_count=scheme.parallel_count,
        part_number=primary_role_layout.part_number,
        package=primary_role_layout.package,
        normalized_package=None if primary_layout is None else primary_layout.normalized_package,
        canonical_package=None if primary_layout is None else primary_layout.canonical_package,
        renderer_template_id=None if primary_layout is None else primary_layout.renderer_template_id,
        package_fallback_warning=None if primary_layout is None else primary_layout.package_fallback_warning,
        role=primary_role_layout.role_name,
        case_id=primary_role_layout.case_id,
        topology_id=topology_id,
        topology_note=topology_specific_note,
        sink_volume_cm3=None if primary_layout is None else primary_layout.sink_volume_cm3,
        sink_model_label="" if primary_layout is None else primary_layout.sink_model_label,
        estimated_sink_dims_mm=sink_dims_mm,
        layout=primary_layout,
        role_layouts=tuple(role_layouts),
        error_message=(
            incomplete_message
            if incomplete_message
            else "; ".join(missing_role_messages)
            if missing_role_messages
            else None if any(role_layout.layout is not None for role_layout in role_layouts)
            else "No heatsink volume estimate is available for this semiconductor scheme."
        ),
        notes=notes,
    )


def _resolve_target_roles(*, topology_id: str, scheme: SemiconductorSchemeResult) -> tuple[list[str], str | None]:
    if not scheme.complete:
        selected_role_names = [role_result.role for role_result in scheme.role_results if role_result.selected_part_number]
        if selected_role_names:
            return selected_role_names, None
        return [], scheme.incomplete_reason

    declared_specs = get_required_semiconductor_roles_for_topology(topology_id)
    if declared_specs:
        declared_role_names = [spec.role_name for spec in declared_specs]
        available_role_names = [role_result.role for role_result in scheme.role_results if role_result.selected_part_number]
        ordered = list(declared_role_names)
        for role_name in available_role_names:
            if role_name not in ordered:
                ordered.append(role_name)
        return ordered, None

    selected_roles = [role_result.role for role_result in scheme.role_results if role_result.selected_part_number]
    if selected_roles:
        return selected_roles, (
            "Topology-specific semiconductor role map unavailable; displaying all selected semiconductor roles from device result."
        )
    return [], "Topology-specific semiconductor role map unavailable; displaying all selected semiconductor roles from device result."


def _format_incomplete_target_message(scheme: SemiconductorSchemeResult) -> str | None:
    if scheme.complete:
        return None
    reason = scheme.incomplete_reason or "missing selected semiconductor role(s)"
    missing_prefixes = (
        "missing selected semiconductor role: ",
        "missing selected semiconductor roles: ",
        "missing selected semiconductor role(s): ",
    )
    for missing_prefix in missing_prefixes:
        if reason.startswith(missing_prefix):
            missing = reason[len(missing_prefix):]
            return f"{scheme.label} infeasible: missing {missing}"
    return f"{scheme.label} infeasible: {reason}"


def _apply_shared_physical_scale(
    targets: tuple[SemiconductorGeometryTarget, ...],
) -> tuple[SemiconductorGeometryTarget, ...]:
    """Attach one figure-level physical scale to all comparison targets."""

    required_bboxes = [_required_panel_bbox_mm(target) for target in targets]
    max_width_mm = max((bbox[0] for bbox in required_bboxes), default=1.0)
    max_height_mm = max((bbox[1] for bbox in required_bboxes), default=1.0)
    max_width_mm = max(max_width_mm, 1.0)
    max_height_mm = max(max_height_mm, 1.0)
    global_mm_to_unit = min(
        _SHARED_SCALE_AVAILABLE_PANEL_WIDTH_UNITS / max_width_mm,
        _SHARED_SCALE_AVAILABLE_PANEL_HEIGHT_UNITS / max_height_mm,
    )
    panel_mm_bbox = (max_width_mm, max_height_mm)
    rendered_unit_bbox = (
        max_width_mm * global_mm_to_unit,
        max_height_mm * global_mm_to_unit,
    )

    scaled_targets: list[SemiconductorGeometryTarget] = []
    for target in targets:
        sink_width_mm, sink_depth_mm = _target_sink_footprint_size_mm(target)
        scaled_role_layouts = tuple(
            replace(
                role_layout,
                package_body_width_rendered=None
                if role_layout.package_body_width_mm is None
                else role_layout.package_body_width_mm * global_mm_to_unit,
                package_body_height_rendered=None
                if role_layout.package_body_height_mm is None
                else role_layout.package_body_height_mm * global_mm_to_unit,
                rendered_body_width_units=None
                if role_layout.package_body_width_mm is None
                else role_layout.package_body_width_mm * global_mm_to_unit,
                rendered_body_height_units=None
                if role_layout.package_body_height_mm is None
                else role_layout.package_body_height_mm * global_mm_to_unit,
                global_mm_to_unit=global_mm_to_unit,
                package_scale_x=None if role_layout.package_body_width_mm is None else global_mm_to_unit,
                package_scale_y=None if role_layout.package_body_height_mm is None else global_mm_to_unit,
                physical_scale_preserved=True,
                visual_scale_factor=1.0,
                panel_scale_source="global",
            )
            for role_layout in target.role_layouts
        )
        scaled_targets.append(
            replace(
                target,
                role_layouts=scaled_role_layouts,
                global_mm_to_unit=global_mm_to_unit,
                panel_mm_bbox=panel_mm_bbox,
                rendered_unit_bbox=rendered_unit_bbox,
                panel_scale_source="global",
                sink_width_mm=sink_width_mm,
                sink_height_mm=None if target.estimated_sink_dims_mm is None else target.estimated_sink_dims_mm[1],
                sink_depth_mm=sink_depth_mm,
                sink_width_rendered=sink_width_mm * global_mm_to_unit,
                sink_height_rendered=None
                if target.estimated_sink_dims_mm is None
                else target.estimated_sink_dims_mm[1] * global_mm_to_unit,
                sink_depth_rendered=sink_depth_mm * global_mm_to_unit,
                sink_scale_x=global_mm_to_unit,
                sink_scale_y=global_mm_to_unit,
            )
        )
    return tuple(scaled_targets)


def _required_panel_bbox_mm(target: SemiconductorGeometryTarget) -> tuple[float, float]:
    sink_width_mm, sink_depth_mm = _target_sink_footprint_size_mm(target)
    role_width_mm, role_height_mm = _target_role_assembly_bbox_mm(target)
    return (
        max(sink_width_mm, role_width_mm) + (2.0 * _PANEL_MARGIN_MM),
        max(sink_depth_mm, role_height_mm) + _INFO_BAND_HEIGHT_MM + (2.0 * _PANEL_MARGIN_MM),
    )


def _target_sink_footprint_size_mm(target: SemiconductorGeometryTarget) -> tuple[float, float]:
    if target.estimated_sink_dims_mm is not None:
        width_mm, _, depth_mm = target.estimated_sink_dims_mm
        return max(width_mm, 1.0), max(depth_mm, 1.0)
    role_width_mm, role_height_mm = _target_role_assembly_bbox_mm(target)
    return max(role_width_mm + 10.0, 24.0), max(role_height_mm + 10.0, 18.0)


def _target_role_assembly_bbox_mm(target: SemiconductorGeometryTarget) -> tuple[float, float]:
    role_boxes = [_role_assembly_bbox_mm(role_layout) for role_layout in target.role_layouts if role_layout.layout is not None]
    if not role_boxes:
        return (1.0, 1.0)
    count = len(role_boxes)
    family = (target.topology_id or "").casefold()
    if "four_switch_buck_boost_simplified_four_mode" in family and count > 1:
        row_count = 2
        col_count = 2
    elif "three_level_tzcm_fixed_frequency" in family and count > 1:
        row_count = count
        col_count = 1
    elif count == 2:
        row_count = 1
        col_count = 2
    else:
        row_count = 1
        col_count = count
    max_role_width_mm = max(width for width, _ in role_boxes)
    max_role_height_mm = max(height for _, height in role_boxes)
    return (
        (col_count * max_role_width_mm) + (max(col_count - 1, 0) * _ROLE_GAP_MM),
        (row_count * max_role_height_mm) + (max(row_count - 1, 0) * _ROLE_GAP_MM),
    )


def _role_assembly_bbox_mm(role_layout: SemiconductorGeometryRoleLayout) -> tuple[float, float]:
    layout = role_layout.layout
    if layout is None:
        return (1.0, 1.0)
    quantity = max(int(role_layout.quantity or 1), 1)
    package_width_mm = _package_span_width_mm(layout)
    package_height_mm = _package_span_height_mm(layout)
    package_gap_mm = max(3.0, 0.28 * package_width_mm)
    return (
        (quantity * package_width_mm) + (max(quantity - 1, 0) * package_gap_mm),
        package_height_mm,
    )


def _package_span_width_mm(layout) -> float:
    if layout.renderer_template_id in {"hdsop_10_top", "hdsop_16_top", "hdsop_22_top", "dso_20_top"}:
        return layout.package_body_width_mm + (2.0 * layout.lead_length_mm)
    return layout.package_body_width_mm


def _package_span_height_mm(layout) -> float:
    if layout.renderer_template_id in {"hdsop_10_top", "hdsop_16_top", "hdsop_22_top", "dso_20_top"}:
        return layout.package_body_height_mm
    if layout.renderer_template_id in {"tson_8_top", "lson_8_top"}:
        return layout.package_body_height_mm + (2.0 * layout.lead_length_mm)
    if layout.renderer_template_id in {
        "to220_3_tht",
        "to247_2_tht",
        "to247_3_tht",
        "to247_4_tht",
        "to252_3_dpak",
        "to263_7_d2pak",
        "hsof_8_top",
        "lhsof_4_top",
        "thinpak_8x8_top",
    }:
        return layout.package_body_height_mm + layout.lead_length_mm
    return layout.package_body_height_mm


def _build_role_layout(
    *,
    registry,
    topology_id: str | None,
    scheme: SemiconductorSchemeResult,
    role_result: SemiconductorRoleSchemeResult,
) -> SemiconductorGeometryRoleLayout:
    spec = get_semiconductor_role_spec(role_result.role, topology_id=topology_id)
    layout = None
    case_id = None
    notes = list(role_result.notes[:2])
    design_loss_key = _find_design_loss_key(losses=scheme.per_device_design_point_losses, role=role_result.role)
    if role_result.selected_part_number is not None and design_loss_key is not None:
        case_id = design_loss_key.split(":", 1)[0] if ":" in design_loss_key else design_loss_key
        device = registry.get_device(role_result.selected_part_number)
        per_device_loss = scheme.per_device_design_point_losses[design_loss_key]
        layout_loss = replace(
            per_device_loss,
            estimated_sink_volume_cm3=role_result.sink_volume_cm3,
            sink_volume_model=role_result.sink_model_label,
            sink_requirement_label=role_result.sink_requirement_label or per_device_loss.sink_requirement_label,
            thermal_feasible=bool(role_result.target_junction_feasible),
        )
        layout = build_semiconductor_geometry_layout(
            device,
            layout_loss,
            scheme_id=scheme.scheme_id,
            scheme_label=scheme.label,
            parallel_count=scheme.parallel_count,
            case_id=case_id,
        )
    elif role_result.selected_part_number is not None:
        notes.append("No design-point loss result was available for this role; geometry metadata is partial.")
    else:
        notes.append(f"Missing selected semiconductor role: {role_result.role}")

    return SemiconductorGeometryRoleLayout(
        role_name=role_result.role,
        role_label=spec.role_label if spec is not None else role_result.role,
        part_number=role_result.selected_part_number,
        vendor=role_result.vendor,
        selection_device_type=role_result.device_type,
        device_structure_type=role_result.device_structure_type,
        package_level=role_result.package_level,
        module_internal_topology=role_result.module_internal_topology,
        diode_subtype=role_result.diode_subtype,
        package=role_result.package,
        quantity=scheme.parallel_count,
        module_group_id=role_result.module_group_id,
        module_section_role=role_result.module_section_role,
        diode_binding_policy=role_result.diode_binding_policy,
        paired_switch_part_number=role_result.paired_switch_part_number,
        paired_diode_part_number=role_result.paired_diode_part_number,
        thermal_source=role_result.thermal_source,
        per_device_loss_w=role_result.per_device_loss_w,
        role_total_loss_w=role_result.total_loss_w,
        case_id=case_id,
        layout=layout,
        package_body_width_mm=None if layout is None else layout.package_body_width_mm,
        package_body_height_mm=None if layout is None else layout.package_body_height_mm,
        package_name=role_result.package,
        notes=notes,
    )


def _find_design_loss_key(*, losses: dict[str, object], role: str) -> str | None:
    for key, loss_result in losses.items():
        if getattr(loss_result, "role", None) == role:
            return key
    return None


def _build_legacy_single_target(*, registry, device_result: DeviceSelectionResult, topology_id: str) -> SemiconductorGeometryTarget:
    primary_key, primary_loss, geometry_basis = _select_primary_loss_result(device_result)
    case_id = primary_key.split(":", 1)[0] if ":" in primary_key else primary_key
    device = registry.get_device(primary_loss.part_number)
    layout = build_semiconductor_geometry_layout(
        device,
        primary_loss,
        scheme_id="single",
        scheme_label="Single Device",
        parallel_count=1,
        case_id=case_id,
    )
    sink_dims_mm = (
        None
        if layout.sink_width_mm is None or layout.sink_height_mm is None or layout.sink_depth_mm is None
        else (layout.sink_width_mm, layout.sink_height_mm, layout.sink_depth_mm)
    )
    role_layout = SemiconductorGeometryRoleLayout(
        role_name=layout.role,
        role_label=layout.role,
        part_number=layout.part_number,
        package=layout.package,
        quantity=1,
        per_device_loss_w=primary_loss.p_total_W,
        role_total_loss_w=primary_loss.p_total_W,
        case_id=case_id,
        layout=layout,
        package_body_width_mm=layout.package_body_width_mm,
        package_body_height_mm=layout.package_body_height_mm,
        package_name=layout.package,
    )
    notes = [
        f"Geometry basis: {geometry_basis}.",
        "Each panel shows all semiconductor roles selected for that topology and scheme.",
        f"Primary geometry role: {layout.role}.",
        f"Reference operating case: {layout.case_id}.",
        f"Resolved package: {layout.package} -> {layout.canonical_package} ({layout.package_template_key}).",
        f"Renderer template: {layout.renderer_template_id}.",
        *layout.notes,
    ]
    topology_specific_note = topology_role_note(topology_id)
    if topology_specific_note:
        notes.append(topology_specific_note)
    return SemiconductorGeometryTarget(
        scheme_id="single",
        label="Single Device",
        parallel_count=1,
        part_number=layout.part_number,
        package=layout.package,
        normalized_package=layout.normalized_package,
        canonical_package=layout.canonical_package,
        renderer_template_id=layout.renderer_template_id,
        package_fallback_warning=layout.package_fallback_warning,
        role=layout.role,
        case_id=layout.case_id,
        topology_id=topology_id,
        topology_note=topology_specific_note,
        sink_volume_cm3=layout.sink_volume_cm3,
        sink_model_label=layout.sink_model_label,
        estimated_sink_dims_mm=sink_dims_mm,
        layout=layout,
        role_layouts=(role_layout,),
        error_message=None if sink_dims_mm is not None else "No heatsink volume estimate is available for the selected semiconductor.",
        notes=notes,
    )


def _select_primary_loss_result(device_result: DeviceSelectionResult) -> tuple[str, DeviceLossResult, str]:
    design_losses = device_result.design_point_losses or device_result.evaluated_losses
    selected_roles = set(device_result.selected_devices)
    selected_entries = [
        (key, loss_result)
        for key, loss_result in design_losses.items()
        if loss_result.role in selected_roles
    ]
    if selected_entries:
        return (*_rank_loss_entries(selected_entries), "selected-device")

    evaluated_entries = list(design_losses.items())
    if not evaluated_entries:
        raise RuntimeError("Device result has no evaluated losses available for semiconductor geometry.")
    return (*_rank_loss_entries(evaluated_entries), "evaluated-device")


def _rank_loss_entries(entries: list[tuple[str, DeviceLossResult]]) -> tuple[str, DeviceLossResult]:
    if not entries:
        raise RuntimeError("No semiconductor loss entries were provided for geometry ranking.")

    def ranking_key(item: tuple[str, DeviceLossResult]) -> tuple[float, float]:
        _, loss_result = item
        sink_volume = loss_result.estimated_sink_volume_cm3 if loss_result.estimated_sink_volume_cm3 is not None else -1.0
        return (sink_volume, loss_result.p_total_W)

    return max(entries, key=ranking_key)
