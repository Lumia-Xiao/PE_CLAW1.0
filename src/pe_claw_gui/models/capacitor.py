"""Capacitor library, sizing, and result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CapacitorCandidate:
    """One capacitor catalog candidate with geometry-ready metadata.

    ``capacitor_technology`` describes the physical technology family used for
    filtering and loss semantics. ``application_category`` describes where the
    part is intended to be used, such as DC-link, snubber, safety, or pulse
    service.
    """

    part_number: str
    manufacturer: str
    series: str
    capacitor_type: str
    construction: str
    capacitance_f: float
    voltage_rating_ac_vrms: float
    voltage_rating_dc_v: float
    surge_voltage_v: float
    diameter_mm: float
    height_mm: float
    irms_rating_a: float
    pmax_w: float
    rs_ohm: float
    esl_h: float
    rth_hotspot_to_ambient_c_per_w: float
    dvdt_v_per_us: float
    tolerance_percent: float
    dielectric: str = ""
    hotspot_temp_max_c: float = 90.0
    tan_delta_0: float = 2e-4
    tan_delta_frequency_hz: float | None = None
    esr_frequency_hz: float | None = None
    application: str = ""
    application_category: str = ""
    application_notes: str = ""
    automotive_grade: bool = False
    safety_class: str = ""
    rated_ac_safety_vac: float | None = None
    voltage_rating_dc_peak_v: float | None = None
    operating_voltage_105c_v: float | None = None
    operating_voltage_115c_v: float | None = None
    operating_voltage_125c_v: float | None = None
    operating_voltage_135c_v: float | None = None
    ipkr_a: float | None = None
    peak_current_a: float | None = None
    irms_rating_basis: str = ""
    current_basis: str = ""
    irms_frequency_hz: float | None = None
    irms_temperature_c: float | None = None
    esr_basis: str = ""
    loss_basis: str = ""
    esr_temperature_c: float | None = None
    esl_basis: str = ""
    thermal_basis: str = ""
    self_heating_limit_c: float = 35.0
    mass_g: float | None = None
    minimum_order_quantity: int | None = None
    not_recommended_for_new_design: bool = False
    ripple_voltage_limit_ratio: float | None = None
    source: str = "KEMET C44P-T datasheet"
    source_pdf: str = ""
    notes: list[str] = field(default_factory=list)
    series_code: str = ""
    order_code_template: str = ""
    is_order_code_template: bool = False
    order_code_placeholders: list[str] = field(default_factory=list)
    order_code_note: str = ""
    reference_standard: str = ""
    operating_temperature_min_c: float | None = None
    operating_temperature_max_c: float | None = None
    package_shape: str = "cylindrical_can"
    case_type: str = ""
    low_profile: bool = False
    available_upon_request: bool = False
    terminal_type: str = "M10_male_screw"
    mounting_style: str = "screw_terminal_can"
    case_material: str = "aluminum"
    recommended_orientation: str = "terminals_on_top"
    clearance_note: str = "Maintain at least 15 mm electrical clearance above terminations for safety-device activation."
    terminal_count: int = 2
    terminal_diameter_mm: float = 10.0
    terminal_pitch_mm: float | None = None
    body_width_mm: float | None = None
    body_depth_mm: float | None = None
    body_height_mm: float | None = None
    dimension_a_mm: float | None = None
    dimension_b_mm: float | None = None
    dimension_c_mm: float | None = None
    dimension_d_mm: float | None = None
    dimension_h_mm: float | None = None
    dimension_l_mm: float | None = None
    dimension_l1_mm: float | None = None
    dimension_p1_mm: float | None = None
    dimension_p2_mm: float | None = None
    width_t_mm: float | None = None
    height_h_mm: float | None = None
    length_l_mm: float | None = None
    lead_pitch_f_mm: float | None = None
    lead_pitch_ls_mm: float | None = None
    lead_spacing_mm: float | None = None
    lead_spacing_secondary_mm: float | None = None
    lead_spacing_s_mm: float | None = None
    lead_spacing_s1_mm: float | None = None
    lead_length_mm: float | None = None
    lead_length_ll_mm: float | None = None
    lead_diameter_mm: float | None = None
    lead_diameter_f_mm: float | None = None
    total_volume_cm3: float | None = None
    body_color: str = "aluminum"
    spq: int | None = None
    esr_mohm: float | None = None
    ls_nh: float | None = None
    irms_60c_1khz_a: float | None = None
    irms_50c_1khz_a: float | None = None
    irms_40c_1khz_a: float | None = None
    irms_70c_10khz_a: float | None = None
    integration_note: str = ""
    esr_value_type: str = ""
    loss_model_type: str = "film_default"
    availability_status: str = "standard"
    capacitor_technology: str = "film"
    family: str = ""
    design_option: str = ""
    ordering_code_template: str = ""
    expanded_ordering_code: str = ""
    capacitance_tolerance_percent: float | None = None
    esr_typ_ohm: float | None = None
    esr_max_ohm: float | None = None
    impedance_max_ohm: float | None = None
    impedance_frequency_hz: float | None = None
    impedance_temperature_c: float | None = None
    ripple_current_max_a: float | None = None
    ripple_current_max_frequency_hz: float | None = None
    ripple_current_max_temperature_c: float | None = None
    ripple_current_rated_a: float | None = None
    ripple_current_rated_frequency_hz: float | None = None
    ripple_current_rated_temperature_c: float | None = None
    endurance_hours: float | None = None
    endurance_temperature_c: float | None = None
    useful_life_hours: float | None = None
    useful_life_reference: str = ""
    tan_delta: float | None = None
    tan_delta_source: str = ""
    correction_curve_available: bool = False
    correction_curve_source: str = ""
    data_source: str = ""


@dataclass(frozen=True)
class CapacitorSizingRequest:
    """Waveform-based capacitor sizing request."""

    side: str
    dc_voltage_v: float
    ripple_ratio_percent: float
    current_time_s: list[float]
    current_waveform_a: list[float]
    switching_frequency_hz: float
    ambient_temp_c: float
    voltage_waveform_v: list[float] | None = None
    voltage_margin: float = 1.2
    allow_parallel: bool = True
    max_parallel_count: int = 5
    max_series_count: int = 1
    include_non_dc_link_capacitors: bool = False
    capacitance_min_f: float = 0.0
    voltage_required_v: float = 0.0
    rms_current_required_a: float = 0.0
    role: str = ""
    design_type: str = ""
    basis: str = ""
    topology_id: str = ""
    pout_design_w: float = 0.0
    vac_rms_v: float = 0.0
    f_line_hz: float = 0.0
    allowed_capacitor_technologies: tuple[str, ...] | None = None
    include_epcos_screw_terminal_electrolytics: bool = False


@dataclass(frozen=True)
class LlcResonantCapacitorDesignRequest:
    """Pending LLC resonant capacitor design request built from FHA tank stress."""

    cr_target_f: float
    cr_target_nF: float
    lr_target_h: float
    lr_total_actual_h: float
    transformer_lk_h: float
    external_lr_actual_h: float
    current_rms_a: float
    current_peak_a: float
    current_basis: str
    voltage_rms_v: float
    voltage_peak_v: float
    voltage_basis: str
    voltage_rating_basis: str
    voltage_margin_factor: float
    required_voltage_rating_v: float
    fs_basis_hz: float
    fs_min_hz: float
    fs_max_hz: float
    frequency_basis: str
    is_design_required: bool
    warning: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LlcResonantCapacitorBankCandidate:
    """One first-pass LLC resonant capacitor bank candidate."""

    design_id: str
    part_number: str
    manufacturer: str
    series: str
    application_category: str
    capacitance_f: float
    capacitance_nF: float
    capacitance_tolerance_percent: float
    parallel_count: int
    bank_capacitance_f: float
    bank_capacitance_nF: float
    cr_target_f: float
    cr_target_nF: float
    capacitance_error_percent: float
    voltage_rating_v: float
    required_voltage_rating_v: float
    voltage_utilization: float
    current_rms_total_a: float
    current_rms_per_cap_a: float
    ripple_current_rating_a: float
    current_utilization: float
    esr_ohm: float
    esr_basis: str
    bank_esr_ohm: float
    loss_w: float
    loss_per_cap_w: float
    hotspot_c: float | None
    estimated_volume_m3: float
    estimated_volume_cm3: float
    package_shape: str = ""
    body_width_mm: float | None = None
    body_depth_mm: float | None = None
    body_height_mm: float | None = None
    diameter_mm: float = 0.0
    height_mm: float = 0.0
    terminal_count: int = 2
    terminal_diameter_mm: float = 0.0
    terminal_pitch_mm: float | None = None
    terminal_pitch_secondary_mm: float | None = None
    terminal_type: str = ""
    ambient_c: float | None = None
    temperature_rise_c: float | None = None
    is_pareto: bool = False
    representative_role: str = ""
    representative_reason: str = ""
    recommended_flag: bool = False
    warning: str = ""
    rejection_reason: str = ""


@dataclass(frozen=True)
class LlcResonantCapacitorSearchResult:
    """First-pass LLC resonant capacitor candidate search and Pareto result."""

    request: LlcResonantCapacitorDesignRequest | None = None
    candidates: list[LlcResonantCapacitorBankCandidate] = field(default_factory=list)
    feasible_candidates: list[LlcResonantCapacitorBankCandidate] = field(default_factory=list)
    pareto_candidates: list[LlcResonantCapacitorBankCandidate] = field(default_factory=list)
    chosen_candidates: list[LlcResonantCapacitorBankCandidate] = field(default_factory=list)
    recommended_candidate: LlcResonantCapacitorBankCandidate | None = None
    min_volume_candidate: LlcResonantCapacitorBankCandidate | None = None
    min_loss_candidate: LlcResonantCapacitorBankCandidate | None = None
    compromise_candidate: LlcResonantCapacitorBankCandidate | None = None
    rejection_counts: dict[str, int] = field(default_factory=dict)
    part_rejection_counts: dict[str, int] = field(default_factory=dict)
    bank_rejection_counts: dict[str, int] = field(default_factory=dict)
    coverage_summary: dict[str, object] = field(default_factory=dict)
    nearest_lower_bank: LlcResonantCapacitorBankCandidate | None = None
    nearest_upper_bank: LlcResonantCapacitorBankCandidate | None = None
    closest_absolute_error_bank: LlcResonantCapacitorBankCandidate | None = None
    lowest_loss_near_miss: LlcResonantCapacitorBankCandidate | None = None
    lowest_volume_near_miss: LlcResonantCapacitorBankCandidate | None = None
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    feasible_csv_path: str = ""
    near_miss_csv_path: str = ""
    pareto_csv_path: str = ""
    chosen_csv_path: str = ""
    pareto_png_path: str = ""
    pareto_notes: list[str] = field(default_factory=list)
    plot_diagnostics: dict[str, object] = field(default_factory=dict)
    geometry_targets: list[CapacitorGeometryTarget] = field(default_factory=list)
    geometry_artifact_paths: list[str] = field(default_factory=list)
    geometry_comparison_2d_path: str = ""
    geometry_comparison_3d_path: str = ""
    geometry_notes: list[str] = field(default_factory=list)
    geometry_diagnostics: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CapacitorSelectionEntry:
    """One evaluated capacitor candidate and series/parallel bank count."""

    candidate: CapacitorCandidate
    parallel_count: int
    equivalent_capacitance_f: float
    equivalent_rs_ohm: float
    equivalent_esl_h: float
    total_volume_cm3: float
    capacitor_current_rms_total_a: float
    capacitor_current_rms_per_cap_a: float
    capacitor_current_pp_total_a: float
    q_swing_c: float
    ripple_capacitive_pp_v: float
    ripple_esr_pp_v: float
    ripple_total_pp_v: float
    ripple_allow_v: float
    p_dielectric_w: float
    p_joule_w: float
    p_total_w: float
    p_total_per_cap_w: float
    delta_t_hotspot_c: float
    hotspot_temp_c: float
    voltage_margin_ratio: float
    current_margin_ratio: float
    loss_margin_ratio: float
    thermal_margin_c: float
    dvdt_required_v_per_us: float
    dvdt_margin_ratio: float
    feasible: bool
    rejection_reasons: list[str] = field(default_factory=list)
    score: float = 0.0
    is_pareto: bool = False
    representative_label: str = ""
    recommended_flag: bool = False
    series_count: int = 1
    bank_voltage_rating_dc_v: float = 0.0

    @property
    def total_capacitor_count(self) -> int:
        return max(int(self.series_count or 1), 1) * max(int(self.parallel_count or 1), 1)


@dataclass(frozen=True)
class CapacitorSideResult:
    """Selection result for one capacitor bank side."""

    request: CapacitorSizingRequest | None = None
    recommended: CapacitorSelectionEntry | None = None
    recommended_policy_name: str = ""
    recommended_selection_reason: str = ""
    recommended_source: str = ""
    recommended_ripple_utilization: float | None = None
    minimum_feasible_parallel_count: int | None = None
    recommended_parallel_count: int | None = None
    top_candidates: list[CapacitorSelectionEntry] = field(default_factory=list)
    feasible_candidates: list[CapacitorSelectionEntry] = field(default_factory=list)
    pareto_front: list[CapacitorSelectionEntry] = field(default_factory=list)
    min_volume: CapacitorSelectionEntry | None = None
    min_loss: CapacitorSelectionEntry | None = None
    compromise: CapacitorSelectionEntry | None = None
    evaluated_count: int = 0
    feasible_count: int = 0
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    diagnostics: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CapacitorBankLayout:
    """First-pass mechanical layout for one series/parallel capacitor bank."""

    side: str
    role: str
    label: str
    part_number: str
    parallel_count: int
    capacitance_f: float
    equivalent_capacitance_f: float
    total_loss_w: float
    total_volume_cm3: float
    package_shape: str
    can_diameter_mm: float
    can_height_mm: float
    pitch_mm: float
    footprint_width_mm: float
    footprint_depth_mm: float
    footprint_area_mm2: float
    bank_height_mm: float
    terminal_count: int
    terminal_diameter_mm: float
    terminal_pitch_mm: float | None
    terminal_pitch_secondary_mm: float | None
    terminal_type: str
    positions_mm: list[tuple[float, float]]
    series_count: int = 1
    total_capacitor_count: int = 1
    bank_voltage_rating_dc_v: float = 0.0
    grid_columns: int = 0
    grid_rows: int = 0
    body_width_mm: float | None = None
    body_depth_mm: float | None = None
    body_height_mm: float | None = None
    caption_lines: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CapacitorGeometryTarget:
    """Geometry target for one representative capacitor PF solution."""

    role: str
    label: str
    entry: CapacitorSelectionEntry | None = None
    layout: CapacitorBankLayout | None = None
    duplicate_of: str | None = None
    artifact_paths_2d: list[str] = field(default_factory=list)
    artifact_paths_3d: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error_message: str | None = None

    @property
    def artifact_paths(self) -> list[str]:
        return [*self.artifact_paths_2d, *self.artifact_paths_3d]


@dataclass(frozen=True)
class CapacitorSideGeometryResult:
    """Geometry comparison result for one capacitor side."""

    side: str
    targets: list[CapacitorGeometryTarget] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    summary: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CapacitorResult:
    """Aggregate capacitor-stage result."""

    input_selection: CapacitorSideResult | None = None
    output_selection: CapacitorSideResult | None = None
    llc_resonant_capacitor_request: LlcResonantCapacitorDesignRequest | None = None
    llc_resonant_capacitor_search_result: LlcResonantCapacitorSearchResult | None = None
    current_operating_input: CapacitorSideResult | None = None
    current_operating_output: CapacitorSideResult | None = None
    input_geometry: CapacitorSideGeometryResult | None = None
    output_geometry: CapacitorSideGeometryResult | None = None
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    diagnostics: dict[str, object] = field(default_factory=dict)


def capacitor_series_display_name(candidate: CapacitorCandidate) -> str:
    """Return a compact manufacturer/series label without duplicated vendor text."""

    manufacturer = (candidate.manufacturer or "").strip()
    series = (candidate.series or "").strip()
    if not manufacturer:
        return series or "-"
    if not series:
        return manufacturer
    if series.casefold().startswith(manufacturer.casefold()):
        return series
    return f"{manufacturer} {series}"


def capacitor_part_reference(candidate: CapacitorCandidate) -> str:
    """Return a compact part/order-code reference for inline summaries."""

    if candidate.is_order_code_template:
        return f"Order code template {candidate.order_code_template or candidate.part_number}"
    return candidate.part_number


def capacitor_part_metadata_label(candidate: CapacitorCandidate) -> str:
    """Return the metadata label used for detail panels."""

    if candidate.is_order_code_template:
        return f"Part / Order code template: {candidate.order_code_template or candidate.part_number}"
    return f"Part: {candidate.part_number}"


def capacitor_order_code_note(candidate: CapacitorCandidate) -> str:
    """Return a display note for configurable order-code templates."""

    if not candidate.is_order_code_template:
        return ""
    return (
        candidate.order_code_note
        or "Configurable ordering template; resolve placeholder options from the datasheet before purchase."
    )
