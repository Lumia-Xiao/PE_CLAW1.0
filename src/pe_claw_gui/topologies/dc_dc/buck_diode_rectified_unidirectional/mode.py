"""Operating-mode resolution for the unified Buck topology."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ....models.operating_point import OperatingPoint
from ...base.candidate import TopologyCandidate


def _clamp_duty(value: float) -> float:
    return min(max(value, 1e-6), 0.999999)


@dataclass(frozen=True)
class BuckOperatingState:
    """Resolved operating state used for waveform and stress generation."""

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
    i_pk: float | None
    diode_conduction_ratio: float | None
    t_zero_current_s: float | None
    r_load_ohm: float
    i_boundary_a: float


def compute_boundary_current(candidate: TopologyCandidate, vin: float, iout_target: float) -> tuple[float, float, float]:
    """Return duty estimate, critical load resistance, and boundary current."""
    duty_ccm_est = _clamp_duty(candidate.vout_target / vin)
    switching_period_s = 1.0 / candidate.fs_hz
    r_crit = 2.0 * candidate.inductance_h / (switching_period_s * max(1.0 - duty_ccm_est, 1e-9))
    i_boundary = candidate.vout_target / max(r_crit, 1e-9)
    _ = iout_target
    return duty_ccm_est, r_crit, i_boundary


def resolve_ccm_state(candidate: TopologyCandidate, vin: float, load_ratio: float) -> BuckOperatingState:
    """Resolve the Buck operating state assuming CCM."""
    bounded_load_ratio = max(load_ratio, 1e-3)
    iout = candidate.iout * bounded_load_ratio
    duty = _clamp_duty(candidate.vout_target / vin)
    vout = candidate.vout_target
    delta_il = (vin - vout) * duty / (candidate.inductance_h * candidate.fs_hz)
    il_avg = iout
    il_min = il_avg - 0.5 * delta_il
    il_max = il_avg + 0.5 * delta_il
    _, r_crit, i_boundary = compute_boundary_current(candidate, vin, iout)
    r_load_ohm = vout / max(iout, 1e-9)

    return BuckOperatingState(
        vin=vin,
        vout=vout,
        duty=duty,
        load_ratio=bounded_load_ratio,
        iout=iout,
        delta_il=delta_il,
        il_avg=il_avg,
        il_min=il_min,
        il_max=il_max,
        switching_period_s=1.0 / candidate.fs_hz,
        mode="CCM",
        i_pk=il_max,
        diode_conduction_ratio=1.0 - duty,
        t_zero_current_s=None,
        r_load_ohm=r_load_ohm,
        i_boundary_a=i_boundary,
    )


def resolve_dcm_state(candidate: TopologyCandidate, vin: float, load_ratio: float) -> BuckOperatingState:
    """Resolve the Buck operating state assuming DCM with regulated output voltage."""
    bounded_load_ratio = max(load_ratio, 1e-3)
    iout = candidate.iout * bounded_load_ratio
    vout = candidate.vout_target
    switching_period_s = 1.0 / candidate.fs_hz

    denominator = switching_period_s * vin * (vin - vout)
    if denominator <= 0.0:
        raise ValueError("Operating Vin must exceed regulated Vout for Buck operation.")

    duty = math.sqrt((2.0 * candidate.inductance_h * iout * vout) / denominator)
    duty = _clamp_duty(duty)
    i_pk = (vin - vout) * duty * switching_period_s / candidate.inductance_h
    diode_conduction_ratio = (vin - vout) * duty / max(vout, 1e-9)

    if duty + diode_conduction_ratio >= 0.999999:
        return resolve_ccm_state(candidate, vin, load_ratio)

    _, r_crit, i_boundary = compute_boundary_current(candidate, vin, iout)
    r_load_ohm = vout / max(iout, 1e-9)

    return BuckOperatingState(
        vin=vin,
        vout=vout,
        duty=duty,
        load_ratio=bounded_load_ratio,
        iout=iout,
        delta_il=i_pk,
        il_avg=iout,
        il_min=0.0,
        il_max=i_pk,
        switching_period_s=switching_period_s,
        mode="DCM",
        i_pk=i_pk,
        diode_conduction_ratio=diode_conduction_ratio,
        t_zero_current_s=(duty + diode_conduction_ratio) * switching_period_s,
        r_load_ohm=r_load_ohm,
        i_boundary_a=i_boundary,
    )


def build_operating_state(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> BuckOperatingState:
    """Resolve the Buck operating mode for the requested operating point."""
    vin = operating_point.vin_v if operating_point is not None else candidate.vin_nom
    load_ratio = operating_point.load_ratio if operating_point is not None else 1.0
    if vin <= 0.0:
        raise ValueError("Operating Vin must be positive.")
    if vin <= candidate.vout_target:
        raise ValueError("Operating Vin must exceed regulated Vout for Buck operation.")

    bounded_load_ratio = max(load_ratio, 1e-3)
    iout = candidate.iout * bounded_load_ratio
    _, _, i_boundary = compute_boundary_current(candidate, vin, iout)
    if iout >= i_boundary:
        return resolve_ccm_state(candidate, vin, load_ratio)
    return resolve_dcm_state(candidate, vin, load_ratio)
