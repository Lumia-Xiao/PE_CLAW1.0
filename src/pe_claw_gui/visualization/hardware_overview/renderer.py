"""Shared-scale proxy renderers for Hardware Overview artifacts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle

from ...engines.hardware_overview import (
    HardwareOverviewBoundingBox,
    HardwareOverviewChildEntry,
    HardwareOverviewComponentGroup,
    HardwareOverviewImageRef,
    HardwareIntegratedBox,
    HardwareIntegratedLayoutObject,
    HardwareOverviewPayload,
    build_integrated_hardware_layout_from_groups,
    write_hardware_overview_payload_json,
)
from .pie import export_hardware_volume_pie

_GROUP_BASENAMES = {
    "semiconductor": ("overview_semiconductor_2d.png", "overview_semiconductor_3d.png"),
    "transformer": ("overview_transformer_2d.png", "overview_transformer_3d.png"),
    "inductor": ("overview_inductor_2d.png", "overview_inductor_3d.png"),
    "capacitor": ("overview_capacitor_2d.png", "overview_capacitor_3d.png"),
}
_GROUP_COLORS = {
    "semiconductor": "#cbd5e1",
    "transformer": "#fef3c7",
    "inductor": "#d9dde6",
    "capacitor": "#dbeafe",
}


def generate_hardware_overview_artifacts(payload: HardwareOverviewPayload, output_dir: str | Path) -> HardwareOverviewPayload:
    """Generate shared-scale overview PNG artifacts and persist the updated payload JSON."""

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    if payload.status != "available":
        json_path = write_hardware_overview_payload_json(payload, output_root)
        return replace(payload, artifact_paths=_dedupe_strings([*payload.artifact_paths, str(json_path)]))
    scale = _resolve_scale_settings(payload)
    updated_groups: list[HardwareOverviewComponentGroup] = []
    overview_artifacts: dict[str, str] = dict(payload.overview_artifacts)
    warnings = list(payload.warnings)

    for group in payload.component_groups:
        artifact_key = group.group_id
        file_names = _GROUP_BASENAMES.get(group.group_id)
        if file_names is None:
            updated_groups.append(group)
            continue
        path_2d = output_root / file_names[0]
        path_3d = output_root / file_names[1]
        group_warnings: list[str] = []
        try:
            if _bbox_complete(group.bounding_box_mm) and group.status != "missing":
                _export_group_2d(group, path_2d, scale)
                _export_group_3d(group, path_3d, scale)
                updated_group = _with_overview_images(group, str(path_2d), str(path_3d))
                group_warnings.append("Overview image uses global shared-scale proxy rendering.")
                warnings.append(f"{group.display_name}: overview image uses bounding-box/proxy rendering.")
            else:
                _export_placeholder_figure(path_2d, group.display_name, "Overview geometry unavailable")
                _export_placeholder_figure(path_3d, group.display_name, "Overview 3D geometry unavailable")
                updated_group = _with_placeholder_images(group, str(path_2d), str(path_3d), "Missing bounding box or group data; generated placeholder artifact.")
                warnings.append(f"{group.display_name}: missing data; placeholder overview artifact generated.")
            overview_artifacts[f"{artifact_key}_2d"] = str(path_2d)
            overview_artifacts[f"{artifact_key}_3d"] = str(path_3d)
            updated_groups.append(replace(updated_group, warnings=_dedupe_strings([*updated_group.warnings, *group_warnings])))
        except Exception as exc:  # pragma: no cover - defensive fallback for renderer/runtime backends.
            updated_group = _with_overview_failure(group, f"Overview artifact generation failed: {exc}")
            updated_groups.append(updated_group)
            warnings.append(f"{group.display_name}: overview artifact generation failed: {exc}")

    pie_path, pie_warnings = export_hardware_volume_pie(updated_groups, output_root)
    overview_artifacts["volume_pie"] = pie_path
    warnings.extend(pie_warnings)
    integrated_artifacts = dict(payload.integrated_overview_artifacts)
    integrated_path_2d = output_root / "overview_hardware_2d.png"
    integrated_path_3d = output_root / "overview_hardware_3d.png"
    integrated_layout = build_integrated_hardware_layout_from_groups(
        updated_groups,
        artifact_paths={
            "hardware_2d": str(integrated_path_2d),
            "hardware_3d": str(integrated_path_3d),
            "volume_pie": pie_path,
        },
    )
    _export_integrated_2d(integrated_layout.groups, integrated_path_2d, integrated_layout)
    _export_integrated_3d(integrated_layout.groups, integrated_path_3d, integrated_layout)
    integrated_artifacts["hardware_2d"] = str(integrated_path_2d)
    integrated_artifacts["hardware_3d"] = str(integrated_path_3d)
    integrated_artifacts["volume_pie"] = pie_path
    warnings.extend(integrated_layout.warnings)

    updated_global_scale = _with_artifact_scale(payload, scale)
    updated_payload = HardwareOverviewPayload(
        component_groups=updated_groups,
        global_geometry_scale=updated_global_scale,
        status=payload.status,
        run_id=payload.run_id,
        topology_id=payload.topology_id,
        blocked_reason=payload.blocked_reason,
        source_ids=dict(payload.source_ids),
        dependency_diagnostics=dict(payload.dependency_diagnostics),
        artifact_paths=_dedupe_strings([*payload.artifact_paths, *overview_artifacts.values(), *integrated_artifacts.values()]),
        overview_artifacts=overview_artifacts,
        integrated_layout=integrated_layout,
        integrated_overview_artifacts=integrated_artifacts,
        notes=_dedupe_strings(
            [
                *payload.notes,
                "Overview-specific 2D/3D artifacts use common global axis limits from the payload scale metadata.",
                "Hardware volume pie uses positive top-level recommended group volumes.",
                "Per-group overview artifacts still exist for debugging and legacy display.",
                "Integrated hardware overview artifacts are the preferred system-level representation.",
            ]
        ),
        warnings=_dedupe_strings(warnings),
    )
    json_path = output_root / "hardware_overview_payload.json"
    updated_payload = replace(updated_payload, artifact_paths=_dedupe_strings([*updated_payload.artifact_paths, str(json_path)]))
    write_hardware_overview_payload_json(updated_payload, output_root)
    return updated_payload


def _export_integrated_2d(objects: list[HardwareIntegratedLayoutObject], output_path: Path, layout) -> None:
    if not objects:
        _export_placeholder_figure(output_path, "Hardware Overview - globally scaled 2D", "No hardware objects are available for integrated overview.")
        return
    figure = Figure(figsize=(8.8, 4.8), dpi=120)
    axis = figure.subplots(1, 1)
    axis.set_aspect("equal", adjustable="box")
    x_limits = layout.common_2d_axis_limits_mm.get("x_mm")
    y_limits = layout.common_2d_axis_limits_mm.get("y_mm")
    if x_limits is None or y_limits is None:
        x_limits, y_limits = _integrated_fallback_2d_limits(objects)
    axis.set_xlim(*x_limits)
    axis.set_ylim(*y_limits)
    axis.set_xlabel("width (mm)")
    axis.set_ylabel("depth (mm)")
    axis.grid(True, alpha=0.18)
    axis.set_title("Hardware Overview - globally scaled 2D", fontsize=11.0)
    for obj in objects:
        _draw_integrated_object_2d(axis, obj)
    scale_bar = _resolve_scale_bar_mm(max(_integrated_max_dimension(objects), 1.0))
    _draw_scale_bar(axis, scale_bar, x_limits, y_limits)
    axis.text(
        0.02,
        0.98,
        "Engineering overview layout, not PCB/package placement.",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=8.0,
        bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.86},
    )
    figure.tight_layout()
    try:
        figure.savefig(output_path)
    finally:
        figure.clear()


def _export_integrated_3d(objects: list[HardwareIntegratedLayoutObject], output_path: Path, layout) -> None:
    if not objects:
        _export_placeholder_figure(output_path, "Hardware Overview - globally scaled 3D", "No hardware objects are available for integrated overview.")
        return
    figure = Figure(figsize=(8.8, 5.4), dpi=120)
    axis = figure.add_subplot(111, projection="3d")
    x_limits = layout.common_3d_axis_limits_mm.get("x_mm")
    y_limits = layout.common_3d_axis_limits_mm.get("y_mm")
    z_limits = layout.common_3d_axis_limits_mm.get("z_mm")
    if x_limits is None or y_limits is None or z_limits is None:
        x_limits, y_limits, z_limits = _integrated_fallback_3d_limits(objects)
    axis.set_xlim(*x_limits)
    axis.set_ylim(*y_limits)
    axis.set_zlim(*z_limits)
    axis.set_xlabel("width (mm)")
    axis.set_ylabel("depth (mm)")
    axis.set_zlabel("height (mm)")
    axis.set_title("Hardware Overview - globally scaled 3D", fontsize=11.0)
    for obj in objects:
        _draw_integrated_object_3d(axis, obj)
    axis.view_init(elev=24.0, azim=-42.0)
    try:
        axis.set_box_aspect((_span(x_limits), _span(y_limits), _span(z_limits)))
    except AttributeError:
        pass
    figure.tight_layout()
    try:
        figure.savefig(output_path)
    finally:
        figure.clear()


def _export_group_2d(group: HardwareOverviewComponentGroup, output_path: Path, scale: dict[str, object]) -> None:
    figure = Figure(figsize=(5.0, 4.2), dpi=120)
    axis = figure.subplots(1, 1)
    axis.set_aspect("equal", adjustable="box")
    x_limits = scale["x_limits"]
    y_limits = scale["y_limits"]
    axis.set_xlim(*x_limits)
    axis.set_ylim(*y_limits)
    axis.set_xlabel("width (mm)")
    axis.set_ylabel("height/depth (mm)")
    axis.grid(True, alpha=0.2)
    axis.set_title(f"{group.display_name} - globally scaled 2D", fontsize=10.0)
    _draw_group_2d(axis, group)
    _draw_scale_bar(axis, float(scale["scale_bar_mm"]), x_limits, y_limits)
    _draw_note(axis, _group_note(group))
    figure.tight_layout()
    try:
        figure.savefig(output_path)
    finally:
        figure.clear()


def _export_group_3d(group: HardwareOverviewComponentGroup, output_path: Path, scale: dict[str, object]) -> None:
    figure = Figure(figsize=(5.0, 4.4), dpi=120)
    axis = figure.add_subplot(111, projection="3d")
    axis.set_xlim(*scale["x_limits"])
    axis.set_ylim(*scale["y_limits"])
    axis.set_zlim(*scale["z_limits"])
    axis.set_xlabel("width (mm)")
    axis.set_ylabel("depth (mm)")
    axis.set_zlabel("height (mm)")
    axis.set_title(f"{group.display_name} - globally scaled 3D", fontsize=10.0)
    _draw_group_3d(axis, group)
    axis.view_init(elev=24.0, azim=-42.0)
    try:
        x_span = _span(scale["x_limits"])
        y_span = _span(scale["y_limits"])
        z_span = _span(scale["z_limits"])
        axis.set_box_aspect((x_span, y_span, z_span))
    except AttributeError:
        pass
    figure.tight_layout()
    try:
        figure.savefig(output_path)
    finally:
        figure.clear()


def _draw_group_2d(axis, group: HardwareOverviewComponentGroup) -> None:
    if group.group_id == "capacitor" and group.child_entries:
        _draw_capacitor_children_2d(axis, group)
        return
    bbox = group.bounding_box_mm
    width = float(bbox.width_mm or 0.0)
    height = float(bbox.height_mm or bbox.depth_mm or 0.0)
    color = _GROUP_COLORS.get(group.group_id, "#e5e7eb")
    axis.add_patch(Rectangle((-0.5 * width, -0.5 * height), width, height, facecolor=color, edgecolor="#111827", alpha=0.55, linewidth=1.2))
    if group.group_id == "semiconductor" and group.volume_breakdown_cm3.get("heatsink_volume_cm3"):
        device_width = max(width * 0.32, min(width, 12.0))
        device_height = max(height * 0.18, min(height, 8.0))
        axis.add_patch(
            Rectangle(
                (-0.5 * device_width, -0.5 * device_height),
                device_width,
                device_height,
                facecolor="#94a3b8",
                edgecolor="#334155",
                linewidth=1.0,
            )
        )
    if group.group_id == "inductor":
        winding_width = width * 0.45
        winding_height = height * 0.45
        axis.add_patch(Rectangle((-0.5 * winding_width, -0.5 * winding_height), winding_width, winding_height, fill=False, edgecolor="#1d4ed8", linewidth=1.1))
    axis.text(0.0, 0.0, group.display_name, ha="center", va="center", fontsize=8.5)


def _draw_capacitor_children_2d(axis, group: HardwareOverviewComponentGroup) -> None:
    valid_children = [child for child in group.child_entries if _bbox_complete(child.bounding_box_mm)]
    if not valid_children:
        _draw_group_bbox_2d(axis, group, "Capacitors")
        return
    total_width = sum(float(child.bounding_box_mm.width_mm or 0.0) for child in valid_children)
    spacing = max(10.0, 0.10 * max(float(child.bounding_box_mm.width_mm or 0.0) for child in valid_children))
    total_width += spacing * max(len(valid_children) - 1, 0)
    x_cursor = -0.5 * total_width
    for child in valid_children:
        width = float(child.bounding_box_mm.width_mm or 0.0)
        depth = float(child.bounding_box_mm.depth_mm or child.bounding_box_mm.height_mm or 0.0)
        center_x = x_cursor + 0.5 * width
        _draw_child_body_2d(axis, child, center_x, 0.0, width, depth)
        axis.text(center_x, -0.5 * depth - 4.0, child.display_name, ha="center", va="top", fontsize=7.5)
        x_cursor += width + spacing


def _draw_child_body_2d(axis, child: HardwareOverviewChildEntry, center_x: float, center_y: float, width: float, depth: float) -> None:
    if child.shape_type in {"cylindrical_can", "cylindrical_plastic_case", "axial_cylindrical"}:
        quantity = max(int(child.quantity or 1), 1)
        shown = min(quantity, 6)
        diameter = min(depth, width / max(shown, 1))
        spacing = diameter * 0.18
        bank_width = shown * diameter + max(shown - 1, 0) * spacing
        x0 = center_x - 0.5 * bank_width + 0.5 * diameter
        for index in range(shown):
            axis.add_patch(Circle((x0 + index * (diameter + spacing), center_y), 0.5 * diameter, facecolor="#dbeafe", edgecolor="#1e3a8a", linewidth=1.0))
        if quantity > shown:
            axis.text(center_x, center_y, f"N={quantity}", ha="center", va="center", fontsize=7.0)
        return
    axis.add_patch(Rectangle((center_x - 0.5 * width, center_y - 0.5 * depth), width, depth, facecolor="#dbeafe", edgecolor="#1e3a8a", alpha=0.65))
    if child.quantity:
        axis.text(center_x, center_y, f"N={child.quantity}", ha="center", va="center", fontsize=7.5)


def _draw_group_bbox_2d(axis, group: HardwareOverviewComponentGroup, label: str) -> None:
    bbox = group.bounding_box_mm
    width = float(bbox.width_mm or 0.0)
    depth = float(bbox.depth_mm or bbox.height_mm or 0.0)
    axis.add_patch(Rectangle((-0.5 * width, -0.5 * depth), width, depth, fill=False, edgecolor="#111827", linewidth=1.0))
    axis.text(0.0, 0.0, label, ha="center", va="center", fontsize=8.0)


def _draw_group_3d(axis, group: HardwareOverviewComponentGroup) -> None:
    if group.group_id == "capacitor" and group.child_entries:
        _draw_capacitor_children_3d(axis, group)
        return
    bbox = group.bounding_box_mm
    width = float(bbox.width_mm or 0.0)
    depth = float(bbox.depth_mm or 0.0)
    height = float(bbox.height_mm or 0.0)
    _draw_box_3d(axis, -0.5 * width, -0.5 * depth, 0.0, width, depth, height, _GROUP_COLORS.get(group.group_id, "#e5e7eb"), alpha=0.55)
    if group.group_id == "semiconductor" and group.volume_breakdown_cm3.get("heatsink_volume_cm3"):
        device_width = max(width * 0.30, min(width, 12.0))
        device_depth = max(depth * 0.24, min(depth, 10.0))
        device_height = max(height * 0.10, min(height, 5.0))
        _draw_box_3d(axis, -0.5 * device_width, -0.5 * device_depth, height, device_width, device_depth, device_height, "#64748b", alpha=0.85)
    axis.text(0.0, 0.0, height * 1.04, group.display_name, ha="center", va="bottom", fontsize=8.0)


def _draw_capacitor_children_3d(axis, group: HardwareOverviewComponentGroup) -> None:
    valid_children = [child for child in group.child_entries if _bbox_complete(child.bounding_box_mm)]
    if not valid_children:
        _draw_group_3d(axis, replace(group, child_entries=[]))
        return
    total_width = sum(float(child.bounding_box_mm.width_mm or 0.0) for child in valid_children)
    spacing = max(10.0, 0.10 * max(float(child.bounding_box_mm.width_mm or 0.0) for child in valid_children))
    total_width += spacing * max(len(valid_children) - 1, 0)
    x_cursor = -0.5 * total_width
    for child in valid_children:
        width = float(child.bounding_box_mm.width_mm or 0.0)
        depth = float(child.bounding_box_mm.depth_mm or 0.0)
        height = float(child.bounding_box_mm.height_mm or 0.0)
        center_x = x_cursor + 0.5 * width
        if child.shape_type in {"cylindrical_can", "cylindrical_plastic_case", "axial_cylindrical"}:
            _draw_capacitor_cylinders_3d(axis, child, center_x, 0.0, width, depth, height)
        else:
            _draw_box_3d(axis, center_x - 0.5 * width, -0.5 * depth, 0.0, width, depth, height, "#dbeafe", alpha=0.7)
        axis.text(center_x, 0.0, height * 1.05, child.display_name, ha="center", va="bottom", fontsize=7.0)
        x_cursor += width + spacing


def _draw_capacitor_cylinders_3d(axis, child: HardwareOverviewChildEntry, center_x: float, center_y: float, width: float, depth: float, height: float) -> None:
    quantity = max(int(child.quantity or 1), 1)
    shown = min(quantity, 6)
    diameter = min(depth, width / max(shown, 1))
    spacing = diameter * 0.18
    bank_width = shown * diameter + max(shown - 1, 0) * spacing
    x0 = center_x - 0.5 * bank_width + 0.5 * diameter
    for index in range(shown):
        _draw_cylinder_3d(axis, x0 + index * (diameter + spacing), center_y, diameter, height)
    if quantity > shown:
        axis.text(center_x, center_y, height * 0.5, f"N={quantity}", ha="center", va="center", fontsize=7.0)


def _draw_integrated_object_2d(axis, obj: HardwareIntegratedLayoutObject) -> None:
    width = _box_width(obj.bbox_mm)
    depth = _box_depth(obj.bbox_mm)
    x = obj.layout_position_mm.x_mm
    y = obj.layout_position_mm.y_mm
    if obj.shape_type in {"cylindrical_can", "cylindrical_plastic_case", "axial_cylindrical"}:
        radius = 0.5 * min(width, depth)
        axis.add_patch(Circle((x, y), radius, facecolor="#dbeafe", edgecolor="#1e3a8a", alpha=0.75, linewidth=1.1))
        if width > 1.3 * depth:
            axis.add_patch(Rectangle((x - 0.5 * width, y - 0.5 * depth), width, depth, fill=False, linestyle="--", edgecolor="#1e3a8a", linewidth=0.8))
    else:
        color = _GROUP_COLORS.get(obj.source_group, "#e5e7eb")
        axis.add_patch(Rectangle((x - 0.5 * width, y - 0.5 * depth), width, depth, facecolor=color, edgecolor="#111827", alpha=0.65, linewidth=1.1))
        if obj.id == "semiconductor":
            device_width = max(width * 0.28, min(width, 12.0))
            device_depth = max(depth * 0.22, min(depth, 10.0))
            axis.add_patch(Rectangle((x - 0.5 * device_width, y - 0.5 * device_depth), device_width, device_depth, facecolor="#94a3b8", edgecolor="#334155", linewidth=0.9))
        if obj.id == "inductor":
            winding_width = width * 0.42
            winding_depth = depth * 0.42
            axis.add_patch(Rectangle((x - 0.5 * winding_width, y - 0.5 * winding_depth), winding_width, winding_depth, fill=False, edgecolor="#1d4ed8", linewidth=1.0))
    label = _integrated_label(obj, include_volume=False)
    axis.text(x, y + 0.5 * depth + 5.0, label, ha="center", va="bottom", fontsize=8.0)
    if obj.volume_cm3 is not None:
        axis.text(x, y, f"{obj.volume_cm3:.3g} cm^3", ha="center", va="center", fontsize=7.0, color="#111827")


def _draw_integrated_object_3d(axis, obj: HardwareIntegratedLayoutObject) -> None:
    width = _box_width(obj.bbox_mm)
    depth = _box_depth(obj.bbox_mm)
    height = _box_height(obj.bbox_mm)
    x = obj.layout_position_mm.x_mm
    y = obj.layout_position_mm.y_mm
    if obj.shape_type in {"cylindrical_can", "cylindrical_plastic_case", "axial_cylindrical"}:
        diameter = min(width, depth)
        _draw_cylinder_3d(axis, x, y, diameter, height)
        if width > 1.3 * depth:
            _draw_box_3d(axis, x - 0.5 * width, y - 0.5 * depth, 0.0, width, depth, max(height * 0.03, 1.0), "#dbeafe", alpha=0.18)
    else:
        color = _GROUP_COLORS.get(obj.source_group, "#e5e7eb")
        _draw_box_3d(axis, x - 0.5 * width, y - 0.5 * depth, 0.0, width, depth, height, color, alpha=0.62)
        if obj.id == "semiconductor":
            device_width = max(width * 0.26, min(width, 12.0))
            device_depth = max(depth * 0.20, min(depth, 10.0))
            device_height = max(height * 0.08, min(height, 5.0))
            _draw_box_3d(axis, x - 0.5 * device_width, y - 0.5 * device_depth, height, device_width, device_depth, device_height, "#64748b", alpha=0.85)
    axis.text(x, y, height * 1.08, _integrated_label(obj, include_volume=False), ha="center", va="bottom", fontsize=7.5)


def _integrated_label(obj: HardwareIntegratedLayoutObject, *, include_volume: bool = True) -> str:
    label = _short_component_label(obj)
    if include_volume and obj.volume_cm3 is not None:
        return f"{label}\n{obj.volume_cm3:.3g} cm^3"
    return label


def _short_component_label(obj: HardwareIntegratedLayoutObject) -> str:
    labels = {
        "capacitor_input": "Input capacitor",
        "semiconductor": "Semiconductor",
        "transformer": "LLC transformer",
        "inductor": "Inductor",
        "llc_resonant_capacitor": "LLC resonant capacitor",
        "capacitor_output": "Output capacitor",
        "capacitor": "Capacitors",
    }
    return labels.get(obj.id, obj.preferred_label or obj.display_name)


def _draw_box_3d(axis, x: float, y: float, z: float, width: float, depth: float, height: float, color: str, *, alpha: float) -> None:
    x_values = np.array([[x, x + width], [x, x + width]])
    y_values = np.array([[y, y], [y + depth, y + depth]])
    axis.plot_surface(x_values, y_values, np.full_like(x_values, z), color=color, alpha=alpha, linewidth=0.25, edgecolor="#475569")
    axis.plot_surface(x_values, y_values, np.full_like(x_values, z + height), color=color, alpha=alpha, linewidth=0.25, edgecolor="#475569")
    for side_x in (x, x + width):
        side_y = np.array([[y, y + depth], [y, y + depth]])
        side_z = np.array([[z, z], [z + height, z + height]])
        axis.plot_surface(np.full_like(side_y, side_x), side_y, side_z, color=color, alpha=alpha, linewidth=0.25, edgecolor="#475569")
    for side_y in (y, y + depth):
        side_x = np.array([[x, x + width], [x, x + width]])
        side_z = np.array([[z, z], [z + height, z + height]])
        axis.plot_surface(side_x, np.full_like(side_x, side_y), side_z, color=color, alpha=alpha, linewidth=0.25, edgecolor="#475569")


def _draw_cylinder_3d(axis, x_mm: float, y_mm: float, diameter_mm: float, height_mm: float) -> None:
    radius_mm = 0.5 * diameter_mm
    theta = np.linspace(0.0, 2.0 * np.pi, 32)
    z_values = np.linspace(0.0, height_mm, 8)
    theta_grid, z_grid = np.meshgrid(theta, z_values)
    x_grid = x_mm + radius_mm * np.cos(theta_grid)
    y_grid = y_mm + radius_mm * np.sin(theta_grid)
    axis.plot_surface(x_grid, y_grid, z_grid, color="#dbeafe", edgecolor="#1e3a8a", linewidth=0.2, alpha=0.82)
    axis.plot(x_mm + radius_mm * np.cos(theta), y_mm + radius_mm * np.sin(theta), np.full_like(theta, height_mm), color="#1e3a8a", linewidth=0.7)


def _export_placeholder_figure(output_path: Path, title: str, message: str) -> None:
    figure = Figure(figsize=(5.0, 4.2), dpi=120)
    axis = figure.subplots(1, 1)
    axis.axis("off")
    axis.set_title(title, fontsize=10.0)
    axis.text(0.5, 0.5, message, ha="center", va="center", fontsize=10.0, transform=axis.transAxes)
    figure.tight_layout()
    try:
        figure.savefig(output_path)
    finally:
        figure.clear()


def _draw_scale_bar(axis, scale_bar_mm: float, x_limits: tuple[float, float], y_limits: tuple[float, float]) -> None:
    x0 = x_limits[0] + 0.08 * _span(x_limits)
    y0 = y_limits[0] + 0.08 * _span(y_limits)
    axis.plot([x0, x0 + scale_bar_mm], [y0, y0], color="#111827", linewidth=2.0)
    axis.text(x0 + 0.5 * scale_bar_mm, y0 + 0.03 * _span(y_limits), f"{scale_bar_mm:g} mm", ha="center", va="bottom", fontsize=8.0)


def _draw_note(axis, text: str) -> None:
    axis.text(
        0.02,
        0.98,
        text,
        ha="left",
        va="top",
        transform=axis.transAxes,
        fontsize=7.5,
        bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.85},
    )


def _group_note(group: HardwareOverviewComponentGroup) -> str:
    parts = [group.recommended_name or group.display_name]
    if group.volume_cm3 is not None:
        parts.append(f"Volume {group.volume_cm3:.3g} cm^3")
    if group.loss_w is not None:
        parts.append(f"Loss {group.loss_w:.3g} W")
    return "\n".join(parts[:3])


def _with_overview_images(group: HardwareOverviewComponentGroup, path_2d: str, path_3d: str) -> HardwareOverviewComponentGroup:
    return replace(
        group,
        overview_image_2d_path=path_2d,
        overview_image_3d_path=path_3d,
        image_2d=HardwareOverviewImageRef(path=path_2d, image_scale_type="global_scale", recommended_for_overview=True),
        image_3d=HardwareOverviewImageRef(path=path_3d, image_scale_type="global_scale", recommended_for_overview=True),
        geometry_source="regenerated_overview_artifact",
    )


def _with_overview_failure(group: HardwareOverviewComponentGroup, warning: str) -> HardwareOverviewComponentGroup:
    return replace(group, warnings=_dedupe_strings([*group.warnings, warning]))


def _with_placeholder_images(group: HardwareOverviewComponentGroup, path_2d: str, path_3d: str, warning: str) -> HardwareOverviewComponentGroup:
    return replace(
        group,
        overview_image_2d_path=path_2d,
        overview_image_3d_path=path_3d,
        image_2d=HardwareOverviewImageRef(path=path_2d, image_scale_type="missing", recommended_for_overview=False),
        image_3d=HardwareOverviewImageRef(path=path_3d, image_scale_type="missing", recommended_for_overview=False),
        warnings=_dedupe_strings([*group.warnings, warning]),
    )


def _resolve_scale_settings(payload: HardwareOverviewPayload) -> dict[str, object]:
    bboxes = [group.bounding_box_mm for group in payload.component_groups if _bbox_complete(group.bounding_box_mm)]
    padding = payload.global_geometry_scale.view_padding_fraction
    max_width = max((float(bbox.width_mm or 0.0) for bbox in bboxes), default=100.0)
    max_height = max((float(bbox.height_mm or 0.0) for bbox in bboxes), default=100.0)
    max_depth = max((float(bbox.depth_mm or 0.0) for bbox in bboxes), default=100.0)
    axis_xy_span = max(max_width, max_depth, max_height, 10.0) * (1.0 + 2.0 * padding)
    z_span = max(max_height, 10.0) * (1.0 + 2.0 * padding)
    max_dimension = payload.global_geometry_scale.max_dimension_mm or max(max_width, max_height, max_depth)
    return {
        "x_limits": (-0.5 * axis_xy_span, 0.5 * axis_xy_span),
        "y_limits": (-0.5 * axis_xy_span, 0.5 * axis_xy_span),
        "z_limits": (0.0, z_span),
        "scale_bar_mm": _resolve_scale_bar_mm(float(max_dimension)),
    }


def _with_artifact_scale(payload: HardwareOverviewPayload, scale: dict[str, object]):
    return replace(
        payload.global_geometry_scale,
        common_2d_axis_limits_mm={
            "x_mm": scale["x_limits"],
            "y_mm": scale["y_limits"],
        },
        common_3d_axis_limits_mm={
            "x_mm": scale["x_limits"],
            "y_mm": scale["y_limits"],
            "z_mm": scale["z_limits"],
        },
        notes=_dedupe_strings(
            [
                *payload.global_geometry_scale.notes,
                "Overview artifacts were generated with these common 2D/3D axis limits.",
            ]
        ),
    )


def _resolve_scale_bar_mm(max_dimension_mm: float) -> float:
    if max_dimension_mm <= 30.0:
        return 10.0
    if max_dimension_mm <= 120.0:
        return 50.0
    if max_dimension_mm <= 320.0:
        return 100.0
    return 200.0


def _integrated_fallback_2d_limits(objects: list[HardwareIntegratedLayoutObject]) -> tuple[tuple[float, float], tuple[float, float]]:
    min_x, max_x, min_y, max_y, _, _ = _integrated_extents(objects)
    x_pad = max(10.0, 0.12 * (max_x - min_x))
    y_pad = max(10.0, 0.12 * (max_y - min_y))
    return (min_x - x_pad, max_x + x_pad), (min_y - y_pad, max_y + y_pad)


def _integrated_fallback_3d_limits(objects: list[HardwareIntegratedLayoutObject]) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    x_limits, y_limits = _integrated_fallback_2d_limits(objects)
    z_max = max((_box_height(obj.bbox_mm) for obj in objects), default=100.0)
    return x_limits, y_limits, (0.0, z_max * 1.12)


def _integrated_extents(objects: list[HardwareIntegratedLayoutObject]) -> tuple[float, float, float, float, float, float]:
    min_x = min(obj.layout_position_mm.x_mm - 0.5 * _box_width(obj.bbox_mm) for obj in objects)
    max_x = max(obj.layout_position_mm.x_mm + 0.5 * _box_width(obj.bbox_mm) for obj in objects)
    min_y = min(obj.layout_position_mm.y_mm - 0.5 * _box_depth(obj.bbox_mm) for obj in objects)
    max_y = max(obj.layout_position_mm.y_mm + 0.5 * _box_depth(obj.bbox_mm) for obj in objects)
    max_z = max(_box_height(obj.bbox_mm) for obj in objects)
    return min_x, max_x, min_y, max_y, 0.0, max_z


def _integrated_max_dimension(objects: list[HardwareIntegratedLayoutObject]) -> float:
    if not objects:
        return 100.0
    min_x, max_x, min_y, max_y, _, max_z = _integrated_extents(objects)
    return max(max_x - min_x, max_y - min_y, max_z)


def _bbox_complete(bbox: HardwareOverviewBoundingBox) -> bool:
    return bool(bbox.width_mm and bbox.height_mm and bbox.depth_mm and bbox.width_mm > 0.0 and bbox.height_mm > 0.0 and bbox.depth_mm > 0.0)


def _box_width(box: HardwareIntegratedBox) -> float:
    return float(box.width_mm or 0.0)


def _box_depth(box: HardwareIntegratedBox) -> float:
    return float(box.depth_mm or 0.0)


def _box_height(box: HardwareIntegratedBox) -> float:
    return float(box.height_mm or 0.0)


def _span(limits: tuple[float, float]) -> float:
    return float(limits[1]) - float(limits[0])


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
