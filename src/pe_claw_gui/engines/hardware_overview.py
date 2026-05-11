"""Backend payload builder for the future Hardware Overview page."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..models.capacitor import CapacitorGeometryTarget, CapacitorSelectionEntry, capacitor_series_display_name
from ..models.design_report import DesignReport
from ..models.geometry_result import GeometryTarget, InductorGeometryLayout
from ..models.inductor import FixedInductorDesignCandidate
from ..models.semiconductor_geometry_result import SemiconductorGeometryRoleLayout, SemiconductorGeometryTarget

_GROUP_IDS = ("semiconductor", "inductor", "capacitor")
_OVERVIEW_OUTPUT_DIR = Path("outputs") / "hardware_overview"


@dataclass(frozen=True)
class HardwareOverviewBoundingBox:
    """Physical bounding box in millimeters."""

    width_mm: float | None = None
    height_mm: float | None = None
    depth_mm: float | None = None


@dataclass(frozen=True)
class HardwareOverviewImageRef:
    """Existing or future overview image reference."""

    path: str | None = None
    image_scale_type: str = "unknown"
    recommended_for_overview: bool = False


@dataclass(frozen=True)
class HardwareOverviewChildEntry:
    """Child hardware entry within a top-level overview group."""

    entry_id: str
    display_name: str
    recommended_name: str = ""
    manufacturer: str | None = None
    series: str | None = None
    part_number: str | None = None
    quantity: int | None = None
    volume_cm3: float | None = None
    loss_w: float | None = None
    bounding_box_mm: HardwareOverviewBoundingBox = field(default_factory=HardwareOverviewBoundingBox)
    shape_type: str = "unknown"
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareOverviewComponentGroup:
    """Top-level component group for Hardware Overview."""

    group_id: str
    display_name: str
    status: str = "missing"
    recommended_name: str = ""
    manufacturer: str | None = None
    series: str | None = None
    part_number: str | None = None
    quantity: int | None = None
    volume_cm3: float | None = None
    volume_breakdown_cm3: dict[str, float | None] = field(default_factory=dict)
    loss_w: float | None = None
    image_2d_path_existing: str | None = None
    image_3d_path_existing: str | None = None
    overview_image_2d_path: str | None = None
    overview_image_3d_path: str | None = None
    image_2d: HardwareOverviewImageRef = field(default_factory=HardwareOverviewImageRef)
    image_3d: HardwareOverviewImageRef = field(default_factory=HardwareOverviewImageRef)
    geometry_source: str = "missing"
    bounding_box_mm: HardwareOverviewBoundingBox = field(default_factory=HardwareOverviewBoundingBox)
    shape_type: str = "unknown"
    child_entries: list[HardwareOverviewChildEntry] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareOverviewGlobalScale:
    """Global physical scale metadata for future overview rendering."""

    scale_mode: str = "global_bbox"
    all_components_bbox_mm: dict[str, HardwareOverviewBoundingBox] = field(default_factory=dict)
    max_dimension_mm: float | None = None
    view_padding_fraction: float = 0.12
    unit: str = "mm"
    applies_to: list[str] = field(default_factory=lambda: list(_GROUP_IDS))
    common_2d_axis_limits_mm: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    common_3d_axis_limits_mm: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareIntegratedBox:
    """Integrated layout object box in millimeters."""

    width_mm: float | None = None
    depth_mm: float | None = None
    height_mm: float | None = None


@dataclass(frozen=True)
class HardwareIntegratedPosition:
    """Integrated layout object anchor position in millimeters."""

    x_mm: float = 0.0
    y_mm: float = 0.0
    z_mm: float = 0.0


@dataclass(frozen=True)
class HardwareIntegratedLayoutObject:
    """One physical object in the integrated system-level hardware layout."""

    id: str
    display_name: str
    source_group: str
    recommended_name: str = ""
    manufacturer: str | None = None
    series: str | None = None
    part_number: str | None = None
    shape_type: str = "unknown"
    bbox_mm: HardwareIntegratedBox = field(default_factory=HardwareIntegratedBox)
    footprint_mm: HardwareIntegratedBox = field(default_factory=HardwareIntegratedBox)
    volume_cm3: float | None = None
    loss_w: float | None = None
    preferred_label: str = ""
    layout_position_mm: HardwareIntegratedPosition = field(default_factory=HardwareIntegratedPosition)
    layout_anchor: str = "center_bottom"
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareIntegratedLayoutPayload:
    """Single-coordinate-system hardware overview layout metadata."""

    unit: str = "mm"
    layout_mode: str = "engineering_overview_not_pcb"
    groups: list[HardwareIntegratedLayoutObject] = field(default_factory=list)
    global_bbox_mm: HardwareIntegratedBox = field(default_factory=HardwareIntegratedBox)
    group_spacing_mm: float | None = None
    capacitor_internal_spacing_mm: float | None = None
    common_2d_axis_limits_mm: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    common_3d_axis_limits_mm: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareOverviewPayload:
    """Complete backend payload for Hardware Overview."""

    component_groups: list[HardwareOverviewComponentGroup]
    global_geometry_scale: HardwareOverviewGlobalScale
    artifact_paths: list[str] = field(default_factory=list)
    overview_artifacts: dict[str, str] = field(default_factory=dict)
    integrated_layout: HardwareIntegratedLayoutPayload | None = None
    integrated_overview_artifacts: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def build_hardware_overview_payload(
    report: DesignReport,
    output_dir: str | Path | None = None,
) -> HardwareOverviewPayload:
    """Build and persist the Hardware Overview backend payload without rerunning design stages."""

    resolved_output_dir = _resolve_output_dir(output_dir)
    groups = [
        _build_semiconductor_group(report),
        _build_inductor_group(report),
        _build_capacitor_group(report),
    ]
    global_scale = _build_global_scale(groups)
    integrated_layout = build_integrated_hardware_layout_from_groups(groups)
    payload = HardwareOverviewPayload(
        component_groups=groups,
        global_geometry_scale=global_scale,
        integrated_layout=integrated_layout,
        notes=[
            "Hardware Overview payload is assembled from existing report results only.",
            "Existing individual-page images are treated as local-scale fallbacks unless generated as overview artifacts.",
            "Integrated hardware overview artifacts are the preferred system-level representation once generated.",
        ],
        warnings=_dedupe_strings([*_payload_warnings(groups), *integrated_layout.warnings]),
    )
    json_path = write_hardware_overview_payload_json(payload, resolved_output_dir)
    return HardwareOverviewPayload(
        component_groups=payload.component_groups,
        global_geometry_scale=payload.global_geometry_scale,
        artifact_paths=[str(json_path)],
        overview_artifacts=payload.overview_artifacts,
        integrated_layout=payload.integrated_layout,
        integrated_overview_artifacts=payload.integrated_overview_artifacts,
        notes=payload.notes,
        warnings=payload.warnings,
    )


def build_and_generate_hardware_overview(
    report: DesignReport,
    output_dir: str | Path | None = None,
) -> HardwareOverviewPayload:
    """Build the overview payload, generate overview artifacts, and persist updated JSON."""

    resolved_output_dir = _resolve_output_dir(output_dir)
    payload = build_hardware_overview_payload(report, resolved_output_dir)
    from ..visualization.hardware_overview import generate_hardware_overview_artifacts

    return generate_hardware_overview_artifacts(payload, resolved_output_dir)


def write_hardware_overview_payload_json(payload: HardwareOverviewPayload, output_dir: str | Path) -> Path:
    """Write a human-readable JSON artifact for the overview payload."""

    path = Path(output_dir) / "hardware_overview_payload.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(payload), indent=2, sort_keys=True), encoding="utf-8")
    return path


def build_integrated_hardware_layout_from_groups(
    groups: list[HardwareOverviewComponentGroup],
    artifact_paths: dict[str, str] | None = None,
) -> HardwareIntegratedLayoutPayload:
    """Build a deterministic system-level hardware layout from available overview groups."""

    objects = _integrated_layout_objects(groups)
    warnings = _integrated_missing_warnings(groups, objects)
    max_major_dimension_mm = max(
        (
            max(
                obj.bbox_mm.width_mm or 0.0,
                obj.bbox_mm.depth_mm or 0.0,
                obj.bbox_mm.height_mm or 0.0,
            )
            for obj in objects
        ),
        default=100.0,
    )
    group_spacing_mm = max(20.0, 0.20 * max_major_dimension_mm)
    capacitor_internal_spacing_mm = max(10.0, 0.10 * max_major_dimension_mm)
    placed = _place_integrated_objects(objects, group_spacing_mm, capacitor_internal_spacing_mm)
    global_bbox = _integrated_global_bbox(placed)
    axis_limits_2d, axis_limits_3d = _integrated_axis_limits(global_bbox)
    if not placed:
        warnings.append("No available hardware objects for integrated overview layout.")
    return HardwareIntegratedLayoutPayload(
        groups=placed,
        global_bbox_mm=global_bbox,
        group_spacing_mm=group_spacing_mm,
        capacitor_internal_spacing_mm=capacitor_internal_spacing_mm,
        common_2d_axis_limits_mm=axis_limits_2d,
        common_3d_axis_limits_mm=axis_limits_3d,
        artifact_paths=dict(artifact_paths or {}),
        notes=[
            "Integrated layout places recommended hardware in one shared coordinate system.",
            "Layout rule, left to right: input capacitor, semiconductor, inductor, output capacitor.",
            "Layout depth rule, back to front: input capacitor, semiconductor, inductor, output capacitor.",
            "This is an engineering overview layout, not a PCB, package, or electrical placement.",
        ],
        warnings=_dedupe_strings(warnings),
    )


def _build_semiconductor_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    if report.device is None:
        return _missing_group("semiconductor", "Semiconductor", "Run Design first to populate semiconductor overview.")

    target = _recommended_semiconductor_target(report)
    if target is None or not target.role_layouts:
        warnings = ["Missing semiconductor geometry; run or refresh design geometry before overview rendering."]
        return HardwareOverviewComponentGroup(
            group_id="semiconductor",
            display_name="Semiconductor",
            status="missing",
            recommended_name=_semiconductor_recommended_name(report),
            loss_w=_resolve_semiconductor_loss_w(report),
            geometry_source="missing",
            notes=["Device selection is available, but semiconductor geometry data is unavailable."],
            warnings=warnings,
        )

    bbox = _semiconductor_bbox(target)
    child_entries = [_semiconductor_child_entry(role_layout) for role_layout in target.role_layouts if role_layout.part_number]
    device_volume_cm3 = sum(value for value in (_semiconductor_role_volume_cm3(role) for role in target.role_layouts) if value is not None)
    heatsink_volume_cm3 = _positive_or_none(target.sink_volume_cm3)
    if heatsink_volume_cm3 is None:
        heatsink_volume_cm3 = _semiconductor_role_sink_volume_cm3(target.role_layouts)
    total_volume_cm3 = (device_volume_cm3 or 0.0) + (heatsink_volume_cm3 or 0.0)
    if total_volume_cm3 <= 0.0:
        total_volume_cm3 = None
    warnings = _bbox_warnings(bbox)
    if heatsink_volume_cm3 is None:
        warnings.append("Semiconductor overview volume excludes heatsink.")
    warnings.append("Existing semiconductor geometry is rendered in-view and not persisted as an overview artifact.")
    primary = next((child for child in child_entries if child.part_number), None)
    return HardwareOverviewComponentGroup(
        group_id="semiconductor",
        display_name="Semiconductor",
        status="available",
        recommended_name=_semiconductor_recommended_name(report),
        manufacturer=primary.manufacturer if primary else None,
        series=primary.series if primary else None,
        part_number=primary.part_number if primary else target.part_number,
        quantity=target.parallel_count,
        volume_cm3=total_volume_cm3,
        volume_breakdown_cm3={
            "device_volume_cm3": device_volume_cm3 if device_volume_cm3 > 0.0 else None,
            "heatsink_volume_cm3": heatsink_volume_cm3,
            "total_volume_cm3": total_volume_cm3,
        },
        loss_w=_resolve_semiconductor_loss_w(report),
        image_2d=_local_image_ref(None),
        image_3d=_local_image_ref(None),
        geometry_source="existing_artifact",
        bounding_box_mm=bbox,
        shape_type="heatsink_plus_device" if heatsink_volume_cm3 is not None else "semiconductor_module",
        child_entries=child_entries,
        metadata={
            "recommended_scheme_id": report.device.recommended_scheme_id,
            "target_scheme_id": target.scheme_id,
            "device_only_volume_cm3": device_volume_cm3 if device_volume_cm3 > 0.0 else None,
            "heatsink_volume_cm3": heatsink_volume_cm3,
            "total_volume_cm3": total_volume_cm3,
        },
        notes=[
            "Semiconductor payload uses the recommended scheme geometry already attached to the design report.",
            "Heatsink volume is included when available because overview size is physical hardware size.",
        ],
        warnings=warnings,
    )


def _integrated_layout_objects(groups: list[HardwareOverviewComponentGroup]) -> list[HardwareIntegratedLayoutObject]:
    by_id = {group.group_id: group for group in groups}
    objects: list[HardwareIntegratedLayoutObject] = []
    semiconductor = by_id.get("semiconductor")
    if semiconductor is not None and _group_available_for_integrated_layout(semiconductor):
        objects.append(_integrated_object_from_group(semiconductor, object_id="semiconductor", display_name="Semiconductor"))
    inductor = by_id.get("inductor")
    if inductor is not None and _group_available_for_integrated_layout(inductor):
        objects.append(_integrated_object_from_group(inductor, object_id="inductor", display_name="Inductor"))
    capacitor = by_id.get("capacitor")
    if capacitor is not None:
        capacitor_children = [child for child in capacitor.child_entries if _bbox_complete(child.bounding_box_mm)]
        for child in capacitor_children:
            if child.entry_id == "input_capacitor":
                objects.append(_integrated_object_from_child(child, "capacitor_input", "Input capacitor"))
            elif child.entry_id == "output_capacitor":
                objects.append(_integrated_object_from_child(child, "capacitor_output", "Output capacitor"))
        if not capacitor_children and _group_available_for_integrated_layout(capacitor):
            objects.append(_integrated_object_from_group(capacitor, object_id="capacitor", display_name="Capacitors"))
    return objects


def _group_available_for_integrated_layout(group: HardwareOverviewComponentGroup) -> bool:
    return group.status != "missing" and _bbox_complete(group.bounding_box_mm)


def _integrated_object_from_group(
    group: HardwareOverviewComponentGroup,
    *,
    object_id: str,
    display_name: str,
) -> HardwareIntegratedLayoutObject:
    bbox = _box_from_overview_bbox(group.bounding_box_mm)
    return HardwareIntegratedLayoutObject(
        id=object_id,
        display_name=display_name,
        source_group=group.group_id,
        recommended_name=group.recommended_name,
        manufacturer=group.manufacturer,
        series=group.series,
        part_number=group.part_number,
        shape_type=group.shape_type,
        bbox_mm=bbox,
        footprint_mm=HardwareIntegratedBox(width_mm=bbox.width_mm, depth_mm=bbox.depth_mm),
        volume_cm3=group.volume_cm3,
        loss_w=group.loss_w,
        preferred_label=display_name,
        notes=list(group.notes),
        warnings=list(group.warnings),
    )


def _integrated_object_from_child(
    child: HardwareOverviewChildEntry,
    object_id: str,
    display_name: str,
) -> HardwareIntegratedLayoutObject:
    bbox = _box_from_overview_bbox(child.bounding_box_mm)
    return HardwareIntegratedLayoutObject(
        id=object_id,
        display_name=display_name,
        source_group="capacitor",
        recommended_name=child.recommended_name,
        manufacturer=child.manufacturer,
        series=child.series,
        part_number=child.part_number,
        shape_type=child.shape_type,
        bbox_mm=bbox,
        footprint_mm=HardwareIntegratedBox(width_mm=bbox.width_mm, depth_mm=bbox.depth_mm),
        volume_cm3=child.volume_cm3,
        loss_w=child.loss_w,
        preferred_label=display_name,
        notes=list(child.notes),
        warnings=list(child.warnings),
    )


def _box_from_overview_bbox(bbox: HardwareOverviewBoundingBox) -> HardwareIntegratedBox:
    return HardwareIntegratedBox(width_mm=bbox.width_mm, depth_mm=bbox.depth_mm, height_mm=bbox.height_mm)


def _place_integrated_objects(
    objects: list[HardwareIntegratedLayoutObject],
    group_spacing_mm: float,
    capacitor_internal_spacing_mm: float,
) -> list[HardwareIntegratedLayoutObject]:
    by_id = {obj.id: obj for obj in objects}
    ordered_ids = ("capacitor_input", "semiconductor", "inductor", "capacitor_output", "capacitor")
    ordered_objects = [by_id[obj_id] for obj_id in ordered_ids if obj_id in by_id]
    placed: list[HardwareIntegratedLayoutObject] = []
    x_cursor = 0.0
    depth_step_mm = max(6.0, 0.30 * capacitor_internal_spacing_mm)
    depth_offsets = _depth_offsets_for_order(ordered_objects, depth_step_mm)
    for index, obj in enumerate(ordered_objects):
        placed.append(_place_object(obj, x_cursor + 0.5 * _box_width(obj.bbox_mm), depth_offsets.get(obj.id, 0.0)))
        x_cursor += _box_width(obj.bbox_mm)
        if index < len(ordered_objects) - 1:
            x_cursor += group_spacing_mm
    return _center_integrated_layout(placed)


def _depth_offsets_for_order(objects: list[HardwareIntegratedLayoutObject], depth_step_mm: float) -> dict[str, float]:
    if len(objects) <= 1:
        return {obj.id: 0.0 for obj in objects}
    center_index = 0.5 * (len(objects) - 1)
    return {obj.id: (index - center_index) * depth_step_mm for index, obj in enumerate(objects)}


def _place_object(obj: HardwareIntegratedLayoutObject, x_mm: float, y_mm: float) -> HardwareIntegratedLayoutObject:
    return HardwareIntegratedLayoutObject(
        id=obj.id,
        display_name=obj.display_name,
        source_group=obj.source_group,
        recommended_name=obj.recommended_name,
        manufacturer=obj.manufacturer,
        series=obj.series,
        part_number=obj.part_number,
        shape_type=obj.shape_type,
        bbox_mm=obj.bbox_mm,
        footprint_mm=obj.footprint_mm,
        volume_cm3=obj.volume_cm3,
        loss_w=obj.loss_w,
        preferred_label=obj.preferred_label,
        layout_position_mm=HardwareIntegratedPosition(x_mm=x_mm, y_mm=y_mm, z_mm=0.0),
        layout_anchor=obj.layout_anchor,
        notes=obj.notes,
        warnings=obj.warnings,
    )


def _center_integrated_layout(objects: list[HardwareIntegratedLayoutObject]) -> list[HardwareIntegratedLayoutObject]:
    if not objects:
        return []
    min_x, max_x, min_y, max_y, _, _ = _integrated_extents(objects)
    center_x = 0.5 * (min_x + max_x)
    center_y = 0.5 * (min_y + max_y)
    return [
        _place_object(
            obj,
            obj.layout_position_mm.x_mm - center_x,
            obj.layout_position_mm.y_mm - center_y,
        )
        for obj in objects
    ]


def _integrated_global_bbox(objects: list[HardwareIntegratedLayoutObject]) -> HardwareIntegratedBox:
    if not objects:
        return HardwareIntegratedBox()
    min_x, max_x, min_y, max_y, min_z, max_z = _integrated_extents(objects)
    return HardwareIntegratedBox(width_mm=max_x - min_x, depth_mm=max_y - min_y, height_mm=max_z - min_z)


def _integrated_extents(objects: list[HardwareIntegratedLayoutObject]) -> tuple[float, float, float, float, float, float]:
    min_x = min(obj.layout_position_mm.x_mm - 0.5 * _box_width(obj.bbox_mm) for obj in objects)
    max_x = max(obj.layout_position_mm.x_mm + 0.5 * _box_width(obj.bbox_mm) for obj in objects)
    min_y = min(obj.layout_position_mm.y_mm - 0.5 * _box_depth(obj.bbox_mm) for obj in objects)
    max_y = max(obj.layout_position_mm.y_mm + 0.5 * _box_depth(obj.bbox_mm) for obj in objects)
    min_z = 0.0
    max_z = max(_box_height(obj.bbox_mm) for obj in objects)
    return min_x, max_x, min_y, max_y, min_z, max_z


def _integrated_axis_limits(global_bbox: HardwareIntegratedBox) -> tuple[dict[str, tuple[float, float] | None], dict[str, tuple[float, float] | None]]:
    if global_bbox.width_mm is None or global_bbox.depth_mm is None or global_bbox.height_mm is None:
        return ({"x_mm": None, "y_mm": None}, {"x_mm": None, "y_mm": None, "z_mm": None})
    padding = 0.12
    x_half = 0.5 * global_bbox.width_mm * (1.0 + 2.0 * padding)
    y_half = 0.5 * global_bbox.depth_mm * (1.0 + 2.0 * padding)
    z_max = global_bbox.height_mm * (1.0 + padding)
    return (
        {"x_mm": (-x_half, x_half), "y_mm": (-y_half, y_half)},
        {"x_mm": (-x_half, x_half), "y_mm": (-y_half, y_half), "z_mm": (0.0, z_max)},
    )


def _integrated_missing_warnings(
    groups: list[HardwareOverviewComponentGroup],
    objects: list[HardwareIntegratedLayoutObject],
) -> list[str]:
    present_ids = {obj.id for obj in objects}
    by_id = {group.group_id: group for group in groups}
    warnings: list[str] = []
    if "semiconductor" not in present_ids:
        warning = _first_warning(by_id.get("semiconductor")) or "Semiconductor is unavailable for integrated hardware overview."
        warnings.append(warning)
    if "inductor" not in present_ids:
        warning = _first_warning(by_id.get("inductor")) or "Inductor is unavailable for integrated hardware overview."
        warnings.append(warning)
    if "capacitor_input" not in present_ids:
        warnings.append("Input capacitor is unavailable for integrated hardware overview.")
    if "capacitor_output" not in present_ids:
        warnings.append("Output capacitor is unavailable for integrated hardware overview.")
    return warnings


def _first_warning(group: HardwareOverviewComponentGroup | None) -> str | None:
    if group is None or not group.warnings:
        return None
    return group.warnings[0]


def _box_width(box: HardwareIntegratedBox) -> float:
    return float(box.width_mm or 0.0)


def _box_depth(box: HardwareIntegratedBox) -> float:
    return float(box.depth_mm or 0.0)


def _box_height(box: HardwareIntegratedBox) -> float:
    return float(box.height_mm or 0.0)


def _build_inductor_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    if report.magnetic is None:
        return _missing_group("inductor", "Inductor", "Run Magnetics first to populate inductor overview.")

    target = _recommended_inductor_target(report)
    design = _recommended_inductor_design(report)
    layout = target.layout if target is not None else report.geometry.selected_layout if report.geometry else None
    if design is None and layout is None:
        return _missing_group("inductor", "Inductor", "Recommended magnetic design is unavailable.")

    bbox = _inductor_bbox(layout)
    artifacts = _inductor_recommended_artifacts(target, report)
    image_2d_path = _first_existing_path(artifacts, suffixes=(".png",), excluded_markers=("_3d",))
    image_3d_path = _first_existing_path(artifacts, suffixes=("_3d.png",))
    volume_cm3 = _m3_to_cm3(target.volume_m3 if target is not None else None)
    if volume_cm3 is None and design is not None:
        volume_cm3 = _m3_to_cm3(design.total_volume_m3)
    loss_w = target.loss_w if target is not None else _inductor_loss_w(report, design.candidate_id if design is not None else None)
    warnings = _bbox_warnings(bbox)
    warnings.extend(_image_warnings(image_2d_path, image_3d_path))
    if volume_cm3 is None:
        warnings.append("Incomplete volume definition: inductor total assembly volume is unavailable.")
    return HardwareOverviewComponentGroup(
        group_id="inductor",
        display_name="Inductor",
        status="available",
        recommended_name=(design.candidate_id if design is not None else layout.design_id if layout is not None else ""),
        manufacturer=None,
        series=(design.core_name if design is not None else layout.core_name if layout is not None else None),
        part_number=(design.candidate_id if design is not None else layout.design_id if layout is not None else None),
        quantity=1,
        volume_cm3=volume_cm3,
        volume_breakdown_cm3={
            "core_volume_cm3": _m3_to_cm3(design.core_volume_m3 if design is not None else None),
            "winding_volume_cm3": _m3_to_cm3(design.winding_volume_m3 if design is not None else None),
            "assembly_volume_cm3": volume_cm3,
        },
        loss_w=loss_w,
        image_2d_path_existing=image_2d_path,
        image_3d_path_existing=image_3d_path,
        image_2d=_local_image_ref(image_2d_path),
        image_3d=_local_image_ref(image_3d_path),
        geometry_source="existing_artifact" if layout is not None else "missing",
        bounding_box_mm=bbox,
        shape_type="magnetic_core_assembly",
        metadata={
            "core_family": layout.core_family if layout is not None else None,
            "core_name": design.core_name if design is not None else layout.core_name if layout is not None else None,
            "base_core_name": design.base_core_name if design is not None else layout.base_core_name if layout is not None else None,
            "winding_type": design.wire_name if design is not None else layout.wire_name if layout is not None else None,
            "turns": design.turns if design is not None else layout.turns if layout is not None else None,
            "parallel_strands": design.parallel_bundles if design is not None else layout.parallels if layout is not None else None,
            "stack_count": design.stack_count if design is not None else layout.stack_count if layout is not None else None,
            "hotspot_proxy_temp_c": _thermal_hotspot_c(report),
        },
        notes=["Inductor overview volume uses total assembly volume, including stacked assembly depth when present."],
        warnings=warnings,
    )


def _build_capacitor_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    if report.capacitor is None:
        return _missing_group("capacitor", "Capacitors", "Run Capacitor first to populate capacitor overview.")

    input_entry = report.capacitor.input_selection.recommended if report.capacitor.input_selection else None
    output_entry = report.capacitor.output_selection.recommended if report.capacitor.output_selection else None
    input_target = _capacitor_recommended_target(report, "input")
    output_target = _capacitor_recommended_target(report, "output")
    child_entries = [
        _capacitor_child_entry("input", input_entry, input_target),
        _capacitor_child_entry("output", output_entry, output_target),
    ]
    child_entries = [child for child in child_entries if child is not None]
    volume_cm3 = _sum_optional(child.volume_cm3 for child in child_entries)
    loss_w = _sum_optional(child.loss_w for child in child_entries)
    bbox = _combined_capacitor_bbox(child_entries)
    artifacts = _capacitor_recommended_artifacts(input_target, output_target)
    image_2d_path = _first_existing_path(artifacts, suffixes=(".png",), excluded_markers=("_3d",))
    image_3d_path = _first_existing_path(artifacts, suffixes=("_3d.png",))
    warnings = _bbox_warnings(bbox)
    warnings.extend(_image_warnings(image_2d_path, image_3d_path))
    if not input_entry:
        warnings.append("Input capacitor recommended bank is unavailable.")
    if not output_entry:
        warnings.append("Output capacitor recommended bank is unavailable.")
    status = "available" if input_entry or output_entry else "missing"
    return HardwareOverviewComponentGroup(
        group_id="capacitor",
        display_name="Capacitors",
        status=status,
        recommended_name=_capacitor_recommended_name(input_entry, output_entry),
        quantity=_sum_ints(child.quantity for child in child_entries),
        volume_cm3=volume_cm3,
        volume_breakdown_cm3={
            "input_capacitor_bank_volume_cm3": _entry_volume(input_entry),
            "output_capacitor_bank_volume_cm3": _entry_volume(output_entry),
        },
        loss_w=loss_w,
        image_2d_path_existing=image_2d_path,
        image_3d_path_existing=image_3d_path,
        image_2d=_local_image_ref(image_2d_path),
        image_3d=_local_image_ref(image_3d_path),
        geometry_source="existing_artifact" if input_target or output_target else "missing",
        bounding_box_mm=bbox,
        shape_type="rectangular_box" if any(child.shape_type == "rectangular_box" for child in child_entries) else "cylindrical_can",
        child_entries=child_entries,
        notes=["Capacitor overview groups input and output recommended banks side by side; it does not merge them physically."],
        warnings=warnings,
    )


def _capacitor_child_entry(
    side: str,
    entry: CapacitorSelectionEntry | None,
    target: CapacitorGeometryTarget | None,
) -> HardwareOverviewChildEntry | None:
    if entry is None:
        return HardwareOverviewChildEntry(
            entry_id=f"{side}_capacitor",
            display_name=f"{side.title()} capacitor recommended",
            bounding_box_mm=HardwareOverviewBoundingBox(),
            warnings=[f"{side.title()} capacitor recommended bank is unavailable."],
        )
    candidate = entry.candidate
    bbox = _capacitor_bbox(entry, target)
    return HardwareOverviewChildEntry(
        entry_id=f"{side}_capacitor",
        display_name=f"{side.title()} capacitor recommended",
        recommended_name=f"{candidate.part_number} N={entry.parallel_count}",
        manufacturer=candidate.manufacturer,
        series=candidate.series,
        part_number=candidate.part_number,
        quantity=entry.parallel_count,
        volume_cm3=entry.total_volume_cm3,
        loss_w=entry.p_total_w,
        bounding_box_mm=bbox,
        shape_type=candidate.package_shape or "unknown",
        notes=[f"Series display: {capacitor_series_display_name(candidate)}."],
        warnings=_bbox_warnings(bbox),
    )


def _build_global_scale(groups: list[HardwareOverviewComponentGroup]) -> HardwareOverviewGlobalScale:
    bboxes = {group.group_id: group.bounding_box_mm for group in groups if _bbox_complete(group.bounding_box_mm)}
    max_width = max((bbox.width_mm or 0.0 for bbox in bboxes.values()), default=0.0)
    max_height = max((bbox.height_mm or 0.0 for bbox in bboxes.values()), default=0.0)
    max_depth = max((bbox.depth_mm or 0.0 for bbox in bboxes.values()), default=0.0)
    max_dimension = max(max_width, max_height, max_depth) if bboxes else None
    padding = 0.12
    common_2d = None
    common_3d = None
    if max_dimension is not None:
        x_half = 0.5 * max_width * (1.0 + 2.0 * padding)
        y_half = 0.5 * max_height * (1.0 + 2.0 * padding)
        z_half = 0.5 * max_depth * (1.0 + 2.0 * padding)
        common_2d = {"x_mm": (-x_half, x_half), "y_mm": (-y_half, y_half)}
        common_3d = {"x_mm": (-x_half, x_half), "y_mm": (-y_half, y_half), "z_mm": (-z_half, z_half)}
    return HardwareOverviewGlobalScale(
        all_components_bbox_mm=bboxes,
        max_dimension_mm=max_dimension,
        view_padding_fraction=padding,
        common_2d_axis_limits_mm=common_2d or {"x_mm": None, "y_mm": None},
        common_3d_axis_limits_mm=common_3d or {"x_mm": None, "y_mm": None, "z_mm": None},
        notes=[
            "Future overview 2D/3D rendering should use these global axis limits instead of individual-page auto-scaling.",
            "Existing individual-page artifacts are marked local-scale fallback only.",
        ],
    )


def _recommended_semiconductor_target(report: DesignReport) -> SemiconductorGeometryTarget | None:
    geometry = report.semiconductor_geometry
    if geometry is None or not geometry.targets:
        return None
    recommended_id = report.device.recommended_scheme_id if report.device else geometry.recommended_scheme_id
    return next((target for target in geometry.targets if target.scheme_id == recommended_id), geometry.targets[0])


def _semiconductor_recommended_name(report: DesignReport) -> str:
    device = report.device
    if device is None:
        return ""
    if device.active_scheme_label:
        return device.active_scheme_label
    if device.recommended_scheme_id:
        return device.recommended_scheme_id
    return ", ".join(f"{role}={part}" for role, part in sorted(device.selected_devices.items()))


def _semiconductor_child_entry(role_layout: SemiconductorGeometryRoleLayout) -> HardwareOverviewChildEntry:
    bbox = _semiconductor_role_bbox(role_layout)
    return HardwareOverviewChildEntry(
        entry_id=role_layout.role_name,
        display_name=role_layout.role_label or role_layout.role_name,
        recommended_name=role_layout.part_number or "",
        manufacturer=role_layout.vendor,
        series=role_layout.package,
        part_number=role_layout.part_number,
        quantity=role_layout.quantity,
        volume_cm3=_semiconductor_role_volume_cm3(role_layout),
        loss_w=role_layout.role_total_loss_w,
        bounding_box_mm=bbox,
        shape_type="semiconductor_module" if role_layout.package_level == "module" else "semiconductor_package",
        notes=[f"Thermal source: {role_layout.thermal_source or '-'}."] if role_layout.thermal_source else [],
        warnings=_bbox_warnings(bbox),
    )


def _semiconductor_bbox(target: SemiconductorGeometryTarget) -> HardwareOverviewBoundingBox:
    if target.estimated_sink_dims_mm is not None:
        sink_width_mm, sink_height_mm, sink_depth_mm = target.estimated_sink_dims_mm
        return HardwareOverviewBoundingBox(float(sink_width_mm), float(sink_height_mm), float(sink_depth_mm))
    role_bboxes = [_semiconductor_role_bbox(role) for role in target.role_layouts if _bbox_complete(_semiconductor_role_bbox(role))]
    return _combined_bbox(role_bboxes)


def _semiconductor_role_bbox(role_layout: SemiconductorGeometryRoleLayout) -> HardwareOverviewBoundingBox:
    layout = role_layout.layout
    if layout is None:
        return HardwareOverviewBoundingBox()
    quantity = max(int(role_layout.quantity or 1), 1)
    width_mm = quantity * layout.package_body_width_mm + max(quantity - 1, 0) * max(3.0, 0.28 * layout.package_body_width_mm)
    height_mm = layout.package_body_height_mm + layout.lead_length_mm
    depth_mm = layout.package_body_thickness_mm
    return HardwareOverviewBoundingBox(width_mm, height_mm, depth_mm)


def _semiconductor_role_volume_cm3(role_layout: SemiconductorGeometryRoleLayout) -> float | None:
    layout = role_layout.layout
    if layout is None:
        return None
    quantity = max(int(role_layout.quantity or 1), 1)
    volume_mm3 = layout.package_body_width_mm * layout.package_body_height_mm * layout.package_body_thickness_mm * quantity
    return volume_mm3 / 1000.0


def _semiconductor_role_sink_volume_cm3(role_layouts: tuple[SemiconductorGeometryRoleLayout, ...]) -> float | None:
    for role_layout in role_layouts:
        if role_layout.layout is not None:
            value = _positive_or_none(role_layout.layout.sink_volume_cm3)
            if value is not None:
                return value
    return None


def _resolve_semiconductor_loss_w(report: DesignReport) -> float | None:
    device = report.device
    if device is None:
        return None
    scheme_id = device.active_scheme_id or device.recommended_scheme_id
    scheme = next((item for item in device.scheme_results if item.scheme_id == scheme_id), None)
    if scheme is not None and scheme.total_scheme_loss_w is not None:
        return scheme.total_scheme_loss_w
    losses = device.current_operating_losses or device.design_point_losses or device.evaluated_losses
    if not losses:
        return None
    return sum(loss.p_total_W for loss in losses.values())


def _recommended_inductor_target(report: DesignReport) -> GeometryTarget | None:
    geometry = report.geometry
    if geometry is None:
        return None
    return next((target for target in geometry.targets if target.role == "recommended"), None)


def _recommended_inductor_design(report: DesignReport) -> FixedInductorDesignCandidate | None:
    magnetic = report.magnetic
    if magnetic is None:
        return None
    target_id = None
    if report.geometry and report.geometry.selected_design_id:
        target_id = report.geometry.selected_design_id
    elif report.loss and report.loss.recommended_design_id:
        target_id = report.loss.recommended_design_id
    elif magnetic.selected_design_id:
        target_id = magnetic.selected_design_id
    if target_id:
        found = next((design for design in magnetic.chosen_designs if design.candidate_id == target_id), None)
        if found is not None:
            return found
    return magnetic.chosen_designs[0] if magnetic.chosen_designs else None


def _inductor_bbox(layout: InductorGeometryLayout | None) -> HardwareOverviewBoundingBox:
    if layout is None:
        return HardwareOverviewBoundingBox()
    return HardwareOverviewBoundingBox(layout.overall_width_mm, layout.overall_height_mm, layout.overall_depth_mm)


def _inductor_loss_w(report: DesignReport, design_id: str | None) -> float | None:
    if design_id is None:
        return None
    if report.magnetic:
        evaluation = next((item for item in report.magnetic.evaluations if item.design_id == design_id), None)
        if evaluation is not None:
            return evaluation.total_loss_w
    if report.loss and report.loss.top_design_losses:
        values = report.loss.top_design_losses.get(design_id)
        if values:
            return values.get("total_loss_w")
    return None


def _thermal_hotspot_c(report: DesignReport) -> float | None:
    if report.thermal is None or report.thermal.recommended_estimate is None:
        return None
    return report.thermal.recommended_estimate.hotspot_proxy_temp_c


def _capacitor_recommended_target(report: DesignReport, side: str) -> CapacitorGeometryTarget | None:
    if report.capacitor is None:
        return None
    geometry = report.capacitor.input_geometry if side == "input" else report.capacitor.output_geometry
    if geometry is None:
        return None
    return next((target for target in geometry.targets if target.role == "recommended"), None)


def _capacitor_bbox(
    entry: CapacitorSelectionEntry,
    target: CapacitorGeometryTarget | None,
) -> HardwareOverviewBoundingBox:
    if target is not None and target.layout is not None:
        layout = target.layout
        return HardwareOverviewBoundingBox(layout.footprint_width_mm, layout.bank_height_mm, layout.footprint_depth_mm)
    candidate = entry.candidate
    width_mm = candidate.body_width_mm or candidate.diameter_mm
    depth_mm = candidate.body_depth_mm or candidate.diameter_mm
    height_mm = candidate.body_height_mm or candidate.height_mm
    if width_mm is None or depth_mm is None or height_mm is None:
        return HardwareOverviewBoundingBox()
    parallel = max(entry.parallel_count, 1)
    spacing_mm = max(8.0, 0.10 * max(width_mm, depth_mm))
    footprint_width_mm = (parallel * width_mm) + max(parallel - 1, 0) * spacing_mm
    return HardwareOverviewBoundingBox(footprint_width_mm, height_mm, depth_mm)


def _combined_capacitor_bbox(child_entries: list[HardwareOverviewChildEntry]) -> HardwareOverviewBoundingBox:
    bboxes = [child.bounding_box_mm for child in child_entries if _bbox_complete(child.bounding_box_mm)]
    if not bboxes:
        return HardwareOverviewBoundingBox()
    if len(bboxes) == 1:
        return bboxes[0]
    spacing_mm = max(10.0, 0.10 * max(bbox.width_mm or 0.0 for bbox in bboxes))
    width_mm = sum(bbox.width_mm or 0.0 for bbox in bboxes) + spacing_mm * (len(bboxes) - 1)
    height_mm = max(bbox.height_mm or 0.0 for bbox in bboxes)
    depth_mm = max(bbox.depth_mm or 0.0 for bbox in bboxes)
    return HardwareOverviewBoundingBox(width_mm, height_mm, depth_mm)


def _capacitor_recommended_name(
    input_entry: CapacitorSelectionEntry | None,
    output_entry: CapacitorSelectionEntry | None,
) -> str:
    parts = []
    if input_entry is not None:
        parts.append(f"input={input_entry.candidate.part_number} N={input_entry.parallel_count}")
    if output_entry is not None:
        parts.append(f"output={output_entry.candidate.part_number} N={output_entry.parallel_count}")
    return ", ".join(parts)


def _capacitor_recommended_artifacts(
    input_target: CapacitorGeometryTarget | None,
    output_target: CapacitorGeometryTarget | None,
) -> list[str]:
    paths: list[str] = []
    for target in (input_target, output_target):
        if target is None:
            continue
        paths.extend(target.artifact_paths)
    return paths


def _inductor_recommended_artifacts(target: GeometryTarget | None, report: DesignReport) -> list[str]:
    paths: list[str] = []
    if target is not None:
        paths.extend(target.artifact_paths)
    if report.geometry is not None:
        paths.extend(report.geometry.artifact_paths)
    return _dedupe_paths(paths)


def _entry_volume(entry: CapacitorSelectionEntry | None) -> float | None:
    return None if entry is None else entry.total_volume_cm3


def _missing_group(group_id: str, display_name: str, warning: str) -> HardwareOverviewComponentGroup:
    return HardwareOverviewComponentGroup(
        group_id=group_id,
        display_name=display_name,
        status="missing",
        geometry_source="missing",
        notes=[warning],
        warnings=[warning],
    )


def _local_image_ref(path: str | None) -> HardwareOverviewImageRef:
    return HardwareOverviewImageRef(path=path, image_scale_type="local_scale" if path else "unknown", recommended_for_overview=False)


def _first_existing_path(
    paths: list[str],
    *,
    suffixes: tuple[str, ...],
    excluded_markers: tuple[str, ...] = (),
) -> str | None:
    for path_text in paths:
        path = Path(path_text)
        name = path.name
        if excluded_markers and any(marker in name for marker in excluded_markers):
            continue
        if any(name.endswith(suffix) for suffix in suffixes) and path.exists():
            return str(path)
    return None


def _image_warnings(image_2d_path: str | None, image_3d_path: str | None) -> list[str]:
    warnings: list[str] = []
    if image_2d_path is None:
        warnings.append("Missing existing 2D geometry image path.")
    else:
        warnings.append("Existing 2D geometry image is local-scale fallback only.")
    if image_3d_path is None:
        warnings.append("Missing existing 3D geometry image path.")
    else:
        warnings.append("Existing 3D geometry image is local-scale fallback only.")
    return warnings


def _bbox_warnings(bbox: HardwareOverviewBoundingBox) -> list[str]:
    return [] if _bbox_complete(bbox) else ["Missing bounding_box_mm for global overview scaling."]


def _bbox_complete(bbox: HardwareOverviewBoundingBox) -> bool:
    values = (bbox.width_mm, bbox.height_mm, bbox.depth_mm)
    return all(value is not None and float(value) > 0.0 and math.isfinite(float(value)) for value in values)


def _combined_bbox(bboxes: list[HardwareOverviewBoundingBox]) -> HardwareOverviewBoundingBox:
    valid = [bbox for bbox in bboxes if _bbox_complete(bbox)]
    if not valid:
        return HardwareOverviewBoundingBox()
    return HardwareOverviewBoundingBox(
        width_mm=max(bbox.width_mm or 0.0 for bbox in valid),
        height_mm=max(bbox.height_mm or 0.0 for bbox in valid),
        depth_mm=max(bbox.depth_mm or 0.0 for bbox in valid),
    )


def _payload_warnings(groups: list[HardwareOverviewComponentGroup]) -> list[str]:
    warnings: list[str] = []
    for group in groups:
        if group.status == "missing":
            warnings.append(f"{group.display_name} overview data is missing.")
        warnings.extend(f"{group.display_name}: {warning}" for warning in group.warnings)
    return _dedupe_strings(warnings)


def _sum_optional(values) -> float | None:
    total = 0.0
    found = False
    for value in values:
        if value is None:
            continue
        total += float(value)
        found = True
    return total if found else None


def _sum_ints(values) -> int | None:
    total = 0
    found = False
    for value in values:
        if value is None:
            continue
        total += int(value)
        found = True
    return total if found else None


def _m3_to_cm3(value_m3: float | None) -> float | None:
    return None if value_m3 is None else float(value_m3) * 1e6


def _positive_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    value = float(value)
    return value if value > 0.0 else None


def _resolve_output_dir(output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        return Path(output_dir)
    return Path(__file__).resolve().parents[3] / _OVERVIEW_OUTPUT_DIR


def _dedupe_paths(paths: list[str]) -> list[str]:
    return _dedupe_strings([str(Path(path)) for path in paths])


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
