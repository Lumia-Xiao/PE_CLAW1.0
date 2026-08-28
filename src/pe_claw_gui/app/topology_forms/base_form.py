"""Base topology form widgets."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable

from ...libraries.semiconductors.metadata import (
    ACTIVE_SWITCH_CATEGORY_OPTIONS,
    DIODE_BINDING_POLICY_INPUT_KEY,
    DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS,
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_OPTIONS,
    SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY,
    SEMICONDUCTOR_DEVICE_TYPE_OPTIONS,
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_OPTIONS,
    SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY,
    SWITCH_IMPLEMENTATION_CATEGORY_OPTIONS,
    SYNCHRONOUS_SWITCH_CATEGORY_OPTIONS,
    SYNC_SWITCH_CATEGORY_INPUT_KEY,
    THREE_LEVEL_SWITCH_CATEGORY_OPTIONS,
    INTERNAL_MODULE_DIODE_CATEGORY,
    diode_binding_policy_for_categories,
    is_module_bound_switch_category,
)
from ...libraries.semiconductors.topology_roles import classify_topology_role_family
from ...models.design_report import DesignReport
from ...models.operating_point import OperatingPoint


@dataclass(frozen=True)
class TopologyField:
    """One input field definition exposed by a topology form."""

    key: str
    label: str
    default: str
    choices: tuple[str, ...] = ()


AMBIENT_TEMPERATURE_FIELD = TopologyField("ambient_temp_c", "Ambient temperature (C)", "25.0")
TARGET_JUNCTION_TEMPERATURE_FIELD = TopologyField("target_junction_temp_c", "Target junction temperature (C)", "100.0")
SEMICONDUCTOR_DEVICE_TYPE_FIELD = TopologyField(
    SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY,
    "Semiconductor device type",
    "Any",
    SEMICONDUCTOR_DEVICE_TYPE_OPTIONS,
)
SEMICONDUCTOR_MANUFACTURER_FIELD = TopologyField(
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
    "Semiconductor manufacturer",
    "Any",
    SEMICONDUCTOR_MANUFACTURER_OPTIONS,
)
MAIN_SWITCH_CATEGORY_FIELD = TopologyField(
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    "Main switch category",
    "Any active switch",
    DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS,
)
RECTIFIER_DIODE_CATEGORY_FIELD = TopologyField(
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    "Rectifier diode category",
    "Any diode",
    RECTIFIER_DIODE_CATEGORY_OPTIONS,
)
SWITCH_DEVICE_CATEGORY_FIELD = TopologyField(
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    "Switch device category",
    "Any active switch",
    SYNCHRONOUS_SWITCH_CATEGORY_OPTIONS,
)
SYNC_SWITCH_CATEGORY_FIELD = TopologyField(
    SYNC_SWITCH_CATEGORY_INPUT_KEY,
    "Sync switch category",
    "Any active switch",
    SYNCHRONOUS_SWITCH_CATEGORY_OPTIONS,
)
SWITCH_IMPLEMENTATION_CATEGORY_FIELD = TopologyField(
    SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY,
    "Switch implementation",
    "Any compatible active switch",
    SWITCH_IMPLEMENTATION_CATEGORY_OPTIONS,
)
THREE_LEVEL_SWITCH_CATEGORY_FIELD = TopologyField(
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    "Switch device category",
    "Any active switch",
    THREE_LEVEL_SWITCH_CATEGORY_OPTIONS,
)


class BaseTopologyForm(ttk.Frame):
    """Base class for topology-specific GUI forms."""

    topology_id = "placeholder"
    display_name = "Placeholder"
    implemented = False
    supports_ambient_temperature = False
    design_fields: tuple[TopologyField, ...] = ()

    def __init__(
        self,
        parent,
        on_run_design=None,
        on_run_capacitor=None,
        on_run_magnetics=None,
        on_generate_waveforms=None,
        on_run_efficiency_sweep=None,
    ) -> None:
        super().__init__(parent, padding=12)
        self._on_run_design = on_run_design
        self._on_run_capacitor = on_run_capacitor
        self._on_run_magnetics = on_run_magnetics
        self._on_generate_waveforms = on_generate_waveforms
        self._on_run_efficiency_sweep = on_run_efficiency_sweep
        self.design_vars: dict[str, tk.StringVar] = {}
        self.operating_vars: dict[str, tk.StringVar] = {}
        self.run_design_button = None
        self.run_capacitor_button = None
        self.run_magnetics_button = None
        self.run_efficiency_sweep_button = None
        self._design_input_trace_ids: list[tuple[tk.StringVar, str]] = []
        self._on_design_input_changed: Callable[[], None] | None = None

    def get_raw_input(self) -> dict[str, str]:
        """Return the raw design input values from the form."""
        raw_input = {key: var.get() for key, var in self.design_vars.items()}
        if MAIN_SWITCH_CATEGORY_INPUT_KEY in raw_input or RECTIFIER_DIODE_CATEGORY_INPUT_KEY in raw_input:
            raw_input[DIODE_BINDING_POLICY_INPUT_KEY] = diode_binding_policy_for_categories(
                raw_input.get(MAIN_SWITCH_CATEGORY_INPUT_KEY),
                raw_input.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY),
            )
        return raw_input

    @classmethod
    def get_design_fields(cls) -> tuple[TopologyField, ...]:
        """Return the topology fields plus any shared runtime fields."""
        shared_fields = cls.get_semiconductor_design_fields()
        if cls.supports_ambient_temperature:
            return (*cls.design_fields, *shared_fields, AMBIENT_TEMPERATURE_FIELD, TARGET_JUNCTION_TEMPERATURE_FIELD)
        return (*cls.design_fields, *shared_fields)

    @classmethod
    def get_semiconductor_design_fields(cls) -> tuple[TopologyField, ...]:
        """Return topology-aware semiconductor category controls."""

        family = classify_topology_role_family(cls.topology_id)
        if family == "diode_rectified_two_role":
            return (MAIN_SWITCH_CATEGORY_FIELD, RECTIFIER_DIODE_CATEGORY_FIELD, SEMICONDUCTOR_MANUFACTURER_FIELD)
        if family == "synchronous_two_role":
            return (SWITCH_DEVICE_CATEGORY_FIELD, SYNC_SWITCH_CATEGORY_FIELD, SEMICONDUCTOR_MANUFACTURER_FIELD)
        if family == "four_switch":
            return (SWITCH_IMPLEMENTATION_CATEGORY_FIELD, SEMICONDUCTOR_MANUFACTURER_FIELD)
        if family == "three_level":
            return (THREE_LEVEL_SWITCH_CATEGORY_FIELD, SEMICONDUCTOR_MANUFACTURER_FIELD)
        return (SEMICONDUCTOR_DEVICE_TYPE_FIELD, SEMICONDUCTOR_MANUFACTURER_FIELD)

    def build_design_input_rows(self, parent, design_input_fields: tuple[TopologyField, ...]) -> None:
        """Create the shared design-input widgets for a topology form."""

        for row, field in enumerate(design_input_fields):
            self.design_vars[field.key] = tk.StringVar(value=field.default)
            ttk.Label(parent, text=field.label).grid(row=row, column=0, sticky="w", padx=6, pady=6)
            if field.choices:
                widget = ttk.Combobox(
                    parent,
                    textvariable=self.design_vars[field.key],
                    values=field.choices,
                    state="readonly",
                )
            else:
                widget = ttk.Entry(parent, textvariable=self.design_vars[field.key])
            widget.grid(row=row, column=1, sticky="ew", padx=6, pady=6)
        self._wire_semiconductor_category_links()

    def set_design_input_change_handler(self, handler: Callable[[], None] | None) -> None:
        """Notify the shell when a design input changes after form creation."""

        for variable, trace_id in self._design_input_trace_ids:
            try:
                variable.trace_remove("write", trace_id)
            except tk.TclError:
                pass
        self._design_input_trace_ids.clear()
        self._on_design_input_changed = handler
        if handler is None:
            return

        for variable in self.design_vars.values():
            trace_id = variable.trace_add("write", self._notify_design_input_changed)
            self._design_input_trace_ids.append((variable, trace_id))

    def _notify_design_input_changed(self, *_args) -> None:
        if self._on_design_input_changed is not None:
            self._on_design_input_changed()

    def build_design_action_buttons(self, parent, row: int, state: str = "normal") -> None:
        """Create the Run Design / Run Capacitor / Run Magnetics row for design forms."""
        button_row = ttk.Frame(parent)
        button_row.grid(row=row, column=0, columnspan=2, sticky="ew", padx=6, pady=(10, 6))
        button_row.columnconfigure(0, weight=1, uniform="design_actions")
        button_row.columnconfigure(1, weight=1, uniform="design_actions")
        button_row.columnconfigure(2, weight=1, uniform="design_actions")
        self.run_design_button = ttk.Button(
            button_row,
            text="Run Design",
            command=self._trigger_run_design,
            state=state,
        )
        self.run_design_button.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.run_capacitor_button = ttk.Button(
            button_row,
            text="Run Capacitor",
            command=self._trigger_run_capacitor,
            state=state,
        )
        self.run_capacitor_button.grid(row=0, column=1, sticky="ew", padx=3)
        self.run_magnetics_button = ttk.Button(
            button_row,
            text="Run Magnetics",
            command=self._trigger_run_magnetics,
            state=state,
        )
        self.run_magnetics_button.grid(row=0, column=2, sticky="ew", padx=(3, 0))

    def build_efficiency_sweep_button(self, parent, row: int, state: str = "normal") -> None:
        """Create the fixed-hardware efficiency sweep action button."""
        self.run_efficiency_sweep_button = ttk.Button(
            parent,
            text="Run Efficiency Sweep",
            command=self._trigger_efficiency_sweep,
            state=state,
        )
        self.run_efficiency_sweep_button.grid(row=row, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 6))

    def _wire_semiconductor_category_links(self) -> None:
        main_var = self.design_vars.get(MAIN_SWITCH_CATEGORY_INPUT_KEY)
        diode_var = self.design_vars.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY)
        if main_var is None or diode_var is None:
            return

        def update_diode_binding(*_args) -> None:
            if is_module_bound_switch_category(main_var.get()):
                diode_var.set(INTERNAL_MODULE_DIODE_CATEGORY)

        main_var.trace_add("write", update_diode_binding)
        update_diode_binding()

    def get_runtime_overrides(self) -> dict[str, str]:
        """Return non-redesign runtime overrides that should affect refresh stages."""
        overrides: dict[str, str] = {}
        ambient_var = self.design_vars.get(AMBIENT_TEMPERATURE_FIELD.key)
        if ambient_var is not None:
            overrides[AMBIENT_TEMPERATURE_FIELD.key] = ambient_var.get()
        target_junction_var = self.design_vars.get(TARGET_JUNCTION_TEMPERATURE_FIELD.key)
        if target_junction_var is not None:
            overrides[TARGET_JUNCTION_TEMPERATURE_FIELD.key] = target_junction_var.get()
        return overrides

    def get_operating_point(self) -> OperatingPoint:
        """Return the requested operating point for waveform generation."""
        vin_value = self._parse_operating_float("vin_v", "Operating Vin [V]", default="0")
        load_ratio = self._parse_operating_float("load_ratio", "Load ratio", default="1.0")
        return OperatingPoint(vin_v=vin_value, load_ratio=load_ratio)

    def _parse_design_float(self, key: str, label: str) -> float:
        """Parse a design input and raise a user-facing validation error."""

        var = self.design_vars.get(key)
        value = var.get() if var is not None else None
        return self._parse_numeric_value(value, label)

    def _parse_operating_float(self, key: str, label: str, *, default: str | None = None) -> float:
        """Parse an operating-point input and raise a user-facing validation error."""

        var = self.operating_vars.get(key)
        value = default if var is None else var.get()
        return self._parse_numeric_value(value, label)

    @staticmethod
    def _parse_numeric_value(value: object, label: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be a valid number.") from exc

    def update_from_report(self, report: DesignReport) -> None:
        """Allow a form to react to a generated report."""

    def _trigger_run_design(self) -> None:
        if self._on_run_design is not None:
            self._on_run_design()

    def _trigger_run_capacitor(self) -> None:
        if self._on_run_capacitor is not None:
            self._on_run_capacitor()

    def _trigger_run_magnetics(self) -> None:
        if self._on_run_magnetics is not None:
            self._on_run_magnetics()

    def _trigger_waveforms(self) -> None:
        if self._on_generate_waveforms is not None:
            self._on_generate_waveforms()

    def _trigger_efficiency_sweep(self) -> None:
        if self._on_run_efficiency_sweep is not None:
            self._on_run_efficiency_sweep()


class PlaceholderTopologyForm(BaseTopologyForm):
    """Safe placeholder form for not-yet-implemented topologies."""

    implemented = False

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
        frame = ttk.LabelFrame(self, text="Topology Status", style="Section.TLabelframe")
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(
            frame,
            text=(
                f"{self.display_name} is a placeholder only.\n\n"
                "Implemented DC-DC topologies currently include Buck and Boost "
                "diode-rectified / synchronous-rectified variants, the "
                "diode-rectified inverting Buck-Boost, and a simplified "
                "four-switch non-inverting Buck-Boost."
            ),
            justify="left",
        ).pack(anchor="nw", padx=12, pady=12)
        button_row = ttk.Frame(frame)
        button_row.pack(fill="x", padx=12, pady=(0, 8))
        button_row.columnconfigure(0, weight=1, uniform="design_actions")
        button_row.columnconfigure(1, weight=1, uniform="design_actions")
        button_row.columnconfigure(2, weight=1, uniform="design_actions")
        self.run_design_button = ttk.Button(button_row, text="Run Design", command=self._trigger_run_design, state="disabled")
        self.run_design_button.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.run_capacitor_button = ttk.Button(button_row, text="Run Capacitor", command=self._trigger_run_capacitor, state="disabled")
        self.run_capacitor_button.grid(row=0, column=1, sticky="ew", padx=3)
        self.run_magnetics_button = ttk.Button(button_row, text="Run Magnetics", command=self._trigger_run_magnetics, state="disabled")
        self.run_magnetics_button.grid(row=0, column=2, sticky="ew", padx=(3, 0))
        ttk.Button(frame, text="Generate Waveforms", command=self._trigger_waveforms, state="disabled").pack(fill="x", padx=12, pady=(0, 12))
        self.run_efficiency_sweep_button = ttk.Button(
            frame,
            text="Run Efficiency Sweep",
            command=self._trigger_efficiency_sweep,
            state="disabled",
        )
        self.run_efficiency_sweep_button.pack(fill="x", padx=12, pady=(0, 12))
