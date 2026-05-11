"""Navitas semiconductor registrations."""

from .gen3f_sic_mosfet import build_navitas_gen3f_sic_mosfet_devices


def get_navitas_devices():
    """Return the currently registered Navitas devices."""

    return [
        *build_navitas_gen3f_sic_mosfet_devices(),
    ]


def build_navitas_devices():
    """Compatibility alias for vendor-level device composition."""

    return get_navitas_devices()


__all__ = [
    "build_navitas_devices",
    "build_navitas_gen3f_sic_mosfet_devices",
    "get_navitas_devices",
]
