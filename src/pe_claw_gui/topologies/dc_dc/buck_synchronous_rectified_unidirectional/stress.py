"""Synchronous Buck stress extraction."""

from __future__ import annotations

import math

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .waveform import generate_waveforms


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / max(len(values), 1))


def _mean_abs(values: list[float]) -> float:
    return sum(abs(value) for value in values) / max(len(values), 1)


def _peak_abs(values: list[float]) -> float:
    return max(abs(value) for value in values) if values else 0.0


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Build a synchronous Buck stress report from waveform data."""
    resolved_waveform = waveform_set or generate_waveforms(candidate)
    high_side_current_a = resolved_waveform.switch_current_a or [0.0]
    low_side_current_a = resolved_waveform.diode_current_a or [0.0]
    low_side_abs_a = [abs(value) for value in low_side_current_a]

    notes = [
        "Stress extracted from waveform-resolved synchronous Buck device currents.",
        "The rectifier stress block is reused as the low-side synchronous MOSFET stress for compatibility.",
    ]
    if waveform_set is None:
        notes.append("No external waveform bundle was provided, so nominal synchronous Buck waveforms were generated internally.")
    else:
        notes.append("Stress matches the plotted synchronous Buck operating-point waveform bundle.")

    return StressResult(
        switch=StressMetric(
            voltage_max_v=max(candidate.vin_max, max(resolved_waveform.switch_node_voltage_v)),
            current_peak_a=_peak_abs(high_side_current_a),
            current_rms_a=_rms(high_side_current_a),
            current_avg_a=_mean_abs(high_side_current_a),
        ),
        rectifier=StressMetric(
            voltage_max_v=candidate.vin_max,
            current_peak_a=_peak_abs(low_side_current_a),
            current_rms_a=_rms(low_side_abs_a),
            current_avg_a=_mean_abs(low_side_current_a),
        ),
        notes=notes,
    )
