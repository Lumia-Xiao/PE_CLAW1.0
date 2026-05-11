"""Idealized same-core stacked magnetic assembly helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

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
    total_volume_m3 = candidate.total_volume_m3
    if ae_m2 is None or le_m is None or ve_m3 is None or aw_m2 is None or total_volume_m3 is None:
        return None

    return _cached_build_same_core_stack_assembly(
        base_core_name=candidate.base_core_name or candidate.core_name,
        stack_count=stack_count,
        base_ae_m2=ae_m2,
        base_le_m=le_m,
        base_ve_m3=ve_m3,
        base_aw_m2=aw_m2,
        base_total_volume_m3=total_volume_m3,
    )


@lru_cache(maxsize=256)
def _cached_build_same_core_stack_assembly(
    base_core_name: str,
    stack_count: int,
    base_ae_m2: float,
    base_le_m: float,
    base_ve_m3: float,
    base_aw_m2: float,
    base_total_volume_m3: float,
) -> StackedCoreAssembly:
    # First-pass idealized same-core stacking model:
    # Ae, Ve, window area, and total volume scale linearly with stack count,
    # while effective magnetic path length is held constant.
    return StackedCoreAssembly(
        base_core_name=base_core_name,
        stack_count=stack_count,
        assembly_type="stacked_same_core",
        effective_Ae_m2=stack_count * base_ae_m2,
        effective_le_m=base_le_m,
        effective_Ve_m3=stack_count * base_ve_m3,
        effective_window_area_m2=stack_count * base_aw_m2,
        effective_total_volume_m3=stack_count * base_total_volume_m3,
        notes=[
            "First-pass idealized same-core stacking approximation.",
            "Only same-core stack_count = 1, 2, 3 is supported.",
            "Effective Ae, Ve, window area, and total volume scale linearly with stack count.",
            "Effective le is held constant.",
            "Gap handling remains a simplified first-pass total-gap approximation.",
        ],
    )


def _as_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
