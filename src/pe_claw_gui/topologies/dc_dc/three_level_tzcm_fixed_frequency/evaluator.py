"""Evaluation helpers for the three-level TZCM fixed-frequency topology."""

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
    """Evaluate the TZCM candidate into a topology summary."""
    operating_state = build_operating_state(
        candidate,
        operating_point=OperatingPoint(vin_v=waveform_set.operating_vin_v, load_ratio=waveform_set.load_ratio)
        if waveform_set is not None
        else None,
    )
    effective_iout = operating_state.effective_iout
    valley_pass = operating_state.valley_zvs_pass
    peak1_pass = operating_state.peak1_zvs_pass
    peak2_pass = operating_state.peak2_zvs_pass
    success_reason = candidate.failure_reason or "OK"
    output_ripple_vpp = (
        max(waveform_set.output_ripple_v) - min(waveform_set.output_ripple_v)
        if waveform_set is not None and waveform_set.output_ripple_v
        else (candidate.output_ripple_vpp_v or 0.0)
    )

    summary_lines = [
        f"Topology name = {candidate.display_name}",
        f"Topology id = {candidate.topology_id}",
        f"Effective Iout used = {effective_iout:.6f} A",
        f"fsw = {candidate.fs_hz:.2f} Hz",
        f"D = {float(candidate.metadata.get('conversion_duty', candidate.duty_nom)):.6f}",
        f"D1 = {operating_state.d1:.6f}",
        f"D4 = {operating_state.d4:.6f}",
        f"Ip_minus = {operating_state.ip_minus:.6f} A",
        f"I1 = {operating_state.i1:.6f} A",
        f"I2 = {operating_state.i2:.6f} A",
        f"L = {candidate.inductance_h * 1e6:.6f} uH",
        f"Co = {candidate.capacitance_f * 1e6:.6f} uF",
        f"Inductor ripple = {operating_state.delta_i_l_pp:.6f} A",
        f"Output ripple Vpp = {output_ripple_vpp:.6f} V",
        f"Valley ZVS = {valley_pass}",
        f"Peak1 ZVS = {peak1_pass}",
        f"Peak2 ZVS = {peak2_pass}",
        f"Success/failure reason = {success_reason}",
    ]
    if waveform_set is not None:
        summary_lines.append(f"Vin operating = {waveform_set.operating_vin_v:.6f} V")
        summary_lines.append(f"Load ratio = {waveform_set.load_ratio:.6f}")
        summary_lines.append(f"Waveform cycles = {waveform_set.time_span_s / waveform_set.switching_period_s:.2f}")
    if stress_result is not None:
        summary_lines.append(f"Equivalent switch Vmax = {stress_result.switch.voltage_max_v:.6f} V")

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=candidate.feasible,
        summary_lines=summary_lines,
        notes=[
            "Three-level DC-DC converter using a fixed-switching-frequency TZCM engineering model.",
            "This is a simplified waveform-oriented implementation with separate nominal design synthesis and operating-point solution.",
            "Waveform generation uses a two-cycle three-level approximation with complementary gates and deadtime.",
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
    """Build the runtime design report for the TZCM plugin."""
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
        notes=["Runtime report assembled by the three-level TZCM fixed-frequency plugin."],
    )
