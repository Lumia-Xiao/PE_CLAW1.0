"""LLC diode-rectifier evaluator entry points."""

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
    """Evaluate the diode LLC FHA electrical design into summary lines."""

    llc_fha = candidate.metadata.get("llc_fha", {})
    coverage_results = list(llc_fha.get("coverage_results", [])) if isinstance(llc_fha, dict) else []
    current_estimates = (
        llc_fha.get("current_estimates_nominal_full_load", {})
        if isinstance(llc_fha, dict)
        else {}
    )
    current_estimates_by_corner = (
        list(llc_fha.get("current_estimates_by_corner", []))
        if isinstance(llc_fha, dict)
        else []
    )
    worst_case_current_stress = (
        llc_fha.get("worst_case_current_stress", {})
        if isinstance(llc_fha, dict)
        else {}
    )
    transformer_target = (
        llc_fha.get("transformer_design_target", {})
        if isinstance(llc_fha, dict)
        else {}
    )
    summary_lines = [
        f"Topology = {candidate.display_name}",
        "Model = first-pass LLC FHA electrical parameter design",
        "Control = variable-frequency with fixed 50% bridge drive",
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
        f"Minimum load ratio = {_fmt(llc_fha.get('min_load_ratio'))}",
        f"Pout min = {_fmt(llc_fha.get('pout_min_w'))} W",
        "",
        "Frequency specification",
        f"fs min/max = {_fmt(llc_fha.get('fs_min_hz'))} / {_fmt(llc_fha.get('fs_max_hz'))} Hz",
        f"fr = {_fmt(llc_fha.get('fr_hz'))} Hz",
        "",
        "Structure",
        f"Primary bridge type = {llc_fha.get('primary_bridge_type', '-')}",
        f"Secondary rectifier type = {llc_fha.get('secondary_rectifier_type', '-')}",
        f"Primary bridge gain factor Kpri = {_fmt(llc_fha.get('primary_bridge_gain_factor'))}",
        "",
        "Transformer",
        (
            "Transformer ratio = "
            f"{llc_fha.get('np_turns', '-')}:"
            f"{llc_fha.get('ns_turns', '-')}"
        ),
        f"n = {_fmt(llc_fha.get('turns_ratio'))}",
        f"ideal n = {_fmt(llc_fha.get('ideal_turns_ratio'))}",
        f"ratio error = {_fmt_percent(llc_fha.get('turns_ratio_error'))}",
        "",
        "FHA tank parameters",
        f"Ln = {_fmt(llc_fha.get('ln'))}",
        f"Q_nom = {_fmt(llc_fha.get('q_nom'))}",
        f"Zr = {_fmt(llc_fha.get('zr_ohm'))} ohm",
        f"Rac_nom = {_fmt(llc_fha.get('rac_nom_ohm'))} ohm",
        f"Lr = {_fmt_scaled(llc_fha.get('lr_h'), 1e6)} uH",
        f"Cr = {_fmt_scaled(llc_fha.get('cr_f'), 1e9)} nF",
        f"Lm = {_fmt_scaled(llc_fha.get('lm_h'), 1e6)} uH",
    ]
    if isinstance(transformer_target, dict) and transformer_target:
        boundary_cases = transformer_target.get("boundary_saturation_case_names", [])
        if isinstance(boundary_cases, list):
            boundary_case_text = ", ".join(str(case_name) for case_name in boundary_cases)
        else:
            boundary_case_text = "-"
        summary_lines.extend([
            "",
            "LLC transformer target",
            "Design type = separated transformer",
            "Transformer realizes = turns ratio and Lm",
            "External resonant inductor realizes = Lr",
            (
                "Turns ratio = "
                f"{transformer_target.get('base_np', '-')}:"
                f"{transformer_target.get('base_ns', '-')}"
            ),
            f"Lm target = {_fmt_scaled(transformer_target.get('lm_target_h'), 1e6)} uH",
            f"Lr target = {_fmt_scaled(transformer_target.get('lr_target_h'), 1e6)} uH",
            f"Saturation boundary cases = {boundary_case_text}",
            "Leakage requirement = estimated Llk < Lr",
            "Status = target generated; run magnetics to screen transformer candidates",
            "Run Design stores electrical/FHA target metadata only; Run Magnetics executes candidate search.",
        ])
    summary_lines.extend([
        "",
        "Coverage",
        f"Overall FHA coverage feasible = {bool(llc_fha.get('overall_feasible', candidate.feasible))}",
    ])
    for corner in coverage_results:
        summary_lines.append(
            "Coverage "
            f"{corner.get('label', '-')}: "
            f"{'PASS' if corner.get('feasible') else 'FAIL'}, "
            f"fs={_fmt(corner.get('fs_hz'))} Hz, "
            f"fn={_fmt(corner.get('fn'))}, "
            f"Mreq={_fmt(corner.get('m_req'))}, "
            f"Mact={_fmt(corner.get('m_actual'))}, "
            f"gain error={_fmt_percent(corner.get('gain_error'))}"
        )
    if isinstance(current_estimates, dict) and "ir_rms_a" in current_estimates:
        summary_lines.extend([
            "",
            "FHA current estimates at nominal full-load point",
            f"Vin = {_fmt(current_estimates.get('vin_v'))} V",
            f"Vout = {_fmt(current_estimates.get('vout_v'))} V",
            f"Pout = {_fmt(current_estimates.get('pout_w'))} W",
            f"fs = {_fmt(current_estimates.get('fs_hz'))} Hz",
            f"Resonant tank current RMS = {_fmt(current_estimates.get('ir_rms_a'))} A",
            f"Resonant tank current peak = {_fmt(current_estimates.get('ir_peak_a'))} A",
            f"Magnetizing current RMS = {_fmt(current_estimates.get('im_rms_a'))} A",
            f"Reflected load current RMS = {_fmt(current_estimates.get('reflected_load_current_rms_a'))} A",
        ])
    if current_estimates_by_corner:
        summary_lines.extend(["", "FHA current stress corner sweep"])
        for estimate in current_estimates_by_corner:
            if not isinstance(estimate, dict):
                continue
            summary_lines.append(
                f"{estimate.get('corner_name', '-')}: "
                f"{'PASS' if estimate.get('feasible') else 'FAIL'}, "
                f"Vin={_fmt(estimate.get('vin_v'))} V, "
                f"Vout={_fmt(estimate.get('vout_v'))} V, "
                f"Pout={_fmt(estimate.get('pout_w'))} W, "
                f"fs={_fmt(estimate.get('fs_hz'))} Hz, "
                f"I_SW_rms={_fmt(estimate.get('primary_switch_rms_a'))} A, "
                f"I_SW_peak={_fmt(estimate.get('primary_switch_peak_a'))} A, "
                f"I_D_rms={_fmt(estimate.get('rectifier_diode_rms_a'))} A, "
                f"I_D_peak={_fmt(estimate.get('rectifier_diode_peak_a'))} A"
            )
    if isinstance(worst_case_current_stress, dict) and "primary_switch_rms_a" in worst_case_current_stress:
        summary_lines.extend([
            "",
            "Worst-case FHA current stress for semiconductor selection",
            (
                "Primary switch I_SW_rms = "
                f"{_fmt(worst_case_current_stress.get('primary_switch_rms_a'))} A, "
                f"corner = {worst_case_current_stress.get('primary_switch_rms_corner', '-')}"
            ),
            (
                "Primary switch I_SW_peak = "
                f"{_fmt(worst_case_current_stress.get('primary_switch_peak_a'))} A, "
                f"corner = {worst_case_current_stress.get('primary_switch_peak_corner', '-')}"
            ),
            (
                "Rectifier I_D_avg = "
                f"{_fmt(worst_case_current_stress.get('rectifier_diode_avg_a'))} A, "
                f"corner = {worst_case_current_stress.get('rectifier_diode_avg_corner', '-')}"
            ),
            (
                "Rectifier I_D_rms = "
                f"{_fmt(worst_case_current_stress.get('rectifier_diode_rms_a'))} A, "
                f"corner = {worst_case_current_stress.get('rectifier_diode_rms_corner', '-')}"
            ),
            (
                "Rectifier I_D_peak = "
                f"{_fmt(worst_case_current_stress.get('rectifier_diode_peak_a'))} A, "
                f"corner = {worst_case_current_stress.get('rectifier_diode_peak_corner', '-')}"
            ),
            f"V_SW_max = {_fmt(worst_case_current_stress.get('primary_switch_voltage_stress_v'))} V",
            f"V_D_reverse_max = {_fmt(worst_case_current_stress.get('rectifier_reverse_voltage_stress_v'))} V",
        ])
    if stress_result is not None:
        summary_lines.extend(["", "First-pass stress (worst-case FHA corner estimates)"])
        summary_lines.append(f"Primary switch first-pass Vstress = {stress_result.switch.voltage_max_v:.6g} V")
        summary_lines.append(f"Primary switch I_SW_rms = {_fmt(stress_result.switch.current_rms_a)} A")
        summary_lines.append(f"Primary switch I_SW_peak = {_fmt(stress_result.switch.current_peak_a)} A")
        summary_lines.append(f"Rectifier first-pass Vrr = {stress_result.rectifier.voltage_max_v:.6g} V")
        summary_lines.append(
            f"Full-load output current = {_fmt(current_estimates.get('output_current_a') if isinstance(current_estimates, dict) else None)} A"
        )
        summary_lines.append(f"Rectifier I_D_avg = {_fmt(stress_result.rectifier.current_avg_a)} A")
        summary_lines.append(f"Rectifier I_D_rms = {_fmt(stress_result.rectifier.current_rms_a)} A")
        summary_lines.append(f"Rectifier I_D_peak = {_fmt(stress_result.rectifier.current_peak_a)} A")
    llc_waveforms = (
        waveform_set.metadata.get("llc_fha_waveforms", {})
        if waveform_set is not None
        else {}
    )
    if isinstance(llc_waveforms, dict) and llc_waveforms:
        phase = llc_waveforms.get("phase", {})
        phase_deg = phase.get("i_lr_vs_v_ab1_deg") if isinstance(phase, dict) else None
        time_shift_s = phase.get("time_shift_s") if isinstance(phase, dict) else None
        summary_lines.extend([
            "",
            "Waveform",
            "Two-cycle first-pass LLC FHA waveform estimate is available.",
            (
                "Operating point = "
                f"Vin {_fmt(llc_waveforms.get('vin_op_v'))} V, "
                f"Vout {_fmt(llc_waveforms.get('vout_op_v'))} V, "
                f"load {_fmt(llc_waveforms.get('load_ratio'))} p.u."
            ),
            (
                "Solved waveform frequency = "
                f"{_fmt(llc_waveforms.get('fs_op_hz'))} Hz, "
                f"fn = {_fmt(llc_waveforms.get('fn_op'))}"
            ),
            "Magnetizing current is shown as a triangular clamped-voltage approximation.",
            "Resonant capacitor voltage trace is AC component only.",
        ])
        if isinstance(phase_deg, (int, float)) and isinstance(time_shift_s, (int, float)):
            summary_lines.append(
                f"Phase(i_Lr vs v_ab,1) = {phase_deg:.6g} deg, time shift = {time_shift_s * 1e9:.6g} ns"
            )

    notes = [
        "Diode LLC result uses a first-pass FHA electrical search only.",
        "No detailed LLC time-domain simulation, magnetic design, or semiconductor loss is implemented here.",
        "First-pass FHA sinusoidal current stress estimates are used for diode LLC semiconductor screening.",
        "LLC capacitor currents use first-pass FHA waveform estimates.",
        "Input capacitor current is estimated from primary bridge instantaneous power.",
        "Output capacitor current is estimated from rectified secondary reflected-load current with magnetizing current excluded.",
        "Worst-case current stress is selected from feasible FHA coverage corners.",
        "Primary switch RMS assumes each primary switch conducts for approximately half a switching period.",
        "Rectifier diode average/RMS currents are output-side first-pass estimates, not conduction-angle-integrated waveform results.",
        "Rectifier peak current is estimated from the reflected FHA tank-current peak.",
        "Detailed LLC time-domain waveforms, dead-time commutation, ZVS current, harmonics, diode conduction angle, harmonic-by-harmonic capacitor loss, and device-level current sharing are not implemented yet.",
    ]
    if isinstance(transformer_target, dict) and transformer_target:
        notes.append(
            "Separated LLC transformer target is generated for turns ratio and Lm; Lr remains external and Run Magnetics screens transformer candidates."
        )
    if waveform_set is not None:
        notes.append(
            "First-pass LLC FHA waveform estimate is available; dead time, ZVS transitions, diode commutation overlap, "
            "harmonics, parasitics, and capacitor DC offset are not included."
        )
    if isinstance(llc_fha, dict):
        secondary_note = llc_fha.get("secondary_rectifier_note")
        if secondary_note:
            notes.append(str(secondary_note))
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
    """Build the runtime design report for the diode LLC FHA design."""

    return DesignReport(
        spec=spec,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        device=DeviceSelectionResult(notes=["Device selection is not implemented for the first-pass LLC FHA design."]),
        loss=LossResult(notes=["Semiconductor and magnetic loss calculation is not implemented for the first-pass LLC FHA design."]),
        magnetic=MagneticResult(summary="LLC magnetic design is not implemented yet.", notes=["Placeholder stage."]),
        thermal=ThermalResult(notes=["Thermal evaluation is not implemented for the first-pass LLC FHA design."]),
        geometry=GeometryResult(notes=["Geometry estimation is not implemented for the first-pass LLC FHA design."]),
        topology_result=topology_result,
        notes=["Runtime report assembled by the diode LLC first-pass FHA electrical design plugin."],
    )


def _fmt(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.6g}"
    return "-"


def _fmt_scaled(value: object, scale: float) -> str:
    if isinstance(value, (int, float)):
        return f"{value * scale:.6g}"
    return "-"


def _fmt_percent(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100.0:.4g}%"
    return "-"
