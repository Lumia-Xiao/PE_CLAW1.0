"""DC-AC category placeholder page."""

from __future__ import annotations

from tkinter import ttk


class DCACCategoryPage(ttk.Frame):
    """Safe placeholder for future DC-AC topology selection."""

    def __init__(self, parent, on_back) -> None:
        super().__init__(parent, padding=24)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="DC-AC Topologies", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(
            self,
            text="No DC-AC topologies are connected yet. This category is reserved for future implementations.",
            justify="left",
            wraplength=520,
        ).grid(row=1, column=0, sticky="w")
        ttk.Button(self, text="Back to Categories", command=on_back).grid(row=2, column=0, sticky="w", pady=(16, 0))


__all__ = ["DCACCategoryPage"]
