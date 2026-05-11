"""Inverting diode Buck-Boost topology evaluation."""

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


def evaluate(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
) -> TopologyResult:
    """Evaluate the inverting diode Buck-Boost candidate into a topology summary."""
    summary_lines = [
        "Topology = Buck-Boost diode rectified unidirectional",
        "Output polarity = Inverted",
        f"Nominal mode capability = {candidate.mode_capable.replace('_', '/').upper()}",
        f"Nominal boundary load ratio = {candidate.boundary_load_ratio:.6f}",
        f"Nominal CCM validity = {candidate.ccm_valid}",
        f"Nominal duty = {candidate.duty_nom:.6f}",
    ]
    if waveform_set is not None:
        summary_lines.append(f"Waveform mode = {waveform_set.mode}")
        summary_lines.append(f"Waveform Vin = {waveform_set.operating_vin_v:.4f} V")
        summary_lines.append(f"Waveform load ratio = {waveform_set.load_ratio:.6f}")
        if waveform_set.t_zero_current_s is not None:
            summary_lines.append(f"Zero-current interval = {waveform_set.t_zero_current_s * 1e6:.6f} us")
    if stress_result is not None:
        summary_lines.append(f"Switch RMS current = {(stress_result.switch.current_rms_a or 0.0):.6f} A")
        summary_lines.append(f"Diode RMS current = {(stress_result.rectifier.current_rms_a or 0.0):.6f} A")
        summary_lines.append(f"Blocking voltage estimate = {stress_result.switch.voltage_max_v:.6f} V")

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=True,
        summary_lines=summary_lines,
        notes=[
            "Inverting Buck-Boost diode rectified unidirectional topology.",
            "Design calculations use output-voltage magnitude while the physical output polarity is inverted.",
            "CCM/DCM operating mode is resolved from the operating point.",
            "Waveform and stress extraction are topology-specific and waveform-based.",
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
    """Build the runtime design report for the inverting Buck-Boost plugin."""
    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(notes=["Device selection is not implemented yet."]),
        loss=LossResult(notes=["Loss calculation is not implemented yet."]),
        magnetic=MagneticResult(summary="Magnetic design is not implemented yet.", notes=["Placeholder stage."]),
        thermal=ThermalResult(notes=["Thermal evaluation is not implemented yet."]),
        geometry=GeometryResult(notes=["Geometry estimation is not implemented yet."]),
        topology_result=topology_result,
        notes=["Runtime report assembled by the inverting diode-rectified Buck-Boost plugin."],
    )
