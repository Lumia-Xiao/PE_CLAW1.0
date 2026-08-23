"""First-order transformer leakage inductance estimators."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, pi

MU0_H_PER_M = 4.0 * pi * 1e-7

INTERLEAVING_FACTORS: dict[str, float] = {
    "P-S": 1.00,
    "P-S-P": 0.35,
    "S-P-S": 0.35,
}
DEFAULT_WINDING_ARRANGEMENT = "P-S-P"


@dataclass(frozen=True)
class LeakageEstimateResult:
    """Structured output for a primary-referred transformer leakage estimate."""

    estimated_lk_h: float
    estimated_lk_uH: float
    method: str
    winding_arrangement: str
    base_ps_lk_h: float
    interleaving_factor: float
    primary_turns: int
    mlt_m: float
    effective_winding_height_m: float
    primary_radial_build_m: float
    secondary_radial_build_m: float
    insulation_gap_m: float
    warning: str = ""


def estimate_layer_based_leakage_inductance(
    primary_turns: int,
    mean_length_per_turn_m: float,
    effective_winding_height_m: float,
    primary_radial_build_m: float,
    secondary_radial_build_m: float,
    insulation_gap_m: float,
    winding_arrangement: str = DEFAULT_WINDING_ARRANGEMENT,
) -> LeakageEstimateResult:
    """Estimate primary-referred leakage inductance from winding-layer geometry."""

    _validate_positive("primary_turns", float(primary_turns))
    _validate_positive("mean_length_per_turn_m", mean_length_per_turn_m)
    _validate_positive("effective_winding_height_m", effective_winding_height_m)
    _validate_non_negative("primary_radial_build_m", primary_radial_build_m)
    _validate_non_negative("secondary_radial_build_m", secondary_radial_build_m)
    _validate_non_negative("insulation_gap_m", insulation_gap_m)
    arrangement = _normalize_winding_arrangement(winding_arrangement)

    layer_term_m = primary_radial_build_m / 3.0 + insulation_gap_m + secondary_radial_build_m / 3.0
    base_ps_lk_h = (
        MU0_H_PER_M
        * float(primary_turns) ** 2
        * mean_length_per_turn_m
        / effective_winding_height_m
        * layer_term_m
    )
    factor = INTERLEAVING_FACTORS[arrangement]
    estimated_lk_h = factor * base_ps_lk_h
    return LeakageEstimateResult(
        estimated_lk_h=estimated_lk_h,
        estimated_lk_uH=estimated_lk_h * 1e6,
        method="layer_based_first_order",
        winding_arrangement=arrangement,
        base_ps_lk_h=base_ps_lk_h,
        interleaving_factor=factor,
        primary_turns=int(primary_turns),
        mlt_m=mean_length_per_turn_m,
        effective_winding_height_m=effective_winding_height_m,
        primary_radial_build_m=primary_radial_build_m,
        secondary_radial_build_m=secondary_radial_build_m,
        insulation_gap_m=insulation_gap_m,
    )


def estimate_legacy_leakage_inductance(lm_actual_h: float, leakage_fraction_estimate: float) -> float:
    """Compatibility wrapper for the legacy fraction-based leakage estimate."""

    if not isfinite(lm_actual_h) or lm_actual_h <= 0.0 or leakage_fraction_estimate < 0.0:
        raise ValueError("Lm and leakage fraction must be non-negative and physically valid.")
    return leakage_fraction_estimate * lm_actual_h


def _normalize_winding_arrangement(value: str) -> str:
    arrangement = str(value).strip().upper()
    if arrangement not in INTERLEAVING_FACTORS:
        supported = ", ".join(sorted(INTERLEAVING_FACTORS))
        raise ValueError(f"Unsupported winding arrangement '{value}'. Supported arrangements: {supported}.")
    return arrangement


def _validate_positive(name: str, value: float) -> None:
    if not isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be positive and finite.")


def _validate_non_negative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be non-negative and finite.")
