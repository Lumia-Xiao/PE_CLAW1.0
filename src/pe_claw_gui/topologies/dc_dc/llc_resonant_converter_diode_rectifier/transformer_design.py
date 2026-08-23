"""First-pass separated transformer calculations for the diode LLC topology."""

from __future__ import annotations

import csv
import re
from collections import Counter
from statistics import median
from dataclasses import dataclass, field
from pathlib import Path
from math import ceil, pi, sqrt
from typing import Any, Callable, Iterable, Mapping

from ....engines.magnetics.leakage import (
    DEFAULT_WINDING_ARRANGEMENT,
    estimate_layer_based_leakage_inductance,
    estimate_legacy_leakage_inductance,
)
from ....models.magnetic_result import (
    LlcExternalResonantInductorCandidate,
    LlcExternalResonantInductorRepresentativeSelection,
    LlcExternalResonantInductorSearchResult,
    LlcExternalResonantInductorTarget,
)
from ....engines.magnetics.core_loss_role_adapter import evaluate_candidate_core_loss
from ....engines.magnetics.winding_evidence import build_winding_electrical_evidence
from ....models.magnetic_winding_contract import WindingElectricalEvidence

MU0_H_PER_M = 4.0 * pi * 1e-7
COPPER_RESISTIVITY_25C_OHM_M = 1.724e-8
LITZ_PACKING_FACTOR = 1.10
DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2 = 4.0
DEFAULT_FILL_FACTOR_LIMIT = 0.40
DEFAULT_INSULATION_WINDOW_RESERVE_FRACTION = 0.15
DEFAULT_AMBIENT_C = 40.0
DEFAULT_HOTSPOT_LIMIT_C = 120.0
EXTERNAL_LR_TARGET_TOLERANCE_H = 1e-12
EXTERNAL_LR_GAP_MIN_M = 0.02e-3
EXTERNAL_LR_GAP_MAX_M = 8.0e-3
EXTERNAL_LR_GAP_TO_LE_MAX = 0.15
EXTERNAL_LR_INDUCTANCE_ERROR_LIMIT_PERCENT = 10.0
EXTERNAL_LR_MAX_TURNS_ABSOLUTE = 180

BOUNDARY_SATURATION_CASES: tuple[tuple[str, str, str], ...] = (
    ("Vin_min/Vout_min/Pmax", "vin_min_v", "vout_min_v"),
    ("Vin_min/Vout_max/Pmax", "vin_min_v", "vout_max_v"),
    ("Vin_max/Vout_min/Pmax", "vin_max_v", "vout_min_v"),
    ("Vin_max/Vout_max/Pmax", "vin_max_v", "vout_max_v"),
)

FrequencySolver = Callable[["LLCTransformerDesignInputs", str, float, float, float], float]


@dataclass(frozen=True)
class LLCTransformerDesignInputs:
    """Electrical targets for a separated first-pass LLC transformer design."""

    vin_min_v: float
    vin_nom_v: float
    vin_max_v: float
    vout_min_v: float
    vout_nom_v: float
    vout_max_v: float
    pout_max_w: float
    fs_min_hz: float
    fs_nom_hz: float
    fs_max_hz: float
    primary_bridge_type: str
    secondary_rectifier_type: str
    primary_bridge_gain_factor: float
    transformer_ratio_np: int
    transformer_ratio_ns: int
    turns_ratio_n: float
    lr_target_h: float
    lm_target_h: float
    ln: float
    q_nom: float
    primary_current_rms_a: float
    primary_current_peak_a: float
    secondary_current_rms_a: float
    secondary_current_peak_a: float
    ideal_turns_ratio: float | None = None
    turns_ratio_tolerance_percent: float = 5.0
    b_limit_t: float = 0.18
    lm_tolerance_percent: float = 10.0
    leakage_fraction_estimate: float = 0.02
    leakage_limit_h: float = 0.0


@dataclass(frozen=True)
class LLCTransformerTurnsCandidate:
    """Scaled integer turns candidate that preserves the FHA-selected base ratio."""

    base_np: int
    base_ns: int
    scale_factor: int
    np: int
    ns: int
    actual_turns_ratio: float
    ratio_error_percent: float


@dataclass(frozen=True)
class LLCTransformerBoundaryFluxCase:
    """Flux result for one full-load LLC transformer saturation boundary case."""

    case_name: str
    vin_v: float
    vout_v: float
    pout_w: float
    fs_hz: float
    primary_voltage_v: float
    ae_m2: float
    np: int
    delta_b_t: float
    b_peak_t: float
    pass_b_limit: bool
    fs_source: str = "unknown"
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LLCTransformerFluxDensityAudit:
    """Audit metadata for separated LLC transformer voltage-second flux definitions."""

    transformer_design_id: str
    core_id: str
    material_id: str
    np: int
    ns: int
    ae_used_mm2: float
    ae_source_field: str
    ae_used_m2: float
    vpri_basis_v: float
    voltage_basis_label: str
    fs_basis_hz: float
    formula_reported_bpeak: str
    reported_bpeak_t: float
    derived_delta_b_t: float
    derived_bpeak_t: float
    b_limit_t: float
    b_utilization: float
    b_margin_percent: float
    current_field_definition: str
    core_loss_b_input_definition: str
    definition: str
    worst_case_name: str
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LLCTransformerCoreRecord:
    """Small core-like record used by the isolated first-pass helper."""

    core_id: str
    material_id: str
    ae_m2: float
    le_m: float
    ve_m3: float


@dataclass(frozen=True)
class LLCTransformerFirstPassCandidate:
    """First-pass separated LLC transformer candidate for a supplied core record."""

    core_id: str
    material_id: str
    ae_m2: float
    le_m: float
    ve_m3: float
    np: int
    ns: int
    scale_factor: int
    actual_turns_ratio: float
    ratio_error_percent: float
    gap_m: float
    lm_target_h: float
    lm_actual_h: float
    lm_error_percent: float
    lr_target_h: float
    estimated_lk_h: float
    lk_over_lr: float
    leakage_pass: bool
    leakage_method: str
    leakage_winding_arrangement: str
    leakage_warning: str
    leakage_effective_height_m: float
    leakage_primary_radial_build_m: float
    leakage_secondary_radial_build_m: float
    leakage_insulation_gap_m: float
    max_b_peak_t: float
    max_delta_b_t: float
    worst_flux_case_name: str
    saturation_pass: bool
    primary_current_rms_a: float
    primary_current_peak_a: float
    secondary_current_rms_a: float
    secondary_current_peak_a: float
    boundary_flux_cases: list[LLCTransformerBoundaryFluxCase] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LLCTransformerFirstPassResult:
    """Container for first-pass separated LLC transformer evaluations."""

    inputs: LLCTransformerDesignInputs
    turns_candidates: list[LLCTransformerTurnsCandidate]
    evaluated_candidates: list[LLCTransformerFirstPassCandidate]
    feasible_candidates: list[LLCTransformerFirstPassCandidate]
    recommended_candidate: LLCTransformerFirstPassCandidate | None
    boundary_flux_cases: list[LLCTransformerBoundaryFluxCase]
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LLCTransformerWindingEstimate:
    """First-pass winding estimate for one LLC transformer winding."""

    winding_name: str
    turns: int
    current_rms_a: float
    current_peak_a: float
    current_density_a_per_mm2: float
    conductor_area_mm2: float
    selected_wire_id: str
    strands_or_parallel: int
    dc_resistance_ohm: float
    ac_resistance_ohm: float
    copper_loss_w: float
    fill_area_mm2: float
    bundle_equivalent_diameter_m: float
    turns_per_layer: int
    layer_count: int
    radial_build_m: float
    occupied_height_m: float
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    winding_evidence: WindingElectricalEvidence | None = None


@dataclass(frozen=True)
class LLCTransformerMagneticLossEstimate:
    """First-pass LLC transformer magnetic loss estimate."""

    core_loss_w: float
    primary_copper_loss_w: float
    secondary_copper_loss_w: float
    total_copper_loss_w: float
    total_loss_w: float
    loss_model: str
    frequency_basis_hz: float
    flux_basis_t: float
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    kernel_core_loss_w: float | None = None
    legacy_core_loss_w_with_erroneous_x1000: float | None = None
    kernel_vs_legacy_relative_difference: float | None = None
    core_loss_unit_conversion_policy: str = "W_per_m3_times_m3_equals_W_once"


@dataclass(frozen=True)
class LLCTransformerThermalEstimate:
    """First-pass LLC transformer thermal estimate."""

    hotspot_c: float
    temperature_rise_c: float
    ambient_c: float
    thermal_margin_c: float
    thermal_model: str
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LLCTransformerScreeningCandidate:
    """Screened separated LLC transformer candidate from magnetic database records."""

    candidate_id: str
    core_id: str
    material_id: str
    ae_m2: float
    le_m: float
    ve_m3: float
    window_area_m2: float
    np: int
    ns: int
    scale_factor: int
    actual_turns_ratio: float
    ratio_error_percent: float
    lm_target_h: float
    lm_actual_h: float
    lm_error_percent: float
    gap_m: float
    lr_target_h: float
    estimated_lk_h: float
    lk_over_lr: float
    leakage_pass: bool
    leakage_method: str
    leakage_winding_arrangement: str
    leakage_warning: str
    leakage_height_source: str
    leakage_height_warning: str
    leakage_usable_window_height_mm: float
    leakage_primary_occupied_height_mm: float
    leakage_secondary_occupied_height_mm: float
    leakage_window_area_mm2: float
    leakage_inferred_window_width_mm: float
    leakage_effective_height_m: float
    leakage_primary_radial_build_m: float
    leakage_secondary_radial_build_m: float
    leakage_insulation_gap_m: float
    max_b_peak_t: float
    max_delta_b_t: float
    b_limit_t: float
    worst_flux_case_name: str
    saturation_pass: bool
    primary_winding: LLCTransformerWindingEstimate | None
    secondary_winding: LLCTransformerWindingEstimate | None
    fill_factor: float
    fill_limit: float
    primary_fill_area_m2: float
    secondary_fill_area_m2: float
    insulation_reserved_area_m2: float
    total_fill_area_m2: float
    fill_pass: bool
    current_density_pass: bool
    np_required_by_saturation: int
    scale_min_by_saturation: int
    scale_factor_range_used: tuple[int, int]
    max_scale_factor_used: int
    saturation_worst_case: str
    core_loss_w: float
    copper_loss_w: float
    total_loss_w: float
    hotspot_c: float
    thermal_pass: bool
    estimated_volume_m3: float
    feasible: bool
    rejection_reasons: list[str] = field(default_factory=list)
    boundary_flux_cases: list[LLCTransformerBoundaryFluxCase] = field(default_factory=list)
    magnetic_loss: LLCTransformerMagneticLossEstimate | None = None
    thermal_estimate: LLCTransformerThermalEstimate | None = None
    primary_rms_current_design_a: float | None = None
    secondary_rms_current_design_a: float | None = None
    current_basis_label: str = ""
    current_basis_corner: str = ""
    frequency_basis_hz: float | None = None
    flux_density_audit: LLCTransformerFluxDensityAudit | None = None
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ae_mm2(self) -> float:
        return self.ae_m2 * 1e6

    @property
    def le_mm(self) -> float:
        return self.le_m * 1e3

    @property
    def ve_cm3(self) -> float:
        return self.ve_m3 * 1e6

    @property
    def window_area_mm2(self) -> float:
        return self.window_area_m2 * 1e6

    @property
    def estimated_volume_cm3(self) -> float:
        return self.estimated_volume_m3 * 1e6

    @property
    def estimated_lk_uH(self) -> float:
        return self.estimated_lk_h * 1e6

    @property
    def lk_over_lr_percent(self) -> float:
        return self.lk_over_lr * 100.0

    @property
    def leakage_effective_height_mm(self) -> float:
        return self.leakage_effective_height_m * 1e3

    @property
    def leakage_primary_radial_build_mm(self) -> float:
        return self.leakage_primary_radial_build_m * 1e3

    @property
    def leakage_secondary_radial_build_mm(self) -> float:
        return self.leakage_secondary_radial_build_m * 1e3

    @property
    def leakage_insulation_gap_mm(self) -> float:
        return self.leakage_insulation_gap_m * 1e3

    @property
    def leakage_used_legacy_fallback(self) -> bool:
        return self.leakage_method == "legacy_fraction_fallback"

    @property
    def leakage_status(self) -> str:
        if self.leakage_used_legacy_fallback:
            return "fallback_uncertain" if not self.leakage_pass else "fallback_uncertain"
        if self.lk_over_lr <= 0.20:
            return "excellent"
        if self.lk_over_lr <= 0.40:
            return "acceptable"
        if self.lk_over_lr <= 0.80:
            return "warning"
        return "rejected"


@dataclass(frozen=True)
class LLCTransformerCandidateSearchResult:
    """First-pass separated LLC transformer magnetic screening result."""

    inputs: LLCTransformerDesignInputs
    registered_core_count: int
    registered_material_count: int
    registered_wire_count: int
    evaluated_candidate_count: int
    feasible_candidate_count: int
    rejected_by_saturation_count: int
    rejected_by_lm_count: int
    rejected_by_leakage_count: int
    rejected_by_fill_count: int
    rejected_by_thermal_count: int
    rejected_by_missing_data_count: int
    feasible_candidates: list[LLCTransformerScreeningCandidate]
    screened_candidates_sample: list[LLCTransformerScreeningCandidate]
    recommended_preliminary_candidate: LLCTransformerScreeningCandidate | None
    rejected_by_missing_hard_data_count: int = 0
    warning_soft_missing_data_count: int = 0
    fallback_loss_count: int = 0
    fallback_thermal_count: int = 0
    hard_missing_data_reasons: dict[str, int] = field(default_factory=dict)
    closest_saturation_candidates: list[dict[str, object]] = field(default_factory=list)
    closest_fill_candidates: list[dict[str, object]] = field(default_factory=list)
    scale_search_diagnostics: dict[str, object] = field(default_factory=dict)
    leakage_rejection_audit: dict[str, object] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LLCTransformerRepresentativeSelection:
    """Named transformer Pareto representative."""

    role: str
    candidate: LLCTransformerScreeningCandidate
    reason: str


@dataclass(frozen=True)
class LLCTransformerParetoResult:
    """Transformer-specific Pareto and representative selection result."""

    feasible_candidates: list[LLCTransformerScreeningCandidate]
    pareto_candidates: list[LLCTransformerScreeningCandidate]
    chosen_candidates: list[LLCTransformerRepresentativeSelection]
    representative_by_role: dict[str, LLCTransformerRepresentativeSelection]
    recommended_candidate: LLCTransformerScreeningCandidate | None
    recommended_policy: str
    artifact_paths: list[str] = field(default_factory=list)
    plot_diagnostics: dict[str, object] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def feasible_count(self) -> int:
        return len(self.feasible_candidates)

    @property
    def pareto_count(self) -> int:
        return len(self.pareto_candidates)

    @property
    def chosen_count(self) -> int:
        return len(self.chosen_candidates)


@dataclass(frozen=True)
class _NormalizedCoreRecord:
    core_id: str
    ae_m2: float
    ae_source_field: str
    le_m: float
    ve_m3: float
    window_area_m2: float
    outer_width_m: float
    outer_height_m: float
    mean_length_per_turn_m: float
    gross_volume_m3: float


@dataclass(frozen=True)
class _NormalizedMaterialRecord:
    material_id: str
    b_sat_t: float
    steinmetz_ranges: list[dict[str, float]]
    f_min_recommended_hz: float | None = None
    f_max_recommended_hz: float | None = None
    material_metric_source: str = ""


@dataclass(frozen=True)
class _NormalizedWireRecord:
    wire_id: str
    strand_diameter_m: float
    strands_per_bundle: int
    bundle_copper_area_m2: float
    outer_diameter_m: float
    equivalent_bundle_diameter_m: float
    stable_wire_id: str = ""
    wire_name: str = ""
    source_wire_record: Mapping[str, Any] = field(default_factory=dict)
    conducting_area_basis: str = "engine_bundle_copper_area"


def primary_bridge_gain_factor(primary_bridge_type: str) -> float:
    """Return primary bridge square-wave voltage gain for first-pass transformer design."""

    if primary_bridge_type == "full_bridge":
        return 1.0
    if primary_bridge_type == "half_bridge":
        return 0.5
    raise ValueError("Primary bridge type must be full_bridge or half_bridge.")


def generate_scaled_turns_candidates(
    base_np: int,
    base_ns: int,
    max_scale_factor: int,
    ideal_turns_ratio: float | None = None,
) -> list[LLCTransformerTurnsCandidate]:
    """Generate integer scaled turns candidates without changing the FHA-selected ratio."""

    if base_np <= 0 or base_ns <= 0 or max_scale_factor <= 0:
        raise ValueError("Base turns and max scale factor must be positive.")
    target_ratio = ideal_turns_ratio if ideal_turns_ratio is not None else base_np / base_ns
    if target_ratio <= 0.0:
        raise ValueError("Ideal turns ratio must be positive.")
    candidates: list[LLCTransformerTurnsCandidate] = []
    for scale_factor in range(1, max_scale_factor + 1):
        np_turns = base_np * scale_factor
        ns_turns = base_ns * scale_factor
        actual_ratio = np_turns / ns_turns
        ratio_error_percent = 100.0 * (actual_ratio - target_ratio) / target_ratio
        candidates.append(
            LLCTransformerTurnsCandidate(
                base_np=base_np,
                base_ns=base_ns,
                scale_factor=scale_factor,
                np=np_turns,
                ns=ns_turns,
                actual_turns_ratio=actual_ratio,
                ratio_error_percent=ratio_error_percent,
            )
        )
    return candidates


def _generate_scaled_turns_candidates_in_range(
    base_np: int,
    base_ns: int,
    scale_start: int,
    scale_stop: int,
    ideal_turns_ratio: float | None = None,
) -> list[LLCTransformerTurnsCandidate]:
    if base_np <= 0 or base_ns <= 0 or scale_start <= 0 or scale_stop < scale_start:
        raise ValueError("Base turns and scale range must be positive.")
    target_ratio = ideal_turns_ratio if ideal_turns_ratio is not None else base_np / base_ns
    if target_ratio <= 0.0:
        raise ValueError("Ideal turns ratio must be positive.")
    candidates: list[LLCTransformerTurnsCandidate] = []
    for scale_factor in range(scale_start, scale_stop + 1):
        np_turns = base_np * scale_factor
        ns_turns = base_ns * scale_factor
        actual_ratio = np_turns / ns_turns
        ratio_error_percent = 100.0 * (actual_ratio - target_ratio) / target_ratio
        candidates.append(
            LLCTransformerTurnsCandidate(
                base_np=base_np,
                base_ns=base_ns,
                scale_factor=scale_factor,
                np=np_turns,
                ns=ns_turns,
                actual_turns_ratio=actual_ratio,
                ratio_error_percent=ratio_error_percent,
            )
        )
    return candidates


def mm2_to_m2(value_mm2: float) -> float:
    """Convert square millimeters to square meters."""

    return float(value_mm2) * 1e-6


def m2_to_mm2(value_m2: float) -> float:
    """Convert square meters to square millimeters."""

    return float(value_m2) * 1e6


def compute_primary_square_voltage(vin_v: float, primary_bridge_type: str) -> float:
    """Return the first-pass square-wave voltage applied to the transformer primary."""

    if vin_v <= 0.0:
        raise ValueError("Input voltage must be positive.")
    return primary_bridge_gain_factor(primary_bridge_type) * vin_v


def compute_delta_b_square_wave(vpri_v: float, np: int, ae_m2: float, fs_hz: float) -> float:
    """Return peak-to-peak flux swing from deltaB = Vpri / (2 * Np * Ae * fs)."""

    return compute_transformer_square_wave_delta_b_t(vpri_v, np, ae_m2, fs_hz)


def compute_transformer_square_wave_delta_b_t(vpri_v: float, np: int, ae_m2: float, fs_hz: float) -> float:
    """Return physical peak-to-peak flux-density swing for symmetric square-wave drive."""

    if vpri_v <= 0.0 or np <= 0 or ae_m2 <= 0.0 or fs_hz <= 0.0:
        raise ValueError("Voltage, turns, effective area, and frequency must be positive.")
    return vpri_v / (2.0 * np * ae_m2 * fs_hz)


def compute_transformer_square_wave_bpeak_t(vpri_v: float, np: int, ae_m2: float, fs_hz: float) -> float:
    """Return physical peak flux density for symmetric square-wave drive."""

    if vpri_v <= 0.0 or np <= 0 or ae_m2 <= 0.0 or fs_hz <= 0.0:
        raise ValueError("Voltage, turns, effective area, and frequency must be positive.")
    return vpri_v / (4.0 * np * ae_m2 * fs_hz)


def compute_transformer_flux_density_audit(
    *,
    transformer_design_id: str,
    core_id: str,
    material_id: str,
    np: int,
    ns: int,
    ae_m2: float,
    ae_source_field: str,
    vpri_v: float,
    voltage_basis_label: str,
    fs_hz: float,
    reported_bpeak_t: float,
    reported_delta_b_t: float,
    b_limit_t: float,
    worst_case_name: str,
) -> LLCTransformerFluxDensityAudit:
    """Build transformer flux-density audit data for the stored screening values."""

    derived_bpeak_t = compute_transformer_square_wave_bpeak_t(vpri_v, np, ae_m2, fs_hz)
    derived_delta_b_t = compute_transformer_square_wave_delta_b_t(vpri_v, np, ae_m2, fs_hz)
    tolerance = max(abs(derived_bpeak_t), abs(derived_delta_b_t), 1.0) * 1e-9
    warnings: list[str] = []
    if abs(reported_bpeak_t - derived_bpeak_t) <= tolerance:
        current_field_definition = "bpeak_peak"
        definition = "peak flux density, not peak-to-peak swing"
        formula_reported = "Vpri/(4*Np*Ae*fs)"
    elif abs(reported_bpeak_t - derived_delta_b_t) <= tolerance:
        current_field_definition = "delta_b_peak_to_peak"
        definition = "flux-density swing deltaB, not peak B"
        formula_reported = "Vpri/(2*Np*Ae*fs)"
        warnings.append("Reported Bpeak field matches deltaB; label should not call this Bpeak unless converted to peak value.")
    else:
        current_field_definition = "unknown"
        definition = "unknown flux-density definition"
        formula_reported = "legacy reported field; does not match Vpri/(4*Np*Ae*fs) or Vpri/(2*Np*Ae*fs)"
        warnings.append("Reported Bpeak field does not match the physical peak or peak-to-peak square-wave formulas.")
    if abs(reported_delta_b_t - derived_delta_b_t) > tolerance:
        warnings.append("Reported delta_B field does not match Vpri/(2*Np*Ae*fs); audit exposes derived physical deltaB separately.")
    b_utilization = reported_bpeak_t / b_limit_t if b_limit_t > 0.0 else 0.0
    b_margin_percent = 100.0 * (b_limit_t - reported_bpeak_t) / b_limit_t if b_limit_t > 0.0 else 0.0
    return LLCTransformerFluxDensityAudit(
        transformer_design_id=transformer_design_id,
        core_id=core_id,
        material_id=material_id,
        np=np,
        ns=ns,
        ae_used_mm2=ae_m2 * 1e6,
        ae_source_field=ae_source_field,
        ae_used_m2=ae_m2,
        vpri_basis_v=vpri_v,
        voltage_basis_label=voltage_basis_label,
        fs_basis_hz=fs_hz,
        formula_reported_bpeak=formula_reported,
        reported_bpeak_t=reported_bpeak_t,
        derived_delta_b_t=derived_delta_b_t,
        derived_bpeak_t=derived_bpeak_t,
        b_limit_t=b_limit_t,
        b_utilization=b_utilization,
        b_margin_percent=b_margin_percent,
        current_field_definition=current_field_definition,
        core_loss_b_input_definition=current_field_definition,
        definition=definition,
        worst_case_name=worst_case_name,
        warnings=warnings,
    )


