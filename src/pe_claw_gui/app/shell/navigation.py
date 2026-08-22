"""Navigation widgets for the category-first runtime flow."""

from __future__ import annotations

from tkinter import ttk

from .state_store import AppStateStore


class NavigationBar(ttk.Frame):
    """Show the current selection path and allow returning to earlier steps."""

    def __init__(
        self,
        parent,
        state_store: AppStateStore,
        on_show_categories,
        on_show_category_topologies,
    ) -> None:
        super().__init__(parent, padding=(12, 12, 12, 0))
        self._state_store = state_store
        self._on_show_categories = on_show_categories
        self._on_show_category_topologies = on_show_category_topologies

        self.columnconfigure(3, weight=1)

        ttk.Button(self, text="Categories", command=self._on_show_categories).grid(row=0, column=0, sticky="w")
        self.topologies_button = ttk.Button(self, text="Topologies", command=self._on_show_category_topologies)
        self.topologies_button.grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(self, text="Current", style="Header.TLabel").grid(row=0, column=2, sticky="e", padx=(16, 8))
        self.selection_label = ttk.Label(self, text="", anchor="w")
        self.selection_label.grid(row=0, column=3, sticky="ew")

        self.refresh()

    def refresh(self) -> None:
        """Update the navigation bar for the active category and topology."""
        category_label = "No category selected"
        topology_label = "No topology selected"

        if self._state_store.selected_category_id is not None:
            category = self._state_store.registry.get_category(self._state_store.selected_category_id)
            category_label = category.display_name

        if self._state_store.selected_topology_id is not None:
            definition = self._state_store.registry.get_definition(self._state_store.selected_topology_id)
            topology_label = definition.display_name

        self.selection_label.configure(text=f"{category_label} -> {topology_label}")
        if self._state_store.selected_category_id is None:
            self.topologies_button.state(["disabled"])
        else:
            self.topologies_button.state(["!disabled"])
