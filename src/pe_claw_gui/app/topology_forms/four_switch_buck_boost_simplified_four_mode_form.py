"""Four-switch non-inverting Buck-Boost topology form widget."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .base_form import BaseTopologyForm, TopologyField


class FourSwitchBuckBoostSimplifiedFourModeForm(BaseTopologyForm):
    """Input form for the simplified four-mode four-switch Buck-Boost topology."""

    topology_id = "four_switch_buck_boost_simplified_four_mode"
    display_name = "Four-Switch Buck-Boost Simplified Four-Mode"
    implemented = True
    supports_ambient_temperature = True
    design_fields = (
        TopologyField("vin_min", "Vin min [V]", "18"),
        TopologyField("vin_max", "Vin max [V]", "36"),
        TopologyField("vout", "Vout [V]", "24"),
        TopologyField("pout", "Pout [W]", "120"),
        TopologyField("fs_khz", "Switching frequency [kHz]", "100"),
        TopologyField("ripple_current_ratio", "Inductor ripple ratio Delta iL/ILavg", "0.30"),
        TopologyField("ripple_voltage_ratio_percent", "Voltage ripple ratio [%]", "1.0"),
        TopologyField("duty_clamp", "Duty clamp", "0.10"),
        TopologyField("transition_band_ratio", "Transition band ratio", "0.10"),
    )

    def __init__(
        self,
        parent,
        on_run_design=None,
        on_run_capacitor=None,
        on_run_magnetics=None,
        on_generate_waveforms=None,
        on_run_efficiency_sweep=None,
    ) -> None:
        super().__init__(
            parent,
            on_run_design=on_run_design,
            on_run_capacitor=on_run_capacitor,
            on_run_magnetics=on_run_magnetics,
            on_generate_waveforms=on_generate_waveforms,
            on_run_efficiency_sweep=on_run_efficiency_sweep,
        )
        self.columnconfigure(0, weight=1)

        title = ttk.Label(self, text=self.display_name, style="Header.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        design_frame = ttk.LabelFrame(self, text="Design Inputs", style="Section.TLabelframe")
        design_frame.grid(row=1, column=0, sticky="ew")
        design_frame.columnconfigure(1, weight=1)

        design_input_fields = self.get_design_fields()
        self.build_design_input_rows(design_frame, design_input_fields)

        self.build_design_action_buttons(design_frame, row=len(design_input_fields))

        op_frame = ttk.LabelFrame(self, text="Waveform Operating Point", style="Section.TLabelframe")
        op_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        op_frame.columnconfigure(1, weight=1)

        self.operating_vars = {
            "vin_v": tk.StringVar(value="24"),
            "load_ratio": tk.StringVar(value="1.0"),
        }

        ttk.Label(op_frame, text="Operating Vin [V]").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["vin_v"]).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Label(op_frame, text="Load ratio [0-1+]").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["load_ratio"]).grid(row=1, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(op_frame, text="Generate Waveforms", command=self._trigger_waveforms).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=6,
            pady=(10, 6),
        )
        self.build_efficiency_sweep_button(op_frame, row=3)

        notes = ttk.LabelFrame(self, text="Notes", style="Section.TLabelframe")
        notes.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        ttk.Label(
            notes,
            text=(
                "This is a non-inverting four-switch buck-boost converter.\n\n"
                "It uses a simplified fixed-frequency four-mode smooth-transition control method.\n\n"
                "The four modes are pure buck, extended buck, extended boost, and pure boost.\n\n"
                "The purpose is dead-zone-free smooth transition and full-range waveform analysis.\n\n"
                "This is not a soft-switching or MPC controller."
            ),
            justify="left",
        ).pack(anchor="nw", padx=10, pady=10)

    def update_from_report(self, report) -> None:
        if report is not None and report.candidate is not None:
            self.operating_vars["vin_v"].set(f"{report.candidate.vin_nom:.4g}")