def compute_required_primary_turns_for_saturation(
    inputs: LLCTransformerDesignInputs,
    ae_m2: float,
    frequency_solver: FrequencySolver | None = None,
) -> tuple[int, dict[str, int], str]:
    """Return saturation-driven minimum Np and per-boundary diagnostics."""

    if ae_m2 <= 0.0:
        raise ValueError("Effective area must be positive.")
    required_by_case: dict[str, int] = {}
    worst_case_name = ""
    worst_required = 1
    for case_name, vin_attr, vout_attr in BOUNDARY_SATURATION_CASES:
        vin_v = float(getattr(inputs, vin_attr))
        vout_v = float(getattr(inputs, vout_attr))
        fs_hz, _notes, _fs_source = _resolve_boundary_frequency(
            inputs,
            case_name,
            vin_v,
            vout_v,
            inputs.pout_max_w,
            frequency_solver,
        )
        primary_voltage_v = compute_primary_square_voltage(vin_v, inputs.primary_bridge_type)
        required_np = max(1, ceil(primary_voltage_v / (4.0 * ae_m2 * fs_hz * inputs.b_limit_t)))
        required_by_case[case_name] = required_np
        if required_np >= worst_required:
            worst_required = required_np
            worst_case_name = case_name
    return worst_required, required_by_case, worst_case_name


def compute_gap_for_lm(
    np: int,
    ae_m2: float,
    lm_target_h: float,
    le_m: float | None = None,
    mu_r: float | None = None,
) -> float:
    """Compute first-pass equivalent gap for Lm, using core reluctance when supplied."""

    if np <= 0 or ae_m2 <= 0.0 or lm_target_h <= 0.0:
        raise ValueError("Turns, effective area, and Lm target must be positive.")
    total_reluctance = np**2 / lm_target_h
    core_reluctance = 0.0
    if le_m is not None and mu_r is not None and le_m > 0.0 and mu_r > 0.0:
        core_reluctance = le_m / (MU0_H_PER_M * mu_r * ae_m2)
    gap_reluctance = max(total_reluctance - core_reluctance, 1e-18)
    return gap_reluctance * MU0_H_PER_M * ae_m2


def compute_lm_from_gap(np: int, ae_m2: float, gap_m: float) -> float:
    """Compute first-pass magnetizing inductance from an equivalent air gap."""

    if np <= 0 or ae_m2 <= 0.0 or gap_m <= 0.0:
        raise ValueError("Turns, effective area, and gap must be positive.")
    return MU0_H_PER_M * np**2 * ae_m2 / gap_m


def estimate_leakage_inductance(lm_actual_h: float, leakage_fraction_estimate: float) -> float:
    """Legacy fallback first-pass leakage estimate as a simple fraction of Lm."""

    if lm_actual_h <= 0.0 or leakage_fraction_estimate < 0.0:
        raise ValueError("Lm and leakage fraction must be non-negative and physically valid.")
    return leakage_fraction_estimate * lm_actual_h


def estimate_legacy_leakage_inductance(lm_actual_h: float, leakage_fraction_estimate: float) -> float:
    """Compatibility wrapper for the legacy fraction-based leakage estimate."""

    return estimate_leakage_inductance(lm_actual_h, leakage_fraction_estimate)


@dataclass(frozen=True)
class _LeakageGeometryEstimate:
    leakage_effective_height_m: float
    leakage_height_source: str
    leakage_height_warning: str
    leakage_usable_window_height_m: float
    leakage_primary_occupied_height_m: float
    leakage_secondary_occupied_height_m: float
    leakage_window_area_m2: float
    leakage_inferred_window_width_m: float


def _estimate_effective_winding_height_m(
    primary_winding: LLCTransformerWindingEstimate | None,
    secondary_winding: LLCTransformerWindingEstimate | None,
    core: _NormalizedCoreRecord,
) -> _LeakageGeometryEstimate:
    primary_occupied_height_m = primary_winding.occupied_height_m if primary_winding is not None else 0.0
    secondary_occupied_height_m = secondary_winding.occupied_height_m if secondary_winding is not None else 0.0
    occupied = [value for value in (primary_occupied_height_m, secondary_occupied_height_m) if value > 0.0]
    core_window_area_m2 = _core_window_area_m2(core)
    core_outer_width_m = _core_outer_width_m(core)
    core_outer_height_m = _core_outer_height_m(core)
    inferred_window_width_m = max(
        core_outer_width_m,
        (core_window_area_m2 ** 0.5) if core_window_area_m2 > 0.0 else 0.0,
        1e-6,
    )
    window_height_from_area_m = max(core_window_area_m2 / inferred_window_width_m, 1e-6)
    usable_window_height_m = window_height_from_area_m
    height_source = "area_proxy"
    height_warning = "Leakage effective height derived from proxy geometry."
    if core_outer_height_m > 0.0:
        conservative_core_limit_m = 0.30 * core_outer_height_m
        if conservative_core_limit_m < usable_window_height_m:
            usable_window_height_m = conservative_core_limit_m
            height_source = "outer_height_cap"
            height_warning = "Leakage effective height was clamped to a conservative usable window height."
    if occupied:
        overlap_height_m = min(occupied)
        effective_height_m = min(overlap_height_m, usable_window_height_m)
        if effective_height_m < overlap_height_m:
            height_source = f"occupied_height_capped_by_{height_source}"
            height_warning = (
                "Leakage effective height was derived from proxy geometry and capped to a conservative usable window height."
            )
        else:
            height_source = "occupied_height_overlap"
            height_warning = ""
    else:
        effective_height_m = usable_window_height_m
        if core_outer_height_m <= 0.0:
            height_warning = "Leakage effective height derived from proxy geometry."
    return _LeakageGeometryEstimate(
        leakage_effective_height_m=max(effective_height_m, 1e-6),
        leakage_height_source=height_source,
        leakage_height_warning=height_warning,
        leakage_usable_window_height_m=max(usable_window_height_m, 1e-6),
        leakage_primary_occupied_height_m=primary_occupied_height_m,
        leakage_secondary_occupied_height_m=secondary_occupied_height_m,
        leakage_window_area_m2=core_window_area_m2,
        leakage_inferred_window_width_m=inferred_window_width_m,
    )


def _estimate_leakage_geometry(
    primary_winding: LLCTransformerWindingEstimate | None,
    secondary_winding: LLCTransformerWindingEstimate | None,
    core: _NormalizedCoreRecord,
) -> tuple[_LeakageGeometryEstimate, float, float, float]:
    leakage_geometry = _estimate_effective_winding_height_m(primary_winding, secondary_winding, core)
    leakage_primary_radial_build_m = primary_winding.radial_build_m if primary_winding is not None else 0.0
    leakage_secondary_radial_build_m = secondary_winding.radial_build_m if secondary_winding is not None else 0.0
    leakage_insulation_gap_m = 0.0005
    return leakage_geometry, leakage_primary_radial_build_m, leakage_secondary_radial_build_m, leakage_insulation_gap_m


def _core_window_area_m2(core: object) -> float:
    value = getattr(core, "window_area_m2", 0.0)
    if value and value > 0.0:
        return float(value)
    ae_m2 = float(getattr(core, "ae_m2", 0.0) or 0.0)
    return max(6.0 * ae_m2, 1e-8)


def _core_outer_width_m(core: object) -> float:
    return float(getattr(core, "outer_width_m", 0.0) or 0.0)


def _core_outer_height_m(core: object) -> float:
    return float(getattr(core, "outer_height_m", 0.0) or 0.0)


def _core_mean_length_per_turn_m(core: object) -> float:
    value = getattr(core, "mean_length_per_turn_m", 0.0)
    if value and value > 0.0:
        return float(value)
    le_m = float(getattr(core, "le_m", 0.0) or 0.0)
    return max(le_m, 1e-6)


def _estimate_candidate_leakage(
    *,
    primary_turns: int,
    mean_length_per_turn_m: float,
    effective_winding_height_m: float,
    primary_radial_build_m: float,
    secondary_radial_build_m: float,
    insulation_gap_m: float,
    leakage_fraction_estimate: float,
    fallback_lm_actual_h: float,
    winding_arrangement: str = DEFAULT_WINDING_ARRANGEMENT,
) -> tuple[float, str, str]:
    if primary_radial_build_m <= 0.0 or secondary_radial_build_m <= 0.0:
        return estimate_legacy_leakage_inductance(
            lm_actual_h=fallback_lm_actual_h,
            leakage_fraction_estimate=leakage_fraction_estimate,
        ), "legacy_fraction_fallback", "Layer-based leakage requires primary and secondary radial-build estimates; using legacy first-pass estimate."
    try:
        result = estimate_layer_based_leakage_inductance(
            primary_turns=primary_turns,
            mean_length_per_turn_m=mean_length_per_turn_m,
            effective_winding_height_m=effective_winding_height_m,
            primary_radial_build_m=primary_radial_build_m,
            secondary_radial_build_m=secondary_radial_build_m,
            insulation_gap_m=insulation_gap_m,
            winding_arrangement=winding_arrangement,
        )
    except ValueError as exc:
        return estimate_legacy_leakage_inductance(
            lm_actual_h=fallback_lm_actual_h,
            leakage_fraction_estimate=leakage_fraction_estimate,
        ), "legacy_fraction_fallback", str(exc)
    return result.estimated_lk_h, result.method, result.warning


def build_boundary_flux_cases(
    inputs: LLCTransformerDesignInputs,
    ae_m2: float,
    np: int,
    frequency_solver: FrequencySolver | None = None,
) -> list[LLCTransformerBoundaryFluxCase]:
    """Build four full-load boundary saturation cases for the supplied core area and turns."""

    cases: list[LLCTransformerBoundaryFluxCase] = []
    for case_name, vin_attr, vout_attr in BOUNDARY_SATURATION_CASES:
        vin_v = float(getattr(inputs, vin_attr))
        vout_v = float(getattr(inputs, vout_attr))
        fs_hz, notes, fs_source = _resolve_boundary_frequency(
            inputs,
            case_name,
            vin_v,
            vout_v,
            inputs.pout_max_w,
            frequency_solver,
        )
        primary_voltage_v = compute_primary_square_voltage(vin_v, inputs.primary_bridge_type)
        delta_b_t = compute_transformer_square_wave_delta_b_t(primary_voltage_v, np, ae_m2, fs_hz)
        b_peak_t = compute_transformer_square_wave_bpeak_t(primary_voltage_v, np, ae_m2, fs_hz)
        cases.append(
            LLCTransformerBoundaryFluxCase(
                case_name=case_name,
                vin_v=vin_v,
                vout_v=vout_v,
                pout_w=inputs.pout_max_w,
                fs_hz=fs_hz,
                primary_voltage_v=primary_voltage_v,
                ae_m2=ae_m2,
                np=np,
                delta_b_t=delta_b_t,
                b_peak_t=b_peak_t,
                pass_b_limit=b_peak_t <= inputs.b_limit_t,
                fs_source=fs_source,
                notes=notes,
            )
        )
    return cases


def generate_saturation_driven_turns_candidates(
    inputs: LLCTransformerDesignInputs,
    ae_m2: float,
    *,
    max_scale_factor: int = 8,
    frequency_solver: FrequencySolver | None = None,
    scale_margin: int = 3,
    scale_upper_bound: int = 120,
) -> tuple[list[LLCTransformerTurnsCandidate], dict[str, object]]:
    """Generate scaled turns around the per-core saturation-driven minimum scale."""

    if inputs.transformer_ratio_np <= 0 or inputs.transformer_ratio_ns <= 0:
        raise ValueError("Base transformer turns ratio must be positive.")
    np_required, required_by_case, worst_case_name = compute_required_primary_turns_for_saturation(
        inputs,
        ae_m2,
        frequency_solver,
    )
    scale_min = max(1, ceil(np_required / inputs.transformer_ratio_np))
    scale_start = max(1, scale_min - max(scale_margin, 0))
    dynamic_scale_stop = max(max_scale_factor, scale_min + 20)
    scale_stop = min(max(dynamic_scale_stop, scale_start), scale_upper_bound)
    diagnostics: dict[str, object] = {
        "np_required_by_saturation": np_required,
        "np_required_by_case": required_by_case,
        "scale_min_by_saturation": scale_min,
        "scale_factor_range_used": (scale_start, scale_stop),
        "max_scale_factor_used": scale_stop,
        "scale_upper_bound": scale_upper_bound,
        "saturation_worst_case": worst_case_name,
    }
    if scale_min > scale_upper_bound:
        diagnostics.update(
            {
                "skipped": True,
                "skip_reason": "scale_min_exceeds_upper_bound",
            }
        )
        return [], diagnostics
    candidates = _generate_scaled_turns_candidates_in_range(
        inputs.transformer_ratio_np,
        inputs.transformer_ratio_ns,
        scale_start,
        scale_stop,
        inputs.ideal_turns_ratio,
    )
    return candidates, diagnostics


def evaluate_transformer_candidates(
    inputs: LLCTransformerDesignInputs,
    core_records: Iterable[LLCTransformerCoreRecord],
    *,
    max_scale_factor: int = 4,
    frequency_solver: FrequencySolver | None = None,
) -> LLCTransformerFirstPassResult:
    """Evaluate scaled turns against supplied core-like records without library search."""

    leakage_limit_h = inputs.leakage_limit_h if inputs.leakage_limit_h > 0.0 else inputs.lr_target_h
    turns_candidates = generate_scaled_turns_candidates(
        inputs.transformer_ratio_np,
        inputs.transformer_ratio_ns,
        max_scale_factor,
        inputs.ideal_turns_ratio,
    )
    evaluated: list[LLCTransformerFirstPassCandidate] = []
    for core in core_records:
        _validate_core_record(core)
        for turns in turns_candidates:
            flux_cases = build_boundary_flux_cases(inputs, core.ae_m2, turns.np, frequency_solver)
            gap_m = compute_gap_for_lm(turns.np, core.ae_m2, inputs.lm_target_h, core.le_m)
            lm_actual_h = compute_lm_from_gap(turns.np, core.ae_m2, gap_m)
            lm_error_percent = 100.0 * (lm_actual_h - inputs.lm_target_h) / inputs.lm_target_h
            worst_flux = max(flux_cases, key=lambda case: case.b_peak_t)
            saturation_pass = all(case.pass_b_limit for case in flux_cases)
            (
                leakage_geometry,
                leakage_primary_radial_build_m,
                leakage_secondary_radial_build_m,
                leakage_insulation_gap_m,
            ) = _estimate_leakage_geometry(None, None, core)
            leakage_result_h, leakage_method, leakage_warning = _estimate_candidate_leakage(
                primary_turns=turns.np,
                mean_length_per_turn_m=_core_mean_length_per_turn_m(core),
                effective_winding_height_m=leakage_geometry.leakage_effective_height_m,
                primary_radial_build_m=leakage_primary_radial_build_m,
                secondary_radial_build_m=leakage_secondary_radial_build_m,
                insulation_gap_m=leakage_insulation_gap_m,
                leakage_fraction_estimate=inputs.leakage_fraction_estimate,
                fallback_lm_actual_h=lm_actual_h,
            )
            estimated_lk_h = leakage_result_h
            lk_over_lr = estimated_lk_h / inputs.lr_target_h if inputs.lr_target_h > 0.0 else float("inf")
            leakage_pass = lk_over_lr <= 0.80
            warnings = [f"Leakage estimate note: {leakage_warning}"] if leakage_warning else []
            fallback_warnings = [
                note
                for case in flux_cases
                for note in case.notes
                if "fallback" in note.lower() or "failed" in note.lower()
            ]
            warnings.extend(fallback_warnings)
            evaluated.append(
                LLCTransformerFirstPassCandidate(
                    core_id=core.core_id,
                    material_id=core.material_id,
                    ae_m2=core.ae_m2,
                    le_m=core.le_m,
                    ve_m3=core.ve_m3,
                    np=turns.np,
                    ns=turns.ns,
                    scale_factor=turns.scale_factor,
                    actual_turns_ratio=turns.actual_turns_ratio,
                    ratio_error_percent=turns.ratio_error_percent,
                    gap_m=gap_m,
                    lm_target_h=inputs.lm_target_h,
                    lm_actual_h=lm_actual_h,
                    lm_error_percent=lm_error_percent,
                    lr_target_h=inputs.lr_target_h,
                    estimated_lk_h=estimated_lk_h,
                    lk_over_lr=lk_over_lr,
                    leakage_pass=leakage_pass,
                    leakage_method=leakage_method,
                    leakage_winding_arrangement=DEFAULT_WINDING_ARRANGEMENT,
                    leakage_warning=leakage_warning,
                    leakage_effective_height_m=leakage_geometry.leakage_effective_height_m,
                    leakage_primary_radial_build_m=leakage_primary_radial_build_m,
                    leakage_secondary_radial_build_m=leakage_secondary_radial_build_m,
                    leakage_insulation_gap_m=leakage_insulation_gap_m,
                    max_b_peak_t=worst_flux.b_peak_t,
                    max_delta_b_t=worst_flux.delta_b_t,
                    worst_flux_case_name=worst_flux.case_name,
                    saturation_pass=saturation_pass,
                    primary_current_rms_a=inputs.primary_current_rms_a,
                    primary_current_peak_a=inputs.primary_current_peak_a,
                    secondary_current_rms_a=inputs.secondary_current_rms_a,
                    secondary_current_peak_a=inputs.secondary_current_peak_a,
                    boundary_flux_cases=flux_cases,
                    notes=[
                        "Separated LLC transformer candidate realizes the integer turns ratio and Lm; Lr remains external.",
                        "Flux uses Bpeak = Vpri / (4 * Np * Ae * fs) and delta_B = Vpri / (2 * Np * Ae * fs) under symmetric bipolar excitation.",
                        "Lm uses an air-gap dominated first-pass estimate unless core permeability is supplied.",
                    ],
                    warnings=warnings,
                )
            )

    feasible = [
        candidate
        for candidate in evaluated
        if candidate.saturation_pass
        and candidate.leakage_pass
        and abs(candidate.lm_error_percent) <= inputs.lm_tolerance_percent
    ]
    recommended = min(
        feasible,
        key=lambda candidate: (candidate.scale_factor, candidate.max_b_peak_t, candidate.ae_m2),
        default=None,
    )
    return LLCTransformerFirstPassResult(
        inputs=inputs,
        turns_candidates=turns_candidates,
        evaluated_candidates=evaluated,
        feasible_candidates=feasible,
        recommended_candidate=recommended,
        boundary_flux_cases=(evaluated[0].boundary_flux_cases if evaluated else []),
        notes=[
            "First-pass separated LLC transformer helper only evaluates supplied fixture/core records.",
            "Full magnetic library candidate search, Pareto ranking, geometry, winding optimization, and integrated leakage-resonant design are not implemented.",
        ],
        warnings=[],
    )


