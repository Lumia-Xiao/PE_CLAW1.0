"""Shared LLC FHA input form helpers."""

from __future__ import annotations

from tkinter import ttk

from .base_form import BaseTopologyForm, TopologyField

LLC_PLACEHOLDER_NOTE = (
    "LLC FHA synthesis is not implemented yet. These inputs capture the design specification for a later FHA calculation step."
)
LLC_FHA_DIODE_NOTE = (
    "LLC diode-rectifier FHA workflow is implemented for first-pass electrical design, waveform generation, "
    "semiconductor selection, transformer screening, external resonant inductor design, resonant capacitor "
    "selection, loss summaries, and engineering artifacts."
)


class LLCPlaceholderForm(BaseTopologyForm):
    """Temporary LLC form exposing FHA design-specification inputs."""

    implemented = False
    supports_ambient_temperature = False
    show_placeholder_status = True
    status_note = LLC_PLACEHOLDER_NOTE
    design_fields = (
        TopologyField("vin_min", "Input voltage min [V]", "360"),
        TopologyField("vin_nom", "Input voltage nominal [V]", "400"),
        TopologyField("vin_max", "Input voltage max [V]", "420"),
        TopologyField("vout_min", "Output voltage min [V]", "48"),
        TopologyField("vout_nom", "Output voltage nominal [V]", "48"),
        TopologyField("vout_max", "Output voltage max [V]", "48"),
        TopologyField("pout_max", "Maximum output power [W]", "4000"),
        TopologyField("min_load_ratio", "Minimum load ratio [p.u.]", "0.1"),
        TopologyField("fs_min_hz", "Minimum switching frequency [Hz]", "80000"),
        TopologyField("fs_max_hz", "Maximum switching frequency [Hz]", "180000"),
    )

    @classmethod
    def get_design_fields(cls) -> tuple[TopologyField, ...]:
        """Return only LLC FHA design fields for the placeholder LLC pages."""

        return cls.design_fields

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

        next_row = 1
        if self.show_placeholder_status and self.status_note:
            note_frame = ttk.LabelFrame(self, text="Placeholder Status", style="Section.TLabelframe")
            note_frame.grid(row=next_row, column=0, sticky="ew")
            ttk.Label(note_frame, text=self.status_note, justify="left", wraplength=420).pack(
                anchor="nw",
                padx=10,
                pady=10,
            )
            next_row += 1

        design_frame = ttk.LabelFrame(self, text="LLC FHA Design Inputs", style="Section.TLabelframe")
        design_frame.grid(row=next_row, column=0, sticky="ew", pady=(12, 0))
        design_frame.columnconfigure(1, weight=1)
        self.design_frame = design_frame

        design_input_fields = self.get_design_fields()
        self.design_input_field_count = len(design_input_fields)
        self.build_design_input_rows(design_frame, design_input_fields)
        self.build_design_action_buttons(design_frame, row=self.design_input_field_count)
        self.next_form_row = next_row + 1
