"""First-pass thermal-resistance estimates for magnetic components."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .thermal_proxies import MagneticThermalGeometryProxy

_CM2_PER_M2 = 1.0e4
_CM3_PER_M3 = 1.0e6
_MIN_AREA_CM2 = 0.10
_MIN_VOLUME_CM3 = 0.01
_WINDING_RESISTANCE_FACTOR = 1.15


@dataclass(frozen=True)
class ThermalResistanceEstimate:
    """Separated first-pass thermal resistances for core and winding."""

    rth_core_to_ambient_k_per_w: float | None
    rth_winding_to_ambient_k_per_w: float | None
    total_temp_rise_maniktala_c: float | None
    notes: list[str] = field(default_factory=list)


def estimate_thermal_resistances(
    *,
    core_loss_w: float,
    copper_loss_w: float,
    geometry: MagneticThermalGeometryProxy,
) -> ThermalResistanceEstimate:
    """Estimate simplified magnetic thermal resistances using MKF-inspired laws."""
    notes = list(geometry.notes)

    core_surface_cm2 = _to_cm2(geometry.core_surface_area_proxy_m2)
    winding_surface_cm2 = _to_cm2(geometry.winding_surface_area_proxy_m2)
    total_surface_cm2 = _to_cm2(geometry.total_surface_area_proxy_m2)
    core_volume_cm3 = _to_cm3(geometry.core_volume_m3)
    winding_volume_cm3 = _to_cm3(geometry.winding_volume_m3)
    total_loss_w = max(core_loss_w, 0.0) + max(copper_loss_w, 0.0)

    if core_surface_cm2 is None or winding_surface_cm2 is None or total_surface_cm2 is None:
        return ThermalResistanceEstimate(
            rth_core_to_ambient_k_per_w=None,
            rth_winding_to_ambient_k_per_w=None,
            total_temp_rise_maniktala_c=None,
            notes=["Thermal surface proxies were unavailable; resistance estimation could not proceed.", *notes],
        )

    # MKF references two lightweight empirical forms worth reusing here:
    # 1. Maniktala-style core thermal resistance scaling with size.
    # 2. Dixon-style thermal resistance scaling with effective cooling area.
    # We blend them so the first-pass PE-Claw model remains size-aware even when
    # only partial geometry is available, while still reacting to better area data.
    core_rth_size = 53.0 * max(core_volume_cm3 or _MIN_VOLUME_CM3, _MIN_VOLUME_CM3) ** -0.54
    core_rth_area = 50.0 / max(core_surface_cm2, _MIN_AREA_CM2) ** 0.70
    winding_rth_size = 53.0 * max(winding_volume_cm3 or _MIN_VOLUME_CM3, _MIN_VOLUME_CM3) ** -0.54
    winding_rth_area = 50.0 / max(winding_surface_cm2, _MIN_AREA_CM2) ** 0.70

    rth_core = math.sqrt(core_rth_size * core_rth_area)
    rth_winding = _WINDING_RESISTANCE_FACTOR * math.sqrt(winding_rth_size * winding_rth_area)

    total_temp_rise_maniktala_c = None
    if total_loss_w > 0.0:
        total_temp_rise_maniktala_c = (total_loss_w / max(total_surface_cm2, _MIN_AREA_CM2)) ** 0.833
        notes.append(
            "Hotspot proxy cross-check includes a Maniktala-style total-rise estimate based on total loss divided by total surface proxy."
        )

    notes.append(
        "Core/winding thermal resistances blend a size-based Maniktala scaling with a surface-based Dixon scaling."
    )
    notes.append(
        "Winding thermal resistance is biased 15% higher than the core path to reflect insulation and poorer local convection."
    )

    return ThermalResistanceEstimate(
        rth_core_to_ambient_k_per_w=rth_core,
        rth_winding_to_ambient_k_per_w=rth_winding,
        total_temp_rise_maniktala_c=total_temp_rise_maniktala_c,
        notes=notes,
    )


def _to_cm2(area_m2: float | None) -> float | None:
    if area_m2 is None:
        return None
    return float(area_m2) * _CM2_PER_M2


def _to_cm3(volume_m3: float | None) -> float | None:
    if volume_m3 is None:
        return None
    return float(volume_m3) * _CM3_PER_M3
