"""Semiconductor package and heatsink layout builder."""

from __future__ import annotations

import math

from ...libraries.semiconductors.packages import resolve_package_template
from ...libraries.semiconductors.power_device import PowerDevice
from ...models.device_loss import DeviceLossResult
from ...models.semiconductor_geometry_result import SemiconductorGeometryLayout

_SINK_ASPECT_RATIO = (1.8, 0.3, 1.0)
_SIDE_LEADED_TOP_RENDERERS = {"hdsop_10_top", "hdsop_16_top", "hdsop_22_top", "dso_20_top"}
_MODULE_RENDERERS = {"module_half_bridge", "module_flat_baseplate", "module_single_switch", "module_six_pack"}


def build_semiconductor_geometry_layout(
    device: PowerDevice,
    loss_result: DeviceLossResult,
    *,
    scheme_id: str = "single",
    scheme_label: str = "Single Device",
    parallel_count: int = 1,
    case_id: str,
) -> SemiconductorGeometryLayout:
    """Build a first-pass package-plus-heatsink drawing layout."""

    resolved_package = resolve_package_template(device.static.package)
    template = resolved_package.template
    package_body_width_mm, package_body_height_mm, package_body_thickness_mm = _resolve_package_body_dimensions(device, template)
    package_span_width_mm = _package_span_width_mm_from_template(template.renderer_template_id, package_body_width_mm, template.lead_length_mm)
    sink_dims_mm = _resolve_sink_dimensions_mm(
        loss_result.estimated_sink_volume_cm3,
        minimum_width_mm=_minimum_sink_width_mm(package_span_width_mm, parallel_count),
    )
    sink_width_mm, sink_height_mm, sink_depth_mm = sink_dims_mm if sink_dims_mm is not None else (None, None, None)
    max_dimension_mm = max(
        _estimate_package_major_dimension_mm(
            template.renderer_template_id,
            package_body_width_mm,
            package_body_height_mm,
            template.lead_length_mm,
        ),
        sink_width_mm or 0.0,
        sink_height_mm or 0.0,
        sink_depth_mm or 0.0,
        10.0,
    )

    notes = [
        f"Package from device record: {device.static.package}.",
        (
            f"Package normalization: {device.static.package} -> "
            f"{resolved_package.canonical_package} ({resolved_package.canonical_key})."
        ),
        f"Renderer template: {resolved_package.renderer_template_id}.",
        (
            "Sink block dimensions come from the first-pass semiconductor thermal sizing proxy "
            "using a fixed width:height:depth ratio of 1.8:0.3:1.0."
        ),
    ]
    if device.is_module and device.static.module_length_mm and device.static.module_width_mm and device.static.module_height_mm:
        notes.append(
            "Module body dimensions come from the Mitsubishi static record: "
            f"{device.static.module_length_mm:.3g} x {device.static.module_width_mm:.3g} x {device.static.module_height_mm:.3g} mm."
        )
    if resolved_package.fallback_warning is not None:
        notes.append(resolved_package.fallback_warning)

    return SemiconductorGeometryLayout(
        scheme_id=scheme_id,
        scheme_label=scheme_label,
        parallel_count=parallel_count,
        part_number=device.part_number,
        package=device.static.package,
        normalized_package=resolved_package.normalized_package,
        canonical_package=resolved_package.canonical_package,
        package_template_key=resolved_package.canonical_key,
        package_style=template.lead_style,
        renderer_template_id=resolved_package.renderer_template_id,
        package_family=resolved_package.package_family,
        package_lead_count=template.lead_count,
        mounting_style=template.mounting_style,
        package_fallback_warning=resolved_package.fallback_warning,
        role=loss_result.role,
        case_id=case_id,
        sink_volume_cm3=loss_result.estimated_sink_volume_cm3,
        sink_model_label=loss_result.sink_volume_model,
        cooling_mode=loss_result.cooling_mode_assumed,
        package_body_width_mm=package_body_width_mm,
        package_body_height_mm=package_body_height_mm,
        package_body_thickness_mm=package_body_thickness_mm,
        package_tab_width_mm=template.tab_width_mm,
        package_tab_height_mm=template.tab_height_mm,
        package_hole_diameter_mm=template.hole_diameter_mm,
        lead_pitch_mm=template.lead_pitch_mm,
        lead_width_mm=template.lead_width_mm,
        lead_length_mm=template.lead_length_mm,
        sink_width_mm=sink_width_mm,
        sink_height_mm=sink_height_mm,
        sink_depth_mm=sink_depth_mm,
        sink_fin_count=_resolve_sink_fin_count(sink_width_mm),
        scale_bar_mm=_resolve_scale_bar_mm(max_dimension_mm),
        notes=notes,
    )


