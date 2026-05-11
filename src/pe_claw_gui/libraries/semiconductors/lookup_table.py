"""Small bounded lookup-table helpers for XML-derived device models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import RegularGridInterpolator


def _clamp_value(axis_name: str, value: float, axis_values: np.ndarray, warnings: list[str] | None, table_name: str) -> float:
    lower = float(axis_values[0])
    upper = float(axis_values[-1])
    if value < lower:
        if warnings is not None:
            warnings.append(f"{table_name}: clamped {axis_name} from {value:.6g} to {lower:.6g}.")
        return lower
    if value > upper:
        if warnings is not None:
            warnings.append(f"{table_name}: clamped {axis_name} from {value:.6g} to {upper:.6g}.")
        return upper
    return value


@dataclass(frozen=True)
class LookupTable2D:
    """Bounded 2D linear interpolation table."""

    name: str
    x_name: str
    y_name: str
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    values: tuple[tuple[float, ...], ...]
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "_x_array", np.asarray(self.x_values, dtype=float))
        object.__setattr__(self, "_y_array", np.asarray(self.y_values, dtype=float))
        object.__setattr__(self, "_value_array", np.asarray(self.values, dtype=float))
        interpolator = RegularGridInterpolator(
            (self._x_array, self._y_array),
            self._value_array,
            bounds_error=False,
            fill_value=None,
        )
        object.__setattr__(self, "_interpolator", interpolator)

    def evaluate(self, x_value: float, y_value: float, warnings: list[str] | None = None) -> float:
        clamped_x = _clamp_value(self.x_name, x_value, self._x_array, warnings, self.name)
        clamped_y = _clamp_value(self.y_name, y_value, self._y_array, warnings, self.name)
        return float(self._interpolator([[clamped_x, clamped_y]])[0])


@dataclass(frozen=True)
class LookupTable3D:
    """Bounded 3D linear interpolation table."""

    name: str
    x_name: str
    y_name: str
    z_name: str
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    z_values: tuple[float, ...]
    values: tuple[tuple[tuple[float, ...], ...], ...]
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "_x_array", np.asarray(self.x_values, dtype=float))
        object.__setattr__(self, "_y_array", np.asarray(self.y_values, dtype=float))
        object.__setattr__(self, "_z_array", np.asarray(self.z_values, dtype=float))
        object.__setattr__(self, "_value_array", np.asarray(self.values, dtype=float))
        interpolator = RegularGridInterpolator(
            (self._x_array, self._y_array, self._z_array),
            self._value_array,
            bounds_error=False,
            fill_value=None,
        )
        object.__setattr__(self, "_interpolator", interpolator)

    def evaluate(
        self,
        x_value: float,
        y_value: float,
        z_value: float,
        warnings: list[str] | None = None,
    ) -> float:
        clamped_x = _clamp_value(self.x_name, x_value, self._x_array, warnings, self.name)
        clamped_y = _clamp_value(self.y_name, y_value, self._y_array, warnings, self.name)
        clamped_z = _clamp_value(self.z_name, z_value, self._z_array, warnings, self.name)
        return float(self._interpolator([[clamped_x, clamped_y, clamped_z]])[0])
