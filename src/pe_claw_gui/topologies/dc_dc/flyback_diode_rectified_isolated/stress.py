"""First-pass Flyback stress extraction."""

from __future__ import annotations

import math

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Build switch and rectifier stress estimates for the Flyback candidate."""

    flyback = candidate.metadata["flyback"]
    notes = [
        "Flyback first-pass stress uses reflected-output voltage plus the configured clamp/spike margin.",
        "Leakage ringing and snubber dynamics are not solved in this step.",
    ]
    switch_peak_a = float(flyback["primary_peak_current_a"])
    switch_rms_a = float(flyback["primary_switch_rms_current_a"])
    diode_peak_a = float(flyback["secondary_peak_current_a"])
    diode_avg_a = float(flyback["secondary_avg_current_a"])
    diode_rms_a = float(flyback["secondary_rms_current_a"])
    if waveform_set is not None:
        switch_peak_a = max(waveform_set.switch_current_a, default=0.0)
        switch_rms_a = _rms(waveform_set.switch_current_a)
        diode_peak_a = max(waveform_set.diode_current_a, default=0.0)
        diode_avg_a = sum(waveform_set.diode_current_a) / max(len(waveform_set.diode_current_a), 1)
        diode_rms_a = _rms(waveform_set.diode_current_a)
        notes.append("Current stresses are refreshed from the generated operating-point waveform.")

    return StressResult(
        switch=StressMetric(
            voltage_max_v=float(flyback["switch_voltage_stress_v"]),
            current_peak_a=switch_peak_a,
            current_rms_a=switch_rms_a,
        ),
        rectifier=StressMetric(
            voltage_max_v=float(flyback["diode_reverse_voltage_stress_v"]),
            current_peak_a=diode_peak_a,
            current_avg_a=diode_avg_a,
            current_rms_a=diode_rms_a,
        ),
        notes=notes,
    )


def _rms(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))
