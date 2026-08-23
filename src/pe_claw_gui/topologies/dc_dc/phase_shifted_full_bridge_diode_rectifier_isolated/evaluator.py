"""First-pass PSFB evaluation and report assembly."""

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
    """Evaluate the first-pass PSFB candidate into summary lines."""

    psfb = candidate.metadata["psfb"]
    zvs = psfb["zvs"]
    summary_lines = [
        f"Topology: {candidate.display_name}",
        "PSFB first-pass synthesis = buck-equivalent duty-loss/ZVS evidence model",
        f"Vin_nom = {candidate.vin_nom:.4f} V",
        f"Vout = {candidate.vout_target:.4f} V",
        f"Pout = {candidate.pout_target:.4f} W",
        f"Turns ratio Np/Ns = {float(psfb['turns_ratio_np_ns']):.6f}",
        f"Effective duty nominal = {float(psfb['effective_duty_nom']):.6f}",
        f"Duty loss nominal = {float(psfb['duty_loss_nom']):.6f}",
        f"Command duty nominal = {float(psfb['command_duty_nom']):.6f}",
        f"Command duty at Vin min = {float(psfb['command_duty_at_vin_min']):.6f}",
        f"Output inductor target = {candidate.inductance_h * 1e6:.6f} uH",
        f"Output capacitor target = {candidate.capacitance_f * 1e6:.6f} uF",
        f"ZVS full-load energy margin = {_format_optional_margin(zvs.get('energy_margin'))}",
        f"ZVS min-load energy margin = {_format_optional_margin(zvs.get('min_load_energy_margin'))}",
    ]
    if waveform_set is not None:
        summary_lines.append(f"Waveform mode = {waveform_set.mode}")
        summary_lines.append(f"Waveforms generated at Vin = {waveform_set.operating_vin_v:.4f} V")
    if stress_result is not None:
        summary_lines.append(f"Primary switch stress = {stress_result.switch.voltage_max_v:.4f} V")
        summary_lines.append(f"Secondary diode reverse stress = {stress_result.rectifier.voltage_max_v:.4f} V")

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=candidate.feasible,
        summary_lines=summary_lines,
        notes=[
            "PSFB first-pass model is suitable for topology-level sizing only.",
            "Full transformer/output-inductor, semiconductor, capacitor, loss, thermal, geometry, and artifact readback is provided by the shared PE-Claw pipeline and md-first backend session.",
        ],
    )


def _format_optional_margin(value: object) -> str:
    if value is None:
        return "unavailable"
    return f"{float(value):.6f}"


def build_report(
    spec: TopologySpec,
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
    topology_result: TopologyResult | None = None,
) -> DesignReport:
    """Build a first-pass PSFB design report."""

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(notes=["PSFB device selection is provided by the shared PE-Claw device pipeline."]),
        loss=LossResult(notes=["PSFB loss readback is provided by the shared PE-Claw loss pipeline."]),
        magnetic=MagneticResult(
            summary="PSFB transformer and output-inductor searches are provided by the shared PE-Claw magnetic pipeline.",
            notes=[
                "Only buck-equivalent output-filter and ZVS target values are available.",
                "Transformer turns, leakage realization, insulation, and manufacturability are not closed yet.",
            ],
        ),
        thermal=ThermalResult(notes=["PSFB thermal readback is provided by the shared PE-Claw thermal pipeline."]),
        geometry=GeometryResult(notes=["PSFB geometry readback is provided by the shared PE-Claw geometry pipeline."]),
        topology_result=topology_result,
        notes=[
            "PSFB first-pass topology plugin; full backend/session integration is wired through the shared PE-Claw pipeline.",
            "Secondary rectifier is modeled as an independent full-bridge diode path for future device selection.",
        ],
    )
