"""Buck topology evaluation."""

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
    """Evaluate the Buck candidate into a mode-aware topology summary."""
    summary_lines = [
        f"Topology: {candidate.display_name}",
        f"Vin_nom = {candidate.vin_nom:.4f} V",
        f"Duty_nom = {candidate.duty_nom:.6f}",
        f"L = {candidate.inductance_h * 1e6:.6f} uH",
        f"C = {candidate.capacitance_f * 1e6:.6f} uF",
        f"Nominal mode capability = {candidate.mode_capable.replace('_', '/').upper()}",
        f"Nominal boundary load ratio = {candidate.boundary_load_ratio:.6f}",
        f"Nominal CCM validity = {candidate.ccm_valid}",
    ]
    if waveform_set is not None:
        summary_lines.append(f"Waveform mode = {waveform_set.mode}")
        summary_lines.append(f"Waveforms generated at Vin = {waveform_set.operating_vin_v:.4f} V")
        if waveform_set.t_zero_current_s is not None:
            summary_lines.append(f"Zero-current interval = {waveform_set.t_zero_current_s * 1e6:.6f} us")
    if stress_result is not None:
        summary_lines.append(f"Switch Vmax = {stress_result.switch.voltage_max_v:.4f} V")
        summary_lines.append(f"Diode Irms = {(stress_result.rectifier.current_rms_a or 0.0):.4f} A")

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=True,
        summary_lines=summary_lines,
        notes=["Buck diode-rectified unidirectional topology now resolves CCM and DCM automatically by operating point."],
    )


def build_report(
    spec: TopologySpec,
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
    topology_result: TopologyResult | None = None,
) -> DesignReport:
    """Build the runtime design report for the unified Buck plugin."""
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
        notes=["Runtime report assembled by the unified Buck diode-rectified unidirectional plugin."],
    )
