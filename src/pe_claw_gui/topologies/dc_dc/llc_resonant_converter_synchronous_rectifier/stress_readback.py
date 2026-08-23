"""First-pass stress readback for executable LLC synchronous rectifier.

This module adapts audited diode LLC FHA stress metadata into SR-specific role
names for the executable first-pass full-bridge SR path.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_SOURCE_TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"
_TARGET_TOPOLOGY_ID = "llc_resonant_converter_synchronous_rectifier"


def build_llc_sr_stress_readback(
    llc_fha: Mapping[str, Any],
    *,
    timing_mode: str = "ideal_complementary_first_pass",
) -> dict[str, Any]:
    """Return SR role stress readback from first-pass diode LLC FHA metadata."""

    stress = _mapping(llc_fha.get("worst_case_current_stress"))
    counts = _sr_topology_counts()
    return {
        "topology_id": _TARGET_TOPOLOGY_ID,
        "source_topology_id": _SOURCE_TOPOLOGY_ID,
        "secondary_rectifier_type": "full_bridge_synchronous_rectifier",
        "stress_source": "diode_llc_fha_worst_case_current_stress_first_pass",
        "semiconductor_topology_counts": counts,
        "role_stresses": {
            "main_switch": {
                "role_kind": "active_switch",
                "v_block_v": _float_or_none(stress.get("primary_switch_voltage_stress_v")),
                "i_rms_a": _float_or_none(stress.get("primary_switch_rms_a")),
                "i_peak_a": _float_or_none(stress.get("primary_switch_peak_a")),
                "i_avg_a": 0.0,
                "duty": 0.5,
                "current_basis": "primary FHA tank current; per primary bridge position",
            },
            "secondary_sync_switch": {
                "role_kind": "synchronous_rectifier_switch",
                "v_block_v": _float_or_none(stress.get("rectifier_reverse_voltage_stress_v")),
                "i_rms_a": _float_or_none(stress.get("rectifier_diode_rms_a")),
                "i_peak_a": _float_or_none(stress.get("rectifier_diode_peak_a")),
                "i_avg_a": _float_or_none(stress.get("rectifier_diode_avg_a")),
                "duty": 0.5,
                "timing_mode": timing_mode,
                "current_basis": "secondary FHA rectifier current remapped to synchronous switch role",
            },
        },
        "first_pass_limitations": (
            "SR stress is remapped from diode LLC FHA current estimates.",
            "Deadtime body-diode current, reverse conduction, gate timing, Coss/Eoss energy, and current sharing are not included.",
            "This readback supports executable LLC SR first-pass reporting, but is not final SR timing or parasitic signoff.",
        ),
    }


def _sr_topology_counts() -> dict[str, dict[str, object]]:
    return {
        "main_switch": {
            "role_kind": "active_switch",
            "topology_position_count": 4,
            "position_labels": ["S1", "S2", "S3", "S4"],
        },
        "secondary_sync_switch": {
            "role_kind": "synchronous_rectifier_switch",
            "topology_position_count": 4,
            "position_labels": ["SR1", "SR2", "SR3", "SR4"],
        },
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


__all__ = ["build_llc_sr_stress_readback"]
