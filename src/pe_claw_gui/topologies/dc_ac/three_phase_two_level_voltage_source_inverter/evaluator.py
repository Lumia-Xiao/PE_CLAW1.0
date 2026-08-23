"""Evaluation/report assembly for the three-phase two-level inverter."""

from __future__ import annotations

from ....models.design_report import DesignReport
from ....models.operating_point import OperatingPoint
from ....models.stress_result import StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from ...base.result import TopologyResult
from ...base.spec import TopologySpec


def evaluate(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
) -> TopologyResult:
    """Build compact first-pass three-phase inverter evaluation lines."""

    metadata = candidate.metadata
    summary_lines = [
        "Three-phase two-level SPWM first-pass estimate completed.",
        f"Modulation index = {_fmt(metadata.get('modulation_index'))} (limit {_fmt(metadata.get('modulation_limit'))}).",
        f"Output inductor per phase = {_fmt(candidate.inductance_h * 1e6)} uH from conservative current-ripple target.",
        (
            f"DC-link capacitor proxy = {_fmt(candidate.capacitance_f * 1e6)} uF from "
            "three-phase switching-ripple first-pass target."
        ),
        "Operating PF is referenced to phase voltage and phase current.",
        "Line-line voltage waveforms have a 30 deg offset relative to phase voltage.",
    ]
    if waveform_set is not None and waveform_set.metadata.get("three_phase_two_level_spwm_waveforms"):
        summary_lines.extend(
            [
                f"SPWM waveform preview samples = {int(waveform_set.metadata.get('spwm_preview_sample_count', 0))}.",
                f"Operating load ratio = {_fmt(waveform_set.load_ratio)}.",
                f"Operating PF = {_fmt(waveform_set.metadata.get('operating_power_factor'))}.",
                "Phase-voltage/current alignment is shown directly for PF checks.",
                f"DC-link capacitor current proxy rms = {_fmt(waveform_set.metadata.get('dc_link_capacitor_current_rms_pwm_a') or waveform_set.metadata.get('dc_link_capacitor_current_rms_a'))} A.",
                "Waveform preview is not a dead-time/Coss/parasitic transition simulation.",
            ]
        )
    summary_lines.extend(
        [
            "DC-link capacitor selection is available after Run Capacitor.",
            "Per-phase output-inductor magnetic realization is available after Run Magnetics.",
            "Loss stage available: six-switch semiconductor, DC-link capacitor, and 3x per-phase inductor first-pass operating loss.",
            "Efficiency sweep available: fixed-hardware load sweep and PF diagnostics.",
        ]
    )
    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=bool(metadata.get("modulation_valid", False)),
        summary_lines=summary_lines,
        notes=[
            "Output inductor is per phase.",
            "Three output inductors are represented by one per-phase magnetic design; system magnetic loss is 3x the per-inductor operating evaluation.",
            "Main-switch selection represents six bridge positions.",
            "DC-link capacitor selection uses an SxP electrolytic bank and a first-pass PWM-level switch-state current proxy.",
            "Loss and efficiency remain first-pass; no SVPWM/DPWM, dead-time, Coss, parasitic ringing, harmonic ESR, or FEA/CFD model is included.",
        ],
    )


def build_report(
    spec: TopologySpec,
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
    topology_result: TopologyResult | None = None,
) -> DesignReport:
    """Build the design report for first-pass three-phase inverter synthesis."""

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
        notes=[
            "Output inductor is sized as a per-phase CCM two-level SPWM first-pass estimate.",
            "DC-link capacitor selection uses a three-phase PWM-level switch-state RMS proxy, with low-frequency comparison retained.",
            "Semiconductor stress uses one selected main switch repeated across six bridge positions.",
            "Magnetics uses a per-phase output-inductor request; system magnetic loss is 3x the per-inductor operating evaluation.",
            "Efficiency sweep uses fixed selected hardware for load and PF diagnostics.",
        ],
    )


def _fmt(value) -> str:
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "-"