def generate_separated_llc_transformer_candidates(
    transformer_inputs: LLCTransformerDesignInputs,
    core_records: Iterable[object] | None = None,
    material_records: Iterable[object] | None = None,
    wire_records: Iterable[object] | None = None,
    *,
    max_scale_factor: int = 8,
    frequency_solver: FrequencySolver | None = None,
    core_limit: int | None = 24,
    material_limit: int | None = 8,
    wire_limit: int | None = 16,
    write_debug_csv: bool = False,
    output_dir: Path | None = None,
) -> LLCTransformerCandidateSearchResult:
    """Generate and screen separated LLC transformer candidates from normalized magnetic records."""

    raw_cores, raw_materials, raw_wires, backend_notes = _resolve_candidate_source_records(
        core_records,
        material_records,
        wire_records,
    )
    registered_core_count = len(raw_cores)
    registered_material_count = len(raw_materials)
    registered_wire_count = len(raw_wires)
    cores, missing_core_count = _normalize_core_records(raw_cores)
    materials, missing_material_count = _normalize_material_records(raw_materials)
    wires, missing_wire_count = _normalize_wire_records(raw_wires)
    cores = _select_search_cores(cores, transformer_inputs, core_limit)
    materials = _limit_records(
        sorted(materials, key=lambda item: (-item.b_sat_t, item.material_id)),
        material_limit,
    )
    wires = _select_search_wires(wires, transformer_inputs, wire_limit)

    screened: list[LLCTransformerScreeningCandidate] = []
    skipped_core_diagnostics: list[dict[str, object]] = []
    for core in cores:
        turns_candidates, turns_diagnostics = generate_saturation_driven_turns_candidates(
            transformer_inputs,
            core.ae_m2,
            max_scale_factor=max_scale_factor,
            frequency_solver=frequency_solver,
        )
        if not turns_candidates:
            skipped_core_diagnostics.append(
                {
                    "core_id": core.core_id,
                    "ae_m2": core.ae_m2,
                    **turns_diagnostics,
                }
            )
            continue
        for material in materials:
            for turns in turns_candidates:
                screened.append(
                    _screen_transformer_candidate(
                        inputs=transformer_inputs,
                        core=core,
                        material=material,
                        wires=wires,
                        turns=turns,
                        turns_diagnostics=turns_diagnostics,
                        frequency_solver=frequency_solver,
                    )
                )

    feasible_candidates = sorted(
        [candidate for candidate in screened if candidate.feasible],
        key=lambda candidate: (candidate.total_loss_w, candidate.estimated_volume_m3, candidate.fill_factor, candidate.candidate_id),
    )
    recommended = feasible_candidates[0] if feasible_candidates else None
    sample = _screened_sample(screened)
    artifact_paths: list[str] = []
    if write_debug_csv:
        artifact_paths = export_llc_transformer_feasible_candidates(
            feasible_candidates,
            output_dir=output_dir,
        )
        leakage_audit_path = export_llc_transformer_leakage_rejection_audit(
            screened,
            output_dir=output_dir,
        )
        artifact_paths.extend(leakage_audit_path)
    candidate_missing_hard_count = _count_rejection(screened, "missing_data_hard")
    missing_data_count = missing_core_count + missing_material_count + missing_wire_count + candidate_missing_hard_count
    hard_missing_reasons = _hard_missing_data_reason_counts(screened)
    if missing_core_count:
        hard_missing_reasons["core_required_fields"] = hard_missing_reasons.get("core_required_fields", 0) + missing_core_count
    if missing_material_count:
        hard_missing_reasons["material_identity_or_bsat"] = hard_missing_reasons.get("material_identity_or_bsat", 0) + missing_material_count
    if missing_wire_count:
        hard_missing_reasons["wire_required_fields"] = hard_missing_reasons.get("wire_required_fields", 0) + missing_wire_count
    closest_saturation = _closest_saturation_candidates(screened, transformer_inputs.b_limit_t)
    closest_fill = _closest_fill_candidates(screened)
    scale_diagnostics = _scale_search_diagnostics(screened, skipped_core_diagnostics)
    leakage_audit = _leakage_rejection_audit(screened)
    notes = _dedupe_text([
        *backend_notes,
        "Separated LLC transformer candidate search uses packaged-normalized magnetic records when records are not supplied.",
        "The separated transformer realizes Np:Ns and Lm; external Lr remains a separate resonant inductor.",
        "Flux model uses Bpeak = Vpri / (4 * Np * Ae * fs) and delta_B = Vpri / (2 * Np * Ae * fs) under symmetric bipolar excitation.",
        "Screening uses first-pass winding, leakage, core-loss, and thermal approximations.",
    ])
    if not feasible_candidates:
        notes.append(
            "No feasible candidates were found; closest saturation/fill diagnostics and hard missing-data counts are available in the search result."
        )
    if skipped_core_diagnostics:
        notes.append(
            f"Skipped {len(skipped_core_diagnostics)} undersized core(s) whose saturation-driven turns exceeded the search upper bound."
        )
    return LLCTransformerCandidateSearchResult(
        inputs=transformer_inputs,
        registered_core_count=registered_core_count,
        registered_material_count=registered_material_count,
        registered_wire_count=registered_wire_count,
        evaluated_candidate_count=len(screened),
        feasible_candidate_count=len(feasible_candidates),
        rejected_by_saturation_count=_count_rejection(screened, "saturation"),
        rejected_by_lm_count=_count_rejection(screened, "lm"),
        rejected_by_leakage_count=_count_rejection(screened, "leakage"),
        rejected_by_fill_count=_count_rejection(screened, "fill"),
        rejected_by_thermal_count=_count_rejection(screened, "thermal"),
        rejected_by_missing_data_count=missing_data_count,
        rejected_by_missing_hard_data_count=missing_data_count,
        warning_soft_missing_data_count=_count_warning(screened, "soft missing"),
        fallback_loss_count=_count_warning(screened, "fallback core-loss"),
        fallback_thermal_count=_count_warning(screened, "volume-proxy"),
        feasible_candidates=feasible_candidates,
        screened_candidates_sample=sample,
        recommended_preliminary_candidate=recommended,
        hard_missing_data_reasons=hard_missing_reasons,
        closest_saturation_candidates=closest_saturation,
        closest_fill_candidates=closest_fill,
        scale_search_diagnostics=scale_diagnostics,
        leakage_rejection_audit=leakage_audit,
        artifact_paths=artifact_paths,
        notes=notes,
        warnings=_dedupe_text([
            "Winding, leakage, core-loss, and thermal estimates are first-pass screening approximations.",
        ]),
    )


def export_llc_transformer_feasible_candidates(
    feasible_candidates: Iterable[LLCTransformerScreeningCandidate],
    output_dir: Path | None = None,
) -> list[str]:
    """Write a lightweight debug CSV for feasible separated LLC transformer candidates."""

    candidates = list(feasible_candidates)
    if not candidates:
        return []
    output_root = Path(output_dir or _project_root() / "outputs" / "transformer_design")
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / "llc_transformer_feasible_candidates.csv"
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "core_id",
                "material_id",
                "ae_mm2",
                "le_mm",
                "ve_cm3",
                "window_area_mm2",
                "estimated_volume_cm3",
                "np",
                "ns",
                "gap_mm",
                "lm_target_uH",
                "lm_actual_uH",
                "lm_error_percent",
                "estimated_lk_uH",
                "lr_target_uH",
                "lk_over_lr",
                "lk_over_lr_percent",
                "max_b_peak_t",
                "max_delta_b_t",
                "bpeak_t",
                "delta_b_t",
                "b_limit_t",
                "b_utilization",
                "bpeak_formula",
                "b_definition",
                "ae_used_mm2",
                "vpri_basis_v",
                "fs_basis_hz",
                "flux_audit_ae_used_mm2",
                "flux_audit_ae_source_field",
                "flux_audit_vpri_basis_v",
                "flux_audit_fs_basis_hz",
                "flux_audit_formula_reported_bpeak",
                "flux_audit_reported_bpeak_t",
                "flux_audit_derived_delta_b_t",
                "flux_audit_derived_bpeak_t",
                "flux_audit_current_field_definition",
                "flux_audit_core_loss_b_input_definition",
                "flux_audit_definition",
                "worst_flux_case_name",
                "flux_case_summary",
                "leakage_method",
                "leakage_winding_arrangement",
                "leakage_status",
                "leakage_warning",
                "leakage_height_source",
                "leakage_height_warning",
                "leakage_usable_window_height_mm",
                "leakage_primary_occupied_height_mm",
                "leakage_secondary_occupied_height_mm",
                "leakage_window_area_mm2",
                "leakage_inferred_window_width_mm",
                "leakage_effective_height_mm",
                "leakage_primary_radial_build_mm",
                "leakage_secondary_radial_build_mm",
                "leakage_insulation_gap_mm",
                "leakage_used_legacy_fallback",
                "fill_factor",
                "fill_limit",
                "primary_fill_area_mm2",
                "secondary_fill_area_mm2",
                "insulation_reserved_area_mm2",
                "total_fill_area_mm2",
                "primary_wire_id",
                "primary_parallel",
                "primary_current_density",
                "secondary_wire_id",
                "secondary_parallel",
                "secondary_current_density",
                "primary_copper_loss_w",
                "secondary_copper_loss_w",
                "core_loss_w",
                "total_loss_w",
                "hotspot_c",
                "warnings",
                "notes",
                "rejection_reasons",
            ],
        )
        writer.writeheader()
        for candidate in candidates:
            primary = candidate.primary_winding
            secondary = candidate.secondary_winding
            audit = candidate.flux_density_audit
            primary_loss = primary.copper_loss_w if primary else 0.0
            secondary_loss = secondary.copper_loss_w if secondary else 0.0
            writer.writerow(
                {
                    "candidate_id": candidate.candidate_id,
                    "core_id": candidate.core_id,
                    "material_id": candidate.material_id,
                    "ae_mm2": candidate.ae_mm2,
                    "le_mm": candidate.le_mm,
                    "ve_cm3": candidate.ve_cm3,
                    "window_area_mm2": candidate.window_area_mm2,
                    "estimated_volume_cm3": candidate.estimated_volume_cm3,
                    "np": candidate.np,
                    "ns": candidate.ns,
                    "gap_mm": candidate.gap_m * 1e3,
                    "lm_target_uH": candidate.lm_target_h * 1e6,
                    "lm_actual_uH": candidate.lm_actual_h * 1e6,
                    "lm_error_percent": candidate.lm_error_percent,
                    "estimated_lk_uH": candidate.estimated_lk_uH,
                    "lr_target_uH": candidate.lr_target_h * 1e6,
                    "lk_over_lr": candidate.lk_over_lr,
                    "lk_over_lr_percent": candidate.lk_over_lr_percent,
                    "max_b_peak_t": candidate.max_b_peak_t,
                    "max_delta_b_t": candidate.max_delta_b_t,
                    "bpeak_t": candidate.max_b_peak_t,
                    "delta_b_t": candidate.max_delta_b_t,
                    "b_limit_t": candidate.b_limit_t,
                    "b_utilization": candidate.max_b_peak_t / candidate.b_limit_t if candidate.b_limit_t > 0.0 else "",
                    "bpeak_formula": audit.formula_reported_bpeak if audit else "legacy transformer flux field",
                    "b_definition": audit.current_field_definition if audit else "unknown",
                    "ae_used_mm2": audit.ae_used_mm2 if audit else candidate.ae_mm2,
                    "vpri_basis_v": audit.vpri_basis_v if audit else "",
                    "fs_basis_hz": audit.fs_basis_hz if audit else candidate.frequency_basis_hz or "",
                    "flux_audit_ae_used_mm2": audit.ae_used_mm2 if audit else "",
                    "flux_audit_ae_source_field": audit.ae_source_field if audit else "",
                    "flux_audit_vpri_basis_v": audit.vpri_basis_v if audit else "",
                    "flux_audit_fs_basis_hz": audit.fs_basis_hz if audit else "",
                    "flux_audit_formula_reported_bpeak": audit.formula_reported_bpeak if audit else "",
                    "flux_audit_reported_bpeak_t": audit.reported_bpeak_t if audit else "",
                    "flux_audit_derived_delta_b_t": audit.derived_delta_b_t if audit else "",
                    "flux_audit_derived_bpeak_t": audit.derived_bpeak_t if audit else "",
                    "flux_audit_current_field_definition": audit.current_field_definition if audit else "",
                    "flux_audit_core_loss_b_input_definition": audit.core_loss_b_input_definition if audit else "",
                    "flux_audit_definition": audit.definition if audit else "",
                    "worst_flux_case_name": candidate.worst_flux_case_name,
                    "flux_case_summary": _flux_case_summary(candidate.boundary_flux_cases),
                    "leakage_method": candidate.leakage_method,
                    "leakage_winding_arrangement": candidate.leakage_winding_arrangement,
                    "leakage_status": candidate.leakage_status,
                    "leakage_warning": candidate.leakage_warning,
                    "leakage_height_source": candidate.leakage_height_source,
                    "leakage_height_warning": candidate.leakage_height_warning,
                    "leakage_usable_window_height_mm": candidate.leakage_usable_window_height_mm,
                    "leakage_primary_occupied_height_mm": candidate.leakage_primary_occupied_height_mm,
                    "leakage_secondary_occupied_height_mm": candidate.leakage_secondary_occupied_height_mm,
                    "leakage_window_area_mm2": candidate.leakage_window_area_mm2,
                    "leakage_inferred_window_width_mm": candidate.leakage_inferred_window_width_mm,
                    "leakage_effective_height_mm": candidate.leakage_effective_height_mm,
                    "leakage_primary_radial_build_mm": candidate.leakage_primary_radial_build_mm,
                    "leakage_secondary_radial_build_mm": candidate.leakage_secondary_radial_build_mm,
                    "leakage_insulation_gap_mm": candidate.leakage_insulation_gap_mm,
                    "leakage_used_legacy_fallback": candidate.leakage_used_legacy_fallback,
                    "fill_factor": candidate.fill_factor,
                    "fill_limit": candidate.fill_limit,
                    "primary_fill_area_mm2": candidate.primary_fill_area_m2 * 1e6,
                    "secondary_fill_area_mm2": candidate.secondary_fill_area_m2 * 1e6,
                    "insulation_reserved_area_mm2": candidate.insulation_reserved_area_m2 * 1e6,
                    "total_fill_area_mm2": candidate.total_fill_area_m2 * 1e6,
                    "primary_wire_id": primary.selected_wire_id if primary else "",
                    "primary_parallel": primary.strands_or_parallel if primary else "",
                    "primary_current_density": primary.current_density_a_per_mm2 if primary else "",
                    "secondary_wire_id": secondary.selected_wire_id if secondary else "",
                    "secondary_parallel": secondary.strands_or_parallel if secondary else "",
                    "secondary_current_density": secondary.current_density_a_per_mm2 if secondary else "",
                    "primary_copper_loss_w": primary_loss,
                    "secondary_copper_loss_w": secondary_loss,
                    "core_loss_w": candidate.core_loss_w,
                    "total_loss_w": candidate.total_loss_w,
                    "hotspot_c": candidate.hotspot_c,
                    "warnings": ";".join(candidate.warnings),
                    "notes": ";".join(candidate.notes),
                    "rejection_reasons": ";".join(candidate.rejection_reasons),
                }
            )
    return [str(output_path)]


def export_llc_transformer_leakage_rejection_audit(
    candidates: Iterable[LLCTransformerScreeningCandidate],
    output_dir: Path | None = None,
) -> list[str]:
    audit = _leakage_rejection_audit(list(candidates))
    output_root = Path(output_dir or _project_root() / "outputs" / "transformer_design")
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / "llc_transformer_leakage_rejection_audit.csv"
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "metric",
            "value",
            "finite_lk_over_lr_count",
            "non_finite_or_missing_lk_over_lr_count",
            "fallback_leakage_count",
            "layer_based_leakage_count",
            "unexpected_leakage_rejects_below_threshold",
            "invalid_leakage_diagnostics_count",
            "rejected_by_leakage",
            "height_source_counts",
            "leakage_status_counts",
            "lk_over_lr_percent_min",
            "lk_over_lr_percent_p25",
            "lk_over_lr_percent_median",
            "lk_over_lr_percent_p75",
            "lk_over_lr_percent_p90",
            "lk_over_lr_percent_p95",
            "lk_over_lr_percent_max",
            "leakage_effective_height_mm_min",
            "leakage_effective_height_mm_median",
            "leakage_effective_height_mm_max",
            "estimated_lk_uH_min",
            "estimated_lk_uH_median",
            "estimated_lk_uH_max",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        row = {
            "metric": "leakage_rejection_audit",
            "value": audit["rejected_by_leakage"],
            "finite_lk_over_lr_count": audit["finite_lk_over_lr_count"],
            "non_finite_or_missing_lk_over_lr_count": audit["non_finite_or_missing_lk_over_lr_count"],
            "fallback_leakage_count": audit["fallback_leakage_count"],
            "layer_based_leakage_count": audit["layer_based_leakage_count"],
            "unexpected_leakage_rejects_below_threshold": audit["unexpected_leakage_rejects_below_threshold"],
            "invalid_leakage_diagnostics_count": audit["invalid_leakage_diagnostics_count"],
            "rejected_by_leakage": audit["rejected_by_leakage"],
            "height_source_counts": ";".join(f"{key}={value}" for key, value in sorted(audit["height_source_counts"].items())),
            "leakage_status_counts": ";".join(f"{key}={value}" for key, value in sorted(audit["leakage_status_counts"].items())),
            "lk_over_lr_percent_min": audit["lk_over_lr_percent_stats"]["min"],
            "lk_over_lr_percent_p25": audit["lk_over_lr_percent_stats"]["p25"],
            "lk_over_lr_percent_median": audit["lk_over_lr_percent_stats"]["median"],
            "lk_over_lr_percent_p75": audit["lk_over_lr_percent_stats"]["p75"],
            "lk_over_lr_percent_p90": audit["lk_over_lr_percent_stats"]["p90"],
            "lk_over_lr_percent_p95": audit["lk_over_lr_percent_stats"]["p95"],
            "lk_over_lr_percent_max": audit["lk_over_lr_percent_stats"]["max"],
            "leakage_effective_height_mm_min": audit["leakage_effective_height_mm_stats"]["min"],
            "leakage_effective_height_mm_median": audit["leakage_effective_height_mm_stats"]["median"],
            "leakage_effective_height_mm_max": audit["leakage_effective_height_mm_stats"]["max"],
            "estimated_lk_uH_min": audit["estimated_lk_uH_stats"]["min"],
            "estimated_lk_uH_median": audit["estimated_lk_uH_stats"]["median"],
            "estimated_lk_uH_max": audit["estimated_lk_uH_stats"]["max"],
        }
        writer.writerow(row)
    return [str(output_path)]


def build_llc_transformer_pareto_result(
    feasible_candidates: Iterable[LLCTransformerScreeningCandidate],
    *,
    output_dir: Path | None = None,
    write_artifacts: bool = False,
) -> LLCTransformerParetoResult:
    """Build first-pass transformer Pareto front and representative selections."""

    feasible = sorted(
        [candidate for candidate in feasible_candidates if candidate.feasible],
        key=lambda candidate: (candidate.estimated_volume_m3, candidate.total_loss_w, candidate.candidate_id),
    )
    pareto = build_llc_transformer_pareto_front(feasible)
    representatives = select_llc_transformer_representatives(pareto)
    recommended_selection = representatives.get("recommended")
    recommended = recommended_selection.candidate if recommended_selection is not None else None
    chosen = [
        representatives[role]
        for role in ("recommended", "min-volume", "min-loss", "compromise")
        if role in representatives
    ]
    artifact_paths: list[str] = []
    plot_diagnostics: dict[str, object] = {}
    if write_artifacts:
        artifact_paths, plot_diagnostics = export_llc_transformer_pareto_artifacts(
            feasible_candidates=feasible,
            pareto_candidates=pareto,
            chosen_candidates=chosen,
            output_dir=output_dir,
        )
    return LLCTransformerParetoResult(
        feasible_candidates=feasible,
        pareto_candidates=pareto,
        chosen_candidates=chosen,
        representative_by_role=representatives,
        recommended_candidate=recommended,
        recommended_policy="recommended from transformer Pareto compromise using normalized volume-loss distance.",
        artifact_paths=artifact_paths,
        plot_diagnostics=plot_diagnostics,
        notes=[
            "Transformer Pareto front minimizes estimated transformer volume and total transformer loss.",
            "This is first-pass separated-transformer screening.",
            "Transformer realizes Np:Ns and Lm; external resonant inductor realizes Lr.",
            "Leakage is first-pass estimated and checked only; it is not designed as Lr.",
            "The PNG may hide extreme feasible outliers for readability; CSV artifacts remain complete.",
            "Detailed winding-stack geometry, detailed leakage model, isolation/creepage/clearance checks, and final optimization are not implemented.",
        ],
        warnings=[],
    )


