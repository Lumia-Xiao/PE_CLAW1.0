"""Shared semiconductor thermal-input parsing helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


AMBIENT_TEMP_INPUT_KEY = "ambient_temp_c"
DEFAULT_AMBIENT_TEMP_C = 25.0
AMBIENT_TEMP_MIN_C = -40.0
AMBIENT_TEMP_MAX_C = 150.0
TARGET_JUNCTION_TEMP_INPUT_KEY = "target_junction_temp_c"
DEFAULT_TARGET_JUNCTION_TEMP_C = 100.0
TARGET_JUNCTION_TEMP_MIN_C = 25.0
TARGET_JUNCTION_TEMP_MAX_C = 175.0


def with_default_ambient_input(raw_input: Mapping[str, str]) -> dict[str, str]:
    """Return raw input with the shared semiconductor thermal fields populated."""
    normalized = dict(raw_input)
    normalized.setdefault(AMBIENT_TEMP_INPUT_KEY, f"{DEFAULT_AMBIENT_TEMP_C:.1f}")
    normalized.setdefault(TARGET_JUNCTION_TEMP_INPUT_KEY, f"{DEFAULT_TARGET_JUNCTION_TEMP_C:.1f}")
    return normalized


def parse_ambient_temperature_c(raw_value: object) -> float:
    """Parse an optional ambient-temperature input with a documented fallback."""
    if raw_value is None:
        return DEFAULT_AMBIENT_TEMP_C
    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
        if raw_value == "":
            return DEFAULT_AMBIENT_TEMP_C

    try:
        ambient_temp_c = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Ambient temperature must be a valid number.") from exc

    if ambient_temp_c < AMBIENT_TEMP_MIN_C or ambient_temp_c > AMBIENT_TEMP_MAX_C:
        raise ValueError(
            f"Ambient temperature must be between {AMBIENT_TEMP_MIN_C:.0f} C and {AMBIENT_TEMP_MAX_C:.0f} C."
        )
    return ambient_temp_c


def parse_target_junction_temperature_c(raw_value: object) -> float:
    """Parse the requested target junction temperature with range validation."""
    if raw_value is None:
        return DEFAULT_TARGET_JUNCTION_TEMP_C
    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
        if raw_value == "":
            return DEFAULT_TARGET_JUNCTION_TEMP_C

    try:
        target_temp_c = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Target junction temperature must be a valid number.") from exc

    if target_temp_c < TARGET_JUNCTION_TEMP_MIN_C or target_temp_c > TARGET_JUNCTION_TEMP_MAX_C:
        raise ValueError(
            "Target junction temperature must be between "
            f"{TARGET_JUNCTION_TEMP_MIN_C:.0f} C and {TARGET_JUNCTION_TEMP_MAX_C:.0f} C."
        )
    return target_temp_c


def merge_ambient_metadata(
    metadata: Mapping[str, Any] | None,
    raw_input: Mapping[str, object],
) -> dict[str, Any]:
    """Attach the normalized semiconductor thermal inputs to the spec metadata."""
    merged = dict(metadata or {})
    merged[AMBIENT_TEMP_INPUT_KEY] = parse_ambient_temperature_c(raw_input.get(AMBIENT_TEMP_INPUT_KEY))
    merged[TARGET_JUNCTION_TEMP_INPUT_KEY] = parse_target_junction_temperature_c(
        raw_input.get(TARGET_JUNCTION_TEMP_INPUT_KEY)
    )
    return merged
