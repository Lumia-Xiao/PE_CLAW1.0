"""AC-DC bridge-rectifier selection handoff models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BridgeRectifierSelectionRequest:
    """Design-point requirements for selecting an AC-DC diode bridge."""

    topology_id: str
    ac_input_rms_v: float
    dc_bus_voltage_v: float
    output_power_w: float
    dc_output_current_a: float
    bridge_current_avg_a: float
    bridge_current_rms_a: float
    required_reverse_voltage_v: float
    line_frequency_hz: float
    bridge_current_waveform_a: tuple[float, ...] = ()
    recommended_reverse_voltage_v: float | None = None
    voltage_margin_basis: str = ""
    voltage_margin_policy: str = "stress_with_margin_warning"
    ambient_temp_c: float = 25.0
    target_junction_temp_c: float = 125.0
    voltage_margin: float = 1.20
    current_margin: float = 1.10
    thermal_mode: str = "rough_rth_ja"
    data_confidence_policy: str = "allow_rough_estimates"
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class BridgeRectifierCandidate:
    """One normalized bridge-rectifier candidate."""

    candidate_id: str
    part_number: str
    manufacturer: str
    digikey_part_number: str
    package_family: str
    package_case: str
    mounting_type: str
    v_rrm_v: float
    io_avg_rectified_a: float
    vf_max_v: float
    vf_test_current_a: float
    tj_min_c: float
    tj_max_c: float
    body_length_mm: float
    body_width_mm: float
    body_height_mm: float
    unit_price_usd: float
    stock_qty: float
    rth_jc_k_per_w: float | None = None
    rth_ja_k_per_w: float | None = None
    rth_jl_k_per_w: float | None = None
    leakage_current_a: float | None = None
    leakage_test_voltage_v: float | None = None
    thermal_condition: str = ""
    package_dimension_status: str = ""
    thermal_status: str = ""
    datasheet_url: str = ""
    digikey_url: str = ""
    source_notes: tuple[str, ...] = ()
    topology_kind: str = ""

    @property
    def body_volume_mm3(self) -> float:
        """Return the rough package body volume used for first-pass ranking."""

        return self.body_length_mm * self.body_width_mm * self.body_height_mm


@dataclass(frozen=True)
class BridgeRectifierLossEstimate:
    """First-pass loss estimate for one bridge candidate."""

    conduction_loss_w: float
    total_loss_w: float
    vf_used_v: float
    current_basis_a: float
    current_basis_label: str = "bridge_current_avg_a"
    waveform_sample_count: int = 0
    conducting_diode_count: int = 2
    method: str = "two_diode_vf_constant"
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class BridgeRectifierThermalEstimate:
    """First-pass bridge thermal estimate tied to a candidate and loss estimate."""

    rth_used_k_per_w: float | None
    rth_basis: str
    ambient_temp_c: float
    target_junction_temp_c: float
    tj_est_c: float | None
    junction_margin_c: float | None
    feasible: bool | None
    method: str = "rough_package_family_estimate"
    bare_rthja_tj_est_c: float | None = None
    bare_rthja_margin_c: float | None = None
    required_sink_rth_k_per_w: float | None = None
    estimated_sink_volume_cm3: float | None = None
    sink_thermal_classification: str = ""
    sink_volume_model: str = ""
    rth_cs_k_per_w: float | None = None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class BridgeRectifierRankingBreakdown:
    """Deterministic score components used to rank accepted bridge candidates."""

    loss_w: float
    tj_est_c: float | None
    unit_price_usd: float
    body_volume_cm3: float
    thermal_over_target_c: float
    normalized_loss: float
    normalized_tj: float
    normalized_price: float
    normalized_volume: float
    loss_score_component: float
    tj_score_component: float
    price_score_component: float
    volume_score_component: float
    thermal_penalty_component: float
    total_score: float
    data_confidence_penalty_component: float = 0.0
    data_confidence_policy: str = "allow_rough_estimates"
    loss_weight: float = 0.60
    tj_weight: float = 0.25
    price_weight: float = 0.10
    volume_weight: float = 0.05
    method: str = "normalized_loss_tj_price_volume"


@dataclass(frozen=True)
class BridgeRectifierCandidateEvaluation:
    """Audit record for one bridge candidate under one selection request."""

    candidate: BridgeRectifierCandidate
    passed_voltage: bool
    passed_current: bool
    passed_price: bool
    passed_package_data: bool
    passed_vf_data: bool
    passed_thermal_data: bool
    passed_recommended_voltage_margin: bool | None = None
    passed_thermal: bool | None = None
    loss_estimate: BridgeRectifierLossEstimate | None = None
    thermal_estimate: BridgeRectifierThermalEstimate | None = None
    ranking_score: float | None = None
    ranking_breakdown: BridgeRectifierRankingBreakdown | None = None
    rejection_reasons: tuple[str, ...] = ()
    advisory_notes: tuple[str, ...] = ()
    ranking_notes: tuple[str, ...] = ()

    @property
    def passed_hard_filters(self) -> bool:
        """Return whether the deterministic hard filters accepted this candidate."""

        required_passes = (
            self.passed_voltage,
            self.passed_recommended_voltage_margin is not False,
            self.passed_current,
            self.passed_price,
            self.passed_package_data,
            self.passed_vf_data,
            self.passed_thermal_data,
        )
        return all(required_passes) and self.passed_thermal is not False


@dataclass(frozen=True)
class BridgeRectifierSelectionResult:
    """Result container for future bridge-rectifier selector output."""

    request: BridgeRectifierSelectionRequest
    candidate_count: int
    passed_candidate_count: int
    selected_candidate: BridgeRectifierCandidate | None = None
    evaluations: tuple[BridgeRectifierCandidateEvaluation, ...] = ()
    rejection_summary: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def bridge_rectifier_package_confidence_label(candidate: BridgeRectifierCandidate) -> str:
    """Return a concise provenance label for package dimensions."""

    base = _bridge_rectifier_status_confidence(candidate.package_dimension_status)
    detail = _source_note_value(candidate.source_notes, "package_dimensions")
    return _append_detail(base, detail)


def bridge_rectifier_thermal_confidence_label(
    candidate: BridgeRectifierCandidate,
    thermal: BridgeRectifierThermalEstimate | None = None,
) -> str:
    """Return a concise provenance label for thermal-resistance data."""

    base = _bridge_rectifier_status_confidence(candidate.thermal_status)
    detail = _source_note_value(candidate.source_notes, "thermal")
    parts = [_append_detail(base, detail)]
    if thermal is not None and thermal.rth_basis:
        parts.append(f"basis={thermal.rth_basis}")
    if candidate.thermal_condition:
        parts.append(f"condition={candidate.thermal_condition}")
    if any("module_rthja_not_comparable_or_missing" in note for note in candidate.source_notes):
        parts.append("RthJA missing/not comparable")
    return ", ".join(parts)


def bridge_rectifier_data_confidence_summary(
    candidate: BridgeRectifierCandidate,
    thermal: BridgeRectifierThermalEstimate | None = None,
) -> str:
    """Return a compact package/thermal confidence summary for dense views."""

    package_label = _bridge_rectifier_status_confidence(candidate.package_dimension_status)
    thermal_label = _bridge_rectifier_status_confidence(candidate.thermal_status)
    if thermal is not None and thermal.rth_basis:
        thermal_label = f"{thermal_label} (basis={thermal.rth_basis})"
    return f"package {package_label}, thermal {thermal_label}"


def _bridge_rectifier_status_confidence(status: str) -> str:
    normalized = (status or "").strip().lower()
    if not normalized:
        return "status not labeled"
    if normalized.startswith("rough_"):
        return "rough package-family estimate"
    if "datasheet" in normalized and "rough" not in normalized:
        return "datasheet-derived"
    return normalized.replace("_", " ")


def _source_note_value(notes: tuple[str, ...], key: str) -> str:
    prefix = f"{key}="
    for note in notes:
        if note.startswith(prefix):
            return note[len(prefix) :].strip()
    return ""


def _append_detail(base: str, detail: str) -> str:
    return f"{base} ({detail})" if detail else base
