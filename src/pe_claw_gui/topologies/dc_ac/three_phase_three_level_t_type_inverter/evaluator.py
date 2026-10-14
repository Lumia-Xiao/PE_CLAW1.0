"""Current-basis T-type evaluation and first-pass report assembly."""

from __future__ import annotations

import math

from ....models.design_report import DesignReport
from ...base.result import TopologyResult
from .stress import PAYLOAD_KEY, extract_stress
from .topology_contract import TOPOLOGY_ID

NOT_RUN = ("device", "capacitor", "magnetic", "loss", "thermal", "geometry",
           "semiconductor_geometry", "bridge_rectifier", "efficiency_sweep")


def evaluate(candidate, waveform_set=None, stress_result=None):
    expected = extract_stress(candidate, waveform_set)
    if stress_result is not None and stress_result != expected:
        raise ValueError("T-type supplied stress disagrees with current basis.")
    actual = waveform_set is not None
    basis = waveform_set.metadata[PAYLOAD_KEY]["basis"] if actual else candidate.metadata
    vdc = basis["vdc_v"] if actual else candidate.vin_nom
    power = basis["pout_w"] if actual else candidate.pout_target
    inductance_basis = "selected" if "t_type_effective_parameter_source" in candidate.metadata else "initial"
    lines = [f"T-type stress basis={'waveform_actual' if actual else 'design_estimate'}.",
             f"Vdc={vdc:.9g} V; grid line-line RMS={candidate.vout_target:.9g} V; total active power={power:.9g} W.",
             f"PF={basis['power_factor']:.9g} {basis['power_factor_phase']}; fsw={candidate.fs_hz:.9g} Hz.",
             f"Per-phase {inductance_basis} inductance={candidate.inductance_h:.9g} H; per-bank capacitance proxy={candidate.capacitance_f:.9g} F.",
             "12 ideal IGBT-reference positions; main static blocking=Vdc, midpoint=Vdc/2."]
    if actual:
        payload = waveform_set.metadata[PAYLOAD_KEY]
        stats = payload["diagnostics"]["phase_statistics"]
        lines.extend([f"Operating load ratio={basis['load_ratio']:.9g}; A-phase total RMS={stats['a']['rms_a']:.9g} A.",
                      f"Maximum local reference-subtracted PWM ripple={max(max(v['ripple_pp_by_switching_period_a']) for v in stats.values()):.9g} A pp."])
    else:
        lines.append("Current peak is a design estimate; RMS/average require waveforms.")
    return TopologyResult(topology_id=TOPOLOGY_ID, display_name=candidate.display_name, candidate=candidate,
                          feasible=True if actual else candidate.feasible, summary_lines=lines,
                          notes=["Balanced ideal bus and inductors; no component selection, losses or system efficiency."])


def build_report(spec, candidate, operating_point=None, waveform_set=None, stress_result=None, topology_result=None):
    if spec.topology_id != TOPOLOGY_ID or candidate.topology_id != TOPOLOGY_ID:
        raise ValueError("T-type report topology identity mismatch.")
    design_fields = {"vin_nom": "vdc_nom_v", "vout_target": "vac_ll_rms_v",
                     "fs_hz": "fsw_hz", "pout_target": "pout_w"}
    estimates = candidate.metadata.get("t_type_design_estimates", {})
    if (any(candidate.metadata.get(key) != value for key, value in spec.metadata.items())
            or any(getattr(candidate, field) != spec.metadata[key] for field, key in design_fields.items())
            or candidate.inductance_h != estimates.get("l_phase_initial_h")
            or candidate.capacitance_f != estimates.get("cbank_proxy_f")):
        raise ValueError("T-type report candidate does not match design source.")
    expected_stress = extract_stress(candidate, waveform_set)
    if stress_result is not None and stress_result != expected_stress:
        raise ValueError("T-type report stress is stale.")
    expected_result = evaluate(candidate, waveform_set, expected_stress)
    if topology_result is not None and topology_result != expected_result:
        raise ValueError("T-type report evaluation is stale.")
    if waveform_set is not None:
        basis = waveform_set.metadata[PAYLOAD_KEY]["basis"]
        requested = {"vdc_v": candidate.vin_nom, "load_ratio": 1., "power_factor": candidate.metadata["power_factor"]}
        if operating_point is not None:
            for target, field in (("vdc_v", "vin_v"), ("load_ratio", "load_ratio"), ("power_factor", "power_factor")):
                value = getattr(operating_point, field)
                if value is not None:
                    requested[target] = value
            if any(value is not None and not math.isclose(value, target, rel_tol=0., abs_tol=tolerance)
                   for value, target, tolerance in ((operating_point.vout_v, candidate.vout_target, 1e-9),
                                                     (operating_point.switching_frequency_hz, candidate.fs_hz, 1e-12))):
                raise ValueError("T-type report unsupported operating request.")
        if any(basis[k] != value for k,value in requested.items()):
            raise ValueError("T-type report waveform does not match requested operating point.")
    return DesignReport(spec=spec, candidate=candidate, operating_point=operating_point, waveform=waveform_set,
                        stress=expected_stress, topology_result=expected_result,
                        notes=[*(f"{stage}: stage not run; outside first-pass T-type scope." for stage in NOT_RUN),
                               "Loss and system efficiency are unavailable.",
                               "Current waveform owns actual position stress; without waveforms stress remains at the design basis."])
