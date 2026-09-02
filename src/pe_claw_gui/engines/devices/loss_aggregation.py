"""Shared semiconductor loss aggregation rules.

Loss evaluators return per-physical-device values.  This module is the single
place that applies topology position and parallel-device counts to those
values when building system totals.
"""

from __future__ import annotations

from collections.abc import Mapping


def active_scheme(device):
    """Return the active semiconductor scheme, if one is available."""

    if device is None:
        return None
    scheme_id = getattr(device, "active_scheme_id", None) or getattr(device, "recommended_scheme_id", None)
    return next(
        (scheme for scheme in getattr(device, "scheme_results", ()) if scheme.scheme_id == scheme_id),
        None,
    )


def role_physical_device_count(device, role_name: str) -> int:
    """Return the installed count represented by one role loss result."""

    scheme = active_scheme(device)
    if scheme is not None:
        role_result = next(
            (item for item in scheme.role_results if item.role == role_name),
            None,
        )
        if role_result is not None:
            return max(int(role_result.total_physical_device_count or 1), 1)
        return max(int(scheme.parallel_count or 1), 1)
    return max(int(getattr(device, "active_parallel_count", 1) or 1), 1)


def role_from_loss_key(key: str, loss_result=None) -> str:
    if ":" in str(key):
        return str(key).split(":", 1)[1]
    return str(getattr(loss_result, "role", key))


def semiconductor_losses_total_w(device, losses: Mapping[str, object] | None) -> float:
    """Aggregate per-device loss results using the active hardware count."""

    if not losses:
        return 0.0
    return sum(
        role_physical_device_count(device, role_from_loss_key(key, loss))
        * float(loss.p_total_W)
        for key, loss in losses.items()
    )


def semiconductor_losses_breakdown_w(device, losses: Mapping[str, object] | None) -> dict[str, float]:
    """Aggregate every per-device loss component with the same count basis."""

    fields = (
        ("conduction", "p_cond_W"),
        ("switching_on", "p_sw_on_W"),
        ("switching_off", "p_sw_off_W"),
        ("reverse_recovery", "p_rr_W"),
        ("reverse_conduction", "p_reverse_conduction_W"),
        ("deadtime", "p_deadtime_W"),
        ("output_capacitance", "p_eoss_W"),
        ("gate_drive", "p_gate_W"),
    )
    totals = {name: 0.0 for name, _ in fields}
    if not losses:
        return totals
    for key, loss in losses.items():
        count = role_physical_device_count(device, role_from_loss_key(key, loss))
        for name, field_name in fields:
            totals[name] += count * float(getattr(loss, field_name, 0.0) or 0.0)
    totals["semiconductor_total"] = sum(totals.values())
    return totals
