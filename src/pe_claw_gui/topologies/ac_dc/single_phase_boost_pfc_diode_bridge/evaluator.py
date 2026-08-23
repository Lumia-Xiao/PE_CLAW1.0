"""Evaluation/report assembly for the single-phase boost PFC topology."""

from __future__ import annotations

from ....models.design_report import DesignReport
from ....models.device_result import DeviceSelectionResult
from ....models.geometry_result import GeometryResult
from ....models.loss_result import LossResult
from ....models.magnetic_result import MagneticResult
from ....models.operating_point import OperatingPoint
from ....models.stress_result import StressResult
from ....models.thermal_result import ThermalResult
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from ...base.result import TopologyResult
from ...base.spec import TopologySpec
from .stress import extract_stress
from .waveform import generate_waveforms


def evaluate(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
) -> TopologyResult:
    """Build a first-pass PFC electrical summary for downstream previews."""

    metadata = candidate.metadata
    summary_lines = [
        f"Topology: {candidate.display_name}",
        "Boost PFC first-pass synthesis = CCM line-cycle envelope model",
        f"Vac_nom = {candidate.vin_nom:.4f} Vrms",
        f"Vdc target = {candidate.vout_target:.4f} V",
        f"Pout = {candidate.pout_target:.4f} W",
        f"Fsw = {candidate.fs_hz:.4f} Hz",
        f"Boost duty at nominal peak = {candidate.duty_nom:.6f}",
        f"Lboost target = {candidate.inductance_h * 1e6:.6f} uH",
        f"Cdc target = {candidate.capacitance_f * 1e6:.6f} uF",
        f"Electrical line Irms = {float(metadata['electrical_ideal_input_current_rms_a']):.6f} A",
        f"Sizing line Irms = {float(metadata['sizing_input_current_rms_a']):.6f} A",
        f"Bridge recommended VRRM = {float(metadata['recommended_diode_vrrm_v']):.6f} V",
    ]
    if waveform_set is not None:
        summary_lines.append(f"Waveform mode = {waveform_set.mode}")
        summary_lines.append(f"Line-cycle readback points = {len(waveform_set.time_s)}")
    if stress_result is not None:
        summary_lines.append(f"Boost switch voltage stress = {stress_result.switch.voltage_max_v:.6f} V")
        summary_lines.append(f"Boost diode reverse stress = {stress_result.rectifier.voltage_max_v:.6f} V")

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=bool(candidate.feasible),
        summary_lines=summary_lines,
        notes=[
            "Boost PFC first-pass model is suitable for topology-level sizing and semiconductor preview only.",
            "THD, control-loop compensation, EMI filter interaction, inrush, and detailed line-cycle loss are not signed off in this stage.",
            "Electrical comparison currents and conservative hardware-sizing currents are reported separately.",
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
    """Build a first-pass PFC design report for staged pipeline integration."""

    if waveform_set is None:
        waveform_set = generate_waveforms(candidate, operating_point=operating_point)
    if stress_result is None:
        stress_result = extract_stress(candidate, waveform_set=waveform_set)
    if topology_result is None:
        topology_result = evaluate(candidate, waveform_set=waveform_set, stress_result=stress_result)

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(notes=["PFC semiconductor preview is attached by run_device_pipeline."]),
        loss=LossResult(notes=["PFC detailed loss calculation is pending; Step 5/6 only exposes device-selection stresses."]),
        magnetic=MagneticResult(
            summary="Boost inductor design is pending.",
            notes=["Boost inductor target is available, but magnetic candidate search is not wired in this stage."],
        ),
        thermal=ThermalResult(notes=["PFC thermal aggregation is pending beyond device-stage preview."]),
        geometry=GeometryResult(notes=["PFC hardware overview is pending beyond selected bridge/switch/diode previews."]),
        topology_result=topology_result,
        notes=[
            "Single-phase boost PFC semiconductor preview maps boost switch, independent boost diode, and input bridge rectifier.",
            "PFC remains a planned topology; this report is a staged handoff for device and bridge selector integration.",
        ],
    )
