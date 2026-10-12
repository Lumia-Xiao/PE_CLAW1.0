"""Time integrals and extrema of exact ideal-L segment currents (A, seconds)."""

from __future__ import annotations

import math

from scipy.integrate import quad
from scipy.optimize import brentq

ANGLES = (0.0, -2 * math.pi / 3, 2 * math.pi / 3)


def sinusoidal_roots(a: float, b: float, c: float, omega: float,
                     phase: float, start: float, end: float) -> list[float]:
    """Interior roots of a*sin(omega*t+phase)+b*cos(...)=c."""
    amplitude = math.hypot(a, b)
    if amplitude == 0 or abs(c) > amplitude:
        return []
    offset = math.atan2(b, a)
    theta = math.asin(max(-1.0, min(1.0, c / amplitude)))
    roots = []
    for base in (theta, math.pi - theta):
        lower = math.ceil((omega * start + phase + offset - base) / (2 * math.pi))
        upper = math.floor((omega * end + phase + offset - base) / (2 * math.pi))
        for k in range(lower, upper + 1):
            t = (base + 2 * math.pi * k - phase - offset) / omega
            if start < t < end:
                roots.append(t)
    return sorted(set(roots))


def segment_current(segment: dict, phase: int, basis: dict):
    """Return exact current callable and its extrema times within one segment."""
    start, end = segment["start_time_s"], segment["end_time_s"]
    omega = 2 * math.pi * basis["f_line_hz"]
    peak = math.sqrt(2 / 3) * basis["vac_ll_rms_v"]
    voltage = segment["phase_neutral_voltages_v"][phase]
    initial = segment["start_currents_a"][phase]
    inductance = basis["inductance_h"]
    angle = ANGLES[phase]

    def current(t):
        area = peak * (math.cos(omega * start + angle) - math.cos(omega * t + angle)) / omega
        return initial + (voltage * (t - start) - area) / inductance

    extrema = [start, *sinusoidal_roots(peak, 0, voltage, omega, angle, start, end), end]
    return current, extrema


def integral_metrics(segments: list[dict], basis: dict) -> dict:
    """Complete-period phase mean/RMS/extrema and per-PWM residual ripple."""
    omega = 2 * math.pi * basis["f_line_hz"]
    voltage_peak = math.sqrt(2 / 3) * basis["vac_ll_rms_v"]
    current_peak = math.sqrt(2) * basis["pout_w"] / (math.sqrt(3) * basis["vac_ll_rms_v"] * basis["power_factor"])
    phi = math.acos(basis["power_factor"]) * (1 if basis["power_factor_phase"] == "lagging" else -1)
    cycles = round(basis["fsw_hz"] / basis["f_line_hz"])
    duration = 1 / basis["f_line_hz"]
    result = {}
    for index, phase in enumerate(("a", "b", "c")):
        area = square = 0.0
        low, high = math.inf, -math.inf
        ripple_low, ripple_high = [math.inf] * cycles, [-math.inf] * cycles
        for segment in segments:
            start, end = segment["start_time_s"], segment["end_time_s"]
            current, extrema = segment_current(segment, index, basis)
            area += quad(current, start, end, epsabs=1e-13, epsrel=1e-10)[0]
            square += quad(lambda t: current(t) ** 2, start, end, epsabs=1e-13, epsrel=1e-10)[0]
            values = [current(t) for t in extrema]
            low, high = min(low, *values), max(high, *values)
            cycle = min(cycles - 1, int((start + end) * .5 * basis["fsw_hz"]))
            # d(i-i_reference)/dt=0; retain both boundaries of every PWM segment.
            a = voltage_peak / basis["inductance_h"] + current_peak * omega * math.sin(phi)
            b = current_peak * omega * math.cos(phi)
            c = segment["phase_neutral_voltages_v"][index] / basis["inductance_h"]
            times = [start, *sinusoidal_roots(a, b, c, omega, ANGLES[index], start, end), end]
            residuals = [current(t) - current_peak * math.sin(omega * t + ANGLES[index] - phi) for t in times]
            ripple_low[cycle] = min(ripple_low[cycle], *residuals)
            ripple_high[cycle] = max(ripple_high[cycle], *residuals)
        result[phase] = {"mean_a": area / duration, "rms_a": math.sqrt(square / duration),
                         "min_a": low, "max_a": high,
                         "ripple_pp_by_switching_period_a": [hi - lo for hi, lo in zip(ripple_high, ripple_low, strict=True)]}
    return result


def current_zero_times(current, extrema: list[float]) -> list[float]:
    """Split monotone intervals at every sign crossing for diode/channel integrals."""
    roots = []
    for left, right in zip(extrema, extrema[1:]):
        if current(left) * current(right) < 0:
            roots.append(brentq(current, left, right, xtol=1e-15))
    return sorted(set([*extrema, *roots]))
