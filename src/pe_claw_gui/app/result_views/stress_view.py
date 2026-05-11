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


def build_stress_summary_lines(report: DesignReport | None, fallback: str = "Stress results are not available.") -> list[str]:
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
    lines = [
        switch_title,
        f"  {switch_voltage_label} = {stress.switch.voltage_max_v:.6f} V",
        f"  {switch_peak_label} = {stress.switch.current_peak_a:.6f} A",
        f"  {switch_rms_label} = {(stress.switch.current_rms_a or 0.0):.6f} A",
        "",
        rectifier_title,
        f"  {rectifier_voltage_label} = {stress.rectifier.voltage_max_v:.6f} V",
        f"  {rectifier_peak_label} = {stress.rectifier.current_peak_a:.6f} A",
        f"  {rectifier_avg_label} = {(stress.rectifier.current_avg_a or 0.0):.6f} A",
        f"  {rectifier_rms_label} = {(stress.rectifier.current_rms_a or 0.0):.6f} A",
    ]
    if stress.notes:
        lines.extend(["", "Stress notes", *[f"  {note}" for note in stress.notes]])
    return lines
