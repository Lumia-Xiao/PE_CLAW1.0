"""Shadow-only Magnetec mass-basis core-loss evaluator."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from ...models.magnetic_loss_contract import (
    CoreLossExcitation,
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
)


STEP7F_MODEL_POLICY = "mkf_compatible_v1_step7f_shadow"
MAGNETEC_FORMULA_ID = "mkf_magnetec_mass_v1"


@dataclass(frozen=True)
class _MagnetecModel:
    model_id: str
    method: str
    scope: str
    output_basis: str
    valid_frequency_range_hz: tuple[float, float] | None
    valid_flux_density_range_t: tuple[float, float] | None
    valid_temperature_range_c: tuple[float, float] | None
    source_provenance: SourceProvenance | None
    source_reference: str | None


def calculate_magnetec_loss(
    *,
    model: MaterialLossModel | Mapping[str, Any],
    excitation: CoreLossExcitation,
    core_mass_kg: float | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Calculate Magnetec mass loss using explicit Bpp and optional mass.

    The returned density remains W/kg.  Effective volume is deliberately not an
    input because it cannot establish a mass basis without an audited solid
    volume and density.
    """

    selected = _coerce_model(model)
    provenance = source_provenance or selected.source_provenance or _material_provenance(model) or _runtime_provenance()
    try:
        if selected.method.casefold() != "magnetec":
            return _unavailable(CoreLossValidityStatus.MODEL_NOT_SUPPORTED, selected, excitation, material_id, material_name, provenance, calculation_mode, "The supplied model is not a Magnetec model.")
        if selected.output_basis != "mass_w_per_kg":
            return _unavailable(CoreLossValidityStatus.INVALID_MATERIAL_RECORD, selected, excitation, material_id, material_name, provenance, calculation_mode, "Magnetec requires mass_w_per_kg output basis.")
        if not isinstance(excitation, CoreLossExcitation):
            raise TypeError("excitation must be CoreLossExcitation.")
        frequency = _positive(excitation.frequency_hz, "frequency_hz")
        bpp = _nonnegative(excitation.flux_peak_to_peak_t, "flux_peak_to_peak_t")
        mass = None if core_mass_kg is None else _positive(core_mass_kg, "core_mass_kg")
        density = 80.0 * (frequency / 100_000.0) ** 1.8 * (bpp / 0.3) ** 2
        _nonnegative(density, "mass_loss_w_per_kg")
        status, message, extrapolated = _range_state(selected, frequency, bpp, excitation.temperature_c)
        total = density * mass if mass is not None else None
        return CoreLossResult(
            core_loss_w=total,
            volumetric_loss_w_per_m3=None,
            mass_loss_w_per_kg=density,
            method_used="magnetec",
            model_policy=STEP7F_MODEL_POLICY,
            material_id=str(material_id),
            material_name=str(material_name),
            temperature_c=excitation.temperature_c,
            frequency_hz=frequency,
            flux_ac_peak_t=excitation.flux_ac_peak_t,
            flux_dc_offset_t=excitation.flux_dc_offset_t,
            validity_status=status,
            validity_messages=(message,),
            interpolated=False,
            fitted=False,
            extrapolated=extrapolated,
            proxy_used=False,
            source_provenance=provenance,
            selected_model_id=selected.model_id,
            selected_model_scope=selected.scope,
            input_flux_definition="flux_peak_to_peak_t",
            core_mass_kg=mass,
            calculation_mode=calculation_mode,
            unit_conversion_policy="magnetec_80_times_normalized_frequency_1p8_times_normalized_Bpp_squared_W_per_kg",
            loss_components={
                "mass_loss_w_per_kg": density,
                "core_loss_w": total,
            },
            model_evaluation_details={
                "formula_id": MAGNETEC_FORMULA_ID,
                "frequency_hz": frequency,
                "flux_peak_to_peak_t": bpp,
                "normalized_frequency": frequency / 100_000.0,
                "normalized_flux_peak_to_peak": bpp / 0.3,
                "mass_basis": "core_mass_kg_required_for_total_watts",
                "mass_source": "explicit_core_mass_kg" if mass is not None else "not_provided",
                "effective_volume_used": False,
                "source_reference": selected.source_reference,
            },
            range_handling="extrapolated_outside_declared_range" if extrapolated else "in_declared_range",
        )
    except (ArithmeticError, TypeError, ValueError) as exc:
        return _unavailable(CoreLossValidityStatus.INVALID_EXCITATION, selected, excitation, material_id, material_name, provenance, calculation_mode, str(exc))


