"""Stress extraction for the three-level TZCM fixed-frequency topology."""

from __future__ import annotations

import math

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .waveform import generate_waveforms


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / max(len(values), 1))


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Extract a simplified path-level stress report for the TZCM topology."""
    if not candidate.feasible:
        return StressResult(
            switch=StressMetric(voltage_max_v=0.0, current_peak_a=0.0, current_rms_a=0.0, current_avg_a=0.0),
            rectifier=StressMetric(voltage_max_v=0.0, current_peak_a=0.0, current_rms_a=0.0, current_avg_a=0.0),
            notes=[f"Stress extraction skipped because the TZCM design is infeasible: {candidate.failure_reason}."],
        )

    resolved_waveform = waveform_set or generate_waveforms(candidate)
    primary_path_current = resolved_waveform.switch_current_a or [0.0]
    secondary_path_current = resolved_waveform.diode_current_a or [0.0]
    peak_current = max(
        abs(candidate.current_ip_minus_a or 0.0),
        candidate.current_i1_a or 0.0,
        candidate.current_i2_a or 0.0,
    )
    blocking_voltage = resolved_waveform.operating_vin_v / 2.0

    notes = [
        "The shared switch and rectifier stress slots represent simplified primary and secondary switching-path equivalents for the three-level converter.",
        "Per-device voltage stress is reported as an approximate Vdc/2 blocking estimate.",
    ]
    if waveform_set is None:
        notes.append("Nominal TZCM waveforms were generated internally for the stress calculation.")
    else:
        notes.append("Stress is extracted from the plotted TZCM waveform bundle.")

    return StressResult(
        switch=StressMetric(
            voltage_max_v=blocking_voltage,
            current_peak_a=max(peak_current, max(abs(value) for value in primary_path_current)),
            current_rms_a=_rms(primary_path_current),
            current_avg_a=sum(abs(value) for value in primary_path_current) / max(len(primary_path_current), 1),
        ),
        rectifier=StressMetric(
            voltage_max_v=blocking_voltage,
            current_peak_a=max(peak_current, max(abs(value) for value in secondary_path_current)),
            current_rms_a=_rms(secondary_path_current),
            current_avg_a=sum(abs(value) for value in secondary_path_current) / max(len(secondary_path_current), 1),
        ),
        notes=notes,
    )
