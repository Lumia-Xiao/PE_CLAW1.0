"""Derive a parameterized geometry layout from a selected magnetic design."""

from __future__ import annotations

import math
import re

from ...models.geometry_result import InductorGeometryLayout
from ...models.inductor import FixedInductorDesignCandidate
from ...utils.core_family_semantics import is_paired_half_core_family, resolve_core_assembly_envelope
from .core_templates import resolve_core_template_geometry
from .winding_layout import estimate_winding_block
from .winding_size_estimator import WIRE_BUNDLE_OUTER_ENVELOPE_FACTOR, estimate_first_pass_winding_size


def build_inductor_geometry_layout(design: FixedInductorDesignCandidate) -> InductorGeometryLayout:
    """Resolve an engineering-layout model for the selected magnetic design."""
    notes: list[str] = []
    metadata = design.metadata

    core_family = _resolve_core_family(design)
    assembly = _resolve_core_assembly(design, core_family, notes)
    outer_width_mm = assembly.assembled_width_m * 1e3
    outer_height_mm = assembly.assembled_height_m * 1e3
    outer_depth_mm = assembly.assembled_depth_m * 1e3
    effective_area_mm2 = _positive_mm2(metadata.get("core_effective_area_m2"))
    effective_window_area_mm2 = _positive_mm2(metadata.get("core_window_area_m2"))
    if design.stack_count > 1 and effective_area_mm2 is not None:
        effective_area_mm2 = effective_area_mm2 / design.stack_count
        notes.append("Displayed front-view core cross-section uses the per-core effective area; stack growth is shown in depth.")
    if design.stack_count > 1 and effective_window_area_mm2 is not None:
        effective_window_area_mm2 = effective_window_area_mm2 / design.stack_count
        notes.append("Displayed front-view window geometry uses the per-core window area; stack growth is shown in depth.")
    if assembly.library_item_is_half_core:
        notes.extend(assembly.notes)
        notes.append(
            f"Geometry view renders one practical {core_family.upper()} assembly per selected design, not a lone library half core."
        )
    if metadata.get("magnetic_effective_parameter_basis"):
        notes.append(str(metadata["magnetic_effective_parameter_basis"]))

    template = resolve_core_template_geometry(
        core_family=core_family,
        outer_width_mm=outer_width_mm,
        outer_height_mm=outer_height_mm,
        outer_depth_mm=outer_depth_mm,
        effective_area_mm2=effective_area_mm2,
        effective_window_area_mm2=effective_window_area_mm2,
        library_half_height_mm=(assembly.library_height_m * 1e3 if assembly.library_item_is_half_core else None),
    )
    notes.extend(template.notes)

    overall_depth_mm = outer_depth_mm * max(design.stack_count, 1)
    winding_block = estimate_winding_block(
        effective_window_width_mm=template.effective_winding_window_width_mm,
        effective_window_height_mm=template.effective_winding_window_height_mm,
        effective_window_depth_mm=overall_depth_mm,
        fill_factor=design.fill_factor,
        winding_volume_m3=design.winding_volume_m3,
    )
    notes.extend(winding_block.notes)
    winding_placement = _resolve_winding_placement(core_family=core_family, template_name=template.template_name)
    winding_geometry_style = _resolve_winding_geometry_style(
        core_family=core_family,
        template_name=template.template_name,
        winding_placement=winding_placement,
    )
    winding_region = _resolve_nominal_winding_region(
        core_family=core_family,
        outer_width_mm=template.outer_width_mm,
        outer_height_mm=template.outer_height_mm,
        effective_window_width_mm=template.effective_winding_window_width_mm,
        effective_window_height_mm=template.effective_winding_window_height_mm,
        core_window_width_mm=template.window_width_mm,
        side_leg_width_mm=template.side_leg_width_mm,
        winding_placement=winding_placement,
    )
    notes.extend(winding_region["notes"])
    opening_leg_width_mm = _resolve_opening_leg_width_mm(
        center_leg_width_mm=template.center_leg_width_mm,
        side_leg_width_mm=template.side_leg_width_mm,
        winding_geometry_style=winding_geometry_style,
    )
    winding_estimate = estimate_first_pass_winding_size(
        wire_name=design.wire_name,
        turn_count=design.turns,
        parallel_count=design.parallel_bundles,
        available_region_width_mm=winding_region["region_width_mm"],
        available_axial_span_mm=winding_region["region_height_mm"],
        available_depth_mm=overall_depth_mm,
        opening_leg_width_mm=opening_leg_width_mm,
    )
    notes.extend(winding_estimate.notes)
    target_block_width_mm = winding_block.width_mm
    target_block_height_mm = winding_block.height_mm
    target_block_depth_mm = winding_block.depth_mm
    if winding_estimate.method == "bundle_first_pass":
        target_block_width_mm = float(winding_estimate.estimated_outer_width_mm or winding_block.width_mm)
        target_block_height_mm = float(winding_estimate.estimated_outer_height_mm or winding_block.height_mm)
        target_block_depth_mm = float(winding_estimate.estimated_depth_mm or winding_block.depth_mm)

    winding_geometry = _resolve_winding_geometry(
        outer_width_mm=template.outer_width_mm,
        outer_height_mm=template.outer_height_mm,
        core_window_width_mm=template.window_width_mm,
        center_leg_width_mm=template.center_leg_width_mm,
        side_leg_width_mm=template.side_leg_width_mm,
        region_x_mm=winding_region["region_x_mm"],
        region_y_mm=winding_region["region_y_mm"],
        region_width_mm=winding_region["region_width_mm"],
        region_height_mm=winding_region["region_height_mm"],
        target_block_width_mm=target_block_width_mm,
        target_block_height_mm=target_block_height_mm,
        overall_depth_mm=overall_depth_mm,
        target_block_depth_mm=target_block_depth_mm,
        winding_placement=winding_placement,
        winding_geometry_style=winding_geometry_style,
        insulation_margin_mm=winding_estimate.insulation_margin_mm,
    )
    notes.extend(winding_geometry["notes"])
    clamp_shrink_width_pct = _resolve_shrink_pct(target_block_width_mm, float(winding_geometry["block_width_mm"]))
    clamp_shrink_height_pct = _resolve_shrink_pct(target_block_height_mm, float(winding_geometry["block_height_mm"]))
    clamp_shrink_depth_pct = _resolve_shrink_pct(target_block_depth_mm, float(winding_geometry["block_depth_mm"]))
    notes.append(
        "Winding size diagnostics (mm): "
        f"proxy {winding_block.width_mm:.3g} x {winding_block.height_mm:.3g} x {winding_block.depth_mm:.3g}; "
        f"estimated {target_block_width_mm:.3g} x {target_block_height_mm:.3g} x {target_block_depth_mm:.3g}; "
        f"rendered {float(winding_geometry['block_width_mm']):.3g} x {float(winding_geometry['block_height_mm']):.3g} x {float(winding_geometry['block_depth_mm']):.3g}; "
        f"clamp shrink {clamp_shrink_width_pct:.1f}% / {clamp_shrink_height_pct:.1f}% / {clamp_shrink_depth_pct:.1f}%."
    )

    return InductorGeometryLayout(
        design_id=design.candidate_id,
        assembly_type=design.assembly_type or "single_core",
        stack_count=max(design.stack_count, 1),
        core_family=core_family or "unknown",
        template_name=template.template_name,
        base_core_name=design.base_core_name or design.core_name,
        core_name=design.core_name,
        library_item_is_half_core=assembly.library_item_is_half_core,
        half_cores_per_assembly=assembly.half_cores_per_assembly,
        pairing_axis=assembly.pairing_axis,
        material_name=design.material_name,
        wire_name=design.wire_name,
        turns=design.turns,
        parallels=design.parallel_bundles,
        winding_placement=winding_placement,
        winding_geometry_style=winding_geometry_style,
        winding_estimation_method=winding_estimate.method,
        fill_factor=design.fill_factor,
        gap_mm=_positive_mm(design.gap_m),
        gap_position_label=_resolve_gap_position_label(core_family=core_family, is_paired_half_core=assembly.library_item_is_half_core),
        outer_width_mm=template.outer_width_mm,
        outer_height_mm=template.outer_height_mm,
        outer_depth_mm=template.outer_depth_mm,
        core_window_width_mm=template.window_width_mm,
        core_window_height_mm=template.window_height_mm,
        window_width_mm=template.effective_winding_window_width_mm,
        window_height_mm=template.effective_winding_window_height_mm,
        window_depth_mm=overall_depth_mm,
        center_leg_width_mm=template.center_leg_width_mm,
        side_leg_width_mm=template.side_leg_width_mm,
        top_yoke_height_mm=template.top_yoke_height_mm,
        bottom_yoke_height_mm=template.bottom_yoke_height_mm,
        effective_area_mm2=effective_area_mm2,
        effective_window_area_mm2=effective_window_area_mm2,
        winding_region_x_mm=winding_geometry["region_x_mm"],
        winding_region_y_mm=winding_geometry["region_y_mm"],
        winding_region_width_mm=winding_geometry["region_width_mm"],
        winding_region_height_mm=winding_geometry["region_height_mm"],
        winding_proxy_block_width_mm=winding_block.width_mm,
        winding_proxy_block_height_mm=winding_block.height_mm,
        winding_proxy_block_depth_mm=winding_block.depth_mm,
        winding_estimated_outer_width_mm=target_block_width_mm,
        winding_estimated_outer_height_mm=target_block_height_mm,
        winding_estimated_outer_depth_mm=target_block_depth_mm,
        winding_bundle_outer_factor=(
            winding_estimate.bundle_outer_factor if winding_estimate.parsed_wire else WIRE_BUNDLE_OUTER_ENVELOPE_FACTOR
        ),
        winding_strand_count=winding_estimate.strand_count,
        winding_strand_diameter_mm=winding_estimate.strand_diameter_mm,
        winding_equivalent_bundle_diameter_mm=winding_estimate.equivalent_bundle_diameter_mm,
        winding_parallel_columns=winding_estimate.bundle_columns,
        winding_parallel_rows=winding_estimate.bundle_rows,
        winding_per_turn_axial_mm=winding_estimate.per_turn_axial_size_mm,
        winding_per_turn_radial_mm=winding_estimate.per_turn_radial_size_mm,
        winding_turns_per_layer=winding_estimate.turns_per_layer,
        winding_layers=winding_estimate.layers,
        winding_fit_axial_ok=bool(winding_geometry["fit_axial_ok"]),
        winding_fit_radial_ok=bool(winding_geometry["fit_radial_ok"]),
        winding_fit_inner_opening_ok=bool(winding_geometry["fit_inner_opening_ok"]),
        winding_fit_clamped=bool(winding_geometry["fit_clamped"]),
        winding_clamp_shrink_width_pct=clamp_shrink_width_pct,
        winding_clamp_shrink_height_pct=clamp_shrink_height_pct,
        winding_clamp_shrink_depth_pct=clamp_shrink_depth_pct,
        winding_block_x_mm=winding_geometry["block_x_mm"],
        winding_block_y_mm=winding_geometry["block_y_mm"],
        winding_block_z_mm=winding_geometry["block_z_mm"],
        winding_block_width_mm=winding_geometry["block_width_mm"],
        winding_block_height_mm=winding_geometry["block_height_mm"],
        winding_block_depth_mm=winding_geometry["block_depth_mm"],
        winding_inner_opening_x_mm=winding_geometry["opening_x_mm"],
        winding_inner_opening_y_mm=winding_geometry["opening_y_mm"],
        winding_inner_opening_z_mm=winding_geometry["opening_z_mm"],
        winding_inner_opening_width_mm=winding_geometry["opening_width_mm"],
        winding_inner_opening_height_mm=winding_geometry["opening_height_mm"],
        winding_inner_opening_depth_mm=winding_geometry["opening_depth_mm"],
        overall_width_mm=template.outer_width_mm,
        overall_height_mm=template.outer_height_mm,
        overall_depth_mm=overall_depth_mm,
        scale_bar_mm=_resolve_scale_bar_mm(
            template.outer_width_mm,
            template.outer_height_mm,
            overall_depth_mm,
            template.effective_winding_window_width_mm,
            template.effective_winding_window_height_mm,
        ),
        notes=notes + ["Core, winding, and assembly panels use one shared mm-to-pixel scale and one common scale-bar basis."],
    )


