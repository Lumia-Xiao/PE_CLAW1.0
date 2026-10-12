"""T-type complete-period position integrals and conservative envelopes."""

from __future__ import annotations

import math

from scipy.integrate import quad

from ....models.stress_result import StressMetric, StressResult
from .integration import current_zero_times, segment_current
from .paths_events import conduction_currents, extract_events, gate_vector
from .topology_contract import TOPOLOGY_ID

PAYLOAD_KEY = "three_phase_t_type_pd_spwm_waveforms"
ROLES = ("QP", "QN", "QA", "QO")


def _envelope(positions):
    keys = next(iter(positions.values())).keys()
    return {key: max(value[key] for value in positions.values()) for key in keys}


def calculate_position_stress(segments, basis, *, subdivisions=1):
    """Integrate exact currents after splitting extrema and current zero crossings."""
    duration = 1 / basis["f_line_hz"]
    metrics = {}
    for index, phase in enumerate(("a", "b", "c")):
        totals = {role: {"signed": [0., 0., 0.], "channel": [0., 0., 0.], "diode": [0., 0., 0.]} for role in ROLES}
        for segment in segments:
            start, end = segment["start_time_s"], segment["end_time_s"]
            current, extrema = segment_current(segment, index, basis)
            splits = current_zero_times(current, extrema)
            signs = {role: path.signed_a for role, path in conduction_currents(segment["states"][index], 1.).items()}
            for role, sign in signs.items():
                if not sign:
                    continue
                functions = {"signed": lambda t, sign=sign: sign * current(t),
                             "channel": lambda t, sign=sign: max(sign * current(t), 0.),
                             "diode": lambda t, sign=sign: max(-sign * current(t), 0.)}
                for path, function in functions.items():
                    total = totals[role][path]
                    total[2] = max(total[2], *(abs(function(t)) for t in extrema))
                    for left, right in zip(splits, splits[1:]):
                        for k in range(subdivisions):
                            a, b = left + (right-left)*k/subdivisions, left + (right-left)*(k+1)/subdivisions
                            total[0] += quad(function, a, b, epsabs=1e-13, epsrel=1e-10)[0]
                            total[1] += quad(lambda t: function(t)**2, a, b, epsabs=1e-13, epsrel=1e-10)[0]
        for role in ROLES:
            record = {"voltage_max_v": basis["vdc_v"] * (1. if role in ("QP", "QN") else .5)}
            for path, (area, square, peak) in totals[role].items():
                record.update({f"{path}_avg_a": area/duration, f"{path}_rms_a": math.sqrt(max(square/duration, 0.)), f"{path}_peak_a": peak})
            metrics[f"{phase}_{role}"] = record
    return {"basis": "waveform_actual", "operating_basis": dict(basis), "positions": metrics,
            "main": _envelope({k:v for k,v in metrics.items() if k.endswith(("QP", "QN"))}),
            "midpoint": _envelope({k:v for k,v in metrics.items() if k.endswith(("QA", "QO"))}),
            "integration_method": "exact ideal-L segment current; adaptive time quadrature split at extrema and zero crossings"}


