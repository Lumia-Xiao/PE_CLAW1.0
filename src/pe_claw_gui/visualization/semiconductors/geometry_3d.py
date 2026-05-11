"""Static Matplotlib 3D engineering renderer for semiconductor geometry."""

from __future__ import annotations

from dataclasses import dataclass

from matplotlib.figure import Figure

from ...models.semiconductor_geometry_result import SemiconductorGeometryLayout, SemiconductorGeometryRoleLayout, SemiconductorGeometryTarget
from ..geometry.primitives_3d import (
    DARK_OUTLINE,
    MUTED_METAL_FACE,
    MUTED_METAL_FACE_ALT,
    PACKAGE_BODY_FACE,
    SILVER_LEAD_FACE,
    TEXT_BOX_STYLE,
    add_box_3d,
    add_box_outline_3d,
    configure_engineering_3d_axis,
    set_equal_physical_box_aspect,
)
from .physical_package_instances import PhysicalPackageInstance, build_physical_package_instances_for_role_layouts

_SUPPORTED_TEMPLATE_IDS = {
    "to220_3_tht": "to220_tht_3",
    "to247_3_tht": "to247_tht_3",
    "hdsop_22_top": "hdsop_smd_22",
    "to247_4_tht": "to247_tht_4",
    "to247_2_tht": "to247_tht_2",
    "to252_3_dpak": "dpak_to252_smd_3",
    "to263_7_d2pak": "d2pak_to263_smd",
    "hdsop_10_top": "hdsop_smd_10",
    "hdsop_16_top": "hdsop_smd_16",
    "dso_20_top": "dso_smd_20",
    "hsof_8_top": "hsof_smd_8",
    "tson_8_top": "leadless_smd_8",
    "lson_8_top": "leadless_smd_8",
    "lhsof_4_top": "lhsof_smd_4",
    "thinpak_8x8_top": "thinpak_smd_8",
    "module_half_bridge": "module_envelope_3d",
    "module_flat_baseplate": "module_envelope_3d",
    "module_single_switch": "module_envelope_3d",
    "module_six_pack": "module_envelope_3d",
    "generic_power_package": "generic_package_envelope_3d",
}
_PREFERRED_ROLE_ORDER = (
    "main_switch",
    "rectifier_diode",
    "sync_switch",
    "switch_a_high",
    "switch_a_low",
    "switch_b_high",
    "switch_b_low",
    "S1",
    "S2",
    "S3",
    "S4",
)
_MODULE_TEMPLATE_IDS = {"module_envelope_3d"}
_SIDE_LEADED_TEMPLATE_IDS = {
    "hdsop_smd_10",
    "hdsop_smd_16",
    "hdsop_smd_22",
    "dso_smd_20",
    "hsof_smd_8",
    "lhsof_smd_4",
    "thinpak_smd_8",
}
_LEADLESS_TEMPLATE_IDS = {"leadless_smd_8"}
_BOTTOM_LEADED_SMD_TEMPLATE_IDS = {"dpak_to252_smd_3", "d2pak_to263_smd"}
_MOUNTING_FACE_Z_MM = 0.0
_PACKAGE_MOUNT_EPSILON_MM = 0.03
_MOUNTING_FACE_VISUAL_THICKNESS_MM = 0.01


@dataclass(frozen=True)
class Semiconductor3DPackageTemplate:
    """Resolved 3D package template for a semiconductor geometry layout."""

    template_id: str
    renderer_template_id: str
    body_width_mm: float
    body_depth_mm: float
    body_thickness_mm: float
    lead_count: int
    lead_width_mm: float
    lead_length_mm: float
    lead_pitch_mm: float
    tab_width_mm: float
    tab_depth_mm: float
    hole_diameter_mm: float
    package_family: str
    package_specific: bool
    visual_scale_factor: float = 1.0


@dataclass(frozen=True)
class Semiconductor3DBox:
    """One physical cuboid in the 3D semiconductor scene."""

    kind: str
    role_name: str | None
    x_mm: float
    y_mm: float
    z_mm: float
    dx_mm: float
    dy_mm: float
    dz_mm: float
    gid: str


@dataclass(frozen=True)
class Semiconductor3DRolePlacement:
    """Resolved physical placement for one semiconductor role."""

    role_name: str
    short_label: str
    part_number: str
    package: str
    quantity: int
    module_group_id: str | None
    section_role_names: tuple[str, ...]
    diode_binding_policy: str | None
    template: Semiconductor3DPackageTemplate
    assembly_x_mm: float
    assembly_y_mm: float
    body_box: Semiconductor3DBox
    body_boxes: tuple[Semiconductor3DBox, ...]
    lead_boxes: tuple[Semiconductor3DBox, ...]
    rendered_body_width_mm: float
    rendered_body_depth_mm: float
    rendered_body_thickness_mm: float
    visual_scale_factor: float = 1.0


@dataclass(frozen=True)
class Semiconductor3DPlacementDebug:
    """Auditable z-placement data for one rendered semiconductor package body."""

    role_name: str
    package_index: int
    mounting_face_z_mm: float
    device_bottom_z_mm: float
    device_top_z_mm: float
    device_intersects_heatsink: bool
    device_intersects_fins: bool


@dataclass(frozen=True)
class Semiconductor3DScene:
    """Resolved semiconductor 3D scene in millimeters."""

    sink_box: Semiconductor3DBox
    sink_base_box: Semiconductor3DBox
    fin_boxes: tuple[Semiconductor3DBox, ...]
    role_placements: tuple[Semiconductor3DRolePlacement, ...]
    package_boxes: tuple[Semiconductor3DBox, ...]
    lead_boxes: tuple[Semiconductor3DBox, ...]
    placement_debug: tuple[Semiconductor3DPlacementDebug, ...]
    mounting_face_z_mm: float
    fin_side_min_z_mm: float
    package_mount_epsilon_mm: float
    total_span_x_mm: float
    total_span_y_mm: float
    total_span_z_mm: float
    center_x_mm: float
    center_y_mm: float
    center_z_mm: float
    summary_lines: tuple[str, ...]
    layout_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Semiconductor3DComparisonSettings:
    """Shared physical 3D bounds for scheme comparison panels."""

    global_mm_to_unit: float
    global_x_range_mm: tuple[float, float]
    global_y_range_mm: tuple[float, float]
    global_z_range_mm: tuple[float, float]
    total_span_x_mm: float
    total_span_y_mm: float
    total_span_z_mm: float
    panel_xlim_mm: tuple[float, float]
    panel_ylim_mm: tuple[float, float]
    panel_zlim_mm: tuple[float, float]


