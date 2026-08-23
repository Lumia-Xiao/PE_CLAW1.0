"""First-pass timing readback for LLC synchronous-rectifier execution.

This helper reports deterministic deadtime/body-diode timing evidence from the
existing stress readback only.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_TARGET_TOPOLOGY_ID = "llc_resonant_converter_synchronous_rectifier"


def build_llc_sr_timing_readback(
    stress_readback: Mapping[str, Any],
    *,
    timing_mode: str = "ideal_complementary_first_pass",
    deadtime_ns: float = 100.0,
    fsw_hz: float | None = None,
) -> dict[str, Any]:
    """Return SR first-pass timing evidence for executable LLC SR sessions."""

    role_stresses = _mapping(stress_readback.get("role_stresses"))
    sr_stress = _mapping(role_stresses.get("secondary_sync_switch"))
    fsw = _float_or_default(fsw_hz, _float_or_default(sr_stress.get("fsw_hz"), 0.0))
    deadtime = max(float(deadtime_ns), 0.0)
    deadtime_fraction = _clamp(2.0 * deadtime * 1e-9 * fsw, 0.0, 1.0)
    return {
        "topology_id": _TARGET_TOPOLOGY_ID,
        "source_topology_id": stress_readback.get("source_topology_id"),
        "execution_status": "executable_first_pass_readback",
        "secondary_rectifier_type": "full_bridge_synchronous_rectifier",
        "timing_mode": timing_mode,
        "timing_data_status": "first_pass_deadtime_proxy",
        "deadtime_ns": deadtime,
        "fsw_hz": fsw,
        "deadtime_fraction": deadtime_fraction,
        "body_diode_conduction_fraction": deadtime_fraction,
        "channel_conduction_fraction": 1.0 - deadtime_fraction,
        "secondary_sync_switch_timing": {
            "role_kind": "synchronous_rectifier_switch",
            "i_avg_a": _float_or_none(sr_stress.get("i_avg_a")),
            "i_rms_a": _float_or_none(sr_stress.get("i_rms_a")),
            "i_peak_a": _float_or_none(sr_stress.get("i_peak_a")),
            "duty": _float_or_none(sr_stress.get("duty")),
            "current_basis": sr_stress.get("current_basis"),
        },
        "formula_basis": {
            "deadtime_fraction": "clamp(2 * deadtime * fsw, 0, 1)",
            "body_diode_conduction_fraction": "deadtime_fraction",
            "channel_conduction_fraction": "1 - deadtime_fraction",
        },
        "limitation_codes": (
            "reverse_conduction_not_resolved",
            "gate_timing_not_optimized",
            "body_diode_proxy_not_final_signoff",
            "current_sharing_not_verified",
        ),
        "first_pass_limitations": (
            "SR timing readback is a first-pass deadtime proxy.",
            "Reverse conduction, channel/body-diode current split, gate timing optimization, and current sharing are not signed off.",
            "This readback supplements executable LLC SR first-pass reporting; it is not final SR gate-timing signoff.",
        ),
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _float_or_default(value: object, fallback: float) -> float:
    if value is None:
        return fallback
    return float(value)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


__all__ = ["build_llc_sr_timing_readback"]
