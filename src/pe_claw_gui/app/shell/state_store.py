"""Shared GUI state for the new runtime shell."""

from __future__ import annotations

from dataclasses import dataclass

from ...models.design_report import DesignReport
from ...topologies.base import TopologyPlugin, TopologyRegistry


@dataclass
class AppStateStore:
    """In-memory GUI state owned by the main window."""

    registry: TopologyRegistry
    selected_category_id: str | None = None
    selected_topology_id: str | None = None
    active_page_name: str | None = None
    active_plugin: TopologyPlugin | None = None
    last_raw_input: dict[str, str] | None = None
    design_report: DesignReport | None = None

    def set_selected_category(self, category_id: str) -> None:
        """Select a converter category and clear topology-specific state."""
        self.selected_category_id = category_id
        self.clear_topology_selection()

    def set_selected_topology(self, topology_id: str, plugin: TopologyPlugin) -> None:
        """Switch the active topology and clear stage outputs."""
        definition = self.registry.get_definition(topology_id)
        self.selected_category_id = definition.category_id
        self.selected_topology_id = topology_id
        self.active_page_name = None
        self.active_plugin = plugin
        self.last_raw_input = None
        self.design_report = None

    def clear_topology_selection(self) -> None:
        """Clear the active topology, plugin, and generated results."""
        self.selected_topology_id = None
        self.active_page_name = None
        self.active_plugin = None
        self.last_raw_input = None
        self.design_report = None

    def reset_to_category_selection(self) -> None:
        """Return the GUI to the first-level category selection page."""
        self.selected_category_id = None
        self.clear_topology_selection()

    def set_active_page(self, page_name: str | None) -> None:
        """Record the currently visible high-level workspace page."""
        self.active_page_name = page_name
