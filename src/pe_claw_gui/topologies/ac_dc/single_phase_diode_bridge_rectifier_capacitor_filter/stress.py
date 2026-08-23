"""Stress estimates for the Phase 1 AC-DC diode bridge rectifier."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> StressResult:
    """Return first-pass diode bridge stress estimates."""

    vrrm_stress_v = float(candidate.metadata["diode_vrrm_stress_v"])
    per_diode_avg_current_a = float(candidate.metadata["per_diode_avg_current_a"])
    simulation = candidate.metadata.get("pulse_simulation")
    if isinstance(simulation, dict) and simulation.get("simulation_succeeded"):
        per_diode_avg_current_a = float(simulation["per_diode_avg_current_a"])
        per_diode_peak_current_a = float(simulation["per_diode_peak_current_a"])
        per_diode_rms_current_a = float(simulation["per_diode_rms_current_a"])
        notes = [
            "Phase 2 diode bridge stress uses Rs-based pulse-current simulation.",
            "Per-diode peak and RMS current are simulated over the final settled line cycle.",
        ]
        warnings = candidate.metadata.get("pulse_simulation_warnings")
        if isinstance(warnings, list):
            notes.extend(str(warning) for warning in warnings)
    else:
        per_diode_peak_current_a = None
        per_diode_rms_current_a = None
        notes = [
            "Phase 1 diode bridge stress uses VRRM = AC peak and per-diode average current = Idc/2.",
            "Diode peak current requires Phase 2 Rs-based pulse-current simulation.",
            "Diode RMS current requires Phase 2 Rs-based pulse-current simulation.",
        ]
    return StressResult(
        switch=StressMetric(
            voltage_max_v=vrrm_stress_v,
            current_peak_a=0.0,
            current_rms_a=0.0,
            current_avg_a=0.0,
        ),
        rectifier=StressMetric(
            voltage_max_v=vrrm_stress_v,
            current_peak_a=per_diode_peak_current_a,
            current_rms_a=per_diode_rms_current_a,
            current_avg_a=per_diode_avg_current_a,
        ),
        notes=notes,
    )
