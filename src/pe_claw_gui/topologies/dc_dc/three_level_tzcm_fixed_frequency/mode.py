"""Design and operating-state helpers for the three-level TZCM topology."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ....models.operating_point import OperatingPoint
from ...base.candidate import TopologyCandidate

NO_REAL_SOLUTION = "NO_REAL_SOLUTION"
DUTY_LIMIT_VIOLATION = "DUTY_LIMIT_VIOLATION"
INVALID_INDUCTANCE = "INVALID_INDUCTANCE"
INVALID_OUTPUT_CAPACITANCE = "INVALID_OUTPUT_CAPACITANCE"
INVALID_RIPPLE_TARGET = "INVALID_RIPPLE_TARGET"


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp a value into the inclusive range [lower, upper]."""
    return min(max(value, lower), upper)


@dataclass(frozen=True)
class ThreeLevelTZCMOperatingState:
    """Resolved single-point operating state for the TZCM topology."""

    vin: float
    vout: float
    iout: float
    pout: float
    izvs: float
    fsw_hz: float
    deadtime_s: float
    switching_period_s: float
    duty_average: float
    d1: float
    d4: float
    ip_minus: float
    i1: float
    i2: float
    inductance_h: float
    capacitance_f: float
    delta_i_l_pp: float
    output_ripple_vpp_v: float
    valley_zvs_threshold_a: float
    peak1_zvs_threshold_a: float
    peak2_zvs_threshold_a: float
    valley_zvs_pass: bool
    peak1_zvs_pass: bool
    peak2_zvs_pass: bool
    feasible: bool
    reason: str | None
    effective_iout: float


