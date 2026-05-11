"""Render first-pass 2D/3D capacitor bank geometry."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle

from ...models.capacitor import CapacitorBankLayout


def resolve_capacitor_2d_comparison_settings(layouts: list[CapacitorBankLayout]) -> dict[str, float]:
    """Return shared 2D physical spans for a side's three targets."""

    if not layouts:
        return {"shared_span_x_mm": 100.0, "shared_span_y_mm": 100.0}
    span_x = max(layout.footprint_width_mm for layout in layouts) * 1.35
    span_y = max(layout.footprint_depth_mm for layout in layouts) * 1.35
    span = max(span_x, span_y, 80.0)
    return {"shared_span_x_mm": span, "shared_span_y_mm": span}


def resolve_capacitor_3d_comparison_settings(layouts: list[CapacitorBankLayout]) -> dict[str, float]:
    """Return shared 3D physical span and camera settings."""

    if not layouts:
        return {"shared_span_mm": 100.0, "shared_height_mm": 100.0, "elev": 24.0, "azim": -42.0}
    span = max(max(layout.footprint_width_mm, layout.footprint_depth_mm) for layout in layouts) * 1.45
    height = max(layout.bank_height_mm for layout in layouts) * 1.25
    return {
        "shared_span_mm": max(span, 80.0),
        "shared_height_mm": max(height, 80.0),
        "elev": 24.0,
        "azim": -42.0,
    }


def create_capacitor_bank_figure_2d(
    layout: CapacitorBankLayout,
    *,
    shared_span_x_mm: float | None = None,
    shared_span_y_mm: float | None = None,
) -> Figure:
    """Create a top-view engineering figure for one capacitor bank."""

    span_x = shared_span_x_mm or max(layout.footprint_width_mm * 1.35, 80.0)
    span_y = shared_span_y_mm or max(layout.footprint_depth_mm * 1.35, 80.0)
    figure = Figure(figsize=(4.4, 3.6), dpi=100)
    axis = figure.add_subplot(111)
    body_width_mm = layout.body_width_mm or layout.can_diameter_mm
    body_depth_mm = layout.body_depth_mm or layout.can_diameter_mm
    radius_mm = 0.5 * layout.can_diameter_mm

    footprint = Rectangle(
        (-0.5 * layout.footprint_width_mm, -0.5 * layout.footprint_depth_mm),
        layout.footprint_width_mm,
        layout.footprint_depth_mm,
        fill=False,
        linestyle="--",
        linewidth=1.1,
        edgecolor="#475569",
    )
    axis.add_patch(footprint)
    for index, (x_mm, y_mm) in enumerate(layout.positions_mm, start=1):
        if layout.package_shape == "rectangular_box":
            axis.add_patch(
                Rectangle(
                    (x_mm - 0.5 * body_width_mm, y_mm - 0.5 * body_depth_mm),
                    body_width_mm,
                    body_depth_mm,
                    facecolor="#d9dee5",
                    edgecolor="#1f2937",
                    linewidth=1.2,
                )
            )
            for terminal_x_mm, terminal_y_mm in _terminal_offsets(layout):
                axis.add_patch(
                    Circle(
                        (x_mm + terminal_x_mm, y_mm + terminal_y_mm),
                        max(0.9, 0.5 * layout.terminal_diameter_mm),
                        facecolor="#94a3b8",
                        edgecolor="#334155",
                        linewidth=0.7,
                    )
                )
        elif layout.package_shape == "axial_cylindrical":
            axis.add_patch(
                Rectangle(
                    (x_mm - 0.5 * body_width_mm, y_mm - 0.5 * body_depth_mm),
                    body_width_mm,
                    body_depth_mm,
                    facecolor="#d9dee5",
                    edgecolor="#1f2937",
                    linewidth=1.2,
                )
            )
            axis.add_patch(
                Circle(
                    (x_mm - 0.5 * body_width_mm, y_mm),
                    0.5 * body_depth_mm,
                    facecolor="#d9dee5",
                    edgecolor="#1f2937",
                    linewidth=1.0,
                )
            )
            axis.add_patch(
                Circle(
                    (x_mm + 0.5 * body_width_mm, y_mm),
                    0.5 * body_depth_mm,
                    facecolor="#d9dee5",
                    edgecolor="#1f2937",
                    linewidth=1.0,
                )
            )
            for terminal_x_mm, terminal_y_mm in _terminal_offsets(layout):
                axis.plot(
                    [x_mm + terminal_x_mm, x_mm + terminal_x_mm + (12.0 if terminal_x_mm > 0 else -12.0)],
                    [y_mm + terminal_y_mm, y_mm + terminal_y_mm],
                    color="#334155",
                    linewidth=1.1,
                )
        else:
            axis.add_patch(Circle((x_mm, y_mm), radius_mm, facecolor="#d9dee5", edgecolor="#1f2937", linewidth=1.2))
            axis.add_patch(Circle((x_mm, y_mm), radius_mm * 0.83, fill=False, edgecolor="#94a3b8", linewidth=0.8))
        axis.text(x_mm, y_mm, str(index), ha="center", va="center", fontsize=8, color="#111827")

    axis.set_title(f"{layout.label}: {layout.part_number}  N={layout.parallel_count}", fontsize=9)
    axis.text(
        0.02,
        0.02,
        f"{_layout_dimension_text(layout)}\n"
        f"Footprint={layout.footprint_width_mm:.3g} x {layout.footprint_depth_mm:.3g} mm",
        transform=axis.transAxes,
        va="bottom",
        ha="left",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.85},
    )
    axis.set_xlim(-0.5 * span_x, 0.5 * span_x)
    axis.set_ylim(-0.5 * span_y, 0.5 * span_y)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("width (mm)")
    axis.set_ylabel("depth (mm)")
    axis.grid(True, alpha=0.22)
    figure.tight_layout()
    return figure


