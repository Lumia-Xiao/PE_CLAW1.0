"""Synthesis logic for the three-level TZCM fixed-frequency topology."""

from __future__ import annotations

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .mode import (
    INVALID_INDUCTANCE,
    INVALID_OUTPUT_CAPACITANCE,
    INVALID_RIPPLE_TARGET,
    NO_REAL_SOLUTION,
    clamp,
    solve_operating_state,
)


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Synthesize the fixed-frequency TZCM design point from the GUI inputs."""
    vin = float(spec.metadata.get("vin_nom", spec.vin_min))
    vout = spec.vout
    pout = spec.pout
    izvs = float(spec.metadata["izvs"])
    fsw_hz = float(spec.metadata["fsw_hz"])
    deadtime_s = float(spec.metadata["deadtime_s"])
    d1_min = float(spec.metadata["d1_min"])
    d4_max = float(spec.metadata["d4_max"])
    coss_eq_f = float(spec.metadata["coss_eq_f"])
    vout_ripple_ratio = float(spec.metadata["vout_ripple_ratio"])

    effective_iout = pout / vout
    duty_average = vout / vin

    d1_design = clamp(duty_average - 0.2, d1_min, 0.25)
    d4_design = 2.0 * duty_average - d1_design
    if d4_design > d4_max:
        d4_design = d4_max
        d1_design = clamp(2.0 * duty_average - d4_design, d1_min, min(0.25, d4_design - 1e-6))

    numerator = vin * vout + 2.0 * d1_design * vin * vout - d1_design * d1_design * vin * vin - 2.0 * vout * vout
    denominator = 2.0 * (effective_iout + izvs) * vin * fsw_hz
    failure_reason: str | None = None
    if denominator <= 0.0:
        failure_reason = INVALID_INDUCTANCE
        l_design = 0.0
    else:
        l_design = numerator / denominator
        if l_design <= 0.0:
            failure_reason = INVALID_INDUCTANCE

    inductance_h = 0.9 * l_design if failure_reason is None else 0.0
    if inductance_h <= 0.0:
        failure_reason = INVALID_INDUCTANCE

    delta_i_l_pp = 0.0
    capacitance_f = 0.0
    solved_state = None
    if failure_reason is None:
        provisional_state = solve_operating_state(
            vin=vin,
            vout=vout,
            iout=effective_iout,
            pout=pout,
            izvs=izvs,
            fsw_hz=fsw_hz,
            deadtime_s=deadtime_s,
            d1_min=d1_min,
            d4_max=d4_max,
            coss_eq_f=coss_eq_f,
            inductance_h=inductance_h,
            capacitance_f=1.0,
        )
        if not provisional_state.feasible:
            failure_reason = provisional_state.reason
        else:
            delta_i_l_pp = provisional_state.delta_i_l_pp
            delta_vout_allow = vout_ripple_ratio * vout
            if delta_vout_allow <= 0.0:
                failure_reason = INVALID_RIPPLE_TARGET
            else:
                co_raw = delta_i_l_pp / (8.0 * fsw_hz * delta_vout_allow)
                capacitance_f = 1.2 * co_raw
                if capacitance_f <= 0.0:
                    failure_reason = INVALID_OUTPUT_CAPACITANCE
                else:
                    solved_state = solve_operating_state(
                        vin=vin,
                        vout=vout,
                        iout=effective_iout,
                        pout=pout,
                        izvs=izvs,
                        fsw_hz=fsw_hz,
                        deadtime_s=deadtime_s,
                        d1_min=d1_min,
                        d4_max=d4_max,
                        coss_eq_f=coss_eq_f,
                        inductance_h=inductance_h,
                        capacitance_f=capacitance_f,
                    )
                    if not solved_state.feasible:
                        failure_reason = solved_state.reason

    if failure_reason is None and solved_state is None:
        failure_reason = NO_REAL_SOLUTION

    if solved_state is None:
        solved_state = solve_operating_state(
            vin=vin,
            vout=vout,
            iout=effective_iout,
            pout=pout,
            izvs=izvs,
            fsw_hz=fsw_hz,
            deadtime_s=deadtime_s,
            d1_min=d1_min,
            d4_max=d4_max,
            coss_eq_f=coss_eq_f,
            inductance_h=max(inductance_h, 0.0),
            capacitance_f=max(capacitance_f, 0.0),
        )

    notes = [
        "Three-level DC-DC converter with fixed-switching-frequency TZCM control.",
        "The design uses the user-specified fixed switching frequency with internal defaults for deadtime, duty limits, and equivalent Coss.",
        "Output capacitance is sized from the user-specified Vout ripple target.",
    ]

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=spec.vin_min,
        vin_max=spec.vin_max,
        vin_nom=vin,
        vout_target=vout,
        pout_target=pout,
        duty_nom=duty_average,
        iout=effective_iout,
        fs_hz=fsw_hz,
        inductance_h=max(inductance_h, 0.0),
        capacitance_f=max(capacitance_f, 0.0),
        delta_il=solved_state.delta_i_l_pp,
        delta_vo=solved_state.output_ripple_vpp_v,
        il_peak=max(solved_state.i1, solved_state.i2),
        il_valley=solved_state.ip_minus,
        ccm_valid=solved_state.feasible,
        mode_capable="tzcm_fixed_frequency",
        control_duty_1=solved_state.d1,
        control_duty_4=solved_state.d4,
        current_ip_minus_a=solved_state.ip_minus,
        current_i1_a=solved_state.i1,
        current_i2_a=solved_state.i2,
        output_ripple_vpp_v=solved_state.output_ripple_vpp_v,
        feasible=solved_state.feasible,
        failure_reason=failure_reason or "OK",
        notes=notes,
        metadata={
            **spec.metadata,
            "effective_iout": effective_iout,
            "conversion_duty": duty_average,
            "d1_design": d1_design,
            "d4_design": d4_design,
            "vin_nom": vin,
            "vout_nom": vout,
            "pout_nom": pout,
            "vout_ripple_ratio": vout_ripple_ratio,
            "valley_zvs_threshold_a": solved_state.valley_zvs_threshold_a,
            "peak1_zvs_threshold_a": solved_state.peak1_zvs_threshold_a,
            "peak2_zvs_threshold_a": solved_state.peak2_zvs_threshold_a,
            "valley_zvs_pass": solved_state.valley_zvs_pass,
            "peak1_zvs_pass": solved_state.peak1_zvs_pass,
            "peak2_zvs_pass": solved_state.peak2_zvs_pass,
            "success_reason": failure_reason or "OK",
        },
    )
