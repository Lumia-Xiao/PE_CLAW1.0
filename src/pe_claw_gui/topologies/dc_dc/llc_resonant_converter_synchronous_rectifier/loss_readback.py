"""First-pass loss readback for LLC synchronous-rectifier execution.

This module reports the secondary SR switch conduction-only loss used by the
runtime device/efficiency pipeline. Timing and capacitance scalar data may be
carried for readback, but they are not included in the SR loss total.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_TARGET_TOPOLOGY_ID = "llc_resonant_converter_synchronous_rectifier"


def build_llc_sr_loss_readback(
    stress_readback: Mapping[str, Any],
    *,
    secondary_sync_switch_part_number: str | None = None,
    rds_on_ohm: float | None = None,
    qg_total_nc: float | None = None,
    coss_pf: float | None = None,
    eoss_uj: float | None = None,
    body_diode_forward_drop_v: float = 1.5,
    deadtime_ns: float = 100.0,
    gate_drive_v: float = 10.0,
    fsw_hz: float | None = None,
    selected_loss_result: Any | None = None,
) -> dict[str, Any]:
    """Return SR first-pass loss readback for executable LLC SR sessions."""

    role_stresses = _mapping(stress_readback.get("role_stresses"))
    sr_stress = _mapping(role_stresses.get("secondary_sync_switch"))
    counts = _mapping(stress_readback.get("semiconductor_topology_counts"))
    sr_count = _mapping(counts.get("secondary_sync_switch"))
    position_count = int(_float_or_default(sr_count.get("topology_position_count"), 4.0))

    v_block_v = _float_or_default(sr_stress.get("v_block_v"), 0.0)
    i_rms_a = _float_or_default(sr_stress.get("i_rms_a"), 0.0)
    i_avg_a = abs(_float_or_default(sr_stress.get("i_avg_a"), i_rms_a))
    fsw = _float_or_default(fsw_hz, _float_or_default(sr_stress.get("fsw_hz"), 0.0))
    deadtime_fraction = _clamp(2.0 * max(deadtime_ns, 0.0) * 1e-9 * fsw, 0.0, 1.0)

    warnings: list[str] = []
    p_conduction_w = None
    if rds_on_ohm is None:
        warnings.append("Missing SR Rds(on); conduction loss was not evaluated.")
    else:
        p_conduction_w = i_rms_a * i_rms_a * max(float(rds_on_ohm), 0.0)
    selected_loss = _mapping_from_object(selected_loss_result)
    selected_loss_method = selected_loss.get("method")
    if selected_loss and selected_loss.get("role") == "secondary_sync_switch":
        p_conduction_w = _float_or_default(selected_loss.get("p_cond_W"), _loss_or_zero(p_conduction_w))
        warnings.append("SR conduction loss readback reused the selected-device pipeline loss result.")

    p_body_diode_deadtime_w = 0.0
    p_gate_w = 0.0
    p_eoss_w = 0.0
    p_total_w = _loss_or_zero(p_conduction_w)
    eoss_source = "not_used_conduction_only"
    warnings.append("LLC SR secondary-sync-switch loss is conduction only for this first-pass model.")
    warnings.append("SR deadtime, gate-drive, and output-capacitance scalars are readback fields only and are not added to loss.")

    role_loss = {
        "role_kind": "synchronous_rectifier_switch",
        "part_number": secondary_sync_switch_part_number,
        "v_block_v": v_block_v,
        "i_rms_a": i_rms_a,
        "i_avg_a": i_avg_a,
        "fsw_hz": fsw,
        "deadtime_ns": float(deadtime_ns),
        "deadtime_fraction": deadtime_fraction,
        "body_diode_forward_drop_v": float(body_diode_forward_drop_v),
        "rds_on_ohm": None if rds_on_ohm is None else float(rds_on_ohm),
        "qg_total_nc": None if qg_total_nc is None else float(qg_total_nc),
        "gate_drive_v": float(gate_drive_v),
        "coss_pf": None if coss_pf is None else float(coss_pf),
        "eoss_uj": None if eoss_uj is None else float(eoss_uj),
        "eoss_source": eoss_source,
        "loss_model": "conduction_only",
        "loss_method": selected_loss_method or "i_rms_squared_rds_on",
        "p_conduction_w": p_conduction_w,
        "p_body_diode_deadtime_w": p_body_diode_deadtime_w,
        "p_gate_w": p_gate_w,
        "p_eoss_w": p_eoss_w,
        "p_total_w": p_total_w,
        "formula_basis": {
            "conduction": "I_rms^2 * Rds(on)",
            "deadtime_body_diode": "not included in first-pass conduction-only SR loss",
            "gate": "not included in first-pass conduction-only SR loss",
            "eoss": "not included in first-pass conduction-only SR loss",
        },
    }
    return {
        "topology_id": _TARGET_TOPOLOGY_ID,
        "source_topology_id": stress_readback.get("source_topology_id"),
        "loss_source": "first_pass_sr_loss_readback",
        "secondary_rectifier_type": "full_bridge_synchronous_rectifier",
        "secondary_sync_switch_position_count": position_count,
        "role_losses": {
            "secondary_sync_switch": role_loss,
        },
        "total_secondary_sync_switch_loss_w": p_total_w * position_count,
        "warnings": warnings,
        "first_pass_limitations": (
            "LLC SR secondary-sync-switch loss is first-pass conduction-only readback from stress and Rds(on).",
            "Gate drive, Eoss/Coss, reverse conduction, channel/body-diode current split, nonlinear Rds(on), timing overlap, layout parasitics, and current sharing are not included in the loss total.",
            "This readback supplements executable LLC SR first-pass reporting; it is not final SR timing or parasitic signoff.",
        ),
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_from_object(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if value is None:
        return {}
    keys = (
        "role",
        "p_cond_W",
        "p_sw_on_W",
        "p_sw_off_W",
        "p_rr_W",
        "p_eoss_W",
        "p_gate_W",
        "p_total_W",
        "method",
    )
    return {key: getattr(value, key) for key in keys if hasattr(value, key)}


def _float_or_default(value: object, fallback: float) -> float:
    if value is None:
        return fallback
    return float(value)


def _loss_or_zero(value: float | None) -> float:
    return 0.0 if value is None else value


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


__all__ = ["build_llc_sr_loss_readback"]
