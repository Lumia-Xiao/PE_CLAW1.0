from __future__ import annotations

import math

import pytest

from pe_claw_gui.engines.magnetics.core_loss_kernel import (
    calculate_igse_loss,
    calculate_steinmetz_loss,
    select_steinmetz_model,
)
from pe_claw_gui.models.magnetic_loss_contract import CoreLossExcitation, CoreLossValidityStatus


MODEL = {
    "model_id": "fixture-n87",
    "scope": "default",
    "minimumFrequency": 10_000.0,
    "maximumFrequency": 500_000.0,
    "k": 0.002,
    "alpha": 1.4,
    "beta": 2.3,
    "input_flux_definition": "ac_peak_t",
}


def _excitation(values: tuple[float, ...], frequency_hz: float = 100_000.0) -> CoreLossExcitation:
    period = 1.0 / frequency_hz
    times = tuple(index * period / (len(values) - 1) for index in range(len(values)))
    mean = sum(values) / len(values)
    return CoreLossExcitation(
        frequency_hz=frequency_hz,
        temperature_c=25.0,
        flux_waveform_time_s=times,
        flux_waveform_t=values,
        flux_ac_peak_t=max(abs(value - mean) for value in values),
        flux_peak_to_peak_t=max(values) - min(values),
        flux_dc_offset_t=mean,
        flux_absolute_peak_t=max(abs(value) for value in values),
        effective_volume_m3=1.0e-5,
        core_mass_kg=0.05,
        magnetizing_inductance_h=None,
        magnetizing_current_rms_a=None,
        waveform_definition="periodic_piecewise_linear",
        source_topology="fixture",
        source_role="core",
    )


def test_steinmetz_uses_si_density_and_single_volume_multiplication() -> None:
    result = calculate_steinmetz_loss(
        model=MODEL,
        frequency_hz=100_000.0,
        flux_ac_peak_t=0.1,
        effective_volume_m3=1.0e-5,
    )
    expected_density = MODEL["k"] * 100_000.0 ** MODEL["alpha"] * 0.1 ** MODEL["beta"]
    assert result.validity_status is CoreLossValidityStatus.VALID
    assert result.volumetric_loss_w_per_m3 == pytest.approx(expected_density)
    assert result.core_loss_w == pytest.approx(expected_density * 1.0e-5)
    assert result.unit_conversion_policy == "W_per_m3_times_m3_equals_W_once"


def test_range_selection_is_deterministic_and_marks_extrapolation() -> None:
    selected = select_steinmetz_model((MODEL,), frequency_hz=1_000_000.0)
    assert selected.model_id == "fixture-n87"
    assert selected.status == "outside_frequency_range"
    assert selected.extrapolated is True


def test_temperature_coefficients_are_applied_as_declared_quadratic() -> None:
    model = {**MODEL, "ct0": 1.2, "ct1": 0.01, "ct2": 0.001}
    result = calculate_steinmetz_loss(model=model, frequency_hz=100_000.0, flux_ac_peak_t=0.1, temperature_c=10.0)
    base = MODEL["k"] * 100_000.0 ** MODEL["alpha"] * 0.1 ** MODEL["beta"]
    assert result.volumetric_loss_w_per_m3 == pytest.approx(base * 1.2)
    assert result.temperature_correction_factor == pytest.approx(1.2)
    assert result.temperature_correction_source == "pinned_mkf_ct2_T2_minus_ct1_T_plus_ct0_degC"


def test_igse_returns_nonzero_for_closed_triangle_and_preserves_dc_offset() -> None:
    excitation = _excitation((0.05, 0.15, 0.05, -0.05, 0.05))
    result = calculate_igse_loss(model=MODEL, excitation=excitation)
    assert result.validity_status is CoreLossValidityStatus.VALID
    assert result.method_used == "igse"
    assert result.volumetric_loss_w_per_m3 is not None and result.volumetric_loss_w_per_m3 > 0.0
    assert result.flux_dc_offset_t == pytest.approx(0.05)


def test_igse_preserves_declared_frequency_range_status() -> None:
    excitation = _excitation((0.0, 0.1, 0.0, -0.1, 0.0), frequency_hz=1_000_000.0)
    result = calculate_igse_loss(model=MODEL, excitation=excitation)
    assert result.validity_status is CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE
    assert result.extrapolated is True
    assert result.core_loss_w is not None
    assert "outside the declared range" in " ".join(result.validity_messages)


