"""Winding-block estimation for first-pass engineering geometry views."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WindingBlockGeometry:
    """Effective occupied winding region for the selected magnetic design."""

    width_mm: float
    height_mm: float
    depth_mm: float
    notes: list[str] = field(default_factory=list)


def estimate_winding_block(
    *,
    effective_window_width_mm: float,
    effective_window_height_mm: float,
    effective_window_depth_mm: float,
    fill_factor: float | None,
    winding_volume_m3: float | None,
) -> WindingBlockGeometry:
    """Estimate a simple occupied winding block inside the effective window."""
    notes: list[str] = []
    fill = _clamp(fill_factor if fill_factor is not None else 0.35, 0.08, 0.90)
    if fill_factor is None:
        notes.append("Winding occupied area used a default fill-factor proxy because fill factor was unavailable.")

    available_area_mm2 = max(effective_window_width_mm * effective_window_height_mm, 1e-6)
    target_area_mm2 = fill * available_area_mm2
    if winding_volume_m3 is not None and effective_window_depth_mm > 0.0:
        volume_area_mm2 = (winding_volume_m3 * 1e9) / max(effective_window_depth_mm, 1e-6)
        target_area_mm2 = 0.5 * (target_area_mm2 + min(volume_area_mm2, 0.95 * available_area_mm2))
        notes.append("Winding occupied area blended fill-factor and winding-volume estimates.")
    else:
        notes.append("Winding occupied area used a fill-factor-only estimate.")

    aspect_ratio = _clamp(effective_window_width_mm / max(effective_window_height_mm, 1e-6), 0.55, 1.80)
    width_mm = math.sqrt(max(target_area_mm2 * aspect_ratio, 1e-6))
    height_mm = target_area_mm2 / max(width_mm, 1e-6)
    width_mm = min(width_mm, 0.92 * effective_window_width_mm)
    height_mm = min(height_mm, 0.92 * effective_window_height_mm)
    width_mm = max(width_mm, 0.28 * effective_window_width_mm)
    height_mm = max(height_mm, 0.28 * effective_window_height_mm)
    depth_mm = 0.88 * effective_window_depth_mm
    return WindingBlockGeometry(
        width_mm=width_mm,
        height_mm=height_mm,
        depth_mm=depth_mm,
        notes=notes,
    )


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))
