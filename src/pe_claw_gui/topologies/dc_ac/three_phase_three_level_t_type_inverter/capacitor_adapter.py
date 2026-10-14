"""Signed split-link port currents; raw charge balance precedes bank selection."""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from ....models.capacitor import CapacitorSizingRequest
from .integration import ANGLES
from .magnetic_adapter import nominal_waveform
from .stress import PAYLOAD_KEY, stress_readback


@dataclass(frozen=True)
class SplitLinkWaveforms:
    time_s: np.ndarray
    rails_a: dict[str, np.ndarray]
    currents_a: dict[str, np.ndarray]
    charges_c: dict[str, np.ndarray]
    metrics: dict[str, object]
    basis: dict[str, float | str]


def validate_charge_balance(charge_drift_c, absolute_charge_c, side):
    limit = max(1e-10, 1e-8 * absolute_charge_c)
    if not math.isfinite(charge_drift_c) or not math.isfinite(absolute_charge_c) or absolute_charge_c < 0:
        raise ValueError(f"{side}: nonfinite raw charge evidence")
    if abs(charge_drift_c) > limit:
        raise ValueError(f"{side}: raw charge drift {charge_drift_c:.12g} C exceeds {limit:.12g} C; source/midpoint is not periodic")
    return limit


def port_waveforms(payload, *, subdivisions=32):
    """Exact ideal-L segment ODE, Gauss rail means, signed charge primitive.

    Each switching boundary retains both limits separated by one floating-point
    time step. This avoids trapezoid smearing of discontinuous rail currents in
    the unchanged shared selector. Raw drift is checked on Gauss integrals.
    """
    if not isinstance(subdivisions, int) or subdivisions < 2:
        raise ValueError("T-type port integration requires at least two subdivisions")
    basis, segments = payload["basis"], payload["segments"]
    if any(not math.isfinite(basis[k]) or basis[k] <= 0 for k in ("inductance_h", "vdc_v", "vac_ll_rms_v", "f_line_hz")):
        raise ValueError("T-type capacitor nonfinite/invalid basis")
    start = np.array([s["start_time_s"] for s in segments])[:, None]
    end = np.array([s["end_time_s"] for s in segments])[:, None]
    period = 1 / basis["f_line_hz"]
    if (not len(segments) or not np.isfinite(start).all() or not np.isfinite(end).all()
            or np.any(end <= start) or start[0, 0] != 0
            or not math.isclose(end[-1, 0], period, abs_tol=1e-12)
            or not np.array_equal(start[1:, 0], end[:-1, 0])):
        raise ValueError("T-type capacitor incomplete/nonmonotone segment time axis")
    initial = np.array([s["start_currents_a"] for s in segments])[:, None, :]
    voltage = np.array([s["phase_neutral_voltages_v"] for s in segments])[:, None, :]
    states = np.array([s["states"] for s in segments])
    if not np.isfinite(initial).all() or not np.isfinite(voltage).all() or not np.isin(states, (-1, 0, 1)).all():
        raise ValueError("T-type capacitor nonfinite current/voltage or invalid state")
    w = 2 * math.pi * basis["f_line_hz"]
    peak = math.sqrt(2 / 3) * basis["vac_ll_rms_v"]
    l = basis["inductance_h"]
    angles = np.array(ANGLES)[None, None, :]

    def current(time):
        return initial + (voltage * (time - start)[:, :, None] + peak / w *
            (np.cos(w * time[:, :, None] + angles) - np.cos(w * start[:, :, None] + angles))) / l

    def primitive(time):
        dt = (time - start)[:, :, None]
        return initial * dt + voltage / (2 * l) * dt ** 2 + peak / (w * l) * (
            (np.sin(w * time[:, :, None] + angles) - np.sin(w * start[:, :, None] + angles)) / w
            - np.cos(w * start[:, :, None] + angles) * dt)

    masks = {rail: (states == state)[:, None, :] for rail, state in (("P", 1), ("O", 0), ("N", -1))}
    nodes, weights = np.polynomial.legendre.leggauss(8)
    gauss_t = (start + end) / 2 + (end - start) * nodes / 2
    dt_weights = (end - start) * weights / 2
    phase_g = current(gauss_t)
    rails_g = {rail: np.sum(phase_g * mask, axis=2) for rail, mask in masks.items()}
    means = {rail: float(np.sum(values * dt_weights) / period) for rail, values in rails_g.items()}
    source = (means["P"] - means["N"]) / 2
    t = start + (end - start) * np.linspace(0, 1, subdivisions + 1)
    # Preserve the left-hand end value; move the next segment's right-hand
    # start by one ULP to make the common engine's time axis strictly increasing.
    t[1:, 0] = np.nextafter(t[1:, 0], np.inf)
    phase = current(t)
    rails = {rail: np.sum(phase * mask, axis=2) for rail, mask in masks.items()}
    if max(float(np.max(np.abs(sum(rails.values())))), float(np.max(np.abs(sum(rails_g.values()))))) > 1e-8:
        raise ValueError("T-type capacitor three-wire rail KCL exceeds 1e-8 A")
    currents = {"upper": source - rails["P"], "lower": source + rails["N"]}
    gcurrents = {"upper": source - rails_g["P"], "lower": source + rails_g["N"]}
    integrals = {rail: np.sum(primitive(t) * mask, axis=2) for rail, mask in masks.items()}
    dt = t - start
    local_q = {"upper": source * dt - integrals["P"], "lower": source * dt + integrals["N"]}
    metrics = {"source_current_a": source, "source_model": "constant complete-line mean bridge power / Vdc",
               "rail_mean_a": means, "rail_rms_a": {r: float(np.sqrt(np.sum(v ** 2 * dt_weights) / period)) for r, v in rails_g.items()},
               "kcl_peak_error_a": float(np.max(np.abs(sum(rails.values())))),
               "bank_difference_error_a": float(np.max(np.abs(currents["upper"] - currents["lower"] - rails["O"]))),
               "banks": {}, "integration": f"Gauss8 raw means/RMS; analytic charge; {subdivisions} event subdivisions for shared trapezoid selector"}
    charges = {}
    for side, values in currents.items():
        g = gcurrents[side]
        drift = float(np.sum(g * dt_weights))
        abs_area = float(np.sum(abs(g) * dt_weights))
        limit = validate_charge_balance(drift, abs_area, side)
        q = local_q[side]
        cumulative = np.concatenate(([0.], np.cumsum(q[:, -1])[:-1]))
        charges[side] = (q + cumulative[:, None]).ravel()
        times, sampled = t.ravel(), values.ravel()
        sampled_area = float(np.sum((sampled[:-1] + sampled[1:]) * np.diff(times) / 2))
        metrics["banks"][side] = {"raw_mean_a": drift / period, "raw_rms_a": float(np.sqrt(np.sum(g ** 2 * dt_weights) / period)),
            "raw_charge_drift_c": drift, "absolute_charge_c": abs_area, "charge_drift_limit_c": limit,
            "selector_numerical_dc_correction_a": sampled_area / period,
            "raw_q_swing_c": float(np.ptp(charges[side]))}
    return SplitLinkWaveforms(t.ravel(), {r: v.ravel() for r, v in rails.items()},
                             {s: v.ravel() for s, v in currents.items()}, charges, metrics, dict(basis))


