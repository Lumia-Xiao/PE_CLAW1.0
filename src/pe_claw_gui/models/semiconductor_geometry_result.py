"""Semiconductor geometry result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SemiconductorGeometryLayout:
    """First-pass semiconductor package and heatsink drawing layout."""

    scheme_id: str
    scheme_label: str
    parallel_count: int
    part_number: str
    package: str
    normalized_package: str
    canonical_package: str
    package_template_key: str
    package_style: str
    renderer_template_id: str
    package_family: str
    package_lead_count: int
    mounting_style: str
    package_fallback_warning: str | None
    role: str
    case_id: str
    sink_volume_cm3: float | None
    sink_model_label: str
    cooling_mode: str
    package_body_width_mm: float
    package_body_height_mm: float
    package_body_thickness_mm: float
    package_tab_width_mm: float
    package_tab_height_mm: float
    package_hole_diameter_mm: float
    lead_pitch_mm: float
    lead_width_mm: float
    lead_length_mm: float
    sink_width_mm: float | None
    sink_height_mm: float | None
    sink_depth_mm: float | None
    sink_fin_count: int
    scale_bar_mm: float
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SemiconductorGeometryRoleLayout:
    """Resolved geometry and metadata for one selected semiconductor role."""

    role_name: str
    role_label: str
    part_number: str | None = None
    vendor: str | None = None
    selection_device_type: str | None = None
    device_structure_type: str | None = None
    package_level: str | None = None
    module_internal_topology: str | None = None
    diode_subtype: str | None = None
    package: str | None = None
    quantity: int = 1
    module_group_id: str | None = None
    module_section_role: str | None = None
    diode_binding_policy: str | None = None
    paired_switch_part_number: str | None = None
    paired_diode_part_number: str | None = None
    thermal_source: str | None = None
    per_device_loss_w: float | None = None
    role_total_loss_w: float | None = None
    case_id: str | None = None
    layout: SemiconductorGeometryLayout | None = None
    package_body_width_mm: float | None = None
    package_body_height_mm: float | None = None
    package_body_width_rendered: float | None = None
    package_body_height_rendered: float | None = None
    rendered_body_width_units: float | None = None
    rendered_body_height_units: float | None = None
    global_mm_to_unit: float | None = None
    package_scale_x: float | None = None
    package_scale_y: float | None = None
    physical_scale_preserved: bool = False
    visual_scale_factor: float = 1.0
    package_name: str | None = None
    panel_scale_source: str = "unscaled"
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SemiconductorGeometryTarget:
    """Comparison target for one semiconductor parallelization scheme."""

    scheme_id: str
    label: str
    parallel_count: int
    part_number: str | None = None
    package: str | None = None
    normalized_package: str | None = None
    canonical_package: str | None = None
    renderer_template_id: str | None = None
    package_fallback_warning: str | None = None
    role: str | None = None
    case_id: str | None = None
    topology_id: str | None = None
    topology_note: str | None = None
    sink_volume_cm3: float | None = None
    sink_model_label: str = ""
    estimated_sink_dims_mm: tuple[float, float, float] | None = None
    layout: SemiconductorGeometryLayout | None = None
    role_layouts: tuple[SemiconductorGeometryRoleLayout, ...] = ()
    global_mm_to_unit: float | None = None
    panel_mm_bbox: tuple[float, float] | None = None
    rendered_unit_bbox: tuple[float, float] | None = None
    panel_scale_source: str = "unscaled"
    sink_width_mm: float | None = None
    sink_height_mm: float | None = None
    sink_depth_mm: float | None = None
    sink_width_rendered: float | None = None
    sink_height_rendered: float | None = None
    sink_depth_rendered: float | None = None
    sink_scale_x: float | None = None
    sink_scale_y: float | None = None
    error_message: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SemiconductorGeometryResult:
    """Aggregate semiconductor geometry artifact for the device stage."""

    summary: str = ""
    part_number: str | None = None
    package: str | None = None
    normalized_package: str | None = None
    canonical_package: str | None = None
    renderer_template_id: str | None = None
    package_fallback_warning: str | None = None
    role: str | None = None
    case_id: str | None = None
    sink_volume_cm3: float | None = None
    sink_model_label: str = ""
    estimated_sink_dims_mm: tuple[float, float, float] | None = None
    layout: SemiconductorGeometryLayout | None = None
    targets: tuple[SemiconductorGeometryTarget, ...] = ()
    global_mm_to_unit: float | None = None
    panel_mm_bbox: tuple[float, float] | None = None
    rendered_unit_bbox: tuple[float, float] | None = None
    recommended_scheme_id: str | None = None
    notes: list[str] = field(default_factory=list)
    placeholder_message: str | None = None
