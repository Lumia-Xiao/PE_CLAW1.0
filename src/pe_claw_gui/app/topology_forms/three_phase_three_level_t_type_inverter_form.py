"""T-type input form using the NPC user-input contract."""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

from ...models.operating_point import OperatingPoint
from .base_form import BaseTopologyForm, TopologyField


class ThreePhaseThreeLevelTTypeInverterForm(BaseTopologyForm):
    topology_id = "three_phase_three_level_t_type_inverter"
    display_name = "Three-Phase Three-Level T-type Inverter"
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

    def __init__(self, parent, **callbacks):
        super().__init__(parent, **callbacks)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text=self.display_name, style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        design = ttk.LabelFrame(self, text="Design Inputs", style="Section.TLabelframe")
        design.grid(row=1, column=0, sticky="ew")
        design.columnconfigure(1, weight=1)
        fields = self.get_design_fields()
        self.build_design_input_rows(design, fields)
        self.build_design_action_buttons(design, row=len(fields))
        self.run_capacitor_button.configure(state="disabled")
        self.run_magnetics_button.configure(state="disabled")
        op = ttk.LabelFrame(self, text="Waveform Operating Point", style="Section.TLabelframe")
        op.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        op.columnconfigure(1, weight=1)
        self.operating_vars = {"load_ratio": tk.StringVar(value="1.0"),
                               "power_factor": tk.StringVar(value=self.design_vars["power_factor"].get())}
        for row, (key, label) in enumerate((("load_ratio", "Load ratio [0-1]"),
                                           ("power_factor", "PF [-1..1]"))):
            ttk.Label(op, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=6)
            ttk.Entry(op, textvariable=self.operating_vars[key]).grid(row=row, column=1, sticky="ew", padx=6, pady=6)
        self.generate_waveforms_button = ttk.Button(op, text="Generate Waveforms", command=self._trigger_waveforms)
        self.generate_waveforms_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(10, 6))
        self.build_efficiency_sweep_button(op, row=3, state="disabled")
        notes = ttk.LabelFrame(self, text="Notes", style="Section.TLabelframe")
        notes.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        ttk.Label(notes, wraplength=360, justify="left", text=(
            "Ideal balanced split bus and zero dead time. L is an initial estimate per phase; "
            "C is a proxy per bank. "
            "IGBT/FRD conduction-only device selection; system losses and efficiency unavailable."
        )).pack(anchor="nw", padx=10, pady=10)

    def get_operating_point(self):
        bus = self._parse_design_float("vdc_nom", "DC bus nominal [V]")
        load = self._parse_operating_float("load_ratio", "Load ratio")
        pf = self._parse_operating_float("power_factor", "Power factor")
        if not math.isfinite(bus) or bus <= 0:
            raise ValueError("Operating DC bus must be finite and positive.")
        if not math.isfinite(load):
            raise ValueError("Load ratio must be finite.")
        if not math.isfinite(pf):
            raise ValueError("Power factor must be finite.")
        clamped_load = min(max(load, 0.0), 1.0)
        clamped_pf = min(max(pf, -1.0), 1.0)
        if clamped_load != load:
            self.operating_vars["load_ratio"].set(f"{clamped_load:.3g}")
        if clamped_pf != pf:
            self.operating_vars["power_factor"].set(f"{clamped_pf:.3g}")
        return OperatingPoint(vin_v=bus, load_ratio=clamped_load, power_factor=clamped_pf)

    def set_operating_input_change_handler(self, handler):
        """Invalidate only current results while keeping the synthesized design."""
        for variable, trace_id in getattr(self, "_operating_input_trace_ids", []):
            variable.trace_remove("write", trace_id)
        self._operating_input_trace_ids = []
        if handler is not None:
            for variable in self.operating_vars.values():
                trace_id = variable.trace_add("write", lambda *_args: handler())
                self._operating_input_trace_ids.append((variable, trace_id))