def create_capacitor_bank_figure_3d(
    layout: CapacitorBankLayout,
    *,
    comparison_settings: dict[str, float] | None = None,
) -> Figure:
    """Create a static 3D engineering figure for one capacitor bank."""

    settings = comparison_settings or resolve_capacitor_3d_comparison_settings([layout])
    span_mm = settings["shared_span_mm"]
    height_mm = settings["shared_height_mm"]
    figure = Figure(figsize=(4.4, 3.6), dpi=100)
    axis = figure.add_subplot(111, projection="3d")

    _draw_baseplate(axis, layout)
    for x_mm, y_mm in layout.positions_mm:
        if layout.package_shape == "rectangular_box":
            _draw_box(axis, x_mm, y_mm, layout)
        elif layout.package_shape == "axial_cylindrical":
            _draw_horizontal_cylinder(axis, x_mm, y_mm, layout)
        else:
            _draw_cylinder(axis, x_mm, y_mm, layout.can_diameter_mm, layout.can_height_mm)
        _draw_terminals(axis, x_mm, y_mm, layout)

    axis.set_title(f"{layout.label}: {layout.part_number}  N={layout.parallel_count}", fontsize=9)
    axis.set_xlim(-0.5 * span_mm, 0.5 * span_mm)
    axis.set_ylim(-0.5 * span_mm, 0.5 * span_mm)
    axis.set_zlim(0.0, height_mm)
    axis.set_xlabel("width (mm)")
    axis.set_ylabel("depth (mm)")
    axis.set_zlabel("height (mm)")
    axis.view_init(elev=settings.get("elev", 24.0), azim=settings.get("azim", -42.0))
    try:
        axis.set_box_aspect((1, 1, height_mm / max(span_mm, 1e-9)))
    except AttributeError:
        pass
    figure.tight_layout()
    return figure


def export_capacitor_geometry_artifacts(
    layout: CapacitorBankLayout,
    *,
    output_dir: Path,
    basename: str,
    comparison_settings_2d: dict[str, float],
    comparison_settings_3d: dict[str, float],
) -> tuple[list[str], list[str]]:
    """Export 2D and 3D PNG artifacts for one capacitor layout."""

    output_dir.mkdir(parents=True, exist_ok=True)
    path_2d = output_dir / f"{basename}.png"
    path_3d = output_dir / f"{basename}_3d.png"

    figure_2d = create_capacitor_bank_figure_2d(layout, **comparison_settings_2d)
    figure_2d.savefig(path_2d)
    figure_2d.clear()

    figure_3d = create_capacitor_bank_figure_3d(layout, comparison_settings=comparison_settings_3d)
    figure_3d.savefig(path_3d)
    figure_3d.clear()

    return [str(path_2d)], [str(path_3d)]


