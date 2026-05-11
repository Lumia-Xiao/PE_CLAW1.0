"""Synchronous Boost stress extraction."""

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
    """Build a synchronous Boost stress report from waveform data."""
    resolved_waveform = waveform_set or generate_waveforms(candidate)
    switch_current_a = resolved_waveform.switch_current_a or [0.0]
    synchronous_current_a = resolved_waveform.diode_current_a or [0.0]
    synchronous_abs_a = [abs(value) for value in synchronous_current_a]
    blocking_voltage = max(candidate.vout_target, max(resolved_waveform.switch_node_voltage_v))

    notes = [
        "Stress extracted from waveform-resolved synchronous Boost device currents.",
        "The rectifier stress block is reused as the synchronous rectifying-switch stress for compatibility.",
    ]
    if waveform_set is None:
        notes.append("No external waveform bundle was provided, so nominal synchronous Boost waveforms were generated internally.")
    else:
        notes.append("Stress matches the plotted synchronous Boost operating-point waveform bundle.")

    return StressResult(
        switch=StressMetric(
            voltage_max_v=blocking_voltage,
            current_peak_a=_peak_abs(switch_current_a),
            current_rms_a=_rms(switch_current_a),
            current_avg_a=_mean_abs(switch_current_a),
        ),
        rectifier=StressMetric(
            voltage_max_v=blocking_voltage,
            current_peak_a=_peak_abs(synchronous_current_a),
            current_rms_a=_rms(synchronous_abs_a),
            current_avg_a=_mean_abs(synchronous_current_a),
        ),
        notes=notes,
    )
