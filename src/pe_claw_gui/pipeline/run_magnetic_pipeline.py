"""Magnetic-stage runtime orchestration."""

from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path

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
from ..models.magnetic_result import MagneticResult
try:
    from ..topologies.dc_dc.llc_resonant_converter_diode_rectifier.fha_design import (
        LLCFHADesign,
        LLCOperatingPointResult,
    )
    from ..topologies.dc_dc.llc_resonant_converter_diode_rectifier.transformer_design import (
        build_llc_external_resonant_inductor_target,
        build_llc_transformer_pareto_result,
        build_transformer_design_inputs_from_fha,
        generate_llc_external_resonant_inductor_candidates,
        generate_separated_llc_transformer_candidates,
        make_fha_boundary_frequency_solver,
    )
except ModuleNotFoundError:  # New LLC topology package is outside the 1.0 GUI scope.
    LLCFHADesign = None
    LLCOperatingPointResult = None
    build_llc_external_resonant_inductor_target = None
    build_llc_transformer_pareto_result = None
    build_transformer_design_inputs_from_fha = None
    generate_llc_external_resonant_inductor_candidates = None
    generate_separated_llc_transformer_candidates = None
    make_fha_boundary_frequency_solver = None

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
LLC_TRANSFORMER_MATERIAL_LIMIT = 16
LLC_EXTERNAL_LR_MATERIAL_LIMIT = 16
FLYBACK_MATERIAL_LIMIT = 16


def run_magnetic_pipeline(
    report: DesignReport,
    *,
    backend_config: MagneticDataBackendConfig | None = None,
) -> DesignReport:
    """Attach magnetic design plus a shadow-only core-loss excitation audit."""

    from ..engines.magnetics.core_loss_excitation_integration import (
        attach_core_loss_excitation_audit,
    )

    completed = _run_magnetic_pipeline_without_excitation_audit(report, backend_config=backend_config)
    return attach_core_loss_excitation_audit(completed)


def _run_magnetic_pipeline_without_excitation_audit(
    report: DesignReport,
    *,
    backend_config: MagneticDataBackendConfig | None = None,
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
) -> DesignReport:
    """Run separated LLC transformer first-pass magnetic screening from Run Magnetics."""

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
        magnetic_result = MagneticResult(
            summary="LLC transformer magnetic screening could not run because transformer target metadata is missing.",
            result_type="separated_llc_transformer",
            design_type="separated_llc_transformer",
            notes=[
                "Run Design must complete the diode LLC FHA design before Run Magnetics can screen separated transformer candidates.",
            ],
        )
        return replace(report, magnetic=magnetic_result, geometry=geometry_result)

    try:
        backend_bundle = resolve_magnetic_data_backend(
            backend_config or get_production_magnetic_backend_config()
        )
        fha_design = _rebuild_llc_fha_design(llc_fha_metadata)
        transformer_inputs = build_transformer_design_inputs_from_fha(fha_design)
        search_result = generate_separated_llc_transformer_candidates(
            transformer_inputs,
            core_records=(backend_bundle.cores if backend_bundle is not None else None),
            material_records=(backend_bundle.materials if backend_bundle is not None else None),
            wire_records=(backend_bundle.wires if backend_bundle is not None else None),
            max_scale_factor=80,
            frequency_solver=make_fha_boundary_frequency_solver(fha_design),
            core_limit=48,
            material_limit=LLC_TRANSFORMER_MATERIAL_LIMIT,
            wire_limit=16,
            write_debug_csv=True,
        )
        pareto_result = build_llc_transformer_pareto_result(
            search_result.feasible_candidates,
            write_artifacts=True,
        )
        recommended = pareto_result.recommended_candidate or search_result.recommended_preliminary_candidate
        selected_design_id = recommended.candidate_id if recommended is not None else None
        external_lr_target = (
            build_llc_external_resonant_inductor_target(fha_design, recommended)
            if recommended is not None
            else None
        )
        external_lr_search_result = (
            generate_llc_external_resonant_inductor_candidates(
                external_lr_target,
                core_records=(backend_bundle.cores if backend_bundle is not None else None),
                material_records=(backend_bundle.materials if backend_bundle is not None else None),
                wire_records=(backend_bundle.wires if backend_bundle is not None else None),
                material_limit=LLC_EXTERNAL_LR_MATERIAL_LIMIT,
            )
            if external_lr_target is not None
            else None
        )
        design_requirements = _llc_transformer_design_requirements(transformer_target, search_result)
        design_requirements["transformer_pareto_count"] = pareto_result.pareto_count
        design_requirements["transformer_chosen_count"] = pareto_result.chosen_count
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
        for role in ("min-volume", "min-loss", "recommended"):
            selection = pareto_result.representative_by_role.get(role)
            candidate_for_role = selection.candidate if selection is not None else (recommended if role == "recommended" else None)
            if candidate_for_role is None:
                continue
            transformer_comparison_candidates[role] = candidate_for_role
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
        if transformer_comparison_candidates:
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
            artifact_paths=artifact_paths,
            notes=_dedupe_notes(notes),
        )
    except Exception as exc:
        magnetic_result = MagneticResult(
            summary="Separated LLC transformer magnetic screening failed unexpectedly.",
            result_type="separated_llc_transformer",
            design_type="separated_llc_transformer",
            notes=[
                "Run Design completed, but Run Magnetics could not screen separated LLC transformer candidates.",
                f"{type(exc).__name__}: {exc}",
            ],
        )
    return replace(report, magnetic=magnetic_result, geometry=geometry_result)


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
) -> dict[str, float | str | bool | None]:
    return {
        "topology_id": str(transformer_target.get("topology_id") or "llc_resonant_converter_diode_rectifier"),
        "design_type": "separated_llc_transformer",
        "transformer_realizes": "Np:Ns and Lm",
        "external_resonant_inductor_realizes": "Lr",
        "np": transformer_target.get("base_np"),
        "ns": transformer_target.get("base_ns"),
        "lm_target_h": transformer_target.get("lm_target_h"),
        "lr_target_h": transformer_target.get("lr_target_h"),
        "b_limit_t": transformer_target.get("b_limit_t"),
        "primary_bridge_type": transformer_target.get("primary_bridge_type"),
        "secondary_rectifier_type": transformer_target.get("secondary_rectifier_type"),
        "boundary_saturation_cases": ", ".join(str(case) for case in transformer_target.get("boundary_saturation_case_names", [])),
        "evaluated_candidate_count": search_result.evaluated_candidate_count,
        "feasible_candidate_count": search_result.feasible_candidate_count,
    }


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
