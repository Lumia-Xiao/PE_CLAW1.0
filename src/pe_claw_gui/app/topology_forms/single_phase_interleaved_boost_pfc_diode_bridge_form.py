"""Planned GUI form for the two-phase interleaved Boost PFC topology."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .base_form import BaseTopologyForm, TopologyField
from ...models.design_report import DesignReport
from ...models.operating_point import OperatingPoint
from ...pipeline.run_efficiency_sweep_pipeline import efficiency_sweep_blocking_warning


class SinglePhaseInterleavedBoostPFCDiodeBridgeForm(BaseTopologyForm):
    """Expose the two-phase first-pass design and staged hardware workflow."""

    topology_id = "single_phase_interleaved_boost_pfc_diode_bridge"
    display_name = "Single-Phase Interleaved Boost PFC Diode Bridge"
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
        TopologyField("input_inductance_h", "Per-phase input inductance [H]", "0.0001"),
        TopologyField("ambient_temp_c", "Ambient temperature [C]", "25"),
        TopologyField("target_junction_temp_c", "Target junction temperature [C]", "100"),
    )

    @classmethod
    def get_semiconductor_design_fields(cls) -> tuple[TopologyField, ...]:
        """Expose shared filters for the four physical phase positions."""

        return super().get_semiconductor_design_fields()

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

        ttk.Label(self, text=self.display_name, style="Header.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        design_frame = ttk.LabelFrame(self, text="Design Inputs", style="Section.TLabelframe")
        design_frame.grid(row=1, column=0, sticky="ew")
        design_frame.columnconfigure(1, weight=1)
        design_input_fields = self.get_design_fields()
        self.build_design_input_rows(design_frame, design_input_fields)
        self.build_design_action_buttons(design_frame, row=len(design_input_fields))
        for button in (self.run_capacitor_button, self.run_magnetics_button):
            if button is not None:
                button.configure(state="disabled")

        op_frame = ttk.LabelFrame(self, text="Waveform Operating Point", style="Section.TLabelframe")
        op_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        op_frame.columnconfigure(1, weight=1)
        self.operating_vars = {"load_ratio": tk.StringVar(value="1.0")}
        ttk.Label(op_frame, text="Load ratio [0-1]").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["load_ratio"]).grid(
            row=0, column=1, sticky="ew", padx=6, pady=6
        )
        self.run_waveforms_button = ttk.Button(op_frame, text="Generate Waveforms", command=self._trigger_waveforms, state="disabled")
        self.run_waveforms_button.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(10, 6)
        )
        self.build_efficiency_sweep_button(op_frame, row=2, state="disabled")

        notes = ttk.LabelFrame(self, text="Notes", style="Section.TLabelframe")
        notes.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        ttk.Label(
            notes,
            text=(
                "First-pass CCM design with two phases fixed at 180-degree interleaving and ideal "
                "50/50 current sharing. Run Design selects the input bridge and four phase-position "
                "devices; Run Capacitor and Run Magnetics select shared DC-link and both phase "
                "inductors. Efficiency Sweep requires all selected hardware. Switching-edge detail, "
                "DCM/CrM, dynamic sharing, THD, EMI, and detailed parasitics are not modeled."
            ),
            justify="left",
            wraplength=420,
        ).pack(anchor="nw", padx=10, pady=10)
        self.update_from_report(None)

    def get_operating_point(self) -> OperatingPoint:
        """Return the requested AC input and load ratio for waveform refresh."""

        load_ratio = self._parse_operating_float("load_ratio", "Load ratio")
        clamped = min(max(load_ratio, 0.0), 1.0)
        if clamped != load_ratio:
            self.operating_vars["load_ratio"].set(f"{clamped:.3g}")
        vac_rms = self._parse_design_float("vac_rms", "Nominal AC input RMS voltage [V]")
        return OperatingPoint(vin_v=vac_rms, load_ratio=clamped)

    def update_from_report(self, report: DesignReport | None) -> None:
        """Enable hardware stages and efficiency only when their prerequisites exist."""

        has_candidate = report is not None and report.candidate is not None
        for button in (self.run_capacitor_button, self.run_magnetics_button):
            if button is not None:
                button.configure(state="normal" if has_candidate else "disabled")
        if self.run_waveforms_button is not None:
            self.run_waveforms_button.configure(state="normal" if has_candidate else "disabled")
        if self.run_efficiency_sweep_button is not None:
            self.run_efficiency_sweep_button.configure(
                state="normal" if efficiency_sweep_blocking_warning(report) is None else "disabled"
            )


__all__ = ["SinglePhaseInterleavedBoostPFCDiodeBridgeForm"]