def create_semiconductor_geometry_figure_3d(target: SemiconductorGeometryTarget) -> Figure:
    """Create the first-pass Single Device semiconductor 3D engineering figure."""

    return create_semiconductor_single_scheme_figure_3d(target)


def create_semiconductor_single_scheme_figure_3d(target: SemiconductorGeometryTarget) -> Figure:
    """Create a static 3D figure for one Single Device semiconductor scheme."""

    scene = build_semiconductor_3d_scene_for_scheme(target)
    figure = Figure(figsize=(8.0, 5.6), dpi=120)
    axis = figure.add_subplot(111, projection="3d")
    _render_scheme_panel_3d(axis, scene, title="Semiconductor 3D Geometry")
    figure.tight_layout(pad=0.8)
    return figure


def create_semiconductor_geometry_comparison_figure_3d(targets: tuple[SemiconductorGeometryTarget, ...]) -> Figure:
    """Create a 1 x N semiconductor 3D comparison figure with one shared physical scale."""

    scenes = tuple(build_semiconductor_3d_scene_for_scheme(target) for target in targets if is_supported_semiconductor_3d_target(target))
    if not scenes:
        figure = Figure(figsize=(8.0, 4.8), dpi=120)
        axis = figure.add_subplot(111)
        axis.axis("off")
        axis.text(0.5, 0.5, "No supported semiconductor 3D geometry targets are available.", ha="center", va="center", fontsize=9.0)
        figure.tight_layout(pad=0.8)
        return figure

    comparison_settings = resolve_semiconductor_3d_comparison_settings(scenes)
    panel_count = len(scenes)
    figure = Figure(figsize=(5.2 * panel_count, 5.6), dpi=120)
    for index, scene in enumerate(scenes, start=1):
        axis = figure.add_subplot(1, panel_count, index, projection="3d")
        _render_scheme_panel_3d(axis, scene, title=scene.summary_lines[0], comparison_settings=comparison_settings)
    figure.tight_layout(pad=0.8)
    return figure


def create_semiconductor_scheme_panel_3d(axis, target: SemiconductorGeometryTarget, *, comparison_settings: Semiconductor3DComparisonSettings | None = None) -> Semiconductor3DScene:
    """Render one scheme target into an existing 3D axis and return its scene."""

    scene = build_semiconductor_3d_scene_for_scheme(target)
    _render_scheme_panel_3d(axis, scene, title=scene.summary_lines[0], comparison_settings=comparison_settings)
    return scene


def find_single_device_3d_target(targets: tuple[SemiconductorGeometryTarget, ...]) -> SemiconductorGeometryTarget | None:
    """Return the supported Single Device 3D target from a geometry result."""

    for target in targets:
        if is_supported_semiconductor_3d_target(target):
            return target
    return None


def find_supported_3d_targets(targets: tuple[SemiconductorGeometryTarget, ...]) -> tuple[SemiconductorGeometryTarget, ...]:
    """Return all supported semiconductor 3D targets in their existing scheme order."""

    return tuple(target for target in targets if is_supported_semiconductor_3d_target(target))


def is_supported_semiconductor_3d_target(target: SemiconductorGeometryTarget) -> bool:
    """Return whether the first-pass 3D renderer supports this target."""

    if target.parallel_count < 1:
        return False
    role_layouts = _ordered_drawable_roles(target)
    if not role_layouts:
        return False
    if _sink_dims_mm(target) is None:
        return False
    return all(role.layout is not None and is_supported_3d_package_layout(role.layout) for role in role_layouts)


def build_semiconductor_single_scheme_scene_3d(target: SemiconductorGeometryTarget) -> Semiconductor3DScene:
    """Resolve a Single Device semiconductor target into physical 3D boxes."""

    if target.scheme_id != "single" or target.parallel_count != 1:
        raise ValueError("Semiconductor 3D prototype only supports the Single Device scheme.")
    return build_semiconductor_3d_scene_for_scheme(target)


