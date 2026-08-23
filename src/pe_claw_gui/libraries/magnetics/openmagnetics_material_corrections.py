"""Apply verified, source-fingerprinted OpenMagnetics material corrections."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any


CORRECTION_MANIFEST_NAME = "material_loss_corrections.json"
CORRECTION_CONTRACT_VERSION = "openmagnetics_verified_material_loss_corrections_v1"
CORRECTION_APPLICATION_CONTRACT_VERSION = "openmagnetics_material_loss_correction_application_v1"
CORRECTION_TYPE = "mass_fitted_k_to_volumetric_k"
CORRECTION_UPSTREAM_COMMIT = "7d028683e14fe6a7657667edd2eb4ddf4eeaadd6"
_DEFAULT_MANIFEST = Path(__file__).resolve().parent / "openmagnetics_data" / CORRECTION_MANIFEST_NAME
_MANIFEST_KEYS = {
    "contract_version",
    "correction_set_id",
    "correction_type",
    "equation",
    "upstream_commit",
    "upstream_commit_date",
    "upstream_project",
    "upstream_reference",
    "corrections",
}
_CORRECTION_KEYS = {
    "correction_id",
    "manufacturer",
    "material_name",
    "source_file",
    "expected_source_record_sha256",
    "method",
    "scope",
    "model_index",
    "range_index",
    "minimum_frequency_hz",
    "maximum_frequency_hz",
    "expected_density_kg_per_m3",
    "expected_original_k",
    "corrected_k",
    "expected_alpha",
    "expected_beta",
    "multiplier",
    "multiplier_basis",
    "upstream_source_reference",
}


class VerifiedMaterialCorrectionError(ValueError):
    """Raised when a verified correction cannot be applied without ambiguity."""


@dataclass(frozen=True)
class VerifiedMaterialCorrectionSet:
    """Strict packaged correction manifest plus its immutable identity."""

    correction_set_id: str
    correction_type: str
    equation: str
    upstream_project: str
    upstream_commit: str
    upstream_commit_date: str
    upstream_reference: str
    manifest_path: str
    manifest_sha256: str
    corrections: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class MaterialLossCorrectionApplication:
    """One deterministic application bound to an exact source model range."""

    correction_id: str
    status: str
    correction_type: str
    manufacturer: str
    material_name: str
    source_file: str
    source_record_index: int
    source_record_sha256: str
    source_reference: str
    method: str
    scope: str
    model_index: int
    range_index: int
    density_kg_per_m3: float
    input_k: float
    expected_original_k: float
    corrected_k: float
    multiplier: float
    multiplier_basis: str
    upstream_project: str
    upstream_commit: str
    upstream_reference: str
    correction_manifest_sha256: str
    material_id: str | None = None
    model_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_version": CORRECTION_APPLICATION_CONTRACT_VERSION,
            "correction_id": self.correction_id,
            "status": self.status,
            "correction_type": self.correction_type,
            "manufacturer": self.manufacturer,
            "material_name": self.material_name,
            "source_file": self.source_file,
            "source_record_index": self.source_record_index,
            "source_record_sha256": self.source_record_sha256,
            "source_reference": self.source_reference,
            "method": self.method,
            "scope": self.scope,
            "model_index": self.model_index,
            "range_index": self.range_index,
            "density_kg_per_m3": self.density_kg_per_m3,
            "input_k": self.input_k,
            "expected_original_k": self.expected_original_k,
            "corrected_k": self.corrected_k,
            "multiplier": self.multiplier,
            "multiplier_basis": self.multiplier_basis,
            "upstream_project": self.upstream_project,
            "upstream_commit": self.upstream_commit,
            "upstream_reference": self.upstream_reference,
            "correction_manifest_sha256": self.correction_manifest_sha256,
            "material_id": self.material_id,
            "model_id": self.model_id,
        }


def get_material_loss_correction_manifest_path() -> Path:
    """Return the packaged verified correction manifest."""

    return _DEFAULT_MANIFEST


@lru_cache(maxsize=8)
def load_verified_material_loss_corrections(
    manifest_path: str | Path | None = None,
) -> VerifiedMaterialCorrectionSet:
    """Load and strictly validate one correction manifest."""

    path = Path(manifest_path or _DEFAULT_MANIFEST).resolve()
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"), parse_constant=_reject_json_constant)
    if not isinstance(payload, dict) or set(payload) != _MANIFEST_KEYS:
        raise VerifiedMaterialCorrectionError("Correction manifest has missing or unknown top-level fields.")
    if payload["contract_version"] != CORRECTION_CONTRACT_VERSION:
        raise VerifiedMaterialCorrectionError("Correction manifest contract version is unsupported.")
    if payload["correction_type"] != CORRECTION_TYPE:
        raise VerifiedMaterialCorrectionError("Correction manifest correction_type is unsupported.")
    if payload["upstream_commit"] != CORRECTION_UPSTREAM_COMMIT:
        raise VerifiedMaterialCorrectionError("Correction manifest upstream commit is not the reviewed MAS fix.")
    corrections = payload["corrections"]
    if not isinstance(corrections, list) or not corrections:
        raise VerifiedMaterialCorrectionError("Correction manifest must contain correction records.")
    normalized: list[Mapping[str, object]] = []
    ids: set[str] = set()
    for index, item in enumerate(corrections):
        normalized_item = _validate_correction(item, index)
        correction_id = str(normalized_item["correction_id"])
        if correction_id in ids:
            raise VerifiedMaterialCorrectionError(f"Duplicate correction_id: {correction_id}")
        ids.add(correction_id)
        normalized.append(normalized_item)
    normalized.sort(key=lambda item: str(item["correction_id"]))
    return VerifiedMaterialCorrectionSet(
        correction_set_id=_text(payload["correction_set_id"], "correction_set_id"),
        correction_type=_text(payload["correction_type"], "correction_type"),
        equation=_text(payload["equation"], "equation"),
        upstream_project=_text(payload["upstream_project"], "upstream_project"),
        upstream_commit=_sha(payload["upstream_commit"], "upstream_commit"),
        upstream_commit_date=_text(payload["upstream_commit_date"], "upstream_commit_date"),
        upstream_reference=_text(payload["upstream_reference"], "upstream_reference"),
        manifest_path=path.as_posix(),
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        corrections=tuple(normalized),
    )


def apply_verified_material_loss_corrections(
    record: Mapping[str, Any],
    *,
    source_file: str,
    source_record_index: int,
    correction_set: VerifiedMaterialCorrectionSet | None = None,
) -> tuple[dict[str, Any], tuple[MaterialLossCorrectionApplication, ...]]:
    """Return a corrected copy and exact audit applications for one record."""

    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping.")
    if isinstance(source_record_index, bool) or not isinstance(source_record_index, int) or source_record_index < 0:
        raise ValueError("source_record_index must be a nonnegative integer.")
    source_file = Path(_text(source_file, "source_file")).name
    corrections = correction_set or load_verified_material_loss_corrections()
    material_name = str(record.get("name") or "").strip()
    manufacturer = _manufacturer_name(record)
    targets = [
        item
        for item in corrections.corrections
        if item["source_file"] == source_file
        and item["manufacturer"] == manufacturer
        and item["material_name"] == material_name
    ]
    corrected = deepcopy(dict(record))
    if not targets:
        return corrected, ()
    record_sha256 = canonical_record_sha256(record)
    density = _finite(record.get("density"), "density")
    applications: list[MaterialLossCorrectionApplication] = []
    for target in targets:
        range_data = _resolve_target_range(corrected, target)
        _require_equal(density, target["expected_density_kg_per_m3"], "density")
        _require_equal(range_data.get("minimumFrequency"), target["minimum_frequency_hz"], "minimumFrequency")
        _require_equal(range_data.get("maximumFrequency"), target["maximum_frequency_hz"], "maximumFrequency")
        _require_equal(range_data.get("alpha"), target["expected_alpha"], "alpha")
        _require_equal(range_data.get("beta"), target["expected_beta"], "beta")
        input_k = _finite(range_data.get("k"), "k")
        expected_k = float(target["expected_original_k"])
        corrected_k = float(target["corrected_k"])
        if input_k == expected_k:
            if record_sha256 != target["expected_source_record_sha256"]:
                raise VerifiedMaterialCorrectionError(
                    f"{target['correction_id']} old coefficient matched but source record SHA-256 did not."
                )
            status = "applied"
            range_data["k"] = corrected_k
        elif input_k == corrected_k:
            status = "already_corrected"
        else:
            raise VerifiedMaterialCorrectionError(
                f"{target['correction_id']} k fingerprint mismatch: {input_k!r}."
            )
        applications.append(
            MaterialLossCorrectionApplication(
                correction_id=str(target["correction_id"]),
                status=status,
                correction_type=corrections.correction_type,
                manufacturer=manufacturer,
                material_name=material_name,
                source_file=source_file,
                source_record_index=source_record_index,
                source_record_sha256=record_sha256,
                source_reference=_source_reference(target),
                method=str(target["method"]),
                scope=str(target["scope"]),
                model_index=int(target["model_index"]),
                range_index=int(target["range_index"]),
                density_kg_per_m3=density,
                input_k=input_k,
                expected_original_k=expected_k,
                corrected_k=corrected_k,
                multiplier=float(target["multiplier"]),
                multiplier_basis=str(target["multiplier_basis"]),
                upstream_project=corrections.upstream_project,
                upstream_commit=corrections.upstream_commit,
                upstream_reference=str(target["upstream_source_reference"]),
                correction_manifest_sha256=corrections.manifest_sha256,
            )
        )
    applications.sort(key=lambda item: item.correction_id)
    return corrected, tuple(applications)


def verify_material_loss_correction_coverage(
    applications: Sequence[MaterialLossCorrectionApplication],
    correction_set: VerifiedMaterialCorrectionSet | None = None,
) -> None:
    """Require every verified target exactly once in a full inventory build."""

    corrections = correction_set or load_verified_material_loss_corrections()
    expected = {str(item["correction_id"]) for item in corrections.corrections}
    counts = Counter(item.correction_id for item in applications)
    missing = sorted(expected - set(counts))
    duplicates = sorted(correction_id for correction_id, count in counts.items() if count != 1)
    unexpected = sorted(set(counts) - expected)
    invalid = sorted(item.correction_id for item in applications if item.status not in {"applied", "already_corrected"})
    if missing or duplicates or unexpected or invalid:
        raise VerifiedMaterialCorrectionError(
            "Correction coverage failed: "
            f"missing={missing}, duplicates={duplicates}, unexpected={unexpected}, invalid={invalid}."
        )


def canonical_record_sha256(record: Mapping[str, Any]) -> str:
    """Return the same deterministic source-record hash used by normalized-v2."""

    canonical = json.dumps(record, sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_correction(value: object, index: int) -> Mapping[str, object]:
    if not isinstance(value, dict) or set(value) != _CORRECTION_KEYS:
        raise VerifiedMaterialCorrectionError(f"Correction {index} has missing or unknown fields.")
    item = dict(value)
    for key in (
        "correction_id",
        "manufacturer",
        "material_name",
        "source_file",
        "method",
        "scope",
        "multiplier_basis",
        "upstream_source_reference",
    ):
        item[key] = _text(item[key], f"corrections[{index}].{key}")
    item["expected_source_record_sha256"] = _sha(
        item["expected_source_record_sha256"], f"corrections[{index}].expected_source_record_sha256"
    )
    for key in ("model_index", "range_index"):
        raw = item[key]
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
            raise VerifiedMaterialCorrectionError(f"corrections[{index}].{key} must be nonnegative integer.")
    for key in (
        "minimum_frequency_hz",
        "maximum_frequency_hz",
        "expected_density_kg_per_m3",
        "expected_original_k",
        "corrected_k",
        "expected_alpha",
        "expected_beta",
        "multiplier",
    ):
        item[key] = _finite(item[key], f"corrections[{index}].{key}")
    if item["method"] != "steinmetz" or item["scope"] != "default":
        raise VerifiedMaterialCorrectionError("Only reviewed default-scope Steinmetz corrections are supported.")
    if float(item["minimum_frequency_hz"]) < 0 or float(item["maximum_frequency_hz"]) <= float(item["minimum_frequency_hz"]):
        raise VerifiedMaterialCorrectionError("Correction frequency range is invalid.")
    if float(item["expected_density_kg_per_m3"]) <= 0 or float(item["expected_original_k"]) <= 0:
        raise VerifiedMaterialCorrectionError("Correction density and old k must be positive.")
    if float(item["corrected_k"]) <= 0 or float(item["multiplier"]) <= 0:
        raise VerifiedMaterialCorrectionError("Correction new k and multiplier must be positive.")
    expected_corrected = float(item["expected_original_k"]) * float(item["expected_density_kg_per_m3"])
    if not math.isclose(float(item["corrected_k"]), expected_corrected, rel_tol=1e-14, abs_tol=0.0):
        raise VerifiedMaterialCorrectionError("corrected_k does not equal old k times density.")
    if float(item["multiplier"]) != float(item["expected_density_kg_per_m3"]):
        raise VerifiedMaterialCorrectionError("multiplier must equal the reviewed material density.")
    return MappingProxyType(item)


def _resolve_target_range(record: dict[str, Any], target: Mapping[str, object]) -> dict[str, Any]:
    losses = record.get("volumetricLosses")
    if not isinstance(losses, dict):
        raise VerifiedMaterialCorrectionError(f"{target['correction_id']} volumetricLosses is missing.")
    methods = losses.get(str(target["scope"]))
    if not isinstance(methods, list) or int(target["model_index"]) >= len(methods):
        raise VerifiedMaterialCorrectionError(f"{target['correction_id']} model target is missing.")
    method = methods[int(target["model_index"])]
    if not isinstance(method, dict) or method.get("method") != target["method"]:
        raise VerifiedMaterialCorrectionError(f"{target['correction_id']} method fingerprint mismatch.")
    ranges = method.get("ranges")
    if not isinstance(ranges, list) or int(target["range_index"]) >= len(ranges):
        raise VerifiedMaterialCorrectionError(f"{target['correction_id']} range target is missing.")
    range_data = ranges[int(target["range_index"])]
    if not isinstance(range_data, dict):
        raise VerifiedMaterialCorrectionError(f"{target['correction_id']} range target is not an object.")
    return range_data


def _source_reference(target: Mapping[str, object]) -> str:
    return (
        f"$.volumetricLosses.{target['scope']}[{target['model_index']}]"
        f".ranges[{target['range_index']}]"
    )


def _manufacturer_name(record: Mapping[str, Any]) -> str:
    value = record.get("manufacturer") or record.get("manufacturerInfo")
    if isinstance(value, Mapping):
        value = value.get("name")
    return str(value or "unknown").strip()


def _require_equal(actual: object, expected: object, field_name: str) -> None:
    actual_value = _finite(actual, field_name)
    expected_value = _finite(expected, field_name)
    if actual_value != expected_value:
        raise VerifiedMaterialCorrectionError(
            f"{field_name} fingerprint mismatch: actual={actual_value!r}, expected={expected_value!r}."
        )


def _finite(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise VerifiedMaterialCorrectionError(f"{field_name} must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise VerifiedMaterialCorrectionError(f"{field_name} must be finite.")
    return result


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise VerifiedMaterialCorrectionError(f"{field_name} must be a nonempty string.")
    return value.strip()


def _sha(value: object, field_name: str) -> str:
    text = _text(value, field_name).lower()
    if len(text) not in {40, 64} or any(character not in "0123456789abcdef" for character in text):
        raise VerifiedMaterialCorrectionError(f"{field_name} must be a hexadecimal Git or SHA-256 value.")
    return text


def _reject_json_constant(value: str) -> None:
    raise VerifiedMaterialCorrectionError(f"Non-finite JSON number is not allowed: {value}")


__all__ = [
    "CORRECTION_APPLICATION_CONTRACT_VERSION",
    "CORRECTION_CONTRACT_VERSION",
    "CORRECTION_MANIFEST_NAME",
    "CORRECTION_TYPE",
    "CORRECTION_UPSTREAM_COMMIT",
    "MaterialLossCorrectionApplication",
    "VerifiedMaterialCorrectionError",
    "VerifiedMaterialCorrectionSet",
    "apply_verified_material_loss_corrections",
    "canonical_record_sha256",
    "get_material_loss_correction_manifest_path",
    "load_verified_material_loss_corrections",
    "verify_material_loss_correction_coverage",
]
