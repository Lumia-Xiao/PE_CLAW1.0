"""Evaluation/report assembly for the Phase 1 three-phase AC-DC rectifier."""

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


def evaluate(
    candidate: TopologyCandidate,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
) -> TopologyResult:
    """Build an auditable first-pass three-phase electrical summary."""

    preview = candidate.metadata.get("three_phase_pulse_simulation")
    artifacts = candidate.metadata.get("six_pulse_waveform_preview_artifacts")
    preview_lines: list[str] = []
    preview_notes: list[str] = []
    if isinstance(preview, dict):
        preview_lines.extend(
            [
                "Three-phase capacitor charging-pulse simulation completed.",
                f"Vdc average = {_fmt_float(preview.get('vdc_avg_v'))} V.",
                f"Output ripple = {_fmt_float(preview.get('vdc_ripple_pp_v'))} Vpp.",
                f"Achieved PF = {_fmt_float(preview.get('power_factor'))}.",
            ]
        )
    if isinstance(artifacts, dict):
        preview_lines.extend(
            [
                f"Waveform CSV artifact = {artifacts.get('waveform_csv', '-')}",
                f"Waveform PNG artifact = {artifacts.get('waveform_png', '-')}",
            ]
        )
    if preview_lines:
        preview_notes.append("DC-link capacitor selection uses the simulated bridge-current-minus-load-current waveform.")

    pf_infeasible = candidate.metadata.get("power_factor_requirement_status") == "infeasible_for_passive_topology"

    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=True,
        summary_lines=[
            "First-pass three-phase diode bridge capacitor-filter estimate completed.",
            "See Design summary for Vdc, Cdc, and diode stress estimates.",
            *preview_lines,
            "Run Capacitor can select a first-pass aluminum electrolytic DC-link bank.",
            *(["Requested PF is infeasible for this passive capacitor-input topology."] if pf_infeasible else []),
        ],
        notes=[
            "Vdc is based on three-phase line-to-line RMS voltage.",
            "Capacitor selection uses registered aluminum electrolytic ESR/ripple data with the charging-pulse waveform.",
            "The model includes per-phase source resistance but not source inductance, commutation overlap, or diode recovery.",
            *preview_notes,
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
    """Build the Phase 1 three-phase AC-DC rectifier design report."""

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=(
            OperatingPoint(
                vin_v=candidate.vin_nom,
                load_ratio=1.0,
                vout_v=float(candidate.metadata.get("vout_achieved_v", candidate.vout_target)),
                power_factor=float(candidate.metadata.get("power_factor_achieved", 0.0)) or None,
            )
            if operating_point is None
            else operating_point
        ),
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(
            notes=[
                "Three-phase diode bridge module selection is pending.",
                "Future selection should use bridge module voltage, current, thermal, and surge ratings.",
            ],
        ),
        capacitor=CapacitorResult(
            notes=[
                "DC-link capacitor requirements are available from the Phase 1 estimate.",
                "Run Capacitor selects a first-pass aluminum electrolytic DC-link bank from the registered library.",
                "The capacitor current basis is the simulated bridge charging current minus load current.",
            ],
        ),
        loss=LossResult(
            notes=[
                "Final loss and efficiency are pending selected three-phase bridge module and DC-link capacitor model.",
                "The diode-drop estimate is a placeholder only, not selected-device loss.",
            ],
        ),
        magnetic=MagneticResult(
            summary="No magnetic design is used by this Phase 1 topology.",
            notes=["No DC-side inductor or transformer stage is applicable to this capacitor-filter topology."],
        ),
        thermal=ThermalResult(notes=["Thermal evaluation is pending selected bridge module and capacitor models."]),
        geometry=GeometryResult(notes=["Hardware Overview and detailed visualization are pending for this topology."]),
        topology_result=topology_result,
        notes=[
            "Three-phase diode bridge Vdc is line-to-line RMS based.",
            "Three-phase capacitor charging-pulse waveform is available.",
            "First-pass electrolytic DC-link capacitor selection is available through Run Capacitor.",
            "Source inductance, capacitor ESR dynamics, and diode recovery remain pending.",
            "Bridge rectifier module selection is pending.",
            "Final loss and efficiency are unavailable.",
        ],
    )


def _fmt_float(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "-"