def _resolve_core_family(design: FixedInductorDesignCandidate) -> str:
    raw_family = str(design.metadata.get("family") or "").strip().lower()
    if raw_family:
        return raw_family
    for raw_name in (design.core_name, design.base_core_name or "", str(design.metadata.get("shape_label") or "")):
        match = re.match(r"\s*([A-Za-z]+)", raw_name or "")
        if match:
            return match.group(1).lower()
    return "unknown"


def _resolve_winding_placement(*, core_family: str, template_name: str) -> str:
    family = (core_family or "").strip().lower()
    if family == "u" or template_name == "u_paired_core":
        return "side_leg_left"
    if family == "t" or template_name == "toroid_ring":
        return "toroid_wrap"
    return "center_leg"


def _resolve_winding_geometry_style(*, core_family: str, template_name: str, winding_placement: str) -> str:
    family = (core_family or "").strip().lower()
    if winding_placement.startswith("side_leg") and (family == "u" or template_name == "u_paired_core"):
        return "sleeve_around_leg"
    if winding_placement == "center_leg" and family in {"e", "etd"} and template_name in {"paired_box_core", "paired_etd_core"}:
        return "sleeve_around_center_leg"
    return "solid_block"


def _resolve_nominal_winding_region(
    *,
    core_family: str,
    outer_width_mm: float,
    outer_height_mm: float,
    effective_window_width_mm: float,
    effective_window_height_mm: float,
    core_window_width_mm: float,
    side_leg_width_mm: float | None,
    winding_placement: str,
) -> dict[str, float | list[str]]:
    notes: list[str] = []
    region_y_mm = 0.5 * (outer_height_mm - effective_window_height_mm)
    region_width_mm = effective_window_width_mm
    region_height_mm = effective_window_height_mm
    region_x_mm = 0.5 * (outer_width_mm - effective_window_width_mm)

    if winding_placement == "side_leg_left":
        side_leg_mm = side_leg_width_mm or max(0.12 * outer_width_mm, 0.5 * (outer_width_mm - core_window_width_mm))
        region_width_mm = side_leg_mm + effective_window_width_mm
        region_x_mm = -0.5 * (region_width_mm - side_leg_mm)
        notes.append("U-family winding placement uses a deterministic left side-leg position instead of a centered middle-window position.")
        notes.append("U-family winding region now spans a full sleeve zone around the selected side leg: one effective inner-side window width shared across the inner-facing and outer-facing sides around the leg centerline.")
    elif winding_placement == "side_leg_right":
        side_leg_mm = side_leg_width_mm or max(0.12 * outer_width_mm, 0.5 * (outer_width_mm - core_window_width_mm))
        region_width_mm = side_leg_mm + effective_window_width_mm
        region_x_mm = outer_width_mm - side_leg_mm - (0.5 * (region_width_mm - side_leg_mm))
        notes.append("Right-side winding placement uses the mirrored side-leg winding region.")
        notes.append("U-family winding region now spans a full mirrored sleeve zone around the selected side leg.")

    return {
        "region_x_mm": region_x_mm,
        "region_y_mm": region_y_mm,
        "region_width_mm": region_width_mm,
        "region_height_mm": region_height_mm,
        "notes": notes,
    }