def _draw_baseplate(axis, layout: CapacitorBankLayout) -> None:
    x = np.array(
        [
            [-0.5 * layout.footprint_width_mm, 0.5 * layout.footprint_width_mm],
            [-0.5 * layout.footprint_width_mm, 0.5 * layout.footprint_width_mm],
        ]
    )
    y = np.array(
        [
            [-0.5 * layout.footprint_depth_mm, -0.5 * layout.footprint_depth_mm],
            [0.5 * layout.footprint_depth_mm, 0.5 * layout.footprint_depth_mm],
        ]
    )
    z = np.zeros_like(x)
    axis.plot_surface(x, y, z, color="#e5e7eb", alpha=0.35, linewidth=0.0)


def _draw_cylinder(axis, x_mm: float, y_mm: float, diameter_mm: float, height_mm: float) -> None:
    radius_mm = 0.5 * diameter_mm
    theta = np.linspace(0.0, 2.0 * math.pi, 32)
    z_values = np.linspace(0.0, height_mm, 8)
    theta_grid, z_grid = np.meshgrid(theta, z_values)
    x_grid = x_mm + radius_mm * np.cos(theta_grid)
    y_grid = y_mm + radius_mm * np.sin(theta_grid)
    axis.plot_surface(x_grid, y_grid, z_grid, color="#cbd5e1", edgecolor="#64748b", linewidth=0.25, alpha=0.92)
    top_x = x_mm + radius_mm * np.cos(theta)
    top_y = y_mm + radius_mm * np.sin(theta)
    axis.plot(top_x, top_y, np.full_like(theta, height_mm), color="#334155", linewidth=0.8)


def _draw_horizontal_cylinder(axis, x_mm: float, y_mm: float, layout: CapacitorBankLayout) -> None:
    length_mm = layout.body_width_mm or layout.can_height_mm
    diameter_mm = layout.body_depth_mm or layout.can_diameter_mm
    radius_mm = 0.5 * diameter_mm
    theta = np.linspace(0.0, 2.0 * math.pi, 32)
    x_values = np.linspace(x_mm - 0.5 * length_mm, x_mm + 0.5 * length_mm, 10)
    x_grid, theta_grid = np.meshgrid(x_values, theta)
    y_grid = y_mm + radius_mm * np.cos(theta_grid)
    z_grid = radius_mm + radius_mm * np.sin(theta_grid)
    axis.plot_surface(x_grid, y_grid, z_grid, color="#cbd5e1", edgecolor="#64748b", linewidth=0.25, alpha=0.92)
    for end_x in (x_mm - 0.5 * length_mm, x_mm + 0.5 * length_mm):
        axis.plot(
            np.full_like(theta, end_x),
            y_mm + radius_mm * np.cos(theta),
            radius_mm + radius_mm * np.sin(theta),
            color="#334155",
            linewidth=0.8,
        )


def _draw_box(axis, x_mm: float, y_mm: float, layout: CapacitorBankLayout) -> None:
    width_mm = layout.body_width_mm or layout.can_diameter_mm
    depth_mm = layout.body_depth_mm or layout.can_diameter_mm
    height_mm = layout.body_height_mm or layout.can_height_mm
    x0 = x_mm - 0.5 * width_mm
    x1 = x_mm + 0.5 * width_mm
    y0 = y_mm - 0.5 * depth_mm
    y1 = y_mm + 0.5 * depth_mm
    z0 = 0.0
    z1 = height_mm
    faces = [
        ([x0, x1], [y0, y0], [z0, z1]),
        ([x0, x1], [y1, y1], [z0, z1]),
        ([x0, x0], [y0, y1], [z0, z1]),
        ([x1, x1], [y0, y1], [z0, z1]),
    ]
    for x_vals, y_vals, z_vals in faces:
        x_grid, z_grid = np.meshgrid(np.array(x_vals), np.array(z_vals))
        if y_vals[0] == y_vals[1]:
            y_grid = np.full_like(x_grid, y_vals[0])
        else:
            y_grid, z_grid = np.meshgrid(np.array(y_vals), np.array(z_vals))
            x_grid = np.full_like(y_grid, x_vals[0])
        axis.plot_surface(x_grid, y_grid, z_grid, color="#cbd5e1", edgecolor="#64748b", linewidth=0.25, alpha=0.92)
    top_x = np.array([[x0, x1], [x0, x1]])
    top_y = np.array([[y0, y0], [y1, y1]])
    top_z = np.full_like(top_x, z1)
    axis.plot_surface(top_x, top_y, top_z, color="#d9dee5", edgecolor="#334155", linewidth=0.5, alpha=0.95)