def _coerce_model(model: MaterialLossModel | Mapping[str, Any]) -> _MagnetecModel:
    if isinstance(model, MaterialLossModel):
        return _MagnetecModel(model.model_id, model.method, model.scope, model.output_basis, model.valid_frequency_range_hz, model.valid_flux_density_range_t, model.valid_temperature_range_c, model.source_provenance, model.source_reference)
    if not isinstance(model, Mapping):
        raise TypeError("model must be MaterialLossModel or mapping.")
    return _MagnetecModel(str(model.get("model_id") or "runtime-magnetec-model"), str(model.get("method") or ""), str(model.get("scope") or "default"), str(model.get("output_basis") or "mass_w_per_kg"), _bounds(model.get("valid_frequency_range_hz")), _bounds(model.get("valid_flux_density_range_t")), _bounds(model.get("valid_temperature_range_c")), model.get("source_provenance") if isinstance(model.get("source_provenance"), SourceProvenance) else None, str(model.get("source_reference")) if model.get("source_reference") is not None else None)


def _range_state(model: _MagnetecModel, frequency: float, bpp: float, temperature: float) -> tuple[CoreLossValidityStatus, str, bool]:
    if model.valid_frequency_range_hz and not _in_range(frequency, model.valid_frequency_range_hz):
        return CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE, "Frequency is outside the declared Magnetec model range.", True
    if model.valid_flux_density_range_t and not _in_range(bpp, model.valid_flux_density_range_t):
        return CoreLossValidityStatus.OUTSIDE_FLUX_RANGE, "Bpp is outside the declared Magnetec model range.", True
    if model.valid_temperature_range_c and not _in_range(temperature, model.valid_temperature_range_c):
        return CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE, "Temperature is outside the declared Magnetec model range.", True
    return CoreLossValidityStatus.VALID, "Magnetec mass loss calculated with the pinned Step 7F equation.", False


def _unavailable(status: CoreLossValidityStatus, model: _MagnetecModel, excitation: Any, material_id: str, material_name: str, provenance: SourceProvenance, calculation_mode: str, message: str) -> CoreLossResult:
    return CoreLossResult(core_loss_w=None, volumetric_loss_w_per_m3=None, mass_loss_w_per_kg=None, method_used=None, model_policy=STEP7F_MODEL_POLICY, material_id=str(material_id), material_name=str(material_name), temperature_c=float(excitation.temperature_c) if hasattr(excitation, "temperature_c") and _is_finite(excitation.temperature_c) else 25.0, frequency_hz=float(excitation.frequency_hz) if hasattr(excitation, "frequency_hz") and _is_finite(excitation.frequency_hz) and float(excitation.frequency_hz) > 0 else 1e-12, flux_ac_peak_t=float(excitation.flux_ac_peak_t) if hasattr(excitation, "flux_ac_peak_t") and _is_finite(excitation.flux_ac_peak_t) and float(excitation.flux_ac_peak_t) >= 0 else 0.0, flux_dc_offset_t=float(excitation.flux_dc_offset_t) if hasattr(excitation, "flux_dc_offset_t") and _is_finite(excitation.flux_dc_offset_t) else 0.0, validity_status=status, validity_messages=(message,), interpolated=False, fitted=False, extrapolated=False, proxy_used=False, source_provenance=provenance, selected_model_id=model.model_id, selected_model_scope=model.scope, calculation_mode=calculation_mode, model_evaluation_details={"formula_id": MAGNETEC_FORMULA_ID})


def _material_provenance(model: Any) -> SourceProvenance | None:
    return model.source_provenance if isinstance(model, NormalizedMagneticMaterialV2) else None


def _runtime_provenance() -> SourceProvenance:
    return SourceProvenance(source_kind="runtime", source_project="PE-Claw", source_file="runtime/core_loss_magnetec.py")


def _bounds(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError("model ranges must contain two values.")
    left, right = _finite(value[0], "range minimum"), _finite(value[1], "range maximum")
    if left > right:
        raise ValueError("model range is not ordered.")
    return left, right


def _in_range(value: float, bounds: tuple[float, float]) -> bool:
    return bounds[0] <= value <= bounds[1]


def _finite(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _positive(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return result


def _nonnegative(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be nonnegative.")
    return result


def _is_finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


__all__ = ["MAGNETEC_FORMULA_ID", "STEP7F_MODEL_POLICY", "calculate_magnetec_loss"]
