"""LLC diode-rectifier FHA form."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.operating_point import OperatingPoint
from ...libraries.semiconductors.metadata import (
    DIODE_BINDING_POLICY_INPUT_KEY,
    DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS,
    PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
    PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_OPTIONS,
    RECTIFIER_DIODE_DEVICE_TYPE_INPUT_KEY,
    RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY,
    SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_OPTIONS,
    diode_binding_policy_for_categories,
)
from .llc_placeholder_form import LLC_FHA_DIODE_NOTE, LLCPlaceholderForm
from .base_form import (
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    TopologyField,
)


class LLCResonantConverterDiodeRectifierForm(LLCPlaceholderForm):
    """Input form for first-pass FHA-based LLC diode-rectifier design."""

    topology_id = "llc_resonant_converter_diode_rectifier"
    display_name = "LLC Resonant Converter Diode Rectifier"
    implemented = True
    show_placeholder_status = False
    status_note = LLC_FHA_DIODE_NOTE
    design_fields = (
        *LLCPlaceholderForm.design_fields,
        TopologyField("ripple_voltage_ratio_percent", "Voltage ripple ratio [%]", "1.0"),
        TopologyField("turns_ratio_tolerance_percent", "Turns-ratio tolerance [%]", "5.0"),
        TopologyField("primary_bridge_type", "Primary bridge type", "full_bridge", ("full_bridge", "half_bridge")),
        TopologyField(
            "secondary_rectifier_type",
            "Secondary rectifier type",
            "full_bridge_rectifier",
            ("full_bridge_rectifier", "full_wave_center_tapped_rectifier"),
        ),
    )
    semiconductor_filter_fields = (
        TopologyField(
            PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
            "Primary switch type",
            "Any active switch",
            DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS,
        ),
        TopologyField(
            PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
            "Primary switch manufacturer",
            "Any",
            SEMICONDUCTOR_MANUFACTURER_OPTIONS,
        ),
        TopologyField(
            RECTIFIER_DIODE_DEVICE_TYPE_INPUT_KEY,
            "Rectifier diode type",
            "Any diode",
            RECTIFIER_DIODE_CATEGORY_OPTIONS,
        ),
        TopologyField(
            RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY,
            "Rectifier diode manufacturer",
            "Any",
            SEMICONDUCTOR_MANUFACTURER_OPTIONS,
        ),
    )

    @classmethod
    def get_design_fields(cls) -> tuple[TopologyField, ...]:
        """Return LLC FHA fields plus role-specific semiconductor filters."""

        return (*cls.design_fields, *cls.semiconductor_filter_fields)

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
        self.build_efficiency_sweep_button(
            self.design_frame,
            row=self.design_input_field_count + 1,
        )
        op_frame = ttk.LabelFrame(self, text="Waveform Operating Point", style="Section.TLabelframe")
        op_frame.grid(row=getattr(self, "next_form_row", 3), column=0, sticky="ew", pady=(12, 0))
        op_frame.columnconfigure(1, weight=1)

        self.operating_vars = {
            "vin_v": tk.StringVar(value=self.design_vars["vin_nom"].get()),
            "vout_v": tk.StringVar(value=self.design_vars["vout_nom"].get()),
            "load_ratio": tk.StringVar(value="1.0"),
        }

        ttk.Label(op_frame, text="Waveform Vin [V]").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["vin_v"]).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Label(op_frame, text="Waveform Vout [V]").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["vout_v"]).grid(row=1, column=1, sticky="ew", padx=6, pady=6)
        ttk.Label(op_frame, text="Waveform load ratio [p.u.]").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(op_frame, textvariable=self.operating_vars["load_ratio"]).grid(row=2, column=1, sticky="ew", padx=6, pady=6)
        self.generate_waveforms_button = ttk.Button(
            op_frame,
            text="Generate Waveforms",
            command=self._trigger_waveforms,
        )
        self.generate_waveforms_button.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=6,
            pady=(10, 6),
        )

    def get_raw_input(self) -> dict[str, str]:
        raw_input = super().get_raw_input()
        primary_type = raw_input.get(PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY, "Any active switch")
        diode_type = raw_input.get(RECTIFIER_DIODE_DEVICE_TYPE_INPUT_KEY, "Any diode")
        raw_input[MAIN_SWITCH_CATEGORY_INPUT_KEY] = primary_type
        raw_input[RECTIFIER_DIODE_CATEGORY_INPUT_KEY] = diode_type
        raw_input.setdefault(SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY, "Any")
        raw_input.setdefault(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY, "Any")
        raw_input[DIODE_BINDING_POLICY_INPUT_KEY] = diode_binding_policy_for_categories(primary_type, diode_type)
        return raw_input

    def get_operating_point(self) -> OperatingPoint:
        return OperatingPoint(
            vin_v=self._parse_operating_float("vin_v", "Operating Vin [V]"),
            vout_v=self._parse_operating_float("vout_v", "Operating Vout [V]"),
            load_ratio=self._parse_operating_float("load_ratio", "Load ratio"),
        )

    def update_from_report(self, report) -> None:
        if report is not None and report.candidate is not None and report.waveform is None:
            self.operating_vars["vin_v"].set(f"{report.candidate.vin_nom:.4g}")
            self.operating_vars["vout_v"].set(f"{report.candidate.vout_target:.4g}")


__all__ = ["LLCResonantConverterDiodeRectifierForm"]
