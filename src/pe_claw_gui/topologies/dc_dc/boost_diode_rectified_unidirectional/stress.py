"""Diode Boost stress extraction."""

from __future__ import annotations

import math

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .waveform import generate_waveforms


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / max(len(values), 1))


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Build a diode Boost stress report from waveform-resolved device currents."""
    resolved_waveform = waveform_set or generate_waveforms(candidate)
    switch_current_a = resolved_waveform.switch_current_a or [0.0]
    diode_current_a = resolved_waveform.diode_current_a or [0.0]
    blocking_voltage = max(candidate.vout_target, max(resolved_waveform.switch_node_voltage_v))

    notes = [
        f"Waveform-based operating-point stress extraction for diode-rectified Boost in {resolved_waveform.mode}.",
        "CCM/DCM mode is resolved from the requested operating point before stress extraction.",
    ]
    if waveform_set is None:
        notes.append("No external waveform bundle was provided, so nominal diode Boost waveforms were generated internally.")
    else:
        notes.append("Stress matches the plotted diode Boost operating-point waveform bundle.")

    return StressResult(
        switch=StressMetric(
            voltage_max_v=blocking_voltage,
            current_peak_a=max(switch_current_a),
            current_rms_a=_rms(switch_current_a),
        ),
        rectifier=StressMetric(
            voltage_max_v=blocking_voltage,
            current_peak_a=max(diode_current_a),
            current_avg_a=_mean(diode_current_a),
            current_rms_a=_rms(diode_current_a),
        ),
        notes=notes,
    )
