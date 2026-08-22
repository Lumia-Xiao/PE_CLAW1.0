"""AC-DC low-frequency reactor design models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AcDcReactorDesignRequest:
    """Normalized request for an AC-DC DC-link reactor selection stage."""

    topology_id: str
    display_name: str
    required_inductance_h: float
    f_line_hz: float
    ripple_frequency_hz: float
    idc_a: float
    i_rms_a: float
    i_peak_a: float
    i_valley_a: float
    delta_i_pp_a: float
    vdc_est_v: float
    throughput_power_w: float
    current_basis: str = ""
    material_family: str = "sendust"
    core_shape: str = "toroid"
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcDcReactorCandidate:
    """One first-pass low-frequency AC-DC reactor candidate."""

    candidate_id: str = ""
    core_part_number: str = ""
    material_id: str = ""
    material_name: str = ""
    relative_permeability: float = 0.0
    parallel_core_count: int = 1
    per_core_turns: int = 0
    turns: int = 0
    per_core_inductance_h: float = 0.0
    per_core_effective_inductance_h: float = 0.0
    inductance_h: float = 0.0
    effective_inductance_h: float = 0.0
    al_dc_derating_factor: float = 1.0
    od_mm: float = 0.0
    id_mm: float = 0.0
    ht_mm: float = 0.0
    ae_cm2: float = 0.0
    le_cm: float = 0.0
    ve_cm3: float = 0.0
    mean_length_per_turn_m: float = 0.0
    window_area_mm2: float = 0.0
    fill_factor: float | None = None
    copper_area_mm2: float | None = None
    equivalent_wire_diameter_mm: float | None = None
    current_density_a_per_mm2: float | None = None
    rdc_25c_ohm: float | None = None
    b_dc_t: float | None = None
    delta_b_t: float | None = None
    b_peak_t: float | None = None
    core_loss_w: float | None = None
    copper_loss_w: float | None = None
    total_loss_w: float | None = None
    estimated_volume_cm3: float | None = None
    score: float | None = None
    rejection_reason: str = ""
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcDcReactorSelectionSettings:
    """First-pass AC-DC low-frequency reactor selection limits."""

    al_dc_derating_factor: float = 0.6
    target_current_density_a_per_mm2: float = 4.0
    target_window_utilization: float = 0.30
    max_fill_factor: float = 0.40
    max_b_peak_t: float = 0.70
    max_delta_b_t: float = 0.25
    max_turns: int = 5000
    max_parallel_core_count: int = 4
    winding_pack_factor: float = 1.25
    copper_temperature_factor: float = 1.25
    top_candidate_count: int = 10
    loss_warning_power_ratio: float = 0.05


@dataclass(frozen=True)
class AcDcReactorSelectionResult:
    """Auditable result of the AC-DC low-frequency reactor selector."""

    request: AcDcReactorDesignRequest
    settings: AcDcReactorSelectionSettings = field(default_factory=AcDcReactorSelectionSettings)
    selected_candidate: AcDcReactorCandidate | None = None
    top_candidates: list[AcDcReactorCandidate] = field(default_factory=list)
    feasible_candidates: list[AcDcReactorCandidate] = field(default_factory=list)
    rejected_candidates: list[AcDcReactorCandidate] = field(default_factory=list)
    evaluated_count: int = 0
    feasible_count: int = 0
    rejection_counts: dict[str, int] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)
    feasible_csv_path: str = ""
    top_candidates_csv_path: str = ""
    rejected_csv_path: str = ""
    selected_loss_power_ratio: float | None = None
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