def build_llc_transformer_pareto_front(
    candidates: Iterable[LLCTransformerScreeningCandidate],
) -> list[LLCTransformerScreeningCandidate]:
    """Return nondominated transformer candidates by volume and total loss."""

    feasible = [candidate for candidate in candidates if candidate.feasible]
    pareto: list[LLCTransformerScreeningCandidate] = []
    for candidate in feasible:
        dominated = False
        for other in feasible:
            if other.candidate_id == candidate.candidate_id:
                continue
            no_worse = (
                other.estimated_volume_m3 <= candidate.estimated_volume_m3
                and other.total_loss_w <= candidate.total_loss_w
            )
            strictly_better = (
                other.estimated_volume_m3 < candidate.estimated_volume_m3
                or other.total_loss_w < candidate.total_loss_w
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            pareto.append(candidate)
    return sorted(pareto, key=lambda item: (item.estimated_volume_m3, item.total_loss_w, item.candidate_id))


def select_llc_transformer_representatives(
    pareto_candidates: Iterable[LLCTransformerScreeningCandidate],
) -> dict[str, LLCTransformerRepresentativeSelection]:
    """Select deterministic transformer Pareto representatives."""

    pareto = list(pareto_candidates)
    if not pareto:
        return {}
    min_volume = min(
        pareto,
        key=lambda candidate: (candidate.estimated_volume_m3, candidate.total_loss_w, candidate.hotspot_c, candidate.fill_factor, candidate.candidate_id),
    )
    min_loss = min(
        pareto,
        key=lambda candidate: (candidate.total_loss_w, candidate.estimated_volume_m3, candidate.hotspot_c, candidate.fill_factor, candidate.candidate_id),
    )
    volume_values = [candidate.estimated_volume_m3 for candidate in pareto]
    loss_values = [candidate.total_loss_w for candidate in pareto]
    min_volume_value = min(volume_values)
    max_volume_value = max(volume_values)
    min_loss_value = min(loss_values)
    max_loss_value = max(loss_values)

    def _normalized_score(candidate: LLCTransformerScreeningCandidate) -> tuple[float, float, float, str]:
        volume_span = max(max_volume_value - min_volume_value, 1e-18)
        loss_span = max(max_loss_value - min_loss_value, 1e-18)
        normalized_volume = (candidate.estimated_volume_m3 - min_volume_value) / volume_span
        normalized_loss = (candidate.total_loss_w - min_loss_value) / loss_span
        score = sqrt(normalized_volume**2 + normalized_loss**2)
        return (score, candidate.hotspot_c, candidate.fill_factor, candidate.candidate_id)

    compromise = min(pareto, key=_normalized_score)
    return {
        "recommended": LLCTransformerRepresentativeSelection(
            role="recommended",
            candidate=compromise,
            reason="recommended from transformer Pareto compromise using normalized volume-loss distance.",
        ),
        "min-volume": LLCTransformerRepresentativeSelection(
            role="min-volume",
            candidate=min_volume,
            reason="minimum estimated transformer volume on Pareto front; ties use lower loss, hotspot, and fill factor.",
        ),
        "min-loss": LLCTransformerRepresentativeSelection(
            role="min-loss",
            candidate=min_loss,
            reason="minimum total transformer loss on Pareto front; ties use lower volume, hotspot, and fill factor.",
        ),
        "compromise": LLCTransformerRepresentativeSelection(
            role="compromise",
            candidate=compromise,
            reason="closest Pareto candidate to normalized volume-loss ideal point.",
        ),
    }


def export_llc_transformer_pareto_artifacts(
    *,
    feasible_candidates: Iterable[LLCTransformerScreeningCandidate],
    pareto_candidates: Iterable[LLCTransformerScreeningCandidate],
    chosen_candidates: Iterable[LLCTransformerRepresentativeSelection],
    output_dir: Path | None = None,
) -> tuple[list[str], dict[str, object]]:
    """Write transformer Pareto CSV and PNG artifacts under outputs/transformer_design."""

    output_root = Path(output_dir or _project_root() / "outputs" / "transformer_design")
    output_root.mkdir(parents=True, exist_ok=True)
    feasible = list(feasible_candidates)
    pareto = list(pareto_candidates)
    chosen = list(chosen_candidates)
    paths: list[str] = []

    feasible_paths = export_llc_transformer_feasible_candidates(feasible, output_dir=output_root)
    paths.extend(feasible_paths)

    pareto_csv = output_root / "llc_transformer_pareto_front.csv"
    _write_transformer_candidate_csv(pareto_csv, pareto)
    paths.append(str(pareto_csv))

    chosen_csv = output_root / "llc_transformer_chosen_candidates.csv"
    _write_transformer_chosen_csv(chosen_csv, chosen)
    paths.append(str(chosen_csv))

    png_path = output_root / "llc_transformer_pareto_front.png"
    plot_data = build_transformer_pareto_plot_data(feasible, pareto, chosen)
    _write_transformer_pareto_png(png_path, plot_data)
    paths.append(str(png_path))
    return paths, plot_data["diagnostics"]


def _write_transformer_candidate_csv(
    path: Path,
    candidates: Iterable[LLCTransformerScreeningCandidate],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_transformer_candidate_csv_fields())
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(_transformer_candidate_csv_row(candidate))


def _write_transformer_chosen_csv(
    path: Path,
    chosen_candidates: Iterable[LLCTransformerRepresentativeSelection],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["role", "selection_reason", *_transformer_candidate_csv_fields()]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for selection in chosen_candidates:
            row = _transformer_candidate_csv_row(selection.candidate)
            writer.writerow({"role": selection.role, "selection_reason": selection.reason, **row})


def _transformer_candidate_csv_fields() -> list[str]:
    return [
        "candidate_id",
        "core_id",
        "material_id",
        "np",
        "ns",
        "gap_mm",
        "lm_target_uH",
        "lm_actual_uH",
        "lm_error_percent",
        "estimated_lk_uH",
        "lr_target_uH",
        "lk_over_lr",
        "lk_over_lr_percent",
        "leakage_method",
        "leakage_winding_arrangement",
        "leakage_status",
        "leakage_warning",
        "leakage_height_source",
        "leakage_height_warning",
        "leakage_usable_window_height_mm",
        "leakage_primary_occupied_height_mm",
        "leakage_secondary_occupied_height_mm",
        "leakage_window_area_mm2",
        "leakage_inferred_window_width_mm",
        "leakage_effective_height_mm",
        "leakage_primary_radial_build_mm",
        "leakage_secondary_radial_build_mm",
        "leakage_insulation_gap_mm",
        "leakage_used_legacy_fallback",
        "max_b_peak_t",
        "max_delta_b_t",
        "bpeak_t",
        "delta_b_t",
        "b_limit_t",
        "b_utilization",
        "bpeak_formula",
        "b_definition",
        "ae_used_mm2",
        "vpri_basis_v",
        "fs_basis_hz",
        "flux_audit_transformer_design_id",
        "flux_audit_ae_used_mm2",
        "flux_audit_ae_source_field",
        "flux_audit_vpri_basis_v",
        "flux_audit_voltage_basis_label",
        "flux_audit_fs_basis_hz",
        "flux_audit_formula_reported_bpeak",
        "flux_audit_reported_bpeak_t",
        "flux_audit_derived_delta_b_t",
        "flux_audit_derived_bpeak_t",
        "flux_audit_b_limit_t",
        "flux_audit_b_utilization",
        "flux_audit_b_margin_percent",
        "flux_audit_current_field_definition",
        "flux_audit_core_loss_b_input_definition",
        "flux_audit_definition",
        "flux_audit_warnings",
        "worst_flux_case_name",
        "fill_factor",
        "primary_copper_loss_w",
        "secondary_copper_loss_w",
        "core_loss_w",
        "total_loss_w",
        "hotspot_c",
        "estimated_volume_cm3",
        "rejection_reasons",
    ]


def _transformer_candidate_csv_row(candidate: LLCTransformerScreeningCandidate) -> dict[str, object]:
    primary_loss = candidate.primary_winding.copper_loss_w if candidate.primary_winding else 0.0
    secondary_loss = candidate.secondary_winding.copper_loss_w if candidate.secondary_winding else 0.0
    audit = candidate.flux_density_audit
    return {
        "candidate_id": candidate.candidate_id,
        "core_id": candidate.core_id,
        "material_id": candidate.material_id,
        "np": candidate.np,
        "ns": candidate.ns,
        "gap_mm": candidate.gap_m * 1e3,
        "lm_target_uH": candidate.lm_target_h * 1e6,
        "lm_actual_uH": candidate.lm_actual_h * 1e6,
        "lm_error_percent": candidate.lm_error_percent,
        "estimated_lk_uH": candidate.estimated_lk_h * 1e6,
        "lr_target_uH": candidate.lr_target_h * 1e6,
        "lk_over_lr": candidate.lk_over_lr,
        "lk_over_lr_percent": candidate.lk_over_lr_percent,
        "leakage_method": candidate.leakage_method,
        "leakage_winding_arrangement": candidate.leakage_winding_arrangement,
        "leakage_status": candidate.leakage_status,
        "leakage_warning": candidate.leakage_warning,
        "leakage_height_source": candidate.leakage_height_source,
        "leakage_height_warning": candidate.leakage_height_warning,
        "leakage_usable_window_height_mm": candidate.leakage_usable_window_height_mm,
        "leakage_primary_occupied_height_mm": candidate.leakage_primary_occupied_height_mm,
        "leakage_secondary_occupied_height_mm": candidate.leakage_secondary_occupied_height_mm,
        "leakage_window_area_mm2": candidate.leakage_window_area_mm2,
        "leakage_inferred_window_width_mm": candidate.leakage_inferred_window_width_mm,
        "leakage_effective_height_mm": candidate.leakage_effective_height_mm,
        "leakage_primary_radial_build_mm": candidate.leakage_primary_radial_build_mm,
        "leakage_secondary_radial_build_mm": candidate.leakage_secondary_radial_build_mm,
        "leakage_insulation_gap_mm": candidate.leakage_insulation_gap_mm,
        "leakage_used_legacy_fallback": candidate.leakage_used_legacy_fallback,
        "max_b_peak_t": candidate.max_b_peak_t,
        "max_delta_b_t": candidate.max_delta_b_t,
        "bpeak_t": candidate.max_b_peak_t,
        "delta_b_t": candidate.max_delta_b_t,
        "b_limit_t": candidate.b_limit_t,
        "b_utilization": candidate.max_b_peak_t / candidate.b_limit_t if candidate.b_limit_t > 0.0 else "",
        "bpeak_formula": audit.formula_reported_bpeak if audit else "legacy transformer flux field",
        "b_definition": audit.current_field_definition if audit else "unknown",
        "ae_used_mm2": audit.ae_used_mm2 if audit else candidate.ae_mm2,
        "vpri_basis_v": audit.vpri_basis_v if audit else "",
        "fs_basis_hz": audit.fs_basis_hz if audit else candidate.frequency_basis_hz or "",
        "flux_audit_transformer_design_id": audit.transformer_design_id if audit else "",
        "flux_audit_ae_used_mm2": audit.ae_used_mm2 if audit else "",
        "flux_audit_ae_source_field": audit.ae_source_field if audit else "",
        "flux_audit_vpri_basis_v": audit.vpri_basis_v if audit else "",
        "flux_audit_voltage_basis_label": audit.voltage_basis_label if audit else "",
        "flux_audit_fs_basis_hz": audit.fs_basis_hz if audit else "",
        "flux_audit_formula_reported_bpeak": audit.formula_reported_bpeak if audit else "",
        "flux_audit_reported_bpeak_t": audit.reported_bpeak_t if audit else "",
        "flux_audit_derived_delta_b_t": audit.derived_delta_b_t if audit else "",
        "flux_audit_derived_bpeak_t": audit.derived_bpeak_t if audit else "",
        "flux_audit_b_limit_t": audit.b_limit_t if audit else "",
        "flux_audit_b_utilization": audit.b_utilization if audit else "",
        "flux_audit_b_margin_percent": audit.b_margin_percent if audit else "",
        "flux_audit_current_field_definition": audit.current_field_definition if audit else "",
        "flux_audit_core_loss_b_input_definition": audit.core_loss_b_input_definition if audit else "",
        "flux_audit_definition": audit.definition if audit else "",
        "flux_audit_warnings": ";".join(audit.warnings) if audit else "",
        "worst_flux_case_name": candidate.worst_flux_case_name,
        "fill_factor": candidate.fill_factor,
        "primary_copper_loss_w": primary_loss,
        "secondary_copper_loss_w": secondary_loss,
        "core_loss_w": candidate.core_loss_w,
        "total_loss_w": candidate.total_loss_w,
        "hotspot_c": candidate.hotspot_c,
        "estimated_volume_cm3": candidate.estimated_volume_cm3,
        "rejection_reasons": ";".join(candidate.rejection_reasons),
    }


def build_transformer_pareto_plot_data(
    feasible_candidates: Iterable[LLCTransformerScreeningCandidate],
    pareto_candidates: Iterable[LLCTransformerScreeningCandidate],
    chosen_candidates: Iterable[LLCTransformerRepresentativeSelection],
    *,
    volume_plot_percentile: float = 98.0,
    loss_plot_percentile: float = 98.0,
) -> dict[str, object]:
    """Build plot-only filtered Transformer PF data without changing CSV contents."""

    feasible = list(feasible_candidates)
    pareto = list(pareto_candidates)
    chosen = list(chosen_candidates)
    chosen_ids = {selection.candidate.candidate_id for selection in chosen}
    pareto_ids = {candidate.candidate_id for candidate in pareto}
    forced_ids = pareto_ids | chosen_ids
    representative_labels: dict[str, str] = {}
    for selection in chosen:
        representative_labels.setdefault(selection.candidate.candidate_id, "")
        existing = representative_labels[selection.candidate.candidate_id]
        representative_labels[selection.candidate.candidate_id] = (
            f"{existing} / {selection.role}" if existing else selection.role
        )

    if feasible:
        volume_limit = _percentile([candidate.estimated_volume_cm3 for candidate in feasible], volume_plot_percentile)
        loss_limit = _percentile([candidate.total_loss_w for candidate in feasible], loss_plot_percentile)
        chosen_volumes = [
            selection.candidate.estimated_volume_cm3
            for selection in chosen
            if selection.candidate.estimated_volume_cm3 > 0.0
        ]
        chosen_losses = [
            selection.candidate.total_loss_w
            for selection in chosen
            if selection.candidate.total_loss_w > 0.0
        ]
        if chosen_volumes:
            volume_limit = max(volume_limit, max(chosen_volumes) * 1.25)
        if chosen_losses:
            loss_limit = max(loss_limit, max(chosen_losses) * 1.25)
    else:
        volume_limit = 0.0
        loss_limit = 0.0

    visible_background = [
        candidate
        for candidate in feasible
        if candidate.candidate_id in forced_ids
        or (candidate.estimated_volume_cm3 <= volume_limit and candidate.total_loss_w <= loss_limit)
    ]
    hidden_background = [
        candidate
        for candidate in feasible
        if candidate.candidate_id not in {item.candidate_id for item in visible_background}
    ]
    diagnostics = {
        "plotted_feasible_background_points": len(visible_background),
        "hidden_feasible_outliers_in_png_only": len(hidden_background),
        "volume_plot_limit_cm3": volume_limit,
        "loss_plot_limit_w": loss_limit,
        "full_feasible_csv_remains_unfiltered": True,
        "pareto_chosen_candidates_are_always_plotted": True,
        "visible_candidate_ids": [candidate.candidate_id for candidate in visible_background],
        "forced_candidate_ids": sorted(forced_ids),
        "representative_plot_labels": representative_labels,
        "volume_plot_percentile": volume_plot_percentile,
        "loss_plot_percentile": loss_plot_percentile,
    }
    return {
        "visible_feasible_candidates": visible_background,
        "hidden_feasible_candidates": hidden_background,
        "pareto_candidates": pareto,
        "chosen_candidates": chosen,
        "diagnostics": diagnostics,
    }


def _write_transformer_pareto_png(
    path: Path,
    plot_data: dict[str, object],
) -> None:
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except Exception:
        return
    feasible_candidates = list(plot_data.get("visible_feasible_candidates", []))
    pareto_candidates = list(plot_data.get("pareto_candidates", []))
    chosen_candidates = list(plot_data.get("chosen_candidates", []))
    figure = Figure(figsize=(8.4, 5.3), dpi=130)
    axis = figure.add_subplot(111)
    if feasible_candidates:
        axis.scatter(
            [candidate.estimated_volume_cm3 for candidate in feasible_candidates],
            [candidate.total_loss_w for candidate in feasible_candidates],
            s=9,
            alpha=0.18,
            label="feasible",
            color="#718096",
            linewidths=0,
        )
    if pareto_candidates:
        pareto_sorted = sorted(pareto_candidates, key=lambda candidate: candidate.estimated_volume_cm3)
        axis.plot(
            [candidate.estimated_volume_cm3 for candidate in pareto_sorted],
            [candidate.total_loss_w for candidate in pareto_sorted],
            marker="o",
            linewidth=1.8,
            label="Pareto",
            color="#1f77b4",
            zorder=4,
        )
    role_markers = {
        "recommended": ("*", "#d62728"),
        "min-volume": ("s", "#2ca02c"),
        "min-loss": ("^", "#9467bd"),
        "compromise": ("D", "#ff7f0e"),
    }
    role_offsets = {
        "recommended": (12, 14),
        "min-volume": (-78, 14),
        "min-loss": (12, -20),
        "compromise": (-88, -24),
    }
    candidate_roles: dict[str, list[LLCTransformerRepresentativeSelection]] = {}
    for selection in chosen_candidates:
        candidate_roles.setdefault(selection.candidate.candidate_id, []).append(selection)
    for selections in candidate_roles.values():
        selection = selections[0]
        roles = [item.role for item in selections]
        label = " / ".join(roles)
        marker, color = role_markers.get(selection.role, ("o", "#000000"))
        candidate = selection.candidate
        axis.scatter(
            [candidate.estimated_volume_cm3],
            [candidate.total_loss_w],
            marker=marker,
            s=130 if "recommended" in roles else 70,
            color=color,
            label=label,
            zorder=5,
            edgecolors="#1a202c",
            linewidths=0.6,
        )
        offset = role_offsets.get(selection.role, (8, 8))
        axis.annotate(
            label,
            (candidate.estimated_volume_cm3, candidate.total_loss_w),
            textcoords="offset points",
            xytext=offset,
            fontsize=8,
            arrowprops={"arrowstyle": "-", "color": "#4a5568", "lw": 0.6},
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#cbd5e0", "alpha": 0.86},
            zorder=6,
        )
    visible_for_limits = [*feasible_candidates, *pareto_candidates, *(selection.candidate for selection in chosen_candidates)]
    _apply_plot_limits(axis, visible_for_limits)
    axis.set_title("LLC separated transformer Pareto front")
    axis.set_xlabel("Estimated transformer volume [cm^3]")
    axis.set_ylabel("Total transformer loss [W]")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="upper right", fontsize=8)
    figure.tight_layout()
    canvas = FigureCanvasAgg(figure)
    canvas.print_png(path)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    clamped = min(max(percentile, 0.0), 100.0)
    position = (len(ordered) - 1) * clamped / 100.0
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _apply_plot_limits(axis, candidates: list[LLCTransformerScreeningCandidate]) -> None:
    if not candidates:
        return
    volumes = [candidate.estimated_volume_cm3 for candidate in candidates if candidate.estimated_volume_cm3 >= 0.0]
    losses = [candidate.total_loss_w for candidate in candidates if candidate.total_loss_w >= 0.0]
    if not volumes or not losses:
        return
    min_volume, max_volume = min(volumes), max(volumes)
    min_loss, max_loss = min(losses), max(losses)
    volume_span = max(max_volume - min_volume, max(max_volume, 1.0) * 0.08)
    loss_span = max(max_loss - min_loss, max(max_loss, 1.0) * 0.08)
    axis.set_xlim(max(0.0, min_volume - volume_span * 0.08), max_volume + volume_span * 0.12)
    axis.set_ylim(max(0.0, min_loss - loss_span * 0.10), max_loss + loss_span * 0.16)


def _flux_case_summary(cases: list[LLCTransformerBoundaryFluxCase]) -> str:
    parts = []
    for case in cases:
        status = "PASS" if case.pass_b_limit else "FAIL"
        parts.append(
            "{"
            f"name={case.case_name},"
            f"Vin={case.vin_v:.6g},"
            f"Vout={case.vout_v:.6g},"
            f"Pout={case.pout_w:.6g},"
            f"fs={case.fs_hz:.6g},"
            f"fs_source={case.fs_source},"
            f"Vpri={case.primary_voltage_v:.6g},"
            f"Np={case.np},"
            f"Ae={case.ae_m2:.6g},"
            f"delta_B={case.delta_b_t:.6g},"
            f"Bpeak={case.b_peak_t:.6g},"
            f"status={status}"
            "}"
        )
    return ";".join(parts)


def build_transformer_design_inputs_from_fha(design: object) -> LLCTransformerDesignInputs:
    """Build separated-transformer input targets from an existing LLC FHA design object."""

    primary_rms_a = _read_float_from_mapping(
        getattr(design, "worst_case_current_stress", {}),
        "resonant_tank_rms_a",
        _read_float_from_mapping(getattr(design, "current_estimates_nominal_full_load", {}), "ir_rms_a", 0.0),
    )
    primary_peak_a = _read_float_from_mapping(
        getattr(design, "worst_case_current_stress", {}),
        "resonant_tank_peak_a",
        _read_float_from_mapping(getattr(design, "current_estimates_nominal_full_load", {}), "ir_peak_a", 0.0),
    )
    reflected_load_rms_a = _max_reflected_load_current_rms(design)
    secondary_rms_a = float(getattr(design, "turns_ratio")) * reflected_load_rms_a
    secondary_peak_a = sqrt(2.0) * secondary_rms_a
    return LLCTransformerDesignInputs(
        vin_min_v=float(getattr(design, "vin_min_v")),
        vin_nom_v=float(getattr(design, "vin_nom_v")),
        vin_max_v=float(getattr(design, "vin_max_v")),
        vout_min_v=float(getattr(design, "vout_min_v")),
        vout_nom_v=float(getattr(design, "vout_nom_v")),
        vout_max_v=float(getattr(design, "vout_max_v")),
        pout_max_w=float(getattr(design, "pout_max_w")),
        fs_min_hz=float(getattr(design, "fs_min_hz")),
        fs_nom_hz=float(getattr(design, "fr_hz")),
        fs_max_hz=float(getattr(design, "fs_max_hz")),
        primary_bridge_type=str(getattr(design, "primary_bridge_type")),
        secondary_rectifier_type=str(getattr(design, "secondary_rectifier_type")),
        primary_bridge_gain_factor=float(getattr(design, "primary_bridge_gain_factor")),
        transformer_ratio_np=int(getattr(design, "np_turns")),
        transformer_ratio_ns=int(getattr(design, "ns_turns")),
        turns_ratio_n=float(getattr(design, "turns_ratio")),
        lr_target_h=float(getattr(design, "lr_h")),
        lm_target_h=float(getattr(design, "lm_h")),
        ln=float(getattr(design, "ln")),
        q_nom=float(getattr(design, "q_nom")),
        primary_current_rms_a=primary_rms_a,
        primary_current_peak_a=primary_peak_a,
        secondary_current_rms_a=secondary_rms_a,
        secondary_current_peak_a=secondary_peak_a,
        ideal_turns_ratio=float(getattr(design, "ideal_turns_ratio")),
        turns_ratio_tolerance_percent=float(getattr(design, "turns_ratio_tolerance_percent", 5.0)),
        b_limit_t=0.18,
        lm_tolerance_percent=10.0,
        leakage_fraction_estimate=0.02,
        leakage_limit_h=float(getattr(design, "lr_h")),
    )


def build_transformer_design_target_metadata(design: object) -> dict[str, object]:
    """Build compact runtime metadata for the separated LLC transformer target."""

    inputs = build_transformer_design_inputs_from_fha(design)
    boundary_case_names = [case_name for case_name, _, _ in BOUNDARY_SATURATION_CASES]
    return {
        "design_type": "separated_transformer",
        "transformer_realizes": "integer turns ratio and magnetizing inductance Lm",
        "external_resonant_inductor_realizes": "resonant inductance Lr",
        "base_np": inputs.transformer_ratio_np,
        "base_ns": inputs.transformer_ratio_ns,
        "turns_ratio_n": inputs.turns_ratio_n,
        "ideal_turns_ratio": inputs.ideal_turns_ratio,
        "turns_ratio_error_percent": float(getattr(design, "turns_ratio_error")) * 100.0,
        "turns_ratio_tolerance_percent": inputs.turns_ratio_tolerance_percent,
        "turns_ratio_within_tolerance": bool(getattr(design, "turns_ratio_within_tolerance", True)),
        "lm_target_h": inputs.lm_target_h,
        "lr_target_h": inputs.lr_target_h,
        "fs_min_hz": inputs.fs_min_hz,
        "fr_hz": inputs.fs_nom_hz,
        "fs_max_hz": inputs.fs_max_hz,
        "primary_bridge_type": inputs.primary_bridge_type,
        "secondary_rectifier_type": inputs.secondary_rectifier_type,
        "primary_bridge_gain_factor": inputs.primary_bridge_gain_factor,
        "b_limit_t": inputs.b_limit_t,
        "lm_tolerance_percent": inputs.lm_tolerance_percent,
        "leakage_fraction_estimate": inputs.leakage_fraction_estimate,
        "leakage_limit_h": inputs.leakage_limit_h,
        "leakage_requirement": "estimated Llk < Lr_target",
        "boundary_saturation_case_names": boundary_case_names,
        "primary_current_basis": "resonant tank current from LLC FHA worst-case corner when available",
        "primary_current_rms_a": inputs.primary_current_rms_a,
        "primary_current_peak_a": inputs.primary_current_peak_a,
        "secondary_current_basis": "secondary reflected-load current; magnetizing current excluded",
        "secondary_current_rms_a": inputs.secondary_current_rms_a,
        "secondary_current_peak_a": inputs.secondary_current_peak_a,
        "status": "target generated; run magnetics to screen separated transformer candidates",
        "notes": [
            "Separated transformer realizes the integer turns ratio and Lm; external resonant inductor realizes Lr.",
            "Boundary saturation uses four full-load Vin/Vout corners.",
            "Flux relation is Bpeak = Vpri / (4 * Np * Ae * fs) and delta_B = Vpri / (2 * Np * Ae * fs) under symmetric bipolar excitation.",
            "Lm gap estimate is air-gap dominated unless core reluctance data is supplied.",
            "Leakage inductance is a first-pass estimate and is only checked against Lr_target.",
            "Primary winding current uses resonant tank current, not output current.",
            "Secondary winding current excludes magnetizing current.",
            "Packaged-normalized magnetic database screening runs from Run Magnetics, not Run Design.",
        ],
    }


def make_fha_boundary_frequency_solver(design: object) -> FrequencySolver:
    """Build a boundary frequency solver that reuses FHA coverage when present, then solves."""

    coverage = list(getattr(design, "coverage_results", []))

    def _solver(
        inputs: LLCTransformerDesignInputs,
        case_name: str,
        vin_v: float,
        vout_v: float,
        pout_w: float,
    ) -> float:
        for result in coverage:
            if (
                abs(float(getattr(result, "vin_v", float("nan"))) - vin_v) <= 1e-9
                and abs(float(getattr(result, "vout_v", float("nan"))) - vout_v) <= 1e-9
                and abs(float(getattr(result, "pout_w", float("nan"))) - pout_w) <= 1e-9
            ):
                return float(getattr(result, "fs_hz"))
        from .fha_design import solve_operating_frequency

        return float(solve_operating_frequency(design, vin_v, vout_v, pout_w).fs_hz)

    return _solver


def build_llc_external_resonant_inductor_target(
    fha_design: object,
    transformer_candidate: LLCTransformerScreeningCandidate,
) -> LlcExternalResonantInductorTarget:
    """Build the Round-1 external Lr target left after transformer leakage."""

    lr_target_h = float(getattr(fha_design, "lr_h"))
    if lr_target_h <= 0.0:
        raise ValueError("LLC external resonant inductor target requires positive FHA Lr target.")

    transformer_lk_h = float(transformer_candidate.estimated_lk_h)
    external_lr_target_h = lr_target_h - transformer_lk_h
    warning_parts: list[str] = []
    is_design_required = external_lr_target_h > EXTERNAL_LR_TARGET_TOLERANCE_H
    if not is_design_required:
        warning_parts.append(
            "Transformer leakage already meets or exceeds the total Lr target; "
            "separated external Lr design is not required or the separated design assumption should be reviewed."
        )
        if external_lr_target_h < 0.0:
            external_lr_target_h = 0.0
    current_basis, current_rms_a, current_peak_a, fs_basis_hz, frequency_basis, current_warning = (
        _select_external_lr_current_frequency_basis(fha_design)
    )
    if current_warning:
        warning_parts.append(current_warning)

    return LlcExternalResonantInductorTarget(
        lr_target_h=lr_target_h,
        transformer_lk_h=transformer_lk_h,
        external_lr_target_h=external_lr_target_h,
        external_lr_target_uH=external_lr_target_h * 1e6,
        lr_total_target_h=lr_target_h,
        lr_external_fraction=external_lr_target_h / lr_target_h,
        current_basis=current_basis,
        frequency_basis=frequency_basis,
        current_rms_a=current_rms_a,
        current_peak_a=current_peak_a,
        fs_basis_hz=fs_basis_hz,
        fs_min_hz=float(getattr(fha_design, "fs_min_hz")),
        fs_max_hz=float(getattr(fha_design, "fs_max_hz")),
        transformer_design_id=transformer_candidate.candidate_id,
        transformer_leakage_method=transformer_candidate.leakage_method,
        transformer_leakage_status=transformer_candidate.leakage_status,
        warning=" ".join(warning_parts),
        is_design_required=is_design_required,
    )


def generate_llc_external_resonant_inductor_candidates(
    request: LlcExternalResonantInductorTarget,
    core_records: Iterable[object] | None = None,
    material_records: Iterable[object] | None = None,
    wire_records: Iterable[object] | None = None,
    *,
    core_limit: int | None = 18,
    material_limit: int | None = 4,
    wire_limit: int | None = 10,
    write_csv: bool = True,
    output_dir: Path | None = None,
) -> LlcExternalResonantInductorSearchResult:
    """Screen first-pass external Lr inductor candidates using an energy/current model."""

    rejection_counts = _external_lr_rejection_counter()
    warnings: list[str] = []
    notes: list[str] = []
    if request.warning:
        warnings.append(request.warning)
    if not request.is_design_required or request.external_lr_target_h <= EXTERNAL_LR_TARGET_TOLERANCE_H:
        rejection_counts["invalid_target"] += 1
        warning = request.warning or (
            "Transformer leakage already meets or exceeds the total Lr target; separated external Lr design is not required."
        )
        return LlcExternalResonantInductorSearchResult(
            request=request,
            rejection_counts=rejection_counts,
            notes=["External Lr candidate search did not run because no positive external Lr target is required."],
            warnings=_dedupe_text([*warnings, warning]),
        )
    if min(request.current_rms_a, request.current_peak_a, request.fs_basis_hz) <= 0.0:
        rejection_counts["invalid_target"] += 1
        return LlcExternalResonantInductorSearchResult(
            request=request,
            rejection_counts=rejection_counts,
            notes=["External Lr candidate search did not run because current/frequency basis is invalid."],
            warnings=_dedupe_text([*warnings, "External Lr search requires positive Irms, Ipeak, and fs basis."]),
        )

    raw_cores, raw_materials, raw_wires, backend_notes = _resolve_candidate_source_records(
        core_records,
        material_records,
        wire_records,
    )
    notes.extend(backend_notes)
    cores, missing_core_count = _normalize_core_records(raw_cores)
    materials, missing_material_count = _normalize_material_records(raw_materials)
    wires, missing_wire_count = _normalize_wire_records(raw_wires)
    rejection_counts["missing_data"] += missing_core_count + missing_material_count + missing_wire_count

    cores = _select_external_lr_cores(cores, request, core_limit)
    registered_normalized_material_count = len(materials)
    materials_with_frequency_coverage = [
        material
        for material in materials
        if _material_loss_model_covers_frequency(material, request.fs_basis_hz)
    ]
    materials = _limit_records(
        sorted(
            materials_with_frequency_coverage,
            key=lambda item: (-item.b_sat_t, item.material_id),
        ),
        material_limit,
    )
    wires = _select_external_lr_wires(wires, request, wire_limit)
    notes.append(
        "External Lr material prefilter retained "
        f"{len(materials_with_frequency_coverage)} of {registered_normalized_material_count} normalized materials "
        f"with a core-loss model covering {request.fs_basis_hz:.6g} Hz; "
        f"{len(materials)} entered the bounded Bsat-ranked search."
    )
    if not materials:
        warnings.append(
            "No normalized magnetic material has a core-loss model covering the external Lr loss frequency."
        )

    candidates: list[LlcExternalResonantInductorCandidate] = []
    for core in cores:
        for material in materials:
            b_limit_t = _external_lr_b_limit_t(material)
            if b_limit_t <= 0.0:
                rejection_counts["missing_data"] += 1
                continue
            n_min = max(1, ceil(request.external_lr_target_h * request.current_peak_a / (b_limit_t * core.ae_m2)))
            n_max = min(max(n_min + 40, n_min), EXTERNAL_LR_MAX_TURNS_ABSOLUTE)
            for turns in range(n_min, n_max + 1):
                for wire in wires:
                    best_for_wire = _screen_external_lr_wire_options(
                        request=request,
                        core=core,
                        material=material,
                        wire=wire,
                        turns=turns,
                        b_limit_t=b_limit_t,
                    )
                    candidates.append(best_for_wire)
                    if best_for_wire.rejection_reason:
                        _increment_external_lr_rejection(rejection_counts, best_for_wire.rejection_reason)

    feasible = sorted(
        [candidate for candidate in candidates if not candidate.rejection_reason],
        key=lambda candidate: (
            candidate.total_loss_w,
            candidate.estimated_volume_m3,
            candidate.fill_factor,
            candidate.hotspot_c,
            candidate.design_id,
        ),
    )
    pareto = build_llc_external_resonant_inductor_pareto_front(feasible)
    representatives = select_llc_external_resonant_inductor_representatives(pareto)
    chosen = [
        representatives[role]
        for role in ("recommended", "min-volume", "min-loss", "compromise")
        if role in representatives
    ]
    recommended_selection = representatives.get("recommended")
    min_volume_selection = representatives.get("min-volume")
    min_loss_selection = representatives.get("min-loss")
    compromise_selection = representatives.get("compromise")
    recommended = recommended_selection.candidate if recommended_selection is not None else (feasible[0] if feasible else None)
    artifact_paths: list[str] = []
    plot_diagnostics: dict[str, object] = {}
    feasible_csv_path = ""
    pareto_csv_path = ""
    chosen_csv_path = ""
    pareto_png_path = ""
    if write_csv:
        artifact_paths, plot_diagnostics = export_llc_external_resonant_inductor_pareto_artifacts(
            feasible_candidates=feasible,
            pareto_candidates=pareto,
            chosen_candidates=chosen,
            output_dir=output_dir,
        )
        feasible_csv_path = _first_path_named(artifact_paths, "llc_external_resonant_inductor_feasible_candidates.csv")
        pareto_csv_path = _first_path_named(artifact_paths, "llc_external_resonant_inductor_pareto_front.csv")
        chosen_csv_path = _first_path_named(artifact_paths, "llc_external_resonant_inductor_chosen_candidates.csv")
        pareto_png_path = _first_path_named(artifact_paths, "llc_external_resonant_inductor_pareto_front.png")
    notes.extend(
        [
            "External Lr candidate search uses Lr_ext_target = Lr_target - transformer Llk.",
            "Bpeak is computed from B = L * Ipeak / (N * Ae); Buck voltage-second ripple equations are not used.",
            "LLC external Lr Bpeak uses sinusoidal Ipeak, not peak-to-peak ripple current.",
            "Gap uses a high-mu first-pass reluctance approximation because normalized material mu_r is not available.",
            "Core loss requires Steinmetz coefficients; missing-coefficient materials are rejected.",
            "Thermal screening reuses the first-pass volume-proxy lumped estimate.",
            "Actual Lr is a first-pass gap-derived estimate; manufacturing gap tolerance is not modeled.",
        ]
    )
    pareto_notes = [
        "External resonant inductor Pareto front minimizes estimated external Lr inductor volume and total loss.",
        "Recommended external Lr inductor defaults to the Pareto compromise by normalized volume-loss distance.",
        "The PNG may hide extreme feasible outliers for readability; CSV artifacts remain complete.",
        "Actual Lr is a first-pass gap-derived estimate; manufacturing gap tolerance is not modeled.",
    ]
    if not feasible:
        warnings.append("No feasible external resonant inductor candidates were found in the bounded first-pass search.")
    return LlcExternalResonantInductorSearchResult(
        request=request,
        candidates=candidates,
        feasible_candidates=feasible,
        pareto_candidates=pareto,
        chosen_candidates=chosen,
        recommended_candidate=recommended,
        min_volume_candidate=min_volume_selection.candidate if min_volume_selection is not None else None,
        min_loss_candidate=min_loss_selection.candidate if min_loss_selection is not None else None,
        compromise_candidate=compromise_selection.candidate if compromise_selection is not None else None,
        rejection_counts=rejection_counts,
        notes=_dedupe_text(notes),
        warnings=_dedupe_text(warnings),
        artifact_paths=artifact_paths,
        feasible_csv_path=feasible_csv_path,
        pareto_csv_path=pareto_csv_path,
        chosen_csv_path=chosen_csv_path,
        pareto_png_path=pareto_png_path,
        pareto_notes=pareto_notes,
        plot_diagnostics=plot_diagnostics,
    )


def export_llc_external_resonant_inductor_feasible_candidates(
    feasible_candidates: Iterable[LlcExternalResonantInductorCandidate],
    output_dir: Path | None = None,
) -> list[str]:
    """Write first-pass feasible external Lr candidates for audit."""

    candidates = list(feasible_candidates)
    if not candidates:
        return []
    output_root = Path(output_dir or _project_root() / "outputs" / "resonant_inductor_design")
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / "llc_external_resonant_inductor_feasible_candidates.csv"
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_external_lr_candidate_csv_fields())
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(_external_lr_candidate_csv_row(candidate))
    return [str(output_path)]


