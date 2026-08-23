"""Wheel-safe topology card image resources."""

from __future__ import annotations

from importlib import resources
import tkinter as tk

_ASSET_PACKAGE = "pe_claw_gui.app"
DEFAULT_MAX_IMAGE_WIDTH_PX = 560
DEFAULT_MAX_IMAGE_HEIGHT_PX = 360
_MAX_SCALE_DENOMINATOR = 12

TOPOLOGY_IMAGE_SUBDIRECTORIES: dict[str, str] = {
    "single_phase_diode_bridge_rectifier_capacitor_filter": "ac_dc",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter": "ac_dc",
    "three_phase_diode_bridge_rectifier_capacitor_filter": "ac_dc",
    "single_phase_boost_pfc_diode_bridge": "ac_dc",
    "single_phase_totem_pole_bridgeless_pfc": "ac_dc",
    "single_phase_full_bridge_inverter": "dc_ac",
    "three_phase_two_level_voltage_source_inverter": "dc_ac",
    "three_phase_three_level_npc_inverter": "dc_ac",
    "buck_diode_rectified_unidirectional": "dc_dc",
    "buck_synchronous_rectified_unidirectional": "dc_dc",
    "buck_boost_diode_rectified_unidirectional": "dc_dc",
    "four_switch_buck_boost_simplified_four_mode": "dc_dc",
    "three_level_tzcm_fixed_frequency": "dc_dc",
    "boost_diode_rectified_unidirectional": "dc_dc",
    "boost_synchronous_rectified_unidirectional": "dc_dc",
    "llc_resonant_converter_diode_rectifier": "dc_dc",
    "llc_resonant_converter_synchronous_rectifier": "dc_dc",
    "flyback_diode_rectified_isolated": "dc_dc",
    "phase_shifted_full_bridge_diode_rectifier_isolated": "dc_dc",
}

TOPOLOGY_IMAGE_FILENAMES: dict[str, str] = {
    "single_phase_diode_bridge_rectifier_capacitor_filter": "single_phase_diode_bridge_rectifier_capacitor_filter.png",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter": "single_phase_diode_bridge_rectifier_dc_inductor_filter.png",
    "three_phase_diode_bridge_rectifier_capacitor_filter": "three_phase_diode_bridge_rectifier_capacitor_filter.png",
    "single_phase_boost_pfc_diode_bridge": "single_phase_boost_pfc_diode_bridge.png",
    "single_phase_totem_pole_bridgeless_pfc": "single_phase_totem_pole_bridgeless_pfc.png",
    "single_phase_full_bridge_inverter": "single_phase_full_bridge_inverter.png",
    "three_phase_two_level_voltage_source_inverter": "three_phase_two_level_voltage_source_inverter.png",
    "three_phase_three_level_npc_inverter": "three_phase_three_level_npc_inverter.png",
    "buck_diode_rectified_unidirectional": "buck_diode_rectified_unidirectional.png",
    "buck_synchronous_rectified_unidirectional": "buck_synchronous_rectified_unidirectional.png",
    "buck_boost_diode_rectified_unidirectional": "buck_boost_diode_rectified_unidirectional.png",
    "four_switch_buck_boost_simplified_four_mode": "four_switch_buck_boost_simplified_four_mode.png",
    "three_level_tzcm_fixed_frequency": "three_level_tzcm_fixed_frequency.png",
    "boost_diode_rectified_unidirectional": "boost_diode_rectified_unidirectional.png",
    "boost_synchronous_rectified_unidirectional": "boost_synchronous_rectified_unidirectional.png",
    "llc_resonant_converter_diode_rectifier": "llc_resonant_converter_diode_rectifier.png",
    "llc_resonant_converter_synchronous_rectifier": "llc_resonant_converter_synchronous_rectifier.png",
    "flyback_diode_rectified_isolated": "flyback_diode_rectified_isolated.png",
    "phase_shifted_full_bridge_diode_rectifier_isolated": "phase_shifted_full_bridge_diode_rectifier_isolated.png",
}


def topology_image_filename(topology_id: str) -> str:
    """Return the packaged PNG filename for a topology id."""

    return TOPOLOGY_IMAGE_FILENAMES.get(topology_id, f"{topology_id}.png")


def get_topology_image_resource(topology_id: str):
    """Return the package resource for a topology image."""

    subdirectory = TOPOLOGY_IMAGE_SUBDIRECTORIES.get(topology_id, "dc_dc")
    return resources.files(_ASSET_PACKAGE).joinpath(
        "assets",
        "topologies",
        subdirectory,
        topology_image_filename(topology_id),
    )


def load_topology_image(
    topology_id: str,
    master: tk.Misc | None = None,
    *,
    max_width_px: int = DEFAULT_MAX_IMAGE_WIDTH_PX,
    max_height_px: int = DEFAULT_MAX_IMAGE_HEIGHT_PX,
) -> tk.PhotoImage | None:
    """Load a Tk PNG image for a topology card, returning None on fallback paths."""

    resource = get_topology_image_resource(topology_id)
    try:
        if not resource.is_file():
            return None
        with resources.as_file(resource) as path:
            image = tk.PhotoImage(master=master, file=str(path))
        return _resize_if_needed(image, max_width_px=max_width_px, max_height_px=max_height_px)
    except (OSError, RuntimeError, tk.TclError):
        return None


def _resize_if_needed(image: tk.PhotoImage, *, max_width_px: int, max_height_px: int) -> tk.PhotoImage:
    width = max(image.width(), 1)
    height = max(image.height(), 1)
    max_width_px = max(max_width_px, 1)
    max_height_px = max(max_height_px, 1)
    if width <= max_width_px and height <= max_height_px:
        return image

    scale = min(max_width_px / width, max_height_px / height)
    numerator, denominator = _largest_rational_at_or_below(scale)
    if numerator == denominator:
        return image
    return image.zoom(numerator, numerator).subsample(denominator, denominator)


def _largest_rational_at_or_below(scale: float) -> tuple[int, int]:
    best = (1, 1)
    best_value = 0.0
    for denominator in range(1, _MAX_SCALE_DENOMINATOR + 1):
        numerator = int(scale * denominator)
        if numerator <= 0:
            continue
        value = numerator / denominator
        if value <= scale and value > best_value:
            best = (numerator, denominator)
            best_value = value
    return best


__all__ = [
    "DEFAULT_MAX_IMAGE_HEIGHT_PX",
    "DEFAULT_MAX_IMAGE_WIDTH_PX",
    "TOPOLOGY_IMAGE_FILENAMES",
    "TOPOLOGY_IMAGE_SUBDIRECTORIES",
    "get_topology_image_resource",
    "load_topology_image",
    "topology_image_filename",
]
