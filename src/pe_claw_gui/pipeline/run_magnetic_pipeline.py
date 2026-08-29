"""Magnetic-stage runtime orchestration."""

from __future__ import annotations

import csv
from dataclasses import fields, replace
from pathlib import Path
from time import perf_counter

from ..engines.magnetics.allow_profiles import get_default_allow_profile
from ..engines.magnetics.ac_dc_reactor_selector import select_ac_dc_sendust_reactor
from ..engines.magnetics.candidate_compression import compress_candidates
from ..engines.magnetics.candidate_metrics import MagneticCandidateContext
from ..engines.magnetics.stacked_expansion import (
    STACKED_MARGIN_NEAR_LIMIT_THRESHOLD,
    STACKED_SEED_LIMIT,
    expand_stacked_same_core_candidates,
    select_stacked_seed_candidates,
)
from ..models.design_report import DesignReport
from ..models.ac_dc_reactor import AcDcReactorDesignRequest
from ..models.geometry_result import GeometryResult
from ..models.magnetic_result import (
    LlcMagneticCombinationContract,
    LlcMagneticResultSummary,
    LlcMagneticStageSummary,
    MagneticResult,
)
try:
    from ..topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import (
        LLCFHADesign,
        LLCOperatingPointResult,
        fha_boundary_frequency_cache_info,
    )
    from ..topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (
        build_llc_external_resonant_inductor_target,
        build_llc_transformer_pareto_result,
        build_llc_magnetic_search_bounds,
        build_transformer_design_inputs_from_fha,
        generate_llc_external_resonant_inductor_candidates,
        generate_separated_llc_transformer_candidates,
        llc_reusable_magnetic_metrics_cache_info,
        make_fha_boundary_frequency_solver,
    )
except ModuleNotFoundError:  # New LLC topology package is outside the 1.0 GUI scope.
    LLCFHADesign = None
    LLCOperatingPointResult = None
    build_llc_external_resonant_inductor_target = None
    build_llc_transformer_pareto_result = None
    build_llc_magnetic_search_bounds = None
    build_transformer_design_inputs_from_fha = None
    generate_llc_external_resonant_inductor_candidates = None
    generate_separated_llc_transformer_candidates = None
    llc_reusable_magnetic_metrics_cache_info = None
    make_fha_boundary_frequency_solver = None
    fha_boundary_frequency_cache_info = None

try:
    from ..topologies.dc_dc.flyback_diode_rectified_isolated.coupled_inductor_design import (
        generate_flyback_coupled_inductor_candidates,
    )
except ModuleNotFoundError:  # New Flyback topology package is outside the 1.0 GUI scope.
    generate_flyback_coupled_inductor_candidates = None

try:
    from ..topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated.magnetic_design import (
        generate_psfb_transformer_output_inductor_candidates,
    )
except ModuleNotFoundError:  # New PSFB topology package is outside the 1.0 GUI scope.
    generate_psfb_transformer_output_inductor_candidates = None

try:
    from ..visualization.magnetics import transformer_geometry_renderer
except ModuleNotFoundError:  # Transformer visualizations belong to later topology phases.
    transformer_geometry_renderer = None
from ..engines.magnetics.inductor_adapter import (
    build_design_requirements_dict,
    build_inductor_design_request,
    InductorRequestUnavailableError,
)
from ..engines.magnetics.inductor_design import (
    InductorDatabaseUnavailableError,
    build_pareto_front,
    choose_representative_designs,
    describe_best_by_stack_count,
    describe_design_spread,
    export_design_artifacts,
    select_best_by_stack_count,
    synthesize_fixed_inductor_candidates_with_backend,
)
from ..engines.magnetics.inductor_frontier_search import search_fixed_inductor_candidate_frontier
from ..engines.magnetics.data_backend import (
    MagneticDataBackendConfig,
    get_production_magnetic_backend_config,
    resolve_magnetic_data_backend,
)


LLC_TRANSFORMER_TOPOLOGY_IDS = {
    "llc_resonant_converter_diode_rectifier",
    "llc_resonant_converter_synchronous_rectifier",
}
FLYBACK_MATERIAL_LIMIT = 16


def run_magnetic_pipeline(
    report: DesignReport,
    *,
    backend_config: MagneticDataBackendConfig | None = None,
    llc_search_mode: str = "fast",
    llc_debug_outputs: bool = False,
    llc_geometry_roles: tuple[str, ...] | None = None,
) -> DesignReport:
    """Attach magnetic design plus a shadow-only core-loss excitation audit."""

    from ..engines.magnetics.core_loss_excitation_integration import (
        attach_core_loss_excitation_audit,
    )

    completed = _run_magnetic_pipeline_without_excitation_audit(
        report,
        backend_config=backend_config,
        llc_search_mode=llc_search_mode,
        llc_debug_outputs=llc_debug_outputs,
        llc_geometry_roles=llc_geometry_roles,
    )
    return attach_core_loss_excitation_audit(completed)


