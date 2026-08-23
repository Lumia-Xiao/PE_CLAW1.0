"""Shadow-only deterministic router for normalized-v2 core-loss models.

The router is deliberately separate from the production Steinmetz path.  It
tries only models with the required evidence, preserves every decision in
``CoreLossResult.routing_attempts``, and treats measured data as explicit
opt-in evidence.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import math
from typing import Any, Mapping

from ...models.magnetic_loss_contract import (
    CoreLossEvaluationContext,
    CoreLossExcitation,
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
    CoreLossExcitationBuildResult,
    CoreLossExcitationBuildStatus,
)
from .core_loss_kernel import calculate_igse_loss, calculate_steinmetz_loss
from .core_loss_loss_factor import calculate_loss_factor_loss
from .core_loss_measured import evaluate_measured_loss
from .core_loss_proprietary_models import calculate_proprietary_volumetric_loss
from .core_loss_roshen import calculate_roshen_loss
from .core_loss_magnetec import calculate_magnetec_loss
from .core_loss_excitation_builder import build_core_loss_excitation


ROUTER_POLICY = "mkf_compatible_v1"
ROUTER_SHADOW_POLICY = "mkf_compatible_v1_step7g_router_shadow"
_SUCCESS = {CoreLossValidityStatus.VALID, CoreLossValidityStatus.VALID_INTERPOLATED}
_SKIPPABLE = _SUCCESS | {
    CoreLossValidityStatus.MODEL_NOT_SUPPORTED,
    CoreLossValidityStatus.LOSS_DATA_NOT_AVAILABLE,
    CoreLossValidityStatus.INSUFFICIENT_MEASURED_DATA,
    CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE,
    CoreLossValidityStatus.OUTSIDE_FLUX_RANGE,
    CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE,
}


def route_legacy_steinmetz_loss(
    *,
    model: Mapping[str, Any],
    frequency_hz: float,
    flux_peak_to_peak_t: float,
    effective_volume_m3: float | None,
    material_id: str,
    material_name: str,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Route one legacy v1 Steinmetz row through the v2 result contract.

    This adapter is intentionally explicit and local to Step 8.  It allows the
    current v1 DataFrame search to exercise the shared router while the v2
    cache/loader migration remains deferred to Step 12.
    """

    bpp = float(flux_peak_to_peak_t)
    if not math.isfinite(bpp) or bpp < 0.0:
        raise ValueError("flux_peak_to_peak_t must be finite and nonnegative.")
    projected, provenance = _legacy_projection(
        tuple(sorted((str(key), float(value)) for key, value in model.items() if key in {"k", "alpha", "beta", "minimumFrequency", "maximumFrequency"})),
        material_id,
    )
    result = calculate_steinmetz_loss(
        model=projected,
        frequency_hz=float(frequency_hz),
        flux_ac_peak_t=bpp / 2.0,
        temperature_c=25.0,
        effective_volume_m3=effective_volume_m3,
        material_id=f"v1:{material_id}",
        material_name=material_name,
        source_provenance=provenance,
        calculation_mode=calculation_mode,
    )
    attempt = {
        "method": "steinmetz",
        "model_id": projected.model_id,
        "scope": projected.scope,
        "eligible": True,
        "selected": result.validity_status in _SUCCESS,
        "rejection_reason": "" if result.validity_status in _SUCCESS else "; ".join(result.validity_messages),
        "missing_required_inputs": [],
        "frequency_range_status": "in_range" if result.validity_status in _SUCCESS else result.validity_status.value,
        "flux_range_status": "in_range",
        "temperature_range_status": "in_range",
        "result_status": result.validity_status.value,
    }
    return replace(result, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=(attempt,))


@lru_cache(maxsize=4096)
def _legacy_projection(model_items: tuple[tuple[str, float], ...], material_id: str) -> tuple[MaterialLossModel, SourceProvenance]:
    values = dict(model_items)
    provenance = SourceProvenance("normalized_v1_projection", "PE-Claw", "normalized-v1/materials")
    projected = MaterialLossModel(
        model_id=f"v1:{material_id}:steinmetz",
        method="steinmetz",
        scope=str(values.pop("scope", "default")),
        coefficients=values,
        coefficient_units={name: "legacy-v1-compatible" for name in values},
        input_flux_definition="ac_peak_t",
        output_basis="volumetric_w_per_m3",
        valid_frequency_range_hz=(values["minimumFrequency"], values["maximumFrequency"]) if "minimumFrequency" in values and "maximumFrequency" in values else None,
        valid_flux_density_range_t=None,
        valid_temperature_range_c=None,
        tabulated_points=(),
        source_reference="normalized-v1:steinmetz_ranges",
        source_provenance=provenance,
    )
    return projected, provenance


