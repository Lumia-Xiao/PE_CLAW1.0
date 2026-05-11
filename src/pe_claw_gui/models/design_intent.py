"""System-level design intent model for AI-assisted design."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


IMPORTANT_FIELDS = (
    "vin_nom_v",
    "vout_v",
    "pout_w",
)


@dataclass(frozen=True)
class DesignIntent:
    """System-level converter requirements used above the physics pipeline."""

    converter_family: str | None = None
    topology_hint: str | None = None
    vin_min_v: float | None = None
    vin_nom_v: float | None = None
    vin_max_v: float | None = None
    vout_v: float | None = None
    iout_a: float | None = None
    pout_w: float | None = None
    fsw_hz: float | None = None
    ripple_voltage_ratio: float | None = None
    ripple_current_pp_a: float | None = None
    isolation_required: bool | None = None
    bidirectional: bool | None = None
    load_type: str | None = None
    priorities: tuple[str, ...] = ()
    constraints: dict[str, object] = field(default_factory=dict)
    missing_fields: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "DesignIntent":
        """Build an intent from loose external input while preserving gaps."""

        priorities_value = values.get("priorities", ())
        if isinstance(priorities_value, str):
            priorities = (priorities_value,)
        elif priorities_value is None:
            priorities = ()
        else:
            priorities = tuple(str(item).strip() for item in priorities_value if str(item).strip())
        intent = cls(
            converter_family=_optional_str(values.get("converter_family")),
            topology_hint=_optional_str(values.get("topology_hint")),
            vin_min_v=_optional_float(values.get("vin_min_v")),
            vin_nom_v=_optional_float(values.get("vin_nom_v")),
            vin_max_v=_optional_float(values.get("vin_max_v")),
            vout_v=_optional_float(values.get("vout_v")),
            iout_a=_optional_float(values.get("iout_a")),
            pout_w=_optional_float(values.get("pout_w")),
            fsw_hz=_optional_float(values.get("fsw_hz")),
            ripple_voltage_ratio=_optional_float(values.get("ripple_voltage_ratio")),
            ripple_current_pp_a=_optional_float(values.get("ripple_current_pp_a")),
            isolation_required=_optional_bool(values.get("isolation_required")),
            bidirectional=_optional_bool(values.get("bidirectional")),
            load_type=_optional_str(values.get("load_type")),
            priorities=priorities,
            constraints=dict(values.get("constraints", {}) or {}),
        ).infer_missing_power_fields()
        return replace(intent, missing_fields=tuple(intent.required_field_status()["missing"]))

    def to_dict(self) -> dict[str, object]:
        """Return a serializable dictionary representation."""

        return {
            "converter_family": self.converter_family,
            "topology_hint": self.topology_hint,
            "vin_min_v": self.vin_min_v,
            "vin_nom_v": self.vin_nom_v,
            "vin_max_v": self.vin_max_v,
            "vout_v": self.vout_v,
            "iout_a": self.iout_a,
            "pout_w": self.pout_w,
            "fsw_hz": self.fsw_hz,
            "ripple_voltage_ratio": self.ripple_voltage_ratio,
            "ripple_current_pp_a": self.ripple_current_pp_a,
            "isolation_required": self.isolation_required,
            "bidirectional": self.bidirectional,
            "load_type": self.load_type,
            "priorities": self.priorities,
            "constraints": dict(self.constraints),
            "missing_fields": self.missing_fields,
        }

    def infer_missing_power_fields(self) -> "DesignIntent":
        """Infer Pout or Iout when the other power fields are available."""

        pout_w = self.pout_w
        iout_a = self.iout_a
        if pout_w is None and self.vout_v not in (None, 0.0) and iout_a is not None:
            pout_w = self.vout_v * iout_a
        if iout_a is None and self.vout_v not in (None, 0.0) and pout_w is not None:
            iout_a = pout_w / self.vout_v
        return replace(self, pout_w=pout_w, iout_a=iout_a)

    def required_field_status(self) -> dict[str, tuple[str, ...]]:
        """Report present and missing important fields without raising."""

        present = []
        missing = []
        inferred = self.infer_missing_power_fields()
        for field_name in IMPORTANT_FIELDS:
            if getattr(inferred, field_name) is None:
                missing.append(field_name)
            else:
                present.append(field_name)
        return {"present": tuple(present), "missing": tuple(missing)}

    def normalized_priorities(self) -> tuple[str, ...]:
        """Return lower-case priority tokens with stable ordering and no duplicates."""

        normalized: list[str] = []
        seen: set[str] = set()
        for priority in self.priorities:
            token = priority.strip().lower().replace("-", "_").replace(" ", "_")
            if not token or token in seen:
                continue
            seen.add(token)
            normalized.append(token)
        return tuple(normalized)


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_bool(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "required"}:
        return True
    if text in {"0", "false", "no", "n", "not_required"}:
        return False
    return None
