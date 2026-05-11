"""Stress extraction for the simplified four-mode four-switch Buck-Boost topology."""

from __future__ import annotations

import math

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .waveform import generate_waveforms


def _mean_abs(values: list[float]) -> float:
    return sum(abs(value) for value in values) / max(len(values), 1)


def _peak_abs(values: list[float]) -> float:
    return max(abs(value) for value in values) if values else 0.0


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / max(len(values), 1))


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Build a path-level stress report for the simplified four-mode topology."""
    resolved_waveform = waveform_set or generate_waveforms(candidate)
    primary_path_current_a = resolved_waveform.switch_current_a or [0.0]
    secondary_path_current_a = resolved_waveform.diode_current_a or [0.0]
    blocking_voltage = max(
        candidate.vin_max,
        candidate.vout_target,
        max(resolved_waveform.switch_node_voltage_v) if resolved_waveform.switch_node_voltage_v else 0.0,
    )
    inductor_current_a = resolved_waveform.inductor_current_a or [0.0]

    notes = [
        "Stress is reported as simplified path-level equivalents for the four-switch Buck-Boost topology.",
        "The shared switch and rectifier slots represent the primary and secondary active switching paths rather than full per-device stress reporting.",
        f"Inductor current peak = {_peak_abs(inductor_current_a):.6f} A, average magnitude = {_mean_abs(inductor_current_a):.6f} A, RMS = {_rms(inductor_current_a):.6f} A.",
    ]
    if waveform_set is None:
        notes.append("No external waveform bundle was provided, so nominal four-mode waveforms were generated internally.")
    else:
        notes.append("Stress matches the plotted four-mode operating-point waveform bundle.")

    return StressResult(
        switch=StressMetric(
            voltage_max_v=blocking_voltage,
            current_peak_a=_peak_abs(primary_path_current_a),
            current_rms_a=_rms(primary_path_current_a),
            current_avg_a=_mean_abs(primary_path_current_a),
        ),
        rectifier=StressMetric(
            voltage_max_v=blocking_voltage,
            current_peak_a=_peak_abs(secondary_path_current_a),
            current_rms_a=_rms(secondary_path_current_a),
            current_avg_a=_mean_abs(secondary_path_current_a),
        ),
        notes=notes,
    )
