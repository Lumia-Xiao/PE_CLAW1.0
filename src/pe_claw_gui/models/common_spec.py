"""Shared topology specification models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CommonSpec:
    """Normalized topology inputs shared across the runtime pipeline."""

    topology_id: str
    display_name: str
    vin_min: float
    vin_max: float
    vout: float
    pout: float
    fs_khz: float
    ripple_current_ratio: float
    ripple_voltage_ratio_percent: float
    raw_input: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def archetype_key(self) -> str:
        """Compatibility alias for legacy Buck code."""
        return self.metadata.get("legacy_key", self.topology_id)
