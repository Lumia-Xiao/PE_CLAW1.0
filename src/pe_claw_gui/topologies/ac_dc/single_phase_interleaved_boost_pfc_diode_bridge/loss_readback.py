"""Topology-local loss readback for the two-phase interleaved Boost PFC."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from ....models.design_report import DesignReport
from ....models.efficiency_sweep import EfficiencySweepPoint


@dataclass(frozen=True)
class InterleavedBoostPFCLossSnapshot:
    """One complete system-loss view with an explicit provenance boundary."""

    source: str
    source_label: str
    semiconductor_loss_w: float | None = None
    bridge_rectifier_loss_w: float | None = None
    magnetic_loss_w: float | None = None
    capacitor_loss_w: float | None = None
    other_loss_w: float | None = None
    total_loss_w: float | None = None
    output_power_w: float | None = None
    efficiency: float | None = None
    unavailable_reason: str | None = None

    @property
    def is_available(self) -> bool:
        return self.source != "unavailable" and self.total_loss_w is not None


def resolve_interleaved_boost_pfc_loss_snapshot(report: DesignReport) -> InterleavedBoostPFCLossSnapshot:
    """Resolve the single source used by the two-phase loss result pages.

    A completed efficiency sweep owns the full-load system-loss view.  A
    design-point loss remains a fallback only when no sweep has been run.  A
    present but incomplete/blocked sweep is reported as unavailable instead of
    mixing its partial values with the design-point snapshot.
    """

    sweep = report.efficiency_sweep
    if sweep is not None:
        if sweep.status != "available":
            return _unavailable_snapshot(
                sweep.blocked_reason
                or f"Efficiency sweep is {sweep.status}; full-load system loss is unavailable."
            )
        point = _full_load_point(sweep.points)
        if point is None:
            return _unavailable_snapshot("Efficiency sweep has no complete 1.0 p.u. full-load point.")
        return _snapshot_from_full_load_point(point)
    return _snapshot_from_design_point(report)


def _snapshot_from_full_load_point(point: EfficiencySweepPoint) -> InterleavedBoostPFCLossSnapshot:
    values = {
        "semiconductor": point.semiconductor_loss_w,
        "bridge rectifier": point.bridge_rectifier_loss_w,
        "magnetic": point.magnetic_loss_w,
        "capacitor": point.capacitor_loss_w,
        "other": point.other_loss_w,
    }
    if any(not _finite_nonnegative(value) for value in values.values()):
        return _unavailable_snapshot("Full-load efficiency sweep is missing one or more loss components.")
    output_power = _as_finite_float(point.output_power_w)
    if output_power is None or output_power <= 0.0:
        return _unavailable_snapshot("Full-load efficiency sweep has no positive output-power basis.")
    total = sum(float(value) for value in values.values())
    denominator = output_power + total
    efficiency = output_power / denominator if denominator > 0.0 else None
    if efficiency is None:
        return _unavailable_snapshot("Full-load efficiency sweep produced an invalid efficiency basis.")
    return InterleavedBoostPFCLossSnapshot(
        source="full_load_efficiency_sweep",
        source_label="Full-load efficiency sweep (1.0 p.u.)",
        semiconductor_loss_w=float(values["semiconductor"]),
        bridge_rectifier_loss_w=float(values["bridge rectifier"]),
        magnetic_loss_w=float(values["magnetic"]),
        capacitor_loss_w=float(values["capacitor"]),
        other_loss_w=float(values["other"]),
        total_loss_w=total,
        output_power_w=output_power,
        efficiency=efficiency,
    )


def _snapshot_from_design_point(report: DesignReport) -> InterleavedBoostPFCLossSnapshot:
    loss = report.loss
    if loss is None or not _finite_nonnegative(loss.total_loss_w):
        return _unavailable_snapshot("Design-point system loss is unavailable.")
    output_power = report.candidate.pout_target if report.candidate is not None else report.spec.pout
    output_power = _as_finite_float(output_power)
    total = float(loss.total_loss_w)
    efficiency = output_power / (output_power + total) if output_power is not None and output_power > 0.0 else None
    breakdown = loss.breakdown_w
    return InterleavedBoostPFCLossSnapshot(
        source="design_point",
        source_label="Design-point",
        semiconductor_loss_w=_as_finite_float(breakdown.get("semiconductor_loss_w")),
        bridge_rectifier_loss_w=_as_finite_float(breakdown.get("bridge_rectifier_loss_w")),
        magnetic_loss_w=_as_finite_float(breakdown.get("inductor_total_loss_w")),
        capacitor_loss_w=_as_finite_float(breakdown.get("dc_link_capacitor_loss_w")),
        other_loss_w=_as_finite_float(breakdown.get("other_loss_w")),
        total_loss_w=total,
        output_power_w=output_power,
        efficiency=efficiency,
    )


def _full_load_point(points: tuple[EfficiencySweepPoint, ...]) -> EfficiencySweepPoint | None:
    for point in points:
        if abs(float(point.load_pu) - 1.0) < 1.0e-9:
            return point
    return None


def _as_finite_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) else None


def _finite_nonnegative(value: object) -> bool:
    result = _as_finite_float(value)
    return result is not None and result >= 0.0


def _unavailable_snapshot(reason: str) -> InterleavedBoostPFCLossSnapshot:
    return InterleavedBoostPFCLossSnapshot(
        source="unavailable",
        source_label="Unavailable",
        unavailable_reason=reason,
    )


__all__ = [
    "InterleavedBoostPFCLossSnapshot",
    "resolve_interleaved_boost_pfc_loss_snapshot",
]
