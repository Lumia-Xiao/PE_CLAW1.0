"""Shared semiconductor loss aggregation contracts."""

from __future__ import annotations

from typing import Iterable


NPC_ROLES = (
    "npc_outer_switch",
    "npc_inner_switch",
    "npc_clamp_diode",
)


def npc_role_physical_device_count(device_result, role: str) -> int:
    """Return the physical count for one NPC role, including parallel parts."""

    active_scheme_id = getattr(device_result, "active_scheme_id", None) or getattr(
        device_result, "recommended_scheme_id", None
    )
    for scheme in getattr(device_result, "scheme_results", ()):
        if scheme.scheme_id != active_scheme_id:
            continue
        for role_result in scheme.role_results:
            if role_result.role == role:
                return max(int(role_result.total_physical_device_count or 1), 1)
    return max(int(getattr(device_result, "active_parallel_count", 1) or 1), 1)


def npc_current_role_loss_totals(device_result) -> dict[str, float]:
    """Aggregate current per-device losses into one total per NPC role.

    Each current ``DeviceLossResult.p_total_W`` is per physical device.  The
    physical count is applied once here and nowhere else in the caller.
    """

    totals: dict[str, float] = {}
    for loss_result in getattr(device_result, "current_operating_losses", {}).values():
        role = str(getattr(loss_result, "role", ""))
        if role not in NPC_ROLES:
            continue
        totals[role] = float(loss_result.p_total_W) * npc_role_physical_device_count(device_result, role)
    return totals


def npc_current_operating_losses_complete(device_result) -> bool:
    """Return whether all NPC roles have current operating-point losses."""

    roles = {
        str(getattr(loss_result, "role", ""))
        for loss_result in getattr(device_result, "current_operating_losses", {}).values()
    }
    return set(NPC_ROLES).issubset(roles)


def npc_loss_basis(device_result) -> str:
    """Return the common display basis used by NPC result pages."""

    return "current operating point" if npc_current_operating_losses_complete(device_result) else "design point"


def _positive_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0.0 else None


def npc_switching_frequency_hz(report) -> tuple[float | None, str]:
    """Resolve NPC switching frequency and identify the winning source."""

    waveform = getattr(report, "waveform", None)
    waveform_metadata = getattr(waveform, "metadata", {})
    if isinstance(waveform_metadata, dict):
        for key in ("fsw_hz", "fs_op_hz", "switching_frequency_hz"):
            value = _positive_float(waveform_metadata.get(key))
            if value is not None:
                return value, f"waveform.metadata.{key}"
    candidate = getattr(report, "candidate", None)
    candidate_metadata = getattr(candidate, "metadata", {})
    if isinstance(candidate_metadata, dict):
        for key in ("fsw_hz", "fs_op_hz", "switching_frequency_hz"):
            value = _positive_float(candidate_metadata.get(key))
            if value is not None:
                return value, f"candidate.metadata.{key}"
    value = _positive_float(getattr(candidate, "fs_hz", None))
    if value is not None:
        return value, "candidate.fs_hz"
    value = _positive_float(1.0 / waveform.switching_period_s) if waveform is not None and waveform.switching_period_s else None
    if value is not None:
        return value, "waveform.switching_period_s"
    return None, "unavailable"


def npc_reverse_recovery_audit(report) -> dict[str, object]:
    """Describe reverse-recovery treatment without assuming every role is SiC."""

    device = getattr(report, "device", None)
    if device is None:
        return {"status": "unavailable", "roles": {}}
    losses = getattr(device, "current_operating_losses", {}) or getattr(device, "design_point_losses", {}) or getattr(device, "evaluated_losses", {})
    role_payloads: dict[str, dict[str, object]] = {}
    for role in NPC_ROLES:
        loss = next((item for item in losses.values() if getattr(item, "role", "") == role), None)
        if loss is None:
            role_payloads[role] = {"status": "unavailable"}
            continue
        device_type = str(getattr(device, "selected_device_types", {}).get(role, "") or "")
        diode_subtype = str(getattr(device, "selected_device_diode_subtypes", {}).get(role, "") or "")
        vendor = str(getattr(device, "selected_device_vendors", {}).get(role, "") or "")
        part_number = str(getattr(loss, "part_number", "") or "")
        identity = " ".join((device_type, diode_subtype, vendor, part_number)).casefold()
        is_sic = "sic" in identity or "silicon carbide" in identity
        p_rr_per_device = float(getattr(loss, "p_rr_W", 0.0) or 0.0)
        count = npc_role_physical_device_count(device, role)
        if is_sic or diode_subtype == "sic_sbd":
            status = "zero_by_sic_device_model"
            basis = "SiC device/SiC Schottky diode; reverse-recovery loss is set to zero."
        elif "body_diode" in diode_subtype or "with diode" in device_type.casefold():
            status = "internal_diode_qrr_model"
            basis = "Non-SiC MOSFET with internal diode; report the device qrr model result, not a SiC assumption."
        elif "diode" in device_type.casefold():
            status = "diode_qrr_model"
            basis = "Standalone diode reverse-recovery model result."
        else:
            status = "not_separately_identified"
            basis = "No separate reverse-recovery path was identified for this device role."
        role_payloads[role] = {
            "status": status,
            "basis": basis,
            "part_number": part_number,
            "device_type": device_type,
            "diode_subtype": diode_subtype,
            "p_rr_W_per_device": p_rr_per_device,
            "physical_device_count": count,
            "p_rr_W_role_total": p_rr_per_device * count,
        }
    available = [item for item in role_payloads.values() if item.get("status") != "unavailable"]
    return {
        "status": "available" if len(available) == len(NPC_ROLES) else "incomplete",
        "total_reverse_recovery_loss_W": sum(float(item.get("p_rr_W_role_total", 0.0) or 0.0) for item in available),
        "roles": role_payloads,
    }


def npc_scheme_role_loss_totals(scheme_or_role_results) -> dict[str, float]:
    """Return already-aggregated design-point loss for each selected NPC role."""

    role_results = getattr(scheme_or_role_results, "role_results", scheme_or_role_results)
    return {
        str(role_result.role): float(role_result.total_loss_w)
        for role_result in role_results
        if str(role_result.role) in NPC_ROLES
        and role_result.selected_part_number is not None
        and role_result.total_loss_w is not None
    }


def npc_sum_role_losses(role_totals: dict[str, float] | Iterable[float]) -> float:
    """Sum role totals without applying another device-count multiplier."""

    values = role_totals.values() if isinstance(role_totals, dict) else role_totals
    return sum(float(value) for value in values)
