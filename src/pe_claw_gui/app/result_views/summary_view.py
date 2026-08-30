"""Summary result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport
from ...models.llc_run_context import is_llc_topology
from .stress_view import build_stress_summary_lines


class SummaryView(ttk.Frame):
    """Render the topology summary and synthesized Buck parameters."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=8)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.text = tk.Text(self, wrap="word", font=("Consolas", 10))
        self.text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scroll.set)
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        lines = ["Run a topology design to view synthesized results."]
        if report is not None and report.candidate is not None:
            candidate = report.candidate
            if report.spec.topology_id == "three_level_tzcm_fixed_frequency":
                from ...models.operating_point import OperatingPoint
                from ...topologies.dc_dc.three_level_tzcm_fixed_frequency.mode import build_operating_state

                operating_state = build_operating_state(
                    candidate,
                    operating_point=report.operating_point
                    if report.operating_point is not None
                    else OperatingPoint(vin_v=candidate.vin_nom, load_ratio=1.0),
                )
                operating_vin = report.waveform.operating_vin_v if report.waveform is not None else candidate.vin_nom
                load_ratio = report.waveform.load_ratio if report.waveform is not None else 1.0
                lines = [
                    "Design summary",
                    f"Topology: {report.spec.display_name}",
                    f"Topology ID: {report.spec.topology_id}",
                    "",
                    "Electrical parameters",
                    f"  vin_nom = {candidate.metadata.get('vin_nom', candidate.vin_nom):.6f} V",
                    f"  vout_nom = {candidate.metadata.get('vout_nom', candidate.vout_target):.6f} V",
                    f"  pout_nom = {candidate.metadata.get('pout_nom', candidate.pout_target):.6f} W",
                    f"  ripple target = {100.0 * float(candidate.metadata.get('vout_ripple_ratio', 0.0)):.6f} %",
                    f"  L = {candidate.inductance_h * 1e6:.6f} uH",
                    f"  Co = {candidate.capacitance_f * 1e6:.6f} uF",
                    "",
                    "Operating mode",
                    f"  vin_operating = {operating_vin:.6f} V",
                    f"  load_ratio = {load_ratio:.6f}",
                    f"  effective Iout = {operating_state.effective_iout:.6f} A",
                    "",
                    "Mode result",
                    f"  D = {float(candidate.metadata.get('conversion_duty', candidate.duty_nom)):.6f}",
                    f"  D1 = {operating_state.d1:.6f}",
                    f"  D4 = {operating_state.d4:.6f}",
                    f"  Ip_minus = {operating_state.ip_minus:.6f} A",
                    f"  I1 = {operating_state.i1:.6f} A",
                    f"  I2 = {operating_state.i2:.6f} A",
                    f"  Delta_iL_pp = {operating_state.delta_i_l_pp:.6f} A",
                    f"  Delta_Vout_pp = {operating_state.output_ripple_vpp_v:.6f} V",
                    f"  Valley ZVS = {operating_state.valley_zvs_pass}",
                    f"  Peak1 ZVS = {operating_state.peak1_zvs_pass}",
                    f"  Peak2 ZVS = {operating_state.peak2_zvs_pass}",
                    f"  Reason = {operating_state.reason or 'OK'}",
                ]
            else:
                lines = [
                    "Design summary",
                    f"Topology: {report.spec.display_name}",
                    f"Topology ID: {report.spec.topology_id}",
                    "",
                    "Electrical parameters",
                    *_build_electrical_parameter_lines(report),
                ]
            if report.topology_result is not None and report.topology_result.summary_lines:
                lines.extend(["", "Topology evaluation", *report.topology_result.summary_lines])
            runtime_lines = build_stage_runtime_lines(report)
            if runtime_lines:
                lines.extend(["", "Stage runtime", *runtime_lines])
            lines.extend(["", "Semiconductor stress summary"])
            lines.extend(build_stress_summary_lines(report, fallback="Stress results are not available for this report."))
            if report.notes:
                lines.extend(["", "Notes / warnings"])
                lines.extend(f"  {note}" for note in report.notes)

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")