def _resolve_opening_leg_width_mm(
    *,
    center_leg_width_mm: float | None,
    side_leg_width_mm: float | None,
    winding_geometry_style: str,
) -> float | None:
    if winding_geometry_style == "sleeve_around_center_leg":
        return center_leg_width_mm
    if winding_geometry_style == "sleeve_around_leg":
        return side_leg_width_mm
    return None


def _resolve_winding_geometry(
    *,
    outer_width_mm: float,
    outer_height_mm: float,
    core_window_width_mm: float,
    center_leg_width_mm: float | None,
    side_leg_width_mm: float | None,
    region_x_mm: float,
    region_y_mm: float,
    region_width_mm: float,
    region_height_mm: float,
    target_block_width_mm: float,
    target_block_height_mm: float,
    overall_depth_mm: float,
    target_block_depth_mm: float,
    winding_placement: str,
    winding_geometry_style: str,
    insulation_margin_mm: float | None,
) -> dict[str, float | bool | list[str] | None]:
    notes: list[str] = []
    block_width_mm = min(target_block_width_mm, region_width_mm)
    block_height_mm = min(target_block_height_mm, region_height_mm)
    fit_axial_ok = target_block_height_mm <= region_height_mm + 1e-9
    fit_radial_ok = target_block_width_mm <= region_width_mm + 1e-9
    fit_clamped = (block_width_mm < target_block_width_mm) or (block_height_mm < target_block_height_mm)
    if fit_clamped:
        notes.append("Final winding fit check clamped the estimated occupied envelope to the chosen local winding region for display.")

    if winding_placement == "side_leg_left":
        side_leg_mm = side_leg_width_mm or max(0.12 * outer_width_mm, 0.5 * (outer_width_mm - core_window_width_mm))
        ideal_block_x_mm = (0.5 * side_leg_mm) - (0.5 * block_width_mm)
        block_x_mm = min(max(ideal_block_x_mm, region_x_mm), region_x_mm + region_width_mm - block_width_mm)
    elif winding_placement == "side_leg_right":
        side_leg_mm = side_leg_width_mm or max(0.12 * outer_width_mm, 0.5 * (outer_width_mm - core_window_width_mm))
        region_x_mm = outer_width_mm - side_leg_mm - (0.5 * (region_width_mm - side_leg_mm))
        ideal_block_x_mm = outer_width_mm - (0.5 * side_leg_mm) - (0.5 * block_width_mm)
        block_x_mm = min(max(ideal_block_x_mm, region_x_mm), region_x_mm + region_width_mm - block_width_mm)
    else:
        block_x_mm = region_x_mm + (0.5 * (region_width_mm - block_width_mm))

    block_y_mm = region_y_mm + (0.5 * (region_height_mm - block_height_mm))
    block_depth_mm = min(target_block_depth_mm, overall_depth_mm)
    fit_clamped = fit_clamped or (block_depth_mm < target_block_depth_mm)
    block_z_mm = 0.5 * (overall_depth_mm - block_depth_mm)
    opening_x_mm = None
    opening_y_mm = None
    opening_z_mm = None
    opening_width_mm = None
    opening_height_mm = None
    opening_depth_mm = None
    fit_inner_opening_ok = True
    resolved_insulation_margin_mm = max(float(insulation_margin_mm or 0.0), 0.15)

    if winding_geometry_style == "sleeve_around_leg":
        side_leg_mm = side_leg_width_mm or max(0.12 * outer_width_mm, 0.5 * (outer_width_mm - core_window_width_mm))
        target_opening_width_mm = side_leg_mm + (2.0 * resolved_insulation_margin_mm)
        min_side_wall_mm = max(0.06 * side_leg_mm, 0.5 * resolved_insulation_margin_mm, 0.5)
        min_outer_width_mm = target_opening_width_mm + (2.0 * min_side_wall_mm)
        if block_width_mm < min_outer_width_mm:
            if min_outer_width_mm <= region_width_mm:
                block_width_mm = min_outer_width_mm
                if winding_placement == "side_leg_left":
                    block_x_mm = min(max(0.5 * side_leg_mm - 0.5 * block_width_mm, region_x_mm), region_x_mm + region_width_mm - block_width_mm)
                elif winding_placement == "side_leg_right":
                    block_x_mm = min(max(outer_width_mm - 0.5 * side_leg_mm - 0.5 * block_width_mm, region_x_mm), region_x_mm + region_width_mm - block_width_mm)
                notes.append("U-family final fit check expanded the displayed sleeve width slightly so the side leg and insulation opening remain visible.")
            else:
                fit_inner_opening_ok = False
                fit_clamped = True
                notes.append("U-family final fit check reached the local width limit; the displayed sleeve keeps only a minimal visible wall.")

        opening_width_mm = min(target_opening_width_mm, max(block_width_mm - (2.0 * min_side_wall_mm), side_leg_mm))
        side_wall_mm = max(0.5 * (block_width_mm - opening_width_mm), 0.4)
        min_opening_height_mm = max(0.30 * block_height_mm, 2.0)
        top_bottom_wall_mm = min(side_wall_mm, 0.5 * max(block_height_mm - min_opening_height_mm, 0.0))
        if top_bottom_wall_mm <= 0.0:
            top_bottom_wall_mm = min(0.18 * block_height_mm, side_wall_mm)
        if winding_placement == "side_leg_left":
            opening_x_mm = (0.5 * side_leg_mm) - (0.5 * opening_width_mm)
        elif winding_placement == "side_leg_right":
            opening_x_mm = outer_width_mm - (0.5 * side_leg_mm) - (0.5 * opening_width_mm)
        else:
            opening_x_mm = block_x_mm + (0.5 * (block_width_mm - opening_width_mm))
        opening_y_mm = block_y_mm + top_bottom_wall_mm
        opening_z_mm = block_z_mm
        opening_height_mm = max(block_height_mm - (2.0 * top_bottom_wall_mm), 1.0)
        opening_depth_mm = block_depth_mm
        fit_inner_opening_ok = fit_inner_opening_ok and opening_width_mm < block_width_mm and opening_height_mm < block_height_mm
        notes.append("U-family winding is rendered as a sleeve around the selected side leg so the core leg remains visible.")
    elif winding_geometry_style == "sleeve_around_center_leg":
        center_leg_mm = center_leg_width_mm or max(0.16 * outer_width_mm, 0.25 * core_window_width_mm)
        target_opening_width_mm = center_leg_mm + (2.0 * resolved_insulation_margin_mm)
        min_side_wall_mm = max(0.08 * center_leg_mm, 0.5 * resolved_insulation_margin_mm, 0.5)
        min_outer_width_mm = target_opening_width_mm + (2.0 * min_side_wall_mm)
        if block_width_mm < min_outer_width_mm:
            if min_outer_width_mm <= region_width_mm:
                block_width_mm = min_outer_width_mm
                block_x_mm = region_x_mm + (0.5 * (region_width_mm - block_width_mm))
                notes.append("E-family final fit check expanded the displayed sleeve width slightly so the center leg and insulation opening remain visible.")
            else:
                fit_inner_opening_ok = False
                fit_clamped = True
                notes.append("E-family final fit check reached the local width limit; the displayed sleeve keeps only a minimal visible wall.")

        opening_width_mm = min(target_opening_width_mm, max(block_width_mm - (2.0 * min_side_wall_mm), center_leg_mm))
        side_wall_mm = max(0.5 * (block_width_mm - opening_width_mm), 0.4)
        min_opening_height_mm = max(0.35 * block_height_mm, center_leg_mm, 2.0)
        top_bottom_wall_mm = min(side_wall_mm, 0.5 * max(block_height_mm - min_opening_height_mm, 0.0))
        if top_bottom_wall_mm <= 0.0:
            top_bottom_wall_mm = min(0.18 * block_height_mm, side_wall_mm)
        opening_x_mm = (0.5 * outer_width_mm) - (0.5 * opening_width_mm)
        opening_y_mm = block_y_mm + top_bottom_wall_mm
        opening_z_mm = block_z_mm
        opening_height_mm = max(block_height_mm - (2.0 * top_bottom_wall_mm), 1.0)
        opening_depth_mm = block_depth_mm
        fit_inner_opening_ok = fit_inner_opening_ok and opening_width_mm < block_width_mm and opening_height_mm < block_height_mm
        notes.append("E-family winding is rendered as a sleeve around the center leg so the center post remains visible.")

    notes.append(
        "Final winding fit check: "
        + ("axial ok" if fit_axial_ok else "axial clamped")
        + ", "
        + ("radial ok" if fit_radial_ok else "radial clamped")
        + ", "
        + ("inner opening ok" if fit_inner_opening_ok else "inner opening constrained")
        + "."
    )

    return {
        "region_x_mm": region_x_mm,
        "region_y_mm": region_y_mm,
        "region_width_mm": region_width_mm,
        "region_height_mm": region_height_mm,
        "block_x_mm": block_x_mm,
        "block_y_mm": block_y_mm,
        "block_z_mm": block_z_mm,
        "block_width_mm": block_width_mm,
        "block_height_mm": block_height_mm,
        "block_depth_mm": block_depth_mm,
        "opening_x_mm": opening_x_mm,
        "opening_y_mm": opening_y_mm,
        "opening_z_mm": opening_z_mm,
        "opening_width_mm": opening_width_mm,
        "opening_height_mm": opening_height_mm,
        "opening_depth_mm": opening_depth_mm,
        "fit_axial_ok": fit_axial_ok,
        "fit_radial_ok": fit_radial_ok,
        "fit_inner_opening_ok": fit_inner_opening_ok,
        "fit_clamped": fit_clamped,
        "notes": notes,
    }


