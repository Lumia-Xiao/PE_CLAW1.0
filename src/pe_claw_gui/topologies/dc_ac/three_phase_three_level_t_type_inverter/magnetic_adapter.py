"""T-type phase magnetics: actual event-current requests and fixed-L readback."""

from __future__ import annotations

from dataclasses import replace
import math
import numpy as np

from ....models.inductor import InductorDesignRequest, InductorOperatingPointRequest
from ....models.operating_point import OperatingPoint
from .engineering_adapter import build_design_basis, candidate_fingerprint
from .integration import ANGLES
from .stress import PAYLOAD_KEY, stress_readback
from .waveform import generate_waveforms


def nominal_waveform(report):
    basis = build_design_basis(report)
    case = basis.cases[0]
    if report.waveform is not None:
        stress_readback(report.candidate, report.waveform)
        actual = report.waveform.metadata[PAYLOAD_KEY]["basis"]
        if (actual["vdc_v"], actual["load_ratio"], actual["power_factor"]) == case:
            return report.waveform
    return generate_waveforms(report.candidate, OperatingPoint(vin_v=case[0], load_ratio=case[1], power_factor=case[2]))


def selected_l_waveform(report, inductance_h, operating_point=None):
    """Internal effective view; never overwrite the original synthesized candidate."""
    build_design_basis(report)
    if not math.isfinite(inductance_h) or inductance_h <= 0:
        raise ValueError("T-type selected inductance must be finite and positive")
    effective = replace(report.candidate, inductance_h=inductance_h)
    wave = generate_waveforms(effective, operating_point)
    stress_readback(effective, wave)
    return effective, wave


def phase_requests(report, *, waveform=None, effective_candidate=None, design=False):
    candidate = effective_candidate or report.candidate
    if candidate is None:
        raise ValueError("T-type magnetics requires a candidate")
    wave = waveform or (nominal_waveform(report) if design else report.waveform)
    if wave is None:
        raise ValueError("T-type magnetics requires actual event waveforms")
    stress_readback(candidate, wave)
    payload = wave.metadata[PAYLOAD_KEY]
    basis = payload["basis"]
    stats = payload["diagnostics"]["phase_statistics"]
    segments = payload["segments"]
    start = np.array([s["start_time_s"] for s in segments])[:, None]
    end = np.array([s["end_time_s"] for s in segments])[:, None]
    nodes, weights = np.polynomial.legendre.leggauss(8)
    time = (start + end) / 2 + (end - start) * nodes / 2
    dt_weights = (end - start) * weights / 2
    period = 1 / basis["f_line_hz"]
    omega = 2 * math.pi * basis["f_line_hz"]
    grid_peak = math.sqrt(2 / 3) * basis["vac_ll_rms_v"]
    reference_peak = math.sqrt(2) * basis["pout_w"] / (math.sqrt(3) * basis["vac_ll_rms_v"] * basis["power_factor"])
    phi = math.acos(basis["power_factor"]) * (1 if basis["power_factor_phase"] == "lagging" else -1)
    cycle = np.minimum(round(basis["fsw_hz"] / basis["f_line_hz"]) - 1,
                       ((start[:, 0] + end[:, 0]) * .5 * basis["fsw_hz"]).astype(int))
    result = {}
    for index, phase in enumerate("abc"):
        voltage = np.array([s["phase_neutral_voltages_v"][index] for s in segments])[:, None]
        initial = np.array([s["start_currents_a"][index] for s in segments])[:, None]
        current = initial + (voltage * (time - start) + grid_peak / omega *
                             (np.cos(omega * time + ANGLES[index]) - np.cos(omega * start + ANGLES[index]))) / basis["inductance_h"]
        residual = current - reference_peak * np.sin(omega * time + ANGLES[index] - phi)
        v_l = voltage - grid_peak * np.sin(omega * time + ANGLES[index])
        positive_area = np.bincount(cycle, weights=np.sum(np.maximum(v_l, 0) * dt_weights, axis=1))
        negative_area = np.bincount(cycle, weights=np.sum(np.maximum(-v_l, 0) * dt_weights, axis=1))
        # Equivalent half-period voltage preserves the largest measured local
        # positive/negative volt-seconds for the unchanged Steinmetz engine.
        on_v = float(max(positive_area)) * basis["fsw_hz"] * 2
        off_v = -float(max(negative_area)) * basis["fsw_hz"] * 2
        local = stats[phase]
        ripple = max(local["ripple_pp_by_switching_period_a"])
        meta = {
            "physical_instance_id": f"phase_{phase}", "phase_count": 3, "magnetic_quantity": 1,
            "magnetic_request_basis": "t_type_actual_event_waveform_per_phase",
            "current_basis": "complete-line-period actual current; exact extrema and event time integrals",
            "voltage_basis": "actual inductor voltage integrated per PWM period; equivalent half-period screening voltage",
            "pwm_ripple_rms_a": float(np.sqrt(np.sum(residual ** 2 * dt_weights) / period)),
            "delta_i_pp_design_target_a": report.candidate.delta_il,
            "delta_i_pp_predicted_achieved_a": ripple,
            "target_inductance_h": report.candidate.inductance_h,
            "actual_inductance_h": basis["inductance_h"],
            "line_frequency_hz": basis["f_line_hz"], "operating_power_factor": basis["power_factor"],
            "operating_load_ratio": basis["load_ratio"], "system_pout_w": basis["pout_w"],
            "per_phase_power_proxy_w": basis["pout_w"] / 3,
            "throughput_label": "per-phase T-type output power proxy",
        }
        fields = dict(topology_id=candidate.topology_id, display_name=candidate.display_name,
                      fs_hz=basis["fsw_hz"], i_avg_a=local["mean_a"], i_rms_a=local["rms_a"],
                      i_peak_a=max(abs(local["min_a"]), abs(local["max_a"])), i_valley_a=local["min_a"],
                      delta_i_pp_a=ripple, throughput_power_w=basis["pout_w"] / 3,
                      mode="CCM", v_l_on_v=on_v, v_l_off_v=off_v, metadata=meta,
                      notes=["Bipolar AC current including zero crossings; CCM is the fixed-inductor engine compatibility tag.",
                             "Steinmetz loss is the existing local PWM excursion approximation; full line excitation is a shadow audit."])
        if design:
            result[phase] = InductorDesignRequest(**fields, inductance_h=basis["inductance_h"],
                vin_nom_v=basis["vdc_v"], vout_nom_v=basis["vac_ll_rms_v"], duty_nom=.5,
                ccm_valid=candidate.ccm_valid, mode_capable=candidate.mode_capable)
        else:
            result[phase] = InductorOperatingPointRequest(**fields, operating_vin_v=basis["vdc_v"],
                operating_vout_v=basis["vac_ll_rms_v"], operating_iout_a=reference_peak / math.sqrt(2),
                duty=.5, load_ratio=basis["load_ratio"])
    return result


