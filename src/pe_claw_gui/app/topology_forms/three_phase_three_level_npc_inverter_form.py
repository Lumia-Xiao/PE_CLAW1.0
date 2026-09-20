"""Input form for the three-phase three-level NPC inverter."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.operating_point import OperatingPoint
from .base_form import BaseTopologyForm, TopologyField


THREE_PHASE_NPC_NOTES = (
    "Runs a first-pass CCM fixed-frequency three-phase NPC inverter design using PD level-shifted SPWM. "
    "Voltage input is line-line RMS; output inductor sizing is reported per phase.\n"
    "Supports first-pass semiconductor loss, split upper/lower DC-link capacitor loss, 3x "
    "output-inductor operating loss, fixed-hardware efficiency load/PF diagnostics, and Hardware Overview.\n"
    "NPC loss uses first-pass PD-SPWM stress; neutral-point balancing, dead-time, Coss, commutation "
    "overlap, parasitic transient models, and ZVS diagnostics are not included."
)


class ThreePhaseThreeLevelNPCInverterForm(BaseTopologyForm):
    """First-pass form for the three-phase three-level NPC inverter."""

    topology_id = "three_phase_three_level_npc_inverter"
    display_name = "Three-Phase Three-Level NPC Inverter"
    implemented = True
    design_fields = (
        TopologyField("vdc_nom", "Vdc nominal [V]", "700"),
        TopologyField("vac_ll_rms", "Vac line-line rms [V]", "400"),
        TopologyField("f_line_hz", "Line frequency [Hz]", "50"),
        TopologyField("fsw_hz", "Switching frequency [Hz]", "20000"),
        TopologyField("pout_w", "Pout [W]", "10000"),
        TopologyField("power_factor", "Power factor", "1.0"),
        TopologyField("inductor_current_ripple_ratio", "Inductor ripple ratio [pp/Ipk]", "0.2"),
        TopologyField("dc_link_voltage_ripple_ratio", "DC-link ripple ratio [pp/Vdc]", "0.05"),
        TopologyField("ambient_temp_c", "Ambient temperature [C]", "25"),
        TopologyField("target_junction_temp_c", "Target junction temperature [C]", "100"),
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
        ttk.Label(self, text=self.display_name, style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))

        design_frame = ttk.LabelFrame(self, text="Design Inputs", style="Section.TLabelframe")
        design_frame.grid(row=1, column=0, sticky="ew")
        design_frame.columnconfigure(1, weight=1)
        all_design_fields = (*self.design_fields, *self.get_semiconductor_design_fields())
        self.build_design_input_rows(design_frame, all_design_fields)
        self.build_design_action_buttons(design_frame, row=len(all_design_fields))
        if self.run_capacitor_button is not None:
            self.run_capacitor_button.configure(state="normal")
        if self.run_magnetics_button is not None:
            self.run_magnetics_button.configure(state="normal")

        op_frame = ttk.LabelFrame(self, text="Waveform Operating Point", style="Section.TLabelframe")
        op_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        op_frame.columnconfigure(1, weight=1)
        self.operating_vars = {
            "load_ratio": tk.StringVar(value="1.0"),
            "power_factor": tk.StringVar(value=self.design_vars["power_factor"].get()),
        }
        ttk.Label(op_frame, text="Load ratio [0-1]").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["load_ratio"]).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Label(op_frame, text="PF [-1..1]").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["power_factor"]).grid(row=1, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(op_frame, text="Generate Waveforms", command=self._trigger_waveforms).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=6,
            pady=(10, 6),
        )
        self.build_efficiency_sweep_button(op_frame, row=3, state="normal")

        notes = ttk.LabelFrame(self, text="Notes", style="Section.TLabelframe")
        notes.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        ttk.Label(
            notes,
            text=THREE_PHASE_NPC_NOTES,
            justify="left",
            wraplength=360,
        ).pack(anchor="nw", padx=10, pady=10)

    def get_operating_point(self) -> OperatingPoint:
        """Return waveform operating point using design DC bus voltage."""

        load_ratio = self._parse_operating_float("load_ratio", "Load ratio")
        clamped = min(max(load_ratio, 0.0), 1.0)
        if clamped != load_ratio:
            self.operating_vars["load_ratio"].set(f"{clamped:.3g}")
        power_factor = self._parse_operating_float("power_factor", "Power factor")
        pf_clamped = min(max(power_factor, -1.0), 1.0)
        if pf_clamped != power_factor:
            self.operating_vars["power_factor"].set(f"{pf_clamped:.3g}")
        return OperatingPoint(
            vin_v=self._parse_design_float("vdc_nom", "DC bus nominal [V]"),
            load_ratio=clamped,
            power_factor=pf_clamped,
        )
