"""Geometry-stage result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class InductorGeometryLayout:
    """Resolved engineering-geometry layout for one fixed inductor design."""

    design_id: str
    assembly_type: str
    stack_count: int
    core_family: str
    template_name: str
    base_core_name: str
    core_name: str
    library_item_is_half_core: bool
    half_cores_per_assembly: int
    pairing_axis: str | None
    material_name: str
    wire_name: str
    turns: int
    parallels: int
    winding_placement: str
    winding_geometry_style: str
    winding_estimation_method: str
    fill_factor: float | None
    gap_mm: float | None
    gap_position_label: str
    outer_width_mm: float
    outer_height_mm: float
    outer_depth_mm: float
    core_window_width_mm: float
    core_window_height_mm: float
    window_width_mm: float
    window_height_mm: float
    window_depth_mm: float
    center_leg_width_mm: float | None
    side_leg_width_mm: float | None
    top_yoke_height_mm: float | None
    bottom_yoke_height_mm: float | None
    effective_area_mm2: float | None
    effective_window_area_mm2: float | None
    winding_region_x_mm: float
    winding_region_y_mm: float
    winding_region_width_mm: float
    winding_region_height_mm: float
    winding_proxy_block_width_mm: float
    winding_proxy_block_height_mm: float
    winding_proxy_block_depth_mm: float
    winding_estimated_outer_width_mm: float
    winding_estimated_outer_height_mm: float
    winding_estimated_outer_depth_mm: float
    winding_bundle_outer_factor: float | None
    winding_strand_count: int | None
    winding_strand_diameter_mm: float | None
    winding_equivalent_bundle_diameter_mm: float | None
    winding_parallel_columns: int | None
    winding_parallel_rows: int | None
    winding_per_turn_axial_mm: float | None
    winding_per_turn_radial_mm: float | None
    winding_turns_per_layer: int | None
    winding_layers: int | None
    winding_fit_axial_ok: bool
    winding_fit_radial_ok: bool
    winding_fit_inner_opening_ok: bool
    winding_fit_clamped: bool
    winding_clamp_shrink_width_pct: float
    winding_clamp_shrink_height_pct: float
    winding_clamp_shrink_depth_pct: float
    winding_block_x_mm: float
    winding_block_y_mm: float
    winding_block_z_mm: float
    winding_block_width_mm: float
    winding_block_height_mm: float
    winding_block_depth_mm: float
    winding_inner_opening_x_mm: float | None
    winding_inner_opening_y_mm: float | None
    winding_inner_opening_z_mm: float | None
    winding_inner_opening_width_mm: float | None
    winding_inner_opening_height_mm: float | None
    winding_inner_opening_depth_mm: float | None
    overall_width_mm: float
    overall_height_mm: float
    overall_depth_mm: float
    scale_bar_mm: float
    geometry_dimension_source: str = ""
    geometry_warning: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GeometryTarget:
    """One fixed geometry-page target and its resolved presentation metadata."""

    role: str
    label: str
    design_id: str | None = None
    layout: InductorGeometryLayout | None = None
    volume_m3: float | None = None
    loss_w: float | None = None
    duplicate_of: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error_message: str | None = None
    component_role: str = "fixed_inductor"
    representative_role: str | None = None


@dataclass(frozen=True)
class GeometryResult:
    """Aggregate geometry-stage result for the selected magnetic design."""

    summary: str = ""
    selected_design_id: str | None = None
    selected_layout: InductorGeometryLayout | None = None
    targets: list[GeometryTarget] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    footprint_mm2: float | None = None
    component_type: str = "fixed_inductor"
    notes: list[str] = field(default_factory=list)
