"""Shared physical package grouping for semiconductor geometry renderers."""

from __future__ import annotations

from dataclasses import dataclass

from ...models.semiconductor_geometry_result import SemiconductorGeometryRoleLayout, SemiconductorGeometryTarget

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


@dataclass(frozen=True)
class PhysicalPackageInstance:
    """One physical package body that may contain one or more electrical roles."""

    instance_id: str
    package_part_number: str
    package_name: str
    quantity: int
    package_level: str | None
    device_structure_type: str | None
    module_group_id: str | None
    roles_in_package: tuple[str, ...]
    role_labels: str
    section_part_numbers: dict[str, str]
    diode_binding_policy: str | None
    physical_dimensions_mm: tuple[float, float, float] | None
    renderer_template_id: str
    primary_role_layout: SemiconductorGeometryRoleLayout
    section_role_layouts: tuple[SemiconductorGeometryRoleLayout, ...]


def build_physical_package_instances_for_target(target: SemiconductorGeometryTarget) -> tuple[PhysicalPackageInstance, ...]:
    """Build physical package instances for one semiconductor geometry target."""

    return build_physical_package_instances_for_role_layouts(target.role_layouts)


def build_physical_package_instances_for_role_layouts(
    role_layouts: tuple[SemiconductorGeometryRoleLayout, ...],
) -> tuple[PhysicalPackageInstance, ...]:
    """Group role layouts into physical package instances.

    Independent roles remain separate. Module-bound switch and internal diode
    sections sharing a module_group_id collapse into one physical module body.
    """

    ordered_role_layouts = _ordered_drawable_roles(role_layouts)
    instances: list[PhysicalPackageInstance] = []
    consumed_indexes: set[int] = set()
    for index, role_layout in enumerate(ordered_role_layouts):
        if index in consumed_indexes:
            continue
        module_group_id = role_layout.module_group_id
        if module_group_id and role_layout.package_level == "power_module":
            member_indexes = [
                member_index
                for member_index, member in enumerate(ordered_role_layouts)
                if member.module_group_id == module_group_id and member.package_level == "power_module"
            ]
            members = tuple(ordered_role_layouts[member_index] for member_index in member_indexes)
            if len(members) > 1 and any(member.diode_binding_policy == "internal_module_diode" for member in members):
                primary = next((member for member in members if member.module_section_role != "internal_diode"), members[0])
                instances.append(_build_instance(primary, members))
                consumed_indexes.update(member_indexes)
                continue
        instances.append(_build_instance(role_layout, (role_layout,)))
        consumed_indexes.add(index)
    return tuple(instances)


def _ordered_drawable_roles(role_layouts: tuple[SemiconductorGeometryRoleLayout, ...]) -> tuple[SemiconductorGeometryRoleLayout, ...]:
    drawable = [role for role in role_layouts if role.part_number is not None and role.layout is not None]
    by_name = {role.role_name: role for role in drawable}
    ordered = [by_name[role_name] for role_name in _PREFERRED_ROLE_ORDER if role_name in by_name]
    ordered.extend(role for role in drawable if role.role_name not in _PREFERRED_ROLE_ORDER)
    return tuple(ordered)


def _build_instance(
    primary: SemiconductorGeometryRoleLayout,
    section_roles: tuple[SemiconductorGeometryRoleLayout, ...],
) -> PhysicalPackageInstance:
    layout = primary.layout
    section_part_numbers = {role.role_name: role.part_number or "-" for role in section_roles}
    diode_binding_policy = _instance_diode_binding_policy(section_roles)
    role_labels = _role_labels(section_roles)
    dimensions_mm = None
    renderer_template_id = ""
    if layout is not None:
        dimensions_mm = (
            layout.package_body_width_mm,
            layout.package_body_height_mm,
            layout.package_body_thickness_mm,
        )
        renderer_template_id = layout.renderer_template_id
    return PhysicalPackageInstance(
        instance_id=_instance_id(primary, section_roles),
        package_part_number=primary.part_number or "-",
        package_name=primary.package or (layout.package if layout is not None else "-"),
        quantity=max(int(primary.quantity or 1), 1),
        package_level=primary.package_level,
        device_structure_type=primary.device_structure_type,
        module_group_id=primary.module_group_id,
        roles_in_package=tuple(role.role_name for role in section_roles),
        role_labels=role_labels,
        section_part_numbers=section_part_numbers,
        diode_binding_policy=diode_binding_policy,
        physical_dimensions_mm=dimensions_mm,
        renderer_template_id=renderer_template_id,
        primary_role_layout=primary,
        section_role_layouts=section_roles,
    )


def _instance_id(primary: SemiconductorGeometryRoleLayout, section_roles: tuple[SemiconductorGeometryRoleLayout, ...]) -> str:
    if primary.module_group_id and len(section_roles) > 1:
        return f"module:{primary.module_group_id}"
    return f"role:{primary.role_name}:{primary.part_number or '-'}"


def _instance_diode_binding_policy(section_roles: tuple[SemiconductorGeometryRoleLayout, ...]) -> str | None:
    if any(role.diode_binding_policy == "internal_module_diode" for role in section_roles):
        return "internal_module_diode"
    return next((role.diode_binding_policy for role in section_roles if role.diode_binding_policy), None)


def _role_labels(section_roles: tuple[SemiconductorGeometryRoleLayout, ...]) -> str:
    labels = tuple(_short_role_label(role.role_name) for role in section_roles)
    if "SW" in labels and "D" in labels:
        return "SW/D"
    return "/".join(dict.fromkeys(labels))


def _short_role_label(role_name: str) -> str:
    normalized = role_name.strip().casefold()
    if normalized == "main_switch":
        return "SW"
    if normalized == "rectifier_diode":
        return "D"
    if normalized == "sync_switch":
        return "SYNC"
    if normalized in {"s1", "s2", "s3", "s4"}:
        return role_name.upper()
    if normalized.startswith("switch_"):
        return role_name.replace("switch_", "").upper()
    return role_name.upper()[:6]
