"""Input form for the single-phase full-bridge inverter."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport
from ...models.operating_point import OperatingPoint
from .base_form import BaseTopologyForm, TopologyField


class SinglePhaseFullBridgeInverterForm(BaseTopologyForm):
    """First-pass form for the single-phase full-bridge inverter."""

    topology_id = "single_phase_full_bridge_inverter"
    display_name = "Single-Phase Full-Bridge Inverter"
    implemented = True
    common_design_fields = (
        TopologyField("conduction_mode", "Current mode", "CCM", ("CCM", "TCM")),
        TopologyField("vdc_nom", "Vdc nominal [V]", "400"),
        TopologyField("vac_rms", "Vac rms [V]", "230"),
        TopologyField("f_line_hz", "Line frequency [Hz]", "50"),
        TopologyField("pout_w", "Pout [W]", "1000"),
        TopologyField("power_factor", "Power factor", "1.0"),
        TopologyField("dc_link_voltage_ripple_ratio", "DC-link ripple ratio [pp/Vdc]", "0.05"),
    )
    ccm_design_fields = (
        TopologyField("fsw_hz", "Switching frequency [Hz]", "20000"),
        TopologyField("inductor_current_ripple_ratio", "Inductor ripple ratio [pp/Ipk]", "0.2"),
    )
    tcm_design_fields = (
        TopologyField("fsw_min_hz", "TCM minimum switching frequency [Hz]", "50000"),
        TopologyField("fsw_max_hz", "TCM maximum switching frequency [Hz]", "300000"),
        TopologyField("tcm_valley_current_target_a", "TCM valley current target [A]", "-1"),
    )
    thermal_design_fields = (
        TopologyField("ambient_temp_c", "Ambient temperature [C]", "25"),
        TopologyField("target_junction_temp_c", "Target junction temperature [C]", "100"),
    )
    design_fields = (*common_design_fields, *ccm_design_fields, *tcm_design_fields, *thermal_design_fields)

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
        design_frame.columnconfigure(0, weight=1)
        action_row = self._build_grouped_design_inputs(design_frame)
        self.build_design_action_buttons(design_frame, row=action_row)
        if self.run_capacitor_button is not None:
            self.run_capacitor_button.configure(state="disabled")
        if self.run_magnetics_button is not None:
            self.run_magnetics_button.configure(state="disabled")
        self.design_vars["conduction_mode"].trace_add("write", lambda *_args: self._update_mode_specific_inputs())
        self._update_mode_specific_inputs()

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
        self.build_efficiency_sweep_button(op_frame, row=3, state="disabled")

        notes = ttk.LabelFrame(self, text="Notes", style="Section.TLabelframe")
        notes.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        ttk.Label(
            notes,
            text=(
                "CCM is the active first-pass design mode and sizes the AC output inductor from "
                "unipolar-SPWM current ripple. TCM shows the staged variable-frequency inputs for the upcoming "
                "triangular-current synthesis with a fixed negative valley-current target.\n"
                "Run Design sizes the AC output inductor from CCM unipolar-SPWM current ripple and sizes "
                "the DC-link electrolytic capacitor from single-phase twice-line energy balance, then selects "
                "a first-pass inverter switch for four bridge positions.\n"
                "Run Capacitor selects a first-pass DC-link electrolytic bank; Run Magnetics selects a rough "
                "output inductor realization. Run Efficiency Sweep reuses the selected switch, capacitor bank, "
                "and output inductor over the fixed-hardware load grid."
            ),
            justify="left",
            wraplength=360,
        ).pack(anchor="nw", padx=10, pady=10)

    def _build_grouped_design_inputs(self, parent) -> int:
        """Build common, CCM, TCM, and shared device/thermal input sections."""

        common_frame = ttk.LabelFrame(parent, text="Common", style="Section.TLabelframe")
        common_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 4))
        common_frame.columnconfigure(1, weight=1)
        self.build_design_input_rows(common_frame, self.common_design_fields)

        self.ccm_parameters_frame = ttk.LabelFrame(parent, text="CCM Parameters", style="Section.TLabelframe")
        self.ccm_parameters_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=4)
        self.ccm_parameters_frame.columnconfigure(1, weight=1)
        self.build_design_input_rows(self.ccm_parameters_frame, self.ccm_design_fields)

        self.tcm_parameters_frame = ttk.LabelFrame(parent, text="TCM Parameters", style="Section.TLabelframe")
        self.tcm_parameters_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=4)
        self.tcm_parameters_frame.columnconfigure(1, weight=1)
        self.build_design_input_rows(self.tcm_parameters_frame, self.tcm_design_fields)

        shared_frame = ttk.LabelFrame(parent, text="Device / Thermal", style="Section.TLabelframe")
        shared_frame.grid(row=3, column=0, sticky="ew", padx=6, pady=4)
        shared_frame.columnconfigure(1, weight=1)
        shared_fields = (*self.get_semiconductor_design_fields(), *self.thermal_design_fields)
        self.build_design_input_rows(shared_frame, shared_fields)
        return 4

    def _update_mode_specific_inputs(self) -> None:
        """Show only the mode-specific parameter group for the selected current mode."""

        mode = self.design_vars["conduction_mode"].get().strip().lower()
        if mode == "tcm":
            self.ccm_parameters_frame.grid_remove()
            self.tcm_parameters_frame.grid()
            return
        self.tcm_parameters_frame.grid_remove()
        self.ccm_parameters_frame.grid()

    def get_operating_point(self) -> OperatingPoint:
        """Return waveform operating point using the design DC bus voltage."""

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

    def update_from_report(self, report: DesignReport | None) -> None:
        """Enable DC-link capacitor selection after the inverter design exists."""

        if self.run_capacitor_button is not None:
            state = "normal" if report is not None and report.candidate is not None else "disabled"
            self.run_capacitor_button.configure(state=state)
        if self.run_magnetics_button is not None:
            state = "normal" if report is not None and report.candidate is not None else "disabled"
            self.run_magnetics_button.configure(state=state)
        if self.run_efficiency_sweep_button is not None:
            state = (
                "normal"
                if report is not None
                and report.candidate is not None
                and report.device is not None
                and (report.device.selected_devices or report.device.design_point_losses)
                else "disabled"
            )
            self.run_efficiency_sweep_button.configure(state=state)