def voltage_ripple(wave, upper_f, lower_f):
    if any(not math.isfinite(c) or c <= 0 for c in (upper_f, lower_f)):
        raise ValueError("T-type both physical bank capacitances must be finite and positive")
    upper = wave.charges_c["upper"] / upper_f
    lower = wave.charges_c["lower"] / lower_f
    return {"upper_capacitive_pp_v": float(np.ptp(upper)), "lower_capacitive_pp_v": float(np.ptp(lower)),
            "link_capacitive_pp_v": float(np.ptp(upper + lower)),
            "midpoint_difference_pp_v": float(np.ptp(upper - lower)),
            "upper_drift_v": float(upper[-1] - upper[0]), "lower_drift_v": float(lower[-1] - lower[0]),
            "equivalent_link_capacitance_f": upper_f * lower_f / (upper_f + lower_f)}


def build_capacitor_requests(report, *, design=False):
    from .engineering_adapter import build_design_basis
    build_design_basis(report)
    wave = nominal_waveform(report) if design else report.waveform
    if wave is None:
        raise ValueError("T-type capacitor actual event waveform is missing")
    stress_readback(report.candidate, wave)
    if not design:
        expected = {"vdc_v": report.candidate.vin_nom, "load_ratio": 1., "power_factor": report.spec.metadata["power_factor"]}
        if report.operating_point is not None:
            for key, field in (("vdc_v", "vin_v"), ("load_ratio", "load_ratio"), ("power_factor", "power_factor")):
                value = getattr(report.operating_point, field)
                if value is not None:
                    expected[key] = value
        if any(wave.metadata[PAYLOAD_KEY]["basis"][k] != v for k, v in expected.items()):
            raise ValueError("T-type capacitor operating basis mismatch; regenerate current waveforms")
    ports = port_waveforms(wave.metadata[PAYLOAD_KEY])
    basis = ports.basis
    requests = {side: CapacitorSizingRequest(side=side, dc_voltage_v=basis["vdc_v"] / 2,
        ripple_ratio_percent=report.candidate.metadata["dc_link_voltage_ripple_ratio"] * 100,
        current_time_s=ports.time_s.tolist(), current_waveform_a=ports.currents_a[side].tolist(),
        switching_frequency_hz=basis["fsw_hz"], ambient_temp_c=report.spec.metadata["engineering_ambient_temp_c"],
        voltage_margin=1.2, max_parallel_count=5, min_series_count=1, max_series_count=4,
        capacitance_min_f=report.candidate.capacitance_f, role="dc_link", design_type="inverter_electrolytic_dc_link",
        basis="t_type_signed_event_ports_fixed_bus_ripple_estimate", topology_id=report.spec.topology_id,
        pout_design_w=basis["pout_w"], vac_rms_v=basis["vac_ll_rms_v"], f_line_hz=basis["f_line_hz"],
        allowed_capacitor_technologies=("aluminum_electrolytic",)) for side in ("upper", "lower")}
    return requests, ports
