"""Topology-only T-type form with separate design and operating inputs."""
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
        TopologyField("vdc_nom", "Design DC bus [V]", "700"),
        TopologyField("vac_ll_rms", "Grid line-line RMS [V]", "400"),
        TopologyField("f_line_hz", "Line frequency [Hz]", "50"),
        TopologyField("fsw_hz", "Switching frequency [Hz]", "20000"),
        TopologyField("pout_w", "Total active power [W]", "10000"),
        TopologyField("power_factor", "Design PF magnitude (0,1]", "1"),
        TopologyField("power_factor_phase", "PF phase", "lagging", ("lagging", "leading")),
        TopologyField("inductor_current_ripple_ratio", "Inductor target ripple [pp/Ipk]", "0.2"),
        TopologyField("dc_link_voltage_ripple_ratio", "DC bus target ripple [pp/Vdc]", "0.05"),
    )

    @classmethod
    def get_semiconductor_design_fields(cls):
        return ()

    def __init__(self, parent, **callbacks):
        super().__init__(parent, **callbacks)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text=self.display_name, style="Header.TLabel").grid(row=0, column=0, sticky="w")
        design = ttk.LabelFrame(self, text="Design Inputs")
        design.grid(row=1, column=0, sticky="ew", pady=8)
        design.columnconfigure(1, weight=1)
        self.build_design_input_rows(design, self.design_fields)
        self.build_design_action_buttons(design, row=len(self.design_fields))
        self.run_capacitor_button.configure(state="disabled")
        self.run_magnetics_button.configure(state="disabled")
        op = ttk.LabelFrame(self, text="Waveform Operating Point")
        op.grid(row=2, column=0, sticky="ew")
        op.columnconfigure(1, weight=1)
        self.operating_vars = {"operating_vdc_v": tk.StringVar(value="700"),
                               "load_ratio": tk.StringVar(value="1"),
                               "power_factor": tk.StringVar(value="1")}
        for row, (key, label) in enumerate((("operating_vdc_v", "Operating DC bus [V]"),
                                           ("load_ratio", "Load ratio [0,1]"),
                                           ("power_factor", "Operating PF magnitude (0,1]"))):
            ttk.Label(op, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=6)
            ttk.Entry(op, textvariable=self.operating_vars[key]).grid(row=row, column=1, sticky="ew", padx=6)
        self.generate_waveforms_button = ttk.Button(op, text="Generate Waveforms", command=self._trigger_waveforms)
        self.generate_waveforms_button.grid(row=3, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        self.build_efficiency_sweep_button(op, row=4, state="disabled")
        ttk.Label(self, wraplength=360, justify="left", text=(
            "Ideal balanced split bus and zero dead time. L is an initial estimate per phase; "
            "C is a proxy per bank. PF phase stays at the design setting during waveform refresh. "
            "Component selection, losses and efficiency are unavailable in this first round."
        )).grid(row=3, column=0, sticky="ew", pady=12)

    def get_operating_point(self):
        bus = self._parse_operating_float("operating_vdc_v", "Operating DC bus")
        load = self._parse_operating_float("load_ratio", "Load ratio")
        pf = self._parse_operating_float("power_factor", "Power factor")
        if not math.isfinite(bus) or bus <= 0:
            raise ValueError("Operating DC bus must be finite and positive.")
        if not math.isfinite(load) or not 0 <= load <= 1:
            raise ValueError("Load ratio must be finite and in [0,1].")
        if not math.isfinite(pf) or not 0 < pf <= 1:
            raise ValueError("Power factor must be finite and in (0,1].")
        return OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf)