def _resolve_outer_dimensions_mm(design: FixedInductorDesignCandidate, notes: list[str]) -> tuple[float, float, float]:
    metadata = design.metadata
    width_mm = _positive_mm(metadata.get("core_width_m"))
    height_mm = _positive_mm(metadata.get("core_height_m"))
    depth_mm = _positive_mm(metadata.get("core_depth_m"))
    if width_mm is not None and height_mm is not None and depth_mm is not None:
        return width_mm, height_mm, depth_mm

    parsed = _parse_dimensions_from_name(design.base_core_name or design.core_name or "")
    if parsed is not None:
        notes.append("Core outer dimensions were reconstructed from the core naming convention.")
        return parsed

    volume_mm3 = _positive_mm3(design.core_volume_m3 or design.total_volume_m3 or metadata.get("gross_volume_m3"))
    if volume_mm3 is not None:
        cube_edge_mm = volume_mm3 ** (1.0 / 3.0)
        notes.append("Core outer dimensions used a volume-derived bounding-box fallback.")
        return cube_edge_mm, 0.80 * cube_edge_mm, 0.60 * cube_edge_mm

    notes.append("Core outer dimensions were unavailable; used a conservative 20 x 16 x 12 mm fallback.")
    return 20.0, 16.0, 12.0


def _resolve_core_assembly(design: FixedInductorDesignCandidate, core_family: str, notes: list[str]):
    metadata = design.metadata
    library_width_m = _positive_m(metadata.get("library_core_width_m"))
    library_height_m = _positive_m(metadata.get("library_core_height_m"))
    library_depth_m = _positive_m(metadata.get("library_core_depth_m"))
    if library_width_m is None or library_height_m is None or library_depth_m is None:
        fallback_width_mm, fallback_height_mm, fallback_depth_mm = _resolve_outer_dimensions_mm(design, notes)
        library_width_m = fallback_width_mm / 1e3
        library_height_m = fallback_height_mm / 1e3
        library_depth_m = fallback_depth_mm / 1e3
        if bool(metadata.get("library_item_is_half_core")) and is_paired_half_core_family(core_family):
            library_height_m = 0.5 * library_height_m
    return resolve_core_assembly_envelope(
        family=core_family,
        library_width_m=library_width_m,
        library_height_m=library_height_m,
        library_depth_m=library_depth_m,
    )