def build_semiconductor_3d_scene_for_scheme(target: SemiconductorGeometryTarget) -> Semiconductor3DScene:
    """Resolve one Single Device semiconductor target into physical 3D boxes.

    Coordinate convention:
    - x is heatsink/package width.
    - y is heatsink depth / package body depth.
    - z is heatsink height / package thickness direction.
    - the flat mounting face is the +z-facing plane at z = 0 mm.
    - semiconductor packages sit just above that mounting face.
    - heatsink base material and fins extrude away from devices toward -z.
    """

    sink_dims = _sink_dims_mm(target)
    if sink_dims is None:
        raise ValueError(f"3D package geometry unavailable: missing sink dimensions for {target.label}.")
    role_layouts = _ordered_drawable_roles(target)
    if not role_layouts:
        raise ValueError(f"3D package geometry unavailable: no drawable semiconductor roles for {target.label}.")
    if not all(role.layout is not None and is_supported_3d_package_layout(role.layout) for role in role_layouts):
        unsupported = [role.package or role.role_name for role in role_layouts if role.layout is None or not is_supported_3d_package_layout(role.layout)]
        raise ValueError("3D package geometry unavailable for: " + ", ".join(unsupported))

    sink_width_mm, sink_height_mm, sink_depth_mm = sink_dims
    base_height_mm = _sink_base_height_mm(sink_height_mm)
    sink_box = Semiconductor3DBox(
        kind="sink",
        role_name=None,
        x_mm=0.0,
        y_mm=0.0,
        z_mm=-sink_height_mm,
        dx_mm=sink_width_mm,
        dy_mm=sink_depth_mm,
        dz_mm=sink_height_mm,
        gid="semiconductor-3d:sink",
    )
    sink_base_box = Semiconductor3DBox(
        kind="sink_base",
        role_name=None,
        x_mm=0.0,
        y_mm=0.0,
        z_mm=-base_height_mm,
        dx_mm=sink_width_mm,
        dy_mm=sink_depth_mm,
        dz_mm=base_height_mm,
        gid="semiconductor-3d:sink-base",
    )
    fin_boxes = _build_sink_fin_boxes(
        target,
        sink_width_mm=sink_width_mm,
        sink_height_mm=sink_height_mm,
        sink_depth_mm=sink_depth_mm,
        base_height_mm=base_height_mm,
    )
    role_placements = _build_role_placements(role_layouts, sink_width_mm=sink_width_mm, sink_depth_mm=sink_depth_mm)
    package_boxes = tuple(box for placement in role_placements for box in placement.body_boxes)
    lead_boxes = tuple(box for placement in role_placements for box in placement.lead_boxes)
    placement_debug = _build_placement_debug(package_boxes, sink_box=sink_box, fin_boxes=tuple(fin_boxes))

    min_x_mm = min([0.0, *(box.x_mm for box in package_boxes)])
    max_x_mm = max([sink_width_mm, *(box.x_mm + box.dx_mm for box in package_boxes)])
    min_y_mm = min([0.0, *(box.y_mm for box in package_boxes)])
    max_y_mm = max([sink_depth_mm, *(box.y_mm + box.dy_mm for box in package_boxes)])
    min_z_mm = min([sink_box.z_mm, *(box.z_mm for box in package_boxes)])
    max_z_mm = max([_MOUNTING_FACE_Z_MM, *(box.z_mm + box.dz_mm for box in package_boxes)])
    span_x_mm = max_x_mm - min_x_mm
    span_y_mm = max_y_mm - min_y_mm
    span_z_mm = max_z_mm - min_z_mm
    pad_x_mm = max(0.12 * span_x_mm, 8.0)
    pad_y_mm = max(0.16 * span_y_mm, 8.0)
    pad_z_mm = max(0.24 * span_z_mm, 6.0)
    layout_warnings = _build_layout_warnings(package_boxes, sink_width_mm=sink_width_mm, sink_depth_mm=sink_depth_mm)
    summary_lines = _build_summary_lines(target, role_placements, sink_width_mm=sink_width_mm, sink_height_mm=sink_height_mm, sink_depth_mm=sink_depth_mm)
    return Semiconductor3DScene(
        sink_box=sink_box,
        sink_base_box=sink_base_box,
        fin_boxes=tuple(fin_boxes),
        role_placements=tuple(role_placements),
        package_boxes=package_boxes,
        lead_boxes=lead_boxes,
        placement_debug=placement_debug,
        mounting_face_z_mm=_MOUNTING_FACE_Z_MM,
        fin_side_min_z_mm=-sink_height_mm,
        package_mount_epsilon_mm=_PACKAGE_MOUNT_EPSILON_MM,
        total_span_x_mm=span_x_mm + (2.0 * pad_x_mm),
        total_span_y_mm=span_y_mm + (2.0 * pad_y_mm),
        total_span_z_mm=span_z_mm + (2.0 * pad_z_mm),
        center_x_mm=0.5 * (min_x_mm + max_x_mm),
        center_y_mm=0.5 * (min_y_mm + max_y_mm),
        center_z_mm=0.5 * (min_z_mm + max_z_mm),
        summary_lines=summary_lines,
        layout_warnings=tuple(layout_warnings),
    )


def resolve_semiconductor_3d_comparison_settings(scenes: tuple[Semiconductor3DScene, ...]) -> Semiconductor3DComparisonSettings:
    """Resolve one common physical 3D extent for all semiconductor scheme panels."""

    if not scenes:
        return Semiconductor3DComparisonSettings(
            global_mm_to_unit=1.0,
            global_x_range_mm=(-50.0, 50.0),
            global_y_range_mm=(-30.0, 30.0),
            global_z_range_mm=(-40.0, 20.0),
            total_span_x_mm=100.0,
            total_span_y_mm=60.0,
            total_span_z_mm=60.0,
            panel_xlim_mm=(-50.0, 50.0),
            panel_ylim_mm=(-30.0, 30.0),
            panel_zlim_mm=(-40.0, 20.0),
        )

    total_span_x_mm = max(scene.total_span_x_mm for scene in scenes)
    total_span_y_mm = max(scene.total_span_y_mm for scene in scenes)
    total_span_z_mm = max(scene.total_span_z_mm for scene in scenes)
    panel_xlim_mm = (-0.5 * total_span_x_mm, 0.5 * total_span_x_mm)
    panel_ylim_mm = (-0.5 * total_span_y_mm, 0.5 * total_span_y_mm)
    panel_zlim_mm = (-0.5 * total_span_z_mm, 0.5 * total_span_z_mm)
    return Semiconductor3DComparisonSettings(
        global_mm_to_unit=1.0,
        global_x_range_mm=panel_xlim_mm,
        global_y_range_mm=panel_ylim_mm,
        global_z_range_mm=panel_zlim_mm,
        total_span_x_mm=total_span_x_mm,
        total_span_y_mm=total_span_y_mm,
        total_span_z_mm=total_span_z_mm,
        panel_xlim_mm=panel_xlim_mm,
        panel_ylim_mm=panel_ylim_mm,
        panel_zlim_mm=panel_zlim_mm,
    )


def resolve_semiconductor_3d_package_template(layout: SemiconductorGeometryLayout) -> Semiconductor3DPackageTemplate:
    """Resolve a 3D package template from the package library renderer id."""

    template_id = _SUPPORTED_TEMPLATE_IDS.get(layout.renderer_template_id, "generic_package_envelope_3d")
    package_specific = template_id != "generic_package_envelope_3d"
    _validate_layout_dimensions(layout)
    return Semiconductor3DPackageTemplate(
        template_id=template_id,
        renderer_template_id=layout.renderer_template_id,
        body_width_mm=layout.package_body_width_mm,
        body_depth_mm=layout.package_body_height_mm,
        body_thickness_mm=layout.package_body_thickness_mm,
        lead_count=layout.package_lead_count,
        lead_width_mm=layout.lead_width_mm,
        lead_length_mm=layout.lead_length_mm,
        lead_pitch_mm=layout.lead_pitch_mm,
        tab_width_mm=layout.package_tab_width_mm,
        tab_depth_mm=layout.package_tab_height_mm,
        hole_diameter_mm=layout.package_hole_diameter_mm,
        package_family=layout.package_family,
        package_specific=package_specific,
        visual_scale_factor=1.0,
    )


def is_supported_3d_package_layout(layout: SemiconductorGeometryLayout) -> bool:
    """Return whether a package layout has enough physical dimensions for 3D rendering."""

    try:
        _validate_layout_dimensions(layout)
    except ValueError:
        return False
    return True