def build_design_request(report):
    requests = phase_requests(report, design=True)
    return replace(requests["a"],
        i_avg_a=max((r.i_avg_a for r in requests.values()), key=abs),
        i_rms_a=max(r.i_rms_a for r in requests.values()),
        i_peak_a=max(r.i_peak_a for r in requests.values()),
        i_valley_a=min(r.i_valley_a for r in requests.values()),
        delta_i_pp_a=max(r.delta_i_pp_a for r in requests.values()),
        v_l_on_v=max(r.v_l_on_v for r in requests.values()),
        v_l_off_v=min(r.v_l_off_v for r in requests.values()),
        metadata={**requests["a"].metadata, "physical_instance_id": "common_phase_model",
                  "magnetic_quantity": 3, "magnetic_request_basis": "t_type_nominal_three_phase_metric_envelope",
                  "delta_i_pp_predicted_achieved_a": max(r.delta_i_pp_a for r in requests.values()),
                  "pwm_ripple_rms_a": max(r.metadata["pwm_ripple_rms_a"] for r in requests.values())})


def build_operating_request(report):
    snapshot = getattr(getattr(report, "t_type_engineering", None), "magnetics", None)
    if snapshot is not None:
        if snapshot.status != "available":
            raise ValueError("T-type selected magnetic operating request is unavailable; refresh required")
        if snapshot.candidate_fingerprint != candidate_fingerprint(report.candidate) or snapshot.run_id != getattr(report.run_context, "run_id", None):
            raise ValueError("T-type magnetic operating request source mismatch")
        expected = {"vdc_v": report.candidate.vin_nom, "load_ratio": 1., "power_factor": report.spec.metadata["power_factor"]}
        if report.operating_point is not None:
            for key, field in (("vdc_v", "vin_v"), ("load_ratio", "load_ratio"), ("power_factor", "power_factor")):
                value = getattr(report.operating_point, field)
                if value is not None:
                    expected[key] = value
        if any(snapshot.operating_basis.get(k) != v for k, v in expected.items()):
            raise ValueError("T-type magnetic operating request basis mismatch; refresh required")
        phase = next((p for p in snapshot.phase_instances if p.instance_id == "phase_a"), None)
        if phase is None or phase.operating_request is None:
            raise ValueError("T-type selected phase-a operating request is missing")
        return phase.operating_request
    return phase_requests(report)["a"]
