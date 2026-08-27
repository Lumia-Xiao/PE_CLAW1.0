"""Input form for the AC-DC single-phase diode bridge DC-side inductor rectifier."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .base_form import BaseTopologyForm, TopologyField
from ...models.design_report import DesignReport
from ...models.operating_point import OperatingPoint
from ...pipeline.run_efficiency_sweep_pipeline import efficiency_sweep_blocking_warning


class SinglePhaseDiodeBridgeRectifierDCInductorFilterForm(BaseTopologyForm):
    """Phase 1 form for the AC-DC diode bridge small DC-reactor topology."""

    topology_id = "single_phase_diode_bridge_rectifier_dc_inductor_filter"
    display_name = "Single-Phase Diode Bridge Rectifier with DC-Side Inductor"
    implemented = True
    design_fields = (
        TopologyField("vac_rms", "Vac rms [V]", "230"),
        TopologyField("f_line_hz", "Line frequency [Hz]", "50"),
        TopologyField("vout_v", "Output target voltage [V]", "325"),
        TopologyField("pout_w", "Pout [W]", "1000"),
        TopologyField("ripple_ratio", "DC-link ripple ratio [pp/nom]", "0.01"),
        TopologyField("dc_reactor_inductance_mh", "DC reactor inductance [mH]", "2"),
        TopologyField("source_resistance_ohm", "Equivalent source resistance Rs [ohm]", "0.1"),
        TopologyField("ambient_temp_c", "Ambient temperature [C]", "25"),
        TopologyField("target_junction_temp_c", "Target junction temperature [C]", "100"),
    )

    @classmethod
    def get_semiconductor_design_fields(cls) -> tuple[TopologyField, ...]:
        """Do not expose diode library filters until bridge module selection exists."""

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
            self.run_magnetics_button.configure(state="disabled")

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
                "Run Design simulates the small DC-reactor rectifier and sizes the DC-link capacitor target; "
                "pulsed or discontinuous reactor current is allowed.\n"
                "Run Capacitor selects the DC-link electrolytic bank, Run Magnetics selects the Sendust reactor, "
                "and Run Efficiency Sweep reuses the selected bridge, capacitor bank, and reactor."
            ),
            justify="left",
            wraplength=360,
        ).pack(anchor="nw", padx=10, pady=10)

    def get_operating_point(self) -> OperatingPoint:
        """Return a placeholder operating point using the design Vac."""

        load_ratio = self._parse_operating_float("load_ratio", "Load ratio")
        clamped = min(max(load_ratio, 0.0), 1.0)
        if clamped != load_ratio:
            self.operating_vars["load_ratio"].set(f"{clamped:.3g}")
        vac_rms = self._parse_design_float("vac_rms", "AC input RMS voltage [V]")
        return OperatingPoint(vin_v=vac_rms, load_ratio=clamped)

    def update_from_report(self, report: DesignReport | None) -> None:
        """Enable component selection after the AC-DC design exists."""

        if self.run_capacitor_button is not None:
            state = "normal" if report is not None and report.candidate is not None else "disabled"
            self.run_capacitor_button.configure(state=state)
        if self.run_magnetics_button is not None:
            state = "normal" if report is not None and report.candidate is not None else "disabled"
            self.run_magnetics_button.configure(state=state)
        if self.run_efficiency_sweep_button is not None:
            state = "normal" if _has_selected_bridge(report) and _has_selected_reactor(report) else "disabled"
            self.run_efficiency_sweep_button.configure(state=state)


def _has_selected_bridge(report: DesignReport | None) -> bool:
    return efficiency_sweep_blocking_warning(report) is None


def _has_selected_reactor(report: DesignReport | None) -> bool:
    magnetic = report.magnetic if report is not None else None
    result = magnetic.ac_dc_reactor_result if magnetic is not None else None
    return bool(
        magnetic is not None
        and magnetic.result_type == "ac_dc_sendust_reactor"
        and result is not None
        and result.selected_candidate is not None
    )
