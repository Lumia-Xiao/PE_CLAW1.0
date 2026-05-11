"""Lumped temperature-rise solver for magnetic thermal estimates."""

from __future__ import annotations

import math

from ...models.thermal_result import ThermalEstimate
from .resistance_chain import ThermalResistanceEstimate
from .thermal_proxies import MagneticThermalGeometryProxy

_CROSS_COUPLING_FACTOR = 0.15


def solve_lumped_magnetic_temperatures(
    *,
    ambient_temp_c: float,
    core_loss_w: float,
    copper_loss_w: float,
    geometry: MagneticThermalGeometryProxy,
    resistance_estimate: ThermalResistanceEstimate,
) -> ThermalEstimate:
    """Solve a first-pass separated core/winding temperature estimate."""
    notes = [*geometry.notes, *resistance_estimate.notes]
    rth_core = resistance_estimate.rth_core_to_ambient_k_per_w
    rth_winding = resistance_estimate.rth_winding_to_ambient_k_per_w
    total_loss_w = max(core_loss_w, 0.0) + max(copper_loss_w, 0.0)

    if rth_core is None or rth_winding is None:
        notes.append("Thermal resistances were unavailable; no temperature estimate was produced.")
        return ThermalEstimate(
            ambient_temp_c=ambient_temp_c,
            core_loss_w=core_loss_w,
            copper_loss_w=copper_loss_w,
            total_loss_w=total_loss_w,
            total_surface_area_proxy_m2=geometry.total_surface_area_proxy_m2,
            core_surface_area_proxy_m2=geometry.core_surface_area_proxy_m2,
            winding_surface_area_proxy_m2=geometry.winding_surface_area_proxy_m2,
            notes=notes,
        )

    shared_rth = math.sqrt(rth_core * rth_winding)
    shared_rise_c = _CROSS_COUPLING_FACTOR * total_loss_w * shared_rth
    core_rise_c = core_loss_w * rth_core + shared_rise_c
    winding_rise_c = copper_loss_w * rth_winding + shared_rise_c
    hotspot_proxy_c = ambient_temp_c + max(
        core_rise_c,
        winding_rise_c,
        resistance_estimate.total_temp_rise_maniktala_c or 0.0,
    )

    notes.append(
        "Temperature rise uses a lumped thermal-electrical analogy: ΔT = P × Rth with a 15% shared-heating cross-coupling proxy."
    )
    notes.append(
        "Detailed winding anisotropy, interface contact resistance, and explicit radiation/forced-air modeling are not included in this first pass."
    )

    return ThermalEstimate(
        ambient_temp_c=ambient_temp_c,
        core_loss_w=core_loss_w,
        copper_loss_w=copper_loss_w,
        total_loss_w=total_loss_w,
        estimated_core_temp_rise_c=core_rise_c,
        estimated_winding_temp_rise_c=winding_rise_c,
        estimated_core_temp_c=ambient_temp_c + core_rise_c,
        estimated_winding_temp_c=ambient_temp_c + winding_rise_c,
        hotspot_proxy_temp_c=hotspot_proxy_c,
        total_temp_rise_maniktala_c=resistance_estimate.total_temp_rise_maniktala_c,
        rth_core_to_ambient_k_per_w=rth_core,
        rth_winding_to_ambient_k_per_w=rth_winding,
        total_surface_area_proxy_m2=geometry.total_surface_area_proxy_m2,
        core_surface_area_proxy_m2=geometry.core_surface_area_proxy_m2,
        winding_surface_area_proxy_m2=geometry.winding_surface_area_proxy_m2,
        notes=notes,
    )