def test_sinusoidal_igse_matches_declared_steinmetz_curve() -> None:
    frequency_hz = 100_000.0
    peak_t = 0.1
    sample_count = 1001
    period = 1.0 / frequency_hz
    times = tuple(index * period / (sample_count - 1) for index in range(sample_count))
    values = tuple(peak_t * math.sin(2.0 * math.pi * frequency_hz * value) for value in times)
    excitation = CoreLossExcitation(
        frequency_hz=frequency_hz,
        temperature_c=25.0,
        flux_waveform_time_s=times,
        flux_waveform_t=values,
        flux_ac_peak_t=peak_t,
        flux_peak_to_peak_t=2.0 * peak_t,
        flux_dc_offset_t=0.0,
        flux_absolute_peak_t=peak_t,
        effective_volume_m3=1.0e-5,
        core_mass_kg=None,
        magnetizing_inductance_h=None,
        magnetizing_current_rms_a=None,
        waveform_definition="sinusoidal_zero_mean",
        source_topology="fixture",
        source_role="core",
    )
    steinmetz = calculate_steinmetz_loss(
        model=MODEL,
        frequency_hz=frequency_hz,
        flux_ac_peak_t=peak_t,
        effective_volume_m3=1.0e-5,
    )
    igse = calculate_igse_loss(model=MODEL, excitation=excitation)
    assert igse.volumetric_loss_w_per_m3 == pytest.approx(
        steinmetz.volumetric_loss_w_per_m3,
        rel=5e-4,
    )


def test_density_can_be_valid_without_volume_but_total_watts_remain_none() -> None:
    result = calculate_steinmetz_loss(
        model=MODEL,
        frequency_hz=100_000.0,
        flux_ac_peak_t=0.1,
    )
    assert result.validity_status is CoreLossValidityStatus.VALID
    assert result.volumetric_loss_w_per_m3 is not None
    assert result.core_loss_w is None


def test_peak_to_peak_model_does_not_silently_reuse_ac_peak() -> None:
    model = {**MODEL, "input_flux_definition": "peak_to_peak_t"}
    missing = calculate_steinmetz_loss(
        model=model,
        frequency_hz=100_000.0,
        flux_ac_peak_t=0.1,
    )
    valid = calculate_steinmetz_loss(
        model=model,
        frequency_hz=100_000.0,
        flux_ac_peak_t=0.1,
        flux_peak_to_peak_t=0.2,
    )
    assert missing.validity_status is CoreLossValidityStatus.INVALID_EXCITATION
    assert valid.volumetric_loss_w_per_m3 == pytest.approx(
        MODEL["k"] * 100_000.0 ** MODEL["alpha"] * 0.2 ** MODEL["beta"]
    )


def test_non_steinmetz_model_is_not_claimed_as_zero_loss() -> None:
    result = calculate_steinmetz_loss(
        model={"method": "poco", "a": 1.0},
        frequency_hz=100_000.0,
        flux_ac_peak_t=0.1,
    )
    assert result.validity_status is CoreLossValidityStatus.MODEL_NOT_SUPPORTED
    assert result.core_loss_w is None
    assert result.volumetric_loss_w_per_m3 is None


@pytest.mark.parametrize("frequency_hz", [0.0, -1.0, math.nan, math.inf])
def test_invalid_frequency_returns_structured_unavailable_loss(frequency_hz: float) -> None:
    result = calculate_steinmetz_loss(
        model=MODEL,
        frequency_hz=frequency_hz,
        flux_ac_peak_t=0.1,
    )
    assert result.validity_status is CoreLossValidityStatus.INVALID_EXCITATION
    assert result.core_loss_w is None
    assert result.volumetric_loss_w_per_m3 is None


def test_nonperiodic_waveform_is_rejected() -> None:
    excitation = _excitation((0.0, 0.1, 0.0, -0.1, 0.02))
    result = calculate_igse_loss(model=MODEL, excitation=excitation)
    assert result.validity_status is CoreLossValidityStatus.INVALID_EXCITATION
    assert result.core_loss_w is None
