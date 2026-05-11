"""Inductor design and operating-evaluation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FixedInductorDesignCandidate:
    """One fixed inductor design selected from the magnetic search space."""

    candidate_id: str = ""
    assembly_type: str | None = "single_core"
    stack_count: int = 1
    base_core_name: str | None = None
    core_name: str = ""
    material_name: str = ""
    wire_name: str = ""
    turns: int = 0
    parallel_bundles: int = 1
    gap_m: float | None = None
    inductance_h: float = 0.0
    rdc_25c_ohm: float | None = None
    fill_factor: float | None = None
    core_volume_m3: float | None = None
    winding_volume_m3: float | None = None
    total_volume_m3: float | None = None
    b_peak_design_t: float | None = None
    saturation_current_a: float | None = None
    reference_copper_loss_w: float | None = None
    reference_core_loss_w: float | None = None
    reference_total_loss_w: float | None = None
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InductorOperatingEvaluation:
    """One operating-point evaluation of a fixed inductor design."""

    design_id: str = ""
    operating_vin_v: float | None = None
    operating_iout_a: float | None = None
    fs_hz: float | None = None
    i_rms_a: float | None = None
    i_peak_a: float | None = None
    delta_il_pp_a: float | None = None
    copper_loss_w: float | None = None
    core_loss_w: float | None = None
    total_loss_w: float | None = None
    b_peak_t: float | None = None
    current_density_a_per_mm2: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class InductorDesignRequest:
    """Normalized inductor design request derived from a synthesized candidate."""

    topology_id: str
    display_name: str
    inductance_h: float
    fs_hz: float
    i_avg_a: float
    i_rms_a: float
    i_peak_a: float
    i_valley_a: float
    delta_i_pp_a: float
    throughput_power_w: float
    mode: str
    vin_nom_v: float | None
    vout_nom_v: float | None
    duty_nom: float
    v_l_on_v: float
    v_l_off_v: float
    ccm_valid: bool | None
    mode_capable: str | None
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def target_inductance_h(self) -> float:
        return self.inductance_h

    @property
    def delta_il_pp_a(self) -> float:
        return self.delta_i_pp_a

    @property
    def pout_nom_w(self) -> float:
        return self.throughput_power_w


@dataclass(frozen=True)
class InductorOperatingPointRequest:
    """Normalized operating-point request for fixed-design evaluation."""

    topology_id: str
    display_name: str
    fs_hz: float
    operating_vin_v: float
    operating_vout_v: float
    operating_iout_a: float
    throughput_power_w: float
    duty: float
    i_avg_a: float
    i_rms_a: float
    i_peak_a: float
    i_valley_a: float
    delta_i_pp_a: float
    v_l_on_v: float
    v_l_off_v: float
    mode: str
    load_ratio: float
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def operating_pout_w(self) -> float:
        return self.throughput_power_w

    @property
    def delta_il_pp_a(self) -> float:
        return self.delta_i_pp_a
