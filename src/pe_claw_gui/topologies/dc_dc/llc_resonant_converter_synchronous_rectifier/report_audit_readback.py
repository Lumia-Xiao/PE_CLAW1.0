"""Report/audit contract readback for LLC synchronous-rectifier first pass.

This helper defines SR-specific report labels and audit expectations. It keeps
the executable first-pass SR path from falling back to diode-rectifier role
names.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_TARGET_TOPOLOGY_ID = "llc_resonant_converter_synchronous_rectifier"


def build_llc_sr_report_audit_readback(
    stress_readback: Mapping[str, Any],
    loss_readback: Mapping[str, Any],
    *,
    selected_secondary_sync_switch: Mapping[str, Any] | None = None,
    timing_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return first-pass report/audit fields for the executable LLC SR path."""

    role_losses = _mapping(loss_readback.get("role_losses"))
    sr_loss = _mapping(role_losses.get("secondary_sync_switch"))
    role_stresses = _mapping(stress_readback.get("role_stresses"))
    sr_stress = _mapping(role_stresses.get("secondary_sync_switch"))
    selected_sr = _mapping(selected_secondary_sync_switch)
    timing = _mapping(timing_readback)
    return {
        "topology_id": _TARGET_TOPOLOGY_ID,
        "report_contract": "llc_sr_first_pass_report_audit_readback_v1",
        "execution_status": "executable_first_pass_readback",
        "semiconductor_roles": {
            "required_roles": ("main_switch", "secondary_sync_switch"),
            "forbidden_roles": ("rectifier_diode",),
            "secondary_rectifier_type": "full_bridge_synchronous_rectifier",
        },
        "semiconductor_key_values": {
            "Secondary Sync Switch": selected_sr.get("part_number") or sr_loss.get("part_number"),
            "Secondary Sync Switch Manufacturer": selected_sr.get("manufacturer"),
            "Secondary Sync Switch Type": selected_sr.get("device_type"),
            "SR Switch Voltage Rating": selected_sr.get("voltage_rating_v"),
            "SR Switch Current Rating": selected_sr.get("current_rating_a"),
            "SR Switch Pulse Current Rating": selected_sr.get("pulse_current_rating_a"),
            "SR Switch Rds(on)": selected_sr.get("rds_on_ohm"),
            "SR Switch Qg Total": selected_sr.get("qg_total_nc"),
            "SR Switch Coss": selected_sr.get("coss_pf"),
            "SR Switch Eoss": selected_sr.get("eoss_uj"),
            "SR Switch Eoss Proxy": selected_sr.get("eoss_proxy_uj"),
            "SR Switch Eoss Source": selected_sr.get("eoss_source"),
            "SR Switch Selection Source": selected_sr.get("selection_source"),
            "SR Switch Scalar Source": selected_sr.get("scalar_source"),
            "SR Switch Dynamic Source": selected_sr.get("dynamic_source_name"),
            "SR Timing Mode": sr_stress.get("timing_mode", "ideal_complementary_first_pass"),
            "SR Timing Data Status": timing.get("timing_data_status"),
            "SR Deadtime": timing.get("deadtime_ns"),
            "SR Deadtime Fraction": timing.get("deadtime_fraction"),
            "SR Body Diode Conduction Fraction": timing.get("body_diode_conduction_fraction"),
            "SR Channel Conduction Fraction": timing.get("channel_conduction_fraction"),
            "SR Switch Count": loss_readback.get("secondary_sync_switch_position_count"),
        },
        "loss_key_values": {
            "SR Loss Source": loss_readback.get("loss_source"),
            "SR Loss Model": sr_loss.get("loss_model"),
            "SR Total Secondary Sync Switch Loss": loss_readback.get(
                "total_secondary_sync_switch_loss_w"
            ),
            "SR Conduction Loss Per Switch": sr_loss.get("p_conduction_w"),
            "SR Deadtime Body Diode Loss Per Switch": sr_loss.get(
                "p_body_diode_deadtime_w"
            ),
            "SR Gate Loss Per Switch": sr_loss.get("p_gate_w"),
            "SR Eoss Loss Per Switch": sr_loss.get("p_eoss_w"),
            "SR Eoss Source": sr_loss.get("eoss_source"),
        },
        "review_note_codes": (
            "llc_sr_first_pass_timing_follow_up",
            "llc_sr_deadtime_body_diode_proxy",
            "llc_sr_not_final_signoff",
        ),
        "first_pass_limitations": tuple(loss_readback.get("first_pass_limitations") or ()),
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = ["build_llc_sr_report_audit_readback"]