def _build_electrical_parameter_lines(report: DesignReport) -> list[str]:
    """Return topology-specific electrical and operating-point readback lines."""

    candidate = report.candidate
    if candidate is None:
        return []
    topology_id = report.spec.topology_id
    metadata = candidate.metadata
    waveform_metadata = report.waveform.metadata if report.waveform is not None else {}
    if is_llc_topology(topology_id):
        llc_fha = metadata.get("llc_fha") if isinstance(metadata.get("llc_fha"), dict) else {}
        reason = "FHA electrical result is unavailable."
        if candidate.failure_reason:
            reason = candidate.failure_reason
        return [
            f"  Vin min/nom/max = {_fmt_triplet(llc_fha, 'vin_min_v', 'vin_nom_v', 'vin_max_v', 'V')}",
            f"  Vout min/nom/max = {_fmt_triplet(llc_fha, 'vout_min_v', 'vout_nom_v', 'vout_max_v', 'V')}",
            f"  Pout max = {_fmt_value(llc_fha.get('pout_max_w'), 'W', reason)}",
            f"  fs min/nom/max = {_fmt_triplet(llc_fha, 'fs_min_hz', 'fr_hz', 'fs_max_hz', 'Hz')}",
            f"  Iavg/Irms/Ipeak = {_fmt_value(_llc_current_value(llc_fha, 'iout_a'), 'A', reason)} / {_fmt_value(_llc_current_value(llc_fha, 'ir_rms_a'), 'A', reason)} / {_fmt_value(_llc_current_value(llc_fha, 'ir_peak_a'), 'A', reason)}",
            f"  Lr/Cr/Lm = {_fmt_value(llc_fha.get('lr_h'), 'H', reason)} / {_fmt_value(llc_fha.get('cr_f'), 'F', reason)} / {_fmt_value(llc_fha.get('lm_h'), 'H', reason)}",
            f"  Mode = {_fmt_text(candidate.mode_capable, reason)}",
        ]
    if topology_id == "single_phase_full_bridge_inverter":
        lines = [
            f"  Vdc_nom = {candidate.vin_nom:.6f} V",
            f"  Vac_rms = {candidate.vout_target:.6f} V",
            f"  Pout = {candidate.pout_target:.6f} W",
            f"  fsw = {candidate.fs_hz:.2f} Hz",
            f"  modulation index = {_fmt_float(metadata.get('modulation_index'))}",
            f"  Lout = {candidate.inductance_h * 1e6:.6f} uH",
            f"  Cdc = {candidate.capacitance_f * 1e6:.6f} uF",
            f"  DC-link ripple target = {candidate.delta_vo:.6f} Vpp",
            f"  Iac rms = {_fmt_float(metadata.get('iac_rms_a'))} A",
            f"  Iac peak = {_fmt_float(metadata.get('iac_peak_a'))} A",
            f"  CCM valid = {candidate.ccm_valid}",
        ]
        if waveform_metadata:
            lines.extend([
                f"  Operating load ratio = {_fmt_float(report.waveform.load_ratio)} pu",
                f"  Operating PF = {_fmt_float(waveform_metadata.get('operating_power_factor'))}",
                f"  Operating Iac rms = {_fmt_float(waveform_metadata.get('operating_iac_rms_a'))} A",
                f"  Operating Idc avg = {_fmt_float(waveform_metadata.get('operating_idc_avg_a'))} A",
            ])
        return lines
    if topology_id == "three_phase_two_level_voltage_source_inverter":
        lines = [
            f"  Vdc_nom = {candidate.vin_nom:.6f} V",
            f"  Vac line-line rms = {candidate.vout_target:.6f} V",
            f"  Vac phase rms = {_fmt_float(metadata.get('vac_phase_rms_v'))} V",
            f"  Pout = {candidate.pout_target:.6f} W",
            f"  PF = {_fmt_float(metadata.get('power_factor'))}",
            f"  fsw = {candidate.fs_hz:.2f} Hz",
            f"  modulation index = {_fmt_float(metadata.get('modulation_index'))}",
            f"  L_phase = {candidate.inductance_h * 1e6:.6f} uH",
            f"  Cdc proxy = {candidate.capacitance_f * 1e6:.6f} uF",
            f"  DC-link ripple target = {candidate.delta_vo:.6f} Vpp",
            f"  I_phase rms = {_fmt_float(metadata.get('i_phase_rms_a'))} A",
            f"  I_phase peak = {_fmt_float(metadata.get('i_phase_peak_a'))} A",
            f"  CCM valid = {candidate.ccm_valid}",
        ]
        return _append_operating_readback(lines, report, "operating_i_phase_rms_a", "operating_i_phase_peak_a")
    if topology_id == "three_phase_three_level_npc_inverter":
        lines = [
            f"  Vdc_nom = {candidate.vin_nom:.6f} V",
            f"  Vac line-line rms = {candidate.vout_target:.6f} V",
            f"  Vac phase rms = {_fmt_float(metadata.get('vac_phase_rms_v'))} V",
            f"  Pout = {candidate.pout_target:.6f} W",
            f"  PF = {_fmt_float(metadata.get('power_factor'))}",
            f"  fsw = {candidate.fs_hz:.2f} Hz",
            "  modulation scheme = PD level-shifted SPWM first-pass",
            f"  modulation index = {_fmt_float(metadata.get('modulation_index'))}",
            f"  L_phase = {candidate.inductance_h * 1e6:.6f} uH",
            f"  Cdc half-link proxy = {candidate.capacitance_f * 1e6:.6f} uF",
            f"  DC-link ripple target = {candidate.delta_vo:.6f} Vpp",
            f"  I_phase rms = {_fmt_float(metadata.get('i_phase_rms_a'))} A",
            f"  I_phase peak = {_fmt_float(metadata.get('i_phase_peak_a'))} A",
            f"  switch positions = {int(metadata.get('switch_position_count', 0))}",
            f"  clamp diode positions = {int(metadata.get('clamp_diode_count', 0))}",
            f"  CCM valid = {candidate.ccm_valid}",
        ]
        return _append_operating_readback(lines, report, "operating_i_phase_rms_a", "operating_i_phase_peak_a")
    return [
        f"  Vin_nom = {candidate.vin_nom:.6f} V",
        f"  Duty_nom = {candidate.duty_nom:.6f}",
        f"  Iout = {candidate.iout:.6f} A",
        f"  fs = {candidate.fs_hz:.2f} Hz",
        f"  L = {candidate.inductance_h * 1e6:.6f} uH",
        f"  C = {candidate.capacitance_f * 1e6:.6f} uF",
        f"  Delta_iL = {candidate.delta_il:.6f} A",
        f"  Delta_vo = {candidate.delta_vo:.6f} V",
        f"  I_L_peak = {candidate.il_peak:.6f} A",
        f"  I_L_valley = {candidate.il_valley:.6f} A",
        f"  CCM valid = {candidate.ccm_valid}",
    ]