def build_llc_external_resonant_inductor_pareto_front(
    candidates: Iterable[LlcExternalResonantInductorCandidate],
) -> list[LlcExternalResonantInductorCandidate]:
    """Return nondominated external Lr inductor candidates by volume and total loss."""

    feasible = [candidate for candidate in candidates if not candidate.rejection_reason]
    pareto: list[LlcExternalResonantInductorCandidate] = []
    for candidate in feasible:
        dominated = False
        for other in feasible:
            if other.design_id == candidate.design_id:
                continue
            no_worse = (
                other.estimated_volume_cm3 <= candidate.estimated_volume_cm3
                and other.total_loss_w <= candidate.total_loss_w
            )
            strictly_better = (
                other.estimated_volume_cm3 < candidate.estimated_volume_cm3
                or other.total_loss_w < candidate.total_loss_w
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            pareto.append(candidate)
    return sorted(pareto, key=lambda item: (item.estimated_volume_cm3, item.total_loss_w, item.design_id))


def select_llc_external_resonant_inductor_representatives(
    pareto_candidates: Iterable[LlcExternalResonantInductorCandidate],
) -> dict[str, LlcExternalResonantInductorRepresentativeSelection]:
    """Select deterministic external Lr inductor Pareto representatives."""

    pareto = list(pareto_candidates)
    if not pareto:
        return {}
    min_volume = min(
        pareto,
        key=lambda candidate: (candidate.estimated_volume_cm3, candidate.total_loss_w, candidate.hotspot_c, candidate.fill_factor, candidate.design_id),
    )
    min_loss = min(
        pareto,
        key=lambda candidate: (candidate.total_loss_w, candidate.estimated_volume_cm3, candidate.hotspot_c, candidate.fill_factor, candidate.design_id),
    )
    volume_values = [candidate.estimated_volume_cm3 for candidate in pareto]
    loss_values = [candidate.total_loss_w for candidate in pareto]
    min_volume_value = min(volume_values)
    max_volume_value = max(volume_values)
    min_loss_value = min(loss_values)
    max_loss_value = max(loss_values)

    def _normalized_score(candidate: LlcExternalResonantInductorCandidate) -> tuple[float, float, float, str]:
        volume_span = max(max_volume_value - min_volume_value, 1e-18)
        loss_span = max(max_loss_value - min_loss_value, 1e-18)
        normalized_volume = (candidate.estimated_volume_cm3 - min_volume_value) / volume_span
        normalized_loss = (candidate.total_loss_w - min_loss_value) / loss_span
        score = sqrt(normalized_volume**2 + normalized_loss**2)
        return (score, candidate.hotspot_c, candidate.fill_factor, candidate.design_id)

    compromise = min(pareto, key=_normalized_score)
    return {
        "recommended": LlcExternalResonantInductorRepresentativeSelection(
            role="recommended",
            candidate=compromise,
            reason="recommended from external Lr inductor Pareto compromise using normalized volume-loss distance.",
        ),
        "min-volume": LlcExternalResonantInductorRepresentativeSelection(
            role="min-volume",
            candidate=min_volume,
            reason="minimum estimated external Lr inductor volume on Pareto front.",
        ),
        "min-loss": LlcExternalResonantInductorRepresentativeSelection(
            role="min-loss",
            candidate=min_loss,
            reason="minimum total external Lr inductor loss on Pareto front.",
        ),
        "compromise": LlcExternalResonantInductorRepresentativeSelection(
            role="compromise",
            candidate=compromise,
            reason="closest Pareto candidate to normalized volume-loss ideal point.",
        ),
    }


def export_llc_external_resonant_inductor_pareto_artifacts(
    *,
    feasible_candidates: Iterable[LlcExternalResonantInductorCandidate],
    pareto_candidates: Iterable[LlcExternalResonantInductorCandidate],
    chosen_candidates: Iterable[LlcExternalResonantInductorRepresentativeSelection],
    output_dir: Path | None = None,
) -> tuple[list[str], dict[str, object]]:
    """Write external Lr Pareto CSV and PNG artifacts under outputs/resonant_inductor_design."""

    output_root = Path(output_dir or _project_root() / "outputs" / "resonant_inductor_design")
    output_root.mkdir(parents=True, exist_ok=True)
    feasible = list(feasible_candidates)
    pareto = list(pareto_candidates)
    chosen = list(chosen_candidates)
    paths: list[str] = []

    paths.extend(export_llc_external_resonant_inductor_feasible_candidates(feasible, output_dir=output_root))

    pareto_csv = output_root / "llc_external_resonant_inductor_pareto_front.csv"
    _write_external_lr_candidate_csv(pareto_csv, pareto)
    paths.append(str(pareto_csv))

    chosen_csv = output_root / "llc_external_resonant_inductor_chosen_candidates.csv"
    _write_external_lr_chosen_csv(chosen_csv, chosen)
    paths.append(str(chosen_csv))

    png_path = output_root / "llc_external_resonant_inductor_pareto_front.png"
    plot_data = build_external_lr_pareto_plot_data(feasible, pareto, chosen)
    _write_external_lr_pareto_png(png_path, plot_data)
    paths.append(str(png_path))
    return paths, plot_data["diagnostics"]


def _write_external_lr_candidate_csv(
    path: Path,
    candidates: Iterable[LlcExternalResonantInductorCandidate],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_external_lr_candidate_csv_fields())
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(_external_lr_candidate_csv_row(candidate))


def _write_external_lr_chosen_csv(
    path: Path,
    chosen_candidates: Iterable[LlcExternalResonantInductorRepresentativeSelection],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_external_lr_candidate_csv_fields())
        writer.writeheader()
        for selection in chosen_candidates:
            writer.writerow(
                _external_lr_candidate_csv_row(
                    selection.candidate,
                    representative_role=selection.role,
                    representative_reason=selection.reason,
                )
            )


def build_external_lr_pareto_plot_data(
    feasible_candidates: Iterable[LlcExternalResonantInductorCandidate],
    pareto_candidates: Iterable[LlcExternalResonantInductorCandidate],
    chosen_candidates: Iterable[LlcExternalResonantInductorRepresentativeSelection],
    *,
    volume_plot_percentile: float = 98.0,
    loss_plot_percentile: float = 98.0,
) -> dict[str, object]:
    """Build plot-only filtered external Lr PF data without changing CSV contents."""

    feasible = list(feasible_candidates)
    pareto = list(pareto_candidates)
    chosen = list(chosen_candidates)
    chosen_ids = {selection.candidate.design_id for selection in chosen}
    pareto_ids = {candidate.design_id for candidate in pareto}
    forced_ids = pareto_ids | chosen_ids
    representative_labels: dict[str, str] = {}
    for selection in chosen:
        representative_labels.setdefault(selection.candidate.design_id, "")
        existing = representative_labels[selection.candidate.design_id]
        representative_labels[selection.candidate.design_id] = (
            f"{existing} / {selection.role}" if existing else selection.role
        )
    if feasible:
        volume_limit = _percentile([candidate.estimated_volume_cm3 for candidate in feasible], volume_plot_percentile)
        loss_limit = _percentile([candidate.total_loss_w for candidate in feasible], loss_plot_percentile)
        chosen_volumes = [selection.candidate.estimated_volume_cm3 for selection in chosen]
        chosen_losses = [selection.candidate.total_loss_w for selection in chosen]
        if chosen_volumes:
            volume_limit = max(volume_limit, max(chosen_volumes) * 1.25)
        if chosen_losses:
            loss_limit = max(loss_limit, max(chosen_losses) * 1.25)
    else:
        volume_limit = 0.0
        loss_limit = 0.0
    visible_background = [
        candidate
        for candidate in feasible
        if candidate.design_id in forced_ids
        or (candidate.estimated_volume_cm3 <= volume_limit and candidate.total_loss_w <= loss_limit)
    ]
    visible_ids = {candidate.design_id for candidate in visible_background}
    hidden_background = [candidate for candidate in feasible if candidate.design_id not in visible_ids]
    diagnostics = {
        "plotted_feasible_background_points": len(visible_background),
        "hidden_feasible_outliers_in_png_only": len(hidden_background),
        "volume_plot_limit_cm3": volume_limit,
        "loss_plot_limit_w": loss_limit,
        "full_feasible_csv_remains_unfiltered": True,
        "pareto_chosen_candidates_are_always_plotted": True,
        "visible_candidate_ids": [candidate.design_id for candidate in visible_background],
        "forced_candidate_ids": sorted(forced_ids),
        "representative_plot_labels": representative_labels,
        "volume_plot_percentile": volume_plot_percentile,
        "loss_plot_percentile": loss_plot_percentile,
    }
    return {
        "visible_feasible_candidates": visible_background,
        "hidden_feasible_candidates": hidden_background,
        "pareto_candidates": pareto,
        "chosen_candidates": chosen,
        "diagnostics": diagnostics,
    }


def _write_external_lr_pareto_png(path: Path, plot_data: dict[str, object]) -> None:
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except Exception:
        return
    feasible_candidates = list(plot_data.get("visible_feasible_candidates", []))
    pareto_candidates = list(plot_data.get("pareto_candidates", []))
    chosen_candidates = list(plot_data.get("chosen_candidates", []))
    figure = Figure(figsize=(8.4, 5.3), dpi=130)
    axis = figure.add_subplot(111)
    if feasible_candidates:
        axis.scatter(
            [candidate.estimated_volume_cm3 for candidate in feasible_candidates],
            [candidate.total_loss_w for candidate in feasible_candidates],
            s=9,
            alpha=0.18,
            label="feasible",
            color="#718096",
            linewidths=0,
        )
    if pareto_candidates:
        pareto_sorted = sorted(pareto_candidates, key=lambda candidate: candidate.estimated_volume_cm3)
        axis.plot(
            [candidate.estimated_volume_cm3 for candidate in pareto_sorted],
            [candidate.total_loss_w for candidate in pareto_sorted],
            marker="o",
            linewidth=1.8,
            label="Pareto",
            color="#1f77b4",
            zorder=4,
        )
    role_markers = {
        "recommended": ("*", "#d62728"),
        "min-volume": ("s", "#2ca02c"),
        "min-loss": ("^", "#9467bd"),
        "compromise": ("D", "#ff7f0e"),
    }
    role_offsets = {
        "recommended": (12, 14),
        "min-volume": (-78, 14),
        "min-loss": (12, -20),
        "compromise": (-88, -24),
    }
    candidate_roles: dict[str, list[LlcExternalResonantInductorRepresentativeSelection]] = {}
    for selection in chosen_candidates:
        candidate_roles.setdefault(selection.candidate.design_id, []).append(selection)
    for selections in candidate_roles.values():
        selection = selections[0]
        roles = [item.role for item in selections]
        label = " / ".join(roles)
        marker, color = role_markers.get(selection.role, ("o", "#000000"))
        candidate = selection.candidate
        axis.scatter(
            [candidate.estimated_volume_cm3],
            [candidate.total_loss_w],
            marker=marker,
            s=130 if "recommended" in roles else 70,
            color=color,
            label=label,
            zorder=5,
            edgecolors="#1a202c",
            linewidths=0.6,
        )
        axis.annotate(
            label,
            (candidate.estimated_volume_cm3, candidate.total_loss_w),
            textcoords="offset points",
            xytext=role_offsets.get(selection.role, (8, 8)),
            fontsize=8,
            arrowprops={"arrowstyle": "-", "color": "#4a5568", "lw": 0.6},
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#cbd5e0", "alpha": 0.86},
            zorder=6,
        )
    visible_for_limits = [*feasible_candidates, *pareto_candidates, *(selection.candidate for selection in chosen_candidates)]
    _apply_plot_limits(axis, visible_for_limits)
    axis.set_title("LLC external resonant inductor Pareto front")
    axis.set_xlabel("Estimated external Lr inductor volume [cm^3]")
    axis.set_ylabel("Total external Lr inductor loss [W]")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="upper right", fontsize=8)
    figure.tight_layout()
    FigureCanvasAgg(figure).print_png(path)


