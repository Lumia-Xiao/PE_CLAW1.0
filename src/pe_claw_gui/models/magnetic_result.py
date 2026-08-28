"""Magnetic-stage result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .inductor import FixedInductorDesignCandidate, InductorOperatingEvaluation
from .ac_dc_reactor import AcDcReactorSelectionResult


@dataclass(frozen=True)
class TransformerVisualizationArtifact:
    """First-pass visualization artifact for a separated LLC transformer."""

    design_type: str = "separated_llc_transformer"
    role: str = "recommended"
    role_label: str = "Recommended"
    recommended_candidate_id: str = ""
    core_id: str = ""
    material_id: str = ""
    np: int = 0
    ns: int = 0
    gap_mm: float = 0.0
    ae_mm2: float = 0.0
    le_mm: float = 0.0
    ve_cm3: float = 0.0
    window_area_mm2: float = 0.0
    estimated_volume_cm3: float = 0.0
    fill_factor: float = 0.0
    fill_limit: float = 0.0
    primary_fill_area_mm2: float = 0.0
    secondary_fill_area_mm2: float = 0.0
    insulation_reserved_area_mm2: float = 0.0
    total_fill_area_mm2: float = 0.0
    total_loss_w: float = 0.0
    hotspot_c: float = 0.0
    primary_wire_id: str = ""
    primary_parallel: int = 0
    secondary_wire_id: str = ""
    secondary_parallel: int = 0
    image_2d_path: str = ""
    image_3d_path: str = ""
    layout_style_2d: str = ""
    layout_style_3d: str = ""
    panel_titles: tuple[str, ...] = ()
    winding_stack_proportions: dict[str, float] = field(default_factory=dict)
    render_metadata: dict[str, object] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LlcExternalResonantInductorTarget:
    """Round-1 target request for a separated LLC external resonant inductor."""

    lr_target_h: float
    transformer_lk_h: float
    external_lr_target_h: float
    external_lr_target_uH: float
    lr_total_target_h: float
    lr_external_fraction: float
    current_basis: str
    frequency_basis: str
    current_rms_a: float
    current_peak_a: float
    fs_basis_hz: float
    fs_min_hz: float
    fs_max_hz: float
    transformer_design_id: str
    transformer_leakage_method: str
    transformer_leakage_status: str
    warning: str = ""
    is_design_required: bool = True


@dataclass(frozen=True)
class LlcExternalResonantInductorCandidate:
    """First-pass separated LLC external resonant inductor candidate."""

    design_id: str
    core_id: str
    core_family: str
    material_name: str
    turns: int
    gap_m: float
    gap_mm: float
    target_l_h: float
    actual_l_h: float
    actual_l_uH: float
    inductance_error_percent: float
    transformer_lk_h: float
    transformer_lk_uH: float
    total_lr_actual_h: float
    total_lr_actual_uH: float
    total_lr_error_percent: float
    current_rms_a: float
    current_peak_a: float
    fs_basis_hz: float
    b_peak_t: float
    b_limit_t: float
    b_margin_percent: float
    fill_factor: float
    current_density_a_per_mm2: float
    core_loss_w: float
    copper_loss_w: float
    total_loss_w: float
    hotspot_c: float
    estimated_volume_m3: float
    estimated_volume_cm3: float
    wire_name: str
    wire_parallel_count: int
    warning: str = ""
    rejection_reason: str = ""
    core_effective_area_m2: float = 0.0
    core_effective_area_source_field: str = ""
    bpeak_formula: str = "L_actual_H * Ipeak_A / (turns * Ae_m2)"
    current_convention: str = "sinusoidal_peak"
    core_window_area_m2: float = 0.0
    core_width_m: float = 0.0
    core_height_m: float = 0.0
    core_depth_m: float = 0.0
    core_volume_m3: float = 0.0
    winding_volume_m3: float = 0.0
    gross_volume_m3: float = 0.0
    transformer_design_id_used_for_lk: str = ""
    external_lr_design_id: str = ""
    lr_closure_status: str = ""


@dataclass(frozen=True)
class LlcExternalResonantInductorRepresentativeSelection:
    """Named external Lr inductor Pareto representative."""

    role: str
    candidate: LlcExternalResonantInductorCandidate
    reason: str


@dataclass(frozen=True)
class LlcExternalResonantInductorSearchResult:
    """Round-2 first-pass LLC external resonant inductor screening result."""

    request: LlcExternalResonantInductorTarget
    candidates: list[LlcExternalResonantInductorCandidate] = field(default_factory=list)
    feasible_candidates: list[LlcExternalResonantInductorCandidate] = field(default_factory=list)
    pareto_candidates: list[LlcExternalResonantInductorCandidate] = field(default_factory=list)
    chosen_candidates: list[LlcExternalResonantInductorRepresentativeSelection] = field(default_factory=list)
    recommended_candidate: LlcExternalResonantInductorCandidate | None = None
    min_volume_candidate: LlcExternalResonantInductorCandidate | None = None
    min_loss_candidate: LlcExternalResonantInductorCandidate | None = None
    compromise_candidate: LlcExternalResonantInductorCandidate | None = None
    rejection_counts: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    feasible_csv_path: str = ""
    pareto_csv_path: str = ""
    chosen_csv_path: str = ""
    pareto_png_path: str = ""
    pareto_notes: list[str] = field(default_factory=list)
    plot_diagnostics: dict[str, object] = field(default_factory=dict)
    performance_timing: dict[str, float] = field(default_factory=dict)
    performance_counts: dict[str, int] = field(default_factory=dict)
    search_bounds: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MagneticResult:
    """Aggregate for magnetic design outputs."""

    summary: str = ""
    result_type: str = "fixed_inductor"
    design_type: str = ""
    design_requirements: dict[str, float | str | bool | None] = field(default_factory=dict)
    basic_feasible_count: int = 0
    post_allow_count: int = 0
    post_compression_count: int = 0
    final_post_allow_count: int = 0
    final_post_compression_count: int = 0
    pareto_count: int = 0
    feasible_count: int = 0
    frequency_band: str | None = None
    allow_profile: dict[str, float | str | None] = field(default_factory=dict)
    plot_source_name: str | None = None
    plot_color_dimension: str | None = None
    stacked_expansion_triggered: bool = False
    stacked_seed_count: int = 0
    stacked_generated_count: int = 0
    stacked_stack2_generated_count: int = 0
    stacked_stack3_generated_count: int = 0
    stacked_precheck_pass_count: int = 0
    stacked_screened_count: int = 0
    search_selected_design_id: str | None = None
    selected_design_id: str | None = None
    screened_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    compressed_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    chosen_designs: list[FixedInductorDesignCandidate] = field(default_factory=list)
    best_by_stack_count: dict[int, FixedInductorDesignCandidate] = field(default_factory=dict)
    evaluations: list[InductorOperatingEvaluation] = field(default_factory=list)
    llc_transformer_result: Any | None = None
    transformer_pareto_result: Any | None = None
    transformer_pareto_candidates: list[Any] = field(default_factory=list)
    transformer_chosen_candidates: list[Any] = field(default_factory=list)
    transformer_representatives: dict[str, Any] = field(default_factory=dict)
    transformer_pareto_artifacts: list[str] = field(default_factory=list)
    transformer_pareto_notes: list[str] = field(default_factory=list)
    transformer_recommended_policy: str = ""
    transformer_visualization: TransformerVisualizationArtifact | None = None
    transformer_visualizations: dict[str, TransformerVisualizationArtifact] = field(default_factory=dict)
    transformer_comparison_visualization: TransformerVisualizationArtifact | None = None
    llc_external_resonant_inductor_target: LlcExternalResonantInductorTarget | None = None
    llc_external_resonant_inductor_search_result: LlcExternalResonantInductorSearchResult | None = None
    ac_dc_reactor_result: AcDcReactorSelectionResult | None = None
    core_loss_excitation_audit: dict[str, object] = field(default_factory=dict)
    frontier_search_audit: dict[str, object] = field(default_factory=dict)
    performance_timing: dict[str, object] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
