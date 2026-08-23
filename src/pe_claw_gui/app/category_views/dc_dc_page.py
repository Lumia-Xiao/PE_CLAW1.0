"""DC-DC topology selection page."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...topologies.base import TopologyRegistry
from ..topology_card_assets import DEFAULT_MAX_IMAGE_HEIGHT_PX, DEFAULT_MAX_IMAGE_WIDTH_PX, load_topology_image

_CARD_COLUMNS = 2
_TOPOLOGY_HINTS = {
    "buck_diode_rectified_unidirectional": "Non-isolated step-down with diode rectification.",
    "buck_synchronous_rectified_unidirectional": "Non-isolated step-down with synchronous rectification.",
    "buck_boost_diode_rectified_unidirectional": "Non-isolated inverting buck-boost conversion.",
    "four_switch_buck_boost_simplified_four_mode": "Non-isolated step-up/down four-switch structure.",
    "three_level_tzcm_fixed_frequency": "Three-level fixed-frequency DC-DC topology.",
    "boost_diode_rectified_unidirectional": "Non-isolated step-up with diode rectification.",
    "boost_synchronous_rectified_unidirectional": "Non-isolated step-up with synchronous rectification.",
    "llc_resonant_converter_diode_rectifier": (
        "Implemented FHA-based isolated LLC workflow with first-pass transformer, external resonant inductor, "
        "resonant capacitor, waveform, loss, and artifact views."
    ),
    "llc_resonant_converter_synchronous_rectifier": (
        "First-pass isolated LLC workflow with full-bridge synchronous rectifier; FHA tank, "
        "transformer/capacitor reuse, primary switch and secondary SR MOSFET selection, "
        "SR timing/loss readback, report, and audit are wired with SR first-pass limitations."
    ),
    "flyback_diode_rectified_isolated": (
        "First-pass isolated diode-rectified Flyback sizing for duty, turns ratio, Lm, current, and stress; "
        "primary/secondary semiconductor selection, coupled-inductor search, capacitor selection, loss, and "
        "report/audit readback are wired with first-pass Flyback limitations."
    ),
    "phase_shifted_full_bridge_diode_rectifier_isolated": (
        "First-pass isolated phase-shifted full bridge with secondary diode rectifier; duty-loss, ZVS/deadtime, "
        "device selection, transformer/output-inductor search, capacitor, loss, thermal, geometry, and report "
        "readback are wired with PSFB first-pass limitations."
    ),
}


class DCDCCategoryPage(ttk.Frame):
    """List registered DC-DC topologies for the selected category."""

    def __init__(self, parent, registry: TopologyRegistry, on_topology_selected, on_back) -> None:
        super().__init__(parent, padding=24)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._topology_images: list[tk.PhotoImage] = []
        self._topology_buttons: dict[str, ttk.Button] = {}
        self._topology_cards: dict[str, ttk.Frame] = {}
        self._topology_card_positions: dict[str, tuple[int, int]] = {}
        self._topology_image_labels: dict[str, ttk.Label] = {}
        self._topology_content_frames: dict[str, ttk.Frame] = {}

        ttk.Label(self, text="DC-DC Topologies", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(
            self,
            text="Select a DC-DC circuit topology to open its input form.",
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        definitions = registry.list_topologies("dc_dc")
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
                )
        else:
            ttk.Label(
                self,
                text="No DC-DC topologies are registered yet.",
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
    ) -> None:
        card = ttk.Frame(parent, padding=12, borderwidth=1, relief="solid")
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        card.columnconfigure(0, weight=0)
        card.columnconfigure(1, weight=1)
        card.rowconfigure(0, weight=1)
        self._topology_cards[topology_id] = card
        self._topology_card_positions[topology_id] = (row, column)

        command = lambda selected_id=topology_id: on_topology_selected(selected_id)
        image_frame = ttk.Frame(card)
        image_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        image = load_topology_image(
            topology_id,
            master=self,
            max_width_px=DEFAULT_MAX_IMAGE_WIDTH_PX,
            max_height_px=DEFAULT_MAX_IMAGE_HEIGHT_PX,
        )
        if image is None:
            image_label = ttk.Label(
                image_frame,
                text="[Topology image unavailable]",
                anchor="center",
                justify="center",
                width=42,
            )
        else:
            self._topology_images.append(image)
            image_label = ttk.Label(image_frame, image=image, anchor="center")
        image_label.grid(row=0, column=0, sticky="nsew")
        self._topology_image_labels[topology_id] = image_label

        content = ttk.Frame(card)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        self._topology_content_frames[topology_id] = content

        name_label = ttk.Label(content, text=display_name, style="Subheader.TLabel", justify="left", anchor="w")
        name_label.grid(row=0, column=0, sticky="ew")
        hint_label = ttk.Label(
            content,
            text=_TOPOLOGY_HINTS.get(topology_id, topology_id),
            justify="left",
            anchor="w",
            wraplength=220,
        )
        hint_label.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        button = ttk.Button(content, text="Open", command=command, width=12)
        button.grid(row=2, column=0, sticky="w", pady=(16, 0))
        self._topology_buttons[topology_id] = button

        for widget in (card, image_frame, image_label, content, name_label, hint_label):
            widget.bind("<Button-1>", lambda _event, action=command: action())


__all__ = ["DCDCCategoryPage"]
