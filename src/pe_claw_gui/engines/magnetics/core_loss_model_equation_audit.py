"""Independent equation, unit, range, and multiplier audit for Step 18D.

The reference equations in this module intentionally do not call the
production loss evaluators. Production results are evaluated once and then
compared with independently assembled arithmetic from frozen inputs.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from ...models.magnetic_loss_contract import (
    CoreLossExcitation,
    CoreLossValidityStatus,
    MaterialLossModel,
)
from .core_loss_kernel import calculate_igse_loss, calculate_steinmetz_loss
from .core_loss_proprietary_models import calculate_micrometals_loss


STEP18_MODEL_EQUATION_AUDIT_VERSION = "openmagnetics-step18-model-equation-audit-v1"
RELATIVE_TOLERANCE = 1.0e-9
ABSOLUTE_FLOOR = 1.0e-15
PINNED_MKF_COMMIT = "8d3bad38297ddca92a2aafe9c88a4fc93ef75d5b"

_FIXED_AUDIT_ROLES = (
    "buck_main_inductor",
    "boost_main_inductor",
    "llc_external_resonant_inductor",
    "single_phase_rectifier_dc_link_reactor",
)
_EXPECTED_UNRECONSTRUCTABLE_ROLES = (
    "flyback_coupled_inductor_transformer",
    "llc_transformer",
    "generic_main_inductor_stacked_core_competitor",
)
_PRIOR_METHOD_ARTIFACTS = {
    "magnetics_micrometals": "reports/openmagnetics_step7_non_steinmetz_kernel_audit_20260726.json",
    "poco_tdg": "reports/openmagnetics_step7_poco_tdg_comparison_audit_20260726.json",
    "lossfactor": "reports/openmagnetics_step7_loss_factor_audit_20260726.json",
    "roshen": "reports/openmagnetics_step7_roshen_audit_20260726.json",
    "magnetec": "reports/openmagnetics_step7_magnetec_audit_20260726.json",
    "measured": "reports/openmagnetics_step7g_measured_router_audit_20260726.json",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _relative_error(actual: float, reference: float) -> float:
    return abs(actual - reference) / max(abs(reference), ABSOLUTE_FLOOR)


def _comparison(actual: float | None, reference: float | None) -> dict[str, Any]:
    if actual is None or reference is None:
        return {
            "status": "not_comparable_missing_value",
            "actual": actual,
            "reference": reference,
            "absolute_error": None,
            "relative_error": None,
            "passed": False,
        }
    absolute = abs(float(actual) - float(reference))
    relative = _relative_error(float(actual), float(reference))
    return {
        "status": "comparable",
        "actual": float(actual),
        "reference": float(reference),
        "absolute_error": absolute,
        "relative_error": relative,
        "passed": absolute <= ABSOLUTE_FLOOR or relative <= RELATIVE_TOLERANCE,
    }


def _temperature_factor(coefficients: Mapping[str, float], temperature_c: float) -> tuple[float, str]:
    if not all(name in coefficients for name in ("ct0", "ct1", "ct2")):
        return 1.0, "no_temperature_coefficients"
    factor = (
        float(coefficients["ct2"]) * temperature_c**2
        - float(coefficients["ct1"]) * temperature_c
        + float(coefficients["ct0"])
    )
    if factor <= 0.0:
        return 1.0, "pinned_mkf_nonpositive_temperature_scale_ignored"
    return factor, "pinned_mkf_ct2_T2_minus_ct1_T_plus_ct0_degC"


def _independent_igse(
    *, model: MaterialLossModel, excitation: CoreLossExcitation,
) -> dict[str, Any]:
    coefficients = model.coefficients
    k = float(coefficients["k"])
    alpha = float(coefficients["alpha"])
    beta = float(coefficients["beta"])
    temperature_factor, temperature_source = _temperature_factor(
        coefficients, excitation.temperature_c,
    )
    integral = 0.0
    for index in range(len(excitation.flux_waveform_time_s) - 1):
        dt = excitation.flux_waveform_time_s[index + 1] - excitation.flux_waveform_time_s[index]
        db = excitation.flux_waveform_t[index + 1] - excitation.flux_waveform_t[index]
        derivative = abs(db / dt)
        if derivative:
            integral += (
                derivative**alpha
                * excitation.flux_peak_to_peak_t ** max(beta - alpha, 0.0)
                * dt
            )
    period_s = excitation.flux_waveform_time_s[-1] - excitation.flux_waveform_time_s[0]
    cosine_integral = (
        2.0
        * math.sqrt(math.pi)
        * math.gamma((alpha + 1.0) / 2.0)
        / math.gamma((alpha + 2.0) / 2.0)
    )
    ki = (
        k
        * (2.0 * math.pi) ** (1.0 - alpha)
        * 2.0 ** (alpha - beta)
        / cosine_integral
    )
    density = ki * temperature_factor * integral / period_s
    volume = excitation.effective_volume_m3
    total = density * volume if volume is not None else None
    return {
        "equation": "Pv=ki*temperature_factor*integral(abs(dB/dt)^alpha*Bpp^(max(beta-alpha,0))*dt)/period; Pcore=Pv*Ve",
        "coefficient_units": dict(model.coefficient_units),
        "input_units": {"frequency": "Hz", "flux": "T", "time": "s", "volume": "m3"},
        "output_units": {"density": "W/m3", "total": "W"},
        "coefficients": {"k": k, "alpha": alpha, "beta": beta},
        "temperature_factor": temperature_factor,
        "temperature_source": temperature_source,
        "period_s": period_s,
        "waveform_integral": integral,
        "cosine_integral": cosine_integral,
        "ki": ki,
        "volumetric_loss_w_per_m3": density,
        "effective_volume_m3": volume,
        "core_loss_w": total,
        "generic_x1000_applied": False,
        "volume_multiplier_count": 1 if volume is not None else 0,
        "temperature_multiplier_count": 1,
    }


def _independent_micrometals(
    *, model: MaterialLossModel, excitation: CoreLossExcitation,
) -> dict[str, Any]:
    coefficients = {name: float(model.coefficients[name]) for name in ("a", "b", "c", "d")}
    flux = excitation.flux_ac_peak_t
    frequency = excitation.frequency_hz
    denominator = (
        coefficients["a"] / flux**3
        + coefficients["b"] / flux**2.3
        + coefficients["c"] / flux**1.65
    )
    frequency_term = frequency / denominator
    eddy_term = coefficients["d"] * flux**2 * frequency**2
    density = frequency_term + eddy_term
    volume = excitation.effective_volume_m3
    total = density * volume if volume is not None else None
    return {
        "equation": "Pv=f/(a/Bac^3+b/Bac^2.3+c/Bac^1.65)+d*Bac^2*f^2; Pcore=Pv*Ve",
        "coefficient_units": dict(model.coefficient_units),
        "input_units": {"frequency": "Hz", "flux": "T", "volume": "m3"},
        "output_units": {"density": "W/m3", "total": "W"},
        "coefficients": coefficients,
        "denominator": denominator,
        "frequency_term_w_per_m3": frequency_term,
        "eddy_term_w_per_m3": eddy_term,
        "volumetric_loss_w_per_m3": density,
        "effective_volume_m3": volume,
        "core_loss_w": total,
        "generic_x1000_applied": False,
        "volume_multiplier_count": 1 if volume is not None else 0,
    }


def _range_status(model: MaterialLossModel, excitation: CoreLossExcitation) -> str:
    checks = (
        ("outside_frequency_range", excitation.frequency_hz, model.valid_frequency_range_hz),
        ("outside_flux_range", excitation.flux_ac_peak_t, model.valid_flux_density_range_t),
        ("outside_temperature_range", excitation.temperature_c, model.valid_temperature_range_c),
    )
    for status, value, bounds in checks:
        if bounds is not None and not (bounds[0] <= value <= bounds[1]):
            return status
    return "valid"


def _evaluate_production(
    *, method: str, model: MaterialLossModel, excitation: CoreLossExcitation,
) -> Any:
    if method == "igse":
        return calculate_igse_loss(
            model=model,
            excitation=excitation,
            material_id="step18d-audit",
            material_name="step18d-audit",
            calculation_mode="step18d_equation_audit",
        )
    if method == "micrometals":
        return calculate_micrometals_loss(
            model=model,
            frequency_hz=excitation.frequency_hz,
            flux_ac_peak_t=excitation.flux_ac_peak_t,
            temperature_c=excitation.temperature_c,
            flux_dc_offset_t=excitation.flux_dc_offset_t,
            effective_volume_m3=excitation.effective_volume_m3,
            core_mass_kg=excitation.core_mass_kg,
            material_id="step18d-audit",
            material_name="step18d-audit",
            calculation_mode="step18d_equation_audit",
        )
    raise ValueError(f"Unsupported Step 18D method: {method}.")


def _model_index(material_records: Sequence[Mapping[str, Any]]) -> dict[str, MaterialLossModel]:
    result: dict[str, MaterialLossModel] = {}
    for material in material_records:
        for model_payload in material.get("loss_models") or ():
            model = MaterialLossModel.from_dict(model_payload)
            if model.model_id in result:
                raise ValueError(f"Duplicate model ID {model.model_id}.")
            result[model.model_id] = model
    return result


def _role_equation_record(
    *, role_record: Mapping[str, Any], models: Mapping[str, MaterialLossModel],
) -> dict[str, Any]:
    role = str(role_record["role"])
    fixed = role_record["layers"]["v2_fixed_hardware_recalculation"]
    if role in _EXPECTED_UNRECONSTRUCTABLE_ROLES:
        return {
            "role": role,
            "status": "not_applicable_fixed_hardware_not_reconstructable",
            "method": None,
            "model_id": None,
            "model_scope": None,
            "blockers": list(role_record.get("blockers") or ()),
            "equation_comparison": None,
            "range_check": None,
            "unit_check": None,
        }
    result_payload = fixed.get("core_loss_result")
    excitation_payload = fixed.get("excitation_build_result", {}).get("excitation")
    if not isinstance(result_payload, Mapping) or not isinstance(excitation_payload, Mapping):
        raise ValueError(f"{role}: Step 18C result or excitation is missing.")
    range_attempt = next(
        (
            item for item in result_payload.get("routing_attempts") or ()
            if item.get("result_status") in {
                "outside_frequency_range", "outside_flux_range",
                "outside_temperature_range",
            }
        ),
        None,
    )
    method = str(result_payload.get("method_used") or (range_attempt or {}).get("method") or "")
    model_id = str(result_payload.get("selected_model_id") or (range_attempt or {}).get("model_id") or "")
    if method not in {"igse", "micrometals"} or model_id not in models:
        raise ValueError(f"{role}: unsupported or missing selected model evidence.")
    model = models[model_id]
    excitation = CoreLossExcitation.from_dict(excitation_payload)
    reference = (
        _independent_igse(model=model, excitation=excitation)
        if method == "igse"
        else _independent_micrometals(model=model, excitation=excitation)
    )
    production = _evaluate_production(method=method, model=model, excitation=excitation)
    density_comparison = _comparison(
        production.volumetric_loss_w_per_m3,
        reference["volumetric_loss_w_per_m3"],
    )
    total_comparison = _comparison(production.core_loss_w, reference["core_loss_w"])
    frozen_density_comparison = _comparison(
        result_payload.get("volumetric_loss_w_per_m3") if range_attempt is None
        else range_attempt.get("diagnostic_volumetric_loss_w_per_m3"),
        reference["volumetric_loss_w_per_m3"],
    )
    frozen_total_comparison = _comparison(
        result_payload.get("core_loss_w") if range_attempt is None
        else range_attempt.get("diagnostic_core_loss_w"),
        reference["core_loss_w"],
    )
    expected_range_status = _range_status(model, excitation)
    range_passed = production.validity_status.value == expected_range_status
    unit_passed = (
        model.output_basis == "volumetric_w_per_m3"
        and reference["generic_x1000_applied"] is False
        and reference["volume_multiplier_count"] == 1
    )
    equation_passed = all(
        item["passed"]
        for item in (density_comparison, total_comparison, frozen_density_comparison, frozen_total_comparison)
    )
    return {
        "role": role,
        "status": "passed" if equation_passed and range_passed and unit_passed else "failed",
        "method": method,
        "model_id": model.model_id,
        "model_scope": model.scope,
        "model_source_reference": model.source_reference,
        "model_source_provenance": model.source_provenance.to_dict(),
        "coefficient_units": dict(model.coefficient_units),
        "excitation": {
            "frequency_hz": excitation.frequency_hz,
            "temperature_c": excitation.temperature_c,
            "flux_ac_peak_t": excitation.flux_ac_peak_t,
            "flux_peak_to_peak_t": excitation.flux_peak_to_peak_t,
            "effective_volume_m3": excitation.effective_volume_m3,
            "waveform_sample_count": len(excitation.flux_waveform_t),
        },
        "independent_reference": reference,
        "equation_comparison": {
            "production_density": density_comparison,
            "production_total": total_comparison,
            "frozen_step18c_density": frozen_density_comparison,
            "frozen_step18c_total": frozen_total_comparison,
            "relative_tolerance": RELATIVE_TOLERANCE,
            "absolute_floor": ABSOLUTE_FLOOR,
            "passed": equation_passed,
        },
        "range_check": {
            "expected_status": expected_range_status,
            "current_kernel_status": production.validity_status.value,
            "frozen_step18c_router_raw_status": (
                range_attempt.get("result_status") if range_attempt
                else result_payload.get("validity_status")
            ),
            "frozen_step18c_formal_status": fixed.get("loss_validity_status"),
            "valid_frequency_range_hz": list(model.valid_frequency_range_hz) if model.valid_frequency_range_hz else None,
            "passed": range_passed,
            "kernel_behavior_corrected_in_step18d": (
                range_attempt is not None
                and result_payload.get("validity_status") == "loss_data_not_available"
                and expected_range_status == production.validity_status.value
            ),
        },
        "unit_check": {
            "output_basis": model.output_basis,
            "unit_conversion_policy": production.unit_conversion_policy,
            "generic_x1000_applied": False,
            "volume_applied_once": reference["volume_multiplier_count"] == 1,
            "passed": unit_passed,
        },
        "blockers": [],
    }


def _finemet_reference_record(models: Mapping[str, MaterialLossModel]) -> dict[str, Any]:
    matches = [model for model in models.values() if model.model_id.startswith("material_loss_model:proterial_finemet_") and model.method.casefold() == "steinmetz"]
    if len(matches) != 1:
        raise ValueError(f"Expected one Finemet Steinmetz model, found {len(matches)}.")
    model = matches[0]
    frequency = 100_000.0
    peak = 0.1
    count = 1001
    period = 1.0 / frequency
    time = tuple(index * period / (count - 1) for index in range(count))
    flux = tuple(peak * math.sin(2.0 * math.pi * frequency * value) for value in time)
    excitation = CoreLossExcitation(
        frequency_hz=frequency,
        temperature_c=25.0,
        flux_waveform_time_s=time,
        flux_waveform_t=flux,
        flux_ac_peak_t=peak,
        flux_peak_to_peak_t=2.0 * peak,
        flux_dc_offset_t=0.0,
        flux_absolute_peak_t=peak,
        effective_volume_m3=1.0e-6,
        core_mass_kg=None,
        magnetizing_inductance_h=None,
        magnetizing_current_rms_a=None,
        waveform_definition="step18d_sinusoidal_reference",
        source_topology="step18d",
        source_role="generic_main_inductor_stacked_core_competitor",
    )
    reference = _independent_igse(model=model, excitation=excitation)
    production = calculate_igse_loss(
        model=model,
        excitation=excitation,
        material_id="step18d-finemet",
        material_name="Finemet",
        calculation_mode="step18d_equation_audit",
    )
    density = _comparison(production.volumetric_loss_w_per_m3, reference["volumetric_loss_w_per_m3"])
    total = _comparison(production.core_loss_w, reference["core_loss_w"])
    return {
        "reference_id": "finemet_selected_model_sinusoidal_reference",
        "roles_covered": ["generic_main_inductor_stacked_core_competitor"],
        "method": "igse",
        "model_id": model.model_id,
        "model_scope": model.scope,
        "fixture_kind": "independently_assembled_sinusoidal_waveform",
        "independent_reference": reference,
        "production_status": production.validity_status.value,
        "density_comparison": density,
        "total_comparison": total,
        "passed": density["passed"] and total["passed"] and production.validity_status is CoreLossValidityStatus.VALID,
    }


def _scalar_steinmetz_reference_record(
    *, model: MaterialLossModel, reference_id: str, material_name: str,
) -> dict[str, Any]:
    frequency = 100_000.0
    flux_ac_peak = 0.1
    temperature = 25.0
    volume = 1.0e-6
    coefficients = model.coefficients
    factor, source = _temperature_factor(coefficients, temperature)
    density = (
        float(coefficients["k"])
        * frequency ** float(coefficients["alpha"])
        * flux_ac_peak ** float(coefficients["beta"])
        * factor
    )
    total = density * volume
    production = calculate_steinmetz_loss(
        model=model,
        frequency_hz=frequency,
        flux_ac_peak_t=flux_ac_peak,
        temperature_c=temperature,
        effective_volume_m3=volume,
        material_id=f"step18d-{material_name.casefold()}",
        material_name=material_name,
        calculation_mode="step18d_equation_audit",
    )
    density_comparison = _comparison(production.volumetric_loss_w_per_m3, density)
    total_comparison = _comparison(production.core_loss_w, total)
    return {
        "reference_id": reference_id,
        "roles_covered": [],
        "method": "steinmetz",
        "model_id": model.model_id,
        "model_scope": model.scope,
        "fixture_kind": "independently_assembled_scalar_si_reference",
        "equation": "Pv=k*f^alpha*Bac_peak^beta*temperature_factor; Pcore=Pv*Ve",
        "inputs": {
            "frequency_hz": frequency,
            "flux_ac_peak_t": flux_ac_peak,
            "temperature_c": temperature,
            "effective_volume_m3": volume,
        },
        "temperature_factor": factor,
        "temperature_source": source,
        "reference_density_w_per_m3": density,
        "reference_core_loss_w": total,
        "production_status": production.validity_status.value,
        "density_comparison": density_comparison,
        "total_comparison": total_comparison,
        "generic_x1000_applied": False,
        "volume_multiplier_count": 1,
        "passed": (
            density_comparison["passed"]
            and total_comparison["passed"]
            and production.validity_status is CoreLossValidityStatus.VALID
        ),
    }


def _prior_method_evidence(root: Path) -> list[dict[str, Any]]:
    records = []
    for name, relative in sorted(_PRIOR_METHOD_ARTIFACTS.items()):
        path = root / relative
        records.append({
            "method_group": name,
            "path": relative,
            "sha256": _sha256(path),
            "status": "reference_only_not_selected_by_step17_roles",
        })
    return records


def _multiplier_audit(root: Path) -> dict[str, Any]:
    files = (
        "src/pe_claw_gui/engines/magnetics/core_loss_kernel.py",
        "src/pe_claw_gui/engines/magnetics/core_loss_proprietary_models.py",
        "src/pe_claw_gui/engines/magnetics/inductor_design.py",
        "src/pe_claw_gui/engines/magnetics/stacked_expansion.py",
        "src/pe_claw_gui/topologies/dc_dc/llc_resonant_converter_diode_rectifier/transformer_design.py",
        "src/pe_claw_gui/topologies/dc_dc/flyback_diode_rectified_isolated/coupled_inductor_design.py",
        "src/pe_claw_gui/topologies/dc_dc/phase_shifted_full_bridge_diode_rectifier_isolated/magnetic_design.py",
    )
    matches: list[dict[str, Any]] = []
    pattern = re.compile(r"(?:1000(?:\.0)?|1e3)")
    for relative in files:
        for line_number, line in enumerate((root / relative).read_text(encoding="utf-8").splitlines(), 1):
            if not pattern.search(line):
                continue
            stripped = line.strip()
            if "core_loss_proprietary_models.py" in relative:
                category = "vendor_local_poco_tdg_conversion"
            elif "kernel_vs_legacy_relative_difference" in stripped or "legacy_core_loss_w_with_erroneous_x1000" in stripped:
                category = "audit_only_legacy_x1000_reference"
            elif (
                "_mm" in stripped
                or "_m * 1e3" in stripped
                or "return self.le_m * 1e3" in stripped
            ):
                category = "geometry_unit_conversion_not_core_loss"
            else:
                category = "unclassified_multiplier"
            matches.append({
                "path": relative,
                "line": line_number,
                "text": stripped,
                "category": category,
            })
    prohibited = [item for item in matches if item["category"] == "unclassified_multiplier"]
    return {
        "scanned_files": list(files),
        "matches": matches,
        "prohibited_generic_or_duplicate_x1000": prohibited,
        "vendor_local_policy": "POCO/TDG only: B*10, f/1000, native output*1000 exactly once",
        "passed": not prohibited,
    }


def _reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value at {path}.")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_non_finite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_non_finite(item, f"{path}[{index}]")


def validate_step18_model_equation_audit(payload: Mapping[str, Any]) -> None:
    _reject_non_finite(payload)
    expected_fields = {
        "contract_version", "recorded_date", "scope", "generation_command",
        "inputs", "tolerance", "selected_methods", "selected_model_ids",
        "role_records", "selected_model_references",
        "non_selected_method_references", "multiplier_audit", "summary",
        "integrity",
    }
    if set(payload) != expected_fields:
        raise ValueError("Step 18D contains missing or unknown top-level fields.")
    if payload.get("contract_version") != STEP18_MODEL_EQUATION_AUDIT_VERSION:
        raise ValueError("Invalid Step 18D contract version.")
    records = payload.get("role_records")
    if not isinstance(records, list) or len(records) != 7:
        raise ValueError("Step 18D requires exactly seven role records.")
    roles = [str(item.get("role")) for item in records]
    expected = set(_FIXED_AUDIT_ROLES) | set(_EXPECTED_UNRECONSTRUCTABLE_ROLES)
    if len(set(roles)) != len(roles) or set(roles) != expected:
        raise ValueError("Step 18D roles must be unique and complete.")
    for record in records:
        expected_record_fields = {
            "role", "status", "method", "model_id", "model_scope",
            "blockers", "equation_comparison", "range_check", "unit_check",
        }
        if record["role"] in _FIXED_AUDIT_ROLES:
            expected_record_fields |= {
                "model_source_reference", "model_source_provenance",
                "coefficient_units", "excitation", "independent_reference",
            }
        if set(record) != expected_record_fields:
            raise ValueError(f"{record['role']}: missing or unknown role fields.")
        if record["role"] in _FIXED_AUDIT_ROLES and record.get("status") != "passed":
            raise ValueError(f"{record['role']}: independent equation audit did not pass.")
        if record["role"] in _EXPECTED_UNRECONSTRUCTABLE_ROLES and not record.get("blockers"):
            raise ValueError(f"{record['role']}: unavailable audit requires exact blockers.")
    references = payload.get("selected_model_references")
    if not isinstance(references, list) or not references or not all(item.get("passed") for item in references):
        raise ValueError("Selected-model references must be present and passing.")
    if not payload.get("multiplier_audit", {}).get("passed"):
        raise ValueError("Multiplier audit contains an unclassified x1000 occurrence.")
    if not payload.get("summary", {}).get("acceptance_passed"):
        raise ValueError("Step 18D acceptance did not pass.")


def build_step18_model_equation_audit(
    *, project_root: str | Path, fixed_hardware_path: str | Path,
    v2_materials_path: str | Path,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    fixed_path = Path(fixed_hardware_path).resolve()
    materials_path = Path(v2_materials_path).resolve()
    fixed = _load_json(fixed_path)
    materials_payload = _load_json(materials_path)
    if not isinstance(materials_payload, list):
        raise ValueError("normalized-v2 materials input must be a JSON array.")
    models = _model_index(materials_payload)
    role_records = [
        _role_equation_record(role_record=record, models=models)
        for record in fixed["records"]
    ]
    role_records.sort(key=lambda item: item["role"])
    finemet_reference = _finemet_reference_record(models)
    af_model_id = "material_loss_model:gaotune_af_volumetriclosses_default_0_ranges_0:298ab5e4f2e8"
    if af_model_id not in models:
        raise ValueError("The selected AF Steinmetz model is unavailable.")
    scalar_references = [
        _scalar_steinmetz_reference_record(
            model=models[af_model_id],
            reference_id="af_selected_model_scalar_steinmetz_reference",
            material_name="AF",
        ),
        _scalar_steinmetz_reference_record(
            model=models[finemet_reference["model_id"]],
            reference_id="finemet_selected_model_scalar_steinmetz_reference",
            material_name="Finemet",
        ),
    ]
    selected_references = scalar_references + [finemet_reference]
    multiplier = _multiplier_audit(root)
    equation_pass_count = sum(item["status"] == "passed" for item in role_records)
    unavailable_count = sum(item["status"].startswith("not_applicable") for item in role_records)
    selected_methods = sorted({item["method"] for item in role_records if item["method"]} | {"igse"})
    selected_model_ids = sorted(
        {item["model_id"] for item in role_records if item["model_id"]}
        | {finemet_reference["model_id"]}
    )
    payload = {
        "contract_version": STEP18_MODEL_EQUATION_AUDIT_VERSION,
        "recorded_date": "2026-07-27",
        "scope": "step18d_independent_equations_units_ranges_and_multipliers",
        "generation_command": "python scripts/audit_openmagnetics_step18_model_equations.py",
        "inputs": {
            "fixed_hardware": {
                "path": fixed_path.relative_to(root).as_posix(),
                "sha256": _sha256(fixed_path),
            },
            "normalized_v2_materials": {
                "path": materials_path.relative_to(root).as_posix(),
                "sha256": _sha256(materials_path),
            },
            "pinned_mkf_commit": PINNED_MKF_COMMIT,
        },
        "tolerance": {
            "relative": RELATIVE_TOLERANCE,
            "absolute_floor": ABSOLUTE_FLOOR,
            "waveform_policy": "use frozen samples exactly; no post-result tolerance widening",
        },
        "selected_methods": selected_methods,
        "selected_model_ids": selected_model_ids,
        "role_records": role_records,
        "selected_model_references": selected_references,
        "non_selected_method_references": _prior_method_evidence(root),
        "multiplier_audit": multiplier,
        "summary": {
            "role_count": len(role_records),
            "equation_pass_count": equation_pass_count,
            "fixed_hardware_not_reconstructable_count": unavailable_count,
            "selected_method_count": len(selected_methods),
            "selected_model_count": len(selected_model_ids),
            "independent_reference_fail_count": sum(item["status"] == "failed" for item in role_records),
            "range_behavior_correction_count": sum(
                bool((item.get("range_check") or {}).get("kernel_behavior_corrected_in_step18d"))
                for item in role_records
            ),
            "acceptance_passed": (
                equation_pass_count == len(_FIXED_AUDIT_ROLES)
                and unavailable_count == len(_EXPECTED_UNRECONSTRUCTABLE_ROLES)
                and all(item["passed"] for item in selected_references)
                and multiplier["passed"]
            ),
        },
        "integrity": {
            "independent_reference_calls_production_evaluator": False,
            "production_evaluator_called_once_per_comparison": True,
            "generic_or_duplicate_x1000_present": False,
            "production_loader_changed": False,
            "production_cache_changed": False,
            "default_backend_changed": False,
            "candidate_selection_run": False,
            "ranking_run": False,
        },
    }
    validate_step18_model_equation_audit(payload)
    return payload


def write_step18_model_equation_audit(path: str | Path, payload: Mapping[str, Any]) -> None:
    validate_step18_model_equation_audit(payload)
    Path(path).write_text(
        json.dumps(payload, sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "ABSOLUTE_FLOOR",
    "RELATIVE_TOLERANCE",
    "STEP18_MODEL_EQUATION_AUDIT_VERSION",
    "build_step18_model_equation_audit",
    "validate_step18_model_equation_audit",
    "write_step18_model_equation_audit",
]
