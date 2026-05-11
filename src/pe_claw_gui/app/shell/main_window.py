"""Main window for the new PE-Claw runtime architecture."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ...topologies.base import build_default_registry
from ..controllers.ai_design_controller import AIDesignController
from ..controllers.device_controller import DeviceController
from ..controllers.efficiency_sweep_controller import EfficiencySweepController
from ..controllers.export_controller import ExportController
from ..controllers.run_design_controller import RunDesignController
from ..controllers.waveform_controller import WaveformController
from .navigation import NavigationBar
from .state_store import AppStateStore
from .workspace import Workspace


class PEClawMainWindow(tk.Tk):
    """Main Tk application shell driven by registry, forms, controllers, and result views."""

    def __init__(self) -> None:
        super().__init__()
        self.title("PE-Claw")
        self.geometry("1400x860")
        self.minsize(1240, 760)

        registry = build_default_registry()
        self.state_store = AppStateStore(
            registry=registry,
        )

        self.design_controller = RunDesignController(self.state_store)
        self.ai_design_controller = AIDesignController(self.state_store)
        self.waveform_controller = WaveformController(self.state_store)
        self.device_controller = DeviceController(self.state_store)
        self.efficiency_sweep_controller = EfficiencySweepController(self.state_store)
        self.export_controller = ExportController(self.state_store)

        self._build_style()
        self._build_layout()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Arial", 10, "bold"))

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.navigation = NavigationBar(
            self,
            self.state_store,
            on_show_categories=self._show_category_selection,
            on_show_category_topologies=self._show_selected_category_page,
            on_show_ai_design=self._show_ai_design_page,
        )
        self.navigation.grid(row=0, column=0, sticky="ew")

        self.workspace = Workspace(
            self,
            state_store=self.state_store,
            on_run_design=self._on_run_design,
            on_run_ai_design=self._on_run_ai_design,
            on_run_capacitor=self._on_run_capacitor,
            on_run_magnetics=self._on_run_magnetics,
            on_generate_waveforms=self._on_generate_waveforms,
            on_run_efficiency_sweep=self._on_run_efficiency_sweep,
            on_category_selected=self._on_category_selected,
            on_topology_selected=self._on_topology_selected,
            on_back_to_categories=self._show_category_selection,
        )
        self.workspace.grid(row=1, column=0, sticky="nsew")

    def _show_category_selection(self) -> None:
        self.state_store.reset_to_category_selection()
        self.workspace.show_category_selection()
        self.navigation.refresh()

    def _show_selected_category_page(self) -> None:
        if self.state_store.selected_category_id is None:
            self._show_category_selection()
            return
        self.state_store.clear_topology_selection()
        self.workspace.show_category_page(self.state_store.selected_category_id)
        self.navigation.refresh()

    def _on_category_selected(self, category_id: str) -> None:
        self.state_store.set_selected_category(category_id)
        self.workspace.show_category_page(category_id)
        self.navigation.refresh()

    def _on_topology_selected(self, topology_id: str) -> None:
        plugin = self.state_store.registry.get_plugin(topology_id)
        self.state_store.set_selected_topology(topology_id, plugin)
        self.workspace.load_form(topology_id)
        self.navigation.refresh()

    def _show_ai_design_page(self) -> None:
        self.workspace.show_ai_design_page()
        self.navigation.refresh()

    def _on_run_design(self) -> None:
        try:
            if self.workspace.active_form is None:
                raise RuntimeError("Select a topology before running the design.")
            raw_input = self.workspace.active_form.get_raw_input()
            report = self.design_controller.run_active_topology(raw_input)
            self.workspace.render_report(report)
            self.navigation.refresh()
        except RuntimeError as exc:  # pragma: no cover - GUI path
            messagebox.showwarning("Selection Required", str(exc))
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("Design Error", str(exc))

    def _on_run_magnetics(self) -> None:
        try:
            report = self.design_controller.run_active_magnetics()
            self.workspace.render_report(report)
            if self.workspace.results_notebook is not None and self.workspace.inductor_view is not None:
                self.workspace.results_notebook.select(self.workspace.inductor_view)
            self.navigation.refresh()
        except RuntimeError as exc:  # pragma: no cover - GUI path
            messagebox.showwarning("No Design", str(exc))
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("Magnetics Error", str(exc))

    def _on_run_ai_design(self) -> None:
        try:
            if self.workspace.ai_design_page is None:
                raise RuntimeError("Open AI Design before running the AI pipeline.")
            report, error_message = self.ai_design_controller.run_ai_design(self.workspace.ai_design_page.get_form_values())
            if error_message is not None or report is None:
                raise RuntimeError(error_message or "AI design pipeline failed.")
            self.workspace.render_ai_design_report(report)
            self.navigation.refresh()
        except RuntimeError as exc:  # pragma: no cover - GUI path
            messagebox.showwarning("AI Design", str(exc))
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("AI Design Error", str(exc))

    def _on_run_capacitor(self) -> None:
        try:
            report = self.design_controller.run_active_capacitors()
            self.workspace.render_report(report)
            if self.workspace.results_notebook is not None and self.workspace.capacitor_view is not None:
                self.workspace.results_notebook.select(self.workspace.capacitor_view)
            self.navigation.refresh()
        except RuntimeError as exc:  # pragma: no cover - GUI path
            messagebox.showwarning("No Design", str(exc))
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("Capacitor Error", str(exc))

    def _on_generate_waveforms(self) -> None:
        try:
            if self.workspace.active_form is None:
                raise RuntimeError("Select a topology before generating waveforms.")
            operating_point = self.workspace.active_form.get_operating_point()
            runtime_overrides = self.workspace.active_form.get_runtime_overrides()
            report = self.waveform_controller.generate_waveforms(operating_point, runtime_overrides=runtime_overrides)
            self.workspace.render_report(report)
            if self.workspace.results_notebook is not None and self.workspace.waveform_view is not None:
                self.workspace.results_notebook.select(self.workspace.waveform_view)
            self.navigation.refresh()
        except RuntimeError as exc:  # pragma: no cover - GUI path
            messagebox.showwarning("No Design", str(exc))
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("Waveform Error", str(exc))

    def _on_run_efficiency_sweep(self) -> None:
        try:
            report = self.efficiency_sweep_controller.run_active_efficiency_sweep()
            self.workspace.render_report(report)
            if self.workspace.results_notebook is not None and self.workspace.efficiency_view is not None:
                self.workspace.results_notebook.select(self.workspace.efficiency_view)
            self.navigation.refresh()
        except RuntimeError as exc:  # pragma: no cover - GUI path
            messagebox.showwarning("Efficiency Sweep", str(exc))
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("Efficiency Sweep Error", str(exc))


def main() -> None:
    """Launch the PE-Claw GUI."""
    app = PEClawMainWindow()
    app.mainloop()
