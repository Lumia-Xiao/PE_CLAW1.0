"""Evaluation/report assembly for the Phase 1 AC-DC rectifier topology."""

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
        "First-pass AC-DC capacitor-input estimate completed.",
    ]
    simulation = candidate.metadata.get("pulse_simulation")
    if isinstance(simulation, dict) and simulation.get("simulation_succeeded"):
        summary_lines.extend([
            "Rs-based pulse-current simulation completed.",
            f"Waveform CSV artifact = {simulation.get('waveform_csv_path', '-')}",
            "See Design summary for Phase 1 estimates and Phase 2 simulated metrics.",
        ])
    else:
        summary_lines.append("See Design summary for computed values.")
    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=True,
        summary_lines=summary_lines,
        notes=[
            "Capacitor-input rectifier Vdc is estimated from AC peak voltage, not 2*Vm/pi.",
            "Phase 2 pulse-current metrics use a first-pass lumped Rs time-domain model.",
            "Equivalent source resistance Rs limits diode charging current in the simulation.",
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
    """Build the Phase 1 AC-DC rectifier design report."""

    if waveform_set is None:
        waveform_set = generate_waveforms(candidate)

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(notes=["Diode bridge device selection is pending for AC-DC Phase 2."]),
        capacitor=CapacitorResult(
            notes=[
                "Run Capacitor selects a first-pass aluminum electrolytic DC-link bank from the registered library.",
                "DC-link capacitor selection uses the shared capacitor selector and Pareto ranking by estimated bank volume and total bank loss.",
            ],
        ),
        loss=LossResult(notes=["Detailed rectifier loss calculation is not implemented in AC-DC Phase 1."]),
        magnetic=MagneticResult(summary="No magnetic design is used by this Phase 1 topology.", notes=["No inductor or transformer stage."]),
        thermal=ThermalResult(notes=["Thermal evaluation is pending for AC-DC Phase 2."]),
        geometry=GeometryResult(notes=["Hardware Overview and detailed visualization are pending for AC-DC Phase 2."]),
        topology_result=topology_result,
        notes=[
            "AC-DC Phase 1 estimates remain visible; Phase 2 adds first-pass Rs-based pulse-current metrics.",
            "Card image temporarily reuses the Buck topology image until an AC-DC rectifier schematic is added.",
            "Rs-based simulation does not include source inductance, EMI filter behavior, diode reverse recovery, or capacitor ESR heating.",
        ],
    )
