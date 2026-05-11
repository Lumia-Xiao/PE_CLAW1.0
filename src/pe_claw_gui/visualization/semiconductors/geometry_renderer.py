"""Semiconductor geometry renderer."""

from __future__ import annotations

from dataclasses import dataclass

from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle

from ...models.semiconductor_geometry_result import SemiconductorGeometryLayout, SemiconductorGeometryRoleLayout, SemiconductorGeometryTarget
from .physical_package_instances import PhysicalPackageInstance, build_physical_package_instances_for_target

_CONTENT_LEFT_PAD_MM = 12.0
_CONTENT_RIGHT_PAD_MM = 8.0
_CONTENT_BOTTOM_PAD_MM = 8.0
_CONTENT_TOP_PAD_MM = 4.0
_TOP_BAND_GAP_MM = 6.0
_TOP_BAND_HEIGHT_MM = 18.0
_PACKAGE_BASELINE_Y_MM = 6.0
_THERMAL_ANCHOR_FRACTION_FROM_SINK_BOTTOM = 0.62
_SIDE_LEADED_TOP_PACKAGES = {"hdsop_10_top", "hdsop_16_top", "hdsop_22_top", "dso_20_top"}
_LEADLESS_TOP_PACKAGES = {"tson_8_top", "lson_8_top"}
_MODULE_PACKAGES = {"module_half_bridge", "module_flat_baseplate", "module_single_switch", "module_six_pack"}


@dataclass(frozen=True)
class SemiconductorGeometryScene:
    """Resolved 2D scene placement for one semiconductor figure."""

    axis_xlim_mm: tuple[float, float]
    axis_ylim_mm: tuple[float, float]
    device_count: int
    device_x_origins_mm: tuple[float, ...]
    thermal_anchor_xs_mm: tuple[float, ...]
    package_body_center_xs_mm: tuple[float, ...]
    top_band_bottom_y_mm: float
    sink_x_origin_mm: float
    sink_y_origin_mm: float
    sink_width_mm: float
    sink_height_mm: float
    sink_depth_mm: float
    sink_footprint_depth_mm: float
    sink_center_x_mm: float
    sink_thermal_anchor_fraction_from_bottom: float
    package_x_origin_mm: float
    package_y_origin_mm: float
    package_span_width_mm: float
    package_span_height_mm: float
    package_body_x_mm: float
    package_body_y_mm: float
    package_body_width_mm: float
    package_body_height_mm: float
    package_body_center_x_mm: float
    package_body_center_y_mm: float
    thermal_anchor_x_mm: float
    thermal_anchor_y_mm: float
    lead_region_center_y_mm: float
    content_min_x_mm: float
    content_max_x_mm: float
    content_max_y_mm: float
    legend_center_x_mm: float
    legend_top_y_mm: float
    legend_lines: tuple[str, ...]


def create_semiconductor_geometry_figure(layout: SemiconductorGeometryLayout) -> Figure:
    """Create a clean first-pass device-plus-heatsink engineering sketch."""

    figure = Figure(figsize=(6.4, 4.8), dpi=120)
    axis = figure.subplots(1, 1)
    _render_semiconductor_axis(axis, layout, title="Semiconductor Geometry")
    figure.tight_layout(pad=1.0)
    return figure


def create_semiconductor_geometry_comparison_figure(targets: tuple[SemiconductorGeometryTarget, ...]) -> Figure:
    """Create side-by-side semiconductor geometry comparison panels."""

    panel_count = max(len(targets), 1)
    figure = Figure(figsize=(5.2 * panel_count, 5.4), dpi=120)
    axes = figure.subplots(1, panel_count)
    if panel_count == 1:
        axes = [axes]
    for axis, target in zip(axes, targets):
        if target.role_layouts:
            _render_multi_role_target(axis, target)
            continue
        if target.layout is None:
            axis.axis("off")
            axis.set_title(target.label, fontsize=10.0, fontweight="bold", pad=6.0)
            axis.text(
                0.5,
                0.5,
                target.error_message or "Geometry unavailable.",
                transform=axis.transAxes,
                ha="center",
                va="center",
                fontsize=9.0,
            )
            continue
        _render_semiconductor_axis(axis, target.layout, title=target.label)
    if any(target.panel_scale_source == "global" for target in targets):
        figure.text(0.5, 0.01, "Shared physical scale across all schemes.", ha="center", va="bottom", fontsize=8.0, color="#374151")
    figure.tight_layout(pad=1.0)
    return figure


def _render_multi_role_target(axis, target: SemiconductorGeometryTarget) -> None:
    axis.axis("off")
    panel_width, panel_height = target.rendered_unit_bbox or (1.0, 1.0)
    axis.set_xlim(-0.5 * panel_width, 0.5 * panel_width)
    axis.set_ylim(-0.5 * panel_height, 0.5 * panel_height)
    axis.set_aspect("equal", adjustable="box")
    axis.set_title(target.label, fontsize=10.0, fontweight="bold", pad=6.0)
    role_layouts = target.role_layouts
    if not role_layouts:
        axis.text(0.5, 0.5, target.error_message or "Geometry unavailable.", ha="center", va="center", fontsize=9.0)
        return

    family = (target.topology_id or "").casefold()
    physical_instances = build_physical_package_instances_for_target(target)
    _draw_shared_sink_scaled(axis, target)
    origins = _resolve_instance_origins_scaled(target, family, physical_instances)
    for instance, (x, y) in zip(physical_instances, origins):
        _draw_physical_instance_group_scaled(axis, target, instance, x=x, y=y)

    notes: list[str] = []
    if target.estimated_sink_dims_mm is not None:
        width_mm, height_mm, depth_mm = target.estimated_sink_dims_mm
        notes.append(f"Sink: {width_mm:.3g} x {height_mm:.3g} x {depth_mm:.3g} mm")
    notes.extend(_physical_instance_summary_lines(physical_instances))
    if target.error_message:
        notes.append(target.error_message)
    if notes:
        axis.text(
            0.5,
            0.02,
            "\n".join(notes),
            transform=axis.transAxes,
            ha="center",
            va="bottom",
            fontsize=7.0,
            color="#374151",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "#ffffff", "edgecolor": "#cbd5e1"},
        )


def _draw_shared_sink_scaled(axis, target: SemiconductorGeometryTarget) -> None:
    scale = target.global_mm_to_unit or 1.0
    sink_width = (target.sink_width_mm or 24.0) * scale
    sink_depth = (target.sink_depth_mm or target.sink_height_mm or 18.0) * scale
    sink = Rectangle(
        (-0.5 * sink_width, -0.5 * sink_depth),
        sink_width,
        sink_depth,
        facecolor="#d9dde6",
        edgecolor="#111827",
        linewidth=1.1,
        zorder=0,
    )
    sink.set_gid(f"shared-sink:{target.scheme_id}")
    axis.add_patch(sink)
    fin_count = 8
    for index in range(fin_count):
        x = -0.42 * sink_width + index * (0.84 * sink_width / max(fin_count - 1, 1))
        axis.plot([x, x], [0.25 * sink_depth, 0.44 * sink_depth], color="#94a3b8", linewidth=0.8, zorder=1)


