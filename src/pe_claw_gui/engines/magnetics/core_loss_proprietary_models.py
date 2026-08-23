"""Shadow-only Magnetics and Micrometals core-loss evaluators.

The functions in this module consume normalized-v2 models and the shared
excitation contract.  They deliberately do not modify the production
Steinmetz/iGSE path; callers opt into these evaluators explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from ...models.magnetic_loss_contract import (
    CoreLossEvaluationContext,
    CoreLossExcitation,
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    SourceProvenance,
)
from .core_loss_evaluation_context import build_core_loss_evaluation_context


STEP7B_MODEL_POLICY = "mkf_compatible_v1_step7b_shadow"
MAGNETICS_FORMULA_ID = "mkf_magnetics_v1"
MICROMETALS_FORMULA_ID = "mkf_micrometals_v1"
POCO_FORMULA_ID = "mkf_poco_v1"
TDG_FORMULA_ID = "mkf_tdg_v1"


@dataclass(frozen=True)
class _ProprietaryModel:
    model_id: str
    method: str
    scope: str
    coefficients: Mapping[str, float]
    input_flux_definition: str
    output_basis: str
    valid_frequency_range_hz: tuple[float, float] | None
    valid_flux_density_range_t: tuple[float, float] | None
    valid_temperature_range_c: tuple[float, float] | None
    source_provenance: SourceProvenance | None
    source_reference: str | None


def calculate_magnetics_loss(
    *,
    model: MaterialLossModel | Mapping[str, Any],
    frequency_hz: float,
    flux_ac_peak_t: float,
    fundamental_flux_amplitude_t: float | None = None,
    evaluation_context: CoreLossEvaluationContext | None = None,
    temperature_c: float = 25.0,
    flux_dc_offset_t: float = 0.0,
    effective_volume_m3: float | None = None,
    core_mass_kg: float | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Evaluate the pinned Magnetics proprietary volumetric model.

    For ``b > 2`` the fundamental amplitude must come from the closed-period
    DFT helper (or an explicitly supplied, audited evaluation context).  A
    total AC peak is never silently substituted for the fundamental.
    """

    try:
        selected = _coerce_model(model)
        if selected.method.casefold() != "magnetics":
            return _unavailable(
                CoreLossValidityStatus.MODEL_NOT_SUPPORTED,
                selected,
                frequency_hz,
                temperature_c,
                flux_ac_peak_t,
                material_id,
                material_name,
                source_provenance,
                calculation_mode,
                "The supplied model is not a Magnetics model.",
            )
        frequency_hz = _finite_positive(frequency_hz, "frequency_hz")
        flux_ac_peak_t = _finite_nonnegative(flux_ac_peak_t, "flux_ac_peak_t")
        temperature_c = _finite(temperature_c, "temperature_c")
        effective_volume_m3 = _optional_positive(effective_volume_m3, "effective_volume_m3")
        core_mass_kg = _optional_positive(core_mass_kg, "core_mass_kg")
        a = _coefficient(selected, "a", nonnegative=False)
        b = _coefficient(selected, "b", nonnegative=False)
        c = _coefficient(selected, "c", nonnegative=False)
        range_status, range_message, extrapolated = _range_state(
            selected, frequency_hz, flux_ac_peak_t, temperature_c
        )
        details: dict[str, Any] = {
            "formula_id": MAGNETICS_FORMULA_ID,
            "input_frequency_hz": frequency_hz,
            "input_flux_ac_peak_t": flux_ac_peak_t,
            "coefficients": {"a": a, "b": b, "c": c},
            "branch": "b_gt_2" if b > 2.0 else "b_le_2",
            "source_reference": selected.source_reference,
        }
        if b > 2.0:
            context = evaluation_context
            if context is None and fundamental_flux_amplitude_t is not None:
                fundamental_flux_amplitude_t = _finite_nonnegative(
                    fundamental_flux_amplitude_t, "fundamental_flux_amplitude_t"
                )
                context = CoreLossEvaluationContext(
                    fundamental_flux_amplitude_t=fundamental_flux_amplitude_t,
                    fundamental_extraction_method="explicit_audited_argument",
                    source_fields=("fundamental_flux_amplitude_t",),
                )
            if context is None:
                return _unavailable(
                    CoreLossValidityStatus.INVALID_EXCITATION,
                    selected,
                    frequency_hz,
                    temperature_c,
                    flux_ac_peak_t,
                    material_id,
                    material_name,
                    source_provenance,
                    calculation_mode,
                    "Magnetics b>2 requires an audited fundamental flux amplitude; total AC peak is not a substitute.",
                )
            if not isinstance(context, CoreLossEvaluationContext):
                raise TypeError("evaluation_context must be CoreLossEvaluationContext.")
            fundamental = context.fundamental_flux_amplitude_t
            if fundamental is None:
                return _unavailable(
                    CoreLossValidityStatus.INVALID_EXCITATION,
                    selected,
                    frequency_hz,
                    temperature_c,
                    flux_ac_peak_t,
                    material_id,
                    material_name,
                    source_provenance,
                    calculation_mode,
                    "Magnetics b>2 requires a nonnegative fundamental flux amplitude.",
                )
            fundamental = _finite_nonnegative(fundamental, "fundamental_flux_amplitude_t")
            if fundamental <= 0.0:
                return _unavailable(
                    CoreLossValidityStatus.INVALID_EXCITATION,
                    selected,
                    frequency_hz,
                    temperature_c,
                    flux_ac_peak_t,
                    material_id,
                    material_name,
                    source_provenance,
                    calculation_mode,
                    "Magnetics b>2 requires a positive fundamental flux amplitude.",
                )
            density = a * fundamental ** (b - 2.0) * frequency_hz**c * flux_ac_peak_t**2
            details["fundamental_flux_amplitude_t"] = fundamental
            details["fundamental_extraction_method"] = context.fundamental_extraction_method
            details["evaluation_source_fields"] = list(context.source_fields)
        else:
            density = a * flux_ac_peak_t**b * frequency_hz**c
        _finite_nonnegative(density, "volumetric_loss_w_per_m3")
        return _result(
            selected=selected,
            density=density,
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            flux_ac_peak_t=flux_ac_peak_t,
            flux_dc_offset_t=flux_dc_offset_t,
            effective_volume_m3=effective_volume_m3,
            core_mass_kg=core_mass_kg,
            material_id=material_id,
            material_name=material_name,
            source_provenance=source_provenance,
            calculation_mode=calculation_mode,
            status=range_status,
            message=range_message,
            extrapolated=extrapolated,
            details=details,
        )
    except (ArithmeticError, TypeError, ValueError) as exc:
        selected = _safe_coerce_model(model)
        return _unavailable(
            CoreLossValidityStatus.INVALID_MATERIAL_RECORD,
            selected,
            frequency_hz,
            temperature_c,
            flux_ac_peak_t,
            material_id,
            material_name,
            source_provenance,
            calculation_mode,
            str(exc),
        )


