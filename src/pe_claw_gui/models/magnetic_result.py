"""Magnetic-stage result model."""

from __future__ import annotations

from dataclasses import dataclass, field

from .inductor import FixedInductorDesignCandidate, InductorOperatingEvaluation


@dataclass(frozen=True)
class MagneticResult:
    """Aggregate for magnetic design outputs."""

    summary: str = ""
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
    selected_design_id: str | None = None
    screened_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    compressed_candidates: list[FixedInductorDesignCandidate] = field(default_factory=list)
    chosen_designs: list[FixedInductorDesignCandidate] = field(default_factory=list)
    best_by_stack_count: dict[int, FixedInductorDesignCandidate] = field(default_factory=dict)
    evaluations: list[InductorOperatingEvaluation] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
