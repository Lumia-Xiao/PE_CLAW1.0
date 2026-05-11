"""Topology evaluation for the simplified four-mode four-switch Buck-Boost converter."""

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
from .mode import build_operating_state


def evaluate(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
) -> TopologyResult:
    """Evaluate the simplified four-mode candidate into a topology summary."""
    if waveform_set is not None:
        state = build_operating_state(
            candidate,
            operating_point=OperatingPoint(vin_v=waveform_set.operating_vin_v, load_ratio=waveform_set.load_ratio),
        )
    else:
        state = build_operating_state(candidate)

    summary_lines = [
        "Topology = Four-Switch Buck-Boost Simplified Four-Mode",
        f"Operating mode = {state.mode}",
        f"Vin = {state.vin:.6f} V",
        f"Vout = {state.vout:.6f} V",
        f"Load ratio = {state.load_ratio:.6f}",
        f"Duty clamp = {state.duty_clamp:.6f}",
        f"Transition band ratio = {state.transition_band_ratio:.6f}",
        f"d2 = {state.d2:.6f}",
        f"d3 = {state.d3:.6f}",
        f"Inductor current min = {state.il_min:.6f} A",
        f"Inductor current max = {state.il_max:.6f} A",
        f"Estimated ripple = {state.delta_il:.6f} A",
    ]
    if stress_result is not None:
        summary_lines.append(f"Primary path RMS current = {(stress_result.switch.current_rms_a or 0.0):.6f} A")
        summary_lines.append(f"Secondary path RMS current = {(stress_result.rectifier.current_rms_a or 0.0):.6f} A")

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=True,
        summary_lines=summary_lines,
        notes=[
            "Simplified fixed-frequency four-mode smooth-transition model.",
            "Intended for full-range waveform analysis rather than soft-switching or optimal control.",
            "Waveforms and stress are reported as path-level equivalents to stay compatible with the shared result models.",
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
    """Build the runtime design report for the four-switch Buck-Boost plugin."""
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
        notes=["Runtime report assembled by the simplified four-mode four-switch Buck-Boost plugin."],
    )
