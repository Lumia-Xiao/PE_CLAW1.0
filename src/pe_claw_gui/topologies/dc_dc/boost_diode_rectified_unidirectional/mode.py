"""Operating-mode resolution for the diode-rectified Boost topology."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ....models.operating_point import OperatingPoint
from ...base.candidate import TopologyCandidate


def _clamp_duty(value: float) -> float:
    return min(max(value, 1e-6), 0.95)


@dataclass(frozen=True)
class BoostOperatingState:
    """Resolved operating state used for Boost waveform and stress generation."""

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
    diode_conduction_ratio: float | None
    t_zero_current_s: float | None
    i_pk: float | None
    r_load_ohm: float
    i_boundary_a: float


def compute_boundary_output_current(candidate: TopologyCandidate, vin: float, vout_target: float) -> tuple[float, float, float]:
    """Return duty estimate, critical load resistance, and boundary output current."""
    duty_est = _clamp_duty(1.0 - vin / vout_target)
    r_crit = 2.0 * candidate.inductance_h * candidate.fs_hz / max(duty_est * (1.0 - duty_est) ** 2, 1e-9)
    i_boundary_out = vout_target / max(r_crit, 1e-9)
    return duty_est, r_crit, i_boundary_out


def resolve_ccm_state(candidate: TopologyCandidate, vin: float, load_ratio: float) -> BoostOperatingState:
    """Resolve the diode Boost operating state assuming CCM."""
    bounded_load_ratio = max(load_ratio, 1e-3)
    vout = candidate.vout_target
    duty = _clamp_duty(1.0 - vin / vout)
    iout = candidate.iout * bounded_load_ratio
    i_l_avg = iout / max(1.0 - duty, 1e-6)
    delta_il = vin * duty / (candidate.inductance_h * candidate.fs_hz)
    il_min = i_l_avg - 0.5 * delta_il
    il_max = i_l_avg + 0.5 * delta_il
    _, r_crit, i_boundary_out = compute_boundary_output_current(candidate, vin, vout)
    r_load_ohm = vout / max(iout, 1e-9)

    return BoostOperatingState(
        vin=vin,
        vout=vout,
        duty=duty,
        load_ratio=bounded_load_ratio,
        iout=iout,
        iL_avg=i_l_avg,
        delta_il=delta_il,
        il_min=il_min,
        il_max=il_max,
        switching_period_s=1.0 / candidate.fs_hz,
        mode="CCM",
        diode_conduction_ratio=1.0 - duty,
        t_zero_current_s=None,
        i_pk=il_max,
        r_load_ohm=r_load_ohm,
        i_boundary_a=i_boundary_out,
    )


def resolve_dcm_state(candidate: TopologyCandidate, vin: float, load_ratio: float) -> BoostOperatingState:
    """Resolve the diode Boost operating state assuming DCM with regulated output voltage."""
    bounded_load_ratio = max(load_ratio, 1e-3)
    iout = candidate.iout * bounded_load_ratio
    vout = candidate.vout_target
    switching_period_s = 1.0 / candidate.fs_hz
    r_load_ohm = vout / max(iout, 1e-9)
    k_factor = 2.0 * candidate.inductance_h / (r_load_ohm * switching_period_s)
    conversion_ratio = vout / vin
    duty = math.sqrt(max(k_factor * conversion_ratio * (conversion_ratio - 1.0), 0.0))
    duty = _clamp_duty(duty)
    i_pk = vin * duty * switching_period_s / candidate.inductance_h
    diode_conduction_ratio = vin * duty / max(vout - vin, 1e-9)

    if duty + diode_conduction_ratio >= 0.999999:
        return resolve_ccm_state(candidate, vin, load_ratio)

    _, r_crit, i_boundary_out = compute_boundary_output_current(candidate, vin, vout)

    return BoostOperatingState(
        vin=vin,
        vout=vout,
        duty=duty,
        load_ratio=bounded_load_ratio,
        iout=iout,
        iL_avg=0.5 * i_pk * (duty + diode_conduction_ratio),
        delta_il=i_pk,
        il_min=0.0,
        il_max=i_pk,
        switching_period_s=switching_period_s,
        mode="DCM",
        diode_conduction_ratio=diode_conduction_ratio,
        t_zero_current_s=(duty + diode_conduction_ratio) * switching_period_s,
        i_pk=i_pk,
        r_load_ohm=r_load_ohm,
        i_boundary_a=i_boundary_out,
    )


def build_operating_state(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> BoostOperatingState:
    """Resolve the diode Boost operating mode for the requested operating point."""
    vin = operating_point.vin_v if operating_point is not None else candidate.vin_nom
    load_ratio = operating_point.load_ratio if operating_point is not None else 1.0
    if vin <= 0.0:
        raise ValueError("Operating Vin must be positive.")
    if vin >= candidate.vout_target:
        raise ValueError("Operating Vin must remain below regulated Vout for Boost operation.")

    bounded_load_ratio = max(load_ratio, 1e-3)
    iout = candidate.iout * bounded_load_ratio
    _, _, i_boundary_out = compute_boundary_output_current(candidate, vin, candidate.vout_target)
    if iout >= i_boundary_out:
        return resolve_ccm_state(candidate, vin, load_ratio)
    return resolve_dcm_state(candidate, vin, load_ratio)
