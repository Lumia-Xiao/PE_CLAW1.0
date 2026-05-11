"""Three-level TZCM fixed-frequency topology form widget."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .base_form import BaseTopologyForm, TopologyField


class ThreeLevelTZCMFixedFrequencyForm(BaseTopologyForm):
    """Input form for the three-level TZCM fixed-frequency topology."""

    topology_id = "three_level_tzcm_fixed_frequency"
    display_name = "Three-Level DC-DC TZCM Fixed Frequency"
    implemented = True
    supports_ambient_temperature = True
    design_fields = (
        TopologyField("vin_nom", "Vin nominal [V]", "400"),
        TopologyField("vout_nom", "Vout nominal [V]", "200"),
        TopologyField("pout_nom", "Pout nominal [W]", "2000"),
        TopologyField("fsw_khz", "Switching frequency [kHz]", "40"),
        TopologyField("izvs", "Izvs [A]", "2"),
        TopologyField("ripple_voltage_ratio_percent", "Voltage ripple ratio [%]", "1.0"),
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
        self._initializing_operating_vars = True
        self._vin_operating_user_edited = False
        self._load_ratio_user_edited = False

        title = ttk.Label(self, text=self.display_name, style="Header.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        design_frame = ttk.LabelFrame(self, text="Design Spec", style="Section.TLabelframe")
        design_frame.grid(row=1, column=0, sticky="ew")
        design_frame.columnconfigure(1, weight=1)

        design_input_fields = self.get_design_fields()
        self.build_design_input_rows(design_frame, design_input_fields)

        self.build_design_action_buttons(design_frame, row=len(design_input_fields))

        op_frame = ttk.LabelFrame(self, text="Waveform Operating Point", style="Section.TLabelframe")
        op_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        op_frame.columnconfigure(1, weight=1)

        self.operating_vars = {
            "vin_operating": tk.StringVar(value=self.design_fields[0].default),
            "load_ratio": tk.StringVar(value="1.0"),
        }
        self.operating_vars["vin_operating"].trace_add("write", self._on_vin_operating_changed)
        self.operating_vars["load_ratio"].trace_add("write", self._on_load_ratio_changed)

        ttk.Label(op_frame, text="Vin operating [V]").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["vin_operating"]).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Label(op_frame, text="Load ratio").grid(row=1, column=0, sticky="w", padx=6, pady=6)
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
                "This form implements a three-level DC-DC converter with fixed-switching-frequency TZCM control.\n\n"
                "The top section defines the nominal design point using Vin, Vout, Pout, Izvs, and a user-specified output-ripple target.\n\n"
                "The bottom section defines the operating point using Vin operating and load ratio.\n\n"
                "Waveforms reuse the synthesized L and Co from the nominal design and solve D1/D4 at the requested operating point."
            ),
            justify="left",
        ).pack(anchor="nw", padx=10, pady=10)

        self.design_vars["vin_nom"].trace_add("write", self._sync_operating_vin)
        self._initializing_operating_vars = False

    def _sync_operating_vin(self, *_args) -> None:
        if self._vin_operating_user_edited:
            return
        self._set_operating_vin_default(self.design_vars["vin_nom"].get())

    def _on_vin_operating_changed(self, *_args) -> None:
        if not self._initializing_operating_vars:
            self._vin_operating_user_edited = True

    def _on_load_ratio_changed(self, *_args) -> None:
        if not self._initializing_operating_vars:
            self._load_ratio_user_edited = True

    def _set_operating_vin_default(self, value: str) -> None:
        previous_flag = self._initializing_operating_vars
        self._initializing_operating_vars = True
        self.operating_vars["vin_operating"].set(value)
        self._initializing_operating_vars = previous_flag

    def _set_load_ratio_default(self, value: str) -> None:
        previous_flag = self._initializing_operating_vars
        self._initializing_operating_vars = True
        self.operating_vars["load_ratio"].set(value)
        self._initializing_operating_vars = previous_flag

    def get_operating_point(self):
        vin_operating = float(self.operating_vars["vin_operating"].get())
        load_ratio = float(self.operating_vars["load_ratio"].get())
        if load_ratio <= 0.0 or load_ratio > 1.0:
            raise ValueError("Load ratio must be in the range (0, 1].")
        from ...models.operating_point import OperatingPoint

        return OperatingPoint(vin_v=vin_operating, load_ratio=load_ratio)

    def update_from_report(self, report) -> None:
        if report is not None and report.candidate is not None:
            if not self._vin_operating_user_edited:
                self._set_operating_vin_default(f"{report.candidate.vin_nom:.4g}")
            if not self.operating_vars["load_ratio"].get().strip():
                self._set_load_ratio_default("1.0")