def _draw_terminals(axis, x_mm: float, y_mm: float, layout: CapacitorBankLayout) -> None:
    if layout.terminal_count <= 0:
        return
    if layout.package_shape == "axial_cylindrical":
        body_width_mm = layout.body_width_mm or layout.can_height_mm
        radius_mm = max(0.4, 0.5 * layout.terminal_diameter_mm)
        z_mm = 0.5 * (layout.body_depth_mm or layout.can_diameter_mm)
        for sign in (-1.0, 1.0):
            axis.plot(
                [x_mm + sign * 0.5 * body_width_mm, x_mm + sign * (0.5 * body_width_mm + 12.0)],
                [y_mm, y_mm],
                [z_mm, z_mm],
                color="#334155",
                linewidth=max(0.8, 2.0 * radius_mm),
            )
        return
    terminal_radius_mm = max(1.5, 0.5 * layout.terminal_diameter_mm)
    height_top_mm = layout.can_height_mm
    terminal_height_mm = min(10.0, max(4.0, 0.08 * layout.can_height_mm))
    for offset_x_mm, offset_y_mm in _terminal_offsets(layout):
        _draw_terminal_cylinder(
            axis,
            x_mm + offset_x_mm,
            y_mm + offset_y_mm,
            terminal_radius_mm,
            height_top_mm,
            height_top_mm + terminal_height_mm,
        )


def _layout_dimension_text(layout: CapacitorBankLayout) -> str:
    if layout.package_shape == "rectangular_box":
        width_mm = layout.body_width_mm or layout.can_diameter_mm
        depth_mm = layout.body_depth_mm or layout.can_diameter_mm
        height_mm = layout.body_height_mm or layout.can_height_mm
        return f"Box={width_mm:.3g} x {depth_mm:.3g} x {height_mm:.3g} mm"
    if layout.package_shape == "axial_cylindrical":
        length_mm = layout.body_width_mm or layout.can_height_mm
        diameter_mm = layout.body_depth_mm or layout.can_diameter_mm
        return f"Axial D={diameter_mm:.3g} mm\nL={length_mm:.3g} mm"
    return f"D={layout.can_diameter_mm:.3g} mm\nH={layout.can_height_mm:.3g} mm"


def _terminal_offsets(layout: CapacitorBankLayout) -> list[tuple[float, float]]:
    if layout.package_shape == "axial_cylindrical":
        body_width_mm = layout.body_width_mm or layout.can_height_mm
        return [(-0.5 * body_width_mm, 0.0), (0.5 * body_width_mm, 0.0)]
    terminal_pitch_mm = layout.terminal_pitch_mm or 0.45 * layout.can_diameter_mm
    if layout.terminal_count <= 1:
        return [(0.0, 0.0)]
    if layout.package_shape == "rectangular_box" and layout.terminal_count >= 4 and layout.terminal_pitch_secondary_mm:
        half_x_mm = 0.5 * terminal_pitch_mm
        half_y_mm = 0.5 * layout.terminal_pitch_secondary_mm
        return [
            (-half_x_mm, -half_y_mm),
            (half_x_mm, -half_y_mm),
            (-half_x_mm, half_y_mm),
            (half_x_mm, half_y_mm),
        ]
    return [(-0.5 * terminal_pitch_mm, 0.0), (0.5 * terminal_pitch_mm, 0.0)][: layout.terminal_count]


def _draw_terminal_cylinder(axis, x_mm: float, y_mm: float, radius_mm: float, z0_mm: float, z1_mm: float) -> None:
    theta = np.linspace(0.0, 2.0 * math.pi, 18)
    z_values = np.linspace(z0_mm, z1_mm, 3)
    theta_grid, z_grid = np.meshgrid(theta, z_values)
    x_grid = x_mm + radius_mm * np.cos(theta_grid)
    y_grid = y_mm + radius_mm * np.sin(theta_grid)
    axis.plot_surface(x_grid, y_grid, z_grid, color="#94a3b8", linewidth=0.1, alpha=1.0)
