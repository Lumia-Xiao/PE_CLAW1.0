"""DC-AC topology selection page."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...topologies.base import TopologyRegistry
from ..topology_card_assets import DEFAULT_MAX_IMAGE_HEIGHT_PX, DEFAULT_MAX_IMAGE_WIDTH_PX, load_topology_image

_CARD_COLUMNS = 2
_TOPOLOGY_HINTS = {
    "single_phase_full_bridge_inverter": (
        "Single-phase full-bridge voltage-source inverter. First-pass CCM unipolar-SPWM output "
        "inductor sizing and DC-link energy-balance capacitor sizing."
    ),
    "three_phase_two_level_voltage_source_inverter": (
        "Three-phase two-level voltage-source inverter with CCM fixed-frequency SPWM synthesis, "
        "phase-voltage/current waveforms, SxP DC-link capacitor bank selection, per-phase "
        "output-inductor magnetics, first-pass loss, efficiency load/PF diagnostics, and Hardware Overview."
    ),
    "three_phase_three_level_npc_inverter": (
        "Three-phase three-level NPC inverter with first-pass CCM PD level-shifted SPWM synthesis, "
        "split upper/lower DC-link capacitor banks, 3x per-phase output-inductor magnetics, "
        "NPC outer/inner switch and clamp-diode loss, fixed-hardware efficiency load/PF diagnostics, "
        "and Hardware Overview."
    ),
}


class DCACCategoryPage(ttk.Frame):
    """List registered DC-AC topologies."""

    def __init__(self, parent, registry: TopologyRegistry, on_topology_selected, on_back) -> None:
        super().__init__(parent, padding=24)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._topology_images: list[tk.PhotoImage] = []
        self._topology_buttons: dict[str, ttk.Button] = {}
        self._topology_cards: dict[str, ttk.Frame] = {}

        ttk.Label(self, text="DC-AC Topologies", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(
            self,
            text="Select a DC-AC topology to review its implementation boundary.",
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        definitions = registry.list_topologies("dc_ac")
        if definitions:
            list_frame = self._build_scrollable_list()
            for index, definition in enumerate(definitions):
                self._add_topology_card(
                    list_frame,
                    index // _CARD_COLUMNS,
                    index % _CARD_COLUMNS,
                    definition.topology_id,
                    definition.display_name,
                    on_topology_selected,
                    definition.implemented,
                )
        else:
            ttk.Label(
                self,
                text="No DC-AC topology is registered yet.",
                justify="left",
            ).grid(row=2, column=0, sticky="w")

        ttk.Button(self, text="Back to Categories", command=on_back).grid(row=3, column=0, sticky="w", pady=(16, 0))

    def _build_scrollable_list(self) -> ttk.Frame:
        host = ttk.LabelFrame(self, text="Available Topologies", style="Section.TLabelframe", padding=12)
        host.grid(row=2, column=0, sticky="nsew")
        host.columnconfigure(0, weight=1)
        host.rowconfigure(0, weight=1)

        canvas = tk.Canvas(host, borderwidth=0, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        list_frame = ttk.Frame(canvas)
        for column in range(_CARD_COLUMNS):
            list_frame.columnconfigure(column, weight=1, uniform="topology_cards")
        window_id = canvas.create_window((0, 0), window=list_frame, anchor="nw")
        list_frame.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        return list_frame

    def _add_topology_card(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        topology_id: str,
        display_name: str,
        on_topology_selected,
        implemented: bool,
    ) -> None:
        card = ttk.Frame(parent, padding=12, borderwidth=1, relief="solid")
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
        self._topology_cards[topology_id] = card

        command = lambda selected_id=topology_id: on_topology_selected(selected_id)
        image = load_topology_image(
            topology_id,
            master=self,
            max_width_px=DEFAULT_MAX_IMAGE_WIDTH_PX,
            max_height_px=DEFAULT_MAX_IMAGE_HEIGHT_PX,
        )
        if image is None:
            image_label = ttk.Label(card, text="[Topology image unavailable]", anchor="center", justify="center", width=42)
        else:
            self._topology_images.append(image)
            image_label = ttk.Label(card, image=image, anchor="center")
        image_label.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        content = ttk.Frame(card)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        name_label = ttk.Label(content, text=display_name, style="Subheader.TLabel", justify="left", anchor="w")
        name_label.grid(row=0, column=0, sticky="ew")
        hint_label = ttk.Label(content, text=_TOPOLOGY_HINTS[topology_id], justify="left", anchor="w", wraplength=220)
        hint_label.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        status_text = "First-pass implemented" if implemented else "Registered placeholder"
        status_label = ttk.Label(content, text=status_text, justify="left", anchor="w")
        status_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        button_text = "Open" if implemented else "Review Status"
        button = ttk.Button(content, text=button_text, command=command, width=14)
        button.grid(row=3, column=0, sticky="w", pady=(12, 0))
        self._topology_buttons[topology_id] = button

        for widget in (card, image_label, content, name_label, hint_label, status_label):
            widget.bind("<Button-1>", lambda _event, action=command: action())


__all__ = ["DCACCategoryPage"]
