"""Fixed two-phase, 180-degree interleaving calculations."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose

PHASE_COUNT = 2
PHASE_SHIFT_DEG = 180.0


@dataclass(frozen=True)
class InterleavedRipple:
    """Per-phase and aggregate switching-ripple envelopes."""

    duty: list[float]
    phase_ripple_pp_a: list[float]
    cancellation_factor: list[float]
    aggregate_ripple_pp_a: list[float]

    def as_metadata(self) -> dict[str, list[float]]:
        return {
            "duty": list(self.duty),
            "phase_ripple_pp_a": list(self.phase_ripple_pp_a),
            "cancellation_factor": list(self.cancellation_factor),
            "aggregate_ripple_pp_a": list(self.aggregate_ripple_pp_a),
        }


def interleaved_cancellation_factor(
    duty: float,
    *,
    phase_shift_deg: float = PHASE_SHIFT_DEG,
) -> float:
    """Return the ideal two-phase ripple factor for a 180-degree shift.

    For identical triangular phase ripple, the aggregate peak-to-peak ripple
    is ``DeltaI_phase * abs(1 - 2D)``. The first-pass contract fixes the shift
    at 180 degrees, so other shifts are rejected instead of approximated.
    """

    if not isclose(phase_shift_deg, PHASE_SHIFT_DEG, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("The first-pass interleaving model requires a 180-degree phase shift.")
    if not 0.0 <= duty <= 1.0:
        raise ValueError("Boost duty must be in [0, 1].")
    return abs(1.0 - 2.0 * duty)


def calculate_interleaved_ripple(
    *,
    duty: list[float],
    phase_ripple_pp_a: list[float],
    phase_shift_deg: float = PHASE_SHIFT_DEG,
) -> InterleavedRipple:
    """Calculate aggregate switching ripple from equal phase envelopes."""

    if len(duty) != len(phase_ripple_pp_a):
        raise ValueError("Duty and phase-ripple arrays must have the same length.")
    if not duty:
        raise ValueError("Duty and phase-ripple arrays cannot be empty.")
    if any(value < 0.0 for value in phase_ripple_pp_a):
        raise ValueError("Phase ripple values cannot be negative.")

    factors = [
        interleaved_cancellation_factor(value, phase_shift_deg=phase_shift_deg)
        for value in duty
    ]
    aggregate = [ripple * factor for ripple, factor in zip(phase_ripple_pp_a, factors, strict=True)]
    return InterleavedRipple(
        duty=[float(value) for value in duty],
        phase_ripple_pp_a=[float(value) for value in phase_ripple_pp_a],
        cancellation_factor=factors,
        aggregate_ripple_pp_a=aggregate,
    )
