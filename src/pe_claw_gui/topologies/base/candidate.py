"""Runtime topology candidate model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TopologyCandidate:
    """Synthesized topology candidate for the currently selected plugin."""

    topology_id: str
    display_name: str
    vin_min: float
    vin_max: float
    vin_nom: float
    vout_target: float
    pout_target: float
    duty_nom: float
    iout: float
    fs_hz: float
    inductance_h: float
    capacitance_f: float
    delta_il: float
    delta_vo: float
    il_peak: float
    il_valley: float
    ccm_valid: bool
    mode_capable: str = "unknown"
    control_duty_1: float | None = None
    control_duty_4: float | None = None
    current_ip_minus_a: float | None = None
    current_i1_a: float | None = None
    current_i2_a: float | None = None
    output_ripple_vpp_v: float | None = None
    feasible: bool = True
    failure_reason: str | None = None
    r_load_nom_ohm: float = 0.0
    r_crit_nom_ohm: float = 0.0
    boundary_load_ratio: float = 0.0
    i_boundary_nom_a: float = 0.0
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
