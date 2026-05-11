"""Semiconductor 3D package-template coverage audit helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...libraries.semiconductors.packages import resolve_package_template
from ...libraries.semiconductors.registry import build_default_semiconductor_registry
from ...models.semiconductor_geometry_result import SemiconductorGeometryLayout
from .geometry_3d import resolve_semiconductor_3d_package_template


@dataclass(frozen=True)
class Semiconductor3DPackageCoverageRow:
    """3D package coverage status for one registered power device."""

    part_number: str
    vendor: str
    package_name: str
    resolved_package: str
    selection_device_type: str
    device_structure_type: str
    package_level: str
    module_internal_topology: str
    renderer_template_id_3d: str | None
    body_width_mm: float | None
    body_height_mm: float | None
    body_thickness_mm: float | None
    has_3d_template: bool
    uses_generic_fallback: bool
    missing_package_dimensions: bool
    missing_package_alias: bool
    failed_reason: str | None = None


@dataclass(frozen=True)
class Semiconductor3DPackageCoverageAudit:
    """Aggregate 3D package coverage audit."""

    total_devices: int
    devices_with_3d_template: int
    devices_using_generic_fallback: int
    devices_missing_package_dimensions: int
    devices_missing_package_alias: int
    devices_failed_3d_geometry_build: int
    rows: tuple[Semiconductor3DPackageCoverageRow, ...] = field(default_factory=tuple)

    @property
    def failed_rows(self) -> tuple[Semiconductor3DPackageCoverageRow, ...]:
        return tuple(row for row in self.rows if row.failed_reason)


def audit_semiconductor_3d_package_coverage() -> Semiconductor3DPackageCoverageAudit:
    """Audit whether default-registry devices can resolve a physical 3D package envelope."""

    rows: list[Semiconductor3DPackageCoverageRow] = []
    for device in build_default_semiconductor_registry().list_devices():
        resolved = resolve_package_template(device.static.package)
        template = resolved.template
        body_width_mm = device.static.module_length_mm if device.is_module and device.static.module_length_mm else template.body_width_mm
        body_height_mm = device.static.module_width_mm if device.is_module and device.static.module_width_mm else template.body_height_mm
        body_thickness_mm = device.static.module_height_mm if device.is_module and device.static.module_height_mm else template.body_thickness_mm
        missing_dimensions = any(value is None or float(value) <= 0.0 for value in (body_width_mm, body_height_mm, body_thickness_mm))
        renderer_template_id_3d = None
        failed_reason = None
        uses_generic = False
        try:
            layout = _layout_for_audit(
                device=device,
                resolved_package=resolved,
                body_width_mm=float(body_width_mm),
                body_height_mm=float(body_height_mm),
                body_thickness_mm=float(body_thickness_mm),
            )
            package_3d = resolve_semiconductor_3d_package_template(layout)
            renderer_template_id_3d = package_3d.template_id
            uses_generic = package_3d.template_id == "generic_package_envelope_3d"
        except Exception as exc:
            failed_reason = f"{type(exc).__name__}: {exc}"

        missing_alias = resolved.fallback_warning is not None
        if missing_alias and failed_reason is None:
            failed_reason = resolved.fallback_warning
        if missing_dimensions and failed_reason is None:
            failed_reason = f"Missing package dimensions for {device.static.package}."

        rows.append(
            Semiconductor3DPackageCoverageRow(
                part_number=device.part_number,
                vendor=device.vendor,
                package_name=device.static.package,
                resolved_package=resolved.canonical_package,
                selection_device_type=device.selection_device_type,
                device_structure_type=device.device_structure_type,
                package_level=device.package_level,
                module_internal_topology=device.module_internal_topology,
                renderer_template_id_3d=renderer_template_id_3d,
                body_width_mm=None if body_width_mm is None else float(body_width_mm),
                body_height_mm=None if body_height_mm is None else float(body_height_mm),
                body_thickness_mm=None if body_thickness_mm is None else float(body_thickness_mm),
                has_3d_template=failed_reason is None,
                uses_generic_fallback=uses_generic,
                missing_package_dimensions=missing_dimensions,
                missing_package_alias=missing_alias,
                failed_reason=failed_reason,
            )
        )

    return Semiconductor3DPackageCoverageAudit(
        total_devices=len(rows),
        devices_with_3d_template=sum(1 for row in rows if row.has_3d_template),
        devices_using_generic_fallback=sum(1 for row in rows if row.uses_generic_fallback),
        devices_missing_package_dimensions=sum(1 for row in rows if row.missing_package_dimensions),
        devices_missing_package_alias=sum(1 for row in rows if row.missing_package_alias),
        devices_failed_3d_geometry_build=sum(1 for row in rows if row.failed_reason),
        rows=tuple(rows),
    )


def _layout_for_audit(*, device, resolved_package, body_width_mm: float, body_height_mm: float, body_thickness_mm: float) -> SemiconductorGeometryLayout:
    template = resolved_package.template
    return SemiconductorGeometryLayout(
        scheme_id="audit",
        scheme_label="Audit",
        parallel_count=1,
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
        role="audit",
        case_id="audit",
        sink_volume_cm3=1.0,
        sink_model_label="audit",
        cooling_mode="audit",
        package_body_width_mm=body_width_mm,
        package_body_height_mm=body_height_mm,
        package_body_thickness_mm=body_thickness_mm,
        package_tab_width_mm=template.tab_width_mm,
        package_tab_height_mm=template.tab_height_mm,
        package_hole_diameter_mm=template.hole_diameter_mm,
        lead_pitch_mm=template.lead_pitch_mm,
        lead_width_mm=template.lead_width_mm,
        lead_length_mm=template.lead_length_mm,
        sink_width_mm=120.0,
        sink_height_mm=60.0,
        sink_depth_mm=48.0,
        sink_fin_count=7,
        scale_bar_mm=20.0,
    )
