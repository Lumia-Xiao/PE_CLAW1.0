"""Family-aware helpers for library-core versus assembled-core semantics."""

from __future__ import annotations

from dataclasses import dataclass, field

_PAIRED_HALF_CORE_FAMILIES = {"u", "e", "etd", "pq", "rm"}


@dataclass(frozen=True)
class CoreAssemblyEnvelope:
    """Resolved relationship between one library item and one assembled magnetic body."""

    family: str
    library_item_is_half_core: bool
    half_cores_per_assembly: int
    pairing_axis: str | None
    library_width_m: float
    library_height_m: float
    library_depth_m: float
    assembled_width_m: float
    assembled_height_m: float
    assembled_depth_m: float
    assembled_volume_m3: float
    notes: list[str] = field(default_factory=list)


def resolve_core_assembly_envelope(
    *,
    family: str,
    library_width_m: float,
    library_height_m: float,
    library_depth_m: float,
) -> CoreAssemblyEnvelope:
    """Resolve how one library core item maps to one practical assembled magnetic body."""
    normalized_family = (family or "").strip().lower()
    if normalized_family in _PAIRED_HALF_CORE_FAMILIES:
        assembled_width_m = library_width_m
        assembled_height_m = 2.0 * library_height_m
        assembled_depth_m = library_depth_m
        family_label = normalized_family.upper()
        return CoreAssemblyEnvelope(
            family=normalized_family,
            library_item_is_half_core=True,
            half_cores_per_assembly=2,
            pairing_axis="height",
            library_width_m=library_width_m,
            library_height_m=library_height_m,
            library_depth_m=library_depth_m,
            assembled_width_m=assembled_width_m,
            assembled_height_m=assembled_height_m,
            assembled_depth_m=assembled_depth_m,
            assembled_volume_m3=2.0 * library_width_m * library_height_m * library_depth_m,
            notes=[
                f"{family_label}-family library entries are interpreted as half cores.",
                f"One practical assembled magnetic body uses two {family_label} halves paired in the height direction.",
            ],
        )

    return CoreAssemblyEnvelope(
        family=normalized_family,
        library_item_is_half_core=False,
        half_cores_per_assembly=1,
        pairing_axis=None,
        library_width_m=library_width_m,
        library_height_m=library_height_m,
        library_depth_m=library_depth_m,
        assembled_width_m=library_width_m,
        assembled_height_m=library_height_m,
        assembled_depth_m=library_depth_m,
        assembled_volume_m3=library_width_m * library_height_m * library_depth_m,
        notes=[],
    )


def is_paired_half_core_family(family: str) -> bool:
    """Return whether the family is treated as a half-core library item."""
    return (family or "").strip().lower() in _PAIRED_HALF_CORE_FAMILIES
