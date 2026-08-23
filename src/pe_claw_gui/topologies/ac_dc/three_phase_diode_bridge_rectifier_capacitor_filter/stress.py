"""Stress estimates for the Phase 1 three-phase AC-DC diode bridge."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> StressResult:
    """Return first-pass uncontrolled three-phase diode bridge stress estimates."""

    metadata = candidate.metadata
    simulation = metadata.get("three_phase_pulse_simulation")
    if waveform_set is not None:
        waveform_metrics = waveform_set.metadata.get("ac_dc_three_phase_rectifier_metrics")
        if isinstance(waveform_metrics, dict):
            simulation = waveform_metrics
    reverse_stress_v = float(metadata["diode_reverse_stress_v"])
    if isinstance(simulation, dict) and simulation.get("simulation_succeeded"):
        diode_peak_a = max(float(simulation[f"diode_d{index}_peak_current_a"]) for index in range(1, 7))
        diode_rms_a = max(float(simulation[f"diode_d{index}_rms_current_a"]) for index in range(1, 7))
        diode_avg_a = max(float(simulation[f"diode_d{index}_avg_current_a"]) for index in range(1, 7))
        notes = [
            "Six diode currents use the final settled charging-pulse simulation.",
            "Surge, reverse recovery, and commutation overlap remain outside the first-stage model.",
        ]
    else:
        diode_peak_a = None
        diode_rms_a = float(metadata["per_diode_rms_current_est_a"])
        diode_avg_a = float(metadata["per_diode_average_current_est_a"])
        notes = ["Fallback diode current uses the initial continuous-current estimate."]
    return StressResult(
        switch=StressMetric(
            voltage_max_v=reverse_stress_v,
            current_peak_a=0.0,
            current_rms_a=0.0,
            current_avg_a=0.0,
        ),
        rectifier=StressMetric(
            voltage_max_v=reverse_stress_v,
            current_peak_a=diode_peak_a,
            current_rms_a=diode_rms_a,
            current_avg_a=diode_avg_a,
        ),
        notes=notes,
    )