def _resolve_package_body_dimensions(device: PowerDevice, template) -> tuple[float, float, float]:
    if device.is_module:
        return (
            device.static.module_length_mm or template.body_width_mm,
            device.static.module_width_mm or template.body_height_mm,
            device.static.module_height_mm or template.body_thickness_mm,
        )
    return template.body_width_mm, template.body_height_mm, template.body_thickness_mm


def _estimate_package_major_dimension_mm(
    renderer_template_id: str,
    body_width_mm: float,
    body_height_mm: float,
    lead_length_mm: float,
) -> float:
    if renderer_template_id in _SIDE_LEADED_TOP_RENDERERS:
        return max(body_width_mm + (2.0 * lead_length_mm), body_height_mm)
    if renderer_template_id in _MODULE_RENDERERS:
        return max(body_width_mm, body_height_mm)
    return max(body_height_mm + lead_length_mm, body_width_mm)


def _package_span_width_mm_from_template(renderer_template_id: str, body_width_mm: float, lead_length_mm: float) -> float:
    if renderer_template_id in _SIDE_LEADED_TOP_RENDERERS:
        return body_width_mm + (2.0 * lead_length_mm)
    return body_width_mm


def _minimum_sink_width_mm(package_span_width_mm: float, parallel_count: int) -> float | None:
    if parallel_count <= 1:
        return None
    package_gap_mm = max(3.0, 0.28 * package_span_width_mm)
    assembly_width_mm = (parallel_count * package_span_width_mm) + ((parallel_count - 1) * package_gap_mm)
    return assembly_width_mm + 6.0


def _resolve_sink_dimensions_mm(
    sink_volume_cm3: float | None,
    *,
    minimum_width_mm: float | None = None,
) -> tuple[float, float, float] | None:
    if sink_volume_cm3 is None or sink_volume_cm3 <= 0.0:
        return None
    ratio_w, ratio_h, ratio_d = _SINK_ASPECT_RATIO
    sink_volume_mm3 = sink_volume_cm3 * 1000.0
    scale_mm = (sink_volume_mm3 / (ratio_w * ratio_h * ratio_d)) ** (1.0 / 3.0)
    sink_dims_mm = (
        ratio_w * scale_mm,
        ratio_h * scale_mm,
        ratio_d * scale_mm,
    )
    if minimum_width_mm is None or sink_dims_mm[0] >= minimum_width_mm:
        return sink_dims_mm

    adjusted_width_mm = minimum_width_mm
    adjusted_height_mm = (sink_volume_mm3 / (ratio_d * adjusted_width_mm)) ** 0.5
    adjusted_depth_mm = ratio_d * adjusted_height_mm
    return (
        adjusted_width_mm,
        adjusted_height_mm,
        adjusted_depth_mm,
    )


def _resolve_sink_fin_count(sink_width_mm: float | None) -> int:
    if sink_width_mm is None or sink_width_mm <= 12.0:
        return 0
    return max(3, min(8, int(round(sink_width_mm / 6.0))))


def _resolve_scale_bar_mm(max_dimension_mm: float) -> float:
    target_mm = 0.30 * max_dimension_mm
    power = 10.0 ** math.floor(math.log10(max(target_mm, 1.0)))
    for factor in (1.0, 2.0, 5.0, 10.0):
        candidate = factor * power
        if candidate >= target_mm:
            return candidate
    return 10.0 * power