def route_core_loss(
    *,
    material: NormalizedMagneticMaterialV2,
    excitation: CoreLossExcitation,
    evaluation_context: CoreLossEvaluationContext | None = None,
    measured_data_opt_in: bool = False,
    core_mass_kg: float | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Select one model using the frozen ``mkf_compatible_v1`` order.

    ``measured_data_opt_in`` is intentionally false by default.  No model is
    silently converted to Steinmetz and programming errors are not swallowed.
    """

    if not isinstance(material, NormalizedMagneticMaterialV2):
        raise TypeError("material must be NormalizedMagneticMaterialV2.")
    if not isinstance(excitation, CoreLossExcitation):
        raise TypeError("excitation must be CoreLossExcitation.")
    models = tuple(sorted(material.loss_models, key=lambda item: (item.method.casefold(), item.scope, item.model_id)))
    attempts: list[dict[str, Any]] = []

    def attempt(method: str, model_id: str | None, scope: str | None, *, result: CoreLossResult | None = None, eligible: bool, reason: str = "", missing: tuple[str, ...] = ()) -> CoreLossResult | None:
        status = result.validity_status.value if result is not None else "not_evaluated"
        selected = result is not None and result.validity_status in _SUCCESS
        attempt_record = {
            "method": method,
            "model_id": model_id,
            "scope": scope,
            "eligible": eligible,
            "selected": selected,
            "rejection_reason": reason if not selected else "",
            "missing_required_inputs": list(missing),
            "frequency_range_status": _range_status(result, "frequency") if result else "not_evaluated",
            "flux_range_status": _range_status(result, "flux") if result else "not_evaluated",
            "temperature_range_status": _range_status(result, "temperature") if result else "not_evaluated",
            "result_status": status,
            "diagnostic_core_loss_w": result.core_loss_w if result is not None else None,
            "diagnostic_volumetric_loss_w_per_m3": (
                result.volumetric_loss_w_per_m3 if result is not None else None
            ),
        }
        attempts.append(attempt_record)
        return result if selected else None

    # Real waveform first: iGSE is tried for Steinmetz models only.
    if len(excitation.flux_waveform_t) >= 3:
        for model in _models_for(models, "steinmetz"):
            result = calculate_igse_loss(model=model, excitation=excitation, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode=calculation_mode)
            selected = attempt("igse", model.model_id, model.scope, result=result, eligible=True, reason=_result_reason(result))
            if selected is not None:
                return replace(selected, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=tuple(attempts))
    else:
        attempt("igse", None, None, eligible=False, reason="closed periodic flux waveform is unavailable", missing=("flux_waveform_t",))

    # Native volumetric models are attempted in deterministic model order.
    for model in models:
        if model.method.casefold() not in {"magnetics", "micrometals", "poco", "tdg"}:
            continue
        proprietary_kwargs = dict(model=model, frequency_hz=excitation.frequency_hz, temperature_c=excitation.temperature_c, flux_ac_peak_t=excitation.flux_ac_peak_t, flux_dc_offset_t=excitation.flux_dc_offset_t, effective_volume_m3=excitation.effective_volume_m3, core_mass_kg=excitation.core_mass_kg, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode=calculation_mode)
        if model.method.casefold() == "magnetics":
            proprietary_kwargs["evaluation_context"] = evaluation_context
        result = calculate_proprietary_volumetric_loss(**proprietary_kwargs)
        selected = attempt(model.method, model.model_id, model.scope, result=result, eligible=True, reason=_result_reason(result))
        if selected is not None:
            return replace(selected, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=tuple(attempts))

    # lossFactor is a total-watt model and needs the magnetic operating data.
    for model in _models_for(models, "lossfactor"):
        missing = tuple(name for name, value in (("magnetizing_inductance_h", excitation.magnetizing_inductance_h), ("magnetizing_current_rms_a", excitation.magnetizing_current_rms_a)) if value is None)
        if missing:
            attempt("lossFactor", model.model_id, model.scope, eligible=False, reason="required operating inputs are missing", missing=missing)
            continue
        result = calculate_loss_factor_loss(material=material, model=model, frequency_hz=excitation.frequency_hz, magnetizing_inductance_h=excitation.magnetizing_inductance_h, magnetizing_current_rms_a=excitation.magnetizing_current_rms_a, temperature_c=excitation.temperature_c, effective_volume_m3=excitation.effective_volume_m3, core_mass_kg=excitation.core_mass_kg, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode=calculation_mode)
        selected = attempt("lossFactor", model.model_id, model.scope, result=result, eligible=True, reason=_result_reason(result))
        if selected is not None:
            return replace(selected, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=tuple(attempts))

    # Scalar Steinmetz fallback remains bounded by the declared model result.
    for model in _models_for(models, "steinmetz"):
        result = calculate_steinmetz_loss(model=model, frequency_hz=excitation.frequency_hz, flux_ac_peak_t=excitation.flux_ac_peak_t, temperature_c=excitation.temperature_c, effective_volume_m3=excitation.effective_volume_m3, core_mass_kg=excitation.core_mass_kg, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode=calculation_mode)
        selected = attempt("steinmetz", model.model_id, model.scope, result=result, eligible=True, reason=_result_reason(result))
        if selected is not None:
            return replace(selected, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=tuple(attempts))

    for model in _models_for(models, "roshen"):
        result = calculate_roshen_loss(material=material, model=model, excitation=excitation, evaluation_context=evaluation_context, effective_volume_m3=excitation.effective_volume_m3, core_mass_kg=core_mass_kg or excitation.core_mass_kg, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode=calculation_mode)
        selected = attempt("roshen", model.model_id, model.scope, result=result, eligible=True, reason=_result_reason(result))
        if selected is not None:
            return replace(selected, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=tuple(attempts))

    # Magnetec is a mass-basis route and must never be converted to a
    # volumetric estimate when the audited core mass is unavailable.
    for model in _models_for(models, "magnetec"):
        result = calculate_magnetec_loss(
            model=model,
            excitation=excitation,
            core_mass_kg=core_mass_kg or excitation.core_mass_kg,
            material_id=material.material_id,
            material_name=material.material_name,
            source_provenance=material.source_provenance,
            calculation_mode=calculation_mode,
        )
        selected = attempt("magnetec", model.model_id, model.scope, result=result, eligible=True, reason=_result_reason(result))
        if selected is not None:
            return replace(selected, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=tuple(attempts))

    # Explicit legacy proxies are centralized here so topology modules do not
    # carry independent empirical core-loss equations.
    for model in _models_for(models, "legacy_proxy"):
        result = _calculate_legacy_proxy(
            model=model,
            excitation=excitation,
            material=material,
            calculation_mode=calculation_mode,
        )
        selected = attempt("legacy_proxy", model.model_id, model.scope, result=result, eligible=True, reason=_result_reason(result))
        if selected is not None:
            return replace(selected, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=tuple(attempts))

    if measured_data_opt_in:
        for dataset in sorted(material.measured_loss_datasets, key=lambda item: (item.scope, item.dataset_id)):
            result = evaluate_measured_loss(dataset=dataset, frequency_hz=excitation.frequency_hz, flux_density_t=excitation.flux_ac_peak_t, temperature_c=excitation.temperature_c, effective_volume_m3=excitation.effective_volume_m3, core_mass_kg=core_mass_kg or excitation.core_mass_kg, waveform_label=excitation.waveform_definition, material_id=material.material_id, material_name=material.material_name, source_provenance=material.source_provenance, calculation_mode=calculation_mode)
            selected = attempt("measured", dataset.dataset_id, dataset.scope, result=result, eligible=True, reason=_result_reason(result))
            if selected is not None:
                return replace(selected, model_policy=ROUTER_SHADOW_POLICY, routing_attempts=tuple(attempts))
    else:
        if material.measured_loss_datasets:
            attempt("measured", None, None, eligible=False, reason="measured route requires explicit opt-in", missing=("measured_data_opt_in",))

    return replace(_unavailable(material, excitation, calculation_mode), routing_attempts=tuple(attempts))


def route_core_loss_from_build_result(
    *,
    material: NormalizedMagneticMaterialV2,
    build_result: CoreLossExcitationBuildResult,
    evaluation_context: CoreLossEvaluationContext | None = None,
    measured_data_opt_in: bool = False,
    core_mass_kg: float | None = None,
    calculation_mode: str = "production",
) -> CoreLossResult:
    """Consume a role-specific excitation result through the common router."""

    if build_result.status not in {
        CoreLossExcitationBuildStatus.VALID_EXPLICIT_FLUX,
        CoreLossExcitationBuildStatus.VALID_VOLTAGE_INTEGRATED,
        CoreLossExcitationBuildStatus.VALID_CURRENT_RECONSTRUCTED,
        CoreLossExcitationBuildStatus.VALID_SCALAR_TEMPLATE,
    } or build_result.excitation is None:
        return _unavailable_from_build(material, build_result, calculation_mode)
    return route_core_loss(
        material=material,
        excitation=build_result.excitation,
        evaluation_context=evaluation_context,
        measured_data_opt_in=measured_data_opt_in,
        core_mass_kg=core_mass_kg,
        calculation_mode=calculation_mode,
    )


def legacy_material_v2(
    *,
    material_id: str,
    material_name: str,
    steinmetz_ranges: list[Mapping[str, Any]] | None = None,
    proxy_coefficients: Mapping[str, float] | None = None,
    source_reference: str = "legacy-runtime-material",
) -> NormalizedMagneticMaterialV2:
    """Create an explicit v2 material view without changing the v1 loader."""

    models: list[MaterialLossModel] = []
    provenance = SourceProvenance("legacy_runtime_projection", "PE-Claw", source_reference)
    for index, values in enumerate(steinmetz_ranges or ()):
        coefficients = {str(k): float(v) for k, v in values.items() if k in {"k", "alpha", "beta", "ct0", "ct1", "ct2"}}
        bounds = values.get("valid_frequency_range_hz") or (
            values.get("minimumFrequency"), values.get("maximumFrequency")
        )
        frequency_range = tuple(float(v) for v in bounds) if bounds and all(v is not None for v in bounds) else None
        models.append(MaterialLossModel(
            model_id=f"legacy:{material_id}:steinmetz:{index}", method="steinmetz", scope="default",
            coefficients=coefficients, coefficient_units={name: "legacy-v1-compatible" for name in coefficients},
            input_flux_definition="ac_peak_t", output_basis="volumetric_w_per_m3",
            valid_frequency_range_hz=frequency_range, valid_flux_density_range_t=None,
            valid_temperature_range_c=None, tabulated_points=(), source_reference=source_reference,
            source_provenance=provenance,
        ))
    if proxy_coefficients:
        models.append(MaterialLossModel(
            model_id=f"legacy:{material_id}:proxy", method="legacy_proxy", scope="default",
            coefficients={str(k): float(v) for k, v in proxy_coefficients.items()},
            coefficient_units={"density_reference_w_per_m3": "W/m3", "reference_frequency_hz": "Hz", "reference_flux_t": "T", "frequency_exponent": "1", "flux_exponent": "1"},
            input_flux_definition="ac_peak_t", output_basis="volumetric_w_per_m3",
            valid_frequency_range_hz=None, valid_flux_density_range_t=None, valid_temperature_range_c=None,
            tabulated_points=(), source_reference=source_reference, source_provenance=provenance,
        ))
    return NormalizedMagneticMaterialV2(
        material_id=str(material_id), material_name=str(material_name), manufacturer="legacy-runtime",
        family=None, composition=None, application=None, density_kg_per_m3=None,
        curie_temperature_c=None, thermal_conductivity_w_per_m_k=None, specific_heat_j_per_kg_k=None,
        resistivity_data={}, saturation_data={}, remanence_data={}, coercive_force_data={},
        permeability_data={}, dc_bias_data={}, loss_models=tuple(models), measured_loss_datasets=(),
        recommended_frequency_range_hz=None, source_provenance=provenance,
    )


def _calculate_legacy_proxy(*, model: MaterialLossModel, excitation: CoreLossExcitation, material: NormalizedMagneticMaterialV2, calculation_mode: str) -> CoreLossResult:
    c = model.coefficients
    density_ref = float(c.get("density_reference_w_per_m3", 0.0))
    f_ref = float(c.get("reference_frequency_hz", 100_000.0))
    b_ref = float(c.get("reference_flux_t", 0.1))
    f_exp = float(c.get("frequency_exponent", 1.0))
    b_exp = float(c.get("flux_exponent", 2.0))
    if density_ref < 0.0 or f_ref <= 0.0 or b_ref <= 0.0 or excitation.flux_ac_peak_t < 0.0:
        return _unavailable(material, excitation, calculation_mode)
    density = density_ref * (excitation.frequency_hz / f_ref) ** f_exp * (excitation.flux_ac_peak_t / b_ref) ** b_exp
    total = density * excitation.effective_volume_m3 if excitation.effective_volume_m3 is not None else None
    return CoreLossResult(
        core_loss_w=total, volumetric_loss_w_per_m3=density, mass_loss_w_per_kg=None,
        method_used="legacy_proxy", model_policy=ROUTER_SHADOW_POLICY, material_id=material.material_id,
        material_name=material.material_name, temperature_c=excitation.temperature_c,
        frequency_hz=excitation.frequency_hz, flux_ac_peak_t=excitation.flux_ac_peak_t,
        flux_dc_offset_t=excitation.flux_dc_offset_t, validity_status=CoreLossValidityStatus.VALID,
        validity_messages=("Explicit legacy proxy evaluated by shared router; not a material datasheet model.",),
        interpolated=False, fitted=False, extrapolated=False, proxy_used=True,
        source_provenance=material.source_provenance, selected_model_id=model.model_id,
        selected_model_scope=model.scope, input_flux_definition=model.input_flux_definition,
        effective_volume_m3=excitation.effective_volume_m3, core_mass_kg=excitation.core_mass_kg,
        calculation_mode=calculation_mode, unit_conversion_policy="W_per_m3_times_m3_equals_W_once",
    )


def _unavailable_from_build(material: NormalizedMagneticMaterialV2, build_result: CoreLossExcitationBuildResult, calculation_mode: str) -> CoreLossResult:
    return CoreLossResult(
        core_loss_w=None, volumetric_loss_w_per_m3=None, mass_loss_w_per_kg=None, method_used=None,
        model_policy=ROUTER_SHADOW_POLICY, material_id=material.material_id, material_name=material.material_name,
        temperature_c=25.0, frequency_hz=build_result.waveform_period_s and 1.0 / build_result.waveform_period_s or 1.0,
        flux_ac_peak_t=0.0, flux_dc_offset_t=0.0,
        validity_status=CoreLossValidityStatus.INVALID_EXCITATION,
        validity_messages=tuple(build_result.messages) or ("Excitation build did not produce a valid waveform.",),
        interpolated=False, fitted=False, extrapolated=False, proxy_used=False,
        source_provenance=material.source_provenance, calculation_mode=calculation_mode,
    )


def _models_for(models: tuple[MaterialLossModel, ...], method: str) -> tuple[MaterialLossModel, ...]:
    return tuple(model for model in models if model.method.casefold() == method.casefold())


def _result_reason(result: CoreLossResult) -> str:
    return "; ".join(result.validity_messages) if result.validity_status not in _SUCCESS else ""


def _range_status(result: CoreLossResult | None, axis: str) -> str:
    if result is None:
        return "not_evaluated"
    status = result.validity_status
    if axis == "frequency" and status is CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE:
        return "outside"
    if axis == "flux" and status is CoreLossValidityStatus.OUTSIDE_FLUX_RANGE:
        return "outside"
    if axis == "temperature" and status is CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE:
        return "outside"
    return "in_range" if status in _SUCCESS else "unknown"


def _unavailable(material: NormalizedMagneticMaterialV2, excitation: CoreLossExcitation, calculation_mode: str) -> CoreLossResult:
    return CoreLossResult(
        core_loss_w=None,
        volumetric_loss_w_per_m3=None,
        mass_loss_w_per_kg=None,
        method_used=None,
        model_policy=ROUTER_SHADOW_POLICY,
        material_id=material.material_id,
        material_name=material.material_name,
        temperature_c=excitation.temperature_c,
        frequency_hz=excitation.frequency_hz,
        flux_ac_peak_t=excitation.flux_ac_peak_t,
        flux_dc_offset_t=excitation.flux_dc_offset_t,
        validity_status=CoreLossValidityStatus.LOSS_DATA_NOT_AVAILABLE,
        validity_messages=("No eligible core-loss route produced a valid result.",),
        interpolated=False,
        fitted=False,
        extrapolated=False,
        proxy_used=False,
        source_provenance=material.source_provenance,
        effective_volume_m3=excitation.effective_volume_m3,
        core_mass_kg=excitation.core_mass_kg,
        calculation_mode=calculation_mode,
    )


__all__ = ["ROUTER_POLICY", "ROUTER_SHADOW_POLICY", "route_core_loss", "route_core_loss_from_build_result", "route_legacy_steinmetz_loss", "legacy_material_v2"]
