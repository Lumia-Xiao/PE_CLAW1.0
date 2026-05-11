"""Registered capacitor library entry points and deterministic coverage counts."""

from __future__ import annotations

from collections import Counter

from ...models.capacitor import CapacitorCandidate
from .jianghai import list_jianghai_capacitors
from .panasonic import list_panasonic_capacitors
from .rubycon import list_rubycon_capacitors
from .tdk import list_tdk_capacitors
from .wima import list_wima_capacitors
from .yageo import list_yageo_capacitors

_REGISTERED_CAPACITOR_CACHE: tuple[CapacitorCandidate, ...] | None = None


def list_registered_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return all registered capacitor candidates."""

    global _REGISTERED_CAPACITOR_CACHE
    if _REGISTERED_CAPACITOR_CACHE is None:
        candidates = tuple(
            (
                *list_yageo_capacitors(),
                *list_tdk_capacitors(),
                *list_wima_capacitors(),
                *list_rubycon_capacitors(),
                *list_panasonic_capacitors(),
                *list_jianghai_capacitors(),
            )
        )
        _validate_unique_part_numbers(candidates)
        _REGISTERED_CAPACITOR_CACHE = candidates
    return _REGISTERED_CAPACITOR_CACHE


def clear_registered_capacitor_cache() -> None:
    """Clear the process-local capacitor registry cache."""

    global _REGISTERED_CAPACITOR_CACHE
    _REGISTERED_CAPACITOR_CACHE = None


def count_registered_capacitor_candidates() -> int:
    """Return the registered capacitor count through the cached registry path."""

    candidates = list_registered_capacitors()
    _validate_unique_part_numbers(candidates)
    return len(candidates)


def capacitor_library_coverage_counts(
    candidates: tuple[CapacitorCandidate, ...] | None = None,
) -> dict[str, object]:
    """Return deterministic coverage counts for report/test use."""

    resolved = candidates if candidates is not None else list_registered_capacitors()
    return {
        "total": len(resolved),
        "by_manufacturer": dict(sorted(Counter(item.manufacturer for item in resolved).items())),
        "by_series": dict(sorted(Counter(item.series for item in resolved).items())),
        "by_package_shape": dict(sorted(Counter(item.package_shape for item in resolved).items())),
        "by_application_category": dict(sorted(Counter(item.application_category for item in resolved).items())),
        "by_voltage_rating_dc_v": dict(sorted(Counter(int(item.voltage_rating_dc_v) for item in resolved).items())),
        "by_terminal_count": dict(sorted(Counter(_terminal_count_label(item) for item in resolved).items())),
        "by_terminal_type": dict(sorted(Counter(item.terminal_type for item in resolved).items())),
        "by_mounting_style": dict(sorted(Counter(item.mounting_style for item in resolved).items())),
        "by_dielectric": dict(sorted(Counter(item.dielectric for item in resolved).items())),
        "by_construction": dict(sorted(Counter(item.construction for item in resolved).items())),
    }


def _terminal_count_label(candidate: CapacitorCandidate) -> str:
    return f"{candidate.terminal_count}-pin"


def _validate_unique_part_numbers(candidates: tuple[CapacitorCandidate, ...]) -> None:
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate capacitor part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)


__all__ = [
    "capacitor_library_coverage_counts",
    "clear_registered_capacitor_cache",
    "count_registered_capacitor_candidates",
    "list_registered_capacitors",
]