def _resolve_instance_origins_scaled(
    target: SemiconductorGeometryTarget,
    topology_id: str,
    physical_instances: tuple[PhysicalPackageInstance, ...],
) -> tuple[tuple[float, float], ...]:
    if not physical_instances:
        return ()
    boxes = [_physical_instance_assembly_size_scaled(instance) for instance in physical_instances]
    count = len(physical_instances)
    if "four_switch_buck_boost_simplified_four_mode" in topology_id and count > 1:
        col_count = 2
        row_count = 2
    elif "three_level_tzcm_fixed_frequency" in topology_id and count > 1:
        col_count = 1
        row_count = count
    elif count == 2:
        col_count = 2
        row_count = 1
    else:
        col_count = count
        row_count = 1

    max_width = max(width for width, _ in boxes)
    max_height = max(height for _, height in boxes)
    gap = _ROLE_GAP_RENDERED(target)
    total_width = (col_count * max_width) + (max(col_count - 1, 0) * gap)
    total_height = (row_count * max_height) + (max(row_count - 1, 0) * gap)
    top_y = 0.5 * total_height
    origins: list[tuple[float, float]] = []
    for index, (width, height) in enumerate(boxes):
        row = index // col_count
        col = index % col_count
        cell_x = -0.5 * total_width + col * (max_width + gap)
        cell_y = top_y - (row + 1) * max_height - row * gap
        origins.append(
            (
                cell_x + 0.5 * (max_width - width),
                cell_y + 0.5 * (max_height - height),
            )
        )
    return tuple(origins)


def _ROLE_GAP_RENDERED(target: SemiconductorGeometryTarget) -> float:
    return 8.0 * (target.global_mm_to_unit or 1.0)


def _role_assembly_size_scaled(role_layout: SemiconductorGeometryRoleLayout) -> tuple[float, float]:
    layout = role_layout.layout
    if layout is None:
        return (0.0, 0.0)
    scale = role_layout.package_body_width_rendered / layout.package_body_width_mm if role_layout.package_body_width_rendered else 1.0
    quantity = max(int(role_layout.quantity or 1), 1)
    package_width = _package_span_width_mm(layout) * scale
    package_height = _package_span_height_mm(layout) * scale
    gap = max(3.0, 0.28 * _package_span_width_mm(layout)) * scale
    return (
        (quantity * package_width) + (max(quantity - 1, 0) * gap),
        package_height,
    )


def _physical_instance_assembly_size_scaled(instance: PhysicalPackageInstance) -> tuple[float, float]:
    return _role_assembly_size_scaled(instance.primary_role_layout)


def _draw_physical_instance_group_scaled(
    axis,
    target: SemiconductorGeometryTarget,
    instance: PhysicalPackageInstance,
    *,
    x: float,
    y: float,
) -> None:
    width, height = _physical_instance_assembly_size_scaled(instance)
    pad = 2.0 * (target.global_mm_to_unit or 1.0)
    axis.add_patch(
        Rectangle(
            (x - pad, y - pad),
            width + (2.0 * pad),
            height + (2.0 * pad),
            facecolor="#ffffff99",
            edgecolor="#94a3b8",
            linewidth=0.8,
            zorder=2,
        )
    )
    axis.text(
        x + 0.5 * width,
        y + height + (3.0 * (target.global_mm_to_unit or 1.0)),
        f"{instance.role_labels} x{instance.quantity}",
        ha="center",
        va="bottom",
        fontsize=6.6,
        color="#111827",
        zorder=5,
    )
    _draw_parallel_package_icons_scaled(axis, target, instance, x=x, y=y)


def _short_role_label(role_name: str) -> str:
    normalized = role_name.strip().casefold()
    if normalized == "main_switch":
        return "SW"
    if normalized == "rectifier_diode":
        return "D"
    if normalized == "sync_switch":
        return "SYNC"
    if normalized in {"s1", "s2", "s3", "s4"}:
        return role_name.upper()
    if normalized.startswith("switch_"):
        return role_name.replace("switch_", "").upper()
    return role_name.upper()[:6]


def _draw_parallel_package_icons_scaled(
    axis,
    target: SemiconductorGeometryTarget,
    instance: PhysicalPackageInstance,
    *,
    x: float,
    y: float,
) -> None:
    role_layout = instance.primary_role_layout
    layout = role_layout.layout
    if layout is None:
        return
    scale = target.global_mm_to_unit or 1.0
    count = max(int(instance.quantity or 1), 1)
    package_width = _package_span_width_mm(layout) * scale
    package_height = _package_span_height_mm(layout) * scale
    gap = max(3.0, 0.28 * _package_span_width_mm(layout)) * scale
    for index in range(count):
        package_x = x + index * (package_width + gap)
        _draw_package_icon_scaled(
            axis,
            role_layout,
            x=package_x,
            y=y,
            scale=scale,
            gid=f"package-icon:{target.scheme_id}:{instance.instance_id}",
        )
    axis.text(
        x + (count * package_width) + (max(count - 1, 0) * gap),
        y + package_height,
        f"x{count}",
        ha="right",
        va="top",
        fontsize=6.8,
        color="#0f172a",
        bbox={"boxstyle": "round,pad=0.12", "facecolor": "#e0f2fe", "edgecolor": "#0284c7"},
        zorder=8,
    )