def _parse_dimensions_from_name(raw_name: str) -> tuple[float, float, float] | None:
    if not raw_name:
        return None
    cleaned = raw_name.replace("_", " ").replace("/", " ")
    prefix_match = re.match(r"\s*([A-Za-z]+)", cleaned)
    family = prefix_match.group(1).lower() if prefix_match else ""
    numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", cleaned)]
    if len(numbers) >= 3:
        if family == "t":
            return numbers[0], numbers[0], numbers[2]
        return numbers[0], numbers[1], numbers[2]
    if len(numbers) == 1:
        return numbers[0], 0.75 * numbers[0], 0.50 * numbers[0]
    return None


def _resolve_scale_bar_mm(*dimensions_mm: float) -> float:
    max_dimension_mm = max(dimensions_mm)
    target_mm = 0.30 * max_dimension_mm
    power = 10.0 ** math.floor(math.log10(max(target_mm, 1.0)))
    for factor in (1.0, 2.0, 5.0, 10.0):
        candidate = factor * power
        if candidate >= target_mm:
            return candidate
    return 10.0 * power


def _resolve_gap_position_label(*, core_family: str, is_paired_half_core: bool) -> str:
    if (core_family or "").strip().lower() == "t":
        return "radial gap"
    if is_paired_half_core:
        return "center mating gap"
    return "top gap"


def _positive_mm(value) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value) * 1e3
    except (TypeError, ValueError):
        return None
    return resolved if resolved > 0.0 else None


def _positive_m(value) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value)
    except (TypeError, ValueError):
        return None
    return resolved if resolved > 0.0 else None


def _positive_mm2(value) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value) * 1e6
    except (TypeError, ValueError):
        return None
    return resolved if resolved > 0.0 else None


def _positive_mm3(value) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value) * 1e9
    except (TypeError, ValueError):
        return None
    return resolved if resolved > 0.0 else None


def _resolve_shrink_pct(target_value_mm: float, final_value_mm: float) -> float:
    baseline = abs(float(target_value_mm))
    if baseline <= 1e-9:
        return 0.0
    return max(0.0, 100.0 * (baseline - abs(float(final_value_mm))) / baseline)