def validate_waveform(candidate, waveform):
    """Reject incomplete, stale, nonfinite or inconsistent actual-waveform records."""
    from ..three_level_common import _sample_three_level_event_segments
    from .paths_events import build_positions
    from .integration import ANGLES
    try:
        if candidate.topology_id != TOPOLOGY_ID:
            raise ValueError("candidate identity")
        payload = waveform.metadata[PAYLOAD_KEY]
        basis, diagnostics = payload["basis"], payload["diagnostics"]
        for key in ("vdc_v", "vac_ll_rms_v", "fsw_hz", "f_line_hz", "inductance_h", "power_factor"):
            if not math.isfinite(basis[key]) or basis[key] <= 0:
                raise ValueError(f"invalid basis {key}")
        expected = {"vac_ll_rms_v": candidate.vout_target, "fsw_hz": candidate.fs_hz,
                    "f_line_hz": candidate.metadata["f_line_hz"], "inductance_h": candidate.inductance_h,
                    "vdc_v": waveform.operating_vin_v, "load_ratio": waveform.load_ratio}
        if any(basis[k] != v for k,v in expected.items()) or basis["power_factor_phase"] != candidate.metadata["power_factor_phase"]:
            raise ValueError("stale operating basis")
        if basis["model_scope"] != candidate.metadata["t_type_model_scope"] or not 0 <= basis["load_ratio"] <= 1 or not 0 < basis["power_factor"] <= 1 or not math.isclose(basis["pout_w"], candidate.pout_target*basis["load_ratio"], abs_tol=1e-8):
            raise ValueError("invalid power/model basis")
        solver = diagnostics["periodic_solver"]
        if diagnostics["status"] != "ok" or not solver["converged"] or not diagnostics["modulation_valid"] or diagnostics["actual_command_saturated"]:
            raise ValueError("invalid solver status")
        if len(solver["residual_a"]) != 3 or not all(math.isfinite(x) and abs(x) <= 1e-8 for x in solver["residual_a"]):
            raise ValueError("invalid periodic residual")
        if not math.isfinite(diagnostics["current_average_error_max_a"]) or diagnostics["current_average_error_max_a"] > 1e-6:
            raise ValueError("invalid current tracking")
        segments, times = payload["segments"], payload["time_s"]
        if not segments or times != waveform.time_s or times[0] != 0 or not math.isclose(times[-1], 1/basis["f_line_hz"], abs_tol=1e-12) or not all(math.isfinite(t) for t in times) or not all(b>a for a,b in zip(times,times[1:])):
            raise ValueError("incomplete period/time axis")
        if abs(segments[0]["start_time_s"]) > 1e-12 or abs(segments[-1]["end_time_s"] - times[-1]) > 1e-12:
            raise ValueError("incomplete segment period")
        previous = None
        for segment in segments:
            start, end = segment["start_time_s"], segment["end_time_s"]
            if not math.isfinite(start) or not math.isfinite(end) or end <= start:
                raise ValueError("invalid segment duration")
            if previous and abs(start-previous["end_time_s"]) > 1e-12:
                raise ValueError("segment gap")
            for key in ("states", "pole_voltages_v", "phase_neutral_voltages_v", "start_currents_a", "end_currents_a"):
                if len(segment[key]) != 3 or not all(math.isfinite(x) for x in segment[key]):
                    raise ValueError(f"incomplete/nonfinite {key}")
            poles = [s*basis["vdc_v"]*.5 for s in segment["states"]]
            neutral = [v-sum(poles)/3 for v in poles]
            if any(abs(a-b)>1e-8 for a,b in zip(poles,segment["pole_voltages_v"])) or any(abs(a-b)>1e-8 for a,b in zip(neutral,segment["phase_neutral_voltages_v"])):
                raise ValueError("segment voltage disagrees with state")
            if abs(sum(segment["start_currents_a"])) > 1e-7 or abs(sum(segment["end_currents_a"])) > 1e-7:
                raise ValueError("three-wire KCL")
            for index in range(3):
                current, _ = segment_current(segment,index,basis)
                if abs(current(end)-segment["end_currents_a"][index]) > 1e-7:
                    raise ValueError("segment current formula")
                if previous and abs(segment["start_currents_a"][index]-previous["end_currents_a"][index]) > 1e-7:
                    raise ValueError("segment current discontinuity")
            previous = segment
        if any(abs(a-b)>1e-8 for a,b in zip(segments[0]["start_currents_a"],segments[-1]["end_currents_a"])):
            raise ValueError("actual nonperiodic segment currents")
        if payload["events"] != extract_events(segments,basis["vdc_v"]):
            raise ValueError("stale events")
        sampled = _sample_three_level_event_segments(time_s=times, segments=segments, inductance_h=basis["inductance_h"], grid_voltage_peak_v=math.sqrt(2)*(basis["vac_ll_rms_v"]/math.sqrt(3)), line_frequency_hz=basis["f_line_hz"], phase_angles=ANGLES, half_bus_voltage_v=basis["vdc_v"]*.5)
        for index, phase in enumerate(("a","b","c")):
            details = payload["phases"][phase]
            for field, source in (("state","phase_states"),("current_a","phase_currents_a"),("pole_to_o_voltage_v","pole_voltages_v"),("phase_neutral_voltage_v","phase_neutral_pwm_v")):
                values = details[field]
                if len(values)!=len(times) or any(not math.isfinite(a) or abs(a-b)>1e-8 for a,b in zip(values,sampled[source][index])):
                    raise ValueError(f"stale phase {field}")
            omega = 2 * math.pi * basis["f_line_hz"]
            voltage_peak = math.sqrt(2) * (basis["vac_ll_rms_v"] / math.sqrt(3))
            current_peak = math.sqrt(2) * basis["pout_w"] / (math.sqrt(3) * basis["vac_ll_rms_v"] * basis["power_factor"])
            phi = math.acos(basis["power_factor"]) * (1 if basis["power_factor_phase"] == "lagging" else -1)
            expected_grid = [voltage_peak * math.sin(omega*t+ANGLES[index]) for t in times]
            expected_reference = [current_peak * math.sin(omega*t+ANGLES[index]-phi) for t in times]
            expected_inductor = [a-b for a,b in zip(details["phase_neutral_voltage_v"], expected_grid)]
            for field, values in (("grid_voltage_v", expected_grid), ("reference_current_a", expected_reference), ("inductor_voltage_v", expected_inductor)):
                if len(details[field]) != len(times) or any(not math.isfinite(a) or abs(a-b)>1e-8 for a,b in zip(details[field], values)):
                    raise ValueError(f"stale phase {field}")
            gates = {role: list(values) for role,values in zip(ROLES,zip(*[gate_vector(state) for state in details["state"]], strict=True))}
            if details["gates"] != gates:
                raise ValueError("stale phase gates")
        a_phase = payload["phases"]["a"]
        for field, expected_values in (("switch_node_voltage_v", a_phase["pole_to_o_voltage_v"]), ("output_voltage_v", a_phase["grid_voltage_v"]), ("inductor_current_a", a_phase["current_a"]), ("inductor_voltage_v", a_phase["inductor_voltage_v"])):
            if getattr(waveform,field) != expected_values:
                raise ValueError(f"stale compatibility field {field}")
        from .integration import integral_metrics
        if diagnostics["phase_statistics"] != integral_metrics(segments,basis):
            raise ValueError("stale phase statistics")
        instantaneous = {key: {k:v for k,v in value.items() if k != "metrics"} for key,value in payload["positions"].items()}
        if instantaneous != build_positions(payload["phases"],basis["vdc_v"]):
            raise ValueError("stale/incomplete positions")
        return payload
    except (KeyError, TypeError, IndexError, ValueError) as exc:
        raise ValueError(f"T-type invalid actual waveform: {exc}") from exc


