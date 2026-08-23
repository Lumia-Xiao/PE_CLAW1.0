"""Evaluation/report assembly for the single-phase Totem-Pole PFC topology."""

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
    """Build a first-pass Totem-Pole PFC electrical summary for downstream reports."""

    metadata = candidate.metadata
    summary_lines = [
        f"Topology: {candidate.display_name}",
        "Totem-Pole PFC first-pass synthesis = CCM full-line-cycle envelope model",
        f"Vac_nom = {candidate.vin_nom:.4f} Vrms",
        f"Vdc target = {candidate.vout_target:.4f} V",
        f"Pout = {candidate.pout_target:.4f} W",
        f"Fsw = {candidate.fs_hz:.4f} Hz",
        f"Boost duty at nominal peak = {candidate.duty_nom:.6f}",
        f"Lboost target = {candidate.inductance_h * 1e6:.6f} uH",
        f"Cdc target = {candidate.capacitance_f * 1e6:.6f} uF",
        f"Line Irms estimate = {float(metadata['i_line_rms_a']):.6f} A",
        "Rectifier path = bridgeless HF/LF active switches; no diode bridge or boost diode.",
    ]
    if waveform_set is not None:
        summary_lines.append(f"Waveform mode = {waveform_set.mode}")
        summary_lines.append(f"Full-line-cycle readback points = {len(waveform_set.time_s)}")
    if stress_result is not None:
        summary_lines.append(f"HF switch voltage stress = {stress_result.switch.voltage_max_v:.6f} V")
        summary_lines.append(f"LF switch voltage stress = {stress_result.rectifier.voltage_max_v:.6f} V")

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=bool(candidate.feasible),
        summary_lines=summary_lines,
        notes=[
            "Totem-Pole PFC first-pass model is suitable for preliminary engineering sizing and md-first execution.",
            "Zero-crossing control, reverse conduction, common-mode EMI, inrush, THD, and final gate-timing validation remain engineering review items.",
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
    """Build a first-pass report for executable Totem-Pole PFC pipelines."""

    if topology_result is None:
        topology_result = evaluate(candidate, waveform_set=waveform_set, stress_result=stress_result)
    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
        notes=[
            "Single-phase Totem-Pole PFC maps HF and LF active switch roles into the executable first-pass pipeline.",
            "This first-pass design does not sign off zero-crossing control, deadtime, reverse conduction, EMI/THD, harmonic compliance, layout parasitics, or production gate timing.",
        ],
    )
