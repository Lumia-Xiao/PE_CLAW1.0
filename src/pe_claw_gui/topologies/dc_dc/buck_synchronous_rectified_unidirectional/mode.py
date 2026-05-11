"""Operating-state resolution for the synchronous Buck topology."""

from __future__ import annotations

from dataclasses import dataclass

from ....models.operating_point import OperatingPoint
from ...base.candidate import TopologyCandidate


def _clamp_duty(value: float) -> float:
    return min(max(value, 1e-6), 0.999999)


@dataclass(frozen=True)
class BuckSrOperatingState:
    """Resolved operating state used for synchronous Buck waveform generation."""

    vin: float
    vout: float
    duty: float
    load_ratio: float
    iout: float
    delta_il: float
    il_avg: float
    il_min: float
    il_max: float
    switching_period_s: float
    mode: str
    negative_current_present: bool


def build_operating_state(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> BuckSrOperatingState:
    """Resolve the synchronous Buck operating state for the requested point."""
    vin = operating_point.vin_v if operating_point is not None else candidate.vin_nom
    load_ratio = operating_point.load_ratio if operating_point is not None else 1.0
    if vin <= 0.0:
        raise ValueError("Operating Vin must be positive.")
    if vin <= candidate.vout_target:
        raise ValueError("Operating Vin must exceed regulated Vout for Buck operation.")

    duty = _clamp_duty(candidate.vout_target / vin)
    switching_period_s = 1.0 / candidate.fs_hz
    iout = candidate.iout * max(load_ratio, 0.0)
    delta_il = (vin - candidate.vout_target) * duty / (candidate.inductance_h * candidate.fs_hz)
    il_avg = iout
    il_min = il_avg - 0.5 * delta_il
    il_max = il_avg + 0.5 * delta_il

    return BuckSrOperatingState(
        vin=vin,
        vout=candidate.vout_target,
        duty=duty,
        load_ratio=max(load_ratio, 0.0),
        iout=iout,
        delta_il=delta_il,
        il_avg=il_avg,
        il_min=il_min,
        il_max=il_max,
        switching_period_s=switching_period_s,
        mode="CCM",
        negative_current_present=il_min < 0.0,
    )
