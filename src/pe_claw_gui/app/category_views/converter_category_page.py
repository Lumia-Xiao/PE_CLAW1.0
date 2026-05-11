"""First-level converter category selection page."""

from __future__ import annotations

from tkinter import ttk

from ...topologies.base import TopologyRegistry


class ConverterCategoryPage(ttk.Frame):
    """Show the four major converter categories as the first runtime step."""

    def __init__(self, parent, registry: TopologyRegistry, on_category_selected) -> None:
        super().__init__(parent, padding=24)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Select Converter Category", style="Header.TLabel").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )
        ttk.Label(
            self,
            text="Choose the first-level converter family before selecting a specific circuit topology.",
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 16))

        for index, category in enumerate(registry.list_categories()):
            row = index // 2 + 2
            column = index % 2
            card = ttk.LabelFrame(self, text=category.display_name, style="Section.TLabelframe", padding=12)
            card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
            ttk.Label(card, text=category.description, justify="left", wraplength=280).pack(anchor="w")
            ttk.Button(
                card,
                text=f"Open {category.display_name}",
                command=lambda category_id=category.category_id: on_category_selected(category_id),
            ).pack(fill="x", pady=(12, 0))


__all__ = ["ConverterCategoryPage"]
