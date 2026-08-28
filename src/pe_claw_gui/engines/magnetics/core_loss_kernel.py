"""Unit-safe Steinmetz and iGSE magnetic core-loss calculations.

The kernel deliberately accepts both normalized-v2 models and legacy range
dictionaries.  Callers receive one explicit SI result instead of duplicating
frequency selection, temperature handling, and volume conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import gamma, isfinite, pi
from typing import Any, Iterable, Mapping

from ...models.magnetic_loss_contract import (
    CoreLossExcitation,
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
)


_SCALAR_TRIANGULAR_MODEL_VERSION = "llc_scalar_triangular_igse_v1"
_SCALAR_TRIANGULAR_WAVEFORMS = frozenset({
    "scalar_bipolar_triangular_flux_template",
    "scalar_dc_biased_triangular_flux_template",
    "scalar_piecewise_linear_current_flux_template",
})


@dataclass(frozen=True)
class MaterialLossModelSelection:
    """Auditable result of deterministic Steinmetz-range selection."""

    model: Any | None
    model_id: str | None
    scope: str | None
    status: str
    extrapolated: bool
    frequency_range_hz: tuple[float, float] | None
    messages: tuple[str, ...] = ()


def select_steinmetz_model(
    models: Iterable[Any],
    *,
    frequency_hz: float,
    flux_ac_peak_t: float | None = None,
    temperature_c: float | None = None,
) -> MaterialLossModelSelection:
    """Select a range without silently hiding out-of-range extrapolation."""

    _finite_positive(frequency_hz, "frequency_hz")
    candidates = [_coerce_model(item, index) for index, item in enumerate(models)]
    candidates = [item for item in candidates if item is not None and item.method.casefold() == "steinmetz"]
    if not candidates:
        return MaterialLossModelSelection(None, None, None, "model_not_supported", False, None, ("No Steinmetz model is available.",))

    def key(item: MaterialLossModel) -> tuple[float, float, str, str]:
        bounds = item.valid_frequency_range_hz or (0.0, float("inf"))
        return (bounds[0], bounds[1], item.scope, item.model_id)

    ordered = sorted(candidates, key=key)
    in_range = [item for item in ordered if _in_range(frequency_hz, item.valid_frequency_range_hz)]
    selected = in_range[0] if in_range else min(
        ordered,
        key=lambda item: (_distance_to_range(frequency_hz, item.valid_frequency_range_hz), key(item)),
    )
    selected_range = selected.valid_frequency_range_hz
    extrapolated = not bool(in_range)
    status = "valid" if in_range else "outside_frequency_range"
    messages = () if in_range else ("Frequency is outside the declared range; nearest range is reported as extrapolated.",)
    if flux_ac_peak_t is not None and selected.valid_flux_density_range_t is not None and not _in_range(flux_ac_peak_t, selected.valid_flux_density_range_t):
        status = "outside_flux_range"
        messages += ("Flux amplitude is outside the declared model range.",)
    if temperature_c is not None and selected.valid_temperature_range_c is not None and not _in_range(temperature_c, selected.valid_temperature_range_c):
        status = "outside_temperature_range"
        messages += ("Temperature is outside the declared model range.",)
    return MaterialLossModelSelection(
        selected,
        selected.model_id,
        selected.scope,
        status,
        extrapolated,
        selected_range,
        messages,
    )


def calculate_steinmetz_loss(
    *,
    model: Any,
    frequency_hz: float,
    flux_ac_peak_t: float | None = None,
    flux_peak_to_peak_t: float | None = None,
    temperature_c: float = 25.0,
    effective_volume_m3: float | None = None,
    core_mass_kg: float | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Calculate Steinmetz loss with SI inputs and explicit output basis."""

    selected = _coerce_model(model, 0)
    if selected is None or selected.method.casefold() != "steinmetz":
        return _invalid_result(
            status=CoreLossValidityStatus.MODEL_NOT_SUPPORTED,
            model=model,
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            flux_ac_peak_t=flux_ac_peak_t or 0.0,
            material_id=material_id,
            material_name=material_name,
            source_provenance=source_provenance,
            calculation_mode=calculation_mode,
            message="The supplied model is not a Steinmetz model.",
        )
    try:
        _finite_positive(frequency_hz, "frequency_hz")
        _finite(temperature_c, "temperature_c")
        if flux_ac_peak_t is None:
            if flux_peak_to_peak_t is None:
                raise ValueError("flux_ac_peak_t or flux_peak_to_peak_t is required.")
            _finite_nonnegative(flux_peak_to_peak_t, "flux_peak_to_peak_t")
            flux_ac_peak_t = flux_peak_to_peak_t / 2.0
        _finite_nonnegative(flux_ac_peak_t, "flux_ac_peak_t")
        if flux_peak_to_peak_t is not None:
            _finite_nonnegative(flux_peak_to_peak_t, "flux_peak_to_peak_t")
        selection = select_steinmetz_model((selected,), frequency_hz=frequency_hz, flux_ac_peak_t=flux_ac_peak_t, temperature_c=temperature_c)
        if selection.model is None:
            raise ValueError("No usable Steinmetz model.")
        coefficients = selection.model.coefficients
        output_basis = getattr(selection.model, "output_basis", "volumetric_w_per_m3")
        if output_basis != "volumetric_w_per_m3":
            raise ValueError(f"Steinmetz output basis {output_basis!r} is not supported by the SI volumetric kernel.")
        k = _required_coefficient(coefficients, "k")
        alpha = _required_coefficient(coefficients, "alpha")
        beta = _required_coefficient(coefficients, "beta")
        if k < 0.0 or alpha < 0.0 or beta < 0.0:
            raise ValueError("Steinmetz k, alpha, and beta must be nonnegative.")
        temperature_factor, temperature_source = _temperature_factor(coefficients, temperature_c)
        model_flux_t = _model_flux_input_t(
            selected.input_flux_definition,
            flux_ac_peak_t=flux_ac_peak_t,
            flux_peak_to_peak_t=flux_peak_to_peak_t,
        )
        density = k * temperature_factor * (frequency_hz ** alpha) * (model_flux_t ** beta)
        if not isfinite(density) or density < 0.0:
            raise ValueError("Steinmetz result is not finite and nonnegative.")
        total = density * effective_volume_m3 if effective_volume_m3 is not None else None
        mass_loss = density / (effective_volume_m3 / core_mass_kg) if effective_volume_m3 and core_mass_kg else None
        status = {
            "valid": CoreLossValidityStatus.VALID,
            "outside_frequency_range": CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE,
            "outside_flux_range": CoreLossValidityStatus.OUTSIDE_FLUX_RANGE,
            "outside_temperature_range": CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE,
        }.get(selection.status, CoreLossValidityStatus.INVALID_MATERIAL_RECORD)
        messages = selection.messages + (("Temperature correction uses pinned MKF ct2*T^2 - ct1*T + ct0.",) if all(name in coefficients for name in ("ct0", "ct1", "ct2")) else ())
        return CoreLossResult(
            core_loss_w=total,
            volumetric_loss_w_per_m3=density,
            mass_loss_w_per_kg=mass_loss,
            method_used="steinmetz",
            model_policy="steinmetz_si_v1",
            material_id=material_id,
            material_name=material_name,
            temperature_c=temperature_c,
            frequency_hz=frequency_hz,
            flux_ac_peak_t=flux_ac_peak_t,
            flux_dc_offset_t=0.0,
            validity_status=status,
            validity_messages=messages or ("Steinmetz SI calculation completed.",),
            interpolated=False,
            fitted=False,
            extrapolated=selection.extrapolated,
            proxy_used=False,
            source_provenance=source_provenance or _default_provenance(),
            selected_model_id=selection.model_id,
            selected_model_scope=selection.scope,
            input_flux_definition=selected.input_flux_definition,
            effective_volume_m3=effective_volume_m3,
            core_mass_kg=core_mass_kg,
            temperature_correction_factor=temperature_factor,
            temperature_correction_source=temperature_source,
            calculation_mode=calculation_mode,
            unit_conversion_policy="W_per_m3_times_m3_equals_W_once",
        )
    except (TypeError, ValueError) as exc:
        return _invalid_result(
            status=CoreLossValidityStatus.INVALID_EXCITATION,
            model=selected,
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            flux_ac_peak_t=flux_ac_peak_t or 0.0,
            material_id=material_id,
            material_name=material_name,
            source_provenance=source_provenance,
            calculation_mode=calculation_mode,
            message=str(exc),
        )