def _run_magnetic_pipeline_without_excitation_audit(
    report: DesignReport,
    *,
    backend_config: MagneticDataBackendConfig | None = None,
    llc_search_mode: str = "fast",
    llc_debug_outputs: bool = False,
    llc_geometry_roles: tuple[str, ...] | None = None,
) -> DesignReport:
    """Attach the inductor magnetic stage to a design report."""
    geometry_result = report.geometry or GeometryResult(notes=["Geometry estimation remains a placeholder stage."])

    if report.candidate is None:
        magnetic_result = MagneticResult(
            summary="Inductor design did not run because no synthesized candidate is available.",
            notes=["Topology synthesis must complete before the magnetic stage can run."],
        )
        return replace(report, magnetic=magnetic_result, geometry=geometry_result)

    resolved_backend_config = backend_config or get_production_magnetic_backend_config()

    if report.spec.topology_id in LLC_TRANSFORMER_TOPOLOGY_IDS:
        return _run_llc_transformer_magnetic_pipeline(
            report,
            geometry_result,
            backend_config=resolved_backend_config,
            llc_search_mode=llc_search_mode,
            llc_debug_outputs=llc_debug_outputs,
            llc_geometry_roles=llc_geometry_roles,
        )

    if report.spec.topology_id == "flyback_diode_rectified_isolated":
        return _run_flyback_coupled_inductor_magnetic_pipeline(
            report,
            geometry_result,
            backend_config=resolved_backend_config,
        )

    if report.spec.topology_id == "phase_shifted_full_bridge_diode_rectifier_isolated":
        return _run_psfb_transformer_output_inductor_magnetic_pipeline(report, geometry_result)

    if report.spec.topology_id == "single_phase_diode_bridge_rectifier_dc_inductor_filter":
        return _run_ac_dc_reactor_magnetic_pipeline(report, geometry_result)

    try:
        request = build_inductor_design_request(report)
    except InductorRequestUnavailableError as exc:
        magnetic_result = MagneticResult(
            summary=str(exc),
            notes=[str(exc)],
        )
        return replace(report, magnetic=magnetic_result, geometry=geometry_result)

    notes = list(request.notes)
    design_requirements = build_design_requirements_dict(request)
    allow_profile = get_default_allow_profile(request.fs_hz)
    screening_context = MagneticCandidateContext(
        topology_id=request.topology_id,
        fs_hz=request.fs_hz,
        throughput_power_w=request.throughput_power_w,
        throughput_label=str(request.metadata.get("throughput_label", "converter throughput power proxy")),
    )
    notes.append(f"Resolved frequency band = {allow_profile.band_name}.")
    notes.append(
        f"Magnetic backend: {resolved_backend_config.backend} "
        f"({resolved_backend_config.mode})."
    )
    notes.append("Magnetic data source: normalized_openmagnetics.")
    notes.append(
        f"P_throughput uses {screening_context.throughput_label} = {request.throughput_power_w:.6g} W."
    )

    try:
        basic_feasible_candidates = synthesize_fixed_inductor_candidates_with_backend(
            request,
            resolved_backend_config,
        )
        if not basic_feasible_candidates:
            magnetic_result = MagneticResult(
                summary="No feasible fixed inductor candidates were found for the synthesized design.",
                design_requirements=design_requirements,
                basic_feasible_count=0,
                post_allow_count=0,
                post_compression_count=0,
                feasible_count=0,
                pareto_count=0,
                frequency_band=allow_profile.band_name,
                allow_profile=allow_profile.to_dict(),
                notes=notes + ["The selected magnetic backend returned no basic feasible candidates."],
            )
            return replace(report, magnetic=magnetic_result, geometry=geometry_result)
        frontier_search_audit: dict[str, object] = {}
        compression_result = compress_candidates(
            basic_feasible_candidates,
            context=screening_context,
            allow_profile=allow_profile,
        )
        if compression_result.post_allow_count == 0:
            frontier_result = search_fixed_inductor_candidate_frontier(
                request,
                context=screening_context,
                allow_profile=allow_profile,
                backend_config=resolved_backend_config,
                baseline_candidates=basic_feasible_candidates or None,
                baseline_compression_result=compression_result,
            )
            basic_feasible_candidates = frontier_result.candidates
            compression_result = frontier_result.compression_result
            frontier_search_audit = frontier_result.audit_dict()
            notes.extend(frontier_result.notes)
            notes.append(
                f"Allow-aware fixed-inductor frontier search status={frontier_result.status}, "
                f"selected_stage={frontier_result.selected_stage or 'none'}."
            )
        notes.extend(compression_result.notes)
        if compression_result.post_allow_count == 0:
            magnetic_result = MagneticResult(
                summary="No fixed-inductor candidate satisfies the current library and engineering limits.",
                design_requirements=design_requirements,
                basic_feasible_count=compression_result.basic_feasible_count,
                post_allow_count=0,
                post_compression_count=0,
                feasible_count=0,
                pareto_count=0,
                frequency_band=allow_profile.band_name,
                allow_profile=allow_profile.to_dict(),
                frontier_search_audit=frontier_search_audit,
                notes=notes,
            )
            return replace(report, magnetic=magnetic_result, geometry=geometry_result)

        final_compression_result = compression_result
        stacked_triggered = False
        stacked_trigger_reason = ""
        stacked_seed_count = 0
        stacked_generated_count = 0
        stacked_stack2_generated_count = 0
        stacked_stack3_generated_count = 0
        stacked_precheck_pass_count = 0
        stacked_screened_count = 0
        seed_pool = compression_result.compressed_candidates or compression_result.filtered_candidates
        if seed_pool:
            stacked_triggered = True
            stacked_trigger_reason = (
                "Selective same-core stack_count = 2, 3 competitors are always sampled from the top single-core seed pool "
                "so 1-core, 2-core, and 3-core options can compete in the final merged Pareto search."
            )
            notes.append(f"Stacked-core competitor mode executed: {stacked_trigger_reason}")
            notes.append(
                f"Selective same-core stacked competitors use top-{STACKED_SEED_LIMIT} single-core seeds and a balanced frontier score "
                f"combining normalized volume, normalized loss, and margin proximity (near-limit threshold reference {STACKED_MARGIN_NEAR_LIMIT_THRESHOLD:.2f})."
            )
            notes.append(
                "This first-pass competitor mode keeps the original turns and parallel settings for stack_count = 2 and 3 rather than re-optimizing every geometry variable."
            )
            notes.append(
                "Stacked-core detailed core loss is recomputed from stacked effective Ae, Ve, and B rather than inherited from the single-core seed. Low-beta imported loss fits use a seed-anchored beta floor only for stacked same-core comparisons."
            )
            seed_candidates = select_stacked_seed_candidates(
                seed_pool,
                metrics_by_id=compression_result.metrics_by_id,
                limit=STACKED_SEED_LIMIT,
                near_limit_threshold=STACKED_MARGIN_NEAR_LIMIT_THRESHOLD,
            )
            stacked_seed_count = len(seed_candidates)
            stacked_expansion_result = expand_stacked_same_core_candidates(
                request=request,
                seed_candidates=seed_candidates,
                allow_profile=allow_profile,
                context=screening_context,
            )
            notes.extend(stacked_expansion_result.notes)
            stacked_generated_count = stacked_expansion_result.generated_count
            stacked_stack2_generated_count = stacked_expansion_result.stack2_generated_count
            stacked_stack3_generated_count = stacked_expansion_result.stack3_generated_count
            stacked_precheck_pass_count = stacked_expansion_result.precheck_pass_count
            if stacked_expansion_result.expanded_candidates:
                combined_candidates = [
                    *compression_result.filtered_candidates,
                    *stacked_expansion_result.expanded_candidates,
                ]
                final_compression_result = compress_candidates(
                    combined_candidates,
                    context=screening_context,
                    allow_profile=allow_profile,
                )
                notes.append(
                    f"Merged single-core and stacked competitors were re-screened from {len(combined_candidates)} to "
                    f"{final_compression_result.post_allow_count} and compressed to {final_compression_result.post_compression_count}."
                )
                stacked_screened_count = sum(
                    1
                    for candidate in final_compression_result.filtered_candidates
                    if candidate.assembly_type == "stacked_same_core"
                )
            else:
                notes.append("Selective stacked-core competitor generation produced no variants that survived the cheap precheck.")
        else:
            notes.append("No single-core screened/compressed seed pool was available for stacked competitor generation.")

        pareto_source = final_compression_result.compressed_candidates
        pareto_candidates = build_pareto_front(pareto_source)
        chosen_designs = choose_representative_designs(pareto_candidates, count=5)
        best_by_stack_count = select_best_by_stack_count(final_compression_result.compressed_candidates)
        selected_design_id = chosen_designs[len(chosen_designs) // 2].candidate_id if chosen_designs else None
        artifact_result = export_design_artifacts(
            feasible_candidates=basic_feasible_candidates,
            screened_candidates=final_compression_result.filtered_candidates,
            compressed_candidates=final_compression_result.compressed_candidates,
            pareto_candidates=pareto_candidates,
            chosen_candidates=chosen_designs,
            stack_count_comparison=best_by_stack_count,
            recommended_design_id=selected_design_id,
        )

        notes.append(describe_design_spread(chosen_designs))
        notes.append(_describe_chosen_stack_options(chosen_designs))
        notes.extend(describe_best_by_stack_count(best_by_stack_count))
        if artifact_result.plot_source_name:
            notes.append(f"PF plot is drawn from {artifact_result.plot_source_name}.")
        if artifact_result.plot_color_dimension:
            notes.append(f"PF plot color encoding uses {artifact_result.plot_color_dimension}.")
        if artifact_result.plot_fallback_note:
            notes.append(artifact_result.plot_fallback_note)
        if artifact_result.artifact_paths:
            notes.append(f"Artifacts saved under {Path(artifact_result.artifact_paths[0]).parent}.")

        magnetic_result = MagneticResult(
            summary=(
                f"Inductor search found {compression_result.basic_feasible_count} single-core basic feasible fixed designs, "
                f"screened to {compression_result.post_allow_count} and compressed to {compression_result.post_compression_count}. "
                f"Selective stack_count = 2, 3 competitors added {stacked_generated_count} variants from {stacked_seed_count} seeds. "
                f"Final merged screening/compression kept {final_compression_result.post_allow_count} / {final_compression_result.post_compression_count}, "
                f"with {len(pareto_candidates)} Pareto points and {len(chosen_designs)} representative designs."
            ),
            design_requirements=design_requirements,
            basic_feasible_count=compression_result.basic_feasible_count,
            post_allow_count=compression_result.post_allow_count,
            post_compression_count=compression_result.post_compression_count,
            final_post_allow_count=final_compression_result.post_allow_count,
            final_post_compression_count=final_compression_result.post_compression_count,
            pareto_count=len(pareto_candidates),
            feasible_count=compression_result.basic_feasible_count,
            frequency_band=allow_profile.band_name,
            allow_profile=allow_profile.to_dict(),
            plot_source_name=artifact_result.plot_source_name,
            plot_color_dimension=artifact_result.plot_color_dimension,
            stacked_expansion_triggered=stacked_triggered,
            stacked_seed_count=stacked_seed_count,
            stacked_generated_count=stacked_generated_count,
            stacked_stack2_generated_count=stacked_stack2_generated_count,
            stacked_stack3_generated_count=stacked_stack3_generated_count,
            stacked_precheck_pass_count=stacked_precheck_pass_count,
            stacked_screened_count=stacked_screened_count,
            search_selected_design_id=selected_design_id,
            selected_design_id=selected_design_id,
            screened_candidates=final_compression_result.filtered_candidates,
            compressed_candidates=final_compression_result.compressed_candidates,
            chosen_designs=chosen_designs,
            best_by_stack_count=best_by_stack_count,
            frontier_search_audit=frontier_search_audit,
            artifact_paths=artifact_result.artifact_paths,
            notes=notes,
        )
    except InductorDatabaseUnavailableError as exc:
        magnetic_result = MagneticResult(
            summary="Inductor design search could not start because a requested legacy magnetic database is unavailable.",
            design_requirements=design_requirements,
            frequency_band=allow_profile.band_name,
            allow_profile=allow_profile.to_dict(),
            notes=notes + [str(exc)],
        )
    except Exception as exc:
        magnetic_result = MagneticResult(
            summary="Inductor design search failed unexpectedly.",
            design_requirements=design_requirements,
            frequency_band=allow_profile.band_name,
            allow_profile=allow_profile.to_dict(),
            notes=notes + [f"{type(exc).__name__}: {exc}"],
        )

    return replace(report, magnetic=magnetic_result, geometry=geometry_result)


def _run_flyback_coupled_inductor_magnetic_pipeline(
    report: DesignReport,
    geometry_result: GeometryResult,
    *,
    backend_config: MagneticDataBackendConfig | None = None,
) -> DesignReport:
    """Run first-pass gapped coupled-inductor search for diode Flyback."""

    try:
        if report.candidate is None:
            raise ValueError("Flyback coupled-inductor search requires a synthesized topology candidate.")
        search_result = generate_flyback_coupled_inductor_candidates(
            report.candidate,
            backend_bundle=resolve_magnetic_data_backend(
                backend_config or get_production_magnetic_backend_config()
            ),
            material_limit=FLYBACK_MATERIAL_LIMIT,
        )
        recommended = search_result.recommended_candidate
        selected_design_id = recommended.candidate_id if recommended is not None else None
        if recommended is None:
            summary = (
                "Flyback coupled-inductor first-pass search found no feasible candidates "
                f"from {search_result.evaluated_count} evaluated variants."
            )
        else:
            metadata = recommended.metadata
            summary = (
                "Flyback coupled-inductor first-pass search completed. "
                f"Selected {recommended.candidate_id}: {recommended.core_name}, "
                f"Np:Ns={metadata.get('primary_turns')}:{metadata.get('secondary_turns')}, "
                f"gap={(recommended.gap_m or 0.0) * 1e3:.6g} mm, "
                f"Bpk={(recommended.b_peak_design_t or 0.0):.6g} T, "
                f"loss={(recommended.reference_total_loss_w or 0.0):.6g} W."
            )
        notes = [
            *search_result.notes,
            *search_result.warnings,
            f"Evaluated Flyback coupled-inductor variants: {search_result.evaluated_count}.",
        ]
        if search_result.rejection_counts:
            notes.append(
                "Rejected variants by reason: "
                + ", ".join(
                    f"{reason}={count}"
                    for reason, count in sorted(search_result.rejection_counts.items())
                )
                + "."
            )
        magnetic_result = MagneticResult(
            summary=summary,
            result_type="flyback_coupled_inductor",
            design_type="gapped_flyback_coupled_inductor",
            design_requirements=search_result.design_requirements,
            basic_feasible_count=search_result.evaluated_count,
            feasible_count=len(search_result.feasible_candidates),
            post_allow_count=len(search_result.feasible_candidates),
            post_compression_count=len(search_result.chosen_candidates),
            final_post_allow_count=len(search_result.feasible_candidates),
            final_post_compression_count=len(search_result.chosen_candidates),
            pareto_count=len(search_result.chosen_candidates),
            search_selected_design_id=selected_design_id,
            selected_design_id=selected_design_id,
            screened_candidates=search_result.feasible_candidates,
            compressed_candidates=search_result.feasible_candidates,
            chosen_designs=search_result.chosen_candidates,
            best_by_stack_count={1: recommended} if recommended is not None else {},
            notes=_dedupe_notes(notes),
        )
    except Exception as exc:
        magnetic_result = MagneticResult(
            summary="Flyback coupled-inductor magnetic screening failed unexpectedly.",
            result_type="flyback_coupled_inductor",
            design_type="gapped_flyback_coupled_inductor",
            notes=[
                "Run Design completed, but Run Magnetics could not screen Flyback gapped coupled-inductor candidates.",
                f"{type(exc).__name__}: {exc}",
            ],
        )
    return replace(report, magnetic=magnetic_result, geometry=geometry_result)


def _run_psfb_transformer_output_inductor_magnetic_pipeline(
    report: DesignReport,
    geometry_result: GeometryResult,
) -> DesignReport:
    """Run first-pass transformer and output-inductor search for PSFB."""

    try:
        if report.candidate is None:
            raise ValueError("PSFB magnetic search requires a synthesized topology candidate.")
        search_result = generate_psfb_transformer_output_inductor_candidates(report.candidate)
        recommended = search_result.recommended_candidate
        selected_design_id = recommended.candidate_id if recommended is not None else None
        if recommended is None:
            summary = (
                "PSFB transformer/output-inductor first-pass search found no feasible transformer candidates "
                f"from {search_result.evaluated_count} evaluated variants."
            )
        else:
            metadata = recommended.metadata
            summary = (
                "PSFB transformer/output-inductor first-pass search completed. "
                f"Selected {recommended.candidate_id}: {recommended.core_name}, "
                f"Np:Ns={metadata.get('primary_turns')}:{metadata.get('secondary_turns')}, "
                f"Bpk={(recommended.b_peak_design_t or 0.0):.6g} T, "
                f"fill={(recommended.fill_factor or 0.0):.6g}, "
                f"Lout={metadata.get('output_inductor_inductance_h', 0.0):.6g} H."
            )
        transformer_visualization = None
        transformer_visualizations = {}
        visualization_warnings: list[str] = []
        visualization_artifact_paths: list[str] = []
        if recommended is not None:
            try:
                artifact = transformer_geometry_renderer.render_psfb_transformer_geometry(
                    recommended,
                    role="recommended",
                )
                transformer_visualization = artifact
                transformer_visualizations["recommended"] = artifact
                visualization_artifact_paths.extend([artifact.image_2d_path, artifact.image_3d_path])
            except Exception as exc:
                visualization_warnings.append(
                    f"PSFB transformer geometry generation failed: {type(exc).__name__}: {exc}"
                )
        notes = [
            *search_result.notes,
            *search_result.warnings,
            f"Evaluated PSFB transformer/output-inductor variants: {search_result.evaluated_count}.",
            f"PSFB output-inductor feasible variants: {search_result.output_inductor_feasible_count}.",
            *(transformer_visualization.notes if transformer_visualization is not None else []),
            *(transformer_visualization.warnings if transformer_visualization is not None else []),
            *visualization_warnings,
        ]
        if search_result.rejection_counts:
            notes.append(
                "Rejected PSFB magnetic variants by reason: "
                + ", ".join(
                    f"{reason}={count}"
                    for reason, count in sorted(search_result.rejection_counts.items())
                )
                + "."
            )
        magnetic_result = MagneticResult(
            summary=summary,
            result_type="psfb_transformer_output_inductor",
            design_type="psfb_transformer_and_output_inductor_first_pass",
            design_requirements=search_result.design_requirements,
            basic_feasible_count=search_result.evaluated_count,
            feasible_count=len(search_result.feasible_candidates),
            post_allow_count=len(search_result.feasible_candidates),
            post_compression_count=len(search_result.chosen_candidates),
            final_post_allow_count=len(search_result.feasible_candidates),
            final_post_compression_count=len(search_result.chosen_candidates),
            pareto_count=len(search_result.chosen_candidates),
            search_selected_design_id=selected_design_id,
            selected_design_id=selected_design_id,
            screened_candidates=search_result.feasible_candidates,
            compressed_candidates=search_result.feasible_candidates,
            chosen_designs=search_result.chosen_candidates,
            best_by_stack_count={1: recommended} if recommended is not None else {},
            transformer_visualization=transformer_visualization,
            transformer_visualizations=transformer_visualizations,
            artifact_paths=_dedupe_notes(visualization_artifact_paths),
            notes=_dedupe_notes(notes),
        )
    except Exception as exc:
        magnetic_result = MagneticResult(
            summary="PSFB transformer/output-inductor magnetic screening failed unexpectedly.",
            result_type="psfb_transformer_output_inductor",
            design_type="psfb_transformer_and_output_inductor_first_pass",
            notes=[
                "Run Design completed, but Run Magnetics could not screen PSFB transformer/output-inductor candidates.",
                f"{type(exc).__name__}: {exc}",
            ],
        )
    return replace(report, magnetic=magnetic_result, geometry=geometry_result)


def _run_ac_dc_reactor_magnetic_pipeline(
    report: DesignReport,
    geometry_result: GeometryResult,
) -> DesignReport:
    """Run first-pass Sendust toroid selection for the AC-DC DC-link reactor."""

    try:
        request = _build_ac_dc_reactor_request(report)
        selection = select_ac_dc_sendust_reactor(request, output_dir=_project_root() / "outputs" / "ac_dc_reactor_design")
        selected = selection.selected_candidate
        requirements = _ac_dc_reactor_design_requirements(request)
        notes = [*request.notes, *selection.notes, *selection.warnings]
        if selected is None:
            summary = (
                "AC-DC Sendust DC-link reactor selection found no feasible toroid candidates "
                f"from {selection.evaluated_count} evaluated variants."
            )
            selected_design_id = None
        else:
            summary = (
                "AC-DC Sendust DC-link reactor selection completed. "
                f"Selected {selected.candidate_id}: {selected.turns} turns on {selected.core_part_number}, "
                f"L_eff={selected.effective_inductance_h * 1e3:.6g} mH, "
                f"loss={selected.total_loss_w:.6g} W."
            )
            selected_design_id = selected.candidate_id
        magnetic_result = MagneticResult(
            summary=summary,
            result_type="ac_dc_sendust_reactor",
            design_type="ac_dc_dc_link_reactor",
            design_requirements=requirements,
            basic_feasible_count=selection.evaluated_count,
            feasible_count=selection.feasible_count,
            post_allow_count=selection.feasible_count,
            post_compression_count=len(selection.top_candidates),
            search_selected_design_id=selected_design_id,
            selected_design_id=selected_design_id,
            ac_dc_reactor_result=selection,
            artifact_paths=selection.artifact_paths,
            notes=notes,
        )
    except Exception as exc:
        magnetic_result = MagneticResult(
            summary="AC-DC Sendust DC-link reactor selection failed unexpectedly.",
            result_type="ac_dc_sendust_reactor",
            design_type="ac_dc_dc_link_reactor",
            notes=[f"{type(exc).__name__}: {exc}"],
        )
    completed = replace(report, magnetic=magnetic_result, geometry=geometry_result)
    if magnetic_result.ac_dc_reactor_result is None:
        return completed
    selected = magnetic_result.ac_dc_reactor_result.selected_candidate
    if selected is None:
        return completed
    return _refresh_ac_dc_reactor_hardware(completed, selected)


def _refresh_ac_dc_reactor_hardware(report: DesignReport, selected: object) -> DesignReport:
    """Refresh the rectifier electrical point using selected reactor L and Rdc."""

    from ..models.operating_point import OperatingPoint
    from ..topologies.ac_dc.single_phase_diode_bridge_rectifier_dc_inductor_filter.evaluator import evaluate
    from ..topologies.ac_dc.single_phase_diode_bridge_rectifier_dc_inductor_filter.stress import extract_stress
    from ..topologies.ac_dc.single_phase_diode_bridge_rectifier_dc_inductor_filter.waveform import (
        generate_waveforms,
        refresh_selected_hardware_candidate,
    )

    candidate = report.candidate
    if candidate is None:
        return report
    candidate, result = refresh_selected_hardware_candidate(
        candidate,
        selected_ldc_h=float(getattr(selected, "effective_inductance_h", 0.0)),
        selected_reactor_rdc_ohm=float(getattr(selected, "rdc_25c_ohm", 0.0) or 0.0),
    )
    if not result.succeeded:
        return report
    operating_point = report.operating_point or OperatingPoint(vin_v=candidate.vin_nom, load_ratio=1.0)
    operating_point = replace(
        operating_point,
        vout_v=float(result.metrics["vdc_avg_v"]),
        power_factor=float(result.metrics["power_factor"]),
    )
    waveform = generate_waveforms(candidate, operating_point=operating_point)
    stress = extract_stress(candidate, waveform_set=waveform)
    topology_result = evaluate(candidate, waveform_set=waveform, stress_result=stress)
    return replace(
        report,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform,
        stress=stress,
        topology_result=topology_result,
        notes=[*report.notes, "Electrical operating point refreshed using selected reactor L_eff and Rdc."],
    )


def _build_ac_dc_reactor_request(report: DesignReport) -> AcDcReactorDesignRequest:
    candidate = report.candidate
    if candidate is None:
        raise ValueError("AC-DC reactor selection requires a synthesized topology candidate.")
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    simulation_current_basis = bool(metadata.get("simulation_primary_metrics_used"))
    current_basis = (
        "design-point state-space simulation pulsed-current metrics"
        if simulation_current_basis
        else "small-reactor first-pass fallback estimates"
    )
    return AcDcReactorDesignRequest(
        topology_id=candidate.topology_id,
        display_name=report.spec.display_name or candidate.display_name,
        required_inductance_h=float(metadata.get("ldc_required_h", candidate.inductance_h)),
        f_line_hz=float(metadata.get("f_line_hz", 0.5 * candidate.fs_hz)),
        ripple_frequency_hz=float(metadata.get("ripple_frequency_hz", candidate.fs_hz)),
        idc_a=float(metadata.get("simulation_primary_il_avg_a", metadata.get("idc_a", candidate.iout))),
        i_rms_a=float(metadata.get("simulation_primary_il_rms_a", metadata.get("il_rms_est_a", candidate.iout))),
        i_peak_a=float(metadata.get("simulation_primary_il_peak_a", metadata.get("il_peak_est_a", candidate.il_peak))),
        i_valley_a=float(metadata.get("simulation_primary_il_min_a", metadata.get("il_min_est_a", candidate.il_valley))),
        delta_i_pp_a=float(
            metadata.get("simulation_primary_delta_il_pp_a", metadata.get("target_delta_il_pp_a", candidate.delta_il))
        ),
        vdc_est_v=float(metadata.get("simulation_primary_vdc_avg_v", metadata.get("vdc_est_v", candidate.vout_target))),
        throughput_power_w=float(candidate.pout_target),
        current_basis=current_basis,
        notes=[
            "Request generated from AC-DC single-phase diode bridge DC-side inductor-filter report.",
            "Ripple frequency is 2*f_line for full-wave rectified single-phase current ripple.",
            "The topology uses a bounded small DC reactor; pulsed/discontinuous current is allowed.",
            f"Reactor current basis: {current_basis}.",
            "The selector uses Sendust toroid powder cores rather than the high-frequency ferrite/OpenMagnetics inductor backend.",
        ],
        metadata={
            "source_topology_metadata_keys": ", ".join(sorted(str(key) for key in metadata.keys())),
            "ldc_requirement_basis": metadata.get("ldc_requirement_basis"),
            "waveform_basis": metadata.get("waveform_basis"),
            "current_basis": current_basis,
            "simulation_primary_metrics_used": simulation_current_basis,
            "bridge_current_rms_a": metadata.get("simulation_primary_bridge_current_rms_a"),
            "capacitor_current_rms_a": metadata.get("simulation_primary_capacitor_current_rms_a"),
            "conduction_angle_half_cycle_deg": metadata.get("simulation_primary_conduction_angle_half_cycle_deg"),
            "bridge_pulse_count_per_line_cycle": metadata.get("simulation_primary_bridge_pulse_count_per_line_cycle"),
        },
    )


def _ac_dc_reactor_design_requirements(request: AcDcReactorDesignRequest) -> dict[str, float | str | bool | None]:
    return {
        "topology_id": request.topology_id,
        "display_name": request.display_name,
        "inductance_h": request.required_inductance_h,
        "target_inductance_h": request.required_inductance_h,
        "fs_hz": request.ripple_frequency_hz,
        "f_line_hz": request.f_line_hz,
        "ripple_frequency_hz": request.ripple_frequency_hz,
        "i_avg_a": request.idc_a,
        "idc_a": request.idc_a,
        "i_rms_a": request.i_rms_a,
        "i_peak_a": request.i_peak_a,
        "i_valley_a": request.i_valley_a,
        "delta_i_pp_a": request.delta_i_pp_a,
        "throughput_power_w": request.throughput_power_w,
        "vdc_est_v": request.vdc_est_v,
        "mode": "single_phase_small_dc_reactor_pulsed_current",
        "current_basis": request.current_basis,
        "bridge_current_rms_a": request.metadata.get("bridge_current_rms_a"),
        "capacitor_current_rms_a": request.metadata.get("capacitor_current_rms_a"),
        "conduction_angle_half_cycle_deg": request.metadata.get("conduction_angle_half_cycle_deg"),
        "bridge_pulse_count_per_line_cycle": request.metadata.get("bridge_pulse_count_per_line_cycle"),
        "material_family": request.material_family,
        "core_shape": request.core_shape,
    }


def _run_llc_transformer_magnetic_pipeline(
    report: DesignReport,
    geometry_result: GeometryResult,
    *,
    backend_config: MagneticDataBackendConfig | None = None,
    llc_search_mode: str = "fast",
    llc_debug_outputs: bool = False,
    llc_geometry_roles: tuple[str, ...] | None = None,
) -> DesignReport:
    """Run separated LLC transformer first-pass magnetic screening from Run Magnetics."""

    pipeline_started = perf_counter()
    pipeline_timing: dict[str, object] = {}
    output_policy = _llc_output_policy(
        debug_outputs=llc_debug_outputs,
        geometry_roles=llc_geometry_roles,
    )
    llc_fha_metadata = (
        report.candidate.metadata.get("llc_fha", {})
        if report.candidate is not None and isinstance(report.candidate.metadata, dict)
        else {}
    )
    transformer_target = (
        llc_fha_metadata.get("transformer_design_target", {})
        if isinstance(llc_fha_metadata, dict)
        else {}
    )
    if not isinstance(transformer_target, dict) or not transformer_target:
        magnetic_result = _llc_transformer_failure_result(
            failure_code="missing_transformer_target",
            failure_reason="LLC transformer target metadata is missing from the FHA design result.",
            notes=[
                "Run Design must complete the diode LLC FHA design before Run Magnetics can screen separated transformer candidates.",
            ],
        )
        return _mark_llc_magnetics_blocked(
            replace(report, magnetic=magnetic_result, geometry=geometry_result),
            magnetic_result.llc_result_summary.transformer.failure_reason,
        )

    try:
        preparation_started = perf_counter()
        backend_bundle = resolve_magnetic_data_backend(
            backend_config or get_production_magnetic_backend_config()
        )
        fha_design = _rebuild_llc_fha_design(llc_fha_metadata)
        transformer_inputs = build_transformer_design_inputs_from_fha(fha_design)
        search_bounds = build_llc_magnetic_search_bounds(transformer_inputs, mode=llc_search_mode)
        pipeline_timing["parameter_preparation_seconds"] = perf_counter() - preparation_started
        transformer_search_started = perf_counter()
        search_result = generate_separated_llc_transformer_candidates(
            transformer_inputs,
            core_records=(backend_bundle.cores if backend_bundle is not None else None),
            material_records=(backend_bundle.materials if backend_bundle is not None else None),
            wire_records=(backend_bundle.wires if backend_bundle is not None else None),
            max_scale_factor=search_bounds.max_scale_factor,
            frequency_solver=make_fha_boundary_frequency_solver(fha_design),
            search_bounds=search_bounds,
            write_debug_csv=True,
            output_dir=_llc_transformer_output_dir(report),
        )
        pipeline_timing["transformer_search_seconds"] = perf_counter() - transformer_search_started
        transformer_output_dir = _llc_transformer_output_dir(report)
        transformer_artifact_paths = list(search_result.artifact_paths)
        if not search_result.feasible_candidates:
            return _finish_llc_transformer_failure(
                report,
                geometry_result,
                search_result=search_result,
                output_policy=output_policy,
                pipeline_timing=pipeline_timing,
                failure_code="no_feasible_candidate",
                failure_reason=(
                    "Transformer candidate search completed, but no candidate passed the LLC magnetic constraints."
                ),
            )
        transformer_pareto_started = perf_counter()
        pareto_result = build_llc_transformer_pareto_result(
            search_result.feasible_candidates,
            write_artifacts=True,
            output_dir=transformer_output_dir,
        )
        pipeline_timing["transformer_pareto_seconds"] = perf_counter() - transformer_pareto_started
        recommended = pareto_result.recommended_candidate or search_result.recommended_preliminary_candidate
        selected_design_id = recommended.candidate_id if recommended is not None else None
        artifact_validation = _validate_llc_transformer_artifacts(
            [*transformer_artifact_paths, *pareto_result.artifact_paths],
            pareto_result,
        )
        if not artifact_validation["valid"]:
            return _finish_llc_transformer_failure(
                report,
                geometry_result,
                search_result=search_result,
                pareto_result=pareto_result,
                output_policy=output_policy,
                pipeline_timing=pipeline_timing,
                failure_code="artifact_incomplete",
                failure_reason=str(artifact_validation["reason"]),
                artifact_paths=[*transformer_artifact_paths, *pareto_result.artifact_paths],
            )
        # The ID becomes run-scoped state only after all required CSVs pass validation.
        if report.llc_run_context is not None:
            report = replace(
                report,
                llc_run_context=report.llc_run_context.with_result_ids(
                    transformer_design_id=selected_design_id,
                ),
            )
        external_lr_target = (
            build_llc_external_resonant_inductor_target(fha_design, recommended)
            if recommended is not None
            else None
        )
        external_lr_search_started = perf_counter()
        external_lr_search_result = (
            generate_llc_external_resonant_inductor_candidates(
                external_lr_target,
                core_records=(backend_bundle.cores if backend_bundle is not None else None),
                material_records=(backend_bundle.materials if backend_bundle is not None else None),
                wire_records=(backend_bundle.wires if backend_bundle is not None else None),
                search_bounds=search_bounds,
                write_csv=True,
                output_dir=_llc_external_lr_output_dir(report),
            )
            if external_lr_target is not None
            else None
        )
        pipeline_timing["external_lr_search_seconds"] = perf_counter() - external_lr_search_started
        recommended_external_lr = (
            external_lr_search_result.recommended_candidate
            if external_lr_search_result is not None
            else None
        )
        transformer_stage_summary = _llc_stage_summary(
            search_result,
            pareto_count=pareto_result.pareto_count,
            recommended_design_id=selected_design_id,
            status=_llc_transformer_status(search_result, selected_design_id),
        )
        transformer_stage_summary = replace(
            transformer_stage_summary,
            artifact_paths=[*transformer_artifact_paths, *pareto_result.artifact_paths],
        )
        external_lr_stage_summary = _llc_external_lr_stage_summary(
            external_lr_target,
            external_lr_search_result,
        )
        if external_lr_target is not None and external_lr_target.is_design_required:
            if external_lr_stage_summary.status != "available" or recommended_external_lr is None:
                return _finish_llc_external_lr_failure(
                    report,
                    geometry_result,
                    search_result=search_result,
                    pareto_result=pareto_result,
                    external_lr_search_result=external_lr_search_result,
                    transformer_artifact_paths=[*transformer_artifact_paths, *pareto_result.artifact_paths],
                    output_policy=output_policy,
                    pipeline_timing=pipeline_timing,
                    failure_code="no_feasible_candidate",
                    failure_reason=(
                        "External resonant-inductor search completed, but no candidate passed the LLC Lr constraints."
                    ),
                )
            external_artifact_validation = _validate_llc_external_lr_artifacts(
                external_lr_search_result,
            )
            if not external_artifact_validation["valid"]:
                return _finish_llc_external_lr_failure(
                    report,
                    geometry_result,
                    search_result=search_result,
                    pareto_result=pareto_result,
                    external_lr_search_result=external_lr_search_result,
                    transformer_artifact_paths=[*transformer_artifact_paths, *pareto_result.artifact_paths],
                    output_policy=output_policy,
                    pipeline_timing=pipeline_timing,
                    failure_code="artifact_incomplete",
                    failure_reason=str(external_artifact_validation["reason"]),
                )
        external_artifact_paths = list(external_lr_search_result.artifact_paths) if external_lr_search_result is not None else []
        external_lr_stage_summary = replace(
            external_lr_stage_summary,
            artifact_paths=external_artifact_paths,
        )
        recommended_external_lr_design_id = (
            recommended_external_lr.design_id
            if recommended_external_lr is not None
            and external_lr_stage_summary.status == "available"
            else None
        )
        recommended_combined_magnetic_design_id = build_llc_combined_magnetic_design_id(
            selected_design_id,
            recommended_external_lr_design_id,
            external_lr_stage_summary.status,
        )
        magnetic_contract = build_llc_magnetic_combination_contract(
            report=report,
            fha_design=fha_design,
            transformer_target=transformer_target,
            transformer=recommended,
            external_lr=recommended_external_lr,
            external_lr_target=external_lr_target,
            transformer_artifact_paths=[*transformer_artifact_paths, *pareto_result.artifact_paths],
            external_lr_artifact_paths=external_artifact_paths,
            external_lr_status=external_lr_stage_summary.status,
        )
        contract_validation = validate_llc_magnetic_combination_contract(
            report=report,
            contract=magnetic_contract,
            transformer_candidates=search_result.feasible_candidates,
            external_lr_candidates=(
                external_lr_search_result.feasible_candidates
                if external_lr_search_result is not None
                else []
            ),
        )
        if not contract_validation["valid"]:
            return _finish_llc_magnetic_contract_failure(
                report,
                geometry_result,
                search_result=search_result,
                pareto_result=pareto_result,
                external_lr_search_result=external_lr_search_result,
                transformer_artifact_paths=[*transformer_artifact_paths, *pareto_result.artifact_paths],
                output_policy=output_policy,
                pipeline_timing=pipeline_timing,
                failure_reason=str(contract_validation["reason"]),
            )
        llc_result_summary = LlcMagneticResultSummary(
            transformer=transformer_stage_summary,
            external_lr=replace(
                external_lr_stage_summary,
                recommended_design_id=recommended_external_lr_design_id,
            ),
            recommended_transformer_design_id=selected_design_id,
            recommended_external_lr_design_id=recommended_external_lr_design_id,
            recommended_combined_magnetic_design_id=recommended_combined_magnetic_design_id,
        )
        if report.llc_run_context is not None and recommended_external_lr_design_id:
            report = replace(
                report,
                llc_run_context=report.llc_run_context.with_result_ids(
                    external_lr_design_id=recommended_external_lr_design_id,
                    combined_magnetic_design_id=magnetic_contract.combined_magnetic_design_id,
                ),
            )
        design_requirements = _llc_transformer_design_requirements(
            transformer_target,
            search_result,
            fha_design=fha_design,
            display_name=report.candidate.display_name,
            recommended_candidate=recommended,
            external_lr_target=external_lr_target,
            search_bounds=search_bounds,
        )
        design_requirements["external_lr_status"] = external_lr_stage_summary.status
        field_status = design_requirements.get("field_status")
        if isinstance(field_status, dict):
            field_status["external_lr"] = external_lr_stage_summary.status
        design_requirements["magnetic_search_bounds"] = search_bounds.to_dict()
        design_requirements["magnetic_output_policy"] = output_policy
        design_requirements["transformer_pareto_count"] = pareto_result.pareto_count
        design_requirements["transformer_chosen_count"] = pareto_result.chosen_count
        design_requirements["llc_magnetic_contract"] = magnetic_contract.to_dict()
        if external_lr_target is not None:
            design_requirements["external_lr_target_h"] = external_lr_target.external_lr_target_h
            design_requirements["external_lr_fraction"] = external_lr_target.lr_external_fraction
            design_requirements["external_lr_current_rms_a"] = external_lr_target.current_rms_a
            design_requirements["external_lr_current_peak_a"] = external_lr_target.current_peak_a
            design_requirements["external_lr_fs_basis_hz"] = external_lr_target.fs_basis_hz
        if external_lr_search_result is not None:
            design_requirements["external_lr_candidate_count"] = len(external_lr_search_result.candidates)
            design_requirements["external_lr_feasible_count"] = len(external_lr_search_result.feasible_candidates)
        summary = (
            "Separated LLC transformer first-pass magnetic screening evaluated "
            f"{search_result.evaluated_candidate_count} candidates and found "
            f"{search_result.feasible_candidate_count} feasible candidates. "
            f"Transformer Pareto front contains {pareto_result.pareto_count} candidates."
        )
        if recommended is not None:
            summary += (
                f" Preliminary transformer recommendation: {recommended.core_id}/{recommended.material_id}, "
                f"Np:Ns={recommended.np}:{recommended.ns}, gap={recommended.gap_m * 1e3:.6g} mm, "
                f"loss={recommended.total_loss_w:.6g} W."
            )
        else:
            summary += " No feasible preliminary transformer recommendation is available."
        transformer_visualization = None
        transformer_visualizations = {}
        transformer_comparison_visualization = None
        transformer_comparison_candidates = {}
        visualization_warnings: list[str] = []
        visualization_artifact_paths: list[str] = []
        geometry_started = perf_counter()
        for role in output_policy["geometry_roles"]:
            selection = pareto_result.representative_by_role.get(role)
            candidate_for_role = selection.candidate if selection is not None else (recommended if role == "recommended" else None)
            if candidate_for_role is None:
                continue
            transformer_comparison_candidates[role] = candidate_for_role
            if transformer_geometry_renderer is None:
                visualization_warnings.append(
                    "LLC transformer geometry renderer is unavailable; structured magnetic results remain available."
                )
                continue
            try:
                artifact = transformer_geometry_renderer.render_llc_transformer_geometry(
                    candidate_for_role,
                    role=role,
                    create_legacy_aliases=(role == "recommended"),
                    use_role_file_names=True,
                )
                transformer_visualizations[role] = artifact
                visualization_artifact_paths.extend([artifact.image_2d_path, artifact.image_3d_path])
                if role == "recommended":
                    transformer_visualization = artifact
                    visualization_artifact_paths.extend(
                        [
                            str(Path(artifact.image_2d_path).with_name("llc_transformer_geometry_2d.png")),
                            str(Path(artifact.image_3d_path).with_name("llc_transformer_geometry_3d.png")),
                        ]
                    )
            except Exception as exc:
                visualization_warnings.append(
                    f"Transformer geometry generation failed for {role}: {type(exc).__name__}: {exc}"
                )
        if llc_debug_outputs and transformer_geometry_renderer is not None and transformer_comparison_candidates:
            try:
                transformer_comparison_visualization = transformer_geometry_renderer.render_llc_transformer_comparison_geometry(
                    transformer_comparison_candidates,
                )
                visualization_artifact_paths.extend(
                    [
                        transformer_comparison_visualization.image_2d_path,
                        transformer_comparison_visualization.image_3d_path,
                    ]
                )
            except Exception as exc:
                visualization_warnings.append(
                    f"Transformer comparison geometry generation failed: {type(exc).__name__}: {exc}"
                )
        pipeline_timing["geometry_seconds"] = perf_counter() - geometry_started
        pipeline_timing["output_policy"] = output_policy
        pipeline_timing["total_seconds"] = perf_counter() - pipeline_started

        notes = [
            "LLC transformer design type: separated LLC transformer.",
            "Transformer realizes the FHA integer turns ratio and Lm; external resonant inductor realizes Lr.",
            "Leakage inductance is first-pass estimated and checked only; it is not designed as Lr.",
            "Run Magnetics executed the LLC transformer candidate search; Run Design remains electrical/FHA only.",
            "External resonant inductor first-pass candidate search is executed after transformer recommendation when Lr_ext_target is positive.",
            "Flux model uses Bpeak = Vpri / (4 * Np * Ae * fs) and delta_B = Vpri / (2 * Np * Ae * fs) under symmetric bipolar excitation.",
            "Transformer Pareto front uses first-pass estimated transformer volume and total transformer loss.",
            "Detailed winding-stack geometry, detailed leakage model, isolation/creepage/clearance checks, and final optimization are not implemented.",
            "Screening uses first-pass winding, leakage, core-loss, and thermal approximations.",
            *search_result.notes,
            *search_result.warnings,
            *pareto_result.notes,
            *(external_lr_search_result.notes if external_lr_search_result is not None else []),
            *(external_lr_search_result.warnings if external_lr_search_result is not None else []),
            *(transformer_visualization.notes if transformer_visualization is not None else []),
            *(transformer_visualization.warnings if transformer_visualization is not None else []),
            *(transformer_comparison_visualization.notes if transformer_comparison_visualization is not None else []),
            *(transformer_comparison_visualization.warnings if transformer_comparison_visualization is not None else []),
            *visualization_warnings,
        ]
        artifact_paths = _dedupe_notes([
            *search_result.artifact_paths,
            *pareto_result.artifact_paths,
            *(external_lr_search_result.artifact_paths if external_lr_search_result is not None else []),
            *visualization_artifact_paths,
        ])
        magnetic_result = MagneticResult(
            summary=summary,
            result_type="separated_llc_transformer",
            design_type="separated_llc_transformer",
            design_requirements=design_requirements,
            basic_feasible_count=search_result.evaluated_candidate_count,
            feasible_count=search_result.feasible_candidate_count,
            pareto_count=pareto_result.pareto_count,
            selected_design_id=selected_design_id,
            llc_result_summary=llc_result_summary,
            llc_magnetic_contract=magnetic_contract,
            recommended_transformer_design_id=selected_design_id,
            recommended_external_lr_design_id=recommended_external_lr_design_id,
            recommended_combined_magnetic_design_id=recommended_combined_magnetic_design_id,
            llc_transformer_result=search_result,
            transformer_pareto_result=pareto_result,
            transformer_pareto_candidates=pareto_result.pareto_candidates,
            transformer_chosen_candidates=pareto_result.chosen_candidates,
            transformer_representatives=pareto_result.representative_by_role,
            transformer_pareto_artifacts=pareto_result.artifact_paths,
            transformer_pareto_notes=pareto_result.notes,
            transformer_recommended_policy=pareto_result.recommended_policy,
            transformer_visualization=transformer_visualization,
            transformer_visualizations=transformer_visualizations,
            transformer_comparison_visualization=transformer_comparison_visualization,
            llc_external_resonant_inductor_target=external_lr_target,
            llc_external_resonant_inductor_search_result=external_lr_search_result,
            performance_timing={
                "pipeline": pipeline_timing,
                "transformer_search": search_result.performance_timing,
                "transformer_counts": search_result.performance_counts,
                "transformer_pareto_timing": pareto_result.performance_timing,
                "transformer_pareto_counts": pareto_result.performance_counts,
                "search_bounds": search_bounds.to_dict(),
                "external_lr_search": (
                    external_lr_search_result.performance_timing
                    if external_lr_search_result is not None
                    else {}
                ),
                "external_lr_counts": (
                    {
                        **external_lr_search_result.performance_counts,
                        "prefilter_rejection_counts": external_lr_search_result.prefilter_rejection_counts,
                    }
                    if external_lr_search_result is not None
                    else {}
                ),
                "fha_boundary_cache": (
                    fha_boundary_frequency_cache_info()
                    if fha_boundary_frequency_cache_info is not None
                    else {}
                ),
                "reusable_magnetic_metrics_cache": (
                    llc_reusable_magnetic_metrics_cache_info()
                    if llc_reusable_magnetic_metrics_cache_info is not None
                    else {}
                ),
            },
            artifact_paths=artifact_paths,
            notes=_dedupe_notes(notes),
        )
    except Exception as exc:
        failure_code = "invalid_transformer_parameters" if isinstance(exc, ValueError) else "transformer_search_failed"
        if isinstance(exc, OSError):
            failure_code = "artifact_write_failed"
        magnetic_result = _llc_transformer_failure_result(
            failure_code=failure_code,
            failure_reason=f"{type(exc).__name__}: {exc}",
            notes=[
                "Run Design completed, but Run Magnetics could not screen separated LLC transformer candidates.",
            ],
        )
    return _mark_llc_magnetics_blocked(
        replace(report, magnetic=magnetic_result, geometry=geometry_result),
        magnetic_result.llc_result_summary.transformer.failure_reason
        if magnetic_result.llc_result_summary is not None
        else str(exc),
    )


def _rebuild_llc_fha_design(llc_fha_metadata: dict[str, object]) -> LLCFHADesign:
    """Rebuild the LLC FHA dataclass from report metadata for Run Magnetics helpers."""

    design_field_names = {field.name for field in fields(LLCFHADesign)}
    values = {
        key: value
        for key, value in llc_fha_metadata.items()
        if key in design_field_names and key != "coverage_results"
    }
    coverage_results = []
    for row in llc_fha_metadata.get("coverage_results", []):
        if isinstance(row, LLCOperatingPointResult):
            coverage_results.append(row)
        elif isinstance(row, dict):
            coverage_results.append(LLCOperatingPointResult(**row))
    values["coverage_results"] = coverage_results
    return LLCFHADesign(**values)


def _llc_transformer_design_requirements(
    transformer_target: dict[str, object],
    search_result,
    *,
    fha_design=None,
    display_name: str | None = None,
    recommended_candidate=None,
    external_lr_target=None,
    search_bounds=None,
) -> dict[str, object]:
    fha = fha_design
    topology_id = str(
        getattr(fha, "topology_id", None)
        or transformer_target.get("topology_id")
        or "llc_resonant_converter_diode_rectifier"
    )
    requirements: dict[str, object] = {
        "topology_id": topology_id,
        "display_name": display_name or topology_id,
        "design_type": "separated_llc_transformer",
        "transformer_realizes": "Np:Ns and Lm",
        "external_resonant_inductor_realizes": "Lr",
        "vin_min_v": getattr(fha, "vin_min_v", None),
        "vin_nom_v": getattr(fha, "vin_nom_v", None),
        "vin_max_v": getattr(fha, "vin_max_v", None),
        "vout_min_v": getattr(fha, "vout_min_v", None),
        "vout_nom_v": getattr(fha, "vout_nom_v", None),
        "vout_max_v": getattr(fha, "vout_max_v", None),
        "pout_min_w": getattr(fha, "pout_min_w", None),
        "pout_max_w": getattr(fha, "pout_max_w", None),
        "fs_min_hz": getattr(fha, "fs_min_hz", None),
        "fs_nom_hz": getattr(fha, "fr_hz", None),
        "fs_max_hz": getattr(fha, "fs_max_hz", None),
        "fr_hz": getattr(fha, "fr_hz", None),
        "base_np": transformer_target.get("base_np"),
        "base_ns": transformer_target.get("base_ns"),
        "recommended_np": getattr(recommended_candidate, "np", None),
        "recommended_ns": getattr(recommended_candidate, "ns", None),
        "np": transformer_target.get("base_np"),
        "ns": transformer_target.get("base_ns"),
        "lm_target_h": transformer_target.get("lm_target_h"),
        "lr_target_h": transformer_target.get("lr_target_h"),
        "b_limit_t": transformer_target.get("b_limit_t"),
        "primary_bridge_type": transformer_target.get("primary_bridge_type"),
        "secondary_rectifier_type": transformer_target.get("secondary_rectifier_type"),
        "boundary_saturation_cases": list(transformer_target.get("boundary_saturation_case_names", [])),
        "primary_current_basis": transformer_target.get("primary_current_basis"),
        "primary_current_rms_a": transformer_target.get("primary_current_rms_a"),
        "primary_current_peak_a": transformer_target.get("primary_current_peak_a"),
        "secondary_current_basis": transformer_target.get("secondary_current_basis"),
        "secondary_current_rms_a": transformer_target.get("secondary_current_rms_a"),
        "secondary_current_peak_a": transformer_target.get("secondary_current_peak_a"),
        "transformer_estimated_lk_h": getattr(recommended_candidate, "estimated_lk_h", None),
        "transformer_leakage_method": getattr(recommended_candidate, "leakage_method", None),
        "transformer_leakage_status": getattr(recommended_candidate, "leakage_status", None),
        "evaluated_candidate_count": search_result.evaluated_candidate_count,
        "feasible_candidate_count": search_result.feasible_candidate_count,
    }
    if external_lr_target is None:
        requirements.update(
            {
                "external_lr_status": "not_evaluated",
                "external_lr_target_h": None,
                "external_lr_target_uH": None,
                "external_lr_is_design_required": False,
                "external_lr_current_rms_a": None,
                "external_lr_current_peak_a": None,
                "external_lr_fs_basis_hz": None,
                "external_lr_fs_min_hz": None,
                "external_lr_fs_max_hz": None,
            }
        )
    else:
        requirements.update(
            {
                "external_lr_status": "available" if external_lr_target.is_design_required else "not_required",
                "external_lr_target_h": external_lr_target.external_lr_target_h,
                "external_lr_target_uH": external_lr_target.external_lr_target_uH,
                "external_lr_total_target_h": external_lr_target.lr_total_target_h,
                "external_lr_transformer_lk_h": external_lr_target.transformer_lk_h,
                "external_lr_is_design_required": external_lr_target.is_design_required,
                "external_lr_current_basis": external_lr_target.current_basis,
                "external_lr_frequency_basis": external_lr_target.frequency_basis,
                "external_lr_current_rms_a": external_lr_target.current_rms_a,
                "external_lr_current_peak_a": external_lr_target.current_peak_a,
                "external_lr_fs_basis_hz": external_lr_target.fs_basis_hz,
                "external_lr_fs_min_hz": external_lr_target.fs_min_hz,
                "external_lr_fs_max_hz": external_lr_target.fs_max_hz,
                "external_lr_warning": external_lr_target.warning,
            }
        )
    if search_bounds is not None:
        requirements["magnetic_search_mode"] = search_bounds.mode
        requirements["magnetic_search_selection_policy"] = search_bounds.selection_policy
        requirements["magnetic_search_bounds"] = search_bounds.to_dict()
    else:
        requirements["magnetic_search_mode"] = "not_available"
    requirements["field_status"] = {
        "vin_range": "available" if fha is not None else "not_available",
        "vout_range": "available" if fha is not None else "not_available",
        "power_range": "available" if fha is not None else "not_available",
        "frequency_range": "available" if fha is not None else "not_available",
        "transformer_leakage": "available" if recommended_candidate is not None else "not_evaluated",
        "external_lr": requirements["external_lr_status"],
    }
    return requirements


def _dedupe_notes(notes: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for note in notes:
        text = str(note)
        if not text or text in seen:
            continue
        deduped.append(text)
        seen.add(text)
    return deduped


def _describe_chosen_stack_options(chosen_designs) -> str:
    stack_counts = sorted({design.stack_count for design in chosen_designs})
    if not stack_counts:
        return "No chosen designs were available to compare stack_count options."
    labels = ", ".join(f"{count}-core" for count in stack_counts)
    return f"Chosen designs include these stack-count options: {labels}."


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _llc_diagnostic_output_dir(kind: str) -> Path:
    """Keep optional LLC diagnostics separate from formal geometry outputs."""

    return _project_root() / "outputs" / "llc_diagnostics" / kind


def _llc_transformer_output_dir(report: DesignReport) -> Path:
    """Return the formal transformer output directory for this run."""

    if report.llc_run_context is not None and report.llc_run_context.output_root:
        return Path(report.llc_run_context.output_root) / "transformer_design"
    return _project_root() / "outputs" / "transformer_design"


def _llc_external_lr_output_dir(report: DesignReport) -> Path:
    """Return the formal external Lr output directory for this run."""

    if report.llc_run_context is not None and report.llc_run_context.output_root:
        return Path(report.llc_run_context.output_root) / "resonant_inductor_design"
    return _project_root() / "outputs" / "resonant_inductor_design"


def _validate_llc_transformer_artifacts(
    artifact_paths: list[str],
    pareto_result,
) -> dict[str, object]:
    """Validate the persisted transformer contract before downstream stages run."""

    required_names = (
        "llc_transformer_feasible_candidates.csv",
        "llc_transformer_pareto_front.csv",
        "llc_transformer_chosen_candidates.csv",
        "llc_transformer_leakage_rejection_audit.csv",
    )
    paths_by_name = {Path(path).name: Path(path) for path in artifact_paths}
    missing = [name for name in required_names if name not in paths_by_name]
    if missing:
        return {"valid": False, "reason": f"Required transformer artifacts were not reported: {', '.join(missing)}"}
    empty = [name for name in required_names if not paths_by_name[name].is_file() or paths_by_name[name].stat().st_size <= 0]
    if empty:
        return {"valid": False, "reason": f"Required transformer artifacts are missing or empty: {', '.join(empty)}"}
    roles = {selection.role for selection in pareto_result.chosen_candidates}
    required_roles = {"recommended", "min-volume", "min-loss"}
    if not required_roles.issubset(roles):
        return {"valid": False, "reason": f"Transformer chosen candidates are missing roles: {', '.join(sorted(required_roles - roles))}"}
    chosen_ids = {selection.candidate.candidate_id for selection in pareto_result.chosen_candidates}
    feasible_ids = {candidate.candidate_id for candidate in pareto_result.feasible_candidates}
    if not chosen_ids.issubset(feasible_ids):
        return {"valid": False, "reason": "Transformer chosen candidates contain an ID absent from feasible candidates."}
    with paths_by_name["llc_transformer_chosen_candidates.csv"].open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    persisted_roles = {str(row.get("role", "")) for row in rows}
    if not required_roles.issubset(persisted_roles):
        return {"valid": False, "reason": "Transformer chosen CSV does not persist all required representative roles."}
    return {"valid": True, "reason": ""}


def _validate_llc_external_lr_artifacts(search_result) -> dict[str, object]:
    """Validate external Lr CSVs and representative roles before geometry use."""

    required_names = (
        "llc_external_resonant_inductor_feasible_candidates.csv",
        "llc_external_resonant_inductor_pareto_front.csv",
        "llc_external_resonant_inductor_chosen_candidates.csv",
    )
    if search_result is None:
        return {"valid": False, "reason": "External Lr search result is missing."}
    paths_by_name = {Path(path).name: Path(path) for path in search_result.artifact_paths}
    missing = [name for name in required_names if name not in paths_by_name]
    if missing:
        return {"valid": False, "reason": f"Required external Lr artifacts were not reported: {', '.join(missing)}"}
    empty = [name for name in required_names if not paths_by_name[name].is_file() or paths_by_name[name].stat().st_size <= 0]
    if empty:
        return {"valid": False, "reason": f"Required external Lr artifacts are missing or empty: {', '.join(empty)}"}
    required_roles = {"recommended", "min-volume", "min-loss"}
    selections = list(search_result.chosen_candidates)
    roles = {selection.role for selection in selections}
    if not required_roles.issubset(roles):
        return {"valid": False, "reason": f"External Lr chosen candidates are missing roles: {', '.join(sorted(required_roles - roles))}"}
    feasible_ids = {candidate.design_id for candidate in search_result.feasible_candidates}
    chosen_ids = {selection.candidate.design_id for selection in selections}
    if not chosen_ids.issubset(feasible_ids):
        return {"valid": False, "reason": "External Lr chosen candidates contain an ID absent from feasible candidates."}
    with paths_by_name["llc_external_resonant_inductor_chosen_candidates.csv"].open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    persisted_roles = {str(row.get("representative_role", "")) for row in rows}
    if not required_roles.issubset(persisted_roles):
        return {"valid": False, "reason": "External Lr chosen CSV does not persist all required representative roles."}
    persisted_ids = {
        str(row.get("design_id", ""))
        for row in rows
        if str(row.get("representative_role", "")) in required_roles
    }
    if not chosen_ids.issubset(persisted_ids):
        return {"valid": False, "reason": "External Lr chosen CSV does not match the current chosen candidate IDs."}
    return {"valid": True, "reason": ""}


def _llc_transformer_failure_result(
    *,
    failure_code: str,
    failure_reason: str,
    notes: list[str] | None = None,
    stage_artifact_paths: list[str] | None = None,
) -> MagneticResult:
    stage = LlcMagneticStageSummary(
        status="failed" if failure_code not in {"no_feasible_candidate", "artifact_incomplete"} else failure_code,
        failure_code=failure_code,
        failure_reason=failure_reason,
        artifact_paths=list(stage_artifact_paths or []),
    )
    return MagneticResult(
        summary=f"Separated LLC transformer magnetic screening failed: {failure_reason}",
        result_type="separated_llc_transformer",
        design_type="separated_llc_transformer",
        llc_result_summary=LlcMagneticResultSummary(transformer=stage),
        design_requirements={"transformer_failure_code": failure_code, "transformer_failure_reason": failure_reason},
        notes=[*(notes or []), f"Transformer failure code: {failure_code}.", failure_reason],
    )


def _finish_llc_transformer_failure(
    report: DesignReport,
    geometry_result: GeometryResult,
    *,
    search_result,
    output_policy: dict[str, object],
    pipeline_timing: dict[str, object],
    failure_code: str,
    failure_reason: str,
    pareto_result=None,
    artifact_paths: list[str] | None = None,
) -> DesignReport:
    paths = list(artifact_paths or search_result.artifact_paths)
    result = _llc_transformer_failure_result(
        failure_code=failure_code,
        failure_reason=failure_reason,
        notes=["External resonant-inductor screening was blocked because transformer results are incomplete."],
        stage_artifact_paths=paths,
    )
    result = replace(
        result,
        basic_feasible_count=search_result.evaluated_candidate_count,
        feasible_count=search_result.feasible_candidate_count,
        llc_transformer_result=search_result,
        transformer_pareto_result=pareto_result,
        artifact_paths=paths,
        performance_timing={"pipeline": {**pipeline_timing, "output_policy": output_policy}},
    )
    return _mark_llc_magnetics_blocked(
        replace(report, magnetic=result, geometry=geometry_result),
        failure_reason,
    )


def _finish_llc_external_lr_failure(
    report: DesignReport,
    geometry_result: GeometryResult,
    *,
    search_result,
    pareto_result,
    external_lr_search_result,
    transformer_artifact_paths: list[str],
    output_policy: dict[str, object],
    pipeline_timing: dict[str, object],
    failure_code: str,
    failure_reason: str,
) -> DesignReport:
    transformer_stage = _llc_stage_summary(
        search_result,
        pareto_count=pareto_result.pareto_count,
        recommended_design_id=pareto_result.recommended_candidate.candidate_id if pareto_result.recommended_candidate else None,
        status="available",
    )
    transformer_stage = replace(transformer_stage, artifact_paths=transformer_artifact_paths)
    external_stage = _llc_external_lr_stage_summary(
        external_lr_search_result.request,
        external_lr_search_result,
    )
    external_stage = replace(
        external_stage,
        status="failed" if failure_code == "artifact_incomplete" else "no_feasible_candidate",
        failure_code=failure_code,
        failure_reason=failure_reason,
        artifact_paths=list(external_lr_search_result.artifact_paths),
    )
    summary = LlcMagneticResultSummary(transformer=transformer_stage, external_lr=external_stage)
    result = MagneticResult(
        summary=f"Separated LLC external resonant-inductor screening failed: {failure_reason}",
        result_type="separated_llc_transformer",
        design_type="separated_llc_transformer",
        basic_feasible_count=search_result.evaluated_candidate_count,
        feasible_count=search_result.feasible_candidate_count,
        selected_design_id=transformer_stage.recommended_design_id,
        recommended_transformer_design_id=transformer_stage.recommended_design_id,
        llc_result_summary=summary,
        llc_transformer_result=search_result,
        transformer_pareto_result=pareto_result,
        transformer_pareto_candidates=pareto_result.pareto_candidates,
        transformer_chosen_candidates=pareto_result.chosen_candidates,
        transformer_representatives=pareto_result.representative_by_role,
        transformer_pareto_artifacts=pareto_result.artifact_paths,
        llc_external_resonant_inductor_target=external_lr_search_result.request,
        llc_external_resonant_inductor_search_result=external_lr_search_result,
        design_requirements={
            "external_lr_failure_code": failure_code,
            "external_lr_failure_reason": failure_reason,
            "magnetic_output_policy": output_policy,
        },
        performance_timing={"pipeline": {**pipeline_timing, "output_policy": output_policy}},
        artifact_paths=_dedupe_notes([*transformer_artifact_paths, *external_lr_search_result.artifact_paths]),
        notes=[
            "External resonant-inductor screening was not accepted as a successful stage.",
            f"External Lr failure code: {failure_code}.",
            failure_reason,
        ],
    )
    return _mark_llc_magnetics_blocked(
        replace(report, magnetic=result, geometry=geometry_result),
        failure_reason,
    )


def _finish_llc_magnetic_contract_failure(
    report: DesignReport,
    geometry_result: GeometryResult,
    *,
    search_result,
    pareto_result,
    external_lr_search_result,
    transformer_artifact_paths: list[str],
    output_policy: dict[str, object],
    pipeline_timing: dict[str, object],
    failure_reason: str,
) -> DesignReport:
    """Return a blocked result when the cross-component LLC contract is invalid."""

    transformer_stage = replace(
        _llc_stage_summary(
            search_result,
            pareto_count=pareto_result.pareto_count,
            recommended_design_id=(
                pareto_result.recommended_candidate.candidate_id
                if pareto_result.recommended_candidate
                else None
            ),
            status="available",
        ),
        artifact_paths=transformer_artifact_paths,
    )
    external_stage = _llc_external_lr_stage_summary(
        getattr(external_lr_search_result, "request", None),
        external_lr_search_result,
    )
    external_stage = replace(
        external_stage,
        failure_code="contract_inconsistent",
        failure_reason=failure_reason,
        artifact_paths=list(getattr(external_lr_search_result, "artifact_paths", []) or []),
    )
    summary = LlcMagneticResultSummary(transformer=transformer_stage, external_lr=external_stage)
    result = MagneticResult(
        summary=f"Separated LLC magnetic combination contract failed: {failure_reason}",
        result_type="separated_llc_transformer",
        design_type="separated_llc_transformer",
        basic_feasible_count=search_result.evaluated_candidate_count,
        feasible_count=search_result.feasible_candidate_count,
        selected_design_id=transformer_stage.recommended_design_id,
        recommended_transformer_design_id=transformer_stage.recommended_design_id,
        llc_result_summary=summary,
        llc_transformer_result=search_result,
        transformer_pareto_result=pareto_result,
        transformer_pareto_candidates=pareto_result.pareto_candidates,
        transformer_chosen_candidates=pareto_result.chosen_candidates,
        transformer_representatives=pareto_result.representative_by_role,
        transformer_pareto_artifacts=pareto_result.artifact_paths,
        llc_external_resonant_inductor_target=(
            getattr(external_lr_search_result, "request", None)
        ),
        llc_external_resonant_inductor_search_result=external_lr_search_result,
        design_requirements={
            "magnetic_contract_failure_code": "contract_inconsistent",
            "magnetic_contract_failure_reason": failure_reason,
            "magnetic_output_policy": output_policy,
        },
        performance_timing={"pipeline": {**pipeline_timing, "output_policy": output_policy}},
        artifact_paths=_dedupe_notes(
            [*transformer_artifact_paths, *getattr(external_lr_search_result, "artifact_paths", [])]
        ),
        notes=[
            "LLC magnetic results were blocked because the transformer/external Lr contract was inconsistent.",
            failure_reason,
        ],
    )
    return _mark_llc_magnetics_blocked(
        replace(report, magnetic=result, geometry=geometry_result),
        failure_reason,
    )


def _mark_llc_magnetics_blocked(report: DesignReport, reason: str | None) -> DesignReport:
    if report.llc_run_context is None:
        return report
    return replace(
        report,
        llc_run_context=report.llc_run_context.transition(
            "magnetics", "blocked", reason=reason or "LLC transformer magnetic stage failed."
        ),
    )


def _llc_output_policy(
    *,
    debug_outputs: bool,
    geometry_roles: tuple[str, ...] | None,
) -> dict[str, object]:
    valid_roles = ("min-volume", "min-loss", "recommended")
    requested_roles = (
        valid_roles
        if geometry_roles is None and debug_outputs
        else geometry_roles or ("recommended",)
    )
    normalized_roles = tuple(dict.fromkeys(str(role).strip().lower() for role in requested_roles))
    invalid_roles = tuple(role for role in normalized_roles if role not in valid_roles)
    if invalid_roles:
        raise ValueError(
            "LLC geometry roles must be selected from min-volume, min-loss, and recommended; "
            f"got {', '.join(invalid_roles)}."
        )
    selected_roles = tuple(role for role in valid_roles if role in normalized_roles)
    return {
        "debug_outputs_enabled": bool(debug_outputs),
        "geometry_roles": list(selected_roles),
        "transformer_debug_csv": bool(debug_outputs),
        "transformer_pareto_artifacts": bool(debug_outputs),
        "transformer_formal_csv": True,
        "transformer_formal_pareto_artifacts": True,
        "external_lr_artifacts": bool(debug_outputs),
        "external_lr_formal_artifacts": True,
        "diagnostic_output_root": str(_project_root() / "outputs" / "llc_diagnostics") if debug_outputs else "",
        "formal_output_roots": [
            "outputs/resonant_inductor_design",
            "outputs/inductor_design",
        ],
    }


def _llc_count(performance_counts: object, key: str, fallback: int = 0) -> int:
    """Read a non-negative integer count from a search result contract."""

    value = performance_counts.get(key) if isinstance(performance_counts, dict) else None
    if value is None:
        value = fallback
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return max(0, int(fallback))


def _llc_stage_summary(
    search_result,
    *,
    pareto_count: int,
    recommended_design_id: str | None,
    status: str,
) -> LlcMagneticStageSummary:
    counts = getattr(search_result, "performance_counts", {}) or {}
    evaluated = _llc_count(counts, "evaluated_candidate_count", getattr(search_result, "evaluated_candidate_count", 0))
    generated = _llc_count(counts, "generated_candidate_count", evaluated)
    precise = _llc_count(counts, "precise_evaluated_candidate_count", evaluated)
    prefilter_pass = _llc_count(counts, "prefilter_pass_count", precise)
    prefilter_rejected = _llc_count(
        counts,
        "prefilter_rejected_candidate_count",
        max(0, generated - prefilter_pass),
    )
    return LlcMagneticStageSummary(
        status=status,
        generated_candidate_count=generated,
        prefilter_rejected_candidate_count=prefilter_rejected,
        prefilter_pass_count=prefilter_pass,
        precise_evaluated_candidate_count=precise,
        feasible_candidate_count=_llc_count(
            counts,
            "feasible_candidate_count",
            getattr(search_result, "feasible_candidate_count", 0),
        ),
        pareto_candidate_count=max(0, int(pareto_count)),
        recommended_design_id=recommended_design_id,
        prefilter_rejection_counts=dict(getattr(search_result, "prefilter_rejection_counts", {}) or {}),
    )


def _llc_transformer_status(search_result, recommended_design_id: str | None) -> str:
    if search_result is None:
        return "not_evaluated"
    feasible = _llc_count(
        getattr(search_result, "performance_counts", {}),
        "feasible_candidate_count",
        getattr(search_result, "feasible_candidate_count", 0),
    )
    if feasible <= 0:
        return "no_feasible_candidate"
    return "available" if recommended_design_id else "no_recommendation"


def _llc_external_lr_stage_summary(target, search_result) -> LlcMagneticStageSummary:
    if search_result is None:
        return LlcMagneticStageSummary(status="not_evaluated")
    if target is not None and not target.is_design_required:
        return LlcMagneticStageSummary(status="not_required")
    counts = getattr(search_result, "performance_counts", {}) or {}
    request = getattr(search_result, "request", target)
    if request is not None and min(
        float(getattr(request, "current_rms_a", 0.0) or 0.0),
        float(getattr(request, "current_peak_a", 0.0) or 0.0),
        float(getattr(request, "fs_basis_hz", 0.0) or 0.0),
    ) <= 0.0:
        status = "invalid_target"
    elif _llc_count(counts, "feasible_candidate_count") > 0:
        status = "available"
    else:
        status = "no_feasible_candidate"
    return _llc_stage_summary(
        search_result,
        pareto_count=_llc_count(counts, "pareto_candidate_count"),
        recommended_design_id=None,
        status=status,
    )


def build_llc_combined_magnetic_design_id(
    transformer_design_id: str | None,
    external_lr_design_id: str | None,
    external_lr_status: str,
) -> str | None:
    """Build a combined ID only when both separated-LLC magnetic roles exist."""

    if external_lr_status != "available" or not transformer_design_id or not external_lr_design_id:
        return None
    return f"{transformer_design_id}+{external_lr_design_id}"


def build_llc_magnetic_combination_contract(
    *,
    report: DesignReport,
    fha_design,
    transformer_target: dict[str, object],
    transformer,
    external_lr,
    external_lr_target,
    transformer_artifact_paths: list[str],
    external_lr_artifact_paths: list[str],
    external_lr_status: str,
) -> LlcMagneticCombinationContract:
    """Build the single handoff contract shared by LLC downstream stages."""

    context = report.llc_run_context
    if context is None:
        raise ValueError("LLC magnetic combination contract requires a run context.")
    transformer_id = str(getattr(transformer, "candidate_id", ""))
    if not transformer_id:
        raise ValueError("LLC magnetic combination contract requires a transformer design ID.")
    external_id = (
        str(getattr(external_lr, "design_id", ""))
        if external_lr is not None and external_lr_status == "available"
        else None
    )
    external_target = external_lr_target
    external_target_h = (
        float(getattr(external_target, "external_lr_target_h"))
        if external_target is not None and external_id is not None
        else None
    )
    external_actual_h = float(getattr(external_lr, "actual_l_h")) if external_id is not None else None
    total_target_h = float(
        getattr(external_target, "lr_total_target_h", None)
        or getattr(fha_design, "lr_h")
        or transformer_target.get("lr_target_h", 0.0)
    )
    total_actual_h = float(getattr(external_lr, "total_lr_actual_h")) if external_id is not None else None
    transformer_leakage_h = float(getattr(transformer, "estimated_lk_h"))
    return LlcMagneticCombinationContract(
        run_id=context.run_id,
        topology_id=str(report.spec.topology_id),
        transformer_design_id=transformer_id,
        external_lr_design_id=external_id,
        combined_magnetic_design_id=(
            build_llc_combined_magnetic_design_id(transformer_id, external_id, external_lr_status)
        ),
        np=int(getattr(transformer, "np")),
        ns=int(getattr(transformer, "ns")),
        lm_target_h=float(getattr(transformer, "lm_target_h")),
        lm_actual_h=float(getattr(transformer, "lm_actual_h")),
        transformer_leakage_h=transformer_leakage_h,
        external_lr_target_h=external_target_h,
        external_lr_actual_h=external_actual_h,
        total_lr_target_h=total_target_h,
        total_lr_actual_h=total_actual_h,
        fs_hz=(
            float(getattr(external_target, "fs_basis_hz"))
            if external_target is not None and getattr(external_target, "fs_basis_hz", None) is not None
            else float(getattr(fha_design, "fr_hz", 0.0))
        ),
        vin_min_v=float(getattr(fha_design, "vin_min_v", None)),
        vin_nom_v=float(getattr(fha_design, "vin_nom_v", None)),
        vin_max_v=float(getattr(fha_design, "vin_max_v", None)),
        vout_min_v=float(getattr(fha_design, "vout_min_v", None)),
        vout_nom_v=float(getattr(fha_design, "vout_nom_v", None)),
        vout_max_v=float(getattr(fha_design, "vout_max_v", None)),
        transformer_current_basis=str(getattr(transformer, "current_basis_label", "")),
        transformer_current_rms_a=getattr(transformer, "primary_rms_current_design_a", None),
        transformer_current_peak_a=(
            float(getattr(fha_design, "worst_case_current_stress", {}).get("resonant_tank_peak_a"))
            if isinstance(getattr(fha_design, "worst_case_current_stress", {}), dict)
            and getattr(fha_design, "worst_case_current_stress", {}).get("resonant_tank_peak_a") is not None
            else None
        ),
        external_lr_current_basis=(str(getattr(external_target, "current_basis", "")) if external_target is not None else None),
        external_lr_current_rms_a=(float(getattr(external_target, "current_rms_a")) if external_target is not None else None),
        external_lr_current_peak_a=(float(getattr(external_target, "current_peak_a")) if external_target is not None else None),
        transformer_artifact_paths=tuple(transformer_artifact_paths),
        external_lr_artifact_paths=tuple(external_lr_artifact_paths),
    )


def validate_llc_magnetic_combination_contract(
    *,
    report: DesignReport,
    contract: LlcMagneticCombinationContract,
    transformer_candidates: list,
    external_lr_candidates: list,
) -> dict[str, object]:
    """Validate the contract at the magnetic-to-downstream pipeline boundary."""

    context = report.llc_run_context
    if context is None:
        return {"valid": False, "reason": "LLC magnetic combination contract has no run context."}
    try:
        contract.validate(
            topology_id=report.spec.topology_id,
            run_id=context.run_id,
            transformer_candidates=transformer_candidates,
            external_lr_candidates=external_lr_candidates,
        )
    except (TypeError, ValueError) as exc:
        return {"valid": False, "reason": str(exc)}
    return {"valid": True, "reason": ""}
