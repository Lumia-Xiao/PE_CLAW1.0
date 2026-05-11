"""Core-template resolution for first-pass engineering geometry drawings."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ...utils.core_family_semantics import is_paired_half_core_family


@dataclass(frozen=True)
class CoreTemplateGeometry:
    """Resolved drawing dimensions for one supported core template."""

    template_name: str
    outer_width_mm: float
    outer_height_mm: float
    outer_depth_mm: float
    window_width_mm: float
    window_height_mm: float
    effective_winding_window_width_mm: float
    effective_winding_window_height_mm: float
    center_leg_width_mm: float | None = None
    side_leg_width_mm: float | None = None
    top_yoke_height_mm: float | None = None
    bottom_yoke_height_mm: float | None = None
    inner_diameter_mm: float | None = None
    library_half_height_mm: float | None = None
    notes: list[str] = field(default_factory=list)


def resolve_core_template_geometry(
    *,
    core_family: str,
    outer_width_mm: float,
    outer_height_mm: float,
    outer_depth_mm: float,
    effective_area_mm2: float | None,
    effective_window_area_mm2: float | None,
    library_half_height_mm: float | None = None,
) -> CoreTemplateGeometry:
    """Resolve a parameterized template geometry for the available core family."""
    family = (core_family or "").strip().lower()
    if family == "t":
        return _build_toroid_geometry(
            outer_width_mm=outer_width_mm,
            outer_height_mm=outer_height_mm,
            outer_depth_mm=outer_depth_mm,
            effective_area_mm2=effective_area_mm2,
            effective_window_area_mm2=effective_window_area_mm2,
        )
    if family == "u":
        return _build_u_geometry(
            outer_width_mm=outer_width_mm,
            outer_height_mm=outer_height_mm,
            outer_depth_mm=outer_depth_mm,
            effective_window_area_mm2=effective_window_area_mm2,
            library_half_height_mm=library_half_height_mm,
        )
    if family == "etd":
        return _build_paired_etd_geometry(
            outer_width_mm=outer_width_mm,
            outer_height_mm=outer_height_mm,
            outer_depth_mm=outer_depth_mm,
            effective_area_mm2=effective_area_mm2,
            effective_window_area_mm2=effective_window_area_mm2,
            library_half_height_mm=library_half_height_mm,
        )
    if family in {"e", "pq", "rm"} or (is_paired_half_core_family(family) and family not in {"u", "etd"}):
        return _build_paired_box_window_geometry(
            core_family=family or "unknown",
            outer_width_mm=outer_width_mm,
            outer_height_mm=outer_height_mm,
            outer_depth_mm=outer_depth_mm,
            effective_area_mm2=effective_area_mm2,
            effective_window_area_mm2=effective_window_area_mm2,
            library_half_height_mm=library_half_height_mm,
        )
    return _build_box_window_geometry(
        core_family=family or "unknown",
        outer_width_mm=outer_width_mm,
        outer_height_mm=outer_height_mm,
        outer_depth_mm=outer_depth_mm,
        effective_area_mm2=effective_area_mm2,
        effective_window_area_mm2=effective_window_area_mm2,
    )


def _build_toroid_geometry(
    *,
    outer_width_mm: float,
    outer_height_mm: float,
    outer_depth_mm: float,
    effective_area_mm2: float | None,
    effective_window_area_mm2: float | None,
) -> CoreTemplateGeometry:
    notes: list[str] = []
    thickness_mm = None
    if effective_area_mm2 is not None and outer_depth_mm > 0.0:
        thickness_mm = effective_area_mm2 / outer_depth_mm
        notes.append("Toroid inner diameter was derived from Ae and core depth.")
    if thickness_mm is None or thickness_mm <= 0.0:
        thickness_mm = 0.18 * outer_width_mm
        notes.append("Toroid section thickness used a first-pass width-based fallback.")

    inner_diameter_mm = max(0.20 * outer_width_mm, min(outer_width_mm - (2.0 * thickness_mm), 0.85 * outer_width_mm))
    effective_window_side_mm = math.sqrt(max(effective_window_area_mm2 or (0.5 * inner_diameter_mm * inner_diameter_mm), 1e-6))
    effective_window_side_mm = min(effective_window_side_mm, 0.92 * inner_diameter_mm)
    return CoreTemplateGeometry(
        template_name="toroid_ring",
        outer_width_mm=outer_width_mm,
        outer_height_mm=outer_height_mm,
        outer_depth_mm=outer_depth_mm,
        window_width_mm=inner_diameter_mm,
        window_height_mm=inner_diameter_mm,
        effective_winding_window_width_mm=effective_window_side_mm,
        effective_winding_window_height_mm=effective_window_side_mm,
        inner_diameter_mm=inner_diameter_mm,
        notes=notes,
    )


def _build_u_geometry(
    *,
    outer_width_mm: float,
    outer_height_mm: float,
    outer_depth_mm: float,
    effective_window_area_mm2: float | None,
    library_half_height_mm: float | None,
) -> CoreTemplateGeometry:
    notes: list[str] = [
        "U-family geometry is rendered as two explicit half cores paired in the height direction.",
    ]
    half_core_height_mm = library_half_height_mm or (0.5 * outer_height_mm)
    leg_width_mm = 0.18 * outer_width_mm
    window_width_mm = max(outer_width_mm - (2.0 * leg_width_mm), 0.34 * outer_width_mm)
    if effective_window_area_mm2 is not None and window_width_mm > 0.0:
        window_height_mm = effective_window_area_mm2 / window_width_mm
        notes.append("U-core paired-window height was derived from Aw and the estimated leg spacing.")
    else:
        window_height_mm = 0.55 * outer_height_mm
        notes.append("U-core paired-window height used a first-pass fallback.")
    window_height_mm = min(max(window_height_mm, 0.28 * outer_height_mm), 0.82 * outer_height_mm)
    yoke_height_mm = max(0.5 * (outer_height_mm - window_height_mm), 0.14 * half_core_height_mm)
    return CoreTemplateGeometry(
        template_name="u_paired_core",
        outer_width_mm=outer_width_mm,
        outer_height_mm=outer_height_mm,
        outer_depth_mm=outer_depth_mm,
        window_width_mm=window_width_mm,
        window_height_mm=window_height_mm,
        effective_winding_window_width_mm=0.90 * window_width_mm,
        effective_winding_window_height_mm=0.90 * window_height_mm,
        side_leg_width_mm=leg_width_mm,
        top_yoke_height_mm=yoke_height_mm,
        bottom_yoke_height_mm=yoke_height_mm,
        library_half_height_mm=half_core_height_mm,
        notes=notes,
    )


def _build_paired_etd_geometry(
    *,
    outer_width_mm: float,
    outer_height_mm: float,
    outer_depth_mm: float,
    effective_area_mm2: float | None,
    effective_window_area_mm2: float | None,
    library_half_height_mm: float | None,
) -> CoreTemplateGeometry:
    notes = [
        "ETD-family geometry uses a dedicated paired ETD engineering template instead of the generic paired-box placeholder.",
    ]
    center_leg_width_mm = None
    if effective_area_mm2 is not None and outer_depth_mm > 0.0:
        center_leg_width_mm = effective_area_mm2 / outer_depth_mm
        notes.append("ETD center-leg width was derived from Ae and core depth.")
    if center_leg_width_mm is None or center_leg_width_mm <= 0.0:
        center_leg_width_mm = 0.20 * outer_width_mm
        notes.append("ETD center-leg width used a first-pass fallback.")

    half_core_height_mm = library_half_height_mm or (0.5 * outer_height_mm)
    side_leg_width_mm = max(0.15 * outer_width_mm, 0.82 * center_leg_width_mm)
    waist_outer_width_mm = outer_width_mm - (2.0 * max(0.08 * outer_width_mm, 0.34 * side_leg_width_mm))
    total_window_width_mm = max(waist_outer_width_mm - center_leg_width_mm - (2.0 * side_leg_width_mm), 0.18 * outer_width_mm)
    each_window_width_mm = 0.5 * total_window_width_mm
    if effective_window_area_mm2 is not None and total_window_width_mm > 0.0:
        window_height_mm = effective_window_area_mm2 / max(total_window_width_mm, 1e-6)
        notes.append("ETD paired-window height was derived from Aw and the narrowed ETD window waist.")
    else:
        window_height_mm = 0.42 * outer_height_mm
        notes.append("ETD paired-window height used a first-pass fallback.")
    window_height_mm = min(max(window_height_mm, 0.26 * outer_height_mm), 0.62 * outer_height_mm)
    yoke_height_mm = max(0.5 * (outer_height_mm - window_height_mm), 0.18 * half_core_height_mm)
    effective_winding_window_width_mm = max(center_leg_width_mm + (2.0 * each_window_width_mm), center_leg_width_mm)
    return CoreTemplateGeometry(
        template_name="paired_etd_core",
        outer_width_mm=outer_width_mm,
        outer_height_mm=outer_height_mm,
        outer_depth_mm=outer_depth_mm,
        window_width_mm=each_window_width_mm,
        window_height_mm=window_height_mm,
        effective_winding_window_width_mm=effective_winding_window_width_mm,
        effective_winding_window_height_mm=0.90 * window_height_mm,
        center_leg_width_mm=center_leg_width_mm,
        side_leg_width_mm=side_leg_width_mm,
        top_yoke_height_mm=yoke_height_mm,
        bottom_yoke_height_mm=yoke_height_mm,
        library_half_height_mm=half_core_height_mm,
        notes=notes,
    )


def _build_paired_box_window_geometry(
    *,
    core_family: str,
    outer_width_mm: float,
    outer_height_mm: float,
    outer_depth_mm: float,
    effective_area_mm2: float | None,
    effective_window_area_mm2: float | None,
    library_half_height_mm: float | None,
) -> CoreTemplateGeometry:
    notes = [
        f"{core_family.upper()}-family geometry is rendered as two explicit mating halves paired in the height direction.",
    ]
    center_leg_width_mm = None
    if effective_area_mm2 is not None and outer_depth_mm > 0.0:
        center_leg_width_mm = effective_area_mm2 / outer_depth_mm
        notes.append("Center-leg width was derived from Ae and core depth.")
    if center_leg_width_mm is None or center_leg_width_mm <= 0.0:
        center_leg_width_mm = 0.18 * outer_width_mm
        notes.append("Center-leg width used a first-pass fallback.")

    side_leg_width_mm = max(0.12 * outer_width_mm, 0.80 * center_leg_width_mm)
    total_window_width_mm = max(outer_width_mm - center_leg_width_mm - (2.0 * side_leg_width_mm), 0.24 * outer_width_mm)
    each_window_width_mm = 0.5 * total_window_width_mm
    if effective_window_area_mm2 is not None and total_window_width_mm > 0.0:
        window_height_mm = effective_window_area_mm2 / max(total_window_width_mm, 1e-6)
        notes.append("Paired-window height was derived from Aw and the estimated dual-window width.")
    else:
        window_height_mm = 0.45 * outer_height_mm
        notes.append("Paired-window height used a first-pass fallback.")
    window_height_mm = min(max(window_height_mm, 0.24 * outer_height_mm), 0.72 * outer_height_mm)
    half_core_height_mm = library_half_height_mm or (0.5 * outer_height_mm)
    yoke_height_mm = max(0.5 * (outer_height_mm - window_height_mm), 0.14 * half_core_height_mm)
    effective_winding_window_width_mm = max(center_leg_width_mm + (2.0 * each_window_width_mm), center_leg_width_mm)
    return CoreTemplateGeometry(
        template_name="paired_box_core",
        outer_width_mm=outer_width_mm,
        outer_height_mm=outer_height_mm,
        outer_depth_mm=outer_depth_mm,
        window_width_mm=each_window_width_mm,
        window_height_mm=window_height_mm,
        effective_winding_window_width_mm=effective_winding_window_width_mm,
        effective_winding_window_height_mm=0.92 * window_height_mm,
        center_leg_width_mm=center_leg_width_mm,
        side_leg_width_mm=side_leg_width_mm,
        top_yoke_height_mm=yoke_height_mm,
        bottom_yoke_height_mm=yoke_height_mm,
        library_half_height_mm=half_core_height_mm,
        notes=notes,
    )


def _build_box_window_geometry(
    *,
    core_family: str,
    outer_width_mm: float,
    outer_height_mm: float,
    outer_depth_mm: float,
    effective_area_mm2: float | None,
    effective_window_area_mm2: float | None,
) -> CoreTemplateGeometry:
    notes = [f"Core family '{core_family}' uses a generic box-window engineering template."]
    center_leg_width_mm = None
    if effective_area_mm2 is not None and outer_depth_mm > 0.0:
        center_leg_width_mm = effective_area_mm2 / outer_depth_mm
        notes.append("Center-leg width was derived from Ae and core depth.")
    if center_leg_width_mm is None or center_leg_width_mm <= 0.0:
        center_leg_width_mm = 0.18 * outer_width_mm
        notes.append("Center-leg width used a first-pass fallback.")

    side_leg_width_mm = max(0.12 * outer_width_mm, 0.80 * center_leg_width_mm)
    total_window_width_mm = max(outer_width_mm - center_leg_width_mm - (2.0 * side_leg_width_mm), 0.24 * outer_width_mm)
    each_window_width_mm = 0.5 * total_window_width_mm
    if effective_window_area_mm2 is not None and each_window_width_mm > 0.0:
        window_height_mm = effective_window_area_mm2 / max(total_window_width_mm, 1e-6)
        notes.append("Window height was derived from Aw and the estimated dual-window width.")
    else:
        window_height_mm = 0.45 * outer_height_mm
        notes.append("Window height used a first-pass fallback.")
    window_height_mm = min(max(window_height_mm, 0.24 * outer_height_mm), 0.72 * outer_height_mm)
    yoke_height_mm = max(0.5 * (outer_height_mm - window_height_mm), 0.12 * outer_height_mm)
    effective_winding_window_width_mm = max(center_leg_width_mm * 1.25, 0.85 * center_leg_width_mm)
    effective_winding_window_width_mm = min(effective_winding_window_width_mm, outer_width_mm - (2.0 * side_leg_width_mm))
    return CoreTemplateGeometry(
        template_name="box_window",
        outer_width_mm=outer_width_mm,
        outer_height_mm=outer_height_mm,
        outer_depth_mm=outer_depth_mm,
        window_width_mm=each_window_width_mm,
        window_height_mm=window_height_mm,
        effective_winding_window_width_mm=effective_winding_window_width_mm,
        effective_winding_window_height_mm=0.92 * window_height_mm,
        center_leg_width_mm=center_leg_width_mm,
        side_leg_width_mm=side_leg_width_mm,
        top_yoke_height_mm=yoke_height_mm,
        bottom_yoke_height_mm=yoke_height_mm,
        notes=notes,
    )
