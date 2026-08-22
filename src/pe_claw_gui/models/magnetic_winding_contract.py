"""Unit-explicit, independently reproducible magnetic-winding evidence."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from types import MappingProxyType
from typing import Any, Mapping


WINDING_ELECTRICAL_EVIDENCE_VERSION = "magnetic-winding-electrical-evidence-v1"
_COPPER_RESISTIVITY_25C_OHM_M = 1.724e-8
_RELATIVE_TOLERANCE = 1.0e-9
_RESISTIVITY_COMPATIBILITY_TOLERANCE = 1.0e-3


@dataclass(frozen=True)
class WindingElectricalEvidence:
    """Evidence needed to reproduce one transformer's winding copper loss.

    ``conducting_area_m2`` is the copper area of one selected wire record.
    ``total_conductor_length_m`` is the series length of one parallel path;
    ``parallel_winding_count`` is therefore applied exactly once in Rdc.
    AC copper loss is the incremental loss above the temperature-adjusted DC
    loss, so ``dc_copper_loss_w + ac_copper_loss_w`` equals the total.
    """

    wire_id: str
    wire_name: str
    source_wire_record: Mapping[str, Any]
    conducting_area_m2: float
    area_basis: str
    strand_diameter_m: float
    strand_count: int
    parallel_winding_count: int
    turns: int
    mean_length_per_turn_m: float
    total_conductor_length_m: float
    rdc_25c_ohm: float
    resistance_temperature_c: float
    resistance_temperature_factor: float
    rac_multiplier: float
    rms_current_a: float
    dc_copper_loss_w: float
    ac_copper_loss_w: float
    total_copper_loss_w: float
    fill_area_m2: float
    contract_version: str = WINDING_ELECTRICAL_EVIDENCE_VERSION

    def __post_init__(self) -> None:
        for name in ("wire_id", "wire_name", "area_basis"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if self.contract_version != WINDING_ELECTRICAL_EVIDENCE_VERSION:
            raise ValueError("Unsupported winding evidence contract_version.")
        object.__setattr__(self, "source_wire_record", _freeze_json_mapping(self.source_wire_record))
        for name in ("strand_count", "parallel_winding_count", "turns"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        for name in (
            "conducting_area_m2", "strand_diameter_m", "mean_length_per_turn_m",
            "total_conductor_length_m", "rdc_25c_ohm", "resistance_temperature_factor",
            "rac_multiplier", "rms_current_a", "dc_copper_loss_w", "total_copper_loss_w",
            "fill_area_m2",
        ):
            value = _finite_number(getattr(self, name), name)
            if value <= 0.0:
                raise ValueError(f"{name} must be positive.")
            object.__setattr__(self, name, value)
        object.__setattr__(
            self,
            "resistance_temperature_c",
            _finite_number(self.resistance_temperature_c, "resistance_temperature_c"),
        )
        ac_loss = _finite_number(self.ac_copper_loss_w, "ac_copper_loss_w")
        if ac_loss < 0.0:
            raise ValueError("ac_copper_loss_w must be nonnegative.")
        object.__setattr__(self, "ac_copper_loss_w", ac_loss)
        if self.rac_multiplier < 1.0:
            raise ValueError("rac_multiplier must be at least 1.0.")
        self._validate_reproducibility()

    def _validate_reproducibility(self) -> None:
        expected_length = self.mean_length_per_turn_m * self.turns
        expected_rdc = (
            _COPPER_RESISTIVITY_25C_OHM_M
            * expected_length
            / (self.conducting_area_m2 * self.parallel_winding_count)
        )
        expected_dc_loss = (
            self.rms_current_a**2
            * self.rdc_25c_ohm
            * self.resistance_temperature_factor
        )
        expected_total_loss = expected_dc_loss * self.rac_multiplier
        checks = (
            (self.total_conductor_length_m, expected_length, "total_conductor_length_m", _RELATIVE_TOLERANCE),
            (self.rdc_25c_ohm, expected_rdc, "rdc_25c_ohm", _RESISTIVITY_COMPATIBILITY_TOLERANCE),
            (self.dc_copper_loss_w, expected_dc_loss, "dc_copper_loss_w", _RELATIVE_TOLERANCE),
            (self.total_copper_loss_w, expected_total_loss, "total_copper_loss_w", _RELATIVE_TOLERANCE),
            (self.dc_copper_loss_w + self.ac_copper_loss_w, self.total_copper_loss_w, "loss decomposition", _RELATIVE_TOLERANCE),
        )
        for actual, expected, label, tolerance in checks:
            if _relative_error(actual, expected) > tolerance:
                raise ValueError(f"{label} is not independently reproducible from the winding evidence.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "wire_id": self.wire_id,
            "wire_name": self.wire_name,
            "source_wire_record": _thaw_json(self.source_wire_record),
            "conducting_area_m2": self.conducting_area_m2,
            "area_basis": self.area_basis,
            "strand_diameter_m": self.strand_diameter_m,
            "strand_count": self.strand_count,
            "parallel_winding_count": self.parallel_winding_count,
            "turns": self.turns,
            "mean_length_per_turn_m": self.mean_length_per_turn_m,
            "total_conductor_length_m": self.total_conductor_length_m,
            "rdc_25c_ohm": self.rdc_25c_ohm,
            "resistance_temperature_c": self.resistance_temperature_c,
            "resistance_temperature_factor": self.resistance_temperature_factor,
            "rac_multiplier": self.rac_multiplier,
            "rms_current_a": self.rms_current_a,
            "dc_copper_loss_w": self.dc_copper_loss_w,
            "ac_copper_loss_w": self.ac_copper_loss_w,
            "total_copper_loss_w": self.total_copper_loss_w,
            "fill_area_m2": self.fill_area_m2,
            "contract_version": self.contract_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WindingElectricalEvidence":
        expected = set(cls.__dataclass_fields__)
        if set(payload) != expected:
            missing = sorted(expected - set(payload))
            unknown = sorted(set(payload) - expected)
            raise ValueError(f"WindingElectricalEvidence fields mismatch; missing={missing}, unknown={unknown}.")
        return cls(**{key: payload[key] for key in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, allow_nan=False,
            ensure_ascii=True, separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, payload: str) -> "WindingElectricalEvidence":
        decoded = json.loads(payload)
        if not isinstance(decoded, dict):
            raise ValueError("WindingElectricalEvidence JSON payload must be an object.")
        return cls.from_dict(decoded)


def _relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-18)


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _freeze_json_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not value:
        raise ValueError("source_wire_record must be a non-empty mapping.")
    return MappingProxyType({str(key): _freeze_json(item) for key, item in sorted(value.items())})


def _freeze_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("source_wire_record cannot contain NaN or Infinity.")
        return value
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in sorted(value.items())})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    raise ValueError(f"source_wire_record contains unsupported value {type(value).__name__}.")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value
