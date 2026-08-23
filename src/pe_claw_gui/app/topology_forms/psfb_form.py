"""First-pass form for the isolated PSFB diode-rectifier topology."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...libraries.semiconductors.metadata import (
    DIODE_BINDING_POLICY_INPUT_KEY,
    DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS,
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_OPTIONS,
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_OPTIONS,
    INTERNAL_MODULE_DIODE_CATEGORY,
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
)
from ...topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated.input_schema import (
    build_default_inputs as build_psfb_default_inputs,
)
from .base_form import BaseTopologyForm, TopologyField

_PSFB_RECTIFIER_DIODE_CATEGORY_OPTIONS = tuple(
    option for option in RECTIFIER_DIODE_CATEGORY_OPTIONS if option != INTERNAL_MODULE_DIODE_CATEGORY
)
_PSFB_MAIN_SWITCH_CATEGORY_FIELD = TopologyField(
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    "Primary bridge switch category",
    "Any active switch",
    DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS,
)
_PSFB_RECTIFIER_DIODE_CATEGORY_FIELD = TopologyField(
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    "Secondary rectifier diode category",
    "Any diode",
    _PSFB_RECTIFIER_DIODE_CATEGORY_OPTIONS,
)
_PSFB_SEMICONDUCTOR_MANUFACTURER_FIELD = TopologyField(
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
    "Semiconductor manufacturer",
    "Any",
    SEMICONDUCTOR_MANUFACTURER_OPTIONS,
)


class PSFBTopologyForm(BaseTopologyForm):
    """Input form for first-pass PSFB diode-rectifier sizing."""

    topology_id = "phase_shifted_full_bridge_diode_rectifier_isolated"
    display_name = "Phase-Shifted Full-Bridge Diode Rectifier Isolated"
    implemented = True
    design_fields = (
        TopologyField("vin_min", "Vin min [V]", "650"),
        TopologyField("vin_nom", "Vin nominal [V]", "750"),
        TopologyField("vin_max", "Vin max [V]", "850"),
        TopologyField("vout", "Vout [V]", "400"),
        TopologyField("pout", "Pout [W]", "5000"),
        TopologyField("fs_khz", "Switching frequency [kHz]", "100"),
        TopologyField("ripple_current_ratio", "Output inductor ripple ratio", "0.25"),
        TopologyField("ripple_voltage_ratio_percent", "Output voltage ripple ratio [%]", "1.0"),
    )

    @classmethod
    def get_semiconductor_design_fields(cls) -> tuple[TopologyField, ...]:
        """Return independent primary switch and secondary diode controls."""

        return (
            _PSFB_MAIN_SWITCH_CATEGORY_FIELD,
            _PSFB_RECTIFIER_DIODE_CATEGORY_FIELD,
            _PSFB_SEMICONDUCTOR_MANUFACTURER_FIELD,
        )

    @classmethod
    def build_gui_default_raw_input(cls) -> dict[str, str]:
        """Return form-equivalent defaults without instantiating Tk widgets."""

        raw_input = build_psfb_default_inputs()
        raw_input.update({field.key: field.default for field in cls.get_design_fields()})
        raw_input[DIODE_BINDING_POLICY_INPUT_KEY] = "independent"
        return raw_input

    def _wire_semiconductor_category_links(self) -> None:
        """Keep the secondary PSFB rectifier diode independent from the primary switches."""

    def get_raw_input(self) -> dict[str, str]:
        """Return raw inputs while forcing the secondary diode binding policy independent."""

        raw_input = build_psfb_default_inputs()
        raw_input.update(super().get_raw_input())
        raw_input[DIODE_BINDING_POLICY_INPUT_KEY] = "independent"
        return raw_input

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

        design_frame = ttk.LabelFrame(self, text="First-Pass Design Inputs", style="Section.TLabelframe")
        design_frame.grid(row=1, column=0, sticky="ew")
        design_frame.columnconfigure(1, weight=1)

        design_fields = self.get_design_fields()
        self.build_design_input_rows(design_frame, design_fields)
        self.build_design_action_buttons(design_frame, row=len(design_fields))

        op_frame = ttk.LabelFrame(self, text="Waveform Operating Point", style="Section.TLabelframe")
        op_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        op_frame.columnconfigure(1, weight=1)
        self.operating_vars = {
            "vin_v": tk.StringVar(value=self.design_vars["vin_nom"].get()),
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
                "First-pass PSFB synthesis estimates turns ratio, leakage-driven duty loss, ZVS/deadtime "
                "evidence, switch stress, and secondary rectifier stress.\n\n"
                "The backend path wires semiconductor selection, transformer/output-inductor first-pass "
                "search, capacitor selection, loss, thermal, geometry, reports, and audit readback. Clamp, "
                "leakage tolerance, EMI, insulation, and manufacturability still require engineering review."
            ),
            justify="left",
            wraplength=460,
        ).pack(anchor="nw", padx=10, pady=10)

    def update_from_report(self, report) -> None:
        if report is not None and report.candidate is not None:
            self.operating_vars["vin_v"].set(f"{report.candidate.vin_nom:.4g}")


__all__ = ["PSFBTopologyForm"]
