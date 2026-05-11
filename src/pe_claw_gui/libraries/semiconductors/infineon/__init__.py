"""Infineon semiconductor registrations."""

from .coolsic_mosfet_g2_650v import build_infineon_coolsic_mosfet_g2_650v_devices
from .coolsic_mosfet_g2_750v import build_infineon_coolsic_mosfet_g2_750v_devices
from .coolgan_650v import build_infineon_coolgan_650v_devices
from .coolmos_cfd7_650v import build_infineon_coolmos_cfd7_650v_devices
from .coolmos_s7a_600v import build_infineon_coolmos_s7a_600v_devices
from .coolmos8_650v import build_infineon_coolmos8_650v_devices
from .coolmos8_600v import build_infineon_coolmos8_600v_devices


def get_infineon_devices():
    """Return the currently registered Infineon devices."""

    return [
        *build_infineon_coolmos8_600v_devices(),
        *build_infineon_coolmos8_650v_devices(),
        *build_infineon_coolmos_cfd7_650v_devices(),
        *build_infineon_coolmos_s7a_600v_devices(),
        *build_infineon_coolgan_650v_devices(),
        *build_infineon_coolsic_mosfet_g2_650v_devices(),
        *build_infineon_coolsic_mosfet_g2_750v_devices(),
    ]


def build_infineon_devices():
    """Compatibility alias for the previous Infineon registry helper."""

    return get_infineon_devices()


__all__ = [
    "get_infineon_devices",
    "build_infineon_devices",
    "build_infineon_coolsic_mosfet_g2_650v_devices",
    "build_infineon_coolsic_mosfet_g2_750v_devices",
    "build_infineon_coolgan_650v_devices",
    "build_infineon_coolmos_cfd7_650v_devices",
    "build_infineon_coolmos_s7a_600v_devices",
    "build_infineon_coolmos8_650v_devices",
    "build_infineon_coolmos8_600v_devices",
]