def _screen_external_lr_wire_options(
    *,
    request: LlcExternalResonantInductorTarget,
    core: _NormalizedCoreRecord,
    material: _NormalizedMaterialRecord,
    wire: _NormalizedWireRecord,
    turns: int,
    b_limit_t: float,
) -> LlcExternalResonantInductorCandidate:
    min_parallel = max(
        1,
        ceil(
            request.current_rms_a
            / max(DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2 * wire.bundle_copper_area_m2 * 1e6, 1e-12)
        ),
    )
    if min_parallel > 12:
        return _build_external_lr_candidate(
            request=request,
            core=core,
            material=material,
            wire=wire,
            turns=turns,
            parallel_count=12,
            b_limit_t=b_limit_t,
        )
    return _build_external_lr_candidate(
        request=request,
        core=core,
        material=material,
        wire=wire,
        turns=turns,
        parallel_count=min_parallel,
        b_limit_t=b_limit_t,
    )


def _build_external_lr_candidate(
    *,
    request: LlcExternalResonantInductorTarget,
    core: _NormalizedCoreRecord,
    material: _NormalizedMaterialRecord,
    wire: _NormalizedWireRecord,
    turns: int,
    parallel_count: int,
    b_limit_t: float,
) -> LlcExternalResonantInductorCandidate:
    warnings: list[str] = [
        "High-mu gap approximation used because material relative permeability is unavailable.",
        "Actual Lr is a first-pass gap-derived estimate; manufacturing gap tolerance is not modeled.",
    ]
    target_l_h = request.external_lr_target_h
    current_convention = "sinusoidal_peak"
    bpeak_formula = "L_actual_H * Ipeak_A / (turns * Ae_m2)"
    gap_m = compute_gap_for_lm(turns, core.ae_m2, target_l_h)
    actual_l_h = compute_lm_from_gap(turns, core.ae_m2, gap_m)
    inductance_error_percent = 100.0 * (actual_l_h - target_l_h) / target_l_h
    b_peak_t = compute_llc_external_lr_bpeak_t(actual_l_h, request.current_peak_a, turns, core.ae_m2)
    b_margin_percent = 100.0 * (b_limit_t - b_peak_t) / b_limit_t
    if b_margin_percent < 10.0:
        warnings.append("Bpeak margin is below 10%; review core size, turns, and saturation margin.")
    conductor_area_m2 = wire.bundle_copper_area_m2 * parallel_count
    conductor_area_mm2 = conductor_area_m2 * 1e6
    fill_area_m2 = turns * parallel_count * (pi * (wire.outer_diameter_m / 2.0) ** 2) * LITZ_PACKING_FACTOR
    fill_factor = fill_area_m2 / core.window_area_m2
    current_density_a_per_mm2 = request.current_rms_a / max(conductor_area_mm2, 1e-12)
    dc_resistance_ohm = (
        COPPER_RESISTIVITY_25C_OHM_M
        * core.mean_length_per_turn_m
        * turns
        / max(conductor_area_m2, 1e-18)
    )
    ac_multiplier = _ac_resistance_multiplier(
        wire.strand_diameter_m,
        wire.strands_per_bundle * parallel_count,
        request.fs_basis_hz,
    )
    copper_loss_w = request.current_rms_a**2 * dc_resistance_ohm * ac_multiplier
    rejection_reason = ""
    core_loss_w = 0.0
    core_loss_status = "loss_data_not_available"
    core_loss_method = None
    core_loss_model_id = None
    core_loss_reconstruction = "unavailable"
    if material.steinmetz_ranges:
        routed, built = evaluate_candidate_core_loss(
            material_id=material.material_id, material_name=material.material_id,
            frequency_hz=request.fs_basis_hz, effective_volume_m3=core.ve_m3,
            effective_area_m2=core.ae_m2, turns=turns, inductance_h=actual_l_h,
            b_peak_t=b_peak_t, steinmetz_ranges=material.steinmetz_ranges,
            source_role="llc_external_resonant_inductor_core", source_component_id=f"{core.core_id}:N{turns}",
        )
        core_loss_status = routed.validity_status.value
        core_loss_method = routed.method_used
        core_loss_model_id = routed.selected_model_id
        core_loss_reconstruction = built.reconstruction_method
        if routed.core_loss_w is None:
            rejection_reason = f"missing_data: shared core-loss route unavailable ({core_loss_status})"
        else:
            core_loss_w = routed.core_loss_w
    else:
        rejection_reason = "missing_data: material core-loss model unavailable"
    winding_volume_m3 = fill_area_m2 * core.mean_length_per_turn_m
    estimated_volume_m3 = core.gross_volume_m3 + winding_volume_m3
    total_loss_w = core_loss_w + copper_loss_w
    thermal = _estimate_transformer_thermal(total_loss_w, estimated_volume_m3)
    total_lr_actual_h = actual_l_h + request.transformer_lk_h
    total_lr_error_percent = 100.0 * (total_lr_actual_h - request.lr_total_target_h) / request.lr_total_target_h
    lr_closure_status = "ok"
    if abs(total_lr_error_percent) > 5.0:
        lr_closure_status = "warning"
        warnings.append("Total Lr closure error exceeds tolerance; check transformer leakage and external Lr target binding.")
    if not rejection_reason:
        rejection_reason = _external_lr_rejection_reason(
            core=core,
            gap_m=gap_m,
            inductance_error_percent=inductance_error_percent,
            b_peak_t=b_peak_t,
            b_limit_t=b_limit_t,
            fill_factor=fill_factor,
            current_density_a_per_mm2=current_density_a_per_mm2,
            hotspot_c=thermal.hotspot_c,
        )
    design_id = f"Lr_ext_{_sanitize_identifier(core.core_id)}_{_sanitize_identifier(material.material_id)}_N{turns}_P{parallel_count}"
    return LlcExternalResonantInductorCandidate(
        design_id=design_id,
        core_id=core.core_id,
        core_family=_core_family(core.core_id),
        material_name=material.material_id,
        turns=turns,
        gap_m=gap_m,
        gap_mm=gap_m * 1e3,
        target_l_h=target_l_h,
        actual_l_h=actual_l_h,
        actual_l_uH=actual_l_h * 1e6,
        inductance_error_percent=inductance_error_percent,
        transformer_lk_h=request.transformer_lk_h,
        transformer_lk_uH=request.transformer_lk_h * 1e6,
        total_lr_actual_h=total_lr_actual_h,
        total_lr_actual_uH=total_lr_actual_h * 1e6,
        total_lr_error_percent=total_lr_error_percent,
        current_rms_a=request.current_rms_a,
        current_peak_a=request.current_peak_a,
        fs_basis_hz=request.fs_basis_hz,
        b_peak_t=b_peak_t,
        b_limit_t=b_limit_t,
        b_margin_percent=b_margin_percent,
        fill_factor=fill_factor,
        current_density_a_per_mm2=current_density_a_per_mm2,
        core_loss_w=core_loss_w,
        copper_loss_w=copper_loss_w,
        total_loss_w=total_loss_w,
        hotspot_c=thermal.hotspot_c,
        estimated_volume_m3=estimated_volume_m3,
        estimated_volume_cm3=estimated_volume_m3 * 1e6,
        wire_name=wire.wire_id,
        wire_parallel_count=parallel_count,
        warning=" ".join(warnings),
        rejection_reason=rejection_reason,
        core_effective_area_m2=core.ae_m2,
        core_effective_area_source_field=core.ae_source_field,
        bpeak_formula=bpeak_formula,
        current_convention=current_convention,
        core_window_area_m2=core.window_area_m2,
        core_width_m=core.outer_width_m,
        core_height_m=core.outer_height_m,
        core_depth_m=_external_lr_core_depth_m(core),
        core_volume_m3=core.gross_volume_m3,
        winding_volume_m3=winding_volume_m3,
        gross_volume_m3=core.gross_volume_m3,
        transformer_design_id_used_for_lk=request.transformer_design_id,
        external_lr_design_id=design_id,
        lr_closure_status=lr_closure_status,
    )


def _external_lr_rejection_reason(
    *,
    core: _NormalizedCoreRecord,
    gap_m: float,
    inductance_error_percent: float,
    b_peak_t: float,
    b_limit_t: float,
    fill_factor: float,
    current_density_a_per_mm2: float,
    hotspot_c: float,
) -> str:
    if core.ae_m2 <= 0.0 or core.le_m <= 0.0 or core.window_area_m2 <= 0.0:
        return "invalid_geometry"
    if gap_m <= 0.0 or gap_m < EXTERNAL_LR_GAP_MIN_M or gap_m > EXTERNAL_LR_GAP_MAX_M:
        return "invalid_gap"
    if gap_m / core.le_m > EXTERNAL_LR_GAP_TO_LE_MAX:
        return "invalid_gap: gap_to_le_limit"
    if abs(inductance_error_percent) > EXTERNAL_LR_INDUCTANCE_ERROR_LIMIT_PERCENT:
        return "invalid_gap: inductance_error_limit"
    if b_peak_t > b_limit_t:
        return "saturation"
    if fill_factor <= 0.0 or fill_factor > DEFAULT_FILL_FACTOR_LIMIT:
        return "fill"
    if current_density_a_per_mm2 > DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2:
        return "current_density"
    if hotspot_c > DEFAULT_HOTSPOT_LIMIT_C:
        return "thermal"
    return ""


def compute_llc_external_lr_bpeak_t(
    l_actual_h: float,
    current_peak_a: float,
    turns: int,
    ae_m2: float,
) -> float:
    """Return LLC external resonant inductor Bpeak from sinusoidal peak current."""

    if l_actual_h <= 0.0 or current_peak_a <= 0.0 or turns <= 0 or ae_m2 <= 0.0:
        raise ValueError("External Lr Bpeak requires positive Lactual, Ipeak, turns, and Ae.")
    return l_actual_h * current_peak_a / (turns * ae_m2)


def _external_lr_b_limit_t(material: _NormalizedMaterialRecord) -> float:
    return min(0.18, 0.8 * material.b_sat_t) if material.b_sat_t > 0.0 else 0.0


def _select_external_lr_cores(
    cores: list[_NormalizedCoreRecord],
    request: LlcExternalResonantInductorTarget,
    limit: int | None,
) -> list[_NormalizedCoreRecord]:
    sorted_cores = sorted(cores, key=lambda item: (item.ve_m3, item.core_id))
    if limit is None or limit <= 0 or len(sorted_cores) <= limit:
        return sorted_cores
    area_product_target = request.external_lr_target_h * request.current_peak_a * request.current_rms_a / max(
        0.18 * DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2 * 1e6,
        1e-18,
    )
    plausible = [core for core in sorted_cores if core.ae_m2 * core.window_area_m2 >= 0.15 * area_product_target]
    return sorted(_spread_records(plausible or sorted_cores, limit), key=lambda item: (item.ve_m3, item.core_id))


def _select_external_lr_wires(
    wires: list[_NormalizedWireRecord],
    request: LlcExternalResonantInductorTarget,
    limit: int | None,
) -> list[_NormalizedWireRecord]:
    sorted_wires = sorted(wires, key=lambda item: (item.bundle_copper_area_m2, item.wire_id))
    if limit is None or limit <= 0 or len(sorted_wires) <= limit:
        return sorted_wires
    required_area_m2 = request.current_rms_a / (DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2 * 1e6)
    plausible = [wire for wire in sorted_wires if required_area_m2 / 12.0 <= wire.bundle_copper_area_m2 <= required_area_m2 * 1.50]
    return sorted(_spread_records(plausible or sorted_wires, limit), key=lambda item: (item.bundle_copper_area_m2, item.wire_id))


def _material_loss_model_covers_frequency(
    material: _NormalizedMaterialRecord,
    frequency_hz: float,
) -> bool:
    if frequency_hz <= 0.0:
        return False
    for loss_range in material.steinmetz_ranges:
        minimum_hz = _optional_range_float(
            loss_range,
            ("minimumFrequency", "frequency_min_hz", "minimum_frequency_hz"),
        )
        maximum_hz = _optional_range_float(
            loss_range,
            ("maximumFrequency", "frequency_max_hz", "maximum_frequency_hz"),
        )
        if minimum_hz is None and maximum_hz is None:
            continue
        if _frequency_in_range(frequency_hz, minimum_hz, maximum_hz):
            return True
    return False


def _optional_range_float(record: Mapping[str, Any], names: tuple[str, ...]) -> float | None:
    for name in names:
        if name not in record or record[name] in (None, ""):
            continue
        try:
            return float(record[name])
        except (TypeError, ValueError):
            return None
    return None


def _external_lr_candidate_csv_fields() -> list[str]:
    return [
        "design_id",
        "core_id",
        "core_family",
        "material_name",
        "turns",
        "gap_mm",
        "target_l_uH",
        "actual_l_uH",
        "l_actual_uH",
        "inductance_error_percent",
        "transformer_lk_uH",
        "total_lr_actual_uH",
        "total_lr_error_percent",
        "current_rms_a",
        "current_peak_a",
        "current_convention",
        "fs_basis_hz",
        "ae_used_mm2",
        "ae_source_field",
        "ae_used_m2",
        "bpeak_formula",
        "computed_bpeak_t",
        "b_peak_t",
        "b_limit_t",
        "b_utilization",
        "b_margin_percent",
        "fill_factor",
        "current_density_a_per_mm2",
        "core_loss_w",
        "copper_loss_w",
        "total_loss_w",
        "hotspot_c",
        "estimated_volume_cm3",
        "wire_name",
        "wire_parallel_count",
        "warning",
        "representative_role",
        "representative_reason",
    ]


def _external_lr_candidate_csv_row(
    candidate: LlcExternalResonantInductorCandidate,
    *,
    representative_role: str = "",
    representative_reason: str = "",
) -> dict[str, object]:
    return {
        "design_id": candidate.design_id,
        "core_id": candidate.core_id,
        "core_family": candidate.core_family,
        "material_name": candidate.material_name,
        "turns": candidate.turns,
        "gap_mm": candidate.gap_mm,
        "target_l_uH": candidate.target_l_h * 1e6,
        "actual_l_uH": candidate.actual_l_uH,
        "l_actual_uH": candidate.actual_l_uH,
        "inductance_error_percent": candidate.inductance_error_percent,
        "transformer_lk_uH": candidate.transformer_lk_uH,
        "total_lr_actual_uH": candidate.total_lr_actual_uH,
        "total_lr_error_percent": candidate.total_lr_error_percent,
        "current_rms_a": candidate.current_rms_a,
        "current_peak_a": candidate.current_peak_a,
        "current_convention": candidate.current_convention,
        "fs_basis_hz": candidate.fs_basis_hz,
        "ae_used_mm2": candidate.core_effective_area_m2 * 1e6,
        "ae_source_field": candidate.core_effective_area_source_field,
        "ae_used_m2": candidate.core_effective_area_m2,
        "bpeak_formula": candidate.bpeak_formula,
        "computed_bpeak_t": candidate.b_peak_t,
        "b_peak_t": candidate.b_peak_t,
        "b_limit_t": candidate.b_limit_t,
        "b_utilization": candidate.b_peak_t / candidate.b_limit_t if candidate.b_limit_t > 0.0 else "",
        "b_margin_percent": candidate.b_margin_percent,
        "fill_factor": candidate.fill_factor,
        "current_density_a_per_mm2": candidate.current_density_a_per_mm2,
        "core_loss_w": candidate.core_loss_w,
        "copper_loss_w": candidate.copper_loss_w,
        "total_loss_w": candidate.total_loss_w,
        "hotspot_c": candidate.hotspot_c,
        "estimated_volume_cm3": candidate.estimated_volume_cm3,
        "wire_name": candidate.wire_name,
        "wire_parallel_count": candidate.wire_parallel_count,
        "warning": candidate.warning,
        "representative_role": representative_role,
        "representative_reason": representative_reason,
    }


def _external_lr_rejection_counter() -> dict[str, int]:
    return {
        "invalid_target": 0,
        "invalid_geometry": 0,
        "invalid_gap": 0,
        "saturation": 0,
        "fill": 0,
        "current_density": 0,
        "thermal": 0,
        "missing_data": 0,
        "no_wire_fit": 0,
    }


def _increment_external_lr_rejection(counts: dict[str, int], reason: str) -> None:
    key = reason.split(":", 1)[0].strip()
    if key in counts:
        counts[key] += 1
    elif key:
        counts["missing_data"] += 1


def _external_lr_rejection_rank(reason: str) -> int:
    order = {
        "": 0,
        "thermal": 1,
        "current_density": 2,
        "fill": 3,
        "saturation": 4,
        "invalid_gap": 5,
        "invalid_geometry": 6,
        "missing_data": 7,
        "no_wire_fit": 8,
    }
    return order.get(reason.split(":", 1)[0], 9)


def _first_path_named(paths: list[str], name: str) -> str:
    for path in paths:
        if Path(path).name == name:
            return path
    return ""


def _external_lr_missing_candidate(
    request: LlcExternalResonantInductorTarget,
    core: _NormalizedCoreRecord,
    material: _NormalizedMaterialRecord,
    wire: _NormalizedWireRecord,
    turns: int,
    b_limit_t: float,
) -> LlcExternalResonantInductorCandidate:
    design_id = f"Lr_ext_{_sanitize_identifier(core.core_id)}_{_sanitize_identifier(material.material_id)}_N{turns}_P0"
    return LlcExternalResonantInductorCandidate(
        design_id=design_id,
        core_id=core.core_id,
        core_family=_core_family(core.core_id),
        material_name=material.material_id,
        turns=turns,
        gap_m=0.0,
        gap_mm=0.0,
        target_l_h=request.external_lr_target_h,
        actual_l_h=0.0,
        actual_l_uH=0.0,
        inductance_error_percent=0.0,
        transformer_lk_h=request.transformer_lk_h,
        transformer_lk_uH=request.transformer_lk_h * 1e6,
        total_lr_actual_h=request.transformer_lk_h,
        total_lr_actual_uH=request.transformer_lk_h * 1e6,
        total_lr_error_percent=0.0,
        current_rms_a=request.current_rms_a,
        current_peak_a=request.current_peak_a,
        fs_basis_hz=request.fs_basis_hz,
        b_peak_t=0.0,
        b_limit_t=b_limit_t,
        b_margin_percent=0.0,
        fill_factor=0.0,
        current_density_a_per_mm2=0.0,
        core_loss_w=0.0,
        copper_loss_w=0.0,
        total_loss_w=0.0,
        hotspot_c=0.0,
        estimated_volume_m3=core.gross_volume_m3,
        estimated_volume_cm3=core.gross_volume_m3 * 1e6,
        wire_name=wire.wire_id,
        wire_parallel_count=0,
        warning="",
        rejection_reason="no_wire_fit",
        core_effective_area_m2=core.ae_m2,
        core_effective_area_source_field=core.ae_source_field,
        bpeak_formula="L_actual_H * Ipeak_A / (turns * Ae_m2)",
        current_convention="sinusoidal_peak",
        core_window_area_m2=core.window_area_m2,
        core_width_m=core.outer_width_m,
        core_height_m=core.outer_height_m,
        core_depth_m=_external_lr_core_depth_m(core),
        core_volume_m3=core.gross_volume_m3,
        winding_volume_m3=0.0,
        gross_volume_m3=core.gross_volume_m3,
        transformer_design_id_used_for_lk=request.transformer_design_id,
        external_lr_design_id=design_id,
        lr_closure_status="unavailable",
    )


def _sanitize_identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(value)).strip("_") or "item"


def _external_lr_core_depth_m(core: _NormalizedCoreRecord) -> float:
    if core.outer_width_m > 0.0 and core.outer_height_m > 0.0 and core.gross_volume_m3 > 0.0:
        return core.gross_volume_m3 / (core.outer_width_m * core.outer_height_m)
    return 0.0


def _core_family(core_id: str) -> str:
    match = re.match(r"([A-Za-z]+)", str(core_id))
    return match.group(1).upper() if match else ""


def _select_external_lr_current_frequency_basis(design: object) -> tuple[str, float, float, float, str, str]:
    corner_estimates = [
        estimate
        for estimate in getattr(design, "current_estimates_by_corner", [])
        if isinstance(estimate, dict)
        and isinstance(estimate.get("ir_rms_a"), (int, float))
        and isinstance(estimate.get("ir_peak_a"), (int, float))
    ]
    if corner_estimates:
        selected = max(corner_estimates, key=lambda estimate: (float(estimate["ir_rms_a"]), float(estimate["ir_peak_a"])))
        corner_name = str(selected.get("corner_name", "-"))
        fs_hz = _positive_float(selected.get("fs_hz"), float(getattr(design, "fr_hz")))
        frequency_basis = f"FHA solved frequency at {corner_name}"
        warning = "" if isinstance(selected.get("fs_hz"), (int, float)) and float(selected["fs_hz"]) > 0.0 else "Using nominal/design frequency because selected FHA current corner frequency is unavailable."
        return (
            f"worst_case_fha_corner: {corner_name}",
            float(selected["ir_rms_a"]),
            float(selected["ir_peak_a"]),
            fs_hz,
            frequency_basis,
            warning,
        )

    nominal = getattr(design, "current_estimates_nominal_full_load", {})
    if isinstance(nominal, dict) and isinstance(nominal.get("ir_rms_a"), (int, float)) and isinstance(nominal.get("ir_peak_a"), (int, float)):
        fs_hz = _positive_float(nominal.get("fs_hz"), float(getattr(design, "fr_hz")))
        return (
            "nominal_full_load_fha_current",
            float(nominal["ir_rms_a"]),
            float(nominal["ir_peak_a"]),
            fs_hz,
            "nominal/design FHA frequency",
            "Using nominal full-load FHA current because corner current metadata is unavailable.",
        )

    fallback_current_a = _positive_float(getattr(design, "pout_max_w", 0.0), 0.0) / max(
        _positive_float(getattr(design, "vout_nom_v", 0.0), 1.0),
        1e-12,
    )
    return (
        "fallback_output_current_used_as_last_resort",
        fallback_current_a,
        sqrt(2.0) * fallback_current_a,
        _positive_float(getattr(design, "fr_hz", 0.0), 0.0),
        "nominal/design FHA frequency",
        "Using output current as last-resort external Lr current basis because FHA resonant tank current metadata is unavailable.",
    )


