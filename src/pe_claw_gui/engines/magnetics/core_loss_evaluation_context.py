"""Build Step 7 model-specific context without changing excitation semantics."""

from __future__ import annotations

import cmath
import math

from ...models.magnetic_loss_contract import (
    CoreLossEvaluationContext,
    CoreLossExcitation,
)


FUNDAMENTAL_EXTRACTION_METHOD = (
    "closed_uniform_period_dft_excluding_duplicate_endpoint"
)


def extract_fundamental_flux_amplitude_t(
    excitation: CoreLossExcitation,
) -> float:
    """Return the first-harmonic peak amplitude from one closed uniform period."""

    if not isinstance(excitation, CoreLossExcitation):
        raise TypeError("excitation must be CoreLossExcitation.")
    times = excitation.flux_waveform_time_s
    flux = excitation.flux_waveform_t
    if len(times) < 3:
        raise ValueError("At least two intervals plus the duplicate endpoint are required.")
    closure_tolerance = max(1e-12, excitation.flux_peak_to_peak_t * 1e-9)
    if abs(flux[0] - flux[-1]) > closure_tolerance:
        raise ValueError("Flux waveform must close before fundamental extraction.")
    intervals = [right - left for left, right in zip(times, times[1:])]
    reference_interval = intervals[0]
    interval_tolerance = max(1e-15, abs(reference_interval) * 1e-9)
    if any(abs(value - reference_interval) > interval_tolerance for value in intervals[1:]):
        raise ValueError("Flux waveform must use uniform sampling for DFT extraction.")
    period = times[-1] - times[0]
    expected_period = 1.0 / excitation.frequency_hz
    if not math.isclose(period, expected_period, rel_tol=1e-9, abs_tol=1e-15):
        raise ValueError("Flux waveform period conflicts with excitation frequency.")

    samples = flux[:-1]
    count = len(samples)
    dc = sum(samples) / count
    coefficient = sum(
        (value - dc) * cmath.exp(-2j * math.pi * index / count)
        for index, value in enumerate(samples)
    ) / count
    amplitude = 2.0 * abs(coefficient)
    if not math.isfinite(amplitude) or amplitude < 0.0:
        raise ValueError("Fundamental extraction produced an invalid amplitude.")
    return amplitude


def build_core_loss_evaluation_context(
    excitation: CoreLossExcitation,
    *,
    eddy_current_path_area_m2: float | None = None,
    source_fields: tuple[str, ...] = (),
) -> CoreLossEvaluationContext:
    """Build audited optional inputs for Magnetics and Roshen model paths."""

    return CoreLossEvaluationContext(
        fundamental_flux_amplitude_t=extract_fundamental_flux_amplitude_t(excitation),
        fundamental_extraction_method=FUNDAMENTAL_EXTRACTION_METHOD,
        eddy_current_path_area_m2=eddy_current_path_area_m2,
        source_fields=source_fields,
    )


__all__ = [
    "FUNDAMENTAL_EXTRACTION_METHOD",
    "build_core_loss_evaluation_context",
    "extract_fundamental_flux_amplitude_t",
]