def _validate_layout_dimensions(layout: SemiconductorGeometryLayout) -> None:
    required = {
        "package_body_width_mm": layout.package_body_width_mm,
        "package_body_height_mm": layout.package_body_height_mm,
        "package_body_thickness_mm": layout.package_body_thickness_mm,
    }
    missing = [name for name, value in required.items() if value is None or float(value) <= 0.0]
    if missing:
        raise ValueError(f"3D package geometry unavailable: missing package dimensions for {layout.package}: {', '.join(missing)}")


def _sink_dims_mm(target: SemiconductorGeometryTarget) -> tuple[float, float, float] | None:
    if target.estimated_sink_dims_mm is not None:
        return tuple(float(value) for value in target.estimated_sink_dims_mm)
    layout = target.layout
    if layout is None or layout.sink_width_mm is None or layout.sink_height_mm is None or layout.sink_depth_mm is None:
        return None
    return (float(layout.sink_width_mm), float(layout.sink_height_mm), float(layout.sink_depth_mm))


def _ordered_drawable_roles(target: SemiconductorGeometryTarget) -> tuple[SemiconductorGeometryRoleLayout, ...]:
    drawable = [role for role in target.role_layouts if role.part_number is not None and role.layout is not None]
    by_name = {role.role_name: role for role in drawable}
    ordered = [by_name[role_name] for role_name in _PREFERRED_ROLE_ORDER if role_name in by_name]
    ordered.extend(role for role in drawable if role.role_name not in _PREFERRED_ROLE_ORDER)
    return tuple(ordered)


def _build_sink_fin_boxes(
    target: SemiconductorGeometryTarget,
    *,
    sink_width_mm: float,
    sink_height_mm: float,
    sink_depth_mm: float,
    base_height_mm: float,
) -> list[Semiconductor3DBox]:
    layout = target.layout
    requested_count = layout.sink_fin_count if layout is not None else 7
    fin_count = max(int(requested_count or 7), 3)
    fin_height_mm = max(sink_height_mm - base_height_mm, 0.0)
    if fin_height_mm <= 0.05:
        return []
    pitch_mm = sink_width_mm / fin_count
    fin_width_mm = max(min(0.28 * pitch_mm, 2.0), 0.35)
    boxes: list[Semiconductor3DBox] = []
    for index in range(fin_count):
        center_x_mm = (index + 0.5) * pitch_mm
        boxes.append(
            Semiconductor3DBox(
                kind="sink_fin",
                role_name=None,
                x_mm=center_x_mm - (0.5 * fin_width_mm),
                y_mm=0.0,
                z_mm=-sink_height_mm,
                dx_mm=fin_width_mm,
                dy_mm=sink_depth_mm,
                dz_mm=fin_height_mm,
                gid=f"semiconductor-3d:sink-fin:{index}",
            )
        )
    return boxes


def _build_role_placements(
    role_layouts: tuple[SemiconductorGeometryRoleLayout, ...],
    *,
    sink_width_mm: float,
    sink_depth_mm: float,
) -> list[Semiconductor3DRolePlacement]:
    physical_instances = build_physical_package_instances_for_role_layouts(tuple(role for role in role_layouts if role.layout is not None))
    group_specs = [
        _build_role_group_spec(instance, sink_width_mm=sink_width_mm)
        for instance in physical_instances
    ]
    max_depth_mm = max(spec["depth_mm"] for spec in group_specs)
    role_gap_mm = max(0.10 * sink_width_mm, 6.0)
    row_gap_mm = max(0.12 * sink_depth_mm, 5.0)
    total_width_mm = sum(spec["width_mm"] for spec in group_specs) + (max(len(group_specs) - 1, 0) * role_gap_mm)
    total_stacked_depth_mm = sum(spec["depth_mm"] for spec in group_specs) + (max(len(group_specs) - 1, 0) * row_gap_mm)
    use_single_row = total_width_mm <= sink_width_mm and max_depth_mm <= sink_depth_mm
    x_mm = 0.5 * (sink_width_mm - total_width_mm) if use_single_row else 0.0
    y_mm = 0.5 * (sink_depth_mm - max_depth_mm) if use_single_row else 0.5 * (sink_depth_mm - total_stacked_depth_mm)
    placements: list[Semiconductor3DRolePlacement] = []
    for spec in group_specs:
        instance = spec["instance"]
        role_layout = instance.primary_role_layout
        layout = role_layout.layout
        if layout is None:
            continue
        template = resolve_semiconductor_3d_package_template(layout)
        quantity = max(int(instance.quantity or 1), 1)
        body_boxes: list[Semiconductor3DBox] = []
        group_x_mm = x_mm if use_single_row else 0.5 * (sink_width_mm - spec["width_mm"])
        group_y_mm = y_mm
        for package_index, (relative_x_mm, relative_y_mm) in enumerate(spec["body_offsets_mm"]):
            body_boxes.append(
                Semiconductor3DBox(
                    kind="package_body",
                    role_name=role_layout.role_name,
                    x_mm=group_x_mm + relative_x_mm,
                    y_mm=group_y_mm + relative_y_mm,
                    z_mm=_MOUNTING_FACE_Z_MM + _PACKAGE_MOUNT_EPSILON_MM,
                    dx_mm=template.body_width_mm,
                    dy_mm=template.body_depth_mm,
                    dz_mm=template.body_thickness_mm,
                    gid=f"semiconductor-3d:package-body:{role_layout.role_name}:{package_index}",
                )
            )
        body_box = body_boxes[0]
        lead_boxes = _build_role_lead_boxes(role_layout.role_name, template, tuple(body_boxes))
        placements.append(
            Semiconductor3DRolePlacement(
                role_name=role_layout.role_name,
                short_label=instance.role_labels,
                part_number=instance.package_part_number,
                package=instance.package_name,
                quantity=quantity,
                module_group_id=instance.module_group_id,
                section_role_names=instance.roles_in_package,
                diode_binding_policy=instance.diode_binding_policy,
                template=template,
                assembly_x_mm=group_x_mm,
                assembly_y_mm=min(box.y_mm for box in body_boxes) - template.lead_length_mm,
                body_box=body_box,
                body_boxes=tuple(body_boxes),
                lead_boxes=lead_boxes,
                rendered_body_width_mm=template.body_width_mm,
                rendered_body_depth_mm=template.body_depth_mm,
                rendered_body_thickness_mm=template.body_thickness_mm,
                visual_scale_factor=1.0,
            )
        )
        if use_single_row:
            x_mm += spec["width_mm"] + role_gap_mm
        else:
            y_mm += spec["depth_mm"] + row_gap_mm
    return placements


