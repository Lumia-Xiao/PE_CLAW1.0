"""Operating-point contract for the two-phase interleaved Boost PFC."""

from __future__ import annotations

from math import isfinite

from ....models.operating_point import OperatingPoint
from ...base.candidate import TopologyCandidate


def validate_operating_point_contract(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint,
) -> None:
    """Validate the two-phase AC operating-point meanings and boundaries.

    ``vin_v`` is the RMS AC input voltage for this topology.  The generic
    operating-point model is intentionally not changed; this validation stays
    topology-local until the later waveform and loss stages consume the fields.
    """

    _require_finite_positive("Operating-point vin_v", operating_point.vin_v)
    vin_min = float(candidate.metadata.get("vac_rms_min_v", candidate.vin_nom))
    vin_max = float(candidate.metadata.get("vac_rms_max_v", candidate.vin_nom))
    if not vin_min <= float(operating_point.vin_v) <= vin_max:
        raise ValueError(
            "Two-phase Boost PFC operating-point vin_v must be within the "
            f"design RMS AC range [{vin_min:g}, {vin_max:g}] V."
        )

    _require_finite_nonnegative("Operating-point load_ratio", operating_point.load_ratio)

    if operating_point.vout_v is not None:
        _require_finite_positive("Operating-point vout_v", operating_point.vout_v)
    if operating_point.power_factor is not None:
        power_factor = float(operating_point.power_factor)
        if not isfinite(power_factor) or not 0.0 < power_factor <= 1.0:
            raise ValueError("Two-phase Boost PFC operating-point power_factor must be in (0, 1].")
    if operating_point.switching_frequency_hz is not None:
        _require_finite_positive(
            "Operating-point switching_frequency_hz",
            operating_point.switching_frequency_hz,
        )


def _require_finite_positive(label: str, value: float) -> None:
    numeric = float(value)
    if not isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{label} must be a finite positive value.")


def _require_finite_nonnegative(label: str, value: float) -> None:
    numeric = float(value)
    if not isfinite(numeric) or numeric < 0.0:
        raise ValueError(f"{label} must be a finite non-negative value.")