def _append_operating_readback(
    lines: list[str],
    report: DesignReport,
    rms_key: str,
    peak_key: str,
) -> list[str]:
    """Append refresh values only when a waveform operating point exists."""

    waveform = report.waveform
    if waveform is None:
        return lines
    metadata = waveform.metadata
    lines.extend([
        f"  Operating load ratio = {_fmt_float(waveform.load_ratio)} pu",
        f"  Operating PF = {_fmt_float(metadata.get('operating_power_factor'))}",
        f"  Operating I_phase rms = {_fmt_float(metadata.get(rms_key))} A",
        f"  Operating I_phase peak = {_fmt_float(metadata.get(peak_key))} A",
        f"  Operating Idc avg = {_fmt_float(metadata.get('operating_idc_avg_a'))} A",
    ])
    return lines


def _fmt_float(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "-"


def _llc_current_value(llc_fha: dict, key: str):
    current = llc_fha.get("current_estimates_nominal_full_load")
    if isinstance(current, dict) and current.get(key) is not None:
        return current.get(key)
    stress = llc_fha.get("worst_case_current_stress")
    return stress.get(key) if isinstance(stress, dict) else None


def _fmt_value(value, unit: str, reason: str) -> str:
    if value is None:
        return f"not computed (reason: {reason})"
    try:
        return f"{float(value):.6g} {unit}"
    except (TypeError, ValueError):
        return f"not computed (reason: {reason})"


def _fmt_text(value, reason: str) -> str:
    return str(value) if value not in (None, "", "unknown") else f"not computed (reason: {reason})"


def _fmt_triplet(values: dict, first: str, second: str, third: str, unit: str) -> str:
    return " / ".join(
        _fmt_value(values.get(key), unit, "FHA parameter is unavailable")
        for key in (first, second, third)
    )


def build_stage_runtime_lines(report: DesignReport | None) -> list[str]:
    """Return user-visible stage runtime lines when timing data is available."""

    if report is None:
        return []
    lines: list[str] = []
    _append_runtime_line(
        lines,
        "Run Design",
        getattr(report, "run_design_runtime_seconds", None),
        getattr(report, "run_design_started_at", None),
        getattr(report, "run_design_finished_at", None),
    )
    capacitor_runtime_s = None
    if report.capacitor is not None:
        capacitor_runtime_s = report.capacitor.diagnostics.get("total_run_capacitor_time_s")
    _append_runtime_line(lines, "Run Capacitor", capacitor_runtime_s, None, None)
    _append_runtime_line(
        lines,
        "Run Magnetics",
        getattr(report, "run_magnetics_runtime_seconds", None),
        getattr(report, "run_magnetics_started_at", None),
        getattr(report, "run_magnetics_finished_at", None),
    )
    return lines


def _append_runtime_line(lines: list[str], label: str, runtime_s, started_at: str | None, finished_at: str | None) -> None:
    line = format_stage_runtime(label, runtime_s, started_at=started_at, finished_at=finished_at)
    if line:
        lines.append(f"  {line}")


def format_stage_runtime(stage_name: str, runtime_seconds, started_at: str | None = None, finished_at: str | None = None) -> str:
    """Format one stage runtime line without dangling separators or malformed timestamp suffixes."""

    if runtime_seconds is None and not started_at and not finished_at:
        return ""
    runtime_text = "-" if runtime_seconds is None else f"{float(runtime_seconds):.3f} s"
    parts = [f"{stage_name}: {runtime_text}"]
    if started_at:
        parts.append(f"started {_clean_timestamp(started_at)}")
    if finished_at:
        parts.append(f"finished {_clean_timestamp(finished_at)}")
    return "; ".join(part for part in parts if part)


def _clean_timestamp(value: str) -> str:
    value = str(value).strip()
    if value.endswith("+00:00d"):
        return value[:-1]
    return value
