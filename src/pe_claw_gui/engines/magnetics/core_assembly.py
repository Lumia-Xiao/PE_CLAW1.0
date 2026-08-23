"""Idealized same-core stacked magnetic assembly helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import math

from ...models.inductor import FixedInductorDesignCandidate


@dataclass(frozen=True)
class StackedCoreAssembly:
    """Idealized same-core stacked assembly used for first-pass expansion."""

    base_core_name: str
    stack_count: int
    assembly_type: str
    effective_Ae_m2: float | None
    effective_le_m: float | None
    effective_Ve_m3: float | None
    effective_window_area_m2: float | None
    effective_total_volume_m3: float | None
    physical_envelope_volume_m3: float | None = None
    solid_material_volume_m3: float | None = None
    mass_kg: float | None = None
    winding_volume_m3: float | None = None
    volume_policy: str = "legacy_v1_stack_total_volume"
    notes: list[str] = field(default_factory=list)


def build_same_core_stack_assembly(
    candidate: FixedInductorDesignCandidate,
    stack_count: int,
) -> StackedCoreAssembly | None:
    """Build an idealized same-core stacked assembly from a single-core candidate."""
    if stack_count < 1 or stack_count > 3:
        return None

    metadata = candidate.metadata
    ae_m2 = _as_float(metadata.get("core_effective_area_m2"))
    le_m = _as_float(metadata.get("core_path_length_m"))
    ve_m3 = _as_float(metadata.get("core_effective_volume_m3"))
    aw_m2 = _as_float(metadata.get("core_window_area_m2"))
    core_envelope_m3 = _as_float(metadata.get("physical_envelope_volume_m3"))
    if core_envelope_m3 is None:
        core_envelope_m3 = candidate.core_volume_m3
    solid_material_volume_m3 = _as_float(metadata.get("solid_material_volume_m3"))
    core_mass_kg = _as_float(metadata.get("core_mass_kg"))
    winding_volume_m3 = candidate.winding_volume_m3
    corrected_v2_semantics = isinstance(metadata.get("core_source_provenance"), dict)
    if ae_m2 is None or le_m is None or ve_m3 is None or aw_m2 is None or core_envelope_m3 is None:
        return None

    return _cached_build_same_core_stack_assembly(
        base_core_name=candidate.base_core_name or candidate.core_name,
        stack_count=stack_count,
        base_ae_m2=ae_m2,
        base_le_m=le_m,
        base_ve_m3=ve_m3,
        base_aw_m2=aw_m2,
        base_physical_envelope_volume_m3=core_envelope_m3,
        base_solid_material_volume_m3=solid_material_volume_m3,
        base_mass_kg=core_mass_kg,
        base_winding_volume_m3=winding_volume_m3,
        corrected_v2_semantics=corrected_v2_semantics,
    )


@lru_cache(maxsize=256)
def _cached_build_same_core_stack_assembly(
    base_core_name: str,
    stack_count: int,
    base_ae_m2: float,
    base_le_m: float,
    base_ve_m3: float,
    base_aw_m2: float,
    base_physical_envelope_volume_m3: float,
    base_solid_material_volume_m3: float | None,
    base_mass_kg: float | None,
    base_winding_volume_m3: float | None,
    corrected_v2_semantics: bool,
) -> StackedCoreAssembly:
    # First-pass idealized same-core stacking model:
    # Ae, Ve, window area, and total volume scale linearly with stack count,
    # while effective magnetic path length is held constant.
    assembled_envelope_m3 = stack_count * base_physical_envelope_volume_m3
    assembled_winding_m3 = (
        base_winding_volume_m3
        if corrected_v2_semantics
        else (stack_count * base_winding_volume_m3 if base_winding_volume_m3 is not None else None)
    )
    assembled_total_m3 = (
        assembled_envelope_m3 + (assembled_winding_m3 or 0.0)
    )
    return StackedCoreAssembly(
        base_core_name=base_core_name,
        stack_count=stack_count,
        assembly_type="stacked_same_core",
        effective_Ae_m2=stack_count * base_ae_m2,
        effective_le_m=base_le_m,
        effective_Ve_m3=stack_count * base_ve_m3,
        effective_window_area_m2=stack_count * base_aw_m2,
        effective_total_volume_m3=assembled_total_m3,
        physical_envelope_volume_m3=assembled_envelope_m3,
        solid_material_volume_m3=(
            stack_count * base_solid_material_volume_m3
            if base_solid_material_volume_m3 is not None
            else None
        ),
        mass_kg=stack_count * base_mass_kg if base_mass_kg is not None else None,
        winding_volume_m3=assembled_winding_m3,
        volume_policy=(
            "step19d_v2_core_geometry_times_stack_once_plus_unchanged_winding_once"
            if corrected_v2_semantics
            else "legacy_v1_entire_candidate_volume_times_stack"
        ),
        notes=[
            "First-pass idealized same-core stacking approximation.",
            "Only same-core stack_count = 1, 2, 3 is supported.",
            "Effective Ae, Ve, window area, core envelope, source solid volume, and source mass scale once with stack count.",
            (
                "The corrected-v2 unchanged turns/wire winding volume and copper loss are retained once."
                if corrected_v2_semantics
                else "The normalized-v1 production path retains its historical whole-candidate stack-volume policy until promotion."
            ),
            "Effective le is held constant.",
            "Gap handling remains a simplified first-pass total-gap approximation.",
        ],
    )


def _as_float(value) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value)
        return resolved if math.isfinite(resolved) else None
    except (TypeError, ValueError):
        return None
