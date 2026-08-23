"""Manual form for the AC-DC single-phase boost PFC topology."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .base_form import BaseTopologyForm, TopologyField
from ...models.design_report import DesignReport
from ...models.operating_point import OperatingPoint


class SinglePhaseBoostPFCDiodeBridgeForm(BaseTopologyForm):
    """GUI-visible first-pass form for the boost PFC topology."""

    topology_id = "single_phase_boost_pfc_diode_bridge"
    display_name = "Single-Phase Boost PFC Diode Bridge"
    implemented = True
    design_fields = (
        TopologyField("vac_rms", "Nominal AC input RMS voltage [V]", "230"),
        TopologyField("vac_rms_min", "Minimum AC input RMS voltage [V]", "180"),
        TopologyField("vac_rms_max", "Maximum AC input RMS voltage [V]", "265"),
        TopologyField("f_line_hz", "Line frequency [Hz]", "50"),
        TopologyField("vdc_target_v", "Target DC bus voltage [V]", "400"),
        TopologyField("pout_w", "Output power [W]", "1000"),
        TopologyField("fsw_hz", "Switching frequency [Hz]", "100000"),
        TopologyField("dc_bus_ripple_percent", "Maximum DC bus ripple [%]", "5"),
        TopologyField("inductor_current_ripple_ratio", "Inductor ripple target [pp/Ipk]", "0.3"),
        TopologyField("power_factor_target", "Minimum power factor", "0.99"),
        TopologyField("sizing_efficiency_assumption", "Sizing efficiency assumption", "0.95"),
        TopologyField("input_inductance_h", "External input inductance [H]", "0.0001"),
        TopologyField("ambient_temp_c", "Ambient temperature [C]", "25"),
        TopologyField("target_junction_temp_c", "Target junction temperature [C]", "100"),
    )

    @classmethod
    def get_semiconductor_design_fields(cls) -> tuple[TopologyField, ...]:
        """Keep the first-pass PFC GUI compact; device filters use shared controls."""

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
        ttk.Entry(op_frame, textvariable=self.operating_vars["load_ratio"]).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=6,
            pady=6,
        )
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
                "This AC-DC topology supports the first-pass md-first and manual GUI flow for a "
                "single-phase diode-bridge boost PFC stage. Run Design performs first-pass "
                "electrical, bridge, boost-switch, boost-diode, loss, thermal, and geometry "
                "preview. Run Capacitor selects the DC-link bank after design; Run Magnetics "
                "selects the boost inductor after design. The md-first runner "
                "uses the same first-pass pipeline."
            ),
            justify="left",
            wraplength=380,
        ).pack(anchor="nw", padx=10, pady=10)

    def get_operating_point(self) -> OperatingPoint:
        """Return the AC input operating point requested for waveform preview."""

        load_ratio = self._parse_operating_float("load_ratio", "Load ratio")
        clamped = min(max(load_ratio, 0.0), 1.0)
        if clamped != load_ratio:
            self.operating_vars["load_ratio"].set(f"{clamped:.3g}")
        vac_rms = self._parse_design_float("vac_rms", "Nominal AC input RMS voltage [V]")
        return OperatingPoint(vin_v=vac_rms, load_ratio=clamped)

    def update_from_report(self, report: DesignReport | None) -> None:
        """Enable staged component actions after the PFC design preview exists."""

        has_candidate = report is not None and report.candidate is not None
        if self.run_capacitor_button is not None:
            self.run_capacitor_button.configure(state="normal" if has_candidate else "disabled")
        if self.run_magnetics_button is not None:
            self.run_magnetics_button.configure(state="normal" if has_candidate else "disabled")
        if self.run_efficiency_sweep_button is not None:
            self.run_efficiency_sweep_button.configure(
                state="normal" if _has_fixed_pfc_hardware(report) else "disabled"
            )


def _has_fixed_pfc_hardware(report: DesignReport | None) -> bool:
    if report is None or report.candidate is None:
        return False
    bridge = report.bridge_rectifier
    if bridge is None or bridge.selected_candidate is None:
        return False
    device = report.device
    if device is None:
        return False
    selected_roles = set(device.selected_devices)
    if not {"main_switch", "rectifier_diode"}.issubset(selected_roles):
        return False
    capacitor = report.capacitor
    if capacitor is None or capacitor.output_selection is None or capacitor.output_selection.recommended is None:
        return False
    magnetic = report.magnetic
    if magnetic is None:
        return False
    if magnetic.selected_design_id:
        return True
    if magnetic.chosen_designs:
        return True
    reactor = magnetic.ac_dc_reactor_result
    return reactor is not None and reactor.selected_candidate is not None
