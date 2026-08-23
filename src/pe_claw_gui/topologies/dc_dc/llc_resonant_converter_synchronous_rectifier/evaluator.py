"""LLC synchronous-rectifier evaluator entry points."""

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
    """Evaluate the first-pass LLC SR FHA design into summary lines."""

    llc_fha = candidate.metadata.get("llc_fha", {})
    llc_sr = candidate.metadata.get("llc_sr", {})
    stress_readback = llc_sr.get("stress_readback", {}) if isinstance(llc_sr, dict) else {}
    timing_readback = llc_sr.get("timing_readback", {}) if isinstance(llc_sr, dict) else {}
    loss_readback = llc_sr.get("loss_readback", {}) if isinstance(llc_sr, dict) else {}
    summary_lines = [
        f"Topology = {candidate.display_name}",
        "Model = first-pass LLC FHA electrical parameter design with full-bridge synchronous rectifier readback",
        "Control = variable-frequency with fixed 50% primary bridge drive",
        "",
        "Input specification",
        (
            "Vin min/nom/max = "
            f"{_fmt(llc_fha.get('vin_min_v'))} / {_fmt(llc_fha.get('vin_nom_v'))} / {_fmt(llc_fha.get('vin_max_v'))} V"
        ),
        "",
        "Output specification",
        (
            "Vout min/nom/max = "
            f"{_fmt(llc_fha.get('vout_min_v'))} / {_fmt(llc_fha.get('vout_nom_v'))} / {_fmt(llc_fha.get('vout_max_v'))} V"
        ),
        f"Pout max = {_fmt(llc_fha.get('pout_max_w'))} W",
        "",
        "Structure",
        f"Primary bridge type = {llc_fha.get('primary_bridge_type', '-')}",
        "Secondary rectifier type = full_bridge_synchronous_rectifier",
        "Required semiconductor roles = main_switch, secondary_sync_switch",
        "",
        "Transformer",
        f"Transformer ratio = {llc_fha.get('np_turns', '-')}:{llc_fha.get('ns_turns', '-')}",
        f"n = {_fmt(llc_fha.get('turns_ratio'))}",
        "",
        "FHA tank parameters",
        f"fr = {_fmt(llc_fha.get('fr_hz'))} Hz",
        f"Lr = {_fmt_scaled(llc_fha.get('lr_h'), 1e6)} uH",
        f"Cr = {_fmt_scaled(llc_fha.get('cr_f'), 1e9)} nF",
        f"Lm = {_fmt_scaled(llc_fha.get('lm_h'), 1e6)} uH",
        f"Overall FHA coverage feasible = {bool(llc_fha.get('overall_feasible', candidate.feasible))}",
    ]
    if stress_result is not None:
        summary_lines.extend([
            "",
            "First-pass stress",
            f"Primary main_switch Vstress = {stress_result.switch.voltage_max_v:.6g} V",
            f"Primary main_switch I_rms = {_fmt(stress_result.switch.current_rms_a)} A",
            f"Primary main_switch I_peak = {_fmt(stress_result.switch.current_peak_a)} A",
            f"Secondary sync switch Vstress = {stress_result.rectifier.voltage_max_v:.6g} V",
            f"Secondary sync switch I_avg = {_fmt(stress_result.rectifier.current_avg_a)} A",
            f"Secondary sync switch I_rms = {_fmt(stress_result.rectifier.current_rms_a)} A",
            f"Secondary sync switch I_peak = {_fmt(stress_result.rectifier.current_peak_a)} A",
        ])
    if isinstance(timing_readback, dict) and timing_readback:
        summary_lines.extend([
            "",
            "SR timing readback",
            f"SR timing mode = {timing_readback.get('timing_mode', '-')}",
            f"SR timing data status = {timing_readback.get('timing_data_status', '-')}",
            f"SR deadtime = {_fmt(timing_readback.get('deadtime_ns'))} ns",
            f"SR deadtime fraction = {_fmt(timing_readback.get('deadtime_fraction'))}",
        ])
    if isinstance(loss_readback, dict) and loss_readback:
        role_losses = loss_readback.get("role_losses", {})
        sr_loss = role_losses.get("secondary_sync_switch", {}) if isinstance(role_losses, dict) else {}
        summary_lines.extend([
            "",
            "SR loss readback",
            f"SR loss source = {loss_readback.get('loss_source', '-')}",
            f"SR loss model = {sr_loss.get('loss_model', '-')}",
            f"SR selected switch = {sr_loss.get('part_number', '-')}",
            f"SR conduction loss per switch = {_fmt(sr_loss.get('p_conduction_w'))} W",
            f"SR total secondary sync switch loss = {_fmt(loss_readback.get('total_secondary_sync_switch_loss_w'))} W",
        ])
    notes = [
        "LLC SR result uses the diode LLC FHA electrical search with full-bridge synchronous-rectifier role remapping.",
        "Secondary SR loss readback is conduction-only first-pass evidence; reverse conduction, deadtime optimization, Coss/Eoss validation, current sharing, and layout parasitics are not included in the loss total.",
        "No rectifier_diode role is required for this topology.",
    ]
    if isinstance(stress_readback, dict):
        notes.extend(str(note) for note in stress_readback.get("first_pass_limitations", ()))
    if isinstance(llc_fha, dict):
        notes.extend(str(warning) for warning in llc_fha.get("warnings", []))
    return TopologyResult(
        topology_id=candidate.topology_id,
        display_name=candidate.display_name,
        candidate=candidate,
        feasible=candidate.feasible,
        summary_lines=summary_lines,
        notes=notes,
    )


def build_report(
    spec: TopologySpec,
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    waveform_set: WaveformSet | None = None,
    stress_result: StressResult | None = None,
    topology_result: TopologyResult | None = None,
) -> DesignReport:
    """Build the runtime design report for the first-pass LLC SR design."""

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(notes=["Device selection will run through the shared semiconductor pipeline."]),
        loss=LossResult(notes=["SR loss readback is attached after semiconductor selection."]),
        magnetic=MagneticResult(summary="LLC SR magnetic design uses the separated LLC transformer path.", notes=["Run Magnetics screens separated transformer candidates."]),
        thermal=ThermalResult(notes=["Thermal evaluation runs after magnetic/loss stages where applicable."]),
        geometry=GeometryResult(notes=["Geometry estimation runs after semiconductor and magnetic stages."]),
        topology_result=topology_result,
        notes=["Runtime report assembled by the LLC SR first-pass FHA electrical design plugin."],
    )


def _fmt(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.6g}"
    return "-"


def _fmt_scaled(value: object, scale: float) -> str:
    if isinstance(value, (int, float)):
        return f"{value * scale:.6g}"
    return "-"
