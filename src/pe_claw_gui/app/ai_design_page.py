"""AI design page for system-level topology recommendation."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .result_views.ai_design_view import AIDesignView


class AIDesignPage(ttk.Frame):
    """Host the AI design intent form and the result view."""

    def __init__(self, parent, on_run_ai_design) -> None:
        super().__init__(parent, padding=12)
        self._on_run_ai_design = on_run_ai_design
        self._fields: dict[str, tk.Variable] = {}
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_layout()

    def _build_layout(self) -> None:
        form_host = ttk.Frame(self)
        form_host.grid(row=0, column=0, sticky="nsw")
        form_host.columnconfigure(1, weight=1)

        form_frame = ttk.LabelFrame(form_host, text="AI Design Intent", style="Section.TLabelframe", padding=12)
        form_frame.grid(row=0, column=0, sticky="nsew")
        form_frame.columnconfigure(1, weight=1)

        self._add_combobox(form_frame, 0, "Converter family", "converter_family", ("dc_dc", "dc_ac", "ac_dc", "ac_ac"), "dc_dc")
        self._add_entry(form_frame, 1, "Topology hint", "topology_hint", "")
        self._add_entry(form_frame, 2, "Vin min [V]", "vin_min_v", "80")
        self._add_entry(form_frame, 3, "Vin nominal [V]", "vin_nom_v", "100")
        self._add_entry(form_frame, 4, "Vin max [V]", "vin_max_v", "112")
        self._add_entry(form_frame, 5, "Vout [V]", "vout_v", "50")
        self._add_entry(form_frame, 6, "Iout [A]", "iout_a", "20")
        self._add_entry(form_frame, 7, "Pout [W]", "pout_w", "1000")
        self._add_entry(form_frame, 8, "Switching frequency [kHz]", "fsw_khz", "100")
        self._add_entry(form_frame, 9, "Voltage ripple ratio [%]", "voltage_ripple_ratio_percent", "1")
        self._add_entry(form_frame, 10, "Current ripple p-p [A]", "current_ripple_pp_a", "")
        self._add_checkbutton(form_frame, 11, "Isolation required", "isolation_required", False)
        self._add_checkbutton(form_frame, 12, "Bidirectional", "bidirectional", False)
        self._add_combobox(
            form_frame,
            13,
            "Load type",
            "load_type",
            ("resistive", "constant_current", "constant_power", "battery", "motor"),
            "resistive",
        )
        self._add_entry(form_frame, 14, "Priorities", "priorities", "efficiency, power_density, thermal_safety")

        ttk.Button(form_frame, text="Run AI Design", command=self._trigger_run).grid(
            row=15,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=6,
            pady=(12, 0),
        )

        result_frame = ttk.LabelFrame(self, text="AI Design Report", style="Section.TLabelframe", padding=12)
        result_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.result_view = AIDesignView(result_frame)
        self.result_view.grid(row=0, column=0, sticky="nsew")

    def _add_entry(self, parent, row: int, label: str, key: str, default: str) -> None:
        self._fields[key] = tk.StringVar(value=default)
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(parent, textvariable=self._fields[key]).grid(row=row, column=1, sticky="ew", padx=6, pady=4)

    def _add_combobox(self, parent, row: int, label: str, key: str, values: tuple[str, ...], default: str) -> None:
        self._fields[key] = tk.StringVar(value=default)
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        widget = ttk.Combobox(parent, textvariable=self._fields[key], values=values, state="readonly")
        widget.grid(row=row, column=1, sticky="ew", padx=6, pady=4)

    def _add_checkbutton(self, parent, row: int, label: str, key: str, default: bool) -> None:
        self._fields[key] = tk.BooleanVar(value=default)
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(parent, variable=self._fields[key]).grid(row=row, column=1, sticky="w", padx=6, pady=4)

    def _trigger_run(self) -> None:
        if self._on_run_ai_design is not None:
            self._on_run_ai_design()

    def get_form_values(self) -> dict[str, object]:
        """Return raw GUI values suitable for controller conversion."""

        return {key: variable.get() for key, variable in self._fields.items()}

    def render_report(self, report) -> None:
        """Render the AI design report in the right-hand result view."""

        self.result_view.render(report)
