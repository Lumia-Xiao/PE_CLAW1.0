"""Stress result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport


class StressView(ttk.Frame):
    """Render electrical stress results."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=8)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.text = tk.Text(self, wrap="word", font=("Consolas", 10))
        self.text.grid(row=0, column=0, sticky="nsew")
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        lines = build_stress_summary_lines(report, fallback="Run a design to view stress results.")

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")


def build_stress_summary_lines(
    report: DesignReport | None,
    fallback: str = "Stress results are not available.",
    *,
    include_notes: bool = True,
) -> list[str]:
    """Build compact electrical stress summary lines."""

    if report is None or report.stress is None:
        return [fallback]

    stress = report.stress
    switch_title = "Switch stress"
    switch_voltage_label = "V_SW_max"
    switch_peak_label = "I_SW_peak"
    switch_rms_label = "I_SW_rms"
    rectifier_title = "Rectifier stress"
    rectifier_voltage_label = "V_D_reverse_max"
    rectifier_peak_label = "I_D_peak"
    rectifier_avg_label = "I_D_avg"
    rectifier_rms_label = "I_D_rms"
    if report.spec.topology_id == "three_level_tzcm_fixed_frequency":
        switch_title = "Primary switching-path equivalent stress"
        switch_voltage_label = "V_EQ1_block_max"
        switch_peak_label = "I_EQ1_peak"
        switch_rms_label = "I_EQ1_rms"
        rectifier_title = "Secondary switching-path equivalent stress"
        rectifier_voltage_label = "V_EQ2_block_max"
        rectifier_peak_label = "I_EQ2_peak"
        rectifier_avg_label = "I_EQ2_avg"
        rectifier_rms_label = "I_EQ2_rms"
    if report.spec.topology_id == "four_switch_buck_boost_simplified_four_mode":
        switch_title = "Primary switching-path stress"
        switch_voltage_label = "V_PATH1_block_max"
        switch_peak_label = "I_PATH1_peak"
        switch_rms_label = "I_PATH1_rms"
        rectifier_title = "Secondary switching-path stress"
        rectifier_voltage_label = "V_PATH2_block_max"
        rectifier_peak_label = "I_PATH2_peak"
        rectifier_avg_label = "I_PATH2_avg"
        rectifier_rms_label = "I_PATH2_rms"
    if "synchronous_rectified" in report.spec.topology_id:
        if report.spec.topology_id.startswith("buck_"):
            rectifier_title = "Low-side synchronous switch stress"
            rectifier_voltage_label = "V_LS_block_max"
            rectifier_peak_label = "I_LS_peak"
            rectifier_avg_label = "I_LS_avg"
            rectifier_rms_label = "I_LS_rms"
        else:
            rectifier_title = "Synchronous rectifying switch stress"
            rectifier_voltage_label = "V_SR_block_max"
            rectifier_peak_label = "I_SR_peak"
            rectifier_avg_label = "I_SR_avg"
            rectifier_rms_label = "I_SR_rms"
    if report.spec.topology_id == "single_phase_full_bridge_inverter":
        switch_title = "Full-bridge switch stress"
        rectifier_title = "Antiparallel/freewheel path stress"
        rectifier_voltage_label = "V_FW_block_max"
        rectifier_peak_label = "I_FW_peak"
        rectifier_avg_label = "I_FW_avg"
        rectifier_rms_label = "I_FW_rms"
    if report.spec.topology_id == "three_phase_two_level_voltage_source_inverter":
        switch_title = "Six-switch bridge switch stress"
        rectifier_title = "Antiparallel/freewheel path stress"
        rectifier_voltage_label = "V_FW_block_max"
        rectifier_peak_label = "I_FW_peak"
        rectifier_avg_label = "I_FW_avg"
        rectifier_rms_label = "I_FW_rms"
    if report.spec.topology_id == "three_phase_three_level_npc_inverter":
        switch_title = "NPC active switch stress"
        switch_voltage_label = "V_SW_block_max"
        rectifier_title = "NPC clamp diode stress"
        rectifier_voltage_label = "V_CLAMP_block_max"
        rectifier_peak_label = "I_CLAMP_peak"
        rectifier_avg_label = "I_CLAMP_avg"
        rectifier_rms_label = "I_CLAMP_rms"
    lines = [
        switch_title,
        f"  {switch_voltage_label} = {stress.switch.voltage_max_v:.6f} V",
        f"  {switch_peak_label} = {_fmt_current(stress.switch.current_peak_a)}",
        f"  {switch_rms_label} = {_fmt_current(stress.switch.current_rms_a)}",
        "",
        rectifier_title,
        f"  {rectifier_voltage_label} = {stress.rectifier.voltage_max_v:.6f} V",
        f"  {rectifier_peak_label} = {_fmt_current(stress.rectifier.current_peak_a)}",
        f"  {rectifier_avg_label} = {_fmt_current(stress.rectifier.current_avg_a)}",
        f"  {rectifier_rms_label} = {_fmt_current(stress.rectifier.current_rms_a)}",
    ]
    if stress.role_voltage_checks:
        lines.extend(["", "NPC voltage-margin checks"])
        for role, check in sorted(stress.role_voltage_checks.items()):
            lines.append(
                f"  {role}: static={check.static_blocking_voltage_v:.6g} V, "
                f"dynamic={check.worst_case_blocking_voltage_v:.6g} V, "
                f"required_rating={check.required_device_rating_v:.6g} V, "
                f"margin_target={check.static_margin_target_ratio:.3g}, "
                f"overvoltage={check.overvoltage_validation_status}"
            )
    if include_notes and stress.notes:
        lines.extend(["", "Stress notes", *[f"  {note}" for note in stress.notes]])
    return lines


def _fmt_current(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.6f} A"