def stress_readback(candidate, waveform=None):
    if candidate.topology_id != TOPOLOGY_ID:
        raise ValueError("T-type stress requires a T-type candidate.")
    if waveform is None:
        peak = candidate.il_peak
        positions = {f"{phase}_{role}": {"voltage_max_v": candidate.vin_nom*(1 if role in ("QP","QN") else .5),
                     "channel_peak_a": peak, "diode_peak_a": peak} for phase in ("a","b","c") for role in ROLES}
        return {"basis": "design_estimate", "positions": positions,
                "main": _envelope({k:v for k,v in positions.items() if k.endswith(("QP","QN"))}),
                "midpoint": _envelope({k:v for k,v in positions.items() if k.endswith(("QA","QO"))})}
    payload = validate_waveform(candidate,waveform)
    current = calculate_position_stress(payload["segments"],payload["basis"])
    if payload.get("stress") != current:
        raise ValueError("T-type actual stress payload missing or stale.")
    if any(payload["positions"][key].get("metrics") != metrics for key,metrics in current["positions"].items()):
        raise ValueError("T-type position stress metrics missing or stale.")
    return current


def extract_stress(candidate, waveform_set=None):
    readback = stress_readback(candidate,waveform_set)
    metrics = readback["positions"]
    actual = waveform_set is not None
    def envelope(path):
        return StressMetric(voltage_max_v=max(v["voltage_max_v"] for v in metrics.values()),
                            current_peak_a=max(v[f"{path}_peak_a"] for v in metrics.values()),
                            current_rms_a=max(v[f"{path}_rms_a"] for v in metrics.values()) if actual else None,
                            current_avg_a=max(v[f"{path}_avg_a"] for v in metrics.values()) if actual else None)
    return StressResult(switch=envelope("channel"), rectifier=envelope("diode"), role_voltage_checks={},
                        notes=[f"T-type stress basis={readback['basis']}; each metric is a per-position maximum, not summed current.",
                               "rectifier is the antiparallel diode envelope; midpoint switches are in the local readback.",
                               "Ideal static blocking: main=Vdc, midpoint=Vdc/2; ratings and overshoot unassessed.",
                               "Complete-period time integrals include PWM ripple." if actual else "Design peak estimate only; RMS/average unavailable before waveforms."])
