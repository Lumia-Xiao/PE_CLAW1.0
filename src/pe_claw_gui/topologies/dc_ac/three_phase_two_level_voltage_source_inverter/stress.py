"""First-pass stress estimates for the three-phase two-level inverter."""

from __future__ import annotations

import math

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Return first-pass per-position switch stress for the six-switch bridge."""

    metadata = candidate.metadata
    waveform_metadata = waveform_set.metadata if waveform_set is not None else {}
    actual_peak_a = float(waveform_metadata.get("phase_current_peak_abs_a", 0.0))
    actual_rms_a = float(waveform_metadata.get("phase_current_total_rms_a", 0.0))
    current_peak_a = actual_peak_a or (
        float(metadata["i_phase_peak_a"]) + 0.5 * float(metadata["delta_il_pp_a"])
    )
    current_rms_a = actual_rms_a or float(metadata["i_phase_rms_a"])
    actual_branch_currents = waveform_metadata.get("three_phase_vsi_branch_currents")
    branch_note = (
        "Actual complete Q1-Q6 branch currents are persisted in waveform metadata."
        if isinstance(actual_branch_currents, dict)
        else "Detailed Q1-Q6 branch currents are unavailable without a waveform."
    )
    metric = StressMetric(
        voltage_max_v=float(metadata["vdc_nom_v"]),
        current_peak_a=current_peak_a,
        current_rms_a=current_rms_a,
    )
    return StressResult(
        switch=metric,
        rectifier=metric,
        notes=[
            "First-pass three-phase two-level inverter switch stress uses Vdc blocking voltage.",
            "Waveform-backed phase RMS/peak includes the integrated three-phase SPWM current ripple; this replaces the six-switch SPWM approximation when a waveform is present.",
            branch_note,
            "Q1-Q6 branch metrics include the complete MOSFET-plus-antiparallel-diode path; channel/diode split remains unavailable.",
        ],
    )