def _draw_package_icon_scaled(axis, role_layout: SemiconductorGeometryRoleLayout, *, x: float, y: float, scale: float, gid: str) -> None:
    layout = role_layout.layout
    if layout is None:
        return
    renderer_id = layout.renderer_template_id
    body_w = layout.package_body_width_mm * scale
    body_h = layout.package_body_height_mm * scale
    lead_len = layout.lead_length_mm * scale
    lead_w = layout.lead_width_mm * scale
    if renderer_id in {"to220_3_tht", "to247_2_tht", "to247_3_tht", "to247_4_tht"}:
        body_y = y + lead_len
        body = Rectangle((x, body_y), body_w, body_h, facecolor="#1f2937", edgecolor="#020617", linewidth=0.9, zorder=5)
        body.set_gid(gid)
        axis.add_patch(body)
        tab_w = min(layout.package_tab_width_mm, layout.package_body_width_mm) * scale
        tab_h = min(layout.package_tab_height_mm, layout.package_body_height_mm) * scale
        tab_x = x + 0.5 * (body_w - tab_w)
        tab_y = body_y + body_h - tab_h - (1.0 * scale)
        axis.add_patch(Rectangle((tab_x, tab_y), tab_w, tab_h, facecolor="#64748b", edgecolor="#334155", linewidth=0.7, zorder=6))
        if layout.package_hole_diameter_mm > 0.0:
            axis.add_patch(
                Circle(
                    (x + 0.5 * body_w, tab_y + 0.5 * tab_h),
                    0.5 * layout.package_hole_diameter_mm * scale,
                    facecolor="#f8fafc",
                    edgecolor="#0f172a",
                    linewidth=0.6,
                    zorder=7,
                )
            )
        lead_count = max(layout.package_lead_count, 2)
        lead_span = max((lead_count - 1) * layout.lead_pitch_mm * scale, 0.0)
        lead_start = x + 0.5 * (body_w - lead_span)
        for index in range(lead_count):
            lead_x = lead_start + index * layout.lead_pitch_mm * scale
            axis.add_patch(Rectangle((lead_x - 0.5 * lead_w, y), lead_w, lead_len, facecolor="#9ca3af", edgecolor="#4b5563", linewidth=0.5, zorder=4))
        return
    if renderer_id in {"hdsop_10_top", "hdsop_16_top", "hdsop_22_top", "dso_20_top"}:
        body_x = x + lead_len
        body = Rectangle((body_x, y), body_w, body_h, facecolor="#334155", edgecolor="#0f172a", linewidth=0.8, zorder=5)
        body.set_gid(gid)
        axis.add_patch(body)
        pad_w = min(layout.package_tab_width_mm, layout.package_body_width_mm) * scale
        pad_h = min(layout.package_tab_height_mm, layout.package_body_height_mm) * scale
        axis.add_patch(
            Rectangle(
                (body_x + 0.5 * (body_w - pad_w), y + 0.5 * (body_h - pad_h)),
                pad_w,
                pad_h,
                facecolor="#94a3b8",
                edgecolor="#475569",
                linewidth=0.5,
                zorder=6,
            )
        )
        pins = max(layout.package_lead_count // 2, 2)
        for side in (0, 1):
            pin_x = x if side == 0 else body_x + body_w
            for index in range(pins):
                pin_y = y + 0.12 * body_h + index * (0.76 * body_h / max(pins - 1, 1))
                axis.add_patch(Rectangle((pin_x, pin_y - 0.5 * lead_w), lead_len, lead_w, facecolor="#9ca3af", edgecolor="#4b5563", linewidth=0.3, zorder=4))
        return
    if renderer_id in _MODULE_PACKAGES:
        body = Rectangle((x, y), body_w, body_h, facecolor="#dbeafe", edgecolor="#1d4ed8", linewidth=0.9, zorder=5)
        body.set_gid(gid)
        axis.add_patch(body)
        axis.add_patch(Rectangle((x, y), body_w, 0.18 * body_h, facecolor="#cbd5e1", edgecolor="#475569", linewidth=0.5, zorder=6))
        return

    body_y = y + (0.25 * lead_len if lead_len > 0 else 0.0)
    body = Rectangle((x, body_y), body_w, body_h, facecolor="#334155", edgecolor="#0f172a", linewidth=0.8, zorder=5)
    body.set_gid(gid)
    axis.add_patch(body)
    if lead_len > 0:
        leads = max(min(layout.package_lead_count, 8), 2)
        pitch = body_w / max(leads + 1, 1)
        for index in range(leads):
            lead_x = x + (index + 1) * pitch - 0.5 * lead_w
            axis.add_patch(Rectangle((lead_x, y), lead_w, 0.25 * lead_len, facecolor="#9ca3af", edgecolor="#4b5563", linewidth=0.4, zorder=4))


def _physical_instance_summary_lines(physical_instances: tuple[PhysicalPackageInstance, ...]) -> tuple[str, ...]:
    lines: list[str] = []
    for instance in physical_instances:
        role_layout = instance.primary_role_layout
        if role_layout.part_number is None:
            lines.append(f"Missing role: {role_layout.role_name}")
            continue
        size_text = ""
        if role_layout.package_body_width_mm is not None and role_layout.package_body_height_mm is not None:
            size_text = f", {role_layout.package_body_width_mm:.3g} x {role_layout.package_body_height_mm:.3g} mm"
        lines.append(
            f"{instance.role_labels}: {instance.package_part_number}, "
            f"{instance.package_name}{size_text}, x{instance.quantity}"
        )
        internal_diodes = [
            part_number
            for role_name, part_number in instance.section_part_numbers.items()
            if role_name == "rectifier_diode" and part_number != instance.package_part_number
        ]
        for part_number in internal_diodes:
            lines.append(f"Internal diode: {part_number}")
    return tuple(lines)


def _role_summary_line(role_layout: SemiconductorGeometryRoleLayout) -> str:
    if role_layout.part_number is None:
        return f"Missing role: {role_layout.role_name}"
    size_text = ""
    if role_layout.package_body_width_mm is not None and role_layout.package_body_height_mm is not None:
        size_text = f", {role_layout.package_body_width_mm:.3g} x {role_layout.package_body_height_mm:.3g} mm"
    return (
        f"{_short_role_label(role_layout.role_name)}: {role_layout.part_number or '-'}, "
        f"{role_layout.package or '-'}{size_text}, x{role_layout.quantity}"
    )


def build_semiconductor_geometry_scene(layout: SemiconductorGeometryLayout) -> SemiconductorGeometryScene:
    """Resolve package, sink, and legend placement into one testable scene."""

    sink_width_mm = layout.sink_width_mm or 18.0
    sink_height_mm = layout.sink_height_mm or (layout.package_body_height_mm + 6.0)
    sink_depth_mm = layout.sink_depth_mm or 8.0
    sink_footprint_depth_mm = sink_depth_mm
    package_span_width_mm = _package_span_width_mm(layout)
    package_span_height_mm = _package_span_height_mm(layout)
    package_body_offset_x_mm, package_body_offset_y_mm = _package_body_offset_mm(layout)
    thermal_anchor_offset_x_mm, thermal_anchor_offset_y_mm = _thermal_anchor_offset_mm(layout)
    package_gap_mm = _resolve_package_gap_mm(
        package_span_width_mm=package_span_width_mm,
        parallel_count=layout.parallel_count,
        sink_width_mm=sink_width_mm,
    )
    assembly_width_mm = (
        layout.parallel_count * package_span_width_mm
        + max(layout.parallel_count - 1, 0) * package_gap_mm
    )

    package_y_origin_mm = _PACKAGE_BASELINE_Y_MM
    assembly_x_origin_mm = -0.5 * assembly_width_mm
    device_x_origins_mm = tuple(
        assembly_x_origin_mm + index * (package_span_width_mm + package_gap_mm)
        for index in range(layout.parallel_count)
    )
    thermal_anchor_xs_mm = tuple(
        package_x_origin_mm + thermal_anchor_offset_x_mm
        for package_x_origin_mm in device_x_origins_mm
    )
    package_body_center_xs_mm = tuple(
        package_x_origin_mm + package_body_offset_x_mm + (0.5 * layout.package_body_width_mm)
        for package_x_origin_mm in device_x_origins_mm
    )
    package_body_x_mm = device_x_origins_mm[0] + package_body_offset_x_mm
    package_body_y_mm = package_y_origin_mm + package_body_offset_y_mm
    package_body_center_y_mm = package_body_y_mm + (0.5 * layout.package_body_height_mm)
    thermal_anchor_y_mm = package_y_origin_mm + thermal_anchor_offset_y_mm
    lead_region_center_y_mm = package_y_origin_mm + (0.5 * package_body_offset_y_mm)

    sink_center_x_mm = sum(thermal_anchor_xs_mm) / len(thermal_anchor_xs_mm)
    sink_x_origin_mm = sink_center_x_mm - (0.5 * sink_width_mm)
    sink_y_origin_mm = thermal_anchor_y_mm - (_THERMAL_ANCHOR_FRACTION_FROM_SINK_BOTTOM * sink_footprint_depth_mm)

    content_min_x_mm = min(
        sink_x_origin_mm - 6.0,
        min(device_x_origins_mm),
    )
    content_max_x_mm = max(
        sink_x_origin_mm + sink_width_mm,
        max(package_x_origin_mm + package_span_width_mm for package_x_origin_mm in device_x_origins_mm),
    )
    content_min_y_mm = sink_y_origin_mm - 6.5
    content_max_y_mm = max(
        sink_y_origin_mm + sink_footprint_depth_mm + 6.0,
        package_y_origin_mm + package_span_height_mm + 2.0,
    )
    top_band_bottom_y_mm = content_max_y_mm + _TOP_BAND_GAP_MM
    axis_xlim_mm = (
        content_min_x_mm - _CONTENT_LEFT_PAD_MM,
        content_max_x_mm + _CONTENT_RIGHT_PAD_MM,
    )
    axis_ylim_mm = (
        min(0.0, content_min_y_mm - _CONTENT_BOTTOM_PAD_MM),
        max(top_band_bottom_y_mm + _TOP_BAND_HEIGHT_MM + _CONTENT_TOP_PAD_MM, 42.0),
    )
    legend_center_x_mm = 0.5 * (axis_xlim_mm[0] + axis_xlim_mm[1])

    return SemiconductorGeometryScene(
        axis_xlim_mm=axis_xlim_mm,
        axis_ylim_mm=axis_ylim_mm,
        device_count=layout.parallel_count,
        device_x_origins_mm=device_x_origins_mm,
        thermal_anchor_xs_mm=thermal_anchor_xs_mm,
        package_body_center_xs_mm=package_body_center_xs_mm,
        top_band_bottom_y_mm=top_band_bottom_y_mm,
        sink_x_origin_mm=sink_x_origin_mm,
        sink_y_origin_mm=sink_y_origin_mm,
        sink_width_mm=sink_width_mm,
        sink_height_mm=sink_height_mm,
        sink_depth_mm=sink_depth_mm,
        sink_footprint_depth_mm=sink_footprint_depth_mm,
        sink_center_x_mm=sink_center_x_mm,
        sink_thermal_anchor_fraction_from_bottom=_THERMAL_ANCHOR_FRACTION_FROM_SINK_BOTTOM,
        package_x_origin_mm=device_x_origins_mm[0],
        package_y_origin_mm=package_y_origin_mm,
        package_span_width_mm=package_span_width_mm,
        package_span_height_mm=package_span_height_mm,
        package_body_x_mm=package_body_x_mm,
        package_body_y_mm=package_body_y_mm,
        package_body_width_mm=layout.package_body_width_mm,
        package_body_height_mm=layout.package_body_height_mm,
        package_body_center_x_mm=sum(package_body_center_xs_mm) / len(package_body_center_xs_mm),
        package_body_center_y_mm=package_body_center_y_mm,
        thermal_anchor_x_mm=sink_center_x_mm,
        thermal_anchor_y_mm=thermal_anchor_y_mm,
        lead_region_center_y_mm=lead_region_center_y_mm,
        content_min_x_mm=content_min_x_mm,
        content_max_x_mm=content_max_x_mm,
        content_max_y_mm=content_max_y_mm,
        legend_center_x_mm=legend_center_x_mm,
        legend_top_y_mm=axis_ylim_mm[1] - 2.0,
        legend_lines=_build_legend_lines(layout, sink_width_mm=sink_width_mm, sink_height_mm=sink_height_mm, sink_depth_mm=sink_depth_mm),
    )


def _render_semiconductor_axis(axis, layout: SemiconductorGeometryLayout, *, title: str) -> None:
    scene = build_semiconductor_geometry_scene(layout)
    axis.set_aspect("equal", adjustable="box")
    axis.axis("off")
    axis.set_xlim(*scene.axis_xlim_mm)
    axis.set_ylim(*scene.axis_ylim_mm)
    axis.set_title(title, fontsize=10.0, fontweight="bold", pad=4.0)

    _draw_sink(
        axis,
        layout,
        x_origin_mm=scene.sink_x_origin_mm,
        y_origin_mm=scene.sink_y_origin_mm,
        width_mm=scene.sink_width_mm,
        depth_mm=scene.sink_footprint_depth_mm,
    )
    for package_x_origin_mm in scene.device_x_origins_mm:
        _draw_package(axis, layout, x_origin_mm=package_x_origin_mm, y_origin_mm=scene.package_y_origin_mm)

    axis.set_xlabel("width (mm)", fontsize=8.0, color="#374151")
    axis.set_ylabel("depth (mm)", fontsize=8.0, color="#374151")

    dimension_origin_x_mm = scene.package_body_x_mm
    if scene.device_x_origins_mm:
        middle_index = len(scene.device_x_origins_mm) // 2
        dimension_origin_x_mm = scene.device_x_origins_mm[middle_index] + _package_body_offset_mm(layout)[0]

    _dimension_line(
        axis,
        scene.sink_x_origin_mm,
        scene.sink_x_origin_mm + scene.sink_width_mm,
        scene.sink_y_origin_mm - 3.2,
        f"sink W {scene.sink_width_mm:.3g} mm",
        vertical=False,
    )
    _dimension_line(
        axis,
        scene.sink_y_origin_mm,
        scene.sink_y_origin_mm + scene.sink_footprint_depth_mm,
        scene.sink_x_origin_mm - 3.0,
        f"sink D {scene.sink_footprint_depth_mm:.3g} mm",
        vertical=True,
    )
    _dimension_line(
        axis,
        dimension_origin_x_mm,
        dimension_origin_x_mm + scene.package_body_width_mm,
        scene.sink_y_origin_mm + scene.sink_footprint_depth_mm + 3.2,
        f"pkg W {scene.package_body_width_mm:.3g} mm",
        vertical=False,
    )
    _add_scale_bar(axis, layout.scale_bar_mm)

    axis.text(
        scene.legend_center_x_mm,
        scene.legend_top_y_mm,
        "\n".join(scene.legend_lines),
        va="top",
        ha="center",
        fontsize=8.4,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#ffffff", "edgecolor": "#d1d5db"},
    )


def _resolve_package_gap_mm(*, package_span_width_mm: float, parallel_count: int, sink_width_mm: float) -> float:
    if parallel_count <= 1:
        return 0.0
    target_gap_mm = max(3.0, 0.28 * package_span_width_mm)
    available_gap_mm = (
        0.88 * sink_width_mm - parallel_count * package_span_width_mm
    ) / max(parallel_count - 1, 1)
    return max(2.0, min(target_gap_mm, available_gap_mm if available_gap_mm > 0.0 else target_gap_mm))


def _package_span_width_mm(layout: SemiconductorGeometryLayout) -> float:
    if layout.renderer_template_id in _SIDE_LEADED_TOP_PACKAGES:
        return layout.package_body_width_mm + (2.0 * layout.lead_length_mm)
    return layout.package_body_width_mm


def _package_span_height_mm(layout: SemiconductorGeometryLayout) -> float:
    if layout.renderer_template_id in _MODULE_PACKAGES:
        return layout.package_body_height_mm
    if layout.renderer_template_id in _SIDE_LEADED_TOP_PACKAGES | _LEADLESS_TOP_PACKAGES:
        return layout.package_body_height_mm
    if layout.renderer_template_id == "generic_power_package":
        return layout.package_body_height_mm
    return layout.package_body_height_mm + layout.lead_length_mm


def _package_body_offset_mm(layout: SemiconductorGeometryLayout) -> tuple[float, float]:
    if layout.renderer_template_id in _MODULE_PACKAGES:
        return (0.0, 0.0)
    if layout.renderer_template_id in _SIDE_LEADED_TOP_PACKAGES:
        return (layout.lead_length_mm, 0.0)
    if layout.renderer_template_id in _LEADLESS_TOP_PACKAGES:
        return (0.0, 0.0)
    if layout.renderer_template_id == "generic_power_package":
        return (0.0, 0.0)
    return (0.0, layout.lead_length_mm)


def _thermal_anchor_offset_mm(layout: SemiconductorGeometryLayout) -> tuple[float, float]:
    body_offset_x_mm, body_offset_y_mm = _package_body_offset_mm(layout)
    if layout.renderer_template_id in _MODULE_PACKAGES:
        return (
            body_offset_x_mm + (0.5 * layout.package_body_width_mm),
            body_offset_y_mm + (0.22 * layout.package_body_height_mm),
        )
    if layout.renderer_template_id == "generic_power_package":
        return (
            body_offset_x_mm + (0.5 * layout.package_body_width_mm),
            body_offset_y_mm + (0.5 * layout.package_body_height_mm),
        )
    return (
        body_offset_x_mm + (0.5 * layout.package_body_width_mm),
        body_offset_y_mm + layout.package_body_height_mm - (0.5 * layout.package_tab_height_mm),
    )


def _build_legend_lines(
    layout: SemiconductorGeometryLayout,
    *,
    sink_width_mm: float,
    sink_height_mm: float,
    sink_depth_mm: float,
) -> tuple[str, str, str, str]:
    sink_dims_text = (
        f"{sink_width_mm:.3g} x {sink_height_mm:.3g} x {sink_depth_mm:.3g} mm"
        if layout.sink_width_mm is not None and layout.sink_height_mm is not None and layout.sink_depth_mm is not None
        else "-"
    )
    return (
        f"Device: {layout.part_number}",
        f"Package: {layout.package}",
        f"Sink size: {sink_dims_text}",
        f"Sink volume: {_fmt_optional(layout.sink_volume_cm3, 'cm^3')}",
    )


def _draw_sink(axis, layout: SemiconductorGeometryLayout, *, x_origin_mm: float, y_origin_mm: float, width_mm: float, depth_mm: float) -> None:
    axis.add_patch(
        Rectangle(
            (x_origin_mm, y_origin_mm),
            width_mm,
            depth_mm,
            facecolor="#d9dde6",
            edgecolor="#111827",
            linewidth=1.4,
        )
    )
    if layout.sink_fin_count <= 0:
        return
    fin_margin_mm = 0.12 * width_mm
    fin_region_width_mm = max(width_mm - (2.0 * fin_margin_mm), 1.0)
    fin_pitch_mm = fin_region_width_mm / max(layout.sink_fin_count - 1, 1)
    fin_height_mm = 0.42 * depth_mm
    for index in range(layout.sink_fin_count):
        x_mm = x_origin_mm + fin_margin_mm + (index * fin_pitch_mm)
        axis.plot(
            [x_mm, x_mm],
            [y_origin_mm + depth_mm - fin_height_mm, y_origin_mm + depth_mm],
            color="#6b7280",
            linewidth=1.0,
        )


def _draw_package(axis, layout: SemiconductorGeometryLayout, *, x_origin_mm: float, y_origin_mm: float) -> None:
    if layout.renderer_template_id == "module_half_bridge":
        _draw_power_module(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="Half-Bridge Module", terminal_count=6)
        return
    if layout.renderer_template_id == "module_flat_baseplate":
        _draw_power_module(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="Flat-Baseplate Module", terminal_count=6, flat_baseplate=True)
        return
    if layout.renderer_template_id == "module_single_switch":
        _draw_power_module(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="Single-Switch Module", terminal_count=4)
        return
    if layout.renderer_template_id == "module_six_pack":
        _draw_power_module(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="Six-Pack Module", terminal_count=12, direct_cooling=True)
        return
    if layout.renderer_template_id in {"to220_3_tht", "to247_2_tht", "to247_3_tht", "to247_4_tht"}:
        _draw_tabbed_tht_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm)
        return
    if layout.renderer_template_id == "to252_3_dpak":
        _draw_dpak_to252_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm)
        return
    if layout.renderer_template_id == "to263_7_d2pak":
        _draw_bottom_leaded_power_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-TO263-7")
        return
    if layout.renderer_template_id == "hdsop_10_top":
        _draw_hdsop_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-HDSOP-10")
        return
    if layout.renderer_template_id == "hdsop_16_top":
        _draw_hdsop_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-HDSOP-16")
        return
    if layout.renderer_template_id == "hdsop_22_top":
        _draw_hdsop_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-HDSOP-22")
        return
    if layout.renderer_template_id == "dso_20_top":
        _draw_hdsop_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-DSO-20")
        return
    if layout.renderer_template_id == "hsof_8_top":
        _draw_bottom_leaded_power_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-HSOF-8")
        return
    if layout.renderer_template_id == "tson_8_top":
        _draw_leadless_power_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-TSON-8")
        return
    if layout.renderer_template_id == "lson_8_top":
        _draw_leadless_power_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-LSON-8")
        return
    if layout.renderer_template_id == "lhsof_4_top":
        _draw_bottom_leaded_power_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="PG-LHSOF-4")
        return
    if layout.renderer_template_id == "thinpak_8x8_top":
        _draw_bottom_leaded_power_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm, label="ThinPAK 8x8")
        return
    _draw_generic_power_package(axis, layout, x_origin_mm=x_origin_mm, y_origin_mm=y_origin_mm)


