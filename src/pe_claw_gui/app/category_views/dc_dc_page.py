"""DC-DC topology selection page."""

from __future__ import annotations

from tkinter import ttk

from ...topologies.base import TopologyRegistry


class DCDCCategoryPage(ttk.Frame):
    """List registered DC-DC topologies for the selected category."""

    def __init__(self, parent, registry: TopologyRegistry, on_topology_selected, on_back) -> None:
        super().__init__(parent, padding=24)
        self.columnconfigure(0, weight=1)

        ttk.Label(self, text="DC-DC Topologies", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(
            self,
            text="Select a DC-DC circuit topology to open its input form.",
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        definitions = registry.list_topologies("dc_dc")
        if definitions:
            list_frame = ttk.LabelFrame(self, text="Available Topologies", style="Section.TLabelframe", padding=12)
            list_frame.grid(row=2, column=0, sticky="ew")
            list_frame.columnconfigure(0, weight=1)
            for row, definition in enumerate(definitions):
                ttk.Button(
                    list_frame,
                    text=definition.display_name,
                    command=lambda topology_id=definition.topology_id: on_topology_selected(topology_id),
                ).grid(row=row, column=0, sticky="ew", pady=4)
        else:
            ttk.Label(
                self,
                text="No DC-DC topologies are registered yet.",
                justify="left",
            ).grid(row=2, column=0, sticky="w")

        ttk.Button(self, text="Back to Categories", command=on_back).grid(row=3, column=0, sticky="w", pady=(16, 0))


__all__ = ["DCDCCategoryPage"]
