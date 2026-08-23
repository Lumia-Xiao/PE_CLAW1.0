"""Wolfspeed semiconductor registrations."""

from .diodes import build_wolfspeed_diode_devices
from .legacy_mosfets import build_wolfspeed_legacy_mosfet_devices
from .mosfet_with_diode import build_wolfspeed_mosfet_with_diode_devices
from .modules import build_wolfspeed_module_devices


def get_wolfspeed_devices():
    """Return the currently registered Wolfspeed devices."""

    return [
        *build_wolfspeed_mosfet_with_diode_devices(),
        *build_wolfspeed_legacy_mosfet_devices(),
        *build_wolfspeed_module_devices(),
        *build_wolfspeed_diode_devices(),
    ]


def build_wolfspeed_devices():
    """Compatibility alias for vendor-level device composition."""

    return get_wolfspeed_devices()


__all__ = [
    "build_wolfspeed_devices",
    "build_wolfspeed_diode_devices",
    "build_wolfspeed_legacy_mosfet_devices",
    "build_wolfspeed_mosfet_with_diode_devices",
    "build_wolfspeed_module_devices",
    "get_wolfspeed_devices",
]