def _draw_power_module(
    axis,
    layout: SemiconductorGeometryLayout,
    *,
    x_origin_mm: float,
    y_origin_mm: float,
    label: str,
    terminal_count: int,
    flat_baseplate: bool = False,
    direct_cooling: bool = False,
) -> None:
    body_width_mm = layout.package_body_width_mm
    body_height_mm = layout.package_body_height_mm
    baseplate_height_mm = max(4.0, 0.12 * body_height_mm)
    axis.add_patch(
        Rectangle(
            (x_origin_mm, y_origin_mm),
            body_width_mm,
            body_height_mm,
            facecolor="#dbeafe",
            edgecolor="#1d4ed8",
            linewidth=1.4,
        )
    )
    axis.add_patch(
        Rectangle(
            (x_origin_mm, y_origin_mm),
            body_width_mm,
            baseplate_height_mm,
            facecolor="#cbd5e1" if not direct_cooling else "#bae6fd",
            edgecolor="#334155",
            linewidth=1.0,
        )
    )
    if flat_baseplate or direct_cooling:
        axis.plot(
            [x_origin_mm + 0.06 * body_width_mm, x_origin_mm + 0.94 * body_width_mm],
            [y_origin_mm + baseplate_height_mm, y_origin_mm + baseplate_height_mm],
            color="#475569",
            linewidth=1.0,
            linestyle="--" if flat_baseplate else "-",
        )

    terminal_block_width_mm = min(max(layout.package_tab_width_mm, 6.0), 0.18 * body_width_mm)
    terminal_block_height_mm = min(max(layout.package_tab_height_mm, 5.0), 0.16 * body_height_mm)
    terminal_rows = 2 if terminal_count >= 8 else 1
    terminals_per_row = max(terminal_count // terminal_rows, 1)
    usable_width_mm = body_width_mm - (2.0 * terminal_block_width_mm)
    terminal_pitch_mm = usable_width_mm / max(terminals_per_row - 1, 1)
    for row in range(terminal_rows):
        y_mm = y_origin_mm + body_height_mm - ((row + 1) * (terminal_block_height_mm + 3.0))
        for index in range(terminals_per_row):
            x_mm = x_origin_mm + terminal_block_width_mm + (index * terminal_pitch_mm)
            axis.add_patch(
                Rectangle(
                    (x_mm - (0.5 * terminal_block_width_mm), y_mm),
                    terminal_block_width_mm,
                    terminal_block_height_mm,
                    facecolor="#93c5fd",
                    edgecolor="#1d4ed8",
                    linewidth=0.9,
                )
            )

    hole_radius_mm = max(0.5 * layout.package_hole_diameter_mm, 1.8)
    for x_mm in (x_origin_mm + 0.1 * body_width_mm, x_origin_mm + 0.9 * body_width_mm):
        axis.add_patch(
            Circle(
                (x_mm, y_origin_mm + 0.5 * baseplate_height_mm),
                hole_radius_mm,
                facecolor="#ffffff",
                edgecolor="#475569",
                linewidth=0.9,
            )
        )

    axis.text(
        x_origin_mm + 0.5 * body_width_mm,
        y_origin_mm + 0.58 * body_height_mm,
        label,
        ha="center",
        va="center",
        fontsize=7.0,
        color="#1e3a8a",
    )
    axis.text(
        x_origin_mm + 0.5 * body_width_mm,
        y_origin_mm + 0.28 * body_height_mm,
        layout.package,
        ha="center",
        va="center",
        fontsize=6.2,
        color="#1f2937",
    )


def _draw_tabbed_tht_package(axis, layout: SemiconductorGeometryLayout, *, x_origin_mm: float, y_origin_mm: float) -> None:
    body_y_mm = y_origin_mm + layout.lead_length_mm
    tab_height_mm = layout.package_tab_height_mm
    body_height_mm = layout.package_body_height_mm
    body_width_mm = layout.package_body_width_mm
    body_without_tab_mm = max(body_height_mm - tab_height_mm, 1.0)
    axis.add_patch(
        Rectangle(
            (x_origin_mm, body_y_mm),
            body_width_mm,
            body_without_tab_mm,
            facecolor="#9ec5fe",
            edgecolor="#1d4ed8",
            linewidth=1.3,
        )
    )
    axis.add_patch(
        Rectangle(
            (x_origin_mm, body_y_mm + body_without_tab_mm),
            layout.package_tab_width_mm,
            tab_height_mm,
            facecolor="#bfdbfe",
            edgecolor="#1d4ed8",
            linewidth=1.1,
        )
    )
    if layout.package_hole_diameter_mm > 0.0:
        hole_center_x_mm = x_origin_mm + (0.5 * layout.package_tab_width_mm)
        hole_center_y_mm = body_y_mm + body_without_tab_mm + (0.45 * tab_height_mm)
        axis.add_patch(
            Circle(
                (hole_center_x_mm, hole_center_y_mm),
                0.5 * layout.package_hole_diameter_mm,
                facecolor="#ffffff",
                edgecolor="#1f2937",
                linewidth=1.0,
            )
        )

    lead_span_mm = max((layout.package_lead_count - 1) * layout.lead_pitch_mm, 0.0)
    lead_start_x_mm = x_origin_mm + (0.5 * (body_width_mm - lead_span_mm))
    lead_top_y_mm = body_y_mm
    lead_bottom_y_mm = max(y_origin_mm, 0.5)
    for index in range(layout.package_lead_count):
        x_mm = lead_start_x_mm + (index * layout.lead_pitch_mm)
        axis.add_patch(
            Rectangle(
                (x_mm - (0.5 * layout.lead_width_mm), lead_bottom_y_mm),
                layout.lead_width_mm,
                lead_top_y_mm - lead_bottom_y_mm,
                facecolor="#9ca3af",
                edgecolor="#4b5563",
                linewidth=0.8,
            )
        )


def _draw_dpak_to252_package(axis, layout: SemiconductorGeometryLayout, *, x_origin_mm: float, y_origin_mm: float) -> None:
    """Draw a simplified PG-TO252-3 / DPAK top-view package."""

    body_width_mm = layout.package_body_width_mm
    body_height_mm = layout.package_body_height_mm
    lead_length_mm = layout.lead_length_mm
    lead_width_mm = layout.lead_width_mm
    lead_pitch_mm = layout.lead_pitch_mm
    lead_top_y_mm = y_origin_mm + lead_length_mm
    lead_bottom_y_mm = y_origin_mm
    foot_length_mm = min(1.25, max(0.55 * lead_length_mm, 0.8))
    foot_height_mm = max(0.32 * lead_width_mm, 0.22)

    lead_span_mm = 2.0 * lead_pitch_mm
    lead_start_x_mm = x_origin_mm + (0.5 * (body_width_mm - lead_span_mm))
    for index in range(3):
        x_mm = lead_start_x_mm + (index * lead_pitch_mm)
        axis.add_patch(
            Rectangle(
                (x_mm - (0.5 * lead_width_mm), lead_bottom_y_mm + foot_height_mm),
                lead_width_mm,
                lead_top_y_mm - lead_bottom_y_mm - foot_height_mm,
                facecolor="#9ca3af",
                edgecolor="#4b5563",
                linewidth=0.8,
            )
        )
        axis.add_patch(
            Rectangle(
                (x_mm - (0.5 * foot_length_mm), lead_bottom_y_mm),
                foot_length_mm,
                foot_height_mm,
                facecolor="#9ca3af",
                edgecolor="#4b5563",
                linewidth=0.8,
            )
        )

    axis.add_patch(
        Rectangle(
            (x_origin_mm, lead_top_y_mm),
            body_width_mm,
            body_height_mm,
            facecolor="#9ec5fe",
            edgecolor="#1d4ed8",
            linewidth=1.3,
        )
    )

    tab_width_mm = min(layout.package_tab_width_mm, body_width_mm - 0.45)
    tab_height_mm = min(layout.package_tab_height_mm, 0.48 * body_height_mm)
    tab_x_mm = x_origin_mm + 0.5 * (body_width_mm - tab_width_mm)
    tab_y_mm = lead_top_y_mm + body_height_mm - tab_height_mm - 0.35
    axis.add_patch(
        Rectangle(
            (tab_x_mm, tab_y_mm),
            tab_width_mm,
            tab_height_mm,
            facecolor="#bfdbfe",
            edgecolor="#1d4ed8",
            linewidth=1.0,
        )
    )
    axis.text(
        x_origin_mm + 0.5 * body_width_mm,
        tab_y_mm + 0.5 * tab_height_mm,
        "drain tab",
        ha="center",
        va="center",
        fontsize=6.8,
        color="#1e3a8a",
    )
    axis.text(
        x_origin_mm + 0.5 * body_width_mm,
        lead_top_y_mm + 0.18 * body_height_mm,
        "DPAK / TO-252",
        ha="center",
        va="center",
        fontsize=6.8,
        color="#1e3a8a",
    )


def _draw_hdsop_package(axis, layout: SemiconductorGeometryLayout, *, x_origin_mm: float, y_origin_mm: float, label: str) -> None:
    body_x_mm = x_origin_mm + layout.lead_length_mm
    body_y_mm = y_origin_mm
    body_width_mm = layout.package_body_width_mm
    body_height_mm = layout.package_body_height_mm
    leads_per_side = max(layout.package_lead_count // 2, 1)
    used_span_mm = min((leads_per_side - 1) * layout.lead_pitch_mm, 0.82 * body_height_mm)
    lead_start_y_mm = body_y_mm + 0.5 * (body_height_mm - used_span_mm)

    axis.add_patch(
        Rectangle(
            (body_x_mm, body_y_mm),
            body_width_mm,
            body_height_mm,
            facecolor="#dbeafe",
            edgecolor="#1d4ed8",
            linewidth=1.2,
        )
    )

    for side_sign in (-1.0, 1.0):
        for index in range(leads_per_side):
            y_mm = lead_start_y_mm + (index * (used_span_mm / max(leads_per_side - 1, 1)))
            lead_x_mm = body_x_mm - layout.lead_length_mm if side_sign < 0.0 else body_x_mm + body_width_mm
            axis.add_patch(
                Rectangle(
                    (lead_x_mm, y_mm - (0.5 * layout.lead_width_mm)),
                    layout.lead_length_mm,
                    layout.lead_width_mm,
                    facecolor="#9ca3af",
                    edgecolor="#4b5563",
                    linewidth=0.7,
                )
            )

    pad_width_mm = min(layout.package_tab_width_mm, 0.78 * body_width_mm)
    pad_height_mm = min(layout.package_tab_height_mm, 0.42 * body_height_mm)
    pad_x_mm = body_x_mm + 0.5 * (body_width_mm - pad_width_mm)
    pad_y_mm = body_y_mm + body_height_mm - pad_height_mm - 0.4
    axis.add_patch(
        Rectangle(
            (pad_x_mm, pad_y_mm),
            pad_width_mm,
            pad_height_mm,
            facecolor="#bfdbfe",
            edgecolor="#1d4ed8",
            linewidth=1.0,
        )
    )
    axis.text(
        body_x_mm + 0.5 * body_width_mm,
        body_y_mm + 0.25 * body_height_mm,
        label,
        ha="center",
        va="center",
        fontsize=6.5,
        color="#1e3a8a",
    )
    axis.text(
        body_x_mm + 0.5 * body_width_mm,
        pad_y_mm + 0.5 * pad_height_mm,
        "drain pad",
        ha="center",
        va="center",
        fontsize=6.3,
        color="#1e3a8a",
    )


def _draw_bottom_leaded_power_package(axis, layout: SemiconductorGeometryLayout, *, x_origin_mm: float, y_origin_mm: float, label: str) -> None:
    body_y_mm = y_origin_mm + layout.lead_length_mm
    body_width_mm = layout.package_body_width_mm
    body_height_mm = layout.package_body_height_mm
    axis.add_patch(
        Rectangle(
            (x_origin_mm, body_y_mm),
            body_width_mm,
            body_height_mm,
            facecolor="#dbeafe",
            edgecolor="#1d4ed8",
            linewidth=1.2,
        )
    )

    lead_span_mm = min((layout.package_lead_count - 1) * layout.lead_pitch_mm, 0.82 * body_width_mm)
    lead_start_x_mm = x_origin_mm + 0.5 * (body_width_mm - lead_span_mm)
    for index in range(layout.package_lead_count):
        x_mm = lead_start_x_mm + (index * (lead_span_mm / max(layout.package_lead_count - 1, 1)))
        axis.add_patch(
            Rectangle(
                (x_mm - (0.5 * layout.lead_width_mm), y_origin_mm),
                layout.lead_width_mm,
                layout.lead_length_mm,
                facecolor="#9ca3af",
                edgecolor="#4b5563",
                linewidth=0.7,
            )
        )

    tab_width_mm = min(layout.package_tab_width_mm, 0.78 * body_width_mm)
    tab_height_mm = min(layout.package_tab_height_mm, 0.40 * body_height_mm)
    tab_x_mm = x_origin_mm + 0.5 * (body_width_mm - tab_width_mm)
    tab_y_mm = body_y_mm + body_height_mm - tab_height_mm - 0.35
    axis.add_patch(
        Rectangle(
            (tab_x_mm, tab_y_mm),
            tab_width_mm,
            tab_height_mm,
            facecolor="#bfdbfe",
            edgecolor="#1d4ed8",
            linewidth=1.0,
        )
    )
    axis.text(
        x_origin_mm + 0.5 * body_width_mm,
        body_y_mm + 0.25 * body_height_mm,
        label,
        ha="center",
        va="center",
        fontsize=6.5,
        color="#1e3a8a",
    )
    axis.text(
        x_origin_mm + 0.5 * body_width_mm,
        tab_y_mm + 0.5 * tab_height_mm,
        "drain tab",
        ha="center",
        va="center",
        fontsize=6.3,
        color="#1e3a8a",
    )


def _draw_leadless_power_package(axis, layout: SemiconductorGeometryLayout, *, x_origin_mm: float, y_origin_mm: float, label: str) -> None:
    body_width_mm = layout.package_body_width_mm
    body_height_mm = layout.package_body_height_mm
    axis.add_patch(
        Rectangle(
            (x_origin_mm, y_origin_mm),
            body_width_mm,
            body_height_mm,
            facecolor="#dbeafe",
            edgecolor="#1d4ed8",
            linewidth=1.2,
        )
    )

    tab_width_mm = min(layout.package_tab_width_mm, 0.75 * body_width_mm)
    tab_height_mm = min(layout.package_tab_height_mm, 0.44 * body_height_mm)
    tab_x_mm = x_origin_mm + 0.5 * (body_width_mm - tab_width_mm)
    tab_y_mm = y_origin_mm + body_height_mm - tab_height_mm - 0.25
    axis.add_patch(
        Rectangle(
            (tab_x_mm, tab_y_mm),
            tab_width_mm,
            tab_height_mm,
            facecolor="#bfdbfe",
            edgecolor="#1d4ed8",
            linewidth=1.0,
        )
    )

    pads_per_side = max(layout.package_lead_count // 2, 1)
    used_span_mm = min((pads_per_side - 1) * layout.lead_pitch_mm, 0.76 * body_height_mm)
    pad_start_y_mm = y_origin_mm + 0.5 * (body_height_mm - used_span_mm)
    pad_length_mm = max(0.45, min(layout.lead_length_mm, 0.9))
    for side_sign in (-1.0, 1.0):
        pad_x_mm = x_origin_mm - pad_length_mm if side_sign < 0.0 else x_origin_mm + body_width_mm
        for index in range(pads_per_side):
            y_mm = pad_start_y_mm + (index * (used_span_mm / max(pads_per_side - 1, 1)))
            axis.add_patch(
                Rectangle(
                    (pad_x_mm, y_mm - (0.5 * layout.lead_width_mm)),
                    pad_length_mm,
                    layout.lead_width_mm,
                    facecolor="#9ca3af",
                    edgecolor="#4b5563",
                    linewidth=0.7,
                )
            )

    axis.text(
        x_origin_mm + 0.5 * body_width_mm,
        y_origin_mm + 0.26 * body_height_mm,
        label,
        ha="center",
        va="center",
        fontsize=6.4,
        color="#1e3a8a",
    )
    axis.text(
        x_origin_mm + 0.5 * body_width_mm,
        tab_y_mm + 0.5 * tab_height_mm,
        "source pad",
        ha="center",
        va="center",
        fontsize=6.1,
        color="#1e3a8a",
    )


def _draw_generic_power_package(axis, layout: SemiconductorGeometryLayout, *, x_origin_mm: float, y_origin_mm: float) -> None:
    axis.add_patch(
        Rectangle(
            (x_origin_mm, y_origin_mm),
            layout.package_body_width_mm,
            layout.package_body_height_mm,
            facecolor="#e5e7eb",
            edgecolor="#374151",
            linewidth=1.2,
        )
    )
    axis.plot(
        [x_origin_mm, x_origin_mm + layout.package_body_width_mm],
        [y_origin_mm, y_origin_mm + layout.package_body_height_mm],
        color="#6b7280",
        linewidth=1.0,
    )
    axis.plot(
        [x_origin_mm, x_origin_mm + layout.package_body_width_mm],
        [y_origin_mm + layout.package_body_height_mm, y_origin_mm],
        color="#6b7280",
        linewidth=1.0,
    )
    axis.text(
        x_origin_mm + 0.5 * layout.package_body_width_mm,
        y_origin_mm + 0.5 * layout.package_body_height_mm,
        "unsupported\npackage",
        ha="center",
        va="center",
        fontsize=6.6,
        color="#374151",
    )


def _dimension_line(axis, start: float, end: float, offset: float, label: str, *, vertical: bool) -> None:
    if vertical:
        axis.annotate(
            "",
            xy=(offset, start),
            xytext=(offset, end),
            arrowprops={"arrowstyle": "<->", "linewidth": 0.9, "color": "#4b5563"},
        )
        axis.text(offset - 0.4, 0.5 * (start + end), label, rotation=90, va="center", ha="right", fontsize=7.8, color="#374151")
    else:
        axis.annotate(
            "",
            xy=(start, offset),
            xytext=(end, offset),
            arrowprops={"arrowstyle": "<->", "linewidth": 0.9, "color": "#4b5563"},
        )
        axis.text(0.5 * (start + end), offset - 0.4, label, va="top", ha="center", fontsize=7.8, color="#374151")


def _add_scale_bar(axis, scale_bar_mm: float) -> None:
    x0, x1 = axis.get_xlim()
    y0, y1 = axis.get_ylim()
    start_x = x0 + 0.08 * (x1 - x0)
    y = y0 + 0.10 * (y1 - y0)
    axis.plot([start_x, start_x + scale_bar_mm], [y, y], color="#111827", linewidth=2.2, solid_capstyle="butt")
    axis.plot([start_x, start_x], [y - 0.35, y + 0.35], color="#111827", linewidth=1.2)
    axis.plot([start_x + scale_bar_mm, start_x + scale_bar_mm], [y - 0.35, y + 0.35], color="#111827", linewidth=1.2)
    axis.text(start_x + 0.5 * scale_bar_mm, y + 0.7, f"{scale_bar_mm:.3g} mm", ha="center", va="bottom", fontsize=8, color="#111827")


def _fmt_optional(value: float | None, unit: str) -> str:
    if value is None:
        return "-"
    return f"{value:.3g} {unit}"