def _module_bound_role_groups(
    role_layouts: tuple[SemiconductorGeometryRoleLayout, ...],
) -> list[tuple[SemiconductorGeometryRoleLayout, tuple[SemiconductorGeometryRoleLayout, ...]]]:
    groups: list[tuple[SemiconductorGeometryRoleLayout, tuple[SemiconductorGeometryRoleLayout, ...]]] = []
    consumed_indexes: set[int] = set()
    for index, role_layout in enumerate(role_layouts):
        if index in consumed_indexes:
            continue
        module_group_id = role_layout.module_group_id
        if module_group_id and role_layout.package_level == "power_module":
            member_indexes = [
                member_index
                for member_index, member in enumerate(role_layouts)
                if member.module_group_id == module_group_id and member.package_level == "power_module"
            ]
            members = tuple(role_layouts[member_index] for member_index in member_indexes)
            if len(members) > 1 and any(member.diode_binding_policy == "internal_module_diode" for member in members):
                primary = next((member for member in members if member.module_section_role != "internal_diode"), members[0])
                ordered_members = tuple(member for member in role_layouts if member in members)
                groups.append((primary, ordered_members))
                consumed_indexes.update(member_indexes)
                continue
        groups.append((role_layout, (role_layout,)))
        consumed_indexes.add(index)
    return groups


def _placement_diode_binding_policy(section_roles: tuple[SemiconductorGeometryRoleLayout, ...]) -> str | None:
    if any(role.diode_binding_policy == "internal_module_diode" for role in section_roles):
        return "internal_module_diode"
    return next((role.diode_binding_policy for role in section_roles if role.diode_binding_policy), None)


def _short_placement_label(section_roles: tuple[SemiconductorGeometryRoleLayout, ...]) -> str:
    labels = tuple(_short_role_label(role.role_name) for role in section_roles)
    if "SW" in labels and "D" in labels:
        return "SW/D"
    return "/".join(dict.fromkeys(labels))