def _calculate_igse_loss_unchecked(
    *,
    model: Any,
    excitation: CoreLossExcitation,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Calculate iGSE loss from one closed periodic flux waveform."""

    selected = _coerce_model(model, 0)
    if selected is None or selected.method.casefold() != "steinmetz":
        return _invalid_result(status=CoreLossValidityStatus.MODEL_NOT_SUPPORTED, model=selected, frequency_hz=excitation.frequency_hz, temperature_c=excitation.temperature_c, flux_ac_peak_t=excitation.flux_ac_peak_t, material_id=material_id, material_name=material_name, source_provenance=source_provenance, calculation_mode=calculation_mode, message="The supplied model is not a Steinmetz model.")
    b = excitation.flux_waveform_t
    if abs(b[0] - b[-1]) > max(1e-9, excitation.flux_peak_to_peak_t * 1e-6):
        return _invalid_result(status=CoreLossValidityStatus.INVALID_EXCITATION, model=selected, frequency_hz=excitation.frequency_hz, temperature_c=excitation.temperature_c, flux_ac_peak_t=excitation.flux_ac_peak_t, material_id=material_id, material_name=material_name, source_provenance=source_provenance, calculation_mode=calculation_mode, message="Flux waveform is not periodic.")
    coefficients = selected.coefficients
    alpha = _required_coefficient(coefficients, "alpha")
    beta = _required_coefficient(coefficients, "beta")
    k = _required_coefficient(coefficients, "k")
    temperature_factor, temperature_source = _temperature_factor(coefficients, excitation.temperature_c)
    selection = select_steinmetz_model(
        (selected,),
        frequency_hz=excitation.frequency_hz,
        flux_ac_peak_t=excitation.flux_ac_peak_t,
        temperature_c=excitation.temperature_c,
    )
    period = excitation.flux_waveform_time_s[-1] - excitation.flux_waveform_time_s[0]
    i_cos = 2.0 * ((pi ** 0.5) * gamma((alpha + 1.0) / 2.0) / gamma((alpha + 2.0) / 2.0))
    ki = k * (2.0 * pi) ** (1.0 - alpha) * 2.0 ** (alpha - beta) / i_cos
    optimized = _scalar_triangular_density(
        model=selected,
        excitation=excitation,
        material_id=material_id,
        alpha=alpha,
        beta=beta,
        k=k,
        temperature_factor=temperature_factor,
        ki=ki,
        period=period,
    )
    if optimized is None:
        integral = 0.0
        for left_t, right_t, left_b, right_b in zip(excitation.flux_waveform_time_s, excitation.flux_waveform_time_s[1:], b, b[1:]):
            dt = right_t - left_t
            slope = abs((right_b - left_b) / dt)
            if slope:
                integral += (slope ** alpha) * (excitation.flux_peak_to_peak_t ** max(beta - alpha, 0.0)) * dt
        density = ki * temperature_factor * integral / period
        calculation_detail = "iGSE calculated from closed periodic flux waveform."
    else:
        density = optimized
        calculation_detail = "iGSE analytical triangular path used for a scalar piecewise-linear excitation."
    total = density * excitation.effective_volume_m3 if excitation.effective_volume_m3 is not None else None
    mass_loss = density / (excitation.effective_volume_m3 / excitation.core_mass_kg) if excitation.effective_volume_m3 and excitation.core_mass_kg else None
    status = {
        "valid": CoreLossValidityStatus.VALID,
        "outside_frequency_range": CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE,
        "outside_flux_range": CoreLossValidityStatus.OUTSIDE_FLUX_RANGE,
        "outside_temperature_range": CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE,
    }.get(selection.status, CoreLossValidityStatus.INVALID_MATERIAL_RECORD)
    return CoreLossResult(
        core_loss_w=total,
        volumetric_loss_w_per_m3=density,
        mass_loss_w_per_kg=mass_loss,
        method_used="igse",
        model_policy="steinmetz_igse_v1",
        material_id=material_id,
        material_name=material_name,
        temperature_c=excitation.temperature_c,
        frequency_hz=excitation.frequency_hz,
        flux_ac_peak_t=excitation.flux_ac_peak_t,
        flux_dc_offset_t=excitation.flux_dc_offset_t,
        validity_status=status,
        validity_messages=selection.messages + (calculation_detail,),
        interpolated=False,
        fitted=False,
        extrapolated=selection.extrapolated,
        proxy_used=False,
        source_provenance=source_provenance or _default_provenance(),
        selected_model_id=selected.model_id,
        selected_model_scope=selected.scope,
        input_flux_definition=selected.input_flux_definition,
        effective_volume_m3=excitation.effective_volume_m3,
        core_mass_kg=excitation.core_mass_kg,
        temperature_correction_factor=temperature_factor,
        temperature_correction_source=temperature_source,
        calculation_mode=calculation_mode,
        unit_conversion_policy="W_per_m3_times_m3_equals_W_once",
        model_evaluation_details={
            "igse_path": "scalar_triangular_analytic" if optimized is not None else "waveform_piecewise_linear",
            "model_version": _SCALAR_TRIANGULAR_MODEL_VERSION if optimized is not None else "igse_waveform_v1",
            "waveform_definition": excitation.waveform_definition,
        },
    )


def _scalar_triangular_density(
    *,
    model: MaterialLossModel,
    excitation: CoreLossExcitation,
    material_id: str,
    alpha: float,
    beta: float,
    k: float,
    temperature_factor: float,
    ki: float,
    period: float,
) -> float | None:
    """Return exact iGSE density for the known scalar triangle templates.

    The path is deliberately gated by the builder's explicit waveform label
    and its five exact breakpoints.  Arbitrary waveforms continue through the
    existing point-by-point integration below.
    """

    if excitation.waveform_definition not in _SCALAR_TRIANGULAR_WAVEFORMS:
        return None
    times = excitation.flux_waveform_time_s
    values = excitation.flux_waveform_t
    if len(times) != 5 or len(values) != 5:
        return None
    normalized_times = tuple((value - times[0]) / period for value in times)
    if any(abs(actual - expected) > 1.0e-12 for actual, expected in zip(normalized_times, (0.0, 0.25, 0.5, 0.75, 1.0))):
        return None
    if abs(values[0] - values[-1]) > max(1.0e-9, excitation.flux_peak_to_peak_t * 1.0e-6):
        return None
    peak_to_peak = excitation.flux_peak_to_peak_t
    if peak_to_peak <= 0.0:
        return 0.0
    dc_offset = excitation.flux_dc_offset_t
    expected_values = (
        dc_offset,
        dc_offset + peak_to_peak / 2.0,
        dc_offset,
        dc_offset - peak_to_peak / 2.0,
        dc_offset,
    )
    tolerance = max(1.0e-12, peak_to_peak * 1.0e-9)
    if any(abs(actual - expected) > tolerance for actual, expected in zip(values, expected_values)):
        return None
    return _cached_scalar_triangular_density(
        _SCALAR_TRIANGULAR_MODEL_VERSION,
        material_id,
        model.model_id,
        excitation.waveform_definition,
        excitation.frequency_hz,
        peak_to_peak,
        excitation.temperature_c,
        k,
        alpha,
        beta,
        temperature_factor,
        ki,
        tuple(
            (name, float(model.coefficients[name]))
            for name in ("k", "alpha", "beta", "ct0", "ct1", "ct2")
            if name in model.coefficients
        ),
    )


@lru_cache(maxsize=4096)
def _cached_scalar_triangular_density(
    model_version: str,
    material_id: str,
    model_id: str,
    waveform_shape: str,
    frequency_hz: float,
    flux_peak_to_peak_t: float,
    temperature_c: float,
    k: float,
    alpha: float,
    beta: float,
    temperature_factor: float,
    ki: float,
    model_coefficients: tuple[tuple[str, float], ...],
) -> float:
    """Cache only the reusable density; volume and mass stay candidate-local."""

    del model_version, material_id, model_id, waveform_shape, temperature_c, model_coefficients
    # For a triangle, |dB/dt| is 2*f*Bpp on each half-cycle.  This is the
    # exact integral used by _calculate_igse_loss_unchecked, including its
    # historical max(beta - alpha, 0) convention.
    slope = 2.0 * frequency_hz * flux_peak_to_peak_t
    integral_per_period = slope**alpha * flux_peak_to_peak_t ** max(beta - alpha, 0.0)
    density = ki * temperature_factor * integral_per_period
    if not isfinite(density) or density < 0.0:
        raise ValueError("Analytical triangular iGSE result is not finite and nonnegative.")
    return density


def clear_scalar_triangular_loss_cache() -> None:
    """Clear the process-local scalar triangular loss cache."""

    _cached_scalar_triangular_density.cache_clear()


def scalar_triangular_loss_cache_info():
    """Return cache hit/miss statistics for performance evidence and tests."""

    return _cached_scalar_triangular_density.cache_info()


def calculate_igse_loss(
    *,
    model: Any,
    excitation: CoreLossExcitation,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Calculate iGSE loss and convert malformed input into a validity result."""

    try:
        return _calculate_igse_loss_unchecked(
            model=model,
            excitation=excitation,
            material_id=material_id,
            material_name=material_name,
            source_provenance=source_provenance,
            calculation_mode=calculation_mode,
        )
    except (ArithmeticError, TypeError, ValueError) as exc:
        return _invalid_result(
            status=CoreLossValidityStatus.INVALID_MATERIAL_RECORD,
            model=model,
            frequency_hz=excitation.frequency_hz,
            temperature_c=excitation.temperature_c,
            flux_ac_peak_t=excitation.flux_ac_peak_t,
            material_id=material_id,
            material_name=material_name,
            source_provenance=source_provenance,
            calculation_mode=calculation_mode,
            message=str(exc),
        )


def calculate_core_loss(*, material: NormalizedMagneticMaterialV2, excitation: CoreLossExcitation, policy: str = "steinmetz_igse_v1") -> CoreLossResult:
    """Choose iGSE for a real waveform and Steinmetz for scalar use."""

    selection = select_steinmetz_model(material.loss_models, frequency_hz=excitation.frequency_hz, flux_ac_peak_t=excitation.flux_ac_peak_t, temperature_c=excitation.temperature_c)
    if selection.model is None:
        return _invalid_result(status=CoreLossValidityStatus.MODEL_NOT_SUPPORTED, model=None, frequency_hz=excitation.frequency_hz, temperature_c=excitation.temperature_c, flux_ac_peak_t=excitation.flux_ac_peak_t, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode="production", message="Material has no supported Steinmetz model.")
    if policy == "steinmetz_igse_v1" and len(excitation.flux_waveform_t) >= 3:
        return calculate_igse_loss(model=selection.model, excitation=excitation, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode="production")
    return calculate_steinmetz_loss(model=selection.model, frequency_hz=excitation.frequency_hz, flux_ac_peak_t=excitation.flux_ac_peak_t, temperature_c=excitation.temperature_c, effective_volume_m3=excitation.effective_volume_m3, core_mass_kg=excitation.core_mass_kg, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode="production")


def steinmetz_loss_density_w_per_m3(*, model: Any, frequency_hz: float, flux_ac_peak_t: float, temperature_c: float = 25.0) -> float:
    """Small scalar adapter for vectorized legacy search paths."""

    result = calculate_steinmetz_loss(model=model, frequency_hz=frequency_hz, flux_ac_peak_t=flux_ac_peak_t, temperature_c=temperature_c)
    if result.volumetric_loss_w_per_m3 is None:
        raise ValueError("Steinmetz density is unavailable: " + "; ".join(result.validity_messages))
    return result.volumetric_loss_w_per_m3


def select_steinmetz_coefficients(ranges: Iterable[Any], frequency_hz: float) -> dict[str, Any]:
    """Compatibility adapter exposing centrally selected coefficients."""

    selection = select_steinmetz_model(ranges, frequency_hz=frequency_hz)
    if selection.model is None:
        raise ValueError("No Steinmetz range is available.")
    coefficients = dict(selection.model.coefficients)
    bounds = selection.frequency_range_hz
    if bounds is not None:
        coefficients.setdefault("minimumFrequency", bounds[0])
        coefficients.setdefault("maximumFrequency", bounds[1])
    coefficients["model_id"] = selection.model_id
    coefficients["scope"] = selection.scope
    coefficients["input_flux_definition"] = selection.model.input_flux_definition
    coefficients["selection_status"] = selection.status
    coefficients["extrapolated"] = selection.extrapolated
    return coefficients


def _coerce_model(model: Any, index: int) -> MaterialLossModel | None:
    if isinstance(model, (MaterialLossModel, _SyntheticModel)):
        return model
    if not isinstance(model, Mapping):
        return None
    method = str(model.get("method", "steinmetz"))
    bounds = model.get("valid_frequency_range_hz") or (
        model.get("minimumFrequency", model.get("frequency_min_hz")),
        model.get("maximumFrequency", model.get("frequency_max_hz")),
    )
    frequency_range = tuple(float(value) for value in bounds) if bounds and all(value is not None for value in bounds) else None
    coefficients = dict(model.get("coefficients") or {})
    for name in ("k", "alpha", "beta", "ct0", "ct1", "ct2"):
        if name in model:
            coefficients[name] = float(model[name])
    if not coefficients and any(name in model for name in ("steinmetz_k", "steinmetz_alpha", "steinmetz_beta")):
        coefficients = {"k": float(model["steinmetz_k"]), "alpha": float(model["steinmetz_alpha"]), "beta": float(model["steinmetz_beta"])}
    return _SyntheticModel(
        model_id=str(model.get("model_id") or model.get("id") or f"legacy-steinmetz-{index}"),
        method=method,
        scope=str(model.get("scope") or "default"),
        coefficients=coefficients,
        input_flux_definition=str(model.get("input_flux_definition") or "ac_peak_t"),
        output_basis=str(model.get("output_basis") or "volumetric_w_per_m3"),
        valid_frequency_range_hz=frequency_range,
        valid_flux_density_range_t=None,
        valid_temperature_range_c=None,
    )


@dataclass(frozen=True)
class _SyntheticModel:
    model_id: str
    method: str
    scope: str
    coefficients: Mapping[str, float]
    input_flux_definition: str
    output_basis: str
    valid_frequency_range_hz: tuple[float, float] | None
    valid_flux_density_range_t: tuple[float, float] | None
    valid_temperature_range_c: tuple[float, float] | None


def _temperature_factor(coefficients: Mapping[str, float], temperature_c: float) -> tuple[float, str]:
    if not all(name in coefficients for name in ("ct0", "ct1", "ct2")):
        return 1.0, "no_temperature_coefficients"
    factor = float(coefficients["ct2"]) * temperature_c**2 - float(coefficients["ct1"]) * temperature_c + float(coefficients["ct0"])
    if not isfinite(factor):
        raise ValueError("temperature correction factor must be finite")
    if factor <= 0.0:
        return 1.0, "pinned_mkf_nonpositive_temperature_scale_ignored"
    return factor, "pinned_mkf_ct2_T2_minus_ct1_T_plus_ct0_degC"


def _model_flux_input_t(
    definition: str,
    *,
    flux_ac_peak_t: float,
    flux_peak_to_peak_t: float | None,
) -> float:
    normalized = definition.strip().casefold().replace("-", "_")
    if any(token in normalized for token in ("peak_to_peak", "bpp", "delta_b")):
        if flux_peak_to_peak_t is None:
            raise ValueError("The selected model requires an explicit peak-to-peak flux input.")
        return flux_peak_to_peak_t
    return flux_ac_peak_t


def _invalid_result(*, status: CoreLossValidityStatus, model: Any, frequency_hz: float, temperature_c: float, flux_ac_peak_t: float, material_id: str, material_name: str, source_provenance: SourceProvenance | None, calculation_mode: str, message: str) -> CoreLossResult:
    selected = _coerce_model(model, 0)
    safe_frequency_hz = float(frequency_hz) if _is_finite_number(frequency_hz) and float(frequency_hz) > 0.0 else 1e-12
    safe_temperature_c = float(temperature_c) if _is_finite_number(temperature_c) else 25.0
    safe_flux_ac_peak_t = float(flux_ac_peak_t) if _is_finite_number(flux_ac_peak_t) and float(flux_ac_peak_t) >= 0.0 else 0.0
    return CoreLossResult(
        core_loss_w=None,
        volumetric_loss_w_per_m3=None,
        mass_loss_w_per_kg=None,
        method_used=None,
        model_policy="steinmetz_igse_v1",
        material_id=material_id,
        material_name=material_name,
        temperature_c=safe_temperature_c,
        frequency_hz=safe_frequency_hz,
        flux_ac_peak_t=safe_flux_ac_peak_t,
        flux_dc_offset_t=0.0,
        validity_status=status,
        validity_messages=(message,),
        interpolated=False,
        fitted=False,
        extrapolated=False,
        proxy_used=False,
        source_provenance=source_provenance or _default_provenance(),
        selected_model_id=selected.model_id if selected else None,
        selected_model_scope=selected.scope if selected else None,
        calculation_mode=calculation_mode,
    )


def _default_provenance() -> SourceProvenance:
    return SourceProvenance(source_kind="runtime", source_project="PE-Claw", source_file="runtime/core_loss_kernel.py")


def _required_coefficient(coefficients: Mapping[str, float], name: str) -> float:
    if name not in coefficients:
        raise ValueError(f"Steinmetz coefficient {name!r} is missing.")
    value = float(coefficients[name])
    if not isfinite(value):
        raise ValueError(f"Steinmetz coefficient {name!r} is not finite.")
    return value


def _finite(value: float, name: str) -> None:
    if not isfinite(float(value)):
        raise ValueError(f"{name} must be finite.")


def _is_finite_number(value: object) -> bool:
    try:
        return isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _finite_positive(value: float, name: str) -> None:
    _finite(value, name)
    if float(value) <= 0.0:
        raise ValueError(f"{name} must be greater than zero.")


def _finite_nonnegative(value: float, name: str) -> None:
    _finite(value, name)
    if float(value) < 0.0:
        raise ValueError(f"{name} must be nonnegative.")


def _in_range(value: float, bounds: tuple[float, float] | None) -> bool:
    return bounds is None or bounds[0] <= value <= bounds[1]


def _distance_to_range(value: float, bounds: tuple[float, float] | None) -> float:
    if bounds is None:
        return 0.0
    return max(bounds[0] - value, 0.0, value - bounds[1])


__all__ = [
    "MaterialLossModelSelection",
    "calculate_core_loss",
    "calculate_igse_loss",
    "calculate_steinmetz_loss",
    "clear_scalar_triangular_loss_cache",
    "select_steinmetz_coefficients",
    "select_steinmetz_model",
    "scalar_triangular_loss_cache_info",
    "steinmetz_loss_density_w_per_m3",
]
