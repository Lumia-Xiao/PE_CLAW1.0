"""Operating-point model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperatingPoint:
    """One evaluated operating point for waveform and stress generation."""

    vin_v: float
    load_ratio: float = 1.0
    vout_v: float | None = None
    power_factor: float | None = None
    switching_frequency_hz: float | None = None
