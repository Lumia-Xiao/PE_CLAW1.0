"""First-pass stress estimates for the single-phase full-bridge inverter."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Return first-pass switch stress for the inverter bridge."""

    metadata = candidate.metadata
    current_peak = max(abs(candidate.il_peak), abs(candidate.il_valley))
    is_tcm = str(candidate.mode_capable).startswith("tcm_")
    if is_tcm:
        current_peak = max(current_peak, abs(float(metadata.get("tcm_i_peak_max_a", current_peak))))
        current_rms = float(metadata.get("tcm_i_rms_a", metadata.get("iac_rms_a", 0.0)))
    elif waveform_set is not None and waveform_set.inductor_current_a:
        current_peak = float(metadata["iac_peak_a"])
        current_rms = float(metadata["iac_rms_a"])
    else:
        current_rms = float(metadata["iac_rms_a"])
    metric = StressMetric(
        voltage_max_v=float(metadata["vdc_nom_v"]),
        current_peak_a=current_peak,
        current_rms_a=current_rms,
    )
    return StressResult(
        switch=metric,
        rectifier=metric,
        notes=[
            (
                "First-pass TCM inverter switch stress uses Vdc blocking voltage and triangular-current envelope RMS/peak."
                if is_tcm
                else "First-pass inverter switch stress uses Vdc blocking voltage and sinusoidal AC current."
            ),
            "Antiparallel/freewheel diode stress is mirrored from switch current until dead-time and device loss segmentation are implemented.",
            (
                "TCM variable-frequency switching-cycle details remain first-pass envelope estimates."
                if is_tcm
                else "PWM ripple current stress is pending."
            ),
        ],
    )
