"""Matplotlib renderer for first-pass magnetic geometry views."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from matplotlib.figure import Figure
from matplotlib.patches import Circle, Polygon, Rectangle

from ...models.geometry_result import InductorGeometryLayout

_OUTPUT_SUBDIR = Path("outputs") / "inductor_design"


@dataclass(frozen=True)
class _PanelFrame:
    """Physical content extents and padding for a geometry subpanel."""

    width_mm: float
    height_mm: float
    pad_x_mm: float
    pad_y_mm: float

    @property
    def span_x_mm(self) -> float:
        return self.width_mm + (2.0 * self.pad_x_mm)

    @property
    def span_y_mm(self) -> float:
        return self.height_mm + (2.0 * self.pad_y_mm)


def create_geometry_figure(layout: InductorGeometryLayout) -> Figure:
    """Create an engineering geometry figure for the selected magnetic design."""
    figure = Figure(figsize=(11.5, 4.8), dpi=120)
    axes = figure.subplots(1, 3)
    for axis in axes:
        axis.set_aspect("equal", adjustable="box")
        axis.axis("off")

    frames = _resolve_panel_frames(layout)
    shared_span_x_mm = max(frame.span_x_mm for frame in frames.values())
    shared_span_y_mm = max(frame.span_y_mm for frame in frames.values())

    _draw_core_view(axes[0], layout, shared_span_x_mm=shared_span_x_mm, shared_span_y_mm=shared_span_y_mm)
    _draw_winding_view(axes[1], layout, shared_span_x_mm=shared_span_x_mm, shared_span_y_mm=shared_span_y_mm)
    _draw_assembly_view(axes[2], layout, shared_span_x_mm=shared_span_x_mm, shared_span_y_mm=shared_span_y_mm)
    figure.tight_layout(pad=1.2)
    return figure


def create_core_geometry_figure(
    layout: InductorGeometryLayout,
    *,
    shared_span_x_mm: float | None = None,
    shared_span_y_mm: float | None = None,
    shared_scale_bar_mm: float | None = None,
) -> Figure:
    """Create a core-only 2D engineering figure for comparison layouts."""
    figure = Figure(figsize=(4.0, 4.6), dpi=120)
    axis = figure.subplots(1, 1)
    axis.set_aspect("equal", adjustable="box")
    axis.axis("off")
    core_frame = _resolve_panel_frames(layout)["core"]
    _draw_core_view(
        axis,
        layout,
        shared_span_x_mm=shared_span_x_mm or core_frame.span_x_mm,
        shared_span_y_mm=shared_span_y_mm or core_frame.span_y_mm,
        scale_bar_mm=shared_scale_bar_mm,
    )
    figure.tight_layout(pad=1.0)
    return figure


def resolve_core_comparison_settings(layouts: list[InductorGeometryLayout]) -> dict[str, float]:
    """Resolve one shared physical scale basis for a set of core-only comparison figures."""
    if not layouts:
        return {
            "shared_span_x_mm": 40.0,
            "shared_span_y_mm": 40.0,
            "shared_scale_bar_mm": 10.0,
        }
    core_frames = [_resolve_panel_frames(layout)["core"] for layout in layouts]
    shared_span_x_mm = max(frame.span_x_mm for frame in core_frames)
    shared_span_y_mm = max(frame.span_y_mm for frame in core_frames)
    max_dimension_mm = max(max(layout.outer_width_mm, layout.outer_height_mm) for layout in layouts)
    return {
        "shared_span_x_mm": shared_span_x_mm,
        "shared_span_y_mm": shared_span_y_mm,
        "shared_scale_bar_mm": _resolve_scale_bar_mm(max_dimension_mm),
    }


def export_geometry_artifacts(
    layout: InductorGeometryLayout,
    output_dir: Path | None = None,
    basename: str = "geometry_selected",
) -> list[str]:
    """Persist PNG and SVG artifacts for the selected geometry layout."""
    output_root = Path(output_dir or _project_root() / _OUTPUT_SUBDIR)
    output_root.mkdir(parents=True, exist_ok=True)
    figure = create_geometry_figure(layout)
    png_path = output_root / f"{basename}.png"
    svg_path = output_root / f"{basename}.svg"
    try:
        figure.savefig(png_path, bbox_inches="tight")
        figure.savefig(svg_path, bbox_inches="tight")
    finally:
        figure.clear()
    return [str(png_path), str(svg_path)]


def _draw_core_view(
    axis,
    layout: InductorGeometryLayout,
    *,
    shared_span_x_mm: float,
    shared_span_y_mm: float,
    scale_bar_mm: float | None = None,
) -> None:
    _configure_axis(
        axis,
        layout.outer_width_mm,
        layout.outer_height_mm,
        title="Core Geometry",
        shared_span_x_mm=shared_span_x_mm,
        shared_span_y_mm=shared_span_y_mm,
    )
    if layout.template_name == "toroid_ring":
        _draw_toroid(axis, layout)
    elif layout.template_name == "u_paired_core":
        _draw_u_paired_core(axis, layout)
    elif layout.template_name == "paired_etd_core":
        _draw_paired_etd_core(axis, layout)
    elif layout.template_name == "paired_box_core":
        _draw_paired_box_core(axis, layout)
    else:
        _draw_box_window_core(axis, layout)

    gap_label = (
        f"{layout.gap_position_label} = {_fmt_mm(layout.gap_mm)}"
        if layout.gap_mm is not None
        else f"{layout.gap_position_label} = n/a"
    )
    assembly_summary = (
        f"{layout.half_cores_per_assembly} half-cores per assembly\n"
        if layout.library_item_is_half_core
        else ""
    )
    axis.text(
        0.02,
        0.98,
        f"{layout.core_family.upper()}  {layout.base_core_name}\n{assembly_summary}{gap_label}",
        transform=axis.transAxes,
        va="top",
        ha="left",
        fontsize=8.5,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#ffffff", "edgecolor": "#d1d5db"},
    )
    _add_scale_bar(axis, scale_bar_mm if scale_bar_mm is not None else layout.scale_bar_mm)


def _draw_toroid(axis, layout: InductorGeometryLayout) -> None:
    center_x = 0.5 * layout.outer_width_mm
    center_y = 0.52 * layout.outer_height_mm
    outer_radius = 0.5 * layout.outer_width_mm
    inner_radius = 0.5 * layout.core_window_width_mm
    axis.add_patch(Circle((center_x, center_y), outer_radius, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.5))
    axis.add_patch(Circle((center_x, center_y), inner_radius, facecolor="white", edgecolor="#111827", linewidth=1.2))
    if layout.gap_mm is not None:
        gap_width_mm = max(layout.gap_mm, 0.15)
        axis.add_patch(
            Rectangle(
                (center_x - 0.5 * gap_width_mm, center_y + inner_radius),
                gap_width_mm,
                max(outer_radius - inner_radius, 0.6),
                facecolor="white",
                edgecolor="#ef4444",
                linewidth=1.0,
            )
        )
        axis.text(center_x, center_y + outer_radius + 1.5, _fmt_mm(layout.gap_mm), ha="center", va="bottom", fontsize=8, color="#b91c1c")
    _dimension_line(axis, 0.0, layout.outer_width_mm, -2.2, f"OD {_fmt_mm(layout.outer_width_mm)}", vertical=False)
    _dimension_line(axis, 0.0, layout.outer_height_mm, -2.2, f"OD {_fmt_mm(layout.outer_height_mm)}", vertical=True)
    axis.text(center_x, center_y, f"ID\n{_fmt_mm(layout.core_window_width_mm)}", ha="center", va="center", fontsize=8, color="#111827")
    if layout.effective_area_mm2 is not None:
        axis.text(center_x, 1.2, f"Ae {_fmt_mm2(layout.effective_area_mm2)}", ha="center", va="bottom", fontsize=8, color="#374151")


def _draw_u_paired_core(axis, layout: InductorGeometryLayout) -> None:
    half_core_height_mm = 0.5 * layout.outer_height_mm
    window_width_mm = layout.core_window_width_mm
    window_height_mm = layout.core_window_height_mm
    leg_width_mm = layout.side_leg_width_mm or max(0.5 * (layout.outer_width_mm - window_width_mm), 0.12 * layout.outer_width_mm)
    yoke_height_mm = layout.top_yoke_height_mm or max(0.5 * (layout.outer_height_mm - window_height_mm), 0.16 * half_core_height_mm)
    top_half_y = layout.outer_height_mm - half_core_height_mm
    bottom_half_y = 0.0
    # Bottom U half.
    axis.add_patch(Rectangle((0.0, bottom_half_y), leg_width_mm, half_core_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((layout.outer_width_mm - leg_width_mm, bottom_half_y), leg_width_mm, half_core_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((0.0, bottom_half_y), layout.outer_width_mm, yoke_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    # Top U half.
    axis.add_patch(Rectangle((0.0, top_half_y), leg_width_mm, half_core_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((layout.outer_width_mm - leg_width_mm, top_half_y), leg_width_mm, half_core_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((0.0, layout.outer_height_mm - yoke_height_mm), layout.outer_width_mm, yoke_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    # Shared paired window region and winding cavity.
    window_y = 0.5 * (layout.outer_height_mm - window_height_mm)
    axis.add_patch(Rectangle((leg_width_mm, window_y), window_width_mm, window_height_mm, facecolor="white", edgecolor="#111827", linewidth=1.0))
    axis.add_patch(
        Rectangle(
            (layout.winding_region_x_mm, layout.winding_region_y_mm),
            layout.winding_region_width_mm,
            layout.winding_region_height_mm,
            facecolor="none",
            edgecolor="#1d4ed8",
            linewidth=1.0,
            linestyle="--",
        )
    )
    _draw_winding_profile(
        axis,
        layout,
        outer_x_mm=layout.winding_block_x_mm,
        outer_y_mm=layout.winding_block_y_mm,
        outer_width_mm=layout.winding_block_width_mm,
        outer_height_mm=layout.winding_block_height_mm,
        opening_x_mm=layout.winding_inner_opening_x_mm,
        opening_y_mm=layout.winding_inner_opening_y_mm,
        opening_width_mm=layout.winding_inner_opening_width_mm,
        opening_height_mm=layout.winding_inner_opening_height_mm,
        opening_fill="#d9dde6",
        alpha=0.55,
    )
    if layout.gap_mm is not None:
        gap_height_mm = max(layout.gap_mm, 0.15)
        axis.add_patch(
            Rectangle(
                (leg_width_mm, 0.5 * layout.outer_height_mm - 0.5 * gap_height_mm),
                window_width_mm,
                gap_height_mm,
                facecolor="#ffffff",
                edgecolor="#ef4444",
                linewidth=1.0,
            )
        )
        axis.annotate(
            _fmt_mm(layout.gap_mm),
            xy=(0.5 * layout.outer_width_mm, 0.5 * layout.outer_height_mm),
            xytext=(0.68 * layout.outer_width_mm, 0.68 * layout.outer_height_mm),
            arrowprops={"arrowstyle": "->", "linewidth": 0.9, "color": "#b91c1c"},
            fontsize=8,
            color="#b91c1c",
            ha="left",
            va="bottom",
        )
    _dimension_line(axis, 0.0, layout.outer_width_mm, -2.0, f"W {_fmt_mm(layout.outer_width_mm)}", vertical=False)
    _dimension_line(axis, 0.0, layout.outer_height_mm, -2.0, f"H {_fmt_mm(layout.outer_height_mm)}", vertical=True)
    axis.text(0.5 * layout.outer_width_mm, window_y + 0.5 * window_height_mm, f"paired window\n{_fmt_mm(window_width_mm)} x {_fmt_mm(window_height_mm)}", ha="center", va="center", fontsize=8)
    axis.text(
        layout.winding_region_x_mm + (0.5 * layout.winding_region_width_mm),
        layout.winding_region_y_mm + layout.winding_region_height_mm + 1.0,
        f"winding side\n{layout.winding_geometry_style}",
        ha="center",
        va="bottom",
        fontsize=7.8,
        color="#1d4ed8",
    )
    axis.text(layout.outer_width_mm + 0.8, 0.5 * half_core_height_mm, "lower half", ha="left", va="center", fontsize=8, color="#374151")
    axis.text(layout.outer_width_mm + 0.8, layout.outer_height_mm - 0.5 * half_core_height_mm, "upper half", ha="left", va="center", fontsize=8, color="#374151")


def _draw_box_window_core(axis, layout: InductorGeometryLayout) -> None:
    side_leg_mm = layout.side_leg_width_mm or max(
        (layout.outer_width_mm - layout.core_window_width_mm - (layout.center_leg_width_mm or 0.0)) / 2.0,
        0.12 * layout.outer_width_mm,
    )
    center_leg_mm = layout.center_leg_width_mm or 0.18 * layout.outer_width_mm
    window_width_mm = layout.core_window_width_mm
    window_height_mm = min(layout.core_window_height_mm, 0.72 * layout.outer_height_mm)
    yoke_mm = layout.top_yoke_height_mm or max(0.5 * (layout.outer_height_mm - window_height_mm), 0.14 * layout.outer_height_mm)

    axis.add_patch(Rectangle((0.0, 0.0), layout.outer_width_mm, layout.outer_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((side_leg_mm, yoke_mm), window_width_mm, window_height_mm, facecolor="white", edgecolor="#111827", linewidth=1.0))
    axis.add_patch(Rectangle((layout.outer_width_mm - side_leg_mm - window_width_mm, yoke_mm), window_width_mm, window_height_mm, facecolor="white", edgecolor="#111827", linewidth=1.0))
    axis.add_patch(
        Rectangle(
            (0.5 * layout.outer_width_mm - 0.5 * center_leg_mm, yoke_mm),
            center_leg_mm,
            window_height_mm,
            facecolor="#c4cad6",
            edgecolor="#111827",
            linewidth=1.0,
        )
    )
    if layout.gap_mm is not None:
        gap_width_mm = max(layout.gap_mm, 0.15)
        axis.add_patch(
            Rectangle(
                (0.5 * layout.outer_width_mm - 0.5 * center_leg_mm, layout.outer_height_mm - yoke_mm),
                center_leg_mm,
                gap_width_mm,
                facecolor="#ffffff",
                edgecolor="#ef4444",
                linewidth=1.0,
            )
        )
        axis.text(0.5 * layout.outer_width_mm, layout.outer_height_mm + 1.2, _fmt_mm(layout.gap_mm), ha="center", va="bottom", fontsize=8, color="#b91c1c")
    _dimension_line(axis, 0.0, layout.outer_width_mm, -2.0, f"W {_fmt_mm(layout.outer_width_mm)}", vertical=False)
    _dimension_line(axis, 0.0, layout.outer_height_mm, -2.0, f"H {_fmt_mm(layout.outer_height_mm)}", vertical=True)
    axis.text(0.5 * layout.outer_width_mm, 1.3, f"center leg {_fmt_mm(layout.center_leg_width_mm)}", ha="center", va="bottom", fontsize=8, color="#374151")


def _draw_paired_box_core(axis, layout: InductorGeometryLayout) -> None:
    side_leg_mm = layout.side_leg_width_mm or max(
        (layout.outer_width_mm - layout.core_window_width_mm - (layout.center_leg_width_mm or 0.0)) / 2.0,
        0.12 * layout.outer_width_mm,
    )
    center_leg_mm = layout.center_leg_width_mm or 0.18 * layout.outer_width_mm
    window_width_mm = layout.core_window_width_mm
    window_height_mm = min(layout.core_window_height_mm, 0.72 * layout.outer_height_mm)
    half_core_height_mm = 0.5 * layout.outer_height_mm
    yoke_mm = layout.top_yoke_height_mm or max(0.5 * (layout.outer_height_mm - window_height_mm), 0.14 * half_core_height_mm)
    upper_yoke_bottom = layout.outer_height_mm - yoke_mm
    window_y = 0.5 * (layout.outer_height_mm - window_height_mm)

    # Lower half.
    axis.add_patch(Rectangle((0.0, 0.0), side_leg_mm, half_core_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((layout.outer_width_mm - side_leg_mm, 0.0), side_leg_mm, half_core_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((0.5 * layout.outer_width_mm - 0.5 * center_leg_mm, 0.0), center_leg_mm, half_core_height_mm - window_y, facecolor="#c4cad6", edgecolor="#111827", linewidth=1.0))
    axis.add_patch(Rectangle((0.0, 0.0), layout.outer_width_mm, yoke_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))

    # Upper half.
    axis.add_patch(Rectangle((0.0, half_core_height_mm), side_leg_mm, half_core_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((layout.outer_width_mm - side_leg_mm, half_core_height_mm), side_leg_mm, half_core_height_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Rectangle((0.5 * layout.outer_width_mm - 0.5 * center_leg_mm, upper_yoke_bottom), center_leg_mm, layout.outer_height_mm - upper_yoke_bottom, facecolor="#c4cad6", edgecolor="#111827", linewidth=1.0))
    axis.add_patch(Rectangle((0.0, layout.outer_height_mm - yoke_mm), layout.outer_width_mm, yoke_mm, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))

    # Shared paired windows.
    axis.add_patch(Rectangle((side_leg_mm, window_y), window_width_mm, window_height_mm, facecolor="white", edgecolor="#111827", linewidth=1.0))
    axis.add_patch(Rectangle((layout.outer_width_mm - side_leg_mm - window_width_mm, window_y), window_width_mm, window_height_mm, facecolor="white", edgecolor="#111827", linewidth=1.0))
    if layout.winding_geometry_style == "sleeve_around_center_leg":
        axis.add_patch(
            Rectangle(
                (layout.winding_region_x_mm, layout.winding_region_y_mm),
                layout.winding_region_width_mm,
                layout.winding_region_height_mm,
                facecolor="none",
                edgecolor="#1d4ed8",
                linewidth=1.0,
                linestyle="--",
            )
        )
        _draw_winding_profile(
            axis,
            layout,
            outer_x_mm=layout.winding_block_x_mm,
            outer_y_mm=layout.winding_block_y_mm,
            outer_width_mm=layout.winding_block_width_mm,
            outer_height_mm=layout.winding_block_height_mm,
            opening_x_mm=layout.winding_inner_opening_x_mm,
            opening_y_mm=layout.winding_inner_opening_y_mm,
            opening_width_mm=layout.winding_inner_opening_width_mm,
            opening_height_mm=layout.winding_inner_opening_height_mm,
            opening_fill="none",
            alpha=0.55,
        )
    if layout.gap_mm is not None:
        gap_height_mm = max(layout.gap_mm, 0.15)
        axis.add_patch(
            Rectangle(
                (0.5 * layout.outer_width_mm - 0.5 * center_leg_mm, 0.5 * layout.outer_height_mm - 0.5 * gap_height_mm),
                center_leg_mm,
                gap_height_mm,
                facecolor="#ffffff",
                edgecolor="#ef4444",
                linewidth=1.0,
            )
        )
        axis.annotate(
            _fmt_mm(layout.gap_mm),
            xy=(0.5 * layout.outer_width_mm, 0.5 * layout.outer_height_mm),
            xytext=(0.68 * layout.outer_width_mm, 0.68 * layout.outer_height_mm),
            arrowprops={"arrowstyle": "->", "linewidth": 0.9, "color": "#b91c1c"},
            fontsize=8,
            color="#b91c1c",
            ha="left",
            va="bottom",
        )
    _dimension_line(axis, 0.0, layout.outer_width_mm, -2.0, f"W {_fmt_mm(layout.outer_width_mm)}", vertical=False)
    _dimension_line(axis, 0.0, layout.outer_height_mm, -2.0, f"H {_fmt_mm(layout.outer_height_mm)}", vertical=True)
    axis.text(0.5 * layout.outer_width_mm, 1.2, f"center leg {_fmt_mm(center_leg_mm)}", ha="center", va="bottom", fontsize=8, color="#374151")
    if layout.winding_geometry_style == "sleeve_around_center_leg":
        axis.text(
            0.5 * layout.outer_width_mm,
            layout.winding_region_y_mm + layout.winding_region_height_mm + 1.0,
            f"center-leg winding\n{layout.winding_geometry_style}",
            ha="center",
            va="bottom",
            fontsize=7.8,
            color="#1d4ed8",
        )
    axis.text(layout.outer_width_mm + 0.8, 0.5 * half_core_height_mm, "lower half", ha="left", va="center", fontsize=8, color="#374151")
    axis.text(layout.outer_width_mm + 0.8, layout.outer_height_mm - 0.5 * half_core_height_mm, "upper half", ha="left", va="center", fontsize=8, color="#374151")


def _draw_paired_etd_core(axis, layout: InductorGeometryLayout) -> None:
    width_mm = layout.outer_width_mm
    height_mm = layout.outer_height_mm
    half_height_mm = 0.5 * height_mm
    center_leg_mm = layout.center_leg_width_mm or (0.20 * width_mm)
    side_leg_mm = layout.side_leg_width_mm or max(0.15 * width_mm, 0.82 * center_leg_mm)
    window_width_mm = layout.core_window_width_mm
    window_height_mm = layout.core_window_height_mm
    window_y = 0.5 * (height_mm - window_height_mm)
    split_y = half_height_mm
    yoke_mm = layout.top_yoke_height_mm or max(0.5 * (height_mm - window_height_mm), 0.16 * half_height_mm)
    shoulder_inset_mm = max(0.08 * width_mm, 0.34 * side_leg_mm)
    shoulder_rise_mm = max(0.18 * half_height_mm, 0.20 * window_height_mm)

    top_half = [
        (0.0, height_mm),
        (width_mm, height_mm),
        (width_mm, height_mm - yoke_mm),
        (width_mm - shoulder_inset_mm, split_y + shoulder_rise_mm),
        (width_mm - shoulder_inset_mm, split_y),
        (shoulder_inset_mm, split_y),
        (shoulder_inset_mm, split_y + shoulder_rise_mm),
        (0.0, height_mm - yoke_mm),
    ]
    bottom_half = [(x, height_mm - y) for x, y in reversed(top_half)]

    axis.add_patch(Polygon(bottom_half, closed=True, facecolor="#d9dde6", edgecolor="#111827", linewidth=1.4))
    axis.add_patch(Polygon(top_half, closed=True, facecolor="#cfd6e2", edgecolor="#111827", linewidth=1.4))

    left_window_x = side_leg_mm
    right_window_x = width_mm - side_leg_mm - window_width_mm
    axis.add_patch(Rectangle((left_window_x, window_y), window_width_mm, window_height_mm, facecolor="white", edgecolor="#111827", linewidth=1.0))
    axis.add_patch(Rectangle((right_window_x, window_y), window_width_mm, window_height_mm, facecolor="white", edgecolor="#111827", linewidth=1.0))

    axis.add_patch(
        Rectangle(
            (0.5 * width_mm - 0.5 * center_leg_mm, 0.0),
            center_leg_mm,
            split_y,
            facecolor="#bcc4d3",
            edgecolor="#111827",
            linewidth=1.0,
        )
    )
    axis.add_patch(
        Rectangle(
            (0.5 * width_mm - 0.5 * center_leg_mm, split_y),
            center_leg_mm,
            split_y,
            facecolor="#bcc4d3",
            edgecolor="#111827",
            linewidth=1.0,
        )
    )

    if layout.winding_geometry_style == "sleeve_around_center_leg":
        axis.add_patch(
            Rectangle(
                (layout.winding_region_x_mm, layout.winding_region_y_mm),
                layout.winding_region_width_mm,
                layout.winding_region_height_mm,
                facecolor="none",
                edgecolor="#1d4ed8",
                linewidth=1.0,
                linestyle="--",
            )
        )
        _draw_winding_profile(
            axis,
            layout,
            outer_x_mm=layout.winding_block_x_mm,
            outer_y_mm=layout.winding_block_y_mm,
            outer_width_mm=layout.winding_block_width_mm,
            outer_height_mm=layout.winding_block_height_mm,
            opening_x_mm=layout.winding_inner_opening_x_mm,
            opening_y_mm=layout.winding_inner_opening_y_mm,
            opening_width_mm=layout.winding_inner_opening_width_mm,
            opening_height_mm=layout.winding_inner_opening_height_mm,
            opening_fill="none",
            alpha=0.55,
        )

    if layout.gap_mm is not None:
        gap_height_mm = max(layout.gap_mm, 0.15)
        axis.add_patch(
            Rectangle(
                (0.5 * width_mm - 0.5 * center_leg_mm, split_y - 0.5 * gap_height_mm),
                center_leg_mm,
                gap_height_mm,
                facecolor="#ffffff",
                edgecolor="#ef4444",
                linewidth=1.0,
                zorder=5,
            )
        )
        axis.annotate(
            _fmt_mm(layout.gap_mm),
            xy=(0.5 * width_mm, split_y),
            xytext=(0.74 * width_mm, split_y + 0.12 * height_mm),
            arrowprops={"arrowstyle": "->", "linewidth": 0.9, "color": "#b91c1c"},
            fontsize=8,
            color="#b91c1c",
            ha="left",
            va="bottom",
        )

    _dimension_line(axis, 0.0, width_mm, -2.0, f"W {_fmt_mm(width_mm)}", vertical=False)
    _dimension_line(axis, 0.0, height_mm, -2.0, f"H {_fmt_mm(height_mm)}", vertical=True)
    axis.text(0.5 * width_mm, 1.2, f"center leg {_fmt_mm(center_leg_mm)}", ha="center", va="bottom", fontsize=8, color="#374151")
    axis.text(0.5 * width_mm, window_y + window_height_mm + 0.8, f"2x window {_fmt_mm(window_width_mm)} x {_fmt_mm(window_height_mm)}", ha="center", va="bottom", fontsize=7.8, color="#374151")
    if layout.winding_geometry_style == "sleeve_around_center_leg":
        axis.text(
            0.5 * width_mm,
            layout.winding_region_y_mm + layout.winding_region_height_mm + 1.0,
            f"center-leg winding\n{layout.winding_geometry_style}",
            ha="center",
            va="bottom",
            fontsize=7.8,
            color="#1d4ed8",
        )
    axis.text(width_mm + 0.8, 0.5 * half_height_mm, "lower half", ha="left", va="center", fontsize=8, color="#374151")
    axis.text(width_mm + 0.8, height_mm - 0.5 * half_height_mm, "upper half", ha="left", va="center", fontsize=8, color="#374151")


def _draw_winding_view(axis, layout: InductorGeometryLayout, *, shared_span_x_mm: float, shared_span_y_mm: float) -> None:
    _configure_axis(
        axis,
        layout.winding_region_width_mm,
        layout.winding_region_height_mm,
        title="Winding Geometry",
        shared_span_x_mm=shared_span_x_mm,
        shared_span_y_mm=shared_span_y_mm,
    )
    axis.add_patch(
        Rectangle(
            (0.0, 0.0),
            layout.winding_region_width_mm,
            layout.winding_region_height_mm,
            facecolor="#f8fafc",
            edgecolor="#111827",
            linewidth=1.3,
            linestyle="--",
        )
    )
    winding_x = layout.winding_block_x_mm - layout.winding_region_x_mm
    winding_y = layout.winding_block_y_mm - layout.winding_region_y_mm
    opening_x = (
        None
        if layout.winding_inner_opening_x_mm is None
        else layout.winding_inner_opening_x_mm - layout.winding_region_x_mm
    )
    opening_y = (
        None
        if layout.winding_inner_opening_y_mm is None
        else layout.winding_inner_opening_y_mm - layout.winding_region_y_mm
    )
    _draw_winding_profile(
        axis,
        layout,
        outer_x_mm=winding_x,
        outer_y_mm=winding_y,
        outer_width_mm=layout.winding_block_width_mm,
        outer_height_mm=layout.winding_block_height_mm,
        opening_x_mm=opening_x,
        opening_y_mm=opening_y,
        opening_width_mm=layout.winding_inner_opening_width_mm,
        opening_height_mm=layout.winding_inner_opening_height_mm,
        opening_fill="#d9dde6",
        alpha=0.85,
    )
    axis.text(
        0.02,
        0.98,
        (
            f"turns = {layout.turns}\n"
            f"parallels = {layout.parallels}\n"
            f"wire = {layout.wire_name}\n"
            f"placement = {layout.winding_placement}\n"
            f"style = {layout.winding_geometry_style}\n"
            f"method = {layout.winding_estimation_method}\n"
            f"bundle = {_fmt_mm(layout.winding_equivalent_bundle_diameter_mm)}\n"
            f"layers = {_fmt_int(layout.winding_layers)} / tpl = {_fmt_int(layout.winding_turns_per_layer)}\n"
            f"fit = {_fmt_fit(layout)}\n"
            f"fill = {_fmt_fill(layout.fill_factor)}"
        ),
        transform=axis.transAxes,
        va="top",
        ha="left",
        fontsize=8.4,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#ffffff", "edgecolor": "#d1d5db"},
    )
    _dimension_line(axis, 0.0, layout.winding_region_width_mm, -1.8, f"zone {_fmt_mm(layout.winding_region_width_mm)}", vertical=False)
    _dimension_line(axis, 0.0, layout.winding_region_height_mm, -1.8, f"zone {_fmt_mm(layout.winding_region_height_mm)}", vertical=True)
    axis.text(
        0.5 * layout.winding_region_width_mm,
        winding_y + layout.winding_block_height_mm + 0.7,
        f"occupied {_fmt_mm(layout.winding_block_width_mm)} x {_fmt_mm(layout.winding_block_height_mm)}",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#1e3a8a",
    )
    axis.text(
        0.5 * layout.winding_region_width_mm,
        0.5,
        f"depth {_fmt_mm(layout.winding_block_depth_mm)}",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#1e3a8a",
    )
    _add_scale_bar(axis, layout.scale_bar_mm)


def _draw_assembly_view(axis, layout: InductorGeometryLayout, *, shared_span_x_mm: float, shared_span_y_mm: float) -> None:
    total_depth_draw_mm = _assembly_stack_draw_depth_mm(layout)
    _configure_axis(
        axis,
        layout.overall_width_mm,
        total_depth_draw_mm,
        title="Assembly Geometry",
        shared_span_x_mm=shared_span_x_mm,
        shared_span_y_mm=shared_span_y_mm,
    )
    element_depth_mm = layout.outer_depth_mm
    gap_between_mm = _assembly_gap_between_mm(layout)
    origin_y = 0.0
    for index in range(layout.stack_count):
        y = origin_y + index * (element_depth_mm + gap_between_mm)
        axis.add_patch(
            Rectangle(
                (0.0, y),
                layout.overall_width_mm,
                element_depth_mm,
                facecolor="#d9dde6",
                edgecolor="#111827",
                linewidth=1.3,
            )
        )
        axis.add_patch(
            Rectangle(
                (layout.winding_region_x_mm, y + 0.18 * element_depth_mm),
                layout.winding_region_width_mm,
                0.64 * element_depth_mm,
                facecolor="#f8fafc",
                edgecolor="#111827",
                linewidth=1.0,
                linestyle="--",
            )
        )
        envelope_y_mm = y + (0.5 * (element_depth_mm - layout.winding_block_depth_mm))
        opening_y_mm = (
            None
            if layout.winding_inner_opening_depth_mm is None
            else y + (0.5 * (element_depth_mm - layout.winding_inner_opening_depth_mm))
        )
        _draw_winding_profile(
            axis,
            layout,
            outer_x_mm=layout.winding_block_x_mm,
            outer_y_mm=envelope_y_mm,
            outer_width_mm=layout.winding_block_width_mm,
            outer_height_mm=layout.winding_block_depth_mm,
            opening_x_mm=layout.winding_inner_opening_x_mm,
            opening_y_mm=opening_y_mm,
            opening_width_mm=layout.winding_inner_opening_width_mm,
            opening_height_mm=layout.winding_inner_opening_depth_mm,
            opening_fill="#d9dde6",
            alpha=0.55,
        )
        if layout.template_name == "paired_etd_core":
            shoulder_inset_mm = max(0.08 * layout.overall_width_mm, 0.34 * (layout.side_leg_width_mm or (0.14 * layout.overall_width_mm)))
            axis.plot([0.0, shoulder_inset_mm], [y + element_depth_mm, y], color="#111827", linewidth=1.0)
            axis.plot(
                [layout.overall_width_mm, layout.overall_width_mm - shoulder_inset_mm],
                [y + element_depth_mm, y],
                color="#111827",
                linewidth=1.0,
            )
    axis.text(
        0.02,
        0.98,
        (
            f"assembly = {layout.assembly_type}\n"
            f"stack_count = {layout.stack_count}\n"
            f"bbox = {_fmt_mm(layout.overall_width_mm)} x {_fmt_mm(layout.overall_height_mm)} x {_fmt_mm(layout.overall_depth_mm)}"
        ),
        transform=axis.transAxes,
        va="top",
        ha="left",
        fontsize=8.4,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#ffffff", "edgecolor": "#d1d5db"},
    )
    _dimension_line(axis, 0.0, layout.overall_width_mm, -1.8, f"W {_fmt_mm(layout.overall_width_mm)}", vertical=False)
    if layout.stack_count == 1:
        _dimension_line(axis, origin_y, origin_y + element_depth_mm, -1.8, f"D {_fmt_mm(layout.overall_depth_mm)}", vertical=True)
    else:
        _dimension_line(axis, origin_y, origin_y + element_depth_mm, -1.8, f"body {_fmt_mm(layout.outer_depth_mm)}", vertical=True)
        axis.text(
            layout.overall_width_mm + 0.8,
            origin_y + total_depth_draw_mm,
            f"physical stack depth {_fmt_mm(layout.overall_depth_mm)}",
            ha="left",
            va="top",
            fontsize=8,
            color="#374151",
        )
        axis.annotate(
            "stack direction",
            xy=(layout.overall_width_mm + 0.5, origin_y + total_depth_draw_mm),
            xytext=(layout.overall_width_mm + 0.5, origin_y),
            arrowprops={"arrowstyle": "<->", "color": "#6b7280", "linewidth": 1.0},
            fontsize=8,
            color="#374151",
            rotation=90,
            va="center",
            ha="left",
        )
    _add_scale_bar(axis, layout.scale_bar_mm)


def _configure_axis(
    axis,
    width_mm: float,
    height_mm: float,
    *,
    title: str,
    shared_span_x_mm: float,
    shared_span_y_mm: float,
) -> None:
    margin_x = max(0.5 * (shared_span_x_mm - width_mm), 0.0)
    margin_y = max(0.5 * (shared_span_y_mm - height_mm), 0.0)
    axis.set_xlim(-margin_x, width_mm + margin_x)
    axis.set_ylim(-margin_y, height_mm + margin_y)
    axis.set_title(title, fontsize=10.5, fontweight="bold", pad=4.0)


def _dimension_line(axis, start: float, end: float, offset: float, label: str, *, vertical: bool) -> None:
    if vertical:
        axis.annotate(
            "",
            xy=(offset, start),
            xytext=(offset, end),
            arrowprops={"arrowstyle": "<->", "linewidth": 0.9, "color": "#4b5563"},
        )
        axis.text(offset - 0.4, 0.5 * (start + end), label, rotation=90, va="center", ha="right", fontsize=8, color="#374151")
    else:
        axis.annotate(
            "",
            xy=(start, offset),
            xytext=(end, offset),
            arrowprops={"arrowstyle": "<->", "linewidth": 0.9, "color": "#4b5563"},
        )
        axis.text(0.5 * (start + end), offset - 0.4, label, va="top", ha="center", fontsize=8, color="#374151")


def _draw_winding_profile(
    axis,
    layout: InductorGeometryLayout,
    *,
    outer_x_mm: float,
    outer_y_mm: float,
    outer_width_mm: float,
    outer_height_mm: float,
    opening_x_mm: float | None,
    opening_y_mm: float | None,
    opening_width_mm: float | None,
    opening_height_mm: float | None,
    opening_fill: str | None,
    alpha: float,
) -> None:
    if layout.winding_geometry_style not in {"sleeve_around_leg", "sleeve_around_center_leg"} or None in (
        opening_x_mm,
        opening_y_mm,
        opening_width_mm,
        opening_height_mm,
    ):
        axis.add_patch(
            Rectangle(
                (outer_x_mm, outer_y_mm),
                outer_width_mm,
                outer_height_mm,
                facecolor="#93c5fd",
                edgecolor="#1d4ed8",
                linewidth=1.1,
                alpha=alpha,
            )
        )
        return

    opening_x_resolved = float(opening_x_mm)
    opening_y_resolved = float(opening_y_mm)
    opening_width_resolved = float(opening_width_mm)
    opening_height_resolved = float(opening_height_mm)
    left_width_mm = max(opening_x_resolved - outer_x_mm, 0.0)
    right_width_mm = max((outer_x_mm + outer_width_mm) - (opening_x_resolved + opening_width_resolved), 0.0)
    bottom_height_mm = max(opening_y_resolved - outer_y_mm, 0.0)
    top_height_mm = max((outer_y_mm + outer_height_mm) - (opening_y_resolved + opening_height_resolved), 0.0)

    segments: list[tuple[float, float, float, float]] = []
    if left_width_mm > 0.0:
        segments.append((outer_x_mm, outer_y_mm, left_width_mm, outer_height_mm))
    if right_width_mm > 0.0:
        segments.append((opening_x_resolved + opening_width_resolved, outer_y_mm, right_width_mm, outer_height_mm))
    if bottom_height_mm > 0.0:
        segments.append((opening_x_resolved, outer_y_mm, opening_width_resolved, bottom_height_mm))
    if top_height_mm > 0.0:
        segments.append((opening_x_resolved, opening_y_resolved + opening_height_resolved, opening_width_resolved, top_height_mm))

    for x_mm, y_mm, width_mm, height_mm in segments:
        axis.add_patch(
            Rectangle(
                (x_mm, y_mm),
                width_mm,
                height_mm,
                facecolor="#93c5fd",
                edgecolor="#1d4ed8",
                linewidth=1.1,
                alpha=alpha,
            )
        )
    axis.add_patch(
        Rectangle(
            (outer_x_mm, outer_y_mm),
            outer_width_mm,
            outer_height_mm,
            facecolor="none",
            edgecolor="#1d4ed8",
            linewidth=1.0,
        )
    )
    axis.add_patch(
        Rectangle(
            (opening_x_resolved, opening_y_resolved),
            opening_width_resolved,
            opening_height_resolved,
            facecolor=("none" if opening_fill is None else opening_fill),
            edgecolor="#1f2937",
            linewidth=1.0,
        )
    )


def _add_scale_bar(axis, scale_bar_mm: float) -> None:
    x0, x1 = axis.get_xlim()
    y0, y1 = axis.get_ylim()
    start_x = x0 + 0.08 * (x1 - x0)
    y = y0 + 0.12 * (y1 - y0)
    axis.plot([start_x, start_x + scale_bar_mm], [y, y], color="#111827", linewidth=2.2, solid_capstyle="butt")
    axis.plot([start_x, start_x], [y - 0.35, y + 0.35], color="#111827", linewidth=1.2)
    axis.plot([start_x + scale_bar_mm, start_x + scale_bar_mm], [y - 0.35, y + 0.35], color="#111827", linewidth=1.2)
    axis.text(start_x + 0.5 * scale_bar_mm, y + 0.7, _fmt_mm(scale_bar_mm), ha="center", va="bottom", fontsize=8, color="#111827")


def _resolve_panel_frames(layout: InductorGeometryLayout) -> dict[str, _PanelFrame]:
    assembly_height_mm = _assembly_stack_draw_depth_mm(layout)
    return {
        "core": _PanelFrame(
            width_mm=layout.outer_width_mm,
            height_mm=layout.outer_height_mm,
            pad_x_mm=max(0.28 * layout.outer_width_mm, 10.0),
            pad_y_mm=max(0.28 * layout.outer_height_mm, 8.0),
        ),
        "winding": _PanelFrame(
            width_mm=layout.winding_region_width_mm,
            height_mm=layout.winding_region_height_mm,
            pad_x_mm=max(0.32 * layout.winding_region_width_mm, 8.0),
            pad_y_mm=max(0.34 * layout.winding_region_height_mm, 8.0),
        ),
        "assembly": _PanelFrame(
            width_mm=layout.overall_width_mm,
            height_mm=assembly_height_mm,
            pad_x_mm=max(0.26 * layout.overall_width_mm, 8.0),
            pad_y_mm=max(0.28 * assembly_height_mm, 8.0),
        ),
    }


def _assembly_gap_between_mm(layout: InductorGeometryLayout) -> float:
    if layout.stack_count <= 1:
        return 0.0
    return max(0.08 * layout.outer_depth_mm, 0.4)


def _assembly_stack_draw_depth_mm(layout: InductorGeometryLayout) -> float:
    gap_between_mm = _assembly_gap_between_mm(layout)
    return (layout.stack_count * layout.outer_depth_mm) + (max(layout.stack_count - 1, 0) * gap_between_mm)


def _fmt_mm(value_mm: float | None) -> str:
    if value_mm is None:
        return "n/a"
    return f"{float(value_mm):.3g} mm"


def _fmt_mm2(value_mm2: float | None) -> str:
    if value_mm2 is None:
        return "n/a"
    return f"{float(value_mm2):.3g} mm^2"


def _fmt_fill(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{100.0 * float(value):.1f}%"


def _fmt_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(int(value))


def _fmt_fit(layout: InductorGeometryLayout) -> str:
    if layout.winding_fit_clamped:
        return "clamped"
    if layout.winding_fit_axial_ok and layout.winding_fit_radial_ok and layout.winding_fit_inner_opening_ok:
        return "ok"
    return "limited"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _resolve_scale_bar_mm(max_dimension_mm: float) -> float:
    target_mm = 0.30 * max_dimension_mm
    power = 10.0 ** math.floor(math.log10(max(target_mm, 1.0)))
    for factor in (1.0, 2.0, 5.0, 10.0):
        candidate = factor * power
        if candidate >= target_mm:
            return candidate
    return 10.0 * power
