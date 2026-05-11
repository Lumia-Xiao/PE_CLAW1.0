"""Lightweight geometry proxies for first-pass magnetic thermal estimates."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ...models.inductor import FixedInductorDesignCandidate
from ...utils.core_family_semantics import resolve_core_assembly_envelope


@dataclass(frozen=True)
class MagneticThermalGeometryProxy:
    """Best-effort size and area proxies for a magnetic design."""

    total_volume_m3: float | None
    core_volume_m3: float | None
    winding_volume_m3: float | None
    total_surface_area_proxy_m2: float | None
    core_surface_area_proxy_m2: float | None
    winding_surface_area_proxy_m2: float | None
    notes: list[str] = field(default_factory=list)


def build_geometry_proxy(design: FixedInductorDesignCandidate) -> MagneticThermalGeometryProxy:
    """Resolve volume and surface proxies from the available magnetic-design metadata."""
    notes: list[str] = []
    metadata = design.metadata

    total_volume_m3 = _positive_or_none(design.total_volume_m3)
    core_volume_m3 = _positive_or_none(design.core_volume_m3)
    winding_volume_m3 = _positive_or_none(design.winding_volume_m3)

    if total_volume_m3 is None and core_volume_m3 is not None and winding_volume_m3 is not None:
        total_volume_m3 = core_volume_m3 + winding_volume_m3
        notes.append("Total magnetic volume was reconstructed from core and winding volumes.")

    if total_volume_m3 is None:
        gross_volume_m3 = _positive_or_none(metadata.get("gross_volume_m3"))
        if gross_volume_m3 is not None:
            total_volume_m3 = gross_volume_m3
            notes.append("Used gross core volume metadata as the thermal total-volume proxy.")

    if total_volume_m3 is None:
        return MagneticThermalGeometryProxy(
            total_volume_m3=None,
            core_volume_m3=core_volume_m3,
            winding_volume_m3=winding_volume_m3,
            total_surface_area_proxy_m2=None,
            core_surface_area_proxy_m2=None,
            winding_surface_area_proxy_m2=None,
            notes=["Magnetic volume is unavailable; thermal size proxy could not be resolved.", *notes],
        )

    if core_volume_m3 is None and winding_volume_m3 is None:
        core_volume_m3 = 0.70 * total_volume_m3
        winding_volume_m3 = 0.30 * total_volume_m3
        notes.append("Core/winding volume split was unavailable; used a 70/30 total-volume partition heuristic.")
    elif core_volume_m3 is None and winding_volume_m3 is not None:
        core_volume_m3 = max(total_volume_m3 - winding_volume_m3, 0.60 * total_volume_m3)
        notes.append("Core volume was reconstructed from total minus winding volume.")
    elif winding_volume_m3 is None and core_volume_m3 is not None:
        winding_volume_m3 = max(total_volume_m3 - core_volume_m3, 0.20 * total_volume_m3)
        notes.append("Winding volume was reconstructed from total minus core volume.")

    total_surface_area_proxy_m2 = _resolve_total_surface_proxy(design, total_volume_m3, notes)
    core_surface_area_proxy_m2 = _surface_from_volume_proxy(core_volume_m3)
    winding_surface_area_proxy_m2 = 1.10 * _surface_from_volume_proxy(winding_volume_m3)

    if total_surface_area_proxy_m2 is not None:
        core_surface_area_proxy_m2 = min(core_surface_area_proxy_m2, 0.90 * total_surface_area_proxy_m2)
        winding_surface_area_proxy_m2 = min(winding_surface_area_proxy_m2, 0.90 * total_surface_area_proxy_m2)

    return MagneticThermalGeometryProxy(
        total_volume_m3=total_volume_m3,
        core_volume_m3=core_volume_m3,
        winding_volume_m3=winding_volume_m3,
        total_surface_area_proxy_m2=total_surface_area_proxy_m2,
        core_surface_area_proxy_m2=core_surface_area_proxy_m2,
        winding_surface_area_proxy_m2=winding_surface_area_proxy_m2,
        notes=notes,
    )


def _resolve_total_surface_proxy(
    design: FixedInductorDesignCandidate,
    total_volume_m3: float,
    notes: list[str],
) -> float:
    metadata = design.metadata
    width_m, height_m, depth_m = _resolve_assembled_bounding_box(design, notes)
    if width_m is not None and height_m is not None and depth_m is not None:
        stacked_depth_m = depth_m * max(design.stack_count, 1)
        bbox_surface_m2 = 2.0 * (
            width_m * height_m
            + height_m * stacked_depth_m
            + width_m * stacked_depth_m
        )
        winding_surface_proxy_m2 = 0.55 * _surface_from_volume_proxy(_positive_or_none(design.winding_volume_m3) or 0.30 * total_volume_m3)
        notes.append("Used magnetic bounding-box dimensions as the primary external surface proxy.")
        if design.stack_count > 1:
            notes.append("Stacked same-core surface proxy assumes the assembly grows mainly along the depth axis.")
        return max(bbox_surface_m2 + winding_surface_proxy_m2, _surface_from_volume_proxy(total_volume_m3))

    notes.append("Exact magnetic outer dimensions were unavailable; used a compact-volume surface proxy.")
    return _surface_from_volume_proxy(total_volume_m3)


def _resolve_assembled_bounding_box(
    design: FixedInductorDesignCandidate,
    notes: list[str],
) -> tuple[float | None, float | None, float | None]:
    metadata = design.metadata
    family = str(metadata.get("family") or "").strip().lower()
    library_width_m = _positive_or_none(metadata.get("library_core_width_m"))
    library_height_m = _positive_or_none(metadata.get("library_core_height_m"))
    library_depth_m = _positive_or_none(metadata.get("library_core_depth_m"))
    if library_width_m is not None and library_height_m is not None and library_depth_m is not None:
        envelope = resolve_core_assembly_envelope(
            family=family,
            library_width_m=library_width_m,
            library_height_m=library_height_m,
            library_depth_m=library_depth_m,
        )
        if envelope.library_item_is_half_core:
            notes.append(
                f"Thermal bounding box uses the paired {family.upper()}-core assembly rather than a lone half-core library item."
            )
        return envelope.assembled_width_m, envelope.assembled_height_m, envelope.assembled_depth_m

    width_m = _positive_or_none(metadata.get("core_width_m"))
    height_m = _positive_or_none(metadata.get("core_height_m"))
    depth_m = _positive_or_none(metadata.get("core_depth_m"))
    if width_m is not None and height_m is not None and depth_m is not None:
        if bool(metadata.get("library_item_is_half_core")):
            notes.append(f"Thermal bounding box used assembled {family.upper()}-core metadata dimensions.")
        return width_m, height_m, depth_m
    return None, None, None


def _surface_from_volume_proxy(volume_m3: float) -> float:
    # Cube-like external area proxy: A ~ 6 * V^(2/3).
    return 6.0 * max(volume_m3, 1e-18) ** (2.0 / 3.0)


def _positive_or_none(value) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value)
    except (TypeError, ValueError):
        return None
    if resolved <= 0.0 or math.isnan(resolved) or math.isinf(resolved):
        return None
    return resolved