def _build_role_group_spec(
    instance: PhysicalPackageInstance,
    *,
    sink_width_mm: float,
) -> dict[str, object]:
    role_layout = instance.primary_role_layout
    layout = role_layout.layout
    if layout is None:
        return {"instance": instance, "width_mm": 1.0, "depth_mm": 1.0, "body_offsets_mm": ((0.0, 0.0),)}
    template = resolve_semiconductor_3d_package_template(layout)
    quantity = max(int(instance.quantity or 1), 1)
    package_gap_mm = _package_gap_mm(template.body_width_mm)
    row_gap_mm = _package_row_gap_mm(template.body_depth_mm)
    max_columns = max(int((sink_width_mm + package_gap_mm) // (template.body_width_mm + package_gap_mm)), 1)
    columns = min(quantity, max_columns)
    body_offsets: list[tuple[float, float]] = []
    for package_index in range(quantity):
        column_index = package_index % columns
        row_index = package_index // columns
        body_offsets.append(
            (
                column_index * (template.body_width_mm + package_gap_mm),
                row_index * (template.body_depth_mm + row_gap_mm),
            )
        )
    row_count = (quantity + columns - 1) // columns
    group_width_mm = min(quantity, columns) * template.body_width_mm + max(min(quantity, columns) - 1, 0) * package_gap_mm
    group_depth_mm = row_count * template.body_depth_mm + max(row_count - 1, 0) * row_gap_mm
    return {
        "instance": instance,
        "width_mm": group_width_mm,
        "depth_mm": group_depth_mm,
        "body_offsets_mm": tuple(body_offsets),
    }


def _sink_base_height_mm(sink_height_mm: float) -> float:
    """Resolve the base thickness under the flat mounting face."""

    return min(max(0.32 * sink_height_mm, 1.2), 0.62 * sink_height_mm)


def _package_assembly_size_mm(layout: SemiconductorGeometryLayout | None) -> tuple[float, float]:
    if layout is None:
        return (1.0, 1.0)
    template = resolve_semiconductor_3d_package_template(layout)
    if template.template_id in _SIDE_LEADED_TEMPLATE_IDS:
        return (template.body_width_mm + (2.0 * template.lead_length_mm), template.body_depth_mm)
    return (template.body_width_mm, template.body_depth_mm + template.lead_length_mm)


def _role_assembly_size_mm(role_layout: SemiconductorGeometryRoleLayout) -> tuple[float, float]:
    layout = role_layout.layout
    if layout is None:
        return (1.0, 1.0)
    quantity = max(int(role_layout.quantity or 1), 1)
    package_width_mm, package_depth_mm = _package_assembly_size_mm(layout)
    return (
        quantity * package_width_mm + max(quantity - 1, 0) * _package_gap_mm(package_width_mm),
        package_depth_mm,
    )


def _package_gap_mm(package_width_mm: float) -> float:
    return max(3.0, 0.28 * package_width_mm)


def _package_row_gap_mm(package_depth_mm: float) -> float:
    return max(4.0, 0.35 * package_depth_mm)


def _build_role_lead_boxes(
    role_name: str,
    template: Semiconductor3DPackageTemplate,
    body_boxes: tuple[Semiconductor3DBox, ...],
) -> tuple[Semiconductor3DBox, ...]:
    lead_boxes: list[Semiconductor3DBox] = []
    for package_index, body in enumerate(body_boxes):
        lead_thickness_mm = min(max(0.16 * template.body_thickness_mm, 0.12), 0.55)
        if template.template_id.startswith("to247") or template.template_id.startswith("to220"):
            lead_count = max(template.lead_count, 2)
            lead_span_mm = max((lead_count - 1) * template.lead_pitch_mm, 0.0)
            lead_start_x_mm = body.x_mm + 0.5 * (body.dx_mm - lead_span_mm)
            for lead_index in range(lead_count):
                x_mm = lead_start_x_mm + lead_index * template.lead_pitch_mm
                lead_boxes.append(
                    Semiconductor3DBox(
                        kind="package_lead",
                        role_name=role_name,
                        x_mm=x_mm - 0.5 * template.lead_width_mm,
                        y_mm=body.y_mm - template.lead_length_mm,
                        z_mm=body.z_mm,
                        dx_mm=template.lead_width_mm,
                        dy_mm=template.lead_length_mm,
                        dz_mm=lead_thickness_mm,
                        gid=f"semiconductor-3d:package-lead:{role_name}:{package_index}:{lead_index}",
                    )
                )
        elif template.template_id in _SIDE_LEADED_TEMPLATE_IDS | _BOTTOM_LEADED_SMD_TEMPLATE_IDS:
            leads_per_side = max(template.lead_count // 2, 1)
            used_span_mm = min((leads_per_side - 1) * template.lead_pitch_mm, 0.82 * template.body_depth_mm)
            lead_start_y_mm = body.y_mm + 0.5 * (template.body_depth_mm - used_span_mm)
            for side in (-1, 1):
                lead_x_mm = body.x_mm - template.lead_length_mm if side < 0 else body.x_mm + body.dx_mm
                for lead_index in range(leads_per_side):
                    y_mm = lead_start_y_mm + lead_index * (used_span_mm / max(leads_per_side - 1, 1))
                    lead_boxes.append(
                        Semiconductor3DBox(
                            kind="package_lead",
                            role_name=role_name,
                            x_mm=lead_x_mm,
                            y_mm=y_mm - 0.5 * template.lead_width_mm,
                            z_mm=body.z_mm,
                            dx_mm=template.lead_length_mm,
                            dy_mm=template.lead_width_mm,
                            dz_mm=lead_thickness_mm,
                            gid=f"semiconductor-3d:package-lead:{role_name}:{package_index}:{side}:{lead_index}",
                        )
                    )
    return tuple(lead_boxes)


def _build_placement_debug(
    package_boxes: tuple[Semiconductor3DBox, ...],
    *,
    sink_box: Semiconductor3DBox,
    fin_boxes: tuple[Semiconductor3DBox, ...],
) -> tuple[Semiconductor3DPlacementDebug, ...]:
    package_indexes_by_role: dict[str, int] = {}
    debug_entries: list[Semiconductor3DPlacementDebug] = []
    for box in package_boxes:
        role_name = box.role_name or ""
        package_index = package_indexes_by_role.get(role_name, 0)
        package_indexes_by_role[role_name] = package_index + 1
        debug_entries.append(
            Semiconductor3DPlacementDebug(
                role_name=role_name,
                package_index=package_index,
                mounting_face_z_mm=_MOUNTING_FACE_Z_MM,
                device_bottom_z_mm=box.z_mm,
                device_top_z_mm=box.z_mm + box.dz_mm,
                device_intersects_heatsink=_boxes_intersect_3d(box, sink_box),
                device_intersects_fins=any(_boxes_intersect_3d(box, fin) for fin in fin_boxes),
            )
        )
    return tuple(debug_entries)


def _package_body_offset_mm(template: Semiconductor3DPackageTemplate) -> tuple[float, float]:
    if template.template_id in _SIDE_LEADED_TEMPLATE_IDS:
        return (template.lead_length_mm, 0.0)
    return (0.0, template.lead_length_mm)


def _boxes_intersect_3d(left: Semiconductor3DBox, right: Semiconductor3DBox) -> bool:
    return (
        left.x_mm < right.x_mm + right.dx_mm
        and left.x_mm + left.dx_mm > right.x_mm
        and left.y_mm < right.y_mm + right.dy_mm
        and left.y_mm + left.dy_mm > right.y_mm
        and left.z_mm < right.z_mm + right.dz_mm
        and left.z_mm + left.dz_mm > right.z_mm
    )


def _draw_sink(axis, scene: Semiconductor3DScene) -> None:
    sink = scene.sink_box
    base = scene.sink_base_box
    add_box_3d(
        axis,
        base.x_mm,
        base.y_mm,
        base.z_mm,
        base.dx_mm,
        base.dy_mm,
        base.dz_mm,
        facecolor=MUTED_METAL_FACE,
        edgecolor=DARK_OUTLINE,
        alpha=0.24,
        linewidth=0.85,
        gid=sink.gid,
    )
    for fin in scene.fin_boxes:
        add_box_3d(
            axis,
            fin.x_mm,
            fin.y_mm,
            fin.z_mm,
            fin.dx_mm,
            fin.dy_mm,
            fin.dz_mm,
            facecolor=MUTED_METAL_FACE_ALT,
            edgecolor="#475569",
            alpha=0.36,
            linewidth=0.55,
            gid=fin.gid,
        )
    _draw_mounting_face_surface(axis, base)
    _draw_mounting_face_outline(axis, base)
    add_box_outline_3d(axis, sink.x_mm, sink.y_mm, sink.z_mm, sink.dx_mm, sink.dy_mm, sink.dz_mm, color=DARK_OUTLINE, linewidth=0.85)


def _draw_mounting_face_surface(axis, base: Semiconductor3DBox) -> None:
    add_box_3d(
        axis,
        base.x_mm,
        base.y_mm,
        _MOUNTING_FACE_Z_MM - _MOUNTING_FACE_VISUAL_THICKNESS_MM,
        base.dx_mm,
        base.dy_mm,
        _MOUNTING_FACE_VISUAL_THICKNESS_MM,
        facecolor="#e5e7eb",
        edgecolor="#64748b",
        alpha=0.10,
        linewidth=0.45,
        gid="semiconductor-3d:mounting-face-surface",
    )


def _draw_mounting_face_outline(axis, base: Semiconductor3DBox) -> None:
    z_mm = base.z_mm + base.dz_mm
    x0_mm = base.x_mm
    x1_mm = base.x_mm + base.dx_mm
    y0_mm = base.y_mm
    y1_mm = base.y_mm + base.dy_mm
    edges = (
        ((x0_mm, y0_mm), (x1_mm, y0_mm)),
        ((x1_mm, y0_mm), (x1_mm, y1_mm)),
        ((x1_mm, y1_mm), (x0_mm, y1_mm)),
        ((x0_mm, y1_mm), (x0_mm, y0_mm)),
    )
    for index, ((start_x_mm, start_y_mm), (end_x_mm, end_y_mm)) in enumerate(edges):
        (line,) = axis.plot(
            [start_x_mm, end_x_mm],
            [start_y_mm, end_y_mm],
            [z_mm, z_mm],
            color="#0f172a",
            linewidth=1.25,
        )
        line.set_gid(f"semiconductor-3d:mounting-face-edge:{index}")


def _render_scheme_panel_3d(
    axis,
    scene: Semiconductor3DScene,
    *,
    title: str,
    comparison_settings: Semiconductor3DComparisonSettings | None = None,
) -> None:
    _draw_sink(axis, scene)
    for placement in scene.role_placements:
        _draw_role_package(axis, placement)
    _annotate_scene(axis, scene)
    configure_engineering_3d_axis(axis, title=title)
    if comparison_settings is None:
        set_equal_physical_box_aspect(
            axis,
            center_x_mm=scene.center_x_mm,
            center_y_mm=scene.center_y_mm,
            center_z_mm=scene.center_z_mm,
            total_span_x_mm=scene.total_span_x_mm,
            total_span_y_mm=scene.total_span_y_mm,
            total_span_z_mm=scene.total_span_z_mm,
        )
        return
    axis.set_xlim(scene.center_x_mm + comparison_settings.panel_xlim_mm[0], scene.center_x_mm + comparison_settings.panel_xlim_mm[1])
    axis.set_ylim(scene.center_y_mm + comparison_settings.panel_ylim_mm[0], scene.center_y_mm + comparison_settings.panel_ylim_mm[1])
    axis.set_zlim(scene.center_z_mm + comparison_settings.panel_zlim_mm[0], scene.center_z_mm + comparison_settings.panel_zlim_mm[1])
    axis.set_box_aspect(
        (
            comparison_settings.total_span_x_mm,
            comparison_settings.total_span_y_mm,
            comparison_settings.total_span_z_mm,
        )
    )


def _draw_role_package(axis, placement: Semiconductor3DRolePlacement) -> None:
    template = placement.template
    for package_index, body in enumerate(placement.body_boxes):
        if template.template_id in _MODULE_TEMPLATE_IDS:
            _draw_module_envelope_3d(axis, placement, body=body, package_index=package_index)
        elif template.template_id.startswith("to247") or template.template_id.startswith("to220"):
            _draw_to247_3d(axis, placement, body=body, package_index=package_index)
        elif template.template_id in _SIDE_LEADED_TEMPLATE_IDS | _LEADLESS_TEMPLATE_IDS | _BOTTOM_LEADED_SMD_TEMPLATE_IDS:
            _draw_smd_package_3d(axis, placement, body=body, package_index=package_index)
        else:
            _draw_generic_package_3d(axis, placement, body=body, package_index=package_index)
    body = _center_label_body(placement)
    axis.text(
        body.x_mm + 0.5 * body.dx_mm,
        body.y_mm + 0.5 * body.dy_mm,
        body.z_mm + body.dz_mm + 0.7,
        placement.short_label,
        ha="center",
        va="center",
        fontsize=8.0,
        color="#111827",
    )


def _center_label_body(placement: Semiconductor3DRolePlacement) -> Semiconductor3DBox:
    if len(placement.body_boxes) == 1:
        return placement.body_box
    first = placement.body_boxes[0]
    last = placement.body_boxes[-1]
    return Semiconductor3DBox(
        kind="label_anchor",
        role_name=placement.role_name,
        x_mm=first.x_mm,
        y_mm=first.y_mm,
        z_mm=first.z_mm,
        dx_mm=(last.x_mm + last.dx_mm) - first.x_mm,
        dy_mm=max(box.dy_mm for box in placement.body_boxes),
        dz_mm=max(box.dz_mm for box in placement.body_boxes),
        gid=f"semiconductor-3d:label-anchor:{placement.role_name}",
    )


def _draw_smd_package_3d(axis, placement: Semiconductor3DRolePlacement, *, body: Semiconductor3DBox, package_index: int) -> None:
    template = placement.template
    add_box_3d(axis, body.x_mm, body.y_mm, body.z_mm, body.dx_mm, body.dy_mm, body.dz_mm, facecolor=PACKAGE_BODY_FACE, edgecolor="#020617", alpha=1.0, gid=body.gid)
    pad_width_mm = min(template.tab_width_mm, template.body_width_mm)
    pad_depth_mm = min(template.tab_depth_mm, template.body_depth_mm)
    add_box_3d(
        axis,
        body.x_mm + 0.5 * (body.dx_mm - pad_width_mm),
        body.y_mm + 0.5 * (body.dy_mm - pad_depth_mm),
        body.z_mm + body.dz_mm,
        pad_width_mm,
        pad_depth_mm,
        0.08,
        facecolor="#94a3b8",
        edgecolor="#475569",
        alpha=0.95,
        linewidth=0.45,
        gid=f"semiconductor-3d:package-pad:{placement.role_name}:{package_index}",
    )
    if template.template_id in _LEADLESS_TEMPLATE_IDS:
        return
    leads_per_side = max(template.lead_count // 2, 1)
    used_span_mm = min((leads_per_side - 1) * template.lead_pitch_mm, 0.82 * template.body_depth_mm)
    lead_start_y_mm = body.y_mm + 0.5 * (template.body_depth_mm - used_span_mm)
    lead_thickness_mm = min(max(0.18 * template.body_thickness_mm, 0.12), 0.28)
    for side in (-1, 1):
        lead_x_mm = body.x_mm - template.lead_length_mm if side < 0 else body.x_mm + body.dx_mm
        for index in range(leads_per_side):
            y_mm = lead_start_y_mm + index * (used_span_mm / max(leads_per_side - 1, 1))
            add_box_3d(
                axis,
                lead_x_mm,
                y_mm - 0.5 * template.lead_width_mm,
                body.z_mm,
                template.lead_length_mm,
                template.lead_width_mm,
                lead_thickness_mm,
                facecolor=SILVER_LEAD_FACE,
                edgecolor="#4b5563",
                alpha=0.88,
                linewidth=0.35,
            )


def _draw_to247_3d(axis, placement: Semiconductor3DRolePlacement, *, body: Semiconductor3DBox, package_index: int) -> None:
    template = placement.template
    add_box_3d(axis, body.x_mm, body.y_mm, body.z_mm, body.dx_mm, body.dy_mm, body.dz_mm, facecolor=PACKAGE_BODY_FACE, edgecolor="#020617", alpha=1.0, gid=body.gid)
    tab_depth_mm = min(template.tab_depth_mm, template.body_depth_mm)
    add_box_3d(
        axis,
        body.x_mm,
        body.y_mm + body.dy_mm - tab_depth_mm,
        body.z_mm + body.dz_mm,
        min(template.tab_width_mm, body.dx_mm),
        tab_depth_mm,
        0.10,
        facecolor="#64748b",
        edgecolor="#334155",
        alpha=0.92,
        linewidth=0.55,
        gid=f"semiconductor-3d:mount-tab:{placement.role_name}:{package_index}",
    )
    if template.hole_diameter_mm > 0.0:
        axis.scatter(
            [body.x_mm + 0.5 * min(template.tab_width_mm, body.dx_mm)],
            [body.y_mm + body.dy_mm - 0.5 * tab_depth_mm],
            [body.z_mm + body.dz_mm + 0.16],
            s=max((template.hole_diameter_mm * 7.0) ** 2, 14.0),
            marker="o",
            color="#f8fafc",
            edgecolor="#0f172a",
            linewidth=0.5,
            depthshade=False,
        )
    lead_count = max(template.lead_count, 2)
    lead_span_mm = max((lead_count - 1) * template.lead_pitch_mm, 0.0)
    lead_start_x_mm = body.x_mm + 0.5 * (body.dx_mm - lead_span_mm)
    lead_thickness_mm = min(max(0.16 * template.body_thickness_mm, 0.28), 0.55)
    for index in range(lead_count):
        x_mm = lead_start_x_mm + index * template.lead_pitch_mm
        add_box_3d(
            axis,
            x_mm - 0.5 * template.lead_width_mm,
            body.y_mm - template.lead_length_mm,
            body.z_mm,
            template.lead_width_mm,
            template.lead_length_mm,
            lead_thickness_mm,
            facecolor=SILVER_LEAD_FACE,
            edgecolor="#4b5563",
            alpha=0.88,
            linewidth=0.42,
        )


def _draw_module_envelope_3d(axis, placement: Semiconductor3DRolePlacement, *, body: Semiconductor3DBox, package_index: int) -> None:
    template = placement.template
    baseplate_thickness_mm = min(max(0.14 * body.dz_mm, 1.2), 0.34 * body.dz_mm)
    add_box_3d(
        axis,
        body.x_mm,
        body.y_mm,
        body.z_mm,
        body.dx_mm,
        body.dy_mm,
        baseplate_thickness_mm,
        facecolor="#cbd5e1",
        edgecolor="#334155",
        alpha=0.78,
        gid=f"semiconductor-3d:module-baseplate:{placement.role_name}:{package_index}",
    )
    add_box_3d(
        axis,
        body.x_mm,
        body.y_mm,
        body.z_mm + baseplate_thickness_mm,
        body.dx_mm,
        body.dy_mm,
        max(body.dz_mm - baseplate_thickness_mm, 0.2),
        facecolor="#dbeafe",
        edgecolor="#1d4ed8",
        alpha=0.86,
        gid=body.gid,
    )
    terminal_count = max(min(template.lead_count, 12), 2)
    terminal_width_mm = min(max(template.lead_width_mm, 2.0), 0.12 * body.dx_mm)
    terminal_depth_mm = min(max(template.lead_length_mm, 3.0), 0.16 * body.dy_mm)
    terminal_height_mm = min(max(0.12 * body.dz_mm, 1.5), 6.0)
    pitch_mm = body.dx_mm / max(terminal_count + 1, 1)
    for index in range(terminal_count):
        add_box_3d(
            axis,
            body.x_mm + (index + 1) * pitch_mm - 0.5 * terminal_width_mm,
            body.y_mm + body.dy_mm - terminal_depth_mm - 1.0,
            body.z_mm + body.dz_mm,
            terminal_width_mm,
            terminal_depth_mm,
            terminal_height_mm,
            facecolor=SILVER_LEAD_FACE,
            edgecolor="#4b5563",
            alpha=0.84,
            linewidth=0.45,
        )


def _draw_generic_package_3d(axis, placement: Semiconductor3DRolePlacement, *, body: Semiconductor3DBox, package_index: int) -> None:
    add_box_3d(
        axis,
        body.x_mm,
        body.y_mm,
        body.z_mm,
        body.dx_mm,
        body.dy_mm,
        body.dz_mm,
        facecolor="#334155",
        edgecolor="#0f172a",
        alpha=0.94,
        gid=body.gid,
    )


def _annotate_scene(axis, scene: Semiconductor3DScene) -> None:
    axis.text2D(
        0.02,
        0.98,
        "\n".join(scene.summary_lines),
        transform=axis.transAxes,
        va="top",
        ha="left",
        fontsize=8.3,
        bbox=TEXT_BOX_STYLE,
    )


def _build_summary_lines(
    target: SemiconductorGeometryTarget,
    placements: list[Semiconductor3DRolePlacement],
    *,
    sink_width_mm: float,
    sink_height_mm: float,
    sink_depth_mm: float,
) -> tuple[str, ...]:
    lines = [target.label, f"Sink: {sink_width_mm:.3g} x {sink_depth_mm:.3g} x {sink_height_mm:.3g} mm"]
    for placement in placements:
        line = f"{placement.short_label}: {placement.part_number}, {placement.package}, qty={placement.quantity}"
        if placement.module_group_id and placement.diode_binding_policy == "internal_module_diode":
            line += ", binding=internal_module_diode"
        lines.append(line)
    return tuple(lines)


def _build_layout_warnings(package_boxes: tuple[Semiconductor3DBox, ...], *, sink_width_mm: float, sink_depth_mm: float) -> list[str]:
    warnings: list[str] = []
    for box in package_boxes:
        if box.x_mm < 0.0 or box.x_mm + box.dx_mm > sink_width_mm or box.y_mm < 0.0 or box.y_mm + box.dy_mm > sink_depth_mm:
            warnings.append("package placement exceeds mounting face")
            break
    for index, box in enumerate(package_boxes):
        if any(_boxes_overlap_xy(box, other) for other in package_boxes[index + 1 :]):
            warnings.append("package bodies overlap on mounting face")
            break
    return warnings


def _boxes_overlap_xy(left: Semiconductor3DBox, right: Semiconductor3DBox) -> bool:
    return (
        left.x_mm < right.x_mm + right.dx_mm
        and left.x_mm + left.dx_mm > right.x_mm
        and left.y_mm < right.y_mm + right.dy_mm
        and left.y_mm + left.dy_mm > right.y_mm
    )


def _short_role_label(role_name: str) -> str:
    normalized = role_name.strip().casefold()
    if normalized == "main_switch":
        return "SW"
    if normalized == "rectifier_diode":
        return "D"
    return role_name.upper()[:6]