def solve_operating_state(
    *,
    vin: float,
    vout: float,
    iout: float,
    pout: float,
    izvs: float,
    fsw_hz: float,
    deadtime_s: float,
    d1_min: float,
    d4_max: float,
    coss_eq_f: float,
    inductance_h: float,
    capacitance_f: float,
) -> ThreeLevelTZCMOperatingState:
    """Solve the fixed-frequency TZCM operating state for the provided L and C."""
    switching_period_s = 1.0 / fsw_hz
    duty_average = vout / vin
    ip_minus = -izvs

    if inductance_h <= 0.0:
        return ThreeLevelTZCMOperatingState(
            vin=vin,
            vout=vout,
            iout=iout,
            pout=pout,
            izvs=izvs,
            fsw_hz=fsw_hz,
            deadtime_s=deadtime_s,
            switching_period_s=switching_period_s,
            duty_average=duty_average,
            d1=0.0,
            d4=0.0,
            ip_minus=ip_minus,
            i1=0.0,
            i2=0.0,
            inductance_h=inductance_h,
            capacitance_f=capacitance_f,
            delta_i_l_pp=0.0,
            output_ripple_vpp_v=0.0,
            valley_zvs_threshold_a=0.0,
            peak1_zvs_threshold_a=0.0,
            peak2_zvs_threshold_a=0.0,
            valley_zvs_pass=False,
            peak1_zvs_pass=False,
            peak2_zvs_pass=False,
            feasible=False,
            reason=INVALID_INDUCTANCE,
            effective_iout=iout,
        )

    delta_d = (vout - 2.0 * (iout + izvs) * inductance_h * fsw_hz) / vin - (vout * vout) / (vin * vin)
    if delta_d < 0.0:
        return ThreeLevelTZCMOperatingState(
            vin=vin,
            vout=vout,
            iout=iout,
            pout=pout,
            izvs=izvs,
            fsw_hz=fsw_hz,
            deadtime_s=deadtime_s,
            switching_period_s=switching_period_s,
            duty_average=duty_average,
            d1=0.0,
            d4=0.0,
            ip_minus=ip_minus,
            i1=0.0,
            i2=0.0,
            inductance_h=inductance_h,
            capacitance_f=capacitance_f,
            delta_i_l_pp=0.0,
            output_ripple_vpp_v=0.0,
            valley_zvs_threshold_a=0.0,
            peak1_zvs_threshold_a=0.0,
            peak2_zvs_threshold_a=0.0,
            valley_zvs_pass=False,
            peak1_zvs_pass=False,
            peak2_zvs_pass=False,
            feasible=False,
            reason=NO_REAL_SOLUTION,
            effective_iout=iout,
        )

    sqrt_term = math.sqrt(delta_d)
    d1 = duty_average - sqrt_term
    d4 = duty_average + sqrt_term
    if not (d1_min <= d1 < d4 <= d4_max):
        return ThreeLevelTZCMOperatingState(
            vin=vin,
            vout=vout,
            iout=iout,
            pout=pout,
            izvs=izvs,
            fsw_hz=fsw_hz,
            deadtime_s=deadtime_s,
            switching_period_s=switching_period_s,
            duty_average=duty_average,
            d1=d1,
            d4=d4,
            ip_minus=ip_minus,
            i1=0.0,
            i2=0.0,
            inductance_h=inductance_h,
            capacitance_f=capacitance_f,
            delta_i_l_pp=0.0,
            output_ripple_vpp_v=0.0,
            valley_zvs_threshold_a=0.0,
            peak1_zvs_threshold_a=0.0,
            peak2_zvs_threshold_a=0.0,
            valley_zvs_pass=False,
            peak1_zvs_pass=False,
            peak2_zvs_pass=False,
            feasible=False,
            reason=DUTY_LIMIT_VIOLATION,
            effective_iout=iout,
        )

    delta_i_l1 = (vin - vout) * d1 / (inductance_h * fsw_hz)
    delta_i_l2 = vout * (1.0 - d4) / (inductance_h * fsw_hz)
    i1 = ip_minus + delta_i_l1
    i2 = ip_minus + delta_i_l2
    delta_i_l_pp = max(i1, i2) - ip_minus

    valley_zvs_threshold_a = math.sqrt(max(0.0, coss_eq_f * vin * (vin - 4.0 * vout) / (2.0 * inductance_h)))
    peak1_zvs_threshold_a = math.sqrt(max(0.0, coss_eq_f * vin * (2.0 * vout - 1.5 * vin) / inductance_h))
    peak2_zvs_threshold_a = math.sqrt(max(0.0, coss_eq_f * vin * (2.0 * vout - 0.5 * vin) / inductance_h))

    if capacitance_f <= 0.0:
        return ThreeLevelTZCMOperatingState(
            vin=vin,
            vout=vout,
            iout=iout,
            pout=pout,
            izvs=izvs,
            fsw_hz=fsw_hz,
            deadtime_s=deadtime_s,
            switching_period_s=switching_period_s,
            duty_average=duty_average,
            d1=d1,
            d4=d4,
            ip_minus=ip_minus,
            i1=i1,
            i2=i2,
            inductance_h=inductance_h,
            capacitance_f=capacitance_f,
            delta_i_l_pp=delta_i_l_pp,
            output_ripple_vpp_v=0.0,
            valley_zvs_threshold_a=valley_zvs_threshold_a,
            peak1_zvs_threshold_a=peak1_zvs_threshold_a,
            peak2_zvs_threshold_a=peak2_zvs_threshold_a,
            valley_zvs_pass=abs(ip_minus) > valley_zvs_threshold_a,
            peak1_zvs_pass=i1 > peak1_zvs_threshold_a,
            peak2_zvs_pass=i2 > peak2_zvs_threshold_a,
            feasible=False,
            reason=INVALID_OUTPUT_CAPACITANCE,
            effective_iout=iout,
        )

    output_ripple_vpp_v = delta_i_l_pp / (8.0 * fsw_hz * capacitance_f)
    return ThreeLevelTZCMOperatingState(
        vin=vin,
        vout=vout,
        iout=iout,
        pout=pout,
        izvs=izvs,
        fsw_hz=fsw_hz,
        deadtime_s=deadtime_s,
        switching_period_s=switching_period_s,
        duty_average=duty_average,
        d1=d1,
        d4=d4,
        ip_minus=ip_minus,
        i1=i1,
        i2=i2,
        inductance_h=inductance_h,
        capacitance_f=capacitance_f,
        delta_i_l_pp=delta_i_l_pp,
        output_ripple_vpp_v=output_ripple_vpp_v,
        valley_zvs_threshold_a=valley_zvs_threshold_a,
        peak1_zvs_threshold_a=peak1_zvs_threshold_a,
        peak2_zvs_threshold_a=peak2_zvs_threshold_a,
        valley_zvs_pass=abs(ip_minus) > valley_zvs_threshold_a,
        peak1_zvs_pass=i1 > peak1_zvs_threshold_a,
        peak2_zvs_pass=i2 > peak2_zvs_threshold_a,
        feasible=True,
        reason=None,
        effective_iout=iout,
    )


def build_operating_state(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> ThreeLevelTZCMOperatingState:
    """Resolve the TZCM operating state for the candidate and requested point."""
    vin = operating_point.vin_v if operating_point is not None else candidate.vin_nom
    load_ratio = operating_point.load_ratio if operating_point is not None else 1.0
    if load_ratio <= 0.0 or load_ratio > 1.0:
        raise ValueError("Load ratio must be in the range (0, 1].")
    iout = candidate.iout * load_ratio
    return solve_operating_state(
        vin=vin,
        vout=candidate.vout_target,
        iout=iout,
        pout=candidate.vout_target * iout,
        izvs=float(candidate.metadata.get("izvs", abs(candidate.current_ip_minus_a or 0.0))),
        fsw_hz=float(candidate.metadata.get("fsw_hz", candidate.fs_hz)),
        deadtime_s=float(candidate.metadata.get("deadtime_s", 0.5e-6)),
        d1_min=float(candidate.metadata.get("d1_min", 0.06)),
        d4_max=float(candidate.metadata.get("d4_max", 0.94)),
        coss_eq_f=float(candidate.metadata.get("coss_eq_f", 178e-12)),
        inductance_h=candidate.inductance_h,
        capacitance_f=candidate.capacitance_f,
    )