def calculate_micrometals_loss(
    *,
    model: MaterialLossModel | Mapping[str, Any],
    frequency_hz: float,
    flux_ac_peak_t: float,
    temperature_c: float = 25.0,
    flux_dc_offset_t: float = 0.0,
    effective_volume_m3: float | None = None,
    core_mass_kg: float | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Evaluate the pinned Micrometals SI-form equation."""

    try:
        selected = _coerce_model(model)
        if selected.method.casefold() != "micrometals":
            return _unavailable(
                CoreLossValidityStatus.MODEL_NOT_SUPPORTED,
                selected,
                frequency_hz,
                temperature_c,
                flux_ac_peak_t,
                material_id,
                material_name,
                source_provenance,
                calculation_mode,
                "The supplied model is not a Micrometals model.",
            )
        frequency_hz = _finite_positive(frequency_hz, "frequency_hz")
        flux_ac_peak_t = _finite_positive(flux_ac_peak_t, "flux_ac_peak_t")
        temperature_c = _finite(temperature_c, "temperature_c")
        effective_volume_m3 = _optional_positive(effective_volume_m3, "effective_volume_m3")
        core_mass_kg = _optional_positive(core_mass_kg, "core_mass_kg")
        coefficients = {
            name: _coefficient(selected, name, nonnegative=False)
            for name in ("a", "b", "c", "d")
        }
        denominator = (
            coefficients["a"] / flux_ac_peak_t**3
            + coefficients["b"] / flux_ac_peak_t**2.3
            + coefficients["c"] / flux_ac_peak_t**1.65
        )
        _finite_positive(denominator, "micrometals denominator")
        frequency_term = frequency_hz / denominator
        eddy_term = coefficients["d"] * flux_ac_peak_t**2 * frequency_hz**2
        _finite_nonnegative(frequency_term, "micrometals frequency term")
        _finite_nonnegative(eddy_term, "micrometals eddy term")
        density = frequency_term + eddy_term
        _finite_nonnegative(density, "volumetric_loss_w_per_m3")
        range_status, range_message, extrapolated = _range_state(
            selected, frequency_hz, flux_ac_peak_t, temperature_c
        )
        return _result(
            selected=selected,
            density=density,
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            flux_ac_peak_t=flux_ac_peak_t,
            flux_dc_offset_t=flux_dc_offset_t,
            effective_volume_m3=effective_volume_m3,
            core_mass_kg=core_mass_kg,
            material_id=material_id,
            material_name=material_name,
            source_provenance=source_provenance,
            calculation_mode=calculation_mode,
            status=range_status,
            message=range_message,
            extrapolated=extrapolated,
            details={
                "formula_id": MICROMETALS_FORMULA_ID,
                "input_frequency_hz": frequency_hz,
                "input_flux_ac_peak_t": flux_ac_peak_t,
                "coefficients": coefficients,
                "denominator": denominator,
                "frequency_term_w_per_m3": frequency_term,
                "eddy_term_w_per_m3": eddy_term,
                "source_reference": selected.source_reference,
            },
            loss_components={
                "frequency_term_w_per_m3": frequency_term,
                "eddy_term_w_per_m3": eddy_term,
            },
        )
    except (ArithmeticError, TypeError, ValueError) as exc:
        selected = _safe_coerce_model(model)
        return _unavailable(
            CoreLossValidityStatus.INVALID_MATERIAL_RECORD,
            selected,
            frequency_hz,
            temperature_c,
            flux_ac_peak_t,
            material_id,
            material_name,
            source_provenance,
            calculation_mode,
            str(exc),
        )


def calculate_poco_loss(
    *,
    model: MaterialLossModel | Mapping[str, Any],
    frequency_hz: float,
    flux_ac_peak_t: float,
    temperature_c: float = 25.0,
    flux_dc_offset_t: float = 0.0,
    effective_volume_m3: float | None = None,
    core_mass_kg: float | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Evaluate POCO with its native B*10 and f/1000 conversions local."""

    return _calculate_native_proprietary_loss(
        method="poco",
        formula_id=POCO_FORMULA_ID,
        model=model,
        frequency_hz=frequency_hz,
        flux_ac_peak_t=flux_ac_peak_t,
        temperature_c=temperature_c,
        flux_dc_offset_t=flux_dc_offset_t,
        effective_volume_m3=effective_volume_m3,
        core_mass_kg=core_mass_kg,
        material_id=material_id,
        material_name=material_name,
        source_provenance=source_provenance,
        calculation_mode=calculation_mode,
    )


def calculate_tdg_loss(
    *,
    model: MaterialLossModel | Mapping[str, Any],
    frequency_hz: float,
    flux_ac_peak_t: float,
    temperature_c: float = 25.0,
    flux_dc_offset_t: float = 0.0,
    effective_volume_m3: float | None = None,
    core_mass_kg: float | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Evaluate TDG with its native B*10 and f/1000 conversions local."""

    return _calculate_native_proprietary_loss(
        method="tdg",
        formula_id=TDG_FORMULA_ID,
        model=model,
        frequency_hz=frequency_hz,
        flux_ac_peak_t=flux_ac_peak_t,
        temperature_c=temperature_c,
        flux_dc_offset_t=flux_dc_offset_t,
        effective_volume_m3=effective_volume_m3,
        core_mass_kg=core_mass_kg,
        material_id=material_id,
        material_name=material_name,
        source_provenance=source_provenance,
        calculation_mode=calculation_mode,
    )


def _calculate_native_proprietary_loss(
    *,
    method: str,
    formula_id: str,
    model: MaterialLossModel | Mapping[str, Any],
    frequency_hz: float,
    flux_ac_peak_t: float,
    temperature_c: float,
    flux_dc_offset_t: float,
    effective_volume_m3: float | None,
    core_mass_kg: float | None,
    material_id: str,
    material_name: str,
    source_provenance: SourceProvenance | None,
    calculation_mode: str,
) -> CoreLossResult:
    try:
        selected = _coerce_model(model)
        if selected.method.casefold() != method:
            return _unavailable(
                CoreLossValidityStatus.MODEL_NOT_SUPPORTED, selected, frequency_hz,
                temperature_c, flux_ac_peak_t, material_id, material_name,
                source_provenance, calculation_mode,
                f"The supplied model is not a {method.upper()} model.",
            )
        frequency_hz = _finite_positive(frequency_hz, "frequency_hz")
        flux_ac_peak_t = _finite_positive(flux_ac_peak_t, "flux_ac_peak_t")
        temperature_c = _finite(temperature_c, "temperature_c")
        effective_volume_m3 = _optional_positive(effective_volume_m3, "effective_volume_m3")
        core_mass_kg = _optional_positive(core_mass_kg, "core_mass_kg")
        coefficients = {
            name: _coefficient(selected, name, nonnegative=True)
            for name in (("a", "b", "c") if method == "poco" else ("a", "b", "c", "d"))
        }
        native_flux = flux_ac_peak_t * 10.0
        native_frequency = frequency_hz / 1000.0
        _finite_positive(native_flux, "native flux density")
        _finite_positive(native_frequency, "native frequency")
        if method == "poco":
            first_term = coefficients["a"] * native_flux**coefficients["b"] * native_frequency
            second_term = coefficients["c"] * (native_flux * native_frequency) ** 2
            _finite_nonnegative(first_term, "POCO first term")
            _finite_nonnegative(second_term, "POCO second term")
            density = 1000.0 * (first_term + second_term)
            components = {
                "linear_native_term_w_per_m3": 1000.0 * first_term,
                "quadratic_native_term_w_per_m3": 1000.0 * second_term,
            }
        else:
            linear_term = coefficients["b"] * native_frequency
            power_term = coefficients["c"] * native_frequency**coefficients["d"]
            _finite_nonnegative(linear_term, "TDG linear frequency term")
            _finite_nonnegative(power_term, "TDG power frequency term")
            flux_factor = native_flux**coefficients["a"]
            _finite_nonnegative(flux_factor, "TDG flux factor")
            density = 1000.0 * flux_factor * (linear_term + power_term)
            components = {
                "linear_frequency_term_w_per_m3": 1000.0 * flux_factor * linear_term,
                "power_frequency_term_w_per_m3": 1000.0 * flux_factor * power_term,
            }
        _finite_nonnegative(density, "volumetric_loss_w_per_m3")
        range_status, range_message, extrapolated = _range_state(
            selected, frequency_hz, flux_ac_peak_t, temperature_c
        )
        return _result(
            selected=selected,
            density=density,
            frequency_hz=frequency_hz,
            temperature_c=temperature_c,
            flux_ac_peak_t=flux_ac_peak_t,
            flux_dc_offset_t=flux_dc_offset_t,
            effective_volume_m3=effective_volume_m3,
            core_mass_kg=core_mass_kg,
            material_id=material_id,
            material_name=material_name,
            source_provenance=source_provenance,
            calculation_mode=calculation_mode,
            status=range_status,
            message=range_message,
            extrapolated=extrapolated,
            details={
                "formula_id": formula_id,
                "input_frequency_hz": frequency_hz,
                "input_flux_ac_peak_t": flux_ac_peak_t,
                "native_frequency": native_frequency,
                "native_frequency_unit": "kHz",
                "native_flux_density": native_flux,
                "native_flux_density_unit": "dT",
                "native_output_scale": 1000.0,
                "conversion_policy": "vendor_local_B_times_10_f_div_1000_output_times_1000_once",
                "coefficients": coefficients,
                "source_reference": selected.source_reference,
            },
            loss_components=components,
        )
    except (ArithmeticError, TypeError, ValueError) as exc:
        selected = _safe_coerce_model(model)
        return _unavailable(
            CoreLossValidityStatus.INVALID_MATERIAL_RECORD, selected, frequency_hz,
            temperature_c, flux_ac_peak_t, material_id, material_name,
            source_provenance, calculation_mode, str(exc),
        )


def calculate_proprietary_volumetric_loss(*, model: MaterialLossModel | Mapping[str, Any], **kwargs: Any) -> CoreLossResult:
    """Dispatch only the two Step 7B methods by declared method name."""

    try:
        selected = _coerce_model(model)
    except (TypeError, ValueError) as exc:
        return _unavailable(
            CoreLossValidityStatus.INVALID_MATERIAL_RECORD,
            _safe_coerce_model(model),
            kwargs.get("frequency_hz", 1.0),
            kwargs.get("temperature_c", 25.0),
            kwargs.get("flux_ac_peak_t", 0.0),
            kwargs.get("material_id", "unknown-material"),
            kwargs.get("material_name", "unknown-material"),
            kwargs.get("source_provenance"),
            kwargs.get("calculation_mode", "shadow"),
            str(exc),
        )
    method = selected.method.casefold()
    if method == "magnetics":
        return calculate_magnetics_loss(model=model, **kwargs)
    if method == "micrometals":
        return calculate_micrometals_loss(model=model, **kwargs)
    if method == "poco":
        return calculate_poco_loss(model=model, **kwargs)
    if method == "tdg":
        return calculate_tdg_loss(model=model, **kwargs)
    return _unavailable(
        CoreLossValidityStatus.MODEL_NOT_SUPPORTED,
        selected,
        kwargs.get("frequency_hz", 1.0),
        kwargs.get("temperature_c", 25.0),
        kwargs.get("flux_ac_peak_t", 0.0),
        kwargs.get("material_id", "unknown-material"),
        kwargs.get("material_name", "unknown-material"),
        kwargs.get("source_provenance"),
        kwargs.get("calculation_mode", "shadow"),
        f"Step 7B/7C does not implement method {selected.method!r}.",
    )


def _coerce_model(model: MaterialLossModel | Mapping[str, Any]) -> _ProprietaryModel:
    if isinstance(model, MaterialLossModel):
        return _ProprietaryModel(
            model.model_id, model.method, model.scope, model.coefficients,
            model.input_flux_definition, model.output_basis,
            model.valid_frequency_range_hz, model.valid_flux_density_range_t,
            model.valid_temperature_range_c, model.source_provenance,
            model.source_reference,
        )
    if not isinstance(model, Mapping):
        raise TypeError("model must be MaterialLossModel or a mapping.")
    bounds = model.get("valid_frequency_range_hz")
    coefficients = dict(model.get("coefficients") or {})
    for name in ("a", "b", "c", "d"):
        if name in model:
            coefficients[name] = model[name]
    return _ProprietaryModel(
        str(model.get("model_id") or model.get("id") or "runtime-proprietary-model"),
        str(model.get("method") or ""),
        str(model.get("scope") or "default"),
        coefficients,
        str(model.get("input_flux_definition") or "ac_peak_t"),
        str(model.get("output_basis") or "volumetric_w_per_m3"),
        _bounds(bounds),
        _bounds(model.get("valid_flux_density_range_t")),
        _bounds(model.get("valid_temperature_range_c")),
        model.get("source_provenance") if isinstance(model.get("source_provenance"), SourceProvenance) else None,
        str(model.get("source_reference")) if model.get("source_reference") is not None else None,
    )


def _safe_coerce_model(model: Any) -> _ProprietaryModel:
    try:
        return _coerce_model(model)
    except Exception:
        return _ProprietaryModel("invalid-model", "unknown", "default", {}, "ac_peak_t", "volumetric_w_per_m3", None, None, None, None, None)


def _bounds(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError("model ranges must contain exactly two values.")
    left, right = float(value[0]), float(value[1])
    if not math.isfinite(left) or not math.isfinite(right) or left > right:
        raise ValueError("model ranges must be finite and ordered.")
    return left, right


def _coefficient(model: _ProprietaryModel, name: str, *, nonnegative: bool) -> float:
    if name not in model.coefficients:
        raise ValueError(f"{model.method} coefficient {name!r} is missing.")
    value = _finite(model.coefficients[name], f"coefficient {name}")
    if nonnegative and value < 0.0:
        raise ValueError(f"{model.method} coefficient {name!r} must be nonnegative.")
    return value


def _range_state(model: _ProprietaryModel, frequency_hz: float, flux_t: float, temperature_c: float) -> tuple[CoreLossValidityStatus, str, bool]:
    if model.valid_frequency_range_hz and not _in_range(frequency_hz, model.valid_frequency_range_hz):
        return CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE, "Frequency is outside the declared model range; value is extrapolated for audit.", True
    if model.valid_flux_density_range_t and not _in_range(flux_t, model.valid_flux_density_range_t):
        return CoreLossValidityStatus.OUTSIDE_FLUX_RANGE, "Flux amplitude is outside the declared model range; value is extrapolated for audit.", True
    if model.valid_temperature_range_c and not _in_range(temperature_c, model.valid_temperature_range_c):
        return CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE, "Temperature is outside the declared model range; value is extrapolated for audit.", True
    return CoreLossValidityStatus.VALID, "Proprietary volumetric loss calculated with the pinned Step 7B equation.", False


def _result(*, selected: _ProprietaryModel, density: float, frequency_hz: float, temperature_c: float, flux_ac_peak_t: float, flux_dc_offset_t: float, effective_volume_m3: float | None, core_mass_kg: float | None, material_id: str, material_name: str, source_provenance: SourceProvenance | None, calculation_mode: str, status: CoreLossValidityStatus, message: str, extrapolated: bool, details: Mapping[str, Any], loss_components: Mapping[str, Any] | None = None) -> CoreLossResult:
    total = density * effective_volume_m3 if effective_volume_m3 is not None else None
    mass_loss = density * effective_volume_m3 / core_mass_kg if effective_volume_m3 is not None and core_mass_kg is not None else None
    return CoreLossResult(
        core_loss_w=total,
        volumetric_loss_w_per_m3=density,
        mass_loss_w_per_kg=mass_loss,
        method_used=selected.method,
        model_policy=STEP7B_MODEL_POLICY,
        material_id=material_id,
        material_name=material_name,
        temperature_c=temperature_c,
        frequency_hz=frequency_hz,
        flux_ac_peak_t=flux_ac_peak_t,
        flux_dc_offset_t=flux_dc_offset_t,
        validity_status=status,
        validity_messages=(message,),
        interpolated=False,
        fitted=False,
        extrapolated=extrapolated,
        proxy_used=False,
        source_provenance=source_provenance or selected.source_provenance or _runtime_provenance(),
        selected_model_id=selected.model_id,
        selected_model_scope=selected.scope,
        input_flux_definition=selected.input_flux_definition,
        effective_volume_m3=effective_volume_m3,
        core_mass_kg=core_mass_kg,
        calculation_mode=calculation_mode,
        unit_conversion_policy="W_per_m3_times_m3_equals_W_once",
        loss_components=loss_components,
        model_evaluation_details=details,
        range_handling="extrapolated_outside_declared_range" if extrapolated else "in_declared_range",
    )


def _unavailable(status: CoreLossValidityStatus, selected: _ProprietaryModel, frequency_hz: Any, temperature_c: Any, flux_ac_peak_t: Any, material_id: str, material_name: str, source_provenance: SourceProvenance | None, calculation_mode: str, message: str) -> CoreLossResult:
    return CoreLossResult(
        core_loss_w=None,
        volumetric_loss_w_per_m3=None,
        mass_loss_w_per_kg=None,
        method_used=None,
        model_policy=STEP7B_MODEL_POLICY,
        material_id=str(material_id),
        material_name=str(material_name),
        temperature_c=float(temperature_c) if _is_finite(temperature_c) else 25.0,
        frequency_hz=float(frequency_hz) if _is_finite(frequency_hz) and float(frequency_hz) > 0 else 1e-12,
        flux_ac_peak_t=float(flux_ac_peak_t) if _is_finite(flux_ac_peak_t) and float(flux_ac_peak_t) >= 0 else 0.0,
        flux_dc_offset_t=0.0,
        validity_status=status,
        validity_messages=(message,),
        interpolated=False,
        fitted=False,
        extrapolated=False,
        proxy_used=False,
        source_provenance=source_provenance or selected.source_provenance or _runtime_provenance(),
        selected_model_id=selected.model_id,
        selected_model_scope=selected.scope,
        calculation_mode=calculation_mode,
        model_evaluation_details={"formula_id": MAGNETICS_FORMULA_ID if selected.method.casefold() == "magnetics" else MICROMETALS_FORMULA_ID},
    )


def _runtime_provenance() -> SourceProvenance:
    return SourceProvenance(source_kind="runtime", source_project="PE-Claw", source_file="runtime/core_loss_proprietary_models.py")


def _finite(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _finite_positive(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return result


def _finite_nonnegative(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be nonnegative.")
    return result


def _optional_positive(value: Any, name: str) -> float | None:
    return None if value is None else _finite_positive(value, name)


def _is_finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _in_range(value: float, bounds: tuple[float, float]) -> bool:
    return bounds[0] <= value <= bounds[1]


__all__ = [
    "MAGNETICS_FORMULA_ID",
    "MICROMETALS_FORMULA_ID",
    "POCO_FORMULA_ID",
    "STEP7B_MODEL_POLICY",
    "TDG_FORMULA_ID",
    "calculate_magnetics_loss",
    "calculate_micrometals_loss",
    "calculate_poco_loss",
    "calculate_proprietary_volumetric_loss",
    "calculate_tdg_loss",
]
