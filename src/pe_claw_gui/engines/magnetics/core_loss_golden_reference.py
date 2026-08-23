"""Golden references and physical checks for the Step 13 loss audit.

This module is intentionally an audit boundary.  It calls the existing loss
evaluators and never changes model selection, production routing, or cached
material data.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any, Mapping, Sequence

from ...models.magnetic_loss_contract import (
    CoreLossExcitation,
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
)


GOLDEN_REFERENCE_CONTRACT_VERSION = "openmagnetics-step13-golden-reference-v1"
PHYSICAL_VALIDATION_CONTRACT_VERSION = "openmagnetics-step13-physical-validation-v1"
DEFAULT_RELATIVE_TOLERANCE = 0.01
EQUATION_RELATIVE_TOLERANCE = 1.0e-9


class _JsonMixin:
    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, allow_nan=False, ensure_ascii=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, payload: str):
        value = json.loads(payload)
        if not isinstance(value, dict):
            raise ValueError(f"{cls.__name__} JSON payload must be an object")
        return cls.from_dict(value)


@dataclass(frozen=True)
class CoreLossGoldenReference(_JsonMixin):
    """One complete, reproducible model/excitation/result reference."""

    reference_id: str
    source_project: str
    source_version: str
    source_commit: str
    material_id: str
    material_name: str
    material_family: str
    material_composition: str
    model_id: str
    model_method: str
    model_scope: str
    excitation: CoreLossExcitation
    expected_result: CoreLossResult
    tolerance: Mapping[str, float]
    expected_strategy_differences: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "reference_id", "source_project", "source_version", "source_commit",
            "material_id", "material_name", "material_family",
            "material_composition", "model_id", "model_method", "model_scope",
        ):
            _text(getattr(self, name), name)
        if len(self.source_commit) != 40 or any(c not in "0123456789abcdefABCDEF" for c in self.source_commit):
            raise ValueError("source_commit must be a full hexadecimal commit")
        if not isinstance(self.excitation, CoreLossExcitation):
            raise ValueError("excitation must be CoreLossExcitation")
        if not isinstance(self.expected_result, CoreLossResult):
            raise ValueError("expected_result must be CoreLossResult")
        tolerance = {str(k): _nonnegative(v, f"tolerance[{k}]") for k, v in self.tolerance.items()}
        if not tolerance:
            raise ValueError("tolerance must not be empty")
        object.__setattr__(self, "tolerance", _freeze_mapping(tolerance))
        strategies = tuple(self.expected_strategy_differences)
        if not all(isinstance(v, str) and v.strip() for v in strategies):
            raise ValueError("expected_strategy_differences must contain text")
        object.__setattr__(self, "expected_strategy_differences", strategies)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": GOLDEN_REFERENCE_CONTRACT_VERSION,
            "reference_id": self.reference_id,
            "source_project": self.source_project,
            "source_version": self.source_version,
            "source_commit": self.source_commit,
            "material_id": self.material_id,
            "material_name": self.material_name,
            "material_family": self.material_family,
            "material_composition": self.material_composition,
            "model_id": self.model_id,
            "model_method": self.model_method,
            "model_scope": self.model_scope,
            "excitation": self.excitation.to_dict(),
            "expected_result": self.expected_result.to_dict(),
            "tolerance": dict(self.tolerance),
            "expected_strategy_differences": list(self.expected_strategy_differences),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CoreLossGoldenReference":
        expected = {
            "contract_version", "reference_id", "source_project", "source_version",
            "source_commit", "material_id", "material_name", "material_family",
            "material_composition", "model_id", "model_method", "model_scope",
            "excitation", "expected_result", "tolerance", "expected_strategy_differences",
        }
        if set(payload) != expected or payload["contract_version"] != GOLDEN_REFERENCE_CONTRACT_VERSION:
            raise ValueError("Invalid or unknown golden-reference fields")
        if not isinstance(payload["tolerance"], dict) or not isinstance(payload["expected_strategy_differences"], list):
            raise ValueError("Golden tolerance and strategy fields have invalid types")
        return cls(
            reference_id=payload["reference_id"], source_project=payload["source_project"],
            source_version=payload["source_version"], source_commit=payload["source_commit"],
            material_id=payload["material_id"], material_name=payload["material_name"],
            material_family=payload["material_family"], material_composition=payload["material_composition"],
            model_id=payload["model_id"], model_method=payload["model_method"], model_scope=payload["model_scope"],
            excitation=CoreLossExcitation.from_dict(payload["excitation"]),
            expected_result=CoreLossResult.from_dict(payload["expected_result"]),
            tolerance=payload["tolerance"], expected_strategy_differences=tuple(payload["expected_strategy_differences"]),
        )


@dataclass(frozen=True)
class PhysicalValidationIssue(_JsonMixin):
    code: str
    severity: str
    message: str
    relative_error: float | None = None

    def __post_init__(self) -> None:
        _text(self.code, "code")
        if self.severity not in {"error", "warning", "info"}:
            raise ValueError("severity must be error, warning, or info")
        _text(self.message, "message")
        if self.relative_error is not None:
            _nonnegative(self.relative_error, "relative_error")

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "severity": self.severity, "message": self.message, "relative_error": self.relative_error}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PhysicalValidationIssue":
        if set(payload) != {"code", "severity", "message", "relative_error"}:
            raise ValueError("Invalid physical validation issue fields")
        return cls(**payload)


@dataclass(frozen=True)
class PhysicalValidationReport(_JsonMixin):
    """Deterministic audit output for one result."""

    contract_version: str
    reference_id: str
    passed: bool
    checks: Mapping[str, Any]
    issues: tuple[PhysicalValidationIssue, ...]

    def __post_init__(self) -> None:
        if self.contract_version != PHYSICAL_VALIDATION_CONTRACT_VERSION:
            raise ValueError("Unsupported physical-validation contract")
        _text(self.reference_id, "reference_id")
        object.__setattr__(self, "checks", _freeze_mapping(self.checks))
        object.__setattr__(self, "issues", tuple(self.issues))
        if not all(isinstance(item, PhysicalValidationIssue) for item in self.issues):
            raise ValueError("issues must contain PhysicalValidationIssue values")

    def to_dict(self) -> dict[str, Any]:
        return {"contract_version": self.contract_version, "reference_id": self.reference_id, "passed": self.passed, "checks": dict(self.checks), "issues": [item.to_dict() for item in self.issues]}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PhysicalValidationReport":
        expected = {"contract_version", "reference_id", "passed", "checks", "issues"}
        if set(payload) != expected or not isinstance(payload["issues"], list):
            raise ValueError("Invalid physical validation report fields")
        return cls(payload["contract_version"], payload["reference_id"], payload["passed"], payload["checks"], tuple(PhysicalValidationIssue.from_dict(item) for item in payload["issues"]))


def validate_core_loss_result(
    result: CoreLossResult,
    *,
    excitation: CoreLossExcitation | None = None,
    reference_id: str = "runtime",
    tolerance: float = DEFAULT_RELATIVE_TOLERANCE,
) -> PhysicalValidationReport:
    """Check units, finite values, identities, ranges, and provenance."""

    issues: list[PhysicalValidationIssue] = []
    checks: dict[str, Any] = {}
    if not isinstance(result, CoreLossResult):
        raise TypeError("result must be CoreLossResult")
    tolerance = _nonnegative(tolerance, "tolerance")
    for field in ("core_loss_w", "volumetric_loss_w_per_m3", "mass_loss_w_per_kg"):
        value = getattr(result, field)
        checks[f"finite_{field}"] = value is None or math.isfinite(value)
        if value is not None and (not math.isfinite(value) or value < 0.0):
            issues.append(PhysicalValidationIssue("nonfinite_or_negative_loss", "error", f"{field} is not finite and nonnegative"))
    valid = result.validity_status in {CoreLossValidityStatus.VALID, CoreLossValidityStatus.VALID_INTERPOLATED}
    checks["validity_status"] = result.validity_status.value
    if valid and result.core_loss_w is None and result.volumetric_loss_w_per_m3 is None and result.mass_loss_w_per_kg is None:
        issues.append(PhysicalValidationIssue("valid_status_without_loss", "error", "valid result has no loss quantity"))
    if not valid and result.core_loss_w is not None and result.validity_status in {CoreLossValidityStatus.LOSS_DATA_NOT_AVAILABLE, CoreLossValidityStatus.INVALID_EXCITATION, CoreLossValidityStatus.MODEL_NOT_SUPPORTED}:
        issues.append(PhysicalValidationIssue("unavailable_with_total_loss", "error", "unavailable result contains total watts"))
    if result.core_loss_w is not None and result.volumetric_loss_w_per_m3 is not None and result.effective_volume_m3 is not None:
        error = _relative_error(result.core_loss_w, result.volumetric_loss_w_per_m3 * result.effective_volume_m3)
        checks["p_vs_pv_ve_relative_error"] = error
        if error > tolerance:
            issues.append(PhysicalValidationIssue("volume_identity_mismatch", "error", "Pcore != Pv * Ve", error))
    if result.core_loss_w is not None and result.mass_loss_w_per_kg is not None and result.core_mass_kg is not None:
        error = _relative_error(result.core_loss_w, result.mass_loss_w_per_kg * result.core_mass_kg)
        checks["p_vs_pm_mass_relative_error"] = error
        if error > tolerance:
            issues.append(PhysicalValidationIssue("mass_identity_mismatch", "error", "Pcore != Pmass * mass", error))
    checks["range_consistent"] = not (result.validity_status in {CoreLossValidityStatus.VALID, CoreLossValidityStatus.VALID_INTERPOLATED} and result.extrapolated)
    if result.validity_status in {CoreLossValidityStatus.VALID, CoreLossValidityStatus.VALID_INTERPOLATED} and result.extrapolated:
        issues.append(PhysicalValidationIssue("silent_extrapolation", "error", "valid result is marked extrapolated"))
    checks["provenance_present"] = bool(result.source_provenance.source_project and result.source_provenance.source_file)
    if not checks["provenance_present"]:
        issues.append(PhysicalValidationIssue("missing_provenance", "error", "loss result has incomplete provenance"))
    if excitation is not None:
        if result.frequency_hz != excitation.frequency_hz:
            issues.append(PhysicalValidationIssue("frequency_mismatch", "error", "result frequency differs from excitation"))
        checks["excitation_defined"] = len(excitation.flux_waveform_t) >= 2
    checks["model_identity_present"] = (not valid) or bool(result.selected_model_id and result.method_used)
    if valid and not checks["model_identity_present"]:
        issues.append(PhysicalValidationIssue("missing_model_identity", "error", "valid result lacks model identity"))
    return PhysicalValidationReport(PHYSICAL_VALIDATION_CONTRACT_VERSION, reference_id, not any(i.severity == "error" for i in issues), checks, tuple(issues))


def validate_golden_reference(reference: CoreLossGoldenReference, *, tolerance: float | None = None) -> PhysicalValidationReport:
    """Validate a fixture's physical result and reference metadata."""

    limit = reference.tolerance.get("relative", DEFAULT_RELATIVE_TOLERANCE) if tolerance is None else tolerance
    report = validate_core_loss_result(reference.expected_result, excitation=reference.excitation, reference_id=reference.reference_id, tolerance=limit)
    issues = list(report.issues)
    if reference.expected_result.selected_model_id not in {None, reference.model_id}:
        issues.append(PhysicalValidationIssue("model_identity_mismatch", "error", "expected result model does not match fixture model"))
    return PhysicalValidationReport(report.contract_version, report.reference_id, not any(i.severity == "error" for i in issues), report.checks, tuple(issues))


def _relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-18)


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return value


def _nonnegative(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    # JSON round-trip is a compact immutable validation/canonicalization step.
    encoded = json.dumps(dict(value), sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":"))
    return json.loads(encoded)


__all__ = [
    "CoreLossGoldenReference", "PhysicalValidationIssue", "PhysicalValidationReport",
    "GOLDEN_REFERENCE_CONTRACT_VERSION", "PHYSICAL_VALIDATION_CONTRACT_VERSION",
    "DEFAULT_RELATIVE_TOLERANCE", "EQUATION_RELATIVE_TOLERANCE",
    "validate_core_loss_result", "validate_golden_reference",
]
