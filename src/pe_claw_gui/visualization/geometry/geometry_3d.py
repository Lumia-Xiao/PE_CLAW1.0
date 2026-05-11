"""Static Matplotlib 3D engineering renderer for selected magnetic designs."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ...models.geometry_result import InductorGeometryLayout
from .primitives_3d import add_box_3d, add_box_outline_3d, configure_engineering_3d_axis, set_equal_physical_box_aspect

_OUTPUT_SUBDIR = Path("outputs") / "inductor_design"
_CORE_FACE = "#cfd4dd"
_CORE_FACE_ALT = "#bcc6d4"
_CORE_EDGE = "#1f2937"
_WINDING_FACE = "#60a5fa"
_WINDING_EDGE = "#1d4ed8"
_GAP_FACE = "#ef4444"
_SEAM_EDGE = "#6b7280"


def create_geometry_figure_3d(
    layout: InductorGeometryLayout,
    *,
    comparison_settings: dict[str, float] | None = None,
) -> Figure:
    """Create a static 3D engineering figure for the selected magnetic design."""
    figure = Figure(figsize=(8.6, 6.0), dpi=120)
    axis = figure.add_subplot(111, projection="3d")
    resolved_settings = comparison_settings or resolve_3d_comparison_settings([layout])
    axis.view_init(elev=resolved_settings["elev"], azim=resolved_settings["azim"])
    axis.set_proj_type("persp")

    if layout.template_name == "toroid_ring":
        _draw_toroid_stack(axis, layout)
    elif layout.template_name == "u_paired_core":
        _draw_u_stack(axis, layout)
    elif layout.template_name == "paired_etd_core":
        _draw_paired_box_stack(axis, layout, etd_style=True)
    elif layout.template_name == "paired_box_core":
        _draw_paired_box_stack(axis, layout, etd_style=False)
    else:
        _draw_box_window_stack(axis, layout)

    _draw_winding_block(axis, layout)
    _annotate_3d_view(axis, layout)
    _configure_axis(axis, layout, comparison_settings=resolved_settings)
    figure.tight_layout(pad=0.8)
    return figure


def resolve_3d_comparison_settings(layouts: list[InductorGeometryLayout]) -> dict[str, float]:
    """Resolve one shared physical 3D comparison extent and camera basis."""
    if not layouts:
        return {
            "content_span_x_mm": 40.0,
            "content_span_y_mm": 40.0,
            "content_span_z_mm": 24.0,
            "pad_x_mm": 4.8,
            "pad_y_mm": 5.6,
            "pad_z_mm": 4.32,
            "total_span_x_mm": 49.6,
            "total_span_y_mm": 51.2,
            "total_span_z_mm": 32.64,
            "elev": 24.0,
            "azim": -56.0,
        }

    content_span_x_mm = max(layout.overall_width_mm for layout in layouts)
    content_span_y_mm = max(layout.overall_height_mm for layout in layouts)
    content_span_z_mm = max(max(layout.overall_depth_mm, layout.outer_depth_mm) for layout in layouts)
    pad_x_mm = max(0.12 * content_span_x_mm, 4.0)
    pad_y_mm = max(0.14 * content_span_y_mm, 4.0)
    pad_z_mm = max(0.18 * content_span_z_mm, 4.0)
    return {
        "content_span_x_mm": content_span_x_mm,
        "content_span_y_mm": content_span_y_mm,
        "content_span_z_mm": content_span_z_mm,
        "pad_x_mm": pad_x_mm,
        "pad_y_mm": pad_y_mm,
        "pad_z_mm": pad_z_mm,
        "total_span_x_mm": content_span_x_mm + (2.0 * pad_x_mm),
        "total_span_y_mm": content_span_y_mm + (2.0 * pad_y_mm),
        "total_span_z_mm": content_span_z_mm + (2.0 * pad_z_mm),
        "elev": 24.0,
        "azim": -56.0,
    }


def export_geometry_3d_artifacts(
    layout: InductorGeometryLayout,
    output_dir: Path | None = None,
    basename: str = "geometry_selected_3d",
) -> list[str]:
    """Persist static 3D PNG/SVG artifacts for the selected geometry layout."""
    output_root = Path(output_dir or _project_root() / _OUTPUT_SUBDIR)
    output_root.mkdir(parents=True, exist_ok=True)
    figure = create_geometry_figure_3d(layout)
    png_path = output_root / f"{basename}.png"
    svg_path = output_root / f"{basename}.svg"
    try:
        figure.savefig(png_path, bbox_inches="tight")
        figure.savefig(svg_path, bbox_inches="tight")
    finally:
        figure.clear()
    return [str(png_path), str(svg_path)]


def _draw_paired_box_stack(axis, layout: InductorGeometryLayout, *, etd_style: bool) -> None:
    width_mm = layout.outer_width_mm
    height_mm = layout.outer_height_mm
    half_height_mm = 0.5 * height_mm
    side_leg_mm = layout.side_leg_width_mm or max(0.14 * width_mm, 0.5 * (width_mm - layout.core_window_width_mm))
    center_leg_mm = layout.center_leg_width_mm or (0.18 * width_mm)
    yoke_mm = layout.top_yoke_height_mm or max(0.14 * half_height_mm, 0.5 * (height_mm - layout.core_window_height_mm))
    shoulder_inset_mm = max(0.08 * width_mm, 0.34 * side_leg_mm)
    shoulder_rise_mm = max(0.18 * half_height_mm, 0.20 * layout.core_window_height_mm)
    gap_mm = max(layout.gap_mm or 0.0, 0.15)

    for body_index, (z0_mm, z1_mm) in enumerate(_body_depth_ranges(layout)):
        depth_mm = z1_mm - z0_mm
        lower_face = _CORE_FACE if body_index % 2 == 0 else _CORE_FACE_ALT
        upper_face = _CORE_FACE_ALT if body_index % 2 == 0 else _CORE_FACE

        _add_box(axis, 0.0, 0.0, z0_mm, width_mm, yoke_mm, depth_mm, facecolor=lower_face)
        _add_box(axis, 0.0, yoke_mm, z0_mm, side_leg_mm, half_height_mm - yoke_mm, depth_mm, facecolor=lower_face)
        _add_box(axis, width_mm - side_leg_mm, yoke_mm, z0_mm, side_leg_mm, half_height_mm - yoke_mm, depth_mm, facecolor=lower_face)
        _add_box(
            axis,
            0.5 * width_mm - 0.5 * center_leg_mm,
            yoke_mm,
            z0_mm,
            center_leg_mm,
            half_height_mm - yoke_mm,
            depth_mm,
            facecolor="#b7c1cf",
        )

        if etd_style:
            _add_box(axis, 0.0, half_height_mm - shoulder_rise_mm, z0_mm, shoulder_inset_mm, shoulder_rise_mm, depth_mm, facecolor=lower_face)
            _add_box(
                axis,
                width_mm - shoulder_inset_mm,
                half_height_mm - shoulder_rise_mm,
                z0_mm,
                shoulder_inset_mm,
                shoulder_rise_mm,
                depth_mm,
                facecolor=lower_face,
            )

        _add_box(axis, 0.0, height_mm - yoke_mm, z0_mm, width_mm, yoke_mm, depth_mm, facecolor=upper_face)
        _add_box(axis, 0.0, half_height_mm, z0_mm, side_leg_mm, half_height_mm - yoke_mm, depth_mm, facecolor=upper_face)
        _add_box(axis, width_mm - side_leg_mm, half_height_mm, z0_mm, side_leg_mm, half_height_mm - yoke_mm, depth_mm, facecolor=upper_face)
        _add_box(
            axis,
            0.5 * width_mm - 0.5 * center_leg_mm,
            half_height_mm,
            z0_mm,
            center_leg_mm,
            half_height_mm - yoke_mm,
            depth_mm,
            facecolor="#b7c1cf",
        )

        if etd_style:
            _add_box(axis, 0.0, half_height_mm, z0_mm, shoulder_inset_mm, shoulder_rise_mm, depth_mm, facecolor=upper_face)
            _add_box(
                axis,
                width_mm - shoulder_inset_mm,
                half_height_mm,
                z0_mm,
                shoulder_inset_mm,
                shoulder_rise_mm,
                depth_mm,
                facecolor=upper_face,
            )

        if layout.gap_mm is not None:
            _add_box(
                axis,
                0.5 * width_mm - 0.5 * center_leg_mm,
                half_height_mm - 0.5 * gap_mm,
                z0_mm + 0.08 * depth_mm,
                center_leg_mm,
                gap_mm,
                0.84 * depth_mm,
                facecolor=_GAP_FACE,
                edgecolor="#b91c1c",
                alpha=0.88,
            )

        if body_index < layout.stack_count - 1:
            _add_stack_seam(axis, width_mm, height_mm, z1_mm)


def _draw_u_stack(axis, layout: InductorGeometryLayout) -> None:
    width_mm = layout.outer_width_mm
    height_mm = layout.outer_height_mm
    half_height_mm = 0.5 * height_mm
    leg_width_mm = layout.side_leg_width_mm or max(0.14 * width_mm, 0.5 * (width_mm - layout.core_window_width_mm))
    yoke_mm = layout.top_yoke_height_mm or max(0.16 * half_height_mm, 0.5 * (height_mm - layout.core_window_height_mm))
    gap_mm = max(layout.gap_mm or 0.0, 0.15)
    window_width_mm = width_mm - (2.0 * leg_width_mm)

    for body_index, (z0_mm, z1_mm) in enumerate(_body_depth_ranges(layout)):
        depth_mm = z1_mm - z0_mm
        lower_face = _CORE_FACE if body_index % 2 == 0 else _CORE_FACE_ALT
        upper_face = _CORE_FACE_ALT if body_index % 2 == 0 else _CORE_FACE

        _add_box(axis, 0.0, 0.0, z0_mm, width_mm, yoke_mm, depth_mm, facecolor=lower_face)
        _add_box(axis, 0.0, yoke_mm, z0_mm, leg_width_mm, half_height_mm - yoke_mm, depth_mm, facecolor=lower_face)
        _add_box(axis, width_mm - leg_width_mm, yoke_mm, z0_mm, leg_width_mm, half_height_mm - yoke_mm, depth_mm, facecolor=lower_face)

        _add_box(axis, 0.0, height_mm - yoke_mm, z0_mm, width_mm, yoke_mm, depth_mm, facecolor=upper_face)
        _add_box(axis, 0.0, half_height_mm, z0_mm, leg_width_mm, half_height_mm - yoke_mm, depth_mm, facecolor=upper_face)
        _add_box(axis, width_mm - leg_width_mm, half_height_mm, z0_mm, leg_width_mm, half_height_mm - yoke_mm, depth_mm, facecolor=upper_face)

        if layout.gap_mm is not None:
            _add_box(
                axis,
                leg_width_mm,
                half_height_mm - 0.5 * gap_mm,
                z0_mm + 0.08 * depth_mm,
                window_width_mm,
                gap_mm,
                0.84 * depth_mm,
                facecolor=_GAP_FACE,
                edgecolor="#b91c1c",
                alpha=0.88,
            )

        if body_index < layout.stack_count - 1:
            _add_stack_seam(axis, width_mm, height_mm, z1_mm)


def _draw_box_window_stack(axis, layout: InductorGeometryLayout) -> None:
    width_mm = layout.outer_width_mm
    height_mm = layout.outer_height_mm
    side_leg_mm = layout.side_leg_width_mm or max(0.14 * width_mm, 0.5 * (width_mm - layout.core_window_width_mm))
    center_leg_mm = layout.center_leg_width_mm or (0.18 * width_mm)
    yoke_mm = layout.top_yoke_height_mm or max(0.16 * height_mm, 0.5 * (height_mm - layout.core_window_height_mm))
    leg_height_mm = max(height_mm - (2.0 * yoke_mm), 0.35 * height_mm)

    for body_index, (z0_mm, z1_mm) in enumerate(_body_depth_ranges(layout)):
        depth_mm = z1_mm - z0_mm
        face = _CORE_FACE if body_index % 2 == 0 else _CORE_FACE_ALT
        _add_box(axis, 0.0, 0.0, z0_mm, width_mm, yoke_mm, depth_mm, facecolor=face)
        _add_box(axis, 0.0, height_mm - yoke_mm, z0_mm, width_mm, yoke_mm, depth_mm, facecolor=face)
        _add_box(axis, 0.0, yoke_mm, z0_mm, side_leg_mm, leg_height_mm, depth_mm, facecolor=face)
        _add_box(axis, width_mm - side_leg_mm, yoke_mm, z0_mm, side_leg_mm, leg_height_mm, depth_mm, facecolor=face)
        _add_box(
            axis,
            0.5 * width_mm - 0.5 * center_leg_mm,
            yoke_mm,
            z0_mm,
            center_leg_mm,
            leg_height_mm,
            depth_mm,
            facecolor="#b7c1cf",
        )
        if body_index < layout.stack_count - 1:
            _add_stack_seam(axis, width_mm, height_mm, z1_mm)


def _draw_toroid_stack(axis, layout: InductorGeometryLayout) -> None:
    outer_radius_mm = 0.5 * layout.outer_width_mm
    inner_radius_mm = 0.5 * layout.core_window_width_mm
    major_radius_mm = 0.5 * (outer_radius_mm + inner_radius_mm)
    radial_radius_mm = max(0.5 * (outer_radius_mm - inner_radius_mm), 0.4)
    axial_radius_mm = 0.5 * layout.outer_depth_mm
    center_x_mm = 0.5 * layout.outer_width_mm
    center_y_mm = 0.5 * layout.outer_height_mm

    theta = np.linspace(0.0, 2.0 * math.pi, 52)
    phi = np.linspace(0.0, 2.0 * math.pi, 28)
    theta_grid, phi_grid = np.meshgrid(theta, phi)

    for body_index, (z0_mm, z1_mm) in enumerate(_body_depth_ranges(layout)):
        center_z_mm = 0.5 * (z0_mm + z1_mm)
        radial_term = major_radius_mm + (radial_radius_mm * np.cos(phi_grid))
        x_grid = center_x_mm + (radial_term * np.cos(theta_grid))
        y_grid = center_y_mm + (radial_term * np.sin(theta_grid))
        z_grid = center_z_mm + (axial_radius_mm * np.sin(phi_grid))
        axis.plot_surface(
            x_grid,
            y_grid,
            z_grid,
            rstride=1,
            cstride=1,
            linewidth=0.25,
            antialiased=True,
            color=_CORE_FACE if body_index % 2 == 0 else _CORE_FACE_ALT,
            edgecolor=_CORE_EDGE,
            shade=True,
            alpha=0.42,
        )
        if body_index < layout.stack_count - 1:
            _add_stack_seam(axis, layout.outer_width_mm, layout.outer_height_mm, z1_mm)

    if layout.gap_mm is not None:
        front_z_mm = 0.5 * layout.outer_depth_mm
        axis.plot(
            [center_x_mm, center_x_mm],
            [center_y_mm + inner_radius_mm, center_y_mm + outer_radius_mm],
            [front_z_mm, front_z_mm],
            color="#b91c1c",
            linewidth=2.4,
        )


def _draw_winding_block(axis, layout: InductorGeometryLayout) -> None:
    x0_mm = layout.winding_block_x_mm
    y0_mm = layout.winding_block_y_mm
    z0_mm = layout.winding_block_z_mm
    if (
        layout.winding_geometry_style in {"sleeve_around_leg", "sleeve_around_center_leg"}
        and layout.winding_inner_opening_x_mm is not None
        and layout.winding_inner_opening_y_mm is not None
        and layout.winding_inner_opening_z_mm is not None
        and layout.winding_inner_opening_width_mm is not None
        and layout.winding_inner_opening_height_mm is not None
        and layout.winding_inner_opening_depth_mm is not None
    ):
        _add_sleeve_boxes(axis, layout)
        _add_box_outline(
            axis,
            x0_mm,
            y0_mm,
            z0_mm,
            layout.winding_block_width_mm,
            layout.winding_block_height_mm,
            layout.winding_block_depth_mm,
            color=_WINDING_EDGE,
            linewidth=1.15,
        )
        return
    _add_box(
        axis,
        x0_mm,
        y0_mm,
        z0_mm,
        layout.winding_block_width_mm,
        layout.winding_block_height_mm,
        layout.winding_block_depth_mm,
        facecolor=_WINDING_FACE,
        edgecolor=_WINDING_EDGE,
        alpha=0.50,
    )
    _add_box_outline(
        axis,
        x0_mm,
        y0_mm,
        z0_mm,
        layout.winding_block_width_mm,
        layout.winding_block_height_mm,
        layout.winding_block_depth_mm,
        color=_WINDING_EDGE,
        linewidth=1.15,
    )


def _add_sleeve_boxes(axis, layout: InductorGeometryLayout) -> None:
    outer_x_mm = layout.winding_block_x_mm
    outer_y_mm = layout.winding_block_y_mm
    outer_z_mm = layout.winding_block_z_mm
    outer_width_mm = layout.winding_block_width_mm
    outer_height_mm = layout.winding_block_height_mm
    outer_depth_mm = layout.winding_block_depth_mm
    opening_x_mm = float(layout.winding_inner_opening_x_mm)
    opening_y_mm = float(layout.winding_inner_opening_y_mm)
    opening_width_mm = float(layout.winding_inner_opening_width_mm)
    opening_height_mm = float(layout.winding_inner_opening_height_mm)
    left_width_mm = max(opening_x_mm - outer_x_mm, 0.0)
    right_width_mm = max((outer_x_mm + outer_width_mm) - (opening_x_mm + opening_width_mm), 0.0)
    bottom_height_mm = max(opening_y_mm - outer_y_mm, 0.0)
    top_height_mm = max((outer_y_mm + outer_height_mm) - (opening_y_mm + opening_height_mm), 0.0)

    if left_width_mm > 0.0:
        _add_box(
            axis,
            outer_x_mm,
            outer_y_mm,
            outer_z_mm,
            left_width_mm,
            outer_height_mm,
            outer_depth_mm,
            facecolor=_WINDING_FACE,
            edgecolor=_WINDING_EDGE,
            alpha=0.50,
        )
    if right_width_mm > 0.0:
        _add_box(
            axis,
            opening_x_mm + opening_width_mm,
            outer_y_mm,
            outer_z_mm,
            right_width_mm,
            outer_height_mm,
            outer_depth_mm,
            facecolor=_WINDING_FACE,
            edgecolor=_WINDING_EDGE,
            alpha=0.50,
        )
    if bottom_height_mm > 0.0:
        _add_box(
            axis,
            opening_x_mm,
            outer_y_mm,
            outer_z_mm,
            opening_width_mm,
            bottom_height_mm,
            outer_depth_mm,
            facecolor=_WINDING_FACE,
            edgecolor=_WINDING_EDGE,
            alpha=0.50,
        )
    if top_height_mm > 0.0:
        _add_box(
            axis,
            opening_x_mm,
            opening_y_mm + opening_height_mm,
            outer_z_mm,
            opening_width_mm,
            top_height_mm,
            outer_depth_mm,
            facecolor=_WINDING_FACE,
            edgecolor=_WINDING_EDGE,
            alpha=0.50,
        )


def _annotate_3d_view(axis, layout: InductorGeometryLayout) -> None:
    axis.text2D(
        0.02,
        0.98,
        (
            f"{layout.design_id}\n"
            f"{layout.core_family.upper()} / {layout.template_name}\n"
            f"stack_count = {layout.stack_count}\n"
            f"bbox = {_fmt_mm(layout.overall_width_mm)} x {_fmt_mm(layout.overall_height_mm)} x {_fmt_mm(layout.overall_depth_mm)}\n"
            f"wind = {layout.turns}T / {layout.parallels}P / {_fmt_mm(layout.winding_equivalent_bundle_diameter_mm)} bundle\n"
            f"layers = {_fmt_int(layout.winding_layers)} / tpl = {_fmt_int(layout.winding_turns_per_layer)} / {_fmt_fit(layout)}\n"
            f"{layout.gap_position_label} = {_fmt_mm(layout.gap_mm)}"
        ),
        transform=axis.transAxes,
        va="top",
        ha="left",
        fontsize=8.4,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#ffffff", "edgecolor": "#d1d5db"},
    )


def _configure_axis(axis, layout: InductorGeometryLayout, *, comparison_settings: dict[str, float]) -> None:
    total_span_x_mm = comparison_settings["total_span_x_mm"]
    total_span_y_mm = comparison_settings["total_span_y_mm"]
    total_span_z_mm = comparison_settings["total_span_z_mm"]
    center_x_mm = 0.5 * layout.overall_width_mm
    center_y_mm = 0.5 * layout.overall_height_mm
    center_z_mm = 0.5 * layout.overall_depth_mm

    set_equal_physical_box_aspect(
        axis,
        center_x_mm=center_x_mm,
        center_y_mm=center_y_mm,
        center_z_mm=center_z_mm,
        total_span_x_mm=total_span_x_mm,
        total_span_y_mm=total_span_y_mm,
        total_span_z_mm=total_span_z_mm,
    )
    configure_engineering_3d_axis(axis, title="3D Static Geometry")


def _body_depth_ranges(layout: InductorGeometryLayout) -> list[tuple[float, float]]:
    return [
        (body_index * layout.outer_depth_mm, (body_index + 1) * layout.outer_depth_mm)
        for body_index in range(max(layout.stack_count, 1))
    ]


def _add_box(
    axis,
    x_mm: float,
    y_mm: float,
    z_mm: float,
    dx_mm: float,
    dy_mm: float,
    dz_mm: float,
    *,
    facecolor: str,
    edgecolor: str = _CORE_EDGE,
    alpha: float = 0.62,
) -> None:
    add_box_3d(axis, x_mm, y_mm, z_mm, dx_mm, dy_mm, dz_mm, facecolor=facecolor, edgecolor=edgecolor, alpha=alpha)


def _add_stack_seam(axis, width_mm: float, height_mm: float, z_mm: float) -> None:
    axis.plot(
        [0.0, width_mm, width_mm, 0.0, 0.0],
        [0.0, 0.0, height_mm, height_mm, 0.0],
        [z_mm, z_mm, z_mm, z_mm, z_mm],
        color=_SEAM_EDGE,
        linewidth=0.9,
    )


def _add_box_outline(
    axis,
    x_mm: float,
    y_mm: float,
    z_mm: float,
    dx_mm: float,
    dy_mm: float,
    dz_mm: float,
    *,
    color: str,
    linewidth: float,
) -> None:
    add_box_outline_3d(axis, x_mm, y_mm, z_mm, dx_mm, dy_mm, dz_mm, color=color, linewidth=linewidth)


def _fmt_mm(value_mm: float | None) -> str:
    if value_mm is None:
        return "n/a"
    return f"{float(value_mm):.3g} mm"


def _fmt_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(int(value))


def _fmt_fit(layout: InductorGeometryLayout) -> str:
    if layout.winding_fit_clamped:
        return "clamped"
    if layout.winding_fit_axial_ok and layout.winding_fit_radial_ok and layout.winding_fit_inner_opening_ok:
        return "fit ok"
    return "fit limited"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]
