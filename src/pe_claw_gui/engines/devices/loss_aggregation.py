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
