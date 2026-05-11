"""Operating-state resolution for the synchronous Boost topology."""

from __future__ import annotations

from dataclasses import dataclass

from ....models.operating_point import OperatingPoint
from ...base.candidate import TopologyCandidate


def _clamp_duty(value: float) -> float:
    return min(max(value, 1e-6), 0.95)


@dataclass(frozen=True)
class BoostSrOperatingState:
    """Resolved operating state used for synchronous Boost waveform generation."""

    vin: float
    vout: float
    duty: float
    load_ratio: float
    iout: float
    iL_avg: float
    delta_il: float
    il_min: float
    il_max: float
    switching_period_s: float
    mode: str
    negative_current_present: bool


def build_operating_state(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> BoostSrOperatingState:
    """Resolve the synchronous Boost operating state for the requested point."""
    vin = operating_point.vin_v if operating_point is not None else candidate.vin_nom
    load_ratio = operating_point.load_ratio if operating_point is not None else 1.0
    if vin <= 0.0:
        raise ValueError("Operating Vin must be positive.")
    if vin >= candidate.vout_target:
        raise ValueError("Operating Vin must remain below regulated Vout for Boost operation.")

    duty = _clamp_duty(1.0 - vin / candidate.vout_target)
    iout = candidate.iout * max(load_ratio, 0.0)
    i_l_avg = iout / max(1.0 - duty, 1e-6)
    delta_il = vin * duty / (candidate.inductance_h * candidate.fs_hz)
    il_min = i_l_avg - 0.5 * delta_il
    il_max = i_l_avg + 0.5 * delta_il

    return BoostSrOperatingState(
        vin=vin,
        vout=candidate.vout_target,
        duty=duty,
        load_ratio=max(load_ratio, 0.0),
        iout=iout,
        iL_avg=i_l_avg,
        delta_il=delta_il,
        il_min=il_min,
        il_max=il_max,
        switching_period_s=1.0 / candidate.fs_hz,
        mode="CCM",
        negative_current_present=il_min < 0.0,
    )
