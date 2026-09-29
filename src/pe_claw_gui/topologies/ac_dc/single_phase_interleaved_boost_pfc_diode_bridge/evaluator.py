"""Electrical evaluation summary for the independent interleaved PFC core."""

from __future__ import annotations

from ....models.design_report import DesignReport
from ....models.operating_point import OperatingPoint
from ....models.stress_result import StressResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from ...base.result import TopologyResult
from ...base.spec import TopologySpec
from .stress import extract_phase_stress
from .waveform import generate_waveforms


def evaluate(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
) -> TopologyResult:
    """Summarize per-phase and aggregate electrical design relationships."""

    resolved_waveform = waveform_set or generate_waveforms(candidate)
    phase_stress = extract_phase_stress(candidate, waveform_set=resolved_waveform)
    resolved_stress = stress_result or phase_stress.shared_result
    wave_metadata = resolved_waveform.metadata
    ripple = wave_metadata["interleaved_ripple_pp_a"]
    summary_lines = [
        f"Topology: {candidate.display_name}",
        "Two-phase CCM Boost PFC electrical envelope; 180-degree interleaving and ideal 50/50 sharing.",
        f"Nominal line input current = {float(candidate.metadata['electrical_input_current_rms_a']):.6f} Arms total.",
        f"Nominal phase current = {float(candidate.metadata['phase_current_rms_a']['phase_1']):.6f} Arms per phase.",
        f"Per-phase total series inductance = {candidate.inductance_h * 1e6:.6f} uH.",
        f"DC-link capacitance requirement = {candidate.capacitance_f * 1e6:.6f} uF.",
        f"Worst nominal aggregate switching ripple = {float(ripple['worst_aggregate_ripple_pp_a']):.6f} App.",
        f"Phase 1 switch RMS current = {resolved_stress.switch.current_rms_a or 0.0:.6f} Arms.",
        f"Phase 1 Boost-diode RMS current = {resolved_stress.rectifier.current_rms_a or 0.0:.6f} Arms.",
        f"Input bridge RMS current = {phase_stress.input_bridge_rectifier.current_rms_a or 0.0:.6f} Arms total.",
        f"Phase 2 switch RMS current = {phase_stress.phase_stress['phase_2'].main_switch.current_rms_a or 0.0:.6f} Arms.",
        f"Phase 2 Boost-diode RMS current = {phase_stress.phase_stress['phase_2'].boost_diode.current_rms_a or 0.0:.6f} Arms.",
    ]
    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=candidate.feasible,
        summary_lines=summary_lines,
        notes=[
            "Aggregate inductor RMS includes the summed line envelope and residual interleaved ripple; device-loss RMS combines independent phase RMS values by root-sum-square.",
            "Phase-level stress is available through the typed InterleavedPFCStress adapter; common StressResult slots represent phase_1.",
            "Switching edges, detailed loss, control-loop, THD, EMI, and phase mismatch are outside this first-pass evaluation.",
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
    """Assemble the topology-local report used while downstream stages are planned."""

    if waveform_set is None:
        waveform_set = generate_waveforms(candidate, operating_point=operating_point)
    if stress_result is None:
        stress_result = extract_phase_stress(candidate, waveform_set=waveform_set).shared_result
    if topology_result is None:
        topology_result = evaluate(
            candidate,
            waveform_set=waveform_set,
            stress_result=stress_result,
        )

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
        notes=[
            "Two-phase interleaved Boost PFC is registered as a planned topology; this report contains topology-local electrical results only.",
            "Input-bridge, semiconductor, magnetic, loss, thermal, geometry, and efficiency stages remain pending for later plan steps.",
        ],
    )
