"""Workspace layout for category pages, topology selection, and runtime forms."""

from __future__ import annotations

from tkinter import ttk

from ...models.design_report import DesignReport
from ..category_views import (
    ACACCategoryPage,
    ACDCCategoryPage,
    ConverterCategoryPage,
    DCACCategoryPage,
    DCDCCategoryPage,
)
from ..result_views import (
    CapacitorPFView,
    CapacitorView,
    DeviceView,
    EfficiencyView,
    GeometryView,
    HardwareOverviewView,
    InductorPFView,
    InductorView,
    LossView,
    MagneticView,
    SummaryView,
    StressView,
    ThermalView,
    WaveformView,
)
from .state_store import AppStateStore


class Workspace(ttk.Frame):
    """Host the active category page or the selected topology form workspace."""

    def __init__(
        self,
        parent,
        state_store: AppStateStore,
        on_run_design,
        on_run_magnetics,
        on_generate_waveforms,
        on_category_selected,
        on_topology_selected,
        on_back_to_categories,
        on_run_capacitor=None,
        on_run_efficiency_sweep=None,
    ) -> None:
        super().__init__(parent, padding=12)
        self._state_store = state_store
        self._on_run_design = on_run_design
        self._on_run_capacitor = on_run_capacitor
        self._on_run_efficiency_sweep = on_run_efficiency_sweep
        self._on_run_magnetics = on_run_magnetics
        self._on_generate_waveforms = on_generate_waveforms
        self._on_category_selected = on_category_selected
        self._on_topology_selected = on_topology_selected
        self._on_back_to_categories = on_back_to_categories
        self.active_form = None
        self.active_page = None
        self.results_notebook = None
        self.summary_view = None
        self.hardware_overview_view = None
        self.waveform_view = None
        self.stress_view = None
        self.device_view = None
        self.capacitor_view = None
        self.capacitor_pf_view = None
        self.loss_view = None
        self.magnetic_view = None
        self.thermal_view = None
        self.geometry_view = None
        self.efficiency_view = None
        self.inductor_view = None
        self.inductor_pf_view = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.content_host = ttk.Frame(self)
        self.content_host.grid(row=0, column=0, sticky="nsew")
        self.content_host.columnconfigure(0, weight=1)
        self.content_host.rowconfigure(0, weight=1)

        self.show_category_selection()

    def _clear_content(self) -> None:
        if self.active_page is not None:
            self.active_page.destroy()
            self.active_page = None
        self.active_form = None
        for child in self.content_host.winfo_children():
            child.destroy()
        self.results_notebook = None
        self.summary_view = None
        self.hardware_overview_view = None
        self.waveform_view = None
        self.stress_view = None
        self.device_view = None
        self.capacitor_view = None
        self.capacitor_pf_view = None
        self.loss_view = None
        self.magnetic_view = None
        self.thermal_view = None
        self.geometry_view = None
        self.efficiency_view = None
        self.inductor_view = None
        self.inductor_pf_view = None

    def show_category_selection(self) -> None:
        """Render the first-level converter category page."""
        self._clear_content()
        self._state_store.set_active_page(None)
        self.active_page = ConverterCategoryPage(
            self.content_host,
            registry=self._state_store.registry,
            on_category_selected=self._on_category_selected,
        )
        self.active_page.grid(row=0, column=0, sticky="nsew")

    def show_category_page(self, category_id: str) -> None:
        """Render the topology-selection page for the chosen category."""
        self._clear_content()
        self._state_store.set_active_page(None)

        if category_id == "dc_dc":
            page = DCDCCategoryPage(
                self.content_host,
                registry=self._state_store.registry,
                on_topology_selected=self._on_topology_selected,
                on_back=self._on_back_to_categories,
            )
        elif category_id == "dc_ac":
            page = DCACCategoryPage(
                self.content_host,
                registry=self._state_store.registry,
                on_topology_selected=self._on_topology_selected,
                on_back=self._on_back_to_categories,
            )
        elif category_id == "ac_dc":
            page = ACDCCategoryPage(
                self.content_host,
                registry=self._state_store.registry,
                on_topology_selected=self._on_topology_selected,
                on_back=self._on_back_to_categories,
            )
        elif category_id == "ac_ac":
            page = ACACCategoryPage(self.content_host, on_back=self._on_back_to_categories)
        else:
            raise ValueError(f"Unsupported converter category: {category_id}")

        self.active_page = page
        self.active_page.grid(row=0, column=0, sticky="nsew")

    def load_form(self, topology_id: str) -> None:
        """Render the selected topology form beside the results notebook."""
        self._clear_content()
        self._state_store.set_active_page(None)

        content = ttk.Frame(self.content_host)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(0, weight=0)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        form_host = ttk.Frame(content)
        form_host.grid(row=0, column=0, sticky="nsw")

        self.results_notebook = ttk.Notebook(content)
        self.results_notebook.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        self.summary_view = SummaryView(self.results_notebook)
        self.hardware_overview_view = HardwareOverviewView(self.results_notebook)
        self.waveform_view = WaveformView(self.results_notebook)
        self.stress_view = StressView(self.results_notebook)
        self.device_view = DeviceView(self.results_notebook)
        self.capacitor_view = CapacitorView(self.results_notebook)
        self.capacitor_pf_view = CapacitorPFView(self.results_notebook)
        self.loss_view = LossView(self.results_notebook)
        self.magnetic_view = MagneticView(self.results_notebook)
        self.thermal_view = ThermalView(self.results_notebook)
        self.geometry_view = GeometryView(self.results_notebook)
        self.efficiency_view = EfficiencyView(self.results_notebook)
        self.inductor_view = InductorView(self.results_notebook)
        self.inductor_pf_view = InductorPFView(self.results_notebook)

        for label, view in (
            ("Summary", self.summary_view),
            ("Waveforms", self.waveform_view),
            ("Stress", self.stress_view),
            ("Devices", self.device_view),
            ("Capacitor PF", self.capacitor_pf_view),
            ("Capacitors", self.capacitor_view),
            ("Inductor PF", self.inductor_pf_view),
            ("Inductor", self.inductor_view),
            ("Magnetic", self.magnetic_view),
            ("Loss", self.loss_view),
            ("Thermal", self.thermal_view),
            ("Geometry", self.geometry_view),
            ("Efficiency", self.efficiency_view),
            ("Hardware Overview", self.hardware_overview_view),
        ):
            self.results_notebook.add(view, text=label)

        form_class = self._state_store.registry.get_form_class(topology_id)
        self.active_form = form_class(
            form_host,
            on_run_design=self._on_run_design,
            on_run_capacitor=self._on_run_capacitor,
            on_run_magnetics=self._on_run_magnetics,
            on_generate_waveforms=self._on_generate_waveforms,
            on_run_efficiency_sweep=self._on_run_efficiency_sweep,
        )
        self.active_form.grid(row=0, column=0, sticky="nsew")
        self.render_report(None)

    def render_report(self, report: DesignReport | None) -> None:
        """Push a report into all result views and the active form."""
        if self.active_form is not None:
            self.active_form.update_from_report(report)  # type: ignore[attr-defined]
        if self.summary_view is None:
            return
        self.summary_view.render(report)
        self.hardware_overview_view.render(report)
        self.waveform_view.render(report)
        self.stress_view.render(report)
        self.device_view.render(report)
        self.capacitor_view.render(report)
        self.capacitor_pf_view.render(report)
        self.loss_view.render(report)
        self.magnetic_view.render(report)
        self.thermal_view.render(report)
        self.geometry_view.render(report)
        self.efficiency_view.render(report)
        self.inductor_view.render(report)
        self.inductor_pf_view.render(report)
