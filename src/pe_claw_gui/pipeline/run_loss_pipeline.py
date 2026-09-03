"""Loss-stage runtime orchestration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..models.design_report import DesignReport
from ..models.design_run_context import get_run_output_dir
from ..models.loss_result import LossResult
from .options import MAGNETIC_LOSS_DISABLED_NOTE, PipelineOptions, resolve_pipeline_options
from ..engines.magnetics.inductor_adapter import (
    InductorRequestUnavailableError,
    build_inductor_operating_point_request,
)
from ..engines.magnetics.inductor_design import evaluate_selected_designs, export_design_artifacts
from ..topology_capabilities import is_single_phase_full_bridge_inverter_topology
from ..engines.magnetics.core_loss_audit import core_loss_consistency, core_loss_status
from ..models.llc_run_context import is_llc_topology


def run_loss_pipeline(
    report: DesignReport,
    preserve_selected_design_id: bool = False,
    refresh_plot_artifact: bool = True,
    pipeline_options: PipelineOptions | None = None,
) -> DesignReport:
    """Attach loss results and refresh the selected-hardware excitation audit."""

    from ..engines.magnetics.core_loss_excitation_integration import (
        attach_core_loss_excitation_audit,
    )

    completed = _run_loss_pipeline_without_excitation_audit(
        report,
        preserve_selected_design_id=preserve_selected_design_id,
        refresh_plot_artifact=refresh_plot_artifact,
        pipeline_options=pipeline_options,
    )
    completed = attach_core_loss_excitation_audit(
        completed,
        include_design_reference=False,
        include_operating_waveform=True,
    )
    return _finalize_llc_loss_stage(completed)


def _finalize_llc_loss_stage(report: DesignReport) -> DesignReport:
    """Close the LLC loss stage from the result actually produced."""

    context = report.llc_run_context
    if context is None or not is_llc_topology(report.spec.topology_id):
        return report
    loss = report.loss
    if loss is not None and loss.recommended_design_id and loss.total_loss_w is not None:
        updated_context = context.transition("loss", "succeeded")
    else:
        updated_context = context.transition(
            "loss",
            "blocked",
            reason="LLC loss result is incomplete; no current-run recommended magnetic loss is available.",
        )
    return replace(report, llc_run_context=updated_context)


def _run_loss_pipeline_without_excitation_audit(
    report: DesignReport,
    preserve_selected_design_id: bool = False,
    refresh_plot_artifact: bool = True,
    pipeline_options: PipelineOptions | None = None,
) -> DesignReport:
    """Attach fixed-inductor loss evaluation results to a design report."""
    options = resolve_pipeline_options(pipeline_options)
    if not options.enable_magnetic_design:
        return replace(report, loss=LossResult(notes=[MAGNETIC_LOSS_DISABLED_NOTE]))

    if report.candidate is None:
        loss_result = LossResult(notes=["Loss calculation did not run because no synthesized candidate is available."])
        return replace(report, loss=loss_result)

    if report.magnetic is not None and report.magnetic.result_type == "separated_llc_transformer":
        contract = report.magnetic.llc_magnetic_contract
        if report.llc_run_context is not None and (contract is None or not contract.combined_magnetic_design_id):
            loss_result = LossResult(
                notes=["LLC magnetic loss is blocked because the magnetic combination contract is incomplete."]
            )
            return replace(report, loss=loss_result)
        transformer_result = report.magnetic.transformer_pareto_result
        transformer = getattr(transformer_result, "recommended_candidate", None)
        external_result = report.magnetic.llc_external_resonant_inductor_search_result
        external = getattr(external_result, "recommended_candidate", None)
        if transformer is None and external is None:
            loss_result = LossResult(
                notes=["No recommended LLC transformer or external resonant-inductor loss result is available."]
            )
        else:
            transformer_core = _optional_float(getattr(transformer, "core_loss_w", None))
            transformer_copper = _optional_float(getattr(transformer, "copper_loss_w", None))
            transformer_total = _optional_float(getattr(transformer, "total_loss_w", None))
            external_core = _optional_float(getattr(external, "core_loss_w", None))
            external_copper = _optional_float(getattr(external, "copper_loss_w", None))
            external_total = _optional_float(getattr(external, "total_loss_w", None))
            core_loss = _sum_optional(transformer_core, external_core)
            copper_loss = _sum_optional(transformer_copper, external_copper)
            total_loss = _sum_optional(transformer_total, external_total)
            volume = _sum_optional(
                _optional_float(getattr(transformer, "estimated_volume_m3", None)),
                _optional_float(getattr(external, "estimated_volume_m3", None)),
            )
            transformer_id = (
                contract.transformer_design_id
                if contract is not None
                else getattr(transformer, "candidate_id", None)
            )
            external_id = (
                contract.external_lr_design_id
                if contract is not None
                else getattr(external, "design_id", None)
            )
            ids = (
                contract.combined_magnetic_design_id
                if contract is not None
                else report.magnetic.recommended_combined_magnetic_design_id
                or "+".join(value for value in (transformer_id, external_id) if value)
                or transformer_id
                or external_id
            )
            component_volumes = {
                key: value
                for key, value in {
                    "transformer_volume_m3": _optional_float(getattr(transformer, "estimated_volume_m3", None)),
                    "external_lr_volume_m3": _optional_float(getattr(external, "estimated_volume_m3", None)),
                    "combined_magnetic_volume_m3": volume,
                }.items()
                if value is not None
            }
            breakdown = {
                key: value
                for key, value in {
                    "llc_transformer_core_loss_w": transformer_core,
                    "llc_transformer_copper_loss_w": transformer_copper,
                    "llc_transformer_total_loss_w": transformer_total,
                    "llc_external_resonant_inductor_core_loss_w": external_core,
                    "llc_external_resonant_inductor_copper_loss_w": external_copper,
                    "llc_external_resonant_inductor_total_loss_w": external_total,
                    "llc_magnetic_core_loss_w": core_loss,
                    "llc_magnetic_copper_loss_w": copper_loss,
                    "llc_magnetic_total_loss_w": total_loss,
                }.items()
                if value is not None
            }
            loss_result = LossResult(
                total_loss_w=total_loss,
                breakdown_w=breakdown,
                recommended_design_id=ids,
                recommended_design_total_volume_m3=volume,
                component_volumes_m3=component_volumes,
                notes=[
                    "LLC magnetic loss is aggregated from the recommended transformer and external resonant-inductor candidates.",
                    "Transformer leakage is not added to the external resonant-inductor loss; the two roles remain separate.",
                    "The loss summary reads the shared v2 magnetic candidate results without changing candidate screening.",
                ],
            )
        return replace(report, loss=loss_result)

    if report.magnetic is not None and report.magnetic.result_type == "ac_dc_sendust_reactor":
        selection = report.magnetic.ac_dc_reactor_result
        selected = selection.selected_candidate if selection is not None else None
        if selected is None:
            loss_result = LossResult(notes=["No selected AC-DC Sendust reactor is available for loss reporting."])
            return replace(report, loss=loss_result)
        top_losses = {
            candidate.candidate_id: {
                key: value
                for key, value in {
                    "copper_loss_w": candidate.copper_loss_w,
                    "core_loss_w": candidate.core_loss_w,
                    "total_loss_w": candidate.total_loss_w,
                }.items()
                if value is not None
            }
            for candidate in (selection.top_candidates if selection is not None else [])
        }
        loss_result = LossResult(
            total_loss_w=selected.total_loss_w,
            breakdown_w={
                "ac_dc_reactor_copper_loss_w": selected.copper_loss_w or 0.0,
                "ac_dc_reactor_core_loss_w": selected.core_loss_w or 0.0,
                "ac_dc_reactor_total_loss_w": selected.total_loss_w or 0.0,
            },
            recommended_design_id=selected.candidate_id,
            recommended_design_total_volume_m3=(selected.estimated_volume_cm3 or 0.0) * 1e-6,
            top_design_losses=top_losses,
            notes=[
                "AC-DC Sendust reactor loss is reported from the design-point selector result.",
                "Core loss uses ripple-frequency deltaB with the fixed Sendust Steinmetz table.",
                "Copper loss uses equivalent copper area sized from target window utilization, with current-density as a minimum copper-area constraint.",
            ],
        )
        return replace(report, loss=loss_result)

    if report.magnetic is not None and report.magnetic.result_type == "flyback_coupled_inductor":
        selected_design = _selected_magnetic_design(report)
        if selected_design is None or selected_design.reference_total_loss_w is None:
            loss_result = LossResult(notes=["No selected Flyback coupled-inductor loss result is available."])
            return replace(report, loss=loss_result)
        top_losses = {
            design.candidate_id: {
                key: value
                for key, value in {
                    "copper_loss_w": design.reference_copper_loss_w,
                    "core_loss_w": design.reference_core_loss_w,
                    "total_loss_w": design.reference_total_loss_w,
                }.items()
                if value is not None
            }
            for design in report.magnetic.chosen_designs
        }
        loss_result = LossResult(
            total_loss_w=selected_design.reference_total_loss_w,
            breakdown_w={
                key: value
                for key, value in {
                    "flyback_coupled_inductor_copper_loss_w": selected_design.reference_copper_loss_w,
                    "flyback_coupled_inductor_core_loss_w": selected_design.reference_core_loss_w,
                    "flyback_coupled_inductor_total_loss_w": selected_design.reference_total_loss_w,
                }.items()
                if value is not None
            },
            recommended_design_id=selected_design.candidate_id,
            recommended_design_total_volume_m3=selected_design.total_volume_m3,
            top_design_losses=top_losses,
            notes=[
                "Flyback coupled-inductor loss is reported from the first-pass magnetic search reference loss.",
                "Copper loss uses the selected primary and secondary winding resistance proxy at the design point.",
                "Core loss uses the Flyback first-pass ferrite Bpeak/frequency/volume proxy.",
                "Switching-device, clamp/snubber, leakage, proximity, insulation, and EMI losses are not included in this magnetic loss readback.",
            ],
        )
        return replace(report, loss=loss_result)

    if report.magnetic is not None and report.magnetic.result_type == "psfb_transformer_output_inductor":
        selected_design = _selected_magnetic_design(report)
        if selected_design is None or selected_design.reference_total_loss_w is None:
            loss_result = LossResult(notes=["No selected PSFB transformer/output-inductor loss result is available."])
            return replace(report, loss=loss_result)
        metadata = selected_design.metadata if isinstance(selected_design.metadata, dict) else {}
        top_losses = {
            design.candidate_id: {
                key: value
                for key, value in {
                    "copper_loss_w": design.reference_copper_loss_w,
                    "core_loss_w": design.reference_core_loss_w,
                    "total_loss_w": design.reference_total_loss_w,
                    "transformer_total_loss_w": (
                        design.metadata.get("transformer_total_loss_w")
                        if isinstance(design.metadata, dict)
                        else None
                    ),
                    "output_inductor_total_loss_w": (
                        design.metadata.get("output_inductor_total_loss_w")
                        if isinstance(design.metadata, dict)
                        else None
                    ),
                }.items()
                if value is not None
            }
            for design in report.magnetic.chosen_designs
        }
        breakdown_w = {
            key: float(value)
            for key, value in {
                "psfb_transformer_copper_loss_w": metadata.get("transformer_copper_loss_w"),
                "psfb_transformer_core_loss_w": metadata.get("transformer_core_loss_w"),
                "psfb_transformer_total_loss_w": metadata.get("transformer_total_loss_w"),
                "psfb_output_inductor_copper_loss_w": metadata.get("output_inductor_copper_loss_w"),
                "psfb_output_inductor_core_loss_w": metadata.get("output_inductor_core_loss_w"),
                "psfb_output_inductor_total_loss_w": metadata.get("output_inductor_total_loss_w"),
                "psfb_magnetic_copper_loss_w": selected_design.reference_copper_loss_w,
                "psfb_magnetic_core_loss_w": selected_design.reference_core_loss_w,
                "psfb_magnetic_total_loss_w": selected_design.reference_total_loss_w,
            }.items()
            if value is not None
        }
        loss_result = LossResult(
            total_loss_w=selected_design.reference_total_loss_w,
            breakdown_w=breakdown_w,
            recommended_design_id=selected_design.candidate_id,
            recommended_design_total_volume_m3=selected_design.total_volume_m3,
            top_design_losses=top_losses,
            notes=[
                "PSFB transformer/output-inductor loss is reported from the first-pass magnetic search reference loss.",
                "Transformer copper/core loss uses the selected primary/secondary winding resistance and ferrite Bpeak/frequency/volume proxy.",
                "Output-inductor copper/core loss uses the paired first-pass gapped output-filter inductor candidate.",
                "Semiconductor switching loss, ZVS-transition residual loss, leakage clamp/snubber loss, proximity loss, insulation, EMI, and manufacturability losses are not included in this magnetic loss readback.",
            ],
        )
        return replace(report, loss=loss_result)

    if (
        is_single_phase_full_bridge_inverter_topology(report.spec.topology_id)
        and report.magnetic is not None
        and report.magnetic.chosen_designs
        and not _is_tcm_inverter_report(report)
    ):
        selected_design = _selected_magnetic_design(report)
        if selected_design is not None and selected_design.reference_total_loss_w is not None:
            top_losses = {
                design.candidate_id: {
                    key: value
                    for key, value in {
                        "copper_loss_w": design.reference_copper_loss_w,
                        "core_loss_w": design.reference_core_loss_w,
                        "total_loss_w": design.reference_total_loss_w,
                    }.items()
                    if value is not None
                }
                for design in report.magnetic.chosen_designs
            }
            loss_result = LossResult(
                total_loss_w=selected_design.reference_total_loss_w,
                breakdown_w={
                    key: value
                    for key, value in {
                        "inductor_copper_loss_w": selected_design.reference_copper_loss_w,
                        "inductor_core_loss_w": selected_design.reference_core_loss_w,
                        "inductor_total_loss_w": selected_design.reference_total_loss_w,
                    }.items()
                    if value is not None
                },
                recommended_design_id=selected_design.candidate_id,
                recommended_design_total_volume_m3=selected_design.total_volume_m3,
                top_design_losses=top_losses,
                notes=[
                    "Single-phase inverter output-inductor loss is reported from the rough magnetic realization.",
                    "This is a first-pass core/copper estimate; calibrated inverter inductor thermal validation is still pending.",
                ],
        )
        return replace(report, loss=loss_result)

    if report.magnetic is None or not report.magnetic.chosen_designs:
        loss_result = LossResult(notes=["No selected fixed inductor designs are available for operating-point evaluation."])
        return replace(report, loss=loss_result)

    try:
        operating_request = build_inductor_operating_point_request(report)
        evaluations = evaluate_selected_designs(report.magnetic.chosen_designs, operating_request)
        recommended_design_id = _choose_recommended_design_id(
            report.magnetic.chosen_designs,
            evaluations,
            preferred_design_id=_resolve_preferred_design_id(report) if preserve_selected_design_id else None,
        )
        evaluation_by_id = {evaluation.design_id: evaluation for evaluation in evaluations}
        design_by_id = {design.candidate_id: design for design in report.magnetic.chosen_designs}
        recommended_evaluation = evaluation_by_id.get(recommended_design_id or "")
        recommended_design = design_by_id.get(recommended_design_id or "")

        top_design_losses = {
            evaluation.design_id: _loss_values_for_evaluation(report, evaluation, operating_request)
            for evaluation in evaluations
        }
        recommended_loss_values = (
            top_design_losses.get(recommended_design_id or "")
            if recommended_design_id
            else {}
        )
        breakdown_w = {
            key: value
            for key, value in {
                "inductor_copper_loss_w": recommended_loss_values.get("copper_loss_w"),
                "inductor_core_loss_w": recommended_loss_values.get("core_loss_w"),
                "inductor_total_loss_w": recommended_loss_values.get("total_loss_w"),
            }.items()
            if value is not None
        }

        loss_notes = list(operating_request.notes) + ["Loss stage currently evaluates fixed inductor copper and core losses only."]
        if _is_three_phase_per_phase_inverter_report(report):
            topology_label = "NPC" if _is_three_phase_npc_inverter_report(report) else "Three-phase"
            loss_notes.extend(
                [
                    f"{topology_label} output inductor loss is per-inductor operating evaluation multiplied by 3.",
                    "Magnetic search page still shows one representative per-phase design.",
                ]
            )
            if _is_three_phase_two_level_inverter_report(report):
                loss_notes.extend(
                    [
                        "Semiconductor loss uses first-pass six-switch SPWM operating stress.",
                        "DC-link capacitor loss uses the selected SxP bank and three-phase PWM-level switch-state DC-link current RMS proxy when capacitor refresh is available.",
                    ]
                )
            elif _is_three_phase_npc_inverter_report(report):
                loss_notes.extend(
                    [
                        "Semiconductor loss uses first-pass NPC PD-SPWM operating stress over 12 active switch positions and 6 clamp diode positions.",
                        "NPC capacitor loss uses selected upper/lower split-link banks and PD-SPWM switch-state current proxies when capacitor refresh is available.",
                        "Neutral-point balancing dynamics, harmonic-by-harmonic ESR, dead-time, Coss, and parasitic transient effects remain pending.",
                    ]
                )
        if _is_tcm_inverter_report(report) and not preserve_selected_design_id:
            tcm_rerank_notes = [
                "TCM operating magnetic recommendation is selected after segment-resolved loss rerank.",
                "Magnetic-stage search recommendation is retained for audit as rough reference-loss Pareto selection.",
            ]
            for note in tcm_rerank_notes:
                if note not in loss_notes:
                    loss_notes.append(note)
        if recommended_evaluation is not None:
            for note in recommended_evaluation.notes:
                if note not in loss_notes:
                    loss_notes.append(note)
        loss_result = LossResult(
            total_loss_w=recommended_loss_values.get("total_loss_w"),
            breakdown_w=breakdown_w,
            recommended_design_id=recommended_design_id,
            recommended_design_total_volume_m3=recommended_design.total_volume_m3 if recommended_design else None,
            top_design_losses=top_design_losses,
            notes=loss_notes,
            core_loss_status=core_loss_status(recommended_design.metadata if recommended_design else None),
            core_loss_audit=_candidate_core_loss_audit(report.magnetic.chosen_designs),
        )
        plot_notes = [
            note
            for note in report.magnetic.notes
            if not (
                _is_tcm_inverter_report(report)
                and note.startswith("Pareto plot highlights recommended design ")
            )
        ]
        artifact_paths = report.magnetic.artifact_paths
        if refresh_plot_artifact:
            try:
                artifact_result = export_design_artifacts(
                    feasible_candidates=[],
                    screened_candidates=report.magnetic.screened_candidates,
                    compressed_candidates=report.magnetic.compressed_candidates,
                    pareto_candidates=[],
                    chosen_candidates=report.magnetic.chosen_designs,
                    recommended_design_id=recommended_design_id,
                    write_csvs=False,
                    output_dir=get_run_output_dir(report, "inductor_design"),
                )
                if artifact_result.artifact_paths:
                    artifact_paths = _merge_artifact_paths(report.magnetic.artifact_paths, artifact_result.artifact_paths)
                if artifact_result.plot_source_name and f"PF plot is drawn from {artifact_result.plot_source_name}." not in plot_notes:
                    plot_notes.append(f"PF plot is drawn from {artifact_result.plot_source_name}.")
                if artifact_result.plot_color_dimension and f"PF plot color encoding uses {artifact_result.plot_color_dimension}." not in plot_notes:
                    plot_notes.append(f"PF plot color encoding uses {artifact_result.plot_color_dimension}.")
                if artifact_result.plot_fallback_note and artifact_result.plot_fallback_note not in plot_notes:
                    plot_notes.append(artifact_result.plot_fallback_note)
                if recommended_design_id:
                    highlight_note = (
                        f"Pareto plot highlights active operating recommendation {recommended_design_id}."
                        if _is_tcm_inverter_report(report)
                        else f"Pareto plot highlights recommended design {recommended_design_id}."
                    )
                    if highlight_note not in plot_notes:
                        plot_notes.append(highlight_note)
            except Exception as exc:
                plot_notes.append(f"Pareto plot refresh after loss evaluation failed: {type(exc).__name__}: {exc}")
        elif preserve_selected_design_id and "Operating-point refresh reused the existing fixed magnetic design set without regenerating artifacts." not in plot_notes:
            plot_notes.append("Operating-point refresh reused the existing fixed magnetic design set without regenerating artifacts.")

        magnetic_result = replace(
            report.magnetic,
            evaluations=evaluations,
            search_selected_design_id=report.magnetic.search_selected_design_id or report.magnetic.selected_design_id,
            selected_design_id=recommended_design_id,
            artifact_paths=artifact_paths,
            notes=plot_notes,
        )
        return replace(report, loss=loss_result, magnetic=magnetic_result)
    except InductorRequestUnavailableError as exc:
        loss_result = LossResult(notes=[str(exc)])
        return replace(report, loss=loss_result)
    except Exception as exc:
        loss_result = LossResult(notes=[f"Inductor loss evaluation failed: {type(exc).__name__}: {exc}"])
        return replace(report, loss=loss_result)


def _choose_recommended_design_id(designs, evaluations, preferred_design_id: str | None = None) -> str | None:
    if not designs:
        return None

    default_design = designs[len(designs) // 2]
    design_ids = {design.candidate_id for design in designs}
    if preferred_design_id and preferred_design_id in design_ids:
        return preferred_design_id
    if not evaluations:
        return default_design.candidate_id

    evaluation_by_id = {evaluation.design_id: evaluation for evaluation in evaluations}
    scored_rows = []
    for design in designs:
        evaluation = evaluation_by_id.get(design.candidate_id)
        if evaluation is None or design.total_volume_m3 is None or evaluation.total_loss_w is None:
            return default_design.candidate_id
        scored_rows.append((design, evaluation))

    volumes = [design.total_volume_m3 or 0.0 for design, _ in scored_rows]
    losses = [evaluation.total_loss_w or 0.0 for _, evaluation in scored_rows]
    min_volume, max_volume = min(volumes), max(volumes)
    min_loss, max_loss = min(losses), max(losses)

    def normalize(value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.0
        return (value - low) / (high - low)

    best_design = min(
        scored_rows,
        key=lambda row: (
            0.5 * normalize(row[0].total_volume_m3 or 0.0, min_volume, max_volume)
            + 0.5 * normalize(row[1].total_loss_w or 0.0, min_loss, max_loss),
            row[0].total_volume_m3 or float("inf"),
            row[1].total_loss_w or float("inf"),
            row[0].candidate_id,
        ),
    )[0]
    return best_design.candidate_id


def _optional_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _sum_optional(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    return sum(present) if present else None


def _is_tcm_inverter_report(report: DesignReport) -> bool:
    candidate = report.candidate
    if candidate is None:
        return False
    return str(candidate.mode_capable or "").startswith("tcm_")


def _is_three_phase_two_level_inverter_report(report: DesignReport) -> bool:
    return report.spec.topology_id == "three_phase_two_level_voltage_source_inverter"


def _is_three_phase_npc_inverter_report(report: DesignReport) -> bool:
    return report.spec.topology_id == "three_phase_three_level_npc_inverter"


def _is_three_phase_per_phase_inverter_report(report: DesignReport) -> bool:
    return _is_three_phase_two_level_inverter_report(report) or _is_three_phase_npc_inverter_report(report)


def _magnetic_quantity(report: DesignReport, operating_request=None) -> int:
    if _is_three_phase_per_phase_inverter_report(report):
        metadata = getattr(operating_request, "metadata", {}) if operating_request is not None else {}
        value = metadata.get("magnetic_quantity")
        if value is None and report.magnetic is not None:
            value = report.magnetic.design_requirements.get("magnetic_quantity")
        try:
            return max(int(value), 1)
        except (TypeError, ValueError):
            return 3
    return 1


def _loss_values_for_evaluation(report: DesignReport, evaluation, operating_request) -> dict[str, float]:
    quantity = _magnetic_quantity(report, operating_request)
    copper = evaluation.copper_loss_w
    core = evaluation.core_loss_w
    total = evaluation.total_loss_w
    values = {
        "per_inductor_copper_loss_w": copper,
        "per_inductor_core_loss_w": core,
        "per_inductor_total_loss_w": total,
        "magnetic_quantity": float(quantity),
        "copper_loss_w": None if copper is None else copper * quantity,
        "core_loss_w": None if core is None else core * quantity,
        "total_loss_w": None if total is None else total * quantity,
    }
    if quantity == 1:
        values["copper_loss_w"] = copper
        values["core_loss_w"] = core
        values["total_loss_w"] = total
    return {key: value for key, value in values.items() if value is not None}


def _candidate_core_loss_audit(designs) -> dict[str, object]:
    records: dict[str, object] = {}
    for design in designs or ():
        metadata = design.metadata if isinstance(design.metadata, dict) else {}
        records[design.candidate_id] = {
            "status": core_loss_status(metadata),
            "core_loss_w": design.reference_core_loss_w,
            "effective_volume_m3": metadata.get("core_effective_volume_m3"),
            "volumetric_loss_w_per_m3": metadata.get("reference_core_loss_density_w_per_m3"),
            "mass_loss_w_per_kg": metadata.get("mass_loss_w_per_kg"),
            "core_mass_kg": metadata.get("core_mass_kg"),
            "identity": {
                "candidate_id": design.candidate_id,
                "core_name": design.core_name,
                "material_name": design.material_name,
                "catalog_core_id": metadata.get("catalog_core_id"),
                "selection_mode": metadata.get("core_selection_mode", "virtual"),
            },
            "consistency": core_loss_consistency(
                core_loss_w=design.reference_core_loss_w,
                volumetric_loss_w_per_m3=metadata.get("reference_core_loss_density_w_per_m3"),
                effective_volume_m3=metadata.get("core_effective_volume_m3"),
                mass_loss_w_per_kg=metadata.get("mass_loss_w_per_kg"),
                core_mass_kg=metadata.get("core_mass_kg"),
            ),
        }
    return records


def _selected_magnetic_design(report: DesignReport):
    if report.magnetic is None:
        return None
    selected_id = report.magnetic.selected_design_id
    if selected_id:
        for design in report.magnetic.chosen_designs:
            if design.candidate_id == selected_id:
                return design
    if report.magnetic.chosen_designs:
        return report.magnetic.chosen_designs[len(report.magnetic.chosen_designs) // 2]
    return None


def _resolve_preferred_design_id(report: DesignReport) -> str | None:
    magnetic_design_id = report.magnetic.selected_design_id if report.magnetic is not None else None
    if magnetic_design_id:
        return magnetic_design_id
    if report.loss is not None:
        return report.loss.recommended_design_id
    return None


def _merge_artifact_paths(existing_paths: list[str], new_paths: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for path in [*existing_paths, *new_paths]:
        normalized = str(Path(path))
        if normalized in seen:
            continue
        merged.append(normalized)
        seen.add(normalized)
    return merged