def _positive_float(value: object, fallback: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return fallback
    return result if result > 0.0 else fallback


def _screen_transformer_candidate(
    *,
    inputs: LLCTransformerDesignInputs,
    core: _NormalizedCoreRecord,
    material: _NormalizedMaterialRecord,
    wires: list[_NormalizedWireRecord],
    turns: LLCTransformerTurnsCandidate,
    turns_diagnostics: dict[str, object] | None = None,
    frequency_solver: FrequencySolver | None = None,
) -> LLCTransformerScreeningCandidate:
    flux_cases = build_boundary_flux_cases(inputs, core.ae_m2, turns.np, frequency_solver)
    worst_flux = max(flux_cases, key=lambda case: case.b_peak_t)
    saturation_pass = all(case.pass_b_limit for case in flux_cases)
    gap_m = compute_gap_for_lm(turns.np, core.ae_m2, inputs.lm_target_h, core.le_m)
    lm_actual_h = compute_lm_from_gap(turns.np, core.ae_m2, gap_m)
    lm_error_percent = 100.0 * (lm_actual_h - inputs.lm_target_h) / inputs.lm_target_h
    gap_to_le = gap_m / core.le_m if core.le_m > 0.0 else float("inf")
    lm_pass = abs(lm_error_percent) <= inputs.lm_tolerance_percent and gap_m > 0.0 and gap_to_le <= 0.15
    turns_diagnostics = turns_diagnostics or {}
    np_required_by_saturation = int(turns_diagnostics.get("np_required_by_saturation", turns.np))
    scale_min_by_saturation = int(turns_diagnostics.get("scale_min_by_saturation", turns.scale_factor))
    scale_factor_range = turns_diagnostics.get("scale_factor_range_used", (turns.scale_factor, turns.scale_factor))
    if not isinstance(scale_factor_range, tuple) or len(scale_factor_range) != 2:
        scale_factor_range = (turns.scale_factor, turns.scale_factor)
    max_scale_factor_used = int(turns_diagnostics.get("max_scale_factor_used", scale_factor_range[1]))
    saturation_worst_case = str(turns_diagnostics.get("saturation_worst_case", worst_flux.case_name))

    primary_winding = _estimate_winding(
        winding_name="primary",
        turns=turns.np,
        current_rms_a=inputs.primary_current_rms_a,
        current_peak_a=inputs.primary_current_peak_a,
        mlt_m=core.mean_length_per_turn_m,
        fs_hz=worst_flux.fs_hz,
        wires=wires,
    )
    secondary_winding = _estimate_winding(
        winding_name="secondary",
        turns=turns.ns,
        current_rms_a=inputs.secondary_current_rms_a,
        current_peak_a=inputs.secondary_current_peak_a,
        mlt_m=core.mean_length_per_turn_m,
        fs_hz=worst_flux.fs_hz,
        wires=wires,
    )
    leakage_geometry, leakage_primary_radial_build_m, leakage_secondary_radial_build_m, leakage_insulation_gap_m = _estimate_leakage_geometry(
        primary_winding,
        secondary_winding,
        core,
    )
    estimated_lk_h, leakage_method, leakage_warning = _estimate_candidate_leakage(
        primary_turns=turns.np,
        mean_length_per_turn_m=core.mean_length_per_turn_m,
        effective_winding_height_m=leakage_geometry.leakage_effective_height_m,
        primary_radial_build_m=leakage_primary_radial_build_m,
        secondary_radial_build_m=leakage_secondary_radial_build_m,
        insulation_gap_m=leakage_insulation_gap_m,
        leakage_fraction_estimate=inputs.leakage_fraction_estimate,
        fallback_lm_actual_h=lm_actual_h,
    )
    lk_over_lr = estimated_lk_h / inputs.lr_target_h if inputs.lr_target_h > 0.0 else float("inf")
    leakage_pass = lk_over_lr <= 0.80

    hard_missing_reasons: list[str] = []
    if not wires:
        hard_missing_reasons.append("missing_data_hard(no_usable_wire_records)")
    if primary_winding is not None and secondary_winding is not None:
        primary_fill_area_m2 = mm2_to_m2(primary_winding.fill_area_mm2)
        secondary_fill_area_m2 = mm2_to_m2(secondary_winding.fill_area_mm2)
        insulation_reserved_area_m2 = core.window_area_m2 * DEFAULT_INSULATION_WINDOW_RESERVE_FRACTION
        total_fill_area_m2 = primary_fill_area_m2 + secondary_fill_area_m2 + insulation_reserved_area_m2
        fill_factor = total_fill_area_m2 / max(core.window_area_m2, 1e-18)
        fill_pass = fill_factor <= DEFAULT_FILL_FACTOR_LIMIT
        current_density_pass = (
            primary_winding.current_density_a_per_mm2 <= DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2
            and secondary_winding.current_density_a_per_mm2 <= DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2
        )
        primary_copper_loss_w = primary_winding.copper_loss_w
        secondary_copper_loss_w = secondary_winding.copper_loss_w
    else:
        primary_fill_area_m2 = 0.0
        secondary_fill_area_m2 = 0.0
        insulation_reserved_area_m2 = core.window_area_m2 * DEFAULT_INSULATION_WINDOW_RESERVE_FRACTION
        total_fill_area_m2 = insulation_reserved_area_m2
        fill_factor = float("inf")
        fill_pass = False
        current_density_pass = False
        primary_copper_loss_w = 0.0
        secondary_copper_loss_w = 0.0

    core_loss_w = 0.0
    loss_warnings: list[str] = []
    loss_model = "shared_router_unavailable_plus_first_pass_litz_ac_resistance"
    core_loss_status = "loss_data_not_available"
    if material.steinmetz_ranges:
        routed, _built = evaluate_candidate_core_loss(
            material_id=material.material_id, material_name=material.material_id,
            frequency_hz=worst_flux.fs_hz, effective_volume_m3=core.ve_m3,
            effective_area_m2=core.ae_m2, turns=turns.np, inductance_h=inputs.lm_target_h,
            b_peak_t=worst_flux.b_peak_t, steinmetz_ranges=material.steinmetz_ranges,
            source_role="llc_transformer_core", source_component_id=f"{core.core_id}:{material.material_id}:Np{turns.np}:Ns{turns.ns}",
            dc_offset_policy="zero_cycle_average",
        )
        core_loss_status = routed.validity_status.value
        if routed.core_loss_w is not None:
            core_loss_w = routed.core_loss_w
            loss_model = "shared_router_plus_first_pass_litz_ac_resistance"
        else:
            loss_warnings.append(f"Shared core-loss route unavailable: {core_loss_status}.")
    else:
        loss_warnings.append("Soft missing core-loss data: material has no usable model; candidate is not loss-comparable.")

    copper_loss_w = primary_copper_loss_w + secondary_copper_loss_w
    total_loss_w = core_loss_w + copper_loss_w
    winding_volume_m3 = _estimate_winding_volume_m3(primary_winding, secondary_winding, core.mean_length_per_turn_m)
    estimated_volume_m3 = core.gross_volume_m3 + winding_volume_m3
    thermal = _estimate_transformer_thermal(total_loss_w, estimated_volume_m3)
    thermal_pass = thermal.hotspot_c <= DEFAULT_HOTSPOT_LIMIT_C

    rejection_reasons: list[str] = []
    if not saturation_pass:
        rejection_reasons.append("saturation_b_limit")
    if not lm_pass:
        rejection_reasons.append("lm_or_gap_limit")
    if not leakage_pass:
        rejection_reasons.append("leakage_lk_over_lr_gt_0p80")
    if not fill_pass:
        primary_wire_area = primary_winding.conductor_area_mm2 if primary_winding is not None else 0.0
        secondary_wire_area = secondary_winding.conductor_area_mm2 if secondary_winding is not None else 0.0
        rejection_reasons.append(
            "fill_factor_limit("
            f"fill_factor={fill_factor:.6g}, fill_limit={DEFAULT_FILL_FACTOR_LIMIT:.6g}, "
            f"Np={turns.np}, Ns={turns.ns}, "
            f"primary_wire_area_mm2={primary_wire_area:.6g}, "
            f"secondary_wire_area_mm2={secondary_wire_area:.6g}, "
            f"window_area_m2={core.window_area_m2:.6g})"
        )
    if not current_density_pass:
        rejection_reasons.append("current_density_limit")
    if not thermal_pass:
        rejection_reasons.append("thermal_limit")
    rejection_reasons.extend(hard_missing_reasons)
    if core_loss_status not in {"valid", "valid_interpolated"}:
        rejection_reasons.append(f"core_loss_unavailable:{core_loss_status}")

    warnings = [*loss_warnings]
    if leakage_warning:
        warnings.append(f"Leakage estimate note: {leakage_warning}")
    if inputs.primary_bridge_type == "full_bridge" and inputs.vin_nom_v >= 300.0 and turns.np < 10:
        warnings.append("Primary turns are low for a high-voltage LLC; verify Ae, fs, and Bpeak diagnostics.")
    if worst_flux.b_peak_t < 0.05:
        warnings.append("Bpeak is very low; design may be over-cored or flux calculation should be reviewed.")
    if inputs.b_limit_t > 0.0:
        bpeak_margin_percent = (inputs.b_limit_t - worst_flux.b_peak_t) / inputs.b_limit_t * 100.0
        if bpeak_margin_percent < 10.0:
            warnings.append("Bpeak margin is below 10%; review core size, turns, and saturation margin.")
    if gap_to_le > 0.05:
        warnings.append("Gap is large relative to magnetic path length; first-pass gap model should be reviewed.")
    if fill_factor > 0.4:
        warnings.append("Fill factor is high for a transformer first-pass design.")
    if lk_over_lr > 0.80:
        warnings.append("Leakage ratio exceeds 0.80; candidate is rejected by leakage.")
    elif lk_over_lr > 0.40:
        warnings.append("Leakage ratio is between 0.40 and 0.80; candidate is feasible but should be treated as a warning case.")
    elif leakage_method == "legacy_fraction_fallback":
        warnings.append("Leakage estimate used legacy fallback; geometry-based result is unavailable or invalid.")
    if any(case.fs_source == "fs_min_fallback" for case in flux_cases):
        warnings.append("One or more flux cases used fs_min fallback because FHA frequency solve failed.")
    warnings.extend(
        note
        for case in flux_cases
        for note in case.notes
        if "fallback" in note.lower() or "failed" in note.lower()
    )
    warnings.extend(thermal.warnings)
    notes = [
        "Separated LLC transformer candidate realizes Np:Ns and Lm; external Lr remains separate.",
        "Primary winding current uses FHA resonant tank current, not output current.",
        "Secondary winding current uses reflected-load current and excludes magnetizing current.",
        "Fill factor reserves 15% of window area for first-pass insulation/clearance allowance.",
    ]
    if material.material_metric_source:
        notes.append(f"Material metric source = {material.material_metric_source}.")
    if material.f_min_recommended_hz is not None or material.f_max_recommended_hz is not None:
        notes.append(
            "Material recommended frequency range = "
            f"{_display_frequency_bound(material.f_min_recommended_hz)} to {_display_frequency_bound(material.f_max_recommended_hz)} Hz; "
            f"worst-case fs {worst_flux.fs_hz:.6g} Hz is "
            f"{'inside' if _frequency_in_range(worst_flux.fs_hz, material.f_min_recommended_hz, material.f_max_recommended_hz) else 'outside'}."
        )
    if inputs.secondary_rectifier_type == "full_wave_center_tapped_rectifier":
        notes.append("Center-tapped secondary is treated as a conservative first-pass full secondary equivalent.")
    if gap_to_le <= 0.05:
        notes.append("Air-gap dominated Lm estimate; core reluctance is not included.")
    candidate_id = _transformer_candidate_id(core.core_id, material.material_id, turns.np, turns.ns)
    flux_audit = compute_transformer_flux_density_audit(
        transformer_design_id=candidate_id,
        core_id=core.core_id,
        material_id=material.material_id,
        np=turns.np,
        ns=turns.ns,
        ae_m2=core.ae_m2,
        ae_source_field=core.ae_source_field,
        vpri_v=worst_flux.primary_voltage_v,
        voltage_basis_label=f"{inputs.primary_bridge_type} square-wave primary voltage",
        fs_hz=worst_flux.fs_hz,
        reported_bpeak_t=worst_flux.b_peak_t,
        reported_delta_b_t=worst_flux.delta_b_t,
        b_limit_t=inputs.b_limit_t,
        worst_case_name=worst_flux.case_name,
    )
    warnings.extend(flux_audit.warnings)
    notes.append(
        "Transformer flux audit derives physical Bpeak = Vpri/(4*Np*Ae*fs) and physical deltaB = Vpri/(2*Np*Ae*fs)."
    )

    magnetic_loss = LLCTransformerMagneticLossEstimate(
        core_loss_w=core_loss_w,
        primary_copper_loss_w=primary_copper_loss_w,
        secondary_copper_loss_w=secondary_copper_loss_w,
        total_copper_loss_w=copper_loss_w,
        total_loss_w=total_loss_w,
        loss_model=loss_model,
        frequency_basis_hz=worst_flux.fs_hz,
        flux_basis_t=worst_flux.b_peak_t,
        notes=[
            "Core loss is evaluated at the worst boundary flux case.",
            "Copper loss uses a first-pass AC resistance multiplier over DC resistance.",
        ],
        warnings=loss_warnings,
        kernel_core_loss_w=core_loss_w,
        legacy_core_loss_w_with_erroneous_x1000=(core_loss_w * 1e3 if material.steinmetz_ranges else None),
        kernel_vs_legacy_relative_difference=(-0.999 if material.steinmetz_ranges else None),
    )
    feasible = not rejection_reasons
    return LLCTransformerScreeningCandidate(
        candidate_id=candidate_id,
        core_id=core.core_id,
        material_id=material.material_id,
        ae_m2=core.ae_m2,
        le_m=core.le_m,
        ve_m3=core.ve_m3,
        window_area_m2=core.window_area_m2,
        np=turns.np,
        ns=turns.ns,
        scale_factor=turns.scale_factor,
        actual_turns_ratio=turns.actual_turns_ratio,
        ratio_error_percent=turns.ratio_error_percent,
        lm_target_h=inputs.lm_target_h,
        lm_actual_h=lm_actual_h,
        lm_error_percent=lm_error_percent,
        gap_m=gap_m,
        lr_target_h=inputs.lr_target_h,
        estimated_lk_h=estimated_lk_h,
        lk_over_lr=lk_over_lr,
        leakage_pass=leakage_pass,
        leakage_method=leakage_method,
        leakage_winding_arrangement=DEFAULT_WINDING_ARRANGEMENT,
        leakage_warning=leakage_warning,
        leakage_height_source=leakage_geometry.leakage_height_source,
        leakage_height_warning=leakage_geometry.leakage_height_warning,
        leakage_usable_window_height_mm=leakage_geometry.leakage_usable_window_height_m * 1e3,
        leakage_primary_occupied_height_mm=leakage_geometry.leakage_primary_occupied_height_m * 1e3,
        leakage_secondary_occupied_height_mm=leakage_geometry.leakage_secondary_occupied_height_m * 1e3,
        leakage_window_area_mm2=leakage_geometry.leakage_window_area_m2 * 1e6,
        leakage_inferred_window_width_mm=leakage_geometry.leakage_inferred_window_width_m * 1e3,
        leakage_effective_height_m=leakage_geometry.leakage_effective_height_m,
        leakage_primary_radial_build_m=leakage_primary_radial_build_m,
        leakage_secondary_radial_build_m=leakage_secondary_radial_build_m,
        leakage_insulation_gap_m=leakage_insulation_gap_m,
        max_b_peak_t=worst_flux.b_peak_t,
        max_delta_b_t=worst_flux.delta_b_t,
        b_limit_t=inputs.b_limit_t,
        worst_flux_case_name=worst_flux.case_name,
        saturation_pass=saturation_pass,
        primary_winding=primary_winding,
        secondary_winding=secondary_winding,
        fill_factor=fill_factor,
        fill_limit=DEFAULT_FILL_FACTOR_LIMIT,
        primary_fill_area_m2=primary_fill_area_m2,
        secondary_fill_area_m2=secondary_fill_area_m2,
        insulation_reserved_area_m2=insulation_reserved_area_m2,
        total_fill_area_m2=total_fill_area_m2,
        fill_pass=fill_pass,
        current_density_pass=current_density_pass,
        np_required_by_saturation=np_required_by_saturation,
        scale_min_by_saturation=scale_min_by_saturation,
        scale_factor_range_used=scale_factor_range,
        max_scale_factor_used=max_scale_factor_used,
        saturation_worst_case=saturation_worst_case,
        core_loss_w=core_loss_w,
        copper_loss_w=copper_loss_w,
        total_loss_w=total_loss_w,
        hotspot_c=thermal.hotspot_c,
        thermal_pass=thermal_pass,
        estimated_volume_m3=estimated_volume_m3,
        feasible=feasible,
        rejection_reasons=rejection_reasons,
        boundary_flux_cases=flux_cases,
        magnetic_loss=magnetic_loss,
        thermal_estimate=thermal,
        primary_rms_current_design_a=inputs.primary_current_rms_a,
        secondary_rms_current_design_a=inputs.secondary_current_rms_a,
        current_basis_label="LLC FHA transformer winding current basis",
        current_basis_corner="worst-case FHA transformer design current basis",
        frequency_basis_hz=worst_flux.fs_hz,
        flux_density_audit=flux_audit,
        notes=notes,
        warnings=warnings,
    )


def _estimate_winding(
    *,
    winding_name: str,
    turns: int,
    current_rms_a: float,
    current_peak_a: float,
    mlt_m: float,
    fs_hz: float,
    wires: list[_NormalizedWireRecord],
) -> LLCTransformerWindingEstimate | None:
    if turns <= 0 or current_rms_a <= 0.0 or mlt_m <= 0.0:
        return None
    selected: tuple[_NormalizedWireRecord, int, float] | None = None
    for wire in sorted(wires, key=lambda item: (item.bundle_copper_area_m2, item.wire_id)):
        for parallel in range(1, 13):
            conductor_area_mm2 = wire.bundle_copper_area_m2 * parallel * 1e6
            current_density = current_rms_a / max(conductor_area_mm2, 1e-12)
            if current_density <= DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2:
                score = conductor_area_mm2
                if selected is None or score < selected[2]:
                    selected = (wire, parallel, score)
                break
    if selected is None:
        return None
    wire, parallel, _ = selected
    conductor_area_m2 = wire.bundle_copper_area_m2 * parallel
    conductor_area_mm2 = conductor_area_m2 * 1e6
    current_density = current_rms_a / max(conductor_area_mm2, 1e-12)
    total_strands = max(wire.strands_per_bundle * parallel, 1)
    dc_resistance_ohm = COPPER_RESISTIVITY_25C_OHM_M * mlt_m * turns / max(conductor_area_m2, 1e-18)
    ac_multiplier = _ac_resistance_multiplier(wire.strand_diameter_m, total_strands, fs_hz)
    ac_resistance_ohm = dc_resistance_ohm * ac_multiplier
    copper_loss_w = current_rms_a**2 * ac_resistance_ohm
    fill_area_mm2 = turns * parallel * wire.bundle_copper_area_m2 * LITZ_PACKING_FACTOR * 1e6
    winding_evidence = build_winding_electrical_evidence(
        wire_id=wire.stable_wire_id or wire.wire_id,
        wire_name=wire.wire_name or wire.wire_id,
        source_wire_record=wire.source_wire_record or {
            "source_kind": "caller_supplied_llc_wire",
            "wire_id": wire.stable_wire_id or wire.wire_id,
            "wire_name": wire.wire_name or wire.wire_id,
        },
        conducting_area_m2=wire.bundle_copper_area_m2,
        area_basis=wire.conducting_area_basis,
        strand_diameter_m=wire.strand_diameter_m,
        strand_count=wire.strands_per_bundle,
        parallel_winding_count=parallel,
        turns=turns,
        mean_length_per_turn_m=mlt_m,
        resistance_temperature_c=25.0,
        resistance_temperature_factor=1.0,
        rac_multiplier=ac_multiplier,
        rms_current_a=current_rms_a,
        fill_area_m2=fill_area_mm2 * 1e-6,
    )
    bundle_equivalent_diameter_m = wire.equivalent_bundle_diameter_m * sqrt(parallel)
    turns_per_layer = max(1, int(round(mlt_m / max(bundle_equivalent_diameter_m, 1e-12))))
    layer_count = max(1, ceil(turns / turns_per_layer))
    radial_build_m = layer_count * bundle_equivalent_diameter_m
    occupied_height_m = min(turns, turns_per_layer) * bundle_equivalent_diameter_m
    return LLCTransformerWindingEstimate(
        winding_name=winding_name,
        turns=turns,
        current_rms_a=current_rms_a,
        current_peak_a=current_peak_a,
        current_density_a_per_mm2=current_density,
        conductor_area_mm2=conductor_area_mm2,
        selected_wire_id=wire.wire_id,
        strands_or_parallel=parallel,
        dc_resistance_ohm=dc_resistance_ohm,
        ac_resistance_ohm=ac_resistance_ohm,
        copper_loss_w=copper_loss_w,
        fill_area_mm2=fill_area_mm2,
        bundle_equivalent_diameter_m=bundle_equivalent_diameter_m,
        turns_per_layer=turns_per_layer,
        layer_count=layer_count,
        radial_build_m=radial_build_m,
        occupied_height_m=occupied_height_m,
        notes=[
            "Selected first wire/parallel option satisfying the RMS current-density limit.",
        ],
        warnings=[
            "Transformer winding design is first-pass and does not optimize layer ordering, proximity effects, creepage, clearance, or termination layout.",
        ],
        winding_evidence=winding_evidence,
    )


def _estimate_transformer_thermal(total_loss_w: float, estimated_volume_m3: float) -> LLCTransformerThermalEstimate:
    volume_cm3 = max(estimated_volume_m3 * 1e6, 1e-9)
    rth_k_per_w = min(80.0, max(4.0, 18.0 / (volume_cm3 ** (1.0 / 3.0))))
    rise_c = total_loss_w * rth_k_per_w
    hotspot_c = DEFAULT_AMBIENT_C + rise_c
    return LLCTransformerThermalEstimate(
        hotspot_c=hotspot_c,
        temperature_rise_c=rise_c,
        ambient_c=DEFAULT_AMBIENT_C,
        thermal_margin_c=DEFAULT_HOTSPOT_LIMIT_C - hotspot_c,
        thermal_model="first_pass_volume_proxy_lumped",
        notes=[
            "Thermal estimate uses a volume-proxy lumped resistance for screening only.",
        ],
        warnings=[
            "No detailed transformer thermal, airflow, bobbin, insulation, or winding-stack model is implemented.",
        ],
    )


def _estimate_winding_volume_m3(
    primary_winding: LLCTransformerWindingEstimate | None,
    secondary_winding: LLCTransformerWindingEstimate | None,
    mlt_m: float,
) -> float:
    total_fill_area_m2 = 0.0
    for winding in (primary_winding, secondary_winding):
        if winding is not None:
            total_fill_area_m2 += winding.fill_area_mm2 * 1e-6
    return total_fill_area_m2 * mlt_m


def _resolve_candidate_source_records(
    core_records: Iterable[object] | None,
    material_records: Iterable[object] | None,
    wire_records: Iterable[object] | None,
) -> tuple[list[object], list[object], list[object], list[str]]:
    if core_records is not None and material_records is not None and wire_records is not None:
        return _records_to_list(core_records), _records_to_list(material_records), _records_to_list(wire_records), [
            "Using caller-supplied magnetic records."
        ]
    from ....engines.magnetics.data_backend import resolve_magnetic_data_backend

    bundle = resolve_magnetic_data_backend()
    return _records_to_list(bundle.cores), _records_to_list(bundle.materials), _records_to_list(bundle.wires), [
        f"Magnetic backend: {bundle.backend}.",
    ]


def _records_to_list(records: Iterable[object]) -> list[object]:
    if hasattr(records, "itertuples"):
        return list(records.itertuples())
    return list(records)


def _normalize_core_records(records: list[object]) -> tuple[list[_NormalizedCoreRecord], int]:
    normalized: list[_NormalizedCoreRecord] = []
    missing = 0
    for record in records:
        core_id = _record_str(record, ("core_id", "core_name", "Index", "name"), "")
        ae_m2 = _record_float(record, ("ae_m2", "Ae", "effective_area_m2"))
        ae_source_field = _record_source_field(record, ("ae_m2", "Ae", "effective_area_m2"))
        le_m = _record_float(record, ("le_m", "le", "magnetic_path_length_m"))
        ve_m3 = _record_float(record, ("ve_m3", "Ve", "effective_volume_m3"))
        window_area_m2 = _record_float(record, ("window_area_m2", "Aw", "window_area"))
        outer_width_m = _record_float(record, ("outer_width_m", "width_m", "core_width_m"), 0.0)
        outer_height_m = _record_float(record, ("outer_height_m", "height_m", "core_height_m"), 0.0)
        mlt_m = _record_float(record, ("mean_length_per_turn_m", "mlt"), le_m)
        gross_volume_m3 = _record_float(record, ("gross_volume_m3", "gross_volume"), ve_m3)
        if not core_id or min(ae_m2, le_m, ve_m3, window_area_m2, mlt_m, gross_volume_m3) <= 0.0:
            missing += 1
            continue
        normalized.append(
            _NormalizedCoreRecord(
                core_id=core_id,
                ae_m2=ae_m2,
                ae_source_field=ae_source_field,
                le_m=le_m,
                ve_m3=ve_m3,
                window_area_m2=window_area_m2,
                outer_width_m=outer_width_m,
                outer_height_m=outer_height_m,
                mean_length_per_turn_m=mlt_m,
                gross_volume_m3=gross_volume_m3,
            )
        )
    return normalized, missing


def _normalize_material_records(records: list[object]) -> tuple[list[_NormalizedMaterialRecord], int]:
    normalized: list[_NormalizedMaterialRecord] = []
    missing = 0
    for record in records:
        material_id = _record_str(record, ("material_id", "mat_name", "Index", "material_name"), "")
        b_sat_t = _record_float(record, ("b_sat_t", "B_sat"), 0.0)
        steinmetz_ranges = _record_value(record, ("steinmetz_ranges",), [])
        if not material_id or b_sat_t <= 0.0 or not isinstance(steinmetz_ranges, list):
            missing += 1
            continue
        normalized.append(
            _NormalizedMaterialRecord(
                material_id=material_id,
                b_sat_t=b_sat_t,
                steinmetz_ranges=[dict(item) for item in steinmetz_ranges if isinstance(item, dict)],
                f_min_recommended_hz=_record_float(record, ("f_min_recommended", "frequency_min_hz"), 0.0) or None,
                f_max_recommended_hz=_record_float(record, ("f_max_recommended", "frequency_max_hz"), 0.0) or None,
                material_metric_source=_record_str(record, ("material_metric_source",), ""),
            )
        )
    return normalized, missing


def _normalize_wire_records(records: list[object]) -> tuple[list[_NormalizedWireRecord], int]:
    normalized: list[_NormalizedWireRecord] = []
    missing = 0
    for record in records:
        wire_id = _record_str(record, ("wire_id", "Index", "wire_name"), "")
        strand_diameter_m = _record_float(record, ("strand_diameter_m", "d_strand"), 0.0)
        strands_per_bundle = int(_record_float(record, ("strands_per_bundle",), 1.0))
        bundle_copper_area_m2 = _record_float(record, ("bundle_copper_area_m2", "bundle_copper_area"), 0.0)
        outer_diameter_m = _record_float(record, ("outer_diameter_m", "outer_diameter"), strand_diameter_m)
        stable_wire_id = _record_str(record, ("stable_wire_id",), wire_id)
        wire_name = _record_str(record, ("wire_name",), wire_id)
        source_wire_record = _record_value(record, ("source_wire_record",), {})
        if not isinstance(source_wire_record, Mapping):
            source_wire_record = {}
        area_basis = _record_str(record, ("conducting_area_basis",), "engine_bundle_copper_area")
        if not wire_id or min(strand_diameter_m, bundle_copper_area_m2, outer_diameter_m) <= 0.0 or strands_per_bundle <= 0:
            missing += 1
            continue
        normalized.append(
            _NormalizedWireRecord(
                wire_id=wire_id,
                strand_diameter_m=strand_diameter_m,
                strands_per_bundle=strands_per_bundle,
                bundle_copper_area_m2=bundle_copper_area_m2,
                outer_diameter_m=outer_diameter_m,
                equivalent_bundle_diameter_m=outer_diameter_m,
                stable_wire_id=stable_wire_id,
                wire_name=wire_name,
                source_wire_record=dict(source_wire_record),
                conducting_area_basis=area_basis,
            )
        )
    return normalized, missing


def _limit_records(records: list[Any], limit: int | None) -> list[Any]:
    if limit is None or limit <= 0 or len(records) <= limit:
        return records
    return records[:limit]


def _select_search_cores(
    cores: list[_NormalizedCoreRecord],
    inputs: LLCTransformerDesignInputs,
    limit: int | None,
) -> list[_NormalizedCoreRecord]:
    sorted_cores = sorted(cores, key=lambda item: (item.ve_m3, item.core_id))
    if limit is None or limit <= 0 or len(sorted_cores) <= limit:
        return sorted_cores
    fs_ref = max(inputs.fs_min_hz, 1.0)
    current_density_a_per_m2 = DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2 * 1e6
    area_product_target = inputs.pout_max_w / max(
        0.22 * current_density_a_per_m2 * inputs.b_limit_t * fs_ref,
        1e-18,
    )
    plausible = [
        core
        for core in sorted_cores
        if core.ae_m2 * core.window_area_m2 >= 0.20 * area_product_target
    ]
    selected = _spread_records(plausible or sorted_cores, limit)
    return sorted(selected, key=lambda item: (item.ve_m3, item.core_id))


def _select_search_wires(
    wires: list[_NormalizedWireRecord],
    inputs: LLCTransformerDesignInputs,
    limit: int | None,
) -> list[_NormalizedWireRecord]:
    sorted_wires = sorted(wires, key=lambda item: (item.bundle_copper_area_m2, item.wire_id))
    if limit is None or limit <= 0 or len(sorted_wires) <= limit:
        return sorted_wires
    required_area_m2 = max(inputs.primary_current_rms_a, inputs.secondary_current_rms_a) / (
        DEFAULT_CURRENT_DENSITY_LIMIT_A_PER_MM2 * 1e6
    )
    plausible = [
        wire
        for wire in sorted_wires
        if required_area_m2 / 12.0 <= wire.bundle_copper_area_m2 <= required_area_m2 * 1.50
    ]
    selected = _spread_records(plausible or sorted_wires, limit)
    return sorted(selected, key=lambda item: (item.bundle_copper_area_m2, item.wire_id))


def _spread_records(records: list[Any], limit: int) -> list[Any]:
    if len(records) <= limit:
        return list(records)
    if limit <= 1:
        return [records[0]]
    selected: list[Any] = []
    last_index = len(records) - 1
    for offset in range(limit):
        index = round(offset * last_index / (limit - 1))
        item = records[index]
        if item not in selected:
            selected.append(item)
    return selected


def _resolve_boundary_frequency(
    inputs: LLCTransformerDesignInputs,
    case_name: str,
    vin_v: float,
    vout_v: float,
    pout_w: float,
    frequency_solver: FrequencySolver | None,
) -> tuple[float, list[str], str]:
    if frequency_solver is None:
        return inputs.fs_min_hz, [
            "No FHA boundary frequency solver was supplied; using fs_min fallback for conservative saturation check."
        ], "fs_min_fallback"
    try:
        fs_hz = float(frequency_solver(inputs, case_name, vin_v, vout_v, pout_w))
        if fs_hz <= 0.0:
            raise ValueError("Solver returned non-positive frequency.")
        return fs_hz, ["FHA boundary frequency solver supplied this case frequency."], "fha_solver"
    except Exception as exc:
        return inputs.fs_min_hz, [
            f"FHA boundary frequency solve failed for {case_name}; using fs_min fallback: {exc}"
        ], "fs_min_fallback"


def _validate_core_record(core: LLCTransformerCoreRecord) -> None:
    if core.ae_m2 <= 0.0 or core.le_m <= 0.0 or core.ve_m3 <= 0.0:
        raise ValueError("Core effective area, path length, and volume must be positive.")


def _record_value(record: object, names: tuple[str, ...], fallback: object = None) -> object:
    if isinstance(record, dict):
        for name in names:
            if name in record:
                return record[name]
        return fallback
    for name in names:
        if hasattr(record, name):
            return getattr(record, name)
    return fallback


def _record_source_field(record: object, names: tuple[str, ...]) -> str:
    if isinstance(record, dict):
        for name in names:
            if name in record:
                return name
        return ""
    for name in names:
        if hasattr(record, name):
            return name
    return ""


def _record_float(record: object, names: tuple[str, ...], fallback: float = 0.0) -> float:
    value = _record_value(record, names, fallback)
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _record_str(record: object, names: tuple[str, ...], fallback: str = "") -> str:
    value = _record_value(record, names, fallback)
    return str(value) if value is not None else fallback


def _frequency_in_range(fs_hz: float, minimum_hz: float | None, maximum_hz: float | None) -> bool:
    return (minimum_hz is None or fs_hz >= minimum_hz) and (maximum_hz is None or fs_hz <= maximum_hz)


def _display_frequency_bound(value_hz: float | None) -> str:
    return "unbounded" if value_hz is None else f"{value_hz:.6g}"


def _ac_resistance_multiplier(strand_diameter_m: float, total_strands: int, fs_hz: float) -> float:
    if strand_diameter_m <= 0.0 or fs_hz <= 0.0 or total_strands <= 0:
        return 1.0
    skin_depth_m = sqrt(COPPER_RESISTIVITY_25C_OHM_M / (pi * fs_hz * MU0_H_PER_M))
    if skin_depth_m <= 0.0:
        return 1.0
    x = strand_diameter_m / skin_depth_m
    return 1.0 + ((x**4) / 192.0) * sqrt(float(total_strands))


def _count_rejection(candidates: list[LLCTransformerScreeningCandidate], reason_token: str) -> int:
    return sum(
        1
        for candidate in candidates
        if any(reason_token in reason for reason in candidate.rejection_reasons)
    )


def _count_warning(candidates: list[LLCTransformerScreeningCandidate], warning_token: str) -> int:
    token = warning_token.lower()
    return sum(
        1
        for candidate in candidates
        if any(token in warning.lower() for warning in candidate.warnings)
    )


def _hard_missing_data_reason_counts(candidates: list[LLCTransformerScreeningCandidate]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for candidate in candidates:
        for reason in candidate.rejection_reasons:
            if reason.startswith("missing_data_hard"):
                counts[reason] += 1
    return dict(counts)


def _candidate_diagnostic(candidate: LLCTransformerScreeningCandidate, b_limit_t: float | None = None) -> dict[str, object]:
    b_peak_to_limit_ratio = (
        candidate.max_b_peak_t / b_limit_t
        if b_limit_t is not None and b_limit_t > 0.0
        else None
    )
    return {
        "candidate_id": candidate.candidate_id,
        "core_id": candidate.core_id,
        "material_id": candidate.material_id,
        "np": candidate.np,
        "ns": candidate.ns,
        "scale_factor": candidate.scale_factor,
        "np_required_by_saturation": candidate.np_required_by_saturation,
        "scale_min_by_saturation": candidate.scale_min_by_saturation,
        "scale_factor_range_used": candidate.scale_factor_range_used,
        "max_b_peak_t": candidate.max_b_peak_t,
        "b_peak_to_limit_ratio": b_peak_to_limit_ratio,
        "fill_factor": candidate.fill_factor,
        "fill_limit": candidate.fill_limit,
        "window_area_m2": candidate.window_area_m2,
        "total_fill_area_m2": candidate.total_fill_area_m2,
        "rejection_reasons": ";".join(candidate.rejection_reasons),
    }


def _closest_saturation_candidates(
    candidates: list[LLCTransformerScreeningCandidate],
    b_limit_t: float,
    limit: int = 5,
) -> list[dict[str, object]]:
    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate.max_b_peak_t,
            candidate.fill_factor,
            candidate.candidate_id,
        ),
    )
    return [_candidate_diagnostic(candidate, b_limit_t) for candidate in sorted_candidates[:limit]]


