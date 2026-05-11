"""Thermal engine helpers."""

from .resistance_chain import ThermalResistanceEstimate, estimate_thermal_resistances
from .temperature_solver import solve_lumped_magnetic_temperatures
from .thermal_estimator import (
    DEFAULT_AMBIENT_TEMP_C,
    MagneticLossSnapshot,
    estimate_design_thermal_entry,
    export_thermal_summary,
    resolve_ambient_temperature_c,
    resolve_loss_snapshot,
)
from .thermal_proxies import MagneticThermalGeometryProxy, build_geometry_proxy

__all__ = [
    "DEFAULT_AMBIENT_TEMP_C",
    "MagneticLossSnapshot",
    "MagneticThermalGeometryProxy",
    "ThermalResistanceEstimate",
    "build_geometry_proxy",
    "estimate_design_thermal_entry",
    "estimate_thermal_resistances",
    "export_thermal_summary",
    "resolve_ambient_temperature_c",
    "resolve_loss_snapshot",
    "solve_lumped_magnetic_temperatures",
]
