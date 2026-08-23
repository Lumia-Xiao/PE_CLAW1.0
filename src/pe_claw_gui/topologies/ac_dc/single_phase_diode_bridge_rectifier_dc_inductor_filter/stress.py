"""Stress estimates for the Phase 1 AC-DC DC-side inductor rectifier."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
) -> StressResult:
    """Return first-pass diode bridge stress estimates."""

    simulation = candidate.metadata.get("state_space_simulation")
    if waveform_set is not None and isinstance(waveform_set.metadata.get("ac_dc_dc_inductor_metrics"), dict):
        simulation = waveform_set.metadata["ac_dc_dc_inductor_metrics"]

    if isinstance(simulation, dict) and simulation.get("simulation_succeeded"):
        rectifier_peak_a = float(simulation["per_diode_peak_current_a"])
        rectifier_rms_a = float(simulation["per_diode_rms_current_a"])
        rectifier_avg_a = float(simulation["per_diode_avg_current_a"])
        notes = [
            "Phase 2 uses state-space DC-side inductor simulation.",
            "Per-diode peak, RMS, and average current are simulated over the final settled line cycle.",
            "Surge and selected bridge module validation are pending.",
        ]
    else:
        rectifier_peak_a = float(candidate.metadata["il_peak_est_a"])
        rectifier_rms_a = float(candidate.metadata["per_diode_rms_current_est_a"])
        rectifier_avg_a = float(candidate.metadata["per_diode_average_current_est_a"])
        notes = [
            "Phase 1 diode bridge stress uses small-reactor capacitor-input first-pass estimates.",
            "Pulsed-current RMS/peak stress should be taken from the state-space simulation when available.",
            "Per-diode RMS current fallback uses Idc/sqrt(2); surge and selected bridge validation are pending.",
        ]

    return StressResult(
        switch=StressMetric(
            voltage_max_v=0.0,
            current_peak_a=0.0,
            current_rms_a=0.0,
            current_avg_a=0.0,
        ),
        rectifier=StressMetric(
            voltage_max_v=float(candidate.metadata["diode_reverse_stress_v"]),
            current_peak_a=rectifier_peak_a,
            current_rms_a=rectifier_rms_a,
            current_avg_a=rectifier_avg_a,
        ),
        notes=notes,
    )
