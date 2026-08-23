"""Evaluation/report assembly for the Phase 1 AC-DC small DC-link reactor rectifier."""

from __future__ import annotations

from ....models.capacitor import CapacitorResult
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
from .waveform import generate_waveforms


def evaluate(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
) -> TopologyResult:
    """Build an auditable first-pass electrical summary."""

    summary_lines = [
        "First-pass AC-DC small DC-reactor rectifier estimate completed.",
        "See Design summary for capacitor-input Vdc, bounded Ldc, Cout, and diode stress estimates.",
    ]
    simulation = candidate.metadata.get("state_space_simulation")
    if isinstance(simulation, dict) and simulation.get("simulation_succeeded"):
        summary_lines.extend([
            "Design-point state-space DC-side inductor validation completed.",
            "  load ratio = 1.0",
            f"  target output power = {simulation.get('target_output_power_w', '-')} W",
            f"  simulated Vdc avg = {simulation.get('vdc_avg_v', '-')} V",
            f"  simulated Vdc ripple pp = {simulation.get('vdc_ripple_pp_v', '-')} V",
            f"  simulated IL rms/peak = {simulation.get('il_rms_a', '-')} / {simulation.get('il_peak_a', '-')} A",
            f"  bridge conduction angle = {simulation.get('bridge_conduction_angle_half_cycle_deg', '-')} deg per half-cycle",
            f"  bridge/capacitor RMS current = {simulation.get('bridge_current_rms_a', '-')} / {simulation.get('capacitor_current_rms_a', '-')} A",
            f"  design-point waveform CSV artifact = {simulation.get('waveform_csv_path', '-')}",
            f"  design-point waveform PNG artifact = {simulation.get('waveform_png_path', '-')}",
        ])
    current_simulation = None
    if waveform_set is not None and isinstance(waveform_set.metadata.get("ac_dc_dc_inductor_metrics"), dict):
        current_simulation = waveform_set.metadata["ac_dc_dc_inductor_metrics"]
    if (
        isinstance(current_simulation, dict)
        and current_simulation.get("simulation_succeeded")
        and abs(float(current_simulation.get("load_ratio", 1.0) or 1.0) - 1.0) > 1e-12
    ):
        summary_lines.extend([
            "Current operating-point state-space validation completed.",
            f"  load ratio = {current_simulation.get('load_ratio', '-')}",
            f"  target output power = {current_simulation.get('target_output_power_w', '-')} W",
            f"  simulated load power = {current_simulation.get('simulated_load_power_w', '-')} W",
            f"  current operating-point waveform CSV artifact = {current_simulation.get('waveform_csv_path', '-')}",
            f"  current operating-point waveform PNG artifact = {current_simulation.get('waveform_png_path', '-')}",
            "  Generate Waveforms refreshed only operating-point-dependent outputs; Ldc and Cout remain design-point values.",
        ])
    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=True,
        summary_lines=summary_lines,
        notes=[
            "Small DC-reactor rectifier Vdc is capacitor-input peak based, not choke-input average based.",
            "Phase 2 uses a first-pass lumped state-space simulation for the DC-side reactor and output capacitor.",
            "Load ratio scales the fixed nominal resistance as Rload_nominal/load_ratio; actual passive-load power is reported.",
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
    """Build the Phase 1 AC-DC DC-side reactor rectifier design report."""

    if waveform_set is None:
        waveform_set = generate_waveforms(candidate)

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=(
            OperatingPoint(
                vin_v=candidate.vin_nom,
                load_ratio=1.0,
                vout_v=float(candidate.metadata.get("simulation_primary_vdc_avg_v", candidate.vout_target)),
                power_factor=float(candidate.metadata.get("state_space_simulation", {}).get("power_factor", 0.0)) or None,
            )
            if operating_point is None
            else operating_point
        ),
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(notes=["Bridge rectifier module selection is handled by the bridge selector stage."]),
        capacitor=CapacitorResult(notes=["Output/DC-link capacitor library selection is pending for this AC-DC topology."]),
        loss=LossResult(notes=["Final AC-DC loss and efficiency use the selected bridge, small DC-link reactor, and capacitor models when those stages have run."]),
        magnetic=MagneticResult(
            summary="Small DC-link reactor requirement is available; Sendust toroid screening is handled by Run Magnetics.",
            design_requirements={
                "topology_id": spec.topology_id,
                "display_name": spec.display_name,
                "inductance_h": candidate.inductance_h,
                "target_inductance_h": candidate.inductance_h,
                "fs_hz": candidate.fs_hz,
                "i_avg_a": candidate.metadata.get("simulation_primary_il_avg_a", candidate.metadata.get("il_avg_a")),
                "i_rms_a": candidate.metadata.get("simulation_primary_il_rms_a", candidate.metadata.get("il_rms_est_a")),
                "i_peak_a": candidate.metadata.get("simulation_primary_il_peak_a", candidate.metadata.get("il_peak_est_a")),
                "i_valley_a": candidate.metadata.get("simulation_primary_il_min_a", candidate.metadata.get("il_min_est_a")),
                "delta_i_pp_a": candidate.delta_il,
                "bridge_current_rms_a": candidate.metadata.get("simulation_primary_bridge_current_rms_a"),
                "capacitor_current_rms_a": candidate.metadata.get("simulation_primary_capacitor_current_rms_a"),
                "conduction_angle_half_cycle_deg": candidate.metadata.get("simulation_primary_conduction_angle_half_cycle_deg"),
                "throughput_power_w": candidate.pout_target,
                "mode": candidate.mode_capable,
            },
            notes=[
                "Small DC-link reactor design is handled by Run Magnetics.",
                "Bounded Ldc, first-pass IL_avg, IL_rms, and IL_peak are available from Run Design.",
                "Existing Buck inductor design formulas are not used for this AC-DC small DC-link reactor.",
            ],
        ),
        thermal=ThermalResult(notes=["Thermal evaluation uses selected bridge, small DC-link reactor, and capacitor models when those stages have run."]),
        geometry=GeometryResult(notes=["Hardware Overview uses selected bridge, small DC-link reactor, and capacitor geometry when those stages have run."]),
        topology_result=topology_result,
        notes=[
            "AC-DC DC-side reactor rectifier Phase 1.1 uses a capacitor-input peak-voltage estimate.",
            "Phase 2 adds first-pass state-space waveform validation for the DC-side reactor and output capacitor.",
            "Card image temporarily reuses the Buck topology image until a dedicated AC-DC inductor-filter rectifier schematic is added.",
            "Bridge rectifier, electrolytic capacitor, and small DC-link reactor selections are shown in their dedicated result pages when those stages have run.",
        ],
    )