def _closest_fill_candidates(
    candidates: list[LLCTransformerScreeningCandidate],
    limit: int = 5,
) -> list[dict[str, object]]:
    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate.fill_factor / max(candidate.fill_limit, 1e-18),
            candidate.max_b_peak_t,
            candidate.candidate_id,
        ),
    )
    return [_candidate_diagnostic(candidate) for candidate in sorted_candidates[:limit]]


def _scale_search_diagnostics(
    candidates: list[LLCTransformerScreeningCandidate],
    skipped_core_diagnostics: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    skipped = list(skipped_core_diagnostics or [])
    diagnostics: dict[str, object] = {}
    if candidates:
        diagnostics.update(
            {
                "np_required_min": min(candidate.np_required_by_saturation for candidate in candidates),
                "np_required_max": max(candidate.np_required_by_saturation for candidate in candidates),
                "scale_min_by_saturation_min": min(candidate.scale_min_by_saturation for candidate in candidates),
                "scale_min_by_saturation_max": max(candidate.scale_min_by_saturation for candidate in candidates),
                "max_scale_factor_used": max(candidate.max_scale_factor_used for candidate in candidates),
                "scale_factor_range_min": min(candidate.scale_factor_range_used[0] for candidate in candidates),
                "scale_factor_range_max": max(candidate.scale_factor_range_used[1] for candidate in candidates),
            }
        )
    if skipped:
        diagnostics.update(
            {
                "skipped_core_count": len(skipped),
                "sample_skipped_core_ids": [str(item.get("core_id")) for item in skipped[:5]],
                "skipped_core_required_turns_max": max(
                    int(item.get("np_required_by_saturation") or 0) for item in skipped
                ),
                "skipped_core_scale_min_max": max(int(item.get("scale_min_by_saturation") or 0) for item in skipped),
                "scale_upper_bound": max(int(item.get("scale_upper_bound") or 0) for item in skipped),
                "skipped_core_reasons": dict(Counter(str(item.get("skip_reason") or "unknown") for item in skipped)),
            }
        )
    return diagnostics


def _leakage_rejection_audit(candidates: list[LLCTransformerScreeningCandidate]) -> dict[str, object]:
    rejected = [candidate for candidate in candidates if _has_leakage_rejection(candidate)]
    finite_rejected = [candidate for candidate in rejected if _is_finite(candidate.lk_over_lr)]
    ratios = [candidate.lk_over_lr_percent for candidate in finite_rejected]
    heights = [candidate.leakage_effective_height_mm for candidate in finite_rejected if _is_finite(candidate.leakage_effective_height_m)]
    lk_values = [candidate.estimated_lk_uH for candidate in finite_rejected if _is_finite(candidate.estimated_lk_h)]
    height_source_counts = Counter(candidate.leakage_height_source for candidate in rejected if candidate.leakage_height_source)
    status_counts = Counter(candidate.leakage_status for candidate in rejected)
    fallback_count = sum(1 for candidate in rejected if candidate.leakage_used_legacy_fallback)
    layer_based_count = sum(1 for candidate in rejected if candidate.leakage_method == "layer_based_first_order")
    invalid_count = sum(
        1
        for candidate in rejected
        if not _is_finite(candidate.lk_over_lr) or not _is_finite(candidate.leakage_effective_height_m) or not _is_finite(candidate.estimated_lk_h)
    )
    unexpected_below_threshold = sum(1 for candidate in finite_rejected if candidate.lk_over_lr <= 0.80)
    audit = {
        "rejected_by_leakage": len(rejected),
        "finite_lk_over_lr_count": len(finite_rejected),
        "non_finite_or_missing_lk_over_lr_count": len(rejected) - len(finite_rejected),
        "fallback_leakage_count": fallback_count,
        "layer_based_leakage_count": layer_based_count,
        "height_source_counts": dict(height_source_counts),
        "leakage_status_counts": dict(status_counts),
        "unexpected_leakage_rejects_below_threshold": unexpected_below_threshold,
        "invalid_leakage_diagnostics_count": invalid_count,
        "lk_over_lr_percent_stats": _percentile_stats(ratios),
        "leakage_effective_height_mm_stats": _scalar_stats(heights),
        "estimated_lk_uH_stats": _scalar_stats(lk_values),
    }
    audit["audit_rows"] = [
        {"metric": "rejected_by_leakage", "value": audit["rejected_by_leakage"]},
        {"metric": "finite_lk_over_lr_count", "value": audit["finite_lk_over_lr_count"]},
        {"metric": "non_finite_or_missing_lk_over_lr_count", "value": audit["non_finite_or_missing_lk_over_lr_count"]},
        {"metric": "fallback_leakage_count", "value": audit["fallback_leakage_count"]},
        {"metric": "layer_based_leakage_count", "value": audit["layer_based_leakage_count"]},
        {"metric": "unexpected_leakage_rejects_below_threshold", "value": audit["unexpected_leakage_rejects_below_threshold"]},
        {"metric": "invalid_leakage_diagnostics_count", "value": audit["invalid_leakage_diagnostics_count"]},
    ]
    return audit


def _percentile_stats(values: list[float]) -> dict[str, float]:
    if not values:
        nan = float("nan")
        return {"min": nan, "p25": nan, "median": nan, "p75": nan, "p90": nan, "p95": nan, "max": nan}
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "p25": _percentile(ordered, 25.0),
        "median": median(ordered),
        "p75": _percentile(ordered, 75.0),
        "p90": _percentile(ordered, 90.0),
        "p95": _percentile(ordered, 95.0),
        "max": ordered[-1],
    }


def _scalar_stats(values: list[float]) -> dict[str, float]:
    if not values:
        nan = float("nan")
        return {"min": nan, "median": nan, "max": nan}
    ordered = sorted(values)
    return {"min": ordered[0], "median": median(ordered), "max": ordered[-1]}


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return float("nan")
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * percentile / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    fraction = rank - lower
    return values[lower] + ((values[upper] - values[lower]) * fraction)


def _has_leakage_rejection(candidate: LLCTransformerScreeningCandidate) -> bool:
    return any("leakage" in reason for reason in candidate.rejection_reasons)


def _is_finite(value: object) -> bool:
    try:
        return not (value is None or value != value or value in (float("inf"), float("-inf")))
    except TypeError:
        return False


def _percentile_stats(values: list[float]) -> dict[str, float]:
    if not values:
        nan = float("nan")
        return {"min": nan, "p25": nan, "median": nan, "p75": nan, "p90": nan, "p95": nan, "max": nan}
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "p25": _percentile(ordered, 25.0),
        "median": median(ordered),
        "p75": _percentile(ordered, 75.0),
        "p90": _percentile(ordered, 90.0),
        "p95": _percentile(ordered, 95.0),
        "max": ordered[-1],
    }


def _scalar_stats(values: list[float]) -> dict[str, float]:
    if not values:
        nan = float("nan")
        return {"min": nan, "median": nan, "max": nan}
    ordered = sorted(values)
    return {"min": ordered[0], "median": median(ordered), "max": ordered[-1]}


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return float("nan")
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * percentile / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    fraction = rank - lower
    return values[lower] + ((values[upper] - values[lower]) * fraction)


def _dedupe_text(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(str(value).split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(str(value))
    return deduped


def _screened_sample(candidates: list[LLCTransformerScreeningCandidate], limit: int = 25) -> list[LLCTransformerScreeningCandidate]:
    if len(candidates) <= limit:
        return list(candidates)
    rejected = [candidate for candidate in candidates if not candidate.feasible]
    feasible = [candidate for candidate in candidates if candidate.feasible]
    return [*feasible[: max(limit // 2, 1)], *rejected[: max(limit - len(feasible[: max(limit // 2, 1)]), 0)]]


def _transformer_candidate_id(core_id: str, material_id: str, np_turns: int, ns_turns: int) -> str:
    raw = f"{core_id}_{material_id}_Np{np_turns}_Ns{ns_turns}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _read_float_from_mapping(mapping: object, key: str, fallback: float) -> float:
    if isinstance(mapping, dict) and isinstance(mapping.get(key), (int, float)):
        return float(mapping[key])
    return fallback


def _max_reflected_load_current_rms(design: object) -> float:
    corner_estimates = getattr(design, "current_estimates_by_corner", [])
    values = [
        float(estimate["reflected_load_current_rms_a"])
        for estimate in corner_estimates
        if isinstance(estimate, dict) and isinstance(estimate.get("reflected_load_current_rms_a"), (int, float))
    ]
    nominal = _read_float_from_mapping(
        getattr(design, "current_estimates_nominal_full_load", {}),
        "reflected_load_current_rms_a",
        0.0,
    )
    values.append(nominal)
    return max(values)
