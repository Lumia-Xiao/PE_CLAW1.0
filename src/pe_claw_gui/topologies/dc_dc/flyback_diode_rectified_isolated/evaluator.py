"""First-pass Flyback evaluation and report assembly."""

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
    """Evaluate the first-pass Flyback candidate into summary lines."""

    flyback = candidate.metadata["flyback"]
    summary_lines = [
        f"Topology: {candidate.display_name}",
        "Flyback first-pass synthesis = energy-balance/reflected-voltage model",
        f"Mode target = {str(flyback['mode']).upper()}",
        f"Vin_nom = {candidate.vin_nom:.4f} V",
        f"Vout = {candidate.vout_target:.4f} V",
        f"Pout = {candidate.pout_target:.4f} W",
        f"Duty_nom = {candidate.duty_nom:.6f}",
        f"Turns ratio Ns/Np = {float(flyback['turns_ratio_ns_np']):.6f}",
        f"Reflected output voltage = {float(flyback['reflected_output_voltage_primary_v']):.4f} V",
        f"Lm target = {candidate.inductance_h * 1e6:.6f} uH",
        f"Cout target = {candidate.capacitance_f * 1e6:.6f} uF",
        f"Primary Ipk = {float(flyback['primary_peak_current_a']):.6f} A",
        f"Secondary Ipk = {float(flyback['secondary_peak_current_a']):.6f} A",
        f"Stored energy = {float(flyback['coupled_inductor_target']['stored_energy_uj']):.6f} uJ",
    ]
    if waveform_set is not None:
        summary_lines.append(f"Waveform mode = {waveform_set.mode}")
        summary_lines.append(f"Waveforms generated at Vin = {waveform_set.operating_vin_v:.4f} V")
    if stress_result is not None:
        summary_lines.append(f"Switch voltage stress = {stress_result.switch.voltage_max_v:.4f} V")
        summary_lines.append(f"Rectifier reverse stress = {stress_result.rectifier.voltage_max_v:.4f} V")

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=True,
        summary_lines=summary_lines,
        notes=[
            "Flyback first-pass model is suitable for topology-level sizing only.",
            "Semiconductor selection can be attached by the pipeline; coupled-inductor search, losses, thermal, snubber, and isolation compliance are pending.",
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
    """Build a first-pass Flyback design report."""

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(notes=["Device selection is attached by the full pipeline for Flyback."]),
        loss=LossResult(notes=["Loss calculation is pending for Flyback."]),
        magnetic=MagneticResult(
            summary="Flyback coupled-inductor search is pending.",
            notes=["Coupled-inductor search is pending; only Lm and stored-energy targets are available."],
        ),
        thermal=ThermalResult(notes=["Thermal evaluation is pending for Flyback."]),
        geometry=GeometryResult(notes=["Geometry estimation is pending for Flyback."]),
        topology_result=topology_result,
        notes=[
            "Flyback first-pass design with semiconductor selection; coupled-inductor search, loss, thermal, capacitor, and artifact stages are pending.",
            "Secondary rectifier is modeled as an independent diode role for device selection.",
        ],
    )
