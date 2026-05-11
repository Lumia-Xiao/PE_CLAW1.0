"""Shared Matplotlib 3D engineering drawing primitives."""

from __future__ import annotations

from mpl_toolkits.mplot3d.art3d import Poly3DCollection

MUTED_METAL_FACE = "#cfd4dd"
MUTED_METAL_FACE_ALT = "#bcc6d4"
DARK_OUTLINE = "#1f2937"
PACKAGE_BODY_FACE = "#1f2937"
SILVER_LEAD_FACE = "#9ca3af"
TEXT_BOX_STYLE = {"boxstyle": "round,pad=0.35", "facecolor": "#ffffff", "edgecolor": "#d1d5db"}


def add_box_3d(
    axis,
    x_mm: float,
    y_mm: float,
    z_mm: float,
    dx_mm: float,
    dy_mm: float,
    dz_mm: float,
    *,
    facecolor: str,
    edgecolor: str = DARK_OUTLINE,
    alpha: float = 0.62,
    linewidth: float = 0.7,
    gid: str | None = None,
) -> Poly3DCollection:
    """Add one physical cuboid to a Matplotlib mplot3d axis."""

    x0_mm, x1_mm = x_mm, x_mm + dx_mm
    y0_mm, y1_mm = y_mm, y_mm + dy_mm
    z0_mm, z1_mm = z_mm, z_mm + dz_mm
    vertices = [
        (x0_mm, y0_mm, z0_mm),
        (x1_mm, y0_mm, z0_mm),
        (x1_mm, y1_mm, z0_mm),
        (x0_mm, y1_mm, z0_mm),
        (x0_mm, y0_mm, z1_mm),
        (x1_mm, y0_mm, z1_mm),
        (x1_mm, y1_mm, z1_mm),
        (x0_mm, y1_mm, z1_mm),
    ]
    faces = [
        [vertices[index] for index in (0, 1, 2, 3)],
        [vertices[index] for index in (4, 5, 6, 7)],
        [vertices[index] for index in (0, 1, 5, 4)],
        [vertices[index] for index in (2, 3, 7, 6)],
        [vertices[index] for index in (1, 2, 6, 5)],
        [vertices[index] for index in (0, 3, 7, 4)],
    ]
    collection = Poly3DCollection(
        faces,
        facecolors=facecolor,
        edgecolors=edgecolor,
        linewidths=linewidth,
        alpha=alpha,
    )
    if gid is not None:
        collection.set_gid(gid)
    axis.add_collection3d(collection)
    return collection


def add_box_outline_3d(
    axis,
    x_mm: float,
    y_mm: float,
    z_mm: float,
    dx_mm: float,
    dy_mm: float,
    dz_mm: float,
    *,
    color: str = DARK_OUTLINE,
    linewidth: float = 1.0,
    gid: str | None = None,
) -> list[object]:
    """Draw the twelve outline edges for one cuboid."""

    x0_mm, x1_mm = x_mm, x_mm + dx_mm
    y0_mm, y1_mm = y_mm, y_mm + dy_mm
    z0_mm, z1_mm = z_mm, z_mm + dz_mm
    edges = [
        ((x0_mm, y0_mm, z0_mm), (x1_mm, y0_mm, z0_mm)),
        ((x1_mm, y0_mm, z0_mm), (x1_mm, y1_mm, z0_mm)),
        ((x1_mm, y1_mm, z0_mm), (x0_mm, y1_mm, z0_mm)),
        ((x0_mm, y1_mm, z0_mm), (x0_mm, y0_mm, z0_mm)),
        ((x0_mm, y0_mm, z1_mm), (x1_mm, y0_mm, z1_mm)),
        ((x1_mm, y0_mm, z1_mm), (x1_mm, y1_mm, z1_mm)),
        ((x1_mm, y1_mm, z1_mm), (x0_mm, y1_mm, z1_mm)),
        ((x0_mm, y1_mm, z1_mm), (x0_mm, y0_mm, z1_mm)),
        ((x0_mm, y0_mm, z0_mm), (x0_mm, y0_mm, z1_mm)),
        ((x1_mm, y0_mm, z0_mm), (x1_mm, y0_mm, z1_mm)),
        ((x1_mm, y1_mm, z0_mm), (x1_mm, y1_mm, z1_mm)),
        ((x0_mm, y1_mm, z0_mm), (x0_mm, y1_mm, z1_mm)),
    ]
    lines: list[object] = []
    for start, end in edges:
        (line,) = axis.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            [start[2], end[2]],
            color=color,
            linewidth=linewidth,
        )
        if gid is not None:
            line.set_gid(gid)
        lines.append(line)
    return lines


def configure_engineering_3d_axis(
    axis,
    *,
    title: str,
    elev: float = 24.0,
    azim: float = -56.0,
) -> None:
    """Apply the PE-Claw static engineering 3D camera and hidden-axis style."""

    axis.view_init(elev=elev, azim=azim)
    axis.set_proj_type("persp")
    axis.set_title(title, fontsize=10.5, fontweight="bold", pad=10.0)
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_zticks([])
    axis.grid(False)
    for axis_entry in (axis.xaxis, axis.yaxis, axis.zaxis):
        axis_entry.pane.set_alpha(0.0)
        axis_entry.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
        axis_entry.line.set_color((1.0, 1.0, 1.0, 0.0))


def set_equal_physical_box_aspect(
    axis,
    *,
    center_x_mm: float,
    center_y_mm: float,
    center_z_mm: float,
    total_span_x_mm: float,
    total_span_y_mm: float,
    total_span_z_mm: float,
) -> None:
    """Set axis limits and box aspect from one physical millimeter extent."""

    axis.set_xlim(center_x_mm - 0.5 * total_span_x_mm, center_x_mm + 0.5 * total_span_x_mm)
    axis.set_ylim(center_y_mm - 0.5 * total_span_y_mm, center_y_mm + 0.5 * total_span_y_mm)
    axis.set_zlim(center_z_mm - 0.5 * total_span_z_mm, center_z_mm + 0.5 * total_span_z_mm)
    axis.set_box_aspect((total_span_x_mm, total_span_y_mm, total_span_z_mm))
