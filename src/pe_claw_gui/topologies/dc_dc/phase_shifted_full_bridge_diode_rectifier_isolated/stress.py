"""First-pass PSFB stress extraction."""

from __future__ import annotations

from ....models.stress_result import StressMetric, StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def extract_stress(candidate: TopologyCandidate, waveform_set: WaveformSet | None = None) -> StressResult:
    """Build primary switch and secondary rectifier stress estimates."""

    psfb = candidate.metadata["psfb"]
    primary_model = psfb.get("primary_current_model")
    primary_model = primary_model if isinstance(primary_model, dict) else {}
    switches = primary_model.get("switches")
    switches = switches if isinstance(switches, dict) else {}
    worst_switch = switches.get(primary_model.get("worst_switch_rms_position", "s1"), {})
    worst_switch = worst_switch if isinstance(worst_switch, dict) else {}
    notes = [
        "PSFB primary switch voltage is treated as the maximum DC-link voltage in this first-pass model.",
        (
            "Secondary full-bridge diode reverse stress uses the reflected high-line transformer "
            "secondary voltage; leakage/clamp spike margin is a first-pass follow-up."
        ),
    ]
    if waveform_set is not None:
        notes.append("Waveforms provide nominal readback; stress remains based on design-corner maxima.")

    return StressResult(
        switch=StressMetric(
            voltage_max_v=candidate.vin_max,
            current_peak_a=float(worst_switch.get("branch_current_peak_a", psfb["primary_peak_current_a"])),
            current_rms_a=float(worst_switch.get("branch_current_rms_a", psfb["primary_rms_current_a"])),
        ),
        rectifier=StressMetric(
            voltage_max_v=float(psfb["diode_reverse_voltage_stress_v"]),
            current_peak_a=candidate.il_peak,
            current_avg_a=float(psfb.get("rectifier_avg_current_a", 0.5 * candidate.iout)),
            current_rms_a=float(psfb["rectifier_rms_current_a"]),
        ),
        notes=notes,
    )
