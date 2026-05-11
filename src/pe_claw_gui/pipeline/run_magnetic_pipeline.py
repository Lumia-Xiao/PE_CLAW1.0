"""Magnetic-stage runtime orchestration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..engines.magnetics.allow_profiles import get_default_allow_profile
from ..engines.magnetics.candidate_compression import compress_candidates
from ..engines.magnetics.candidate_metrics import MagneticCandidateContext
from ..engines.magnetics.stacked_expansion import (
    STACKED_MARGIN_NEAR_LIMIT_THRESHOLD,
    STACKED_SEED_LIMIT,
    expand_stacked_same_core_candidates,
    select_stacked_seed_candidates,
)
from ..models.design_report import DesignReport
from ..models.geometry_result import GeometryResult
from ..models.magnetic_result import MagneticResult
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
    synthesize_fixed_inductor_candidates,
)


def run_magnetic_pipeline(report: DesignReport) -> DesignReport:
    """Attach the inductor magnetic stage to a design report."""
    geometry_result = report.geometry or GeometryResult(notes=["Geometry estimation remains a placeholder stage."])

    if report.candidate is None:
        magnetic_result = MagneticResult(
            summary="Inductor design did not run because no synthesized candidate is available.",
            notes=["Topology synthesis must complete before the magnetic stage can run."],
        )
        return replace(report, magnetic=magnetic_result, geometry=geometry_result)

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
        f"P_throughput uses {screening_context.throughput_label} = {request.throughput_power_w:.6g} W."
    )

    try:
        basic_feasible_candidates = synthesize_fixed_inductor_candidates(request)
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
                notes=notes + ["The OpenMagnetics-derived search space returned no feasible candidates."],
            )
            return replace(report, magnetic=magnetic_result, geometry=geometry_result)

        compression_result = compress_candidates(
            basic_feasible_candidates,
            context=screening_context,
            allow_profile=allow_profile,
        )
        notes.extend(compression_result.notes)

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
            selected_design_id=selected_design_id,
            screened_candidates=final_compression_result.filtered_candidates,
            compressed_candidates=final_compression_result.compressed_candidates,
            chosen_designs=chosen_designs,
            best_by_stack_count=best_by_stack_count,
            artifact_paths=artifact_result.artifact_paths,
            notes=notes,
        )
    except InductorDatabaseUnavailableError as exc:
        magnetic_result = MagneticResult(
            summary="Inductor design search could not start because the external magnetic database is unavailable.",
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


def _describe_chosen_stack_options(chosen_designs) -> str:
    stack_counts = sorted({design.stack_count for design in chosen_designs})
    if not stack_counts:
        return "No chosen designs were available to compare stack_count options."
    labels = ", ".join(f"{count}-core" for count in stack_counts)
    return f"Chosen designs include these stack-count options: {labels}."
