"""Generic engineering metrics used for magnetic candidate screening."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...models.inductor import FixedInductorDesignCandidate
from .allow_profiles import MagneticAllowProfile


@dataclass(frozen=True)
class MagneticCandidateContext:
    """Generic runtime context for magnetic candidate screening."""

    topology_id: str
    fs_hz: float
    throughput_power_w: float | None = None
    throughput_label: str = "throughput power"
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MagneticCandidateEngineeringMetrics:
    """Resolved engineering metrics and margins for one magnetic candidate."""

    candidate_id: str
    b_peak_t: float | None
    b_allow_t: float | None
    total_loss_w: float | None
    p_loss_allow_w: float | None
    current_density_a_per_mm2: float | None
    j_allow_a_per_mm2: float | None
    fill_factor: float | None
    k_fill_allow: float | None
    volume_cm3: float | None
    throughput_power_w: float | None
    sat_margin: float | None
    loss_margin: float | None
    current_density_margin: float | None
    fill_margin: float | None
    notes: list[str] = field(default_factory=list)


def compute_candidate_engineering_metrics(
    candidate: FixedInductorDesignCandidate,
    context: MagneticCandidateContext,
    allow_profile: MagneticAllowProfile,
) -> MagneticCandidateEngineeringMetrics:
    """Compute generic engineering screening metrics for one magnetic candidate."""
    notes = list(context.notes)

    b_peak_t = _resolve_b_peak(candidate, notes)
    b_sat_100c_t = _resolve_b_sat_100c(candidate, notes)
    b_allow_t = (
        allow_profile.b_allow_ratio_to_bsat_100c * b_sat_100c_t
        if b_sat_100c_t is not None
        else None
    )

    total_loss_w = _resolve_total_loss(candidate, notes)
    volume_cm3 = _resolve_volume_cm3(candidate, notes)
    throughput_power_w = context.throughput_power_w
    density_limited_loss = (
        allow_profile.loss_allow_density_w_per_cm3 * volume_cm3
        if volume_cm3 is not None
        else None
    )
    power_limited_loss = (
        allow_profile.loss_allow_power_ratio * throughput_power_w
        if throughput_power_w is not None
        else None
    )
    p_loss_allow_w = _resolve_min_allow(power_limited_loss, density_limited_loss)

    current_density_a_per_mm2 = _resolve_current_density(candidate, notes)
    fill_factor = _resolve_fill_factor(candidate, notes)

    sat_margin = _safe_ratio(b_allow_t, b_peak_t)
    loss_margin = _safe_ratio(p_loss_allow_w, total_loss_w)
    current_density_margin = _safe_ratio(allow_profile.j_allow_a_per_mm2, current_density_a_per_mm2)
    fill_margin = _safe_ratio(allow_profile.fill_allow, fill_factor)

    return MagneticCandidateEngineeringMetrics(
        candidate_id=candidate.candidate_id,
        b_peak_t=b_peak_t,
        b_allow_t=b_allow_t,
        total_loss_w=total_loss_w,
        p_loss_allow_w=p_loss_allow_w,
        current_density_a_per_mm2=current_density_a_per_mm2,
        j_allow_a_per_mm2=allow_profile.j_allow_a_per_mm2,
        fill_factor=fill_factor,
        k_fill_allow=allow_profile.fill_allow,
        volume_cm3=volume_cm3,
        throughput_power_w=throughput_power_w,
        sat_margin=sat_margin,
        loss_margin=loss_margin,
        current_density_margin=current_density_margin,
        fill_margin=fill_margin,
        notes=notes,
    )


def _resolve_b_peak(candidate: FixedInductorDesignCandidate, notes: list[str]) -> float | None:
    if candidate.b_peak_design_t is not None:
        return candidate.b_peak_design_t
    metadata_value = _as_float(candidate.metadata.get("b_peak_t"))
    if metadata_value is not None:
        notes.append("Used metadata B_peak fallback for engineering screening.")
    return metadata_value


def _resolve_b_sat_100c(candidate: FixedInductorDesignCandidate, notes: list[str]) -> float | None:
    metadata = candidate.metadata
    b_sat_100c_t = _as_float(metadata.get("b_sat_100c_t"))
    if b_sat_100c_t is not None:
        source = metadata.get("b_sat_100c_source")
        if source and source != "exact":
            notes.append(f"B_sat(100C) used fallback source '{source}'.")
        return b_sat_100c_t

    b_sat_t = _as_float(metadata.get("b_sat_t"))
    if b_sat_t is None:
        notes.append("B_sat(100C) is unavailable; saturation-margin screening was skipped.")
        return None

    # Conservative fallback when only nominal or room-temperature saturation is present.
    fallback = 0.80 * b_sat_t
    notes.append("B_sat(100C) was unavailable; used 0.80 x nominal B_sat as a conservative fallback.")
    return fallback


def _resolve_total_loss(candidate: FixedInductorDesignCandidate, notes: list[str]) -> float | None:
    if candidate.reference_total_loss_w is not None:
        return candidate.reference_total_loss_w
    if candidate.reference_copper_loss_w is not None or candidate.reference_core_loss_w is not None:
        notes.append("Reference total loss was reconstructed from copper/core loss fields.")
        return (candidate.reference_copper_loss_w or 0.0) + (candidate.reference_core_loss_w or 0.0)
    metadata_value = _as_float(candidate.metadata.get("reference_total_loss_w"))
    if metadata_value is not None:
        notes.append("Reference total loss used metadata fallback.")
        return metadata_value
    notes.append("Reference total loss is unavailable; loss-margin screening was skipped.")
    return None


def _resolve_volume_cm3(candidate: FixedInductorDesignCandidate, notes: list[str]) -> float | None:
    if candidate.total_volume_m3 is not None:
        return candidate.total_volume_m3 * 1e6
    if candidate.core_volume_m3 is not None or candidate.winding_volume_m3 is not None:
        notes.append("Total magnetic volume was reconstructed from core and winding volumes.")
        return ((candidate.core_volume_m3 or 0.0) + (candidate.winding_volume_m3 or 0.0)) * 1e6
    metadata_value = _as_float(candidate.metadata.get("gross_volume_m3"))
    if metadata_value is not None:
        notes.append("Used gross magnetic volume metadata fallback for loss-density screening.")
        return metadata_value * 1e6
    notes.append("Magnetic volume is unavailable; density-limited loss screening was skipped.")
    return None


def _resolve_current_density(candidate: FixedInductorDesignCandidate, notes: list[str]) -> float | None:
    metadata = candidate.metadata
    value = _as_float(metadata.get("reference_current_density_a_per_mm2"))
    if value is not None:
        return value

    bundle_area_m2 = _as_float(metadata.get("bundle_copper_area_m2"))
    parallel_bundles = max(candidate.parallel_bundles, 1)
    i_rms_a = _as_float(metadata.get("reference_i_rms_a"))
    if bundle_area_m2 is not None and i_rms_a is not None:
        notes.append("Reference current density was derived from wire area metadata.")
        return i_rms_a / (bundle_area_m2 * parallel_bundles * 1e6)

    notes.append("Current density is unavailable; current-density screening was skipped.")
    return None


def _resolve_fill_factor(candidate: FixedInductorDesignCandidate, notes: list[str]) -> float | None:
    if candidate.fill_factor is not None:
        return candidate.fill_factor
    value = _as_float(candidate.metadata.get("fill_factor"))
    if value is not None:
        notes.append("Fill factor used metadata fallback.")
        return value
    notes.append("Fill factor is unavailable; fill-factor screening was skipped.")
    return None


def _resolve_min_allow(first: float | None, second: float | None) -> float | None:
    available = [value for value in (first, second) if value is not None]
    if not available:
        return None
    return min(available)


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0.0:
        return None
    return numerator / denominator


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
