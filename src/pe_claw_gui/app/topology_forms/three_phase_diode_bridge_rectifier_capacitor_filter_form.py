"""Input form for the three-phase diode bridge capacitor-filter rectifier."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport
from ...models.operating_point import OperatingPoint
from .base_form import BaseTopologyForm, TopologyField


class ThreePhaseDiodeBridgeRectifierCapacitorFilterForm(BaseTopologyForm):
    """Phase 1 form for three-phase diode bridge capacitor-filter estimates."""

    topology_id = "three_phase_diode_bridge_rectifier_capacitor_filter"
    display_name = "Three-Phase Diode Bridge Rectifier Capacitor Filter"
    implemented = True
    design_fields = (
        TopologyField("vll_rms", "VLL rms [V]", "400"),
        TopologyField("f_line_hz", "Line frequency [Hz]", "50"),
        TopologyField("vout_v", "Output target voltage [V]", "540"),
        TopologyField("pout_w", "Pout [W]", "3000"),
        TopologyField("dc_link_ripple_ratio", "DC-link ripple ratio [pp/nom]", "0.02"),
        TopologyField("diode_forward_drop_v", "Diode forward drop estimate Vd [V]", "1.0"),
        TopologyField("diode_voltage_margin", "Diode voltage margin", "2.0"),
        TopologyField("source_resistance_ohm", "Source resistance per phase [ohm]", "0.05"),
        TopologyField("power_factor_target", "Minimum PF requirement [optional]", ""),
        TopologyField("ambient_temp_c", "Ambient temperature [C]", "25"),
        TopologyField("target_junction_temp_c", "Target junction temperature [C]", "100"),
    )

    @classmethod
    def get_semiconductor_design_fields(cls) -> tuple[TopologyField, ...]:
        """Do not expose bridge-module filters until three-phase bridge selection exists."""

        return ()

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

        design_input_fields = self.get_design_fields()
        self.build_design_input_rows(design_frame, design_input_fields)
        self.build_design_action_buttons(design_frame, row=len(design_input_fields))
        if self.run_capacitor_button is not None:
            self.run_capacitor_button.configure(state="disabled")
        if self.run_magnetics_button is not None:
            button_row = self.run_magnetics_button.master
            self.run_magnetics_button.destroy()
            self.run_magnetics_button = None
            button_row.columnconfigure(2, weight=0)

        op_frame = ttk.LabelFrame(self, text="Waveform Operating Point", style="Section.TLabelframe")
        op_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        op_frame.columnconfigure(1, weight=1)
        self.operating_vars = {
            "load_ratio": tk.StringVar(value="1.0"),
        }
        ttk.Label(op_frame, text="Load ratio [0-1]").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["load_ratio"]).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(op_frame, text="Generate Waveforms", command=self._trigger_waveforms).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=6,
            pady=(10, 6),
        )
        self.build_efficiency_sweep_button(op_frame, row=2, state="disabled")

        notes = ttk.LabelFrame(self, text="Notes", style="Section.TLabelframe")
        notes.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        ttk.Label(
            notes,
            text=(
                "Run Design simulates three-phase capacitor charging pulses using the fixed passive load and per-phase source resistance.\n"
                "Run Capacitor selects the DC-link electrolytic bank; Run Efficiency Sweep reuses the "
                "selected bridge and capacitor bank when available."
            ),
            justify="left",
            wraplength=360,
        ).pack(anchor="nw", padx=10, pady=10)

    def get_operating_point(self) -> OperatingPoint:
        """Return AC-DC waveform operating point using the design line-line RMS voltage."""

        load_ratio = self._parse_operating_float("load_ratio", "Load ratio")
        clamped = min(max(load_ratio, 0.0), 1.0)
        if clamped != load_ratio:
            self.operating_vars["load_ratio"].set(f"{clamped:.3g}")
        vll_rms = self._parse_design_float("vll_rms", "AC line-line RMS voltage [V]")
        return OperatingPoint(vin_v=vll_rms, load_ratio=clamped)

    def update_from_report(self, report: DesignReport | None) -> None:
        """Enable first-pass DC-link capacitor selection after the design exists."""

        if self.run_capacitor_button is not None:
            state = "normal" if report is not None and report.candidate is not None else "disabled"
            self.run_capacitor_button.configure(state=state)
        if self.run_magnetics_button is not None:
            self.run_magnetics_button.configure(state="disabled")
        if self.run_efficiency_sweep_button is not None:
            state = "normal" if _has_selected_bridge(report) else "disabled"
            self.run_efficiency_sweep_button.configure(state=state)


def _has_selected_bridge(report: DesignReport | None) -> bool:
    bridge = report.bridge_rectifier if report is not None else None
    return bool(
        report is not None
        and report.candidate is not None
        and bridge is not None
        and bridge.selected_candidate is not None
    )
