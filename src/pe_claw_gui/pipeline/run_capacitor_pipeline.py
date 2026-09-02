"""Capacitor-stage runtime orchestration."""

from __future__ import annotations

from math import pi, sqrt
import time
from dataclasses import replace
from pathlib import Path

from ..engines.capacitors.artifacts import write_capacitor_pareto_artifacts
from ..engines.capacitors.llc_resonant import search_llc_resonant_capacitor_banks
from ..engines.capacitors.selection import evaluate_capacitor_bank
from ..engines.capacitors.selection import select_capacitor_bank
from ..engines.thermal.thermal_estimator import resolve_ambient_temperature_c
from ..libraries.capacitors import list_registered_capacitors
from ..models.capacitor import (
    CapacitorResult,
    CapacitorSideResult,
    CapacitorSizingRequest,
    LlcResonantCapacitorDesignRequest,
)
from ..models.design_report import DesignReport
from ..models.design_run_context import get_run_output_root
from ..models.operating_point import OperatingPoint
from ..topologies.base import TopologyPlugin
from ..topology_capabilities import has_split_dc_link_capacitor_bank
from .run_capacitor_geometry_pipeline import run_capacitor_geometry_pipeline
from .npc_capacitor_design import build_npc_capacitor_design

_SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
_SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID = "single_phase_totem_pole_bridgeless_pfc"
AC_DC_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS = {
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID,
    _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID,
}
INVERTER_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS = {
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
}
LLC_RESONANT_CAPACITOR_TOPOLOGY_IDS = {
    "llc_resonant_converter_diode_rectifier",
    "llc_resonant_converter_synchronous_rectifier",
}


def run_capacitor_pipeline(
    report: DesignReport,
    plugin: TopologyPlugin | None = None,
    output_root: str | Path | None = None,
) -> DesignReport:
    """Attach first-pass registered capacitor selection results to a design report."""

    pipeline_start_s = time.perf_counter()
    notes = [
        "Capacitor stage uses registered capacitor series.",
        "Selection is anchored to the full-load design point: candidate nominal Vin and load_ratio=1.0.",
    ]
    if report.spec.topology_id in LLC_RESONANT_CAPACITOR_TOPOLOGY_IDS:
        notes.extend(
            [
                "LLC capacitor currents use first-pass FHA waveform estimates.",
                "Input capacitor current is estimated from primary bridge instantaneous power.",
                "Output capacitor current is estimated from rectified secondary reflected-load current.",
                "Exact LLC time-domain simulation, rectifier commutation overlap, and harmonic-by-harmonic capacitor loss are not implemented.",
            ]
        )
    if _is_ac_dc_electrolytic_dc_link_topology(report):
        notes.extend(
            [
                "AC-DC rectifier capacitor selection is for the output/DC-link capacitor bank only.",
                "AC-DC rectifier capacitor selection uses aluminum electrolytic candidates from the registered library.",
                "AC-DC input-source current is not reused as an input capacitor current waveform.",
            ]
        )
    if report.spec.topology_id == _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        notes.extend(
            [
                "Boost PFC capacitor selection is for the regulated DC-link capacitor bank only.",
                "Boost PFC DC-link capacitor current uses the sampled line-cycle boost-diode current minus DC load current.",
                "Boost PFC EMI/input-filter capacitors are not selected in this first-pass stage.",
            ]
        )
    if report.spec.topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID:
        notes.extend(
            [
                "Totem-Pole PFC capacitor selection is for the regulated DC-link capacitor bank only.",
                "Totem-Pole PFC DC-link capacitor current uses the sampled full-line-cycle bus current minus DC load current.",
                "Totem-Pole PFC EMI/input-filter capacitors are not selected in this first-pass stage.",
            ]
        )
    if _is_inverter_electrolytic_dc_link_topology(report):
        if _is_split_dc_link_capacitor_topology(report):
            notes.extend(
                [
                    "Three-phase NPC capacitor selection is for the split upper/lower DC-link capacitor banks.",
                    "Upper and lower banks are selected separately from the NPC PWM-level split-link current proxies.",
                    "NPC split-link audit adds equalizing/discharge resistors, bridge-leg film decoupling, midpoint scenarios, life, ripple, surge, and precharge checks.",
                    "Neutral-point closed-loop dynamics, dead-time, Coss, commutation overlap, parasitics, and harmonic-by-harmonic ESR remain outside this first-pass proxy.",
                ]
            )
        elif report.spec.topology_id == "three_phase_two_level_voltage_source_inverter":
            notes.extend(
                [
                    "Three-phase inverter capacitor selection is for the DC-link electrolytic capacitor bank only.",
                    "Three-phase DC-link capacitor selection supports series-parallel electrolytic banks.",
                    "DC-link RMS current uses a first-pass PWM-level switch-state bus-current proxy from the SPWM waveform preview.",
                    "Real PWM bus pulse shape, dead-time, Coss, parasitics, and harmonic-by-harmonic ESR are not modeled.",
                    "Series electrolytic bank voltage balancing and balancing-resistor loss are not included.",
                    "Selected capacitor loss is a selector proxy; detailed inverter capacitor loss validation is pending.",
                ]
            )
        else:
            notes.extend(
                [
                    "Single-phase inverter capacitor selection is for the DC-link electrolytic capacitor bank only.",
                    "TCM high-frequency triangular-current DC-link RMS is included in capacitor Irms/loss proxy when detail data is available.",
                    "Selected capacitor loss is a selector proxy; detailed inverter capacitor loss validation is pending.",
                    "Harmonic-by-harmonic ESR evaluation remains future work.",
                ]
            )
    if _is_flyback_topology(report):
        notes.extend(
            [
                "Flyback output capacitor selection uses secondary rectifier current minus load current.",
                "Flyback input capacitor selection uses primary switch/input-source current ripple at the design point.",
                "Clamp/snubber capacitor selection, leakage ringing, EMI input filter design, and harmonic-by-harmonic ESR remain pending.",
            ]
        )
    if _is_psfb_topology(report):
        notes.extend(
            [
                "PSFB output capacitor selection uses output inductor ripple current minus load current.",
                "PSFB input capacitor selection uses primary bridge/input-source current ripple at the design point.",
                "Bridge commutation, resonant-transition, clamp/snubber, EMI input filter, and harmonic-by-harmonic ESR remain pending.",
            ]
        )
    llc_resonant_request = _build_llc_resonant_capacitor_request(report)
    warnings: list[str] = []
    if llc_resonant_request is not None and llc_resonant_request.warning:
        warnings.append(llc_resonant_request.warning)
    registry_start_s = time.perf_counter()
    candidates = _load_capacitor_candidates(report)
    registry_elapsed_s = time.perf_counter() - registry_start_s
    ambient_temp_c = resolve_ambient_temperature_c(report)
    llc_resonant_search = _run_llc_resonant_capacitor_search(
        llc_resonant_request,
        candidates,
        ambient_temp_c,
        output_root=output_root or get_run_output_root(report),
    )
    if llc_resonant_search is not None:
        warnings.extend(llc_resonant_search.warnings)

    if report.candidate is None:
        result = CapacitorResult(
            llc_resonant_capacitor_request=llc_resonant_request,
            llc_resonant_capacitor_search_result=llc_resonant_search,
            notes=notes,
            warnings=["Capacitor selection did not run because no topology candidate is available."],
        )
        return _attach_llc_cr_design_id(replace(report, capacitor=result))

    waveform_start_s = time.perf_counter()
    design_report = _build_design_point_waveform_report(report, plugin)
    waveform_elapsed_s = time.perf_counter() - waveform_start_s
    if design_report.waveform is None:
        result = CapacitorResult(
            llc_resonant_capacitor_request=llc_resonant_request,
            llc_resonant_capacitor_search_result=llc_resonant_search,
            notes=notes,
            warnings=["Capacitor selection did not run because waveform data is unavailable."],
        )
        return _attach_llc_cr_design_id(replace(report, capacitor=result))

    ripple_ratio_percent = _resolve_ripple_ratio_percent(design_report)
    ambient_temp_c = resolve_ambient_temperature_c(design_report)
    output_selection = _select_output_capacitor(design_report, candidates, ripple_ratio_percent, ambient_temp_c)
    input_selection = _select_input_capacitor(design_report, candidates, ripple_ratio_percent, ambient_temp_c)
    output_dir = _capacitor_output_dir(report, output_root)
    output_selection = write_capacitor_pareto_artifacts(output_selection, output_dir)
    if input_selection is not None and input_selection.request is not None:
        input_selection = write_capacitor_pareto_artifacts(input_selection, output_dir)

    if input_selection is not None:
        warnings.extend(input_selection.warnings)
    if output_selection is not None:
        warnings.extend(output_selection.warnings)
    npc_design = None
    if report.spec.topology_id == "three_phase_three_level_npc_inverter":
        npc_design = build_npc_capacitor_design(
            design_report,
            input_selection,
            output_selection,
            output_dir,
        )
        warnings.extend(npc_design.warnings)
    total_before_geometry_s = time.perf_counter() - pipeline_start_s
    diagnostics = {
        "registered_candidates": len(candidates),
        "registry_loading_time_s": registry_elapsed_s,
        "design_point_waveform_preparation_time_s": waveform_elapsed_s,
        "output_selection_time_s": output_selection.diagnostics.get("selection_time_s", 0.0),
        "input_selection_time_s": input_selection.diagnostics.get("selection_time_s", 0.0) if input_selection is not None else 0.0,
        "output_artifact_csv_time_s": output_selection.diagnostics.get("artifact_csv_time_s", 0.0),
        "output_artifact_png_time_s": output_selection.diagnostics.get("artifact_png_time_s", 0.0),
        "output_artifact_total_time_s": output_selection.diagnostics.get("artifact_total_time_s", 0.0),
        "input_artifact_csv_time_s": input_selection.diagnostics.get("artifact_csv_time_s", 0.0) if input_selection is not None else 0.0,
        "input_artifact_png_time_s": input_selection.diagnostics.get("artifact_png_time_s", 0.0) if input_selection is not None else 0.0,
        "input_artifact_total_time_s": input_selection.diagnostics.get("artifact_total_time_s", 0.0) if input_selection is not None else 0.0,
        "run_capacitor_time_before_geometry_s": total_before_geometry_s,
        "epcos_screw_terminal_electrolytics_enabled": _include_epcos_screw_terminal_electrolytics(report),
    }
    notes.extend(
        [
            f"Capacitor registry loading time: {registry_elapsed_s:.3f} s for {len(candidates)} registered candidates.",
            f"Design-point waveform/capacitor-current preparation time: {waveform_elapsed_s:.3f} s.",
            f"Run Capacitor time before geometry: {total_before_geometry_s:.3f} s.",
        ]
    )
    result = CapacitorResult(
        input_selection=input_selection,
        output_selection=output_selection,
        npc_design=npc_design,
        llc_resonant_capacitor_request=llc_resonant_request,
        llc_resonant_capacitor_search_result=llc_resonant_search,
        notes=notes,
        warnings=_dedupe(warnings),
        artifact_paths=_dedupe([
            *(input_selection.artifact_paths if input_selection is not None else []),
            *output_selection.artifact_paths,
            *(npc_design.artifact_paths if npc_design is not None else []),
            *(_llc_resonant_artifact_paths(llc_resonant_search)),
        ]),
        diagnostics=diagnostics,
    )
    completed = run_capacitor_geometry_pipeline(
        replace(report, capacitor=result),
        output_root=output_root or get_run_output_root(report),
    )
    if completed.capacitor is None:
        return _attach_llc_cr_design_id(completed)
    total_elapsed_s = time.perf_counter() - pipeline_start_s
    capacitor = replace(
        completed.capacitor,
        diagnostics={**completed.capacitor.diagnostics, "total_run_capacitor_time_s": total_elapsed_s},
        notes=[*completed.capacitor.notes, f"Total Run Capacitor time: {total_elapsed_s:.3f} s."],
    )
    completed = replace(completed, capacitor=capacitor)
    completed = _refresh_selected_single_phase_rectifier(completed, plugin)
    completed = _refresh_selected_active_pfc(completed, plugin)
    completed = _refresh_selected_npc_inverter(completed, plugin)
    completed = _refresh_selected_llc(completed, plugin)
    completed = run_capacitor_operating_point_refresh(completed) if completed.waveform is not None else completed
    return _attach_llc_cr_design_id(completed)


def _attach_llc_cr_design_id(report: DesignReport) -> DesignReport:
    """Bind the LLC Cr recommendation to the current run context."""

    context = report.llc_run_context
    search = (
        report.capacitor.llc_resonant_capacitor_search_result
        if report.capacitor is not None
        else None
    )
    recommended = search.recommended_candidate if search is not None else None
    updated_report = report
    if context is not None and recommended is not None:
        updated_report = replace(
            updated_report,
            llc_run_context=context.with_result_ids(cr_design_id=recommended.design_id),
        )
    magnetic = updated_report.magnetic
    if magnetic is None or magnetic.result_type != "separated_llc_transformer":
        return updated_report
    requirements = dict(magnetic.design_requirements or {})
    request = getattr(search, "request", None) if search is not None else None
    coverage = (getattr(search, "coverage_summary", {}) or {}) if search is not None else {}
    requirements.update(
        {
            "cr_target_f": getattr(request, "cr_target_f", requirements.get("cr_target_f")),
            "cr_actual_f": getattr(recommended, "bank_capacitance_f", None),
            "cr_error_percent": getattr(recommended, "capacitance_error_percent", None),
            "cr_error_limit_percent": coverage.get("capacitance_error_limit_percent"),
            "cr_status": (
                "available"
                if recommended is not None
                else "no_feasible_candidate"
                if search is not None and request is not None
                else "not_evaluated"
            ),
            "cr_actual_source": "LLC resonant capacitor recommended candidate",
        }
    )
    field_status = dict(requirements.get("field_status") or {})
    field_status["cr"] = requirements["cr_status"]
    requirements["field_status"] = field_status
    return replace(updated_report, magnetic=replace(magnetic, design_requirements=requirements))


def _refresh_selected_llc(report: DesignReport, plugin: TopologyPlugin | None) -> DesignReport:
    """Refresh the LLC operating point with the selected output capacitor bank."""

    if report.spec.topology_id not in LLC_RESONANT_CAPACITOR_TOPOLOGY_IDS:
        return report
    if plugin is None or report.candidate is None or report.capacitor is None:
        return report
    selection = report.capacitor.output_selection
    selected = selection.recommended if selection is not None else None
    if selected is None:
        return report
    llc_fha = report.candidate.metadata.get("llc_fha", {})
    if not isinstance(llc_fha, dict):
        return report
    fixed_hardware = llc_fha.get("fixed_hardware_snapshot", {})
    reuse_fixed_output_bank = (
        llc_fha.get("hardware_reuse_mode") == "fixed_hardware"
        and isinstance(fixed_hardware, dict)
    )
    selected_capacitance_f = (
        float(fixed_hardware["output_capacitance_f"])
        if reuse_fixed_output_bank
        else float(selected.equivalent_capacitance_f)
    )
    selected_esr_ohm = (
        float(fixed_hardware["output_capacitor_esr_ohm"])
        if reuse_fixed_output_bank
        else float(selected.equivalent_rs_ohm)
    )
    llc_fha = {
        **llc_fha,
        "selected_output_capacitance_f": selected_capacitance_f,
        "selected_output_capacitor_esr_ohm": selected_esr_ohm,
        "selected_output_capacitor_part_number": (
            "fixed_hardware_snapshot"
            if reuse_fixed_output_bank
            else selected.candidate.part_number
        ),
        "selected_output_capacitor_parallel_count": (
            1 if reuse_fixed_output_bank else int(selected.parallel_count)
        ),
        "selected_output_capacitor_series_count": (
            1 if reuse_fixed_output_bank else int(selected.series_count)
        ),
        "selected_output_capacitor_esr_frequency_hz": (
            None if reuse_fixed_output_bank else selected.candidate.esr_frequency_hz
        ),
    }
    candidate = replace(
        report.candidate,
        metadata={**report.candidate.metadata, "llc_fha": llc_fha},
    )
    operating_point = report.operating_point or OperatingPoint(
        vin_v=candidate.vin_nom,
        load_ratio=1.0,
        switching_frequency_hz=float(
            llc_fha.get("commanded_switching_frequency_hz", candidate.fs_hz)
        ),
    )
    waveform = plugin.generate_waveforms(candidate, operating_point=operating_point)
    stress = plugin.extract_stress(candidate, waveform_set=waveform)
    topology_result = plugin.evaluate(candidate, waveform_set=waveform, stress_result=stress)
    waveform_metadata = waveform.metadata.get("llc_fha_waveforms", {}) if waveform is not None else {}
    achieved_vout_v = float(waveform_metadata.get("vout_op_v", candidate.vout_target))
    operating_point = replace(
        operating_point,
        vout_v=achieved_vout_v,
        switching_frequency_hz=float(waveform_metadata.get("fs_op_hz", candidate.fs_hz)),
    )
    return replace(
        report,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform,
        stress=stress,
        topology_result=topology_result,
        notes=[*report.notes, "LLC electrical readback refreshed using the selected output capacitor C and ESR."],
    )


def _refresh_selected_single_phase_rectifier(
    report: DesignReport,
    plugin: TopologyPlugin | None,
) -> DesignReport:
    """Refresh the capacitor-filter rectifier at the selected hardware capacitor."""

    topology_id = report.spec.topology_id
    if topology_id not in {
        "single_phase_diode_bridge_rectifier_capacitor_filter",
        "single_phase_diode_bridge_rectifier_dc_inductor_filter",
        "three_phase_diode_bridge_rectifier_capacitor_filter",
    }:
        return report
    if plugin is None or report.candidate is None or report.capacitor is None:
        return report
    output_selection = report.capacitor.output_selection
    selected = output_selection.recommended if output_selection is not None else None
    if selected is None or selected.equivalent_capacitance_f <= 0.0:
        return report

    load_ratio = report.operating_point.load_ratio if report.operating_point is not None else 1.0
    if topology_id == "single_phase_diode_bridge_rectifier_capacitor_filter":
        from ..topologies.ac_dc.single_phase_diode_bridge_rectifier_capacitor_filter.waveform import (
            refresh_selected_capacitor_candidate,
        )

        candidate, _ = refresh_selected_capacitor_candidate(
            report.candidate,
            float(selected.equivalent_capacitance_f),
            load_ratio=load_ratio,
        )
    elif topology_id == "single_phase_diode_bridge_rectifier_dc_inductor_filter":
        from ..topologies.ac_dc.single_phase_diode_bridge_rectifier_dc_inductor_filter.waveform import (
            refresh_selected_hardware_candidate,
        )

        candidate, _ = refresh_selected_hardware_candidate(
            report.candidate,
            selected_cdc_f=float(selected.equivalent_capacitance_f),
            load_ratio=load_ratio,
        )
    else:
        from ..topologies.ac_dc.three_phase_diode_bridge_rectifier_capacitor_filter.waveform import (
            refresh_selected_capacitor_candidate,
        )

        candidate, _ = refresh_selected_capacitor_candidate(
            report.candidate,
            float(selected.equivalent_capacitance_f),
            load_ratio=load_ratio,
        )
    operating_point = report.operating_point or OperatingPoint(vin_v=candidate.vin_nom, load_ratio=load_ratio)
    waveform = plugin.generate_waveforms(candidate, operating_point=operating_point)
    stress = plugin.extract_stress(candidate, waveform_set=waveform)
    topology_result = plugin.evaluate(candidate, waveform_set=waveform, stress_result=stress)
    metrics_key = {
        "single_phase_diode_bridge_rectifier_capacitor_filter": "pulse_simulation",
        "single_phase_diode_bridge_rectifier_dc_inductor_filter": "state_space_simulation",
        "three_phase_diode_bridge_rectifier_capacitor_filter": "three_phase_pulse_simulation",
    }[topology_id]
    metrics = candidate.metadata.get(metrics_key, {})
    if isinstance(metrics, dict):
        operating_point = replace(
            operating_point,
            vout_v=float(metrics.get("vdc_avg_v", 0.0)) or None,
            power_factor=float(metrics.get("power_factor", 0.0)) or None,
        )
    notes = [
        *report.notes,
        "Passive rectifier operating point refreshed using the selected capacitor bank.",
    ]
    return replace(
        report,
        candidate=candidate,
        operating_point=operating_point,
        waveform=waveform,
        stress=stress,
        topology_result=topology_result,
        notes=notes,
    )


def _refresh_selected_active_pfc(
    report: DesignReport,
    plugin: TopologyPlugin | None,
) -> DesignReport:
    """Refresh active-PFC ripple and currents with the selected DC-link bank."""

    topology_id = report.spec.topology_id
    if topology_id not in {
        _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID,
        _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID,
    }:
        return report
    if plugin is None or report.candidate is None or report.capacitor is None:
        return report
    output_selection = report.capacitor.output_selection
    selected = output_selection.recommended if output_selection is not None else None
    if selected is None or selected.equivalent_capacitance_f <= 0.0:
        return report

    if topology_id == _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        from ..topologies.ac_dc.single_phase_boost_pfc_diode_bridge.waveform import (
            refresh_selected_capacitor_candidate,
        )
    else:
        from ..topologies.ac_dc.single_phase_totem_pole_bridgeless_pfc.waveform import (
            refresh_selected_capacitor_candidate,
        )

    candidate = refresh_selected_capacitor_candidate(
        report.candidate,
        float(selected.equivalent_capacitance_f),
    )
    operating_point = report.operating_point or OperatingPoint(vin_v=candidate.vin_nom, load_ratio=1.0)
    waveform = plugin.generate_waveforms(candidate, operating_point=operating_point)
    stress = plugin.extract_stress(candidate, waveform_set=waveform)
    topology_result = plugin.evaluate(candidate, waveform_set=waveform, stress_result=stress)
    waveform_metadata = waveform.metadata if waveform is not None else {}
    predicted_power_factor = waveform_metadata.get("power_factor")
    operating_point = replace(
        operating_point,
        vout_v=candidate.vout_target,
        power_factor=(
            float(predicted_power_factor)
            if predicted_power_factor is not None
            else operating_point.power_factor
        ),
    )
    topology_label = "Boost PFC" if topology_id == _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID else "Totem-Pole PFC"
    return replace(
        report,
        candidate=candidate,
        waveform=waveform,
        stress=stress,
        topology_result=topology_result,
        operating_point=operating_point,
        notes=[*report.notes, f"{topology_label} electrical readback refreshed using the selected DC-link capacitor bank."],
    )


def _refresh_selected_npc_inverter(
    report: DesignReport,
    plugin: TopologyPlugin | None,
) -> DesignReport:
    """Refresh NPC waveforms with the independently selected split-link banks."""

    if report.spec.topology_id != "three_phase_three_level_npc_inverter":
        return report
    if plugin is None or report.candidate is None or report.capacitor is None:
        return report
    upper_side = report.capacitor.input_selection
    lower_side = report.capacitor.output_selection
    upper = upper_side.recommended if upper_side is not None else None
    lower = lower_side.recommended if lower_side is not None else None
    if upper is None or lower is None:
        return report
    upper_f = float(upper.equivalent_capacitance_f)
    lower_f = float(lower.equivalent_capacitance_f)
    if upper_f <= 0.0 or lower_f <= 0.0:
        return report
    selected_series_equivalent_f = upper_f * lower_f / (upper_f + lower_f)
    candidate = replace(
        report.candidate,
        metadata={
            **report.candidate.metadata,
            "dc_link_upper_selected_capacitance_f": upper_f,
            "dc_link_lower_selected_capacitance_f": lower_f,
            "dc_link_selected_series_equivalent_capacitance_f": selected_series_equivalent_f,
            "dc_link_upper_selected_part_number": upper.candidate.part_number,
            "dc_link_lower_selected_part_number": lower.candidate.part_number,
            "dc_link_upper_selected_parallel_count": upper.parallel_count,
            "dc_link_lower_selected_parallel_count": lower.parallel_count,
            "dc_link_upper_selected_series_count": upper.series_count,
            "dc_link_lower_selected_series_count": lower.series_count,
            "dc_link_selected_capacitance_source": "run_capacitor_recommended_split_banks",
        },
    )
    operating_point = report.operating_point or OperatingPoint(vin_v=candidate.vin_nom, load_ratio=1.0)
    waveform = plugin.generate_waveforms(candidate, operating_point=operating_point)
    stress = plugin.extract_stress(candidate, waveform_set=waveform)
    topology_result = plugin.evaluate(candidate, waveform_set=waveform, stress_result=stress)
    return replace(
        report,
        candidate=candidate,
        waveform=waveform,
        stress=stress,
        topology_result=topology_result,
        notes=[
            *report.notes,
            "NPC electrical readback refreshed using the selected upper and lower split-link capacitor banks.",
        ],
    )


def run_capacitor_operating_point_refresh(report: DesignReport) -> DesignReport:
    """Refresh current operating-point capacitor losses without changing design-point selection or geometry."""

    if report.capacitor is None or report.waveform is None or report.candidate is None:
        return report
    capacitor = report.capacitor
    input_result = _refresh_side_operating_loss(report, capacitor.input_selection)
    output_result = _refresh_side_operating_loss(report, capacitor.output_selection)
    return replace(
        report,
        capacitor=replace(
            capacitor,
            current_operating_input=input_result,
            current_operating_output=output_result,
        ),
    )


def _build_design_point_waveform_report(report: DesignReport, plugin: TopologyPlugin | None) -> DesignReport:
    if report.candidate is None:
        return report
    if plugin is None:
        return report
    operating_point = OperatingPoint(
        vin_v=report.candidate.vin_nom,
        load_ratio=1.0,
        switching_frequency_hz=(
            _operating_switching_frequency_hz(report)
            if report.spec.topology_id in LLC_RESONANT_CAPACITOR_TOPOLOGY_IDS
            else None
        ),
    )
    waveform_set = plugin.generate_waveforms(report.candidate, operating_point=operating_point)
    stress_result = plugin.extract_stress(report.candidate, waveform_set=waveform_set)
    topology_result = plugin.evaluate(report.candidate, waveform_set=waveform_set, stress_result=stress_result)
    return replace(
        report,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
    )


def _select_output_capacitor(report, candidates, ripple_ratio_percent: float, ambient_temp_c: float) -> CapacitorSideResult:
    if _is_split_dc_link_capacitor_topology(report):
        request = _build_split_link_request(report, "lower", ripple_ratio_percent, ambient_temp_c)
    else:
        request = _build_output_request(report, ripple_ratio_percent, ambient_temp_c)
    return select_capacitor_bank(request, candidates)


def _select_input_capacitor(report, candidates, ripple_ratio_percent: float, ambient_temp_c: float) -> CapacitorSideResult | None:
    if _is_split_dc_link_capacitor_topology(report):
        request = _build_split_link_request(report, "upper", ripple_ratio_percent, ambient_temp_c)
        return select_capacitor_bank(request, candidates)
    if _is_electrolytic_dc_link_topology(report):
        return None
    request = _build_input_request(report, ripple_ratio_percent, ambient_temp_c)
    if request is None:
        return CapacitorSideResult(
            notes=["Input capacitor current waveform unavailable for this topology in the first-pass capacitor stage."],
            warnings=["Input capacitor selection skipped because input capacitor current waveform is unavailable."],
        )
    return select_capacitor_bank(request, candidates)


def _build_output_request(report, ripple_ratio_percent: float, ambient_temp_c: float) -> CapacitorSizingRequest:
    waveform = report.waveform
    current_time_s, current_waveform_a, basis = _resolve_output_capacitor_waveform(report)
    return CapacitorSizingRequest(
        side="output",
        dc_voltage_v=_output_dc_voltage_v(report),
        ripple_ratio_percent=ripple_ratio_percent,
        current_time_s=current_time_s,
        current_waveform_a=current_waveform_a,
        voltage_waveform_v=list(waveform.output_voltage_v),
        switching_frequency_hz=_operating_switching_frequency_hz(report),
        ambient_temp_c=ambient_temp_c,
        voltage_margin=_output_voltage_margin(report),
        allowed_capacitor_technologies=_allowed_capacitor_technologies(report),
        include_epcos_screw_terminal_electrolytics=_include_epcos_screw_terminal_electrolytics(report),
        capacitance_min_f=_output_capacitance_min_f(report),
        role="dc_link" if _is_electrolytic_dc_link_topology(report) else "output",
        design_type=_output_design_type(report),
        topology_id=report.spec.topology_id,
        basis=basis,
        min_series_count=2 if report.spec.topology_id == "three_phase_three_level_npc_inverter" else 1,
    )


def _build_input_request(report, ripple_ratio_percent: float, ambient_temp_c: float) -> CapacitorSizingRequest | None:
    waveform = report.waveform
    input_current = _build_input_capacitor_current(report)
    if input_current is None:
        return None
    return CapacitorSizingRequest(
        side="input",
        dc_voltage_v=max(abs(float(waveform.operating_vin_v)), 1e-9),
        ripple_ratio_percent=ripple_ratio_percent,
        current_time_s=list(waveform.time_s),
        current_waveform_a=input_current,
        switching_frequency_hz=float(report.candidate.fs_hz),
        ambient_temp_c=ambient_temp_c,
        allowed_capacitor_technologies=_allowed_capacitor_technologies(report),
        include_epcos_screw_terminal_electrolytics=_include_epcos_screw_terminal_electrolytics(report),
        role="input",
        topology_id=report.spec.topology_id,
    )


def _operating_switching_frequency_hz(report: DesignReport) -> float:
    if report.spec.topology_id in LLC_RESONANT_CAPACITOR_TOPOLOGY_IDS:
        if report.operating_point is not None and report.operating_point.switching_frequency_hz is not None:
            return float(report.operating_point.switching_frequency_hz)
        llc_fha = _llc_fha_metadata(report)
        commanded = llc_fha.get("commanded_switching_frequency_hz")
        if isinstance(commanded, (int, float)) and commanded > 0.0:
            return float(commanded)
    return float(report.candidate.fs_hz)


def _refresh_side_operating_loss(report: DesignReport, design_side: CapacitorSideResult | None) -> CapacitorSideResult | None:
    if design_side is None or design_side.recommended is None:
        return None
    ripple_ratio_percent = _resolve_ripple_ratio_percent(report)
    ambient_temp_c = resolve_ambient_temperature_c(report)
    side = design_side.request.side if design_side.request is not None else ""
    if _is_split_dc_link_capacitor_topology(report):
        request = _build_split_link_request(report, side if side in {"upper", "lower"} else "lower", ripple_ratio_percent, ambient_temp_c)
    else:
        request = (
            _build_output_request(report, ripple_ratio_percent, ambient_temp_c)
            if side == "output"
            else _build_input_request(report, ripple_ratio_percent, ambient_temp_c)
        )
    if request is None:
        return CapacitorSideResult(
            request=design_side.request,
            notes=["Current operating-point capacitor loss refresh skipped because capacitor current waveform is unavailable."],
            warnings=["Current operating-point capacitor loss refresh skipped because capacitor current waveform is unavailable."],
        )
    entry = evaluate_capacitor_bank(
        request,
        design_side.recommended.candidate,
        design_side.recommended.parallel_count,
        series_count=design_side.recommended.series_count,
    )
    entry = replace(entry, representative_label="current operating point", recommended_flag=True)
    return CapacitorSideResult(
        request=request,
        recommended=entry,
        top_candidates=[entry],
        evaluated_count=1,
        feasible_count=1 if entry.feasible else 0,
        notes=["Current operating-point capacitor loss refresh reuses the fixed design-point capacitor bank."],
        warnings=list(entry.rejection_reasons),
    )


def _resolve_output_capacitor_waveform(report: DesignReport) -> tuple[list[float], list[float], str]:
    waveform = report.waveform
    if waveform is None:
        return [], [], "unavailable"
    metadata = waveform.metadata if isinstance(waveform.metadata, dict) else {}
    if report.spec.topology_id == "three_phase_diode_bridge_rectifier_capacitor_filter":
        return (
            list(waveform.time_s),
            list(waveform.capacitor_current_a),
            "Three-phase bridge charging current minus fixed-resistive DC load current",
        )
    if _is_flyback_topology(report):
        return (
            list(waveform.time_s),
            list(waveform.capacitor_current_a),
            "Flyback secondary rectifier current minus output load current, first-pass RMS/ripple basis",
        )
    if _is_psfb_topology(report):
        return (
            list(waveform.time_s),
            list(waveform.capacitor_current_a),
            "PSFB output inductor ripple current minus output load current, first-pass RMS/ripple basis",
        )
    if report.spec.topology_id == _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        return (
            list(waveform.time_s),
            list(waveform.capacitor_current_a),
            "Boost PFC line-cycle DC-link capacitor current from boost diode current minus DC load current",
        )
    if report.spec.topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID:
        return (
            list(waveform.time_s),
            list(waveform.capacitor_current_a),
            "Totem-Pole PFC full-line-cycle DC-link capacitor current from bus current minus DC load current",
        )
    if report.spec.topology_id == "single_phase_full_bridge_inverter":
        detail_time_s = metadata.get("tcm_dc_link_capacitor_current_detail_time_s")
        detail_current_a = metadata.get("tcm_dc_link_capacitor_current_detail_a")
        detail_basis = str(metadata.get("tcm_dc_link_capacitor_current_basis") or "").strip()
        if detail_time_s and detail_current_a:
            return (
                list(detail_time_s),
                list(detail_current_a),
                detail_basis or "TCM detailed instantaneous-power DC-link current, first-pass RMS basis",
            )
    if report.spec.topology_id == "three_phase_two_level_voltage_source_inverter":
        pwm_detail_current_a = metadata.get("dc_link_capacitor_current_pwm_a")
        pwm_detail_lf_current_a = metadata.get("dc_link_capacitor_current_lf_a")
        pwm_basis = str(metadata.get("dc_link_capacitor_current_basis") or "").strip()
        if pwm_detail_current_a:
            return (
                list(waveform.time_s),
                list(pwm_detail_current_a),
                pwm_basis or "three-phase PWM-level switch-state DC-link current proxy, first-pass RMS basis",
            )
        if pwm_detail_lf_current_a:
            return (
                list(waveform.time_s),
                list(pwm_detail_lf_current_a),
                "three-phase low-frequency DC-link current proxy, comparison basis only",
            )
        return (
            list(waveform.time_s),
            list(waveform.capacitor_current_a),
            "three-phase low-frequency DC-link current proxy, comparison basis only",
        )
    return list(waveform.time_s), list(waveform.capacitor_current_a), "low-frequency DC-link capacitor current waveform"


def _build_split_link_request(
    report: DesignReport,
    bank_side: str,
    ripple_ratio_percent: float,
    ambient_temp_c: float,
) -> CapacitorSizingRequest:
    waveform = report.waveform
    current_time_s, current_waveform_a, voltage_waveform_v, basis = _resolve_split_link_capacitor_waveform(report, bank_side)
    voltage_required_v = max((abs(float(value)) for value in voltage_waveform_v), default=0.0)
    if voltage_required_v <= 0.0:
        voltage_required_v = max(abs(float(waveform.operating_vout_v)) * 0.5, 1e-9)
    return CapacitorSizingRequest(
        side=bank_side,
        dc_voltage_v=voltage_required_v,
        ripple_ratio_percent=ripple_ratio_percent,
        current_time_s=current_time_s,
        current_waveform_a=current_waveform_a,
        voltage_waveform_v=voltage_waveform_v,
        switching_frequency_hz=float(report.candidate.fs_hz),
        ambient_temp_c=ambient_temp_c,
        voltage_margin=_output_voltage_margin(report),
        allowed_capacitor_technologies=_allowed_capacitor_technologies(report),
        include_epcos_screw_terminal_electrolytics=_include_epcos_screw_terminal_electrolytics(report),
        capacitance_min_f=_output_capacitance_min_f(report),
        role="dc_link",
        design_type=_output_design_type(report),
        topology_id=report.spec.topology_id,
        basis=basis,
        min_series_count=2,
    )


def _resolve_split_link_capacitor_waveform(
    report: DesignReport,
    bank_side: str,
) -> tuple[list[float], list[float], list[float], str]:
    waveform = report.waveform
    if waveform is None:
        return [], [], [], "unavailable"
    metadata = waveform.metadata if isinstance(waveform.metadata, dict) else {}
    waveforms = metadata.get("three_phase_npc_pd_spwm_waveforms")
    if isinstance(waveforms, dict):
        if bank_side == "upper":
            current_a = list(waveforms.get("upper_dc_link_capacitor_current_pwm_a") or [])
            voltage_v = list(waveforms.get("upper_dc_link_voltage_v") or [])
        else:
            current_a = list(waveforms.get("lower_dc_link_capacitor_current_pwm_a") or [])
            voltage_v = list(waveforms.get("lower_dc_link_voltage_v") or [])
        if current_a and voltage_v:
            return (
                list(waveform.time_s),
                current_a,
                voltage_v,
                "NPC split DC-link PWM-level ripple proxy with neutral-point comparison retained",
            )
    current_key = "upper_dc_link_capacitor_current_pwm_a" if bank_side == "upper" else "lower_dc_link_capacitor_current_pwm_a"
    voltage_key = "upper_dc_link_voltage_v" if bank_side == "upper" else "lower_dc_link_voltage_v"
    current_a = list(metadata.get(current_key) or [])
    voltage_v = list(metadata.get(voltage_key) or [])
    if current_a and voltage_v:
        return (
            list(waveform.time_s),
            current_a,
            voltage_v,
            "NPC split DC-link PWM-level ripple proxy with neutral-point comparison retained",
        )
    return list(waveform.time_s), list(waveform.capacitor_current_a), list(waveform.output_voltage_v), "NPC split DC-link PWM-level ripple proxy with neutral-point comparison retained"


def _build_input_capacitor_current(report) -> list[float] | None:
    waveform = report.waveform
    topology_id = report.spec.topology_id
    if waveform.input_source_current_a:
        return _remove_average(list(waveform.input_source_current_a))
    if topology_id.startswith("buck_") and waveform.switch_current_a:
        return _remove_average(list(waveform.switch_current_a))
    if topology_id.startswith("boost_") and waveform.inductor_current_a:
        return _remove_average(list(waveform.inductor_current_a))
    return None


def _load_capacitor_candidates(report: DesignReport) -> tuple:
    return list_registered_capacitors()


def _is_ac_dc_electrolytic_dc_link_topology(report: DesignReport) -> bool:
    return report.spec.topology_id in AC_DC_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS


def _is_inverter_electrolytic_dc_link_topology(report: DesignReport) -> bool:
    return report.spec.topology_id in INVERTER_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS


def _is_flyback_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == "flyback_diode_rectified_isolated"


def _is_psfb_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == "phase_shifted_full_bridge_diode_rectifier_isolated"


def _is_split_dc_link_capacitor_topology(report: DesignReport) -> bool:
    return has_split_dc_link_capacitor_bank(report.spec.topology_id)


def _is_electrolytic_dc_link_topology(report: DesignReport) -> bool:
    return _is_ac_dc_electrolytic_dc_link_topology(report) or _is_inverter_electrolytic_dc_link_topology(report)


def _output_design_type(report: DesignReport) -> str:
    if report.spec.topology_id == _SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID:
        return "boost_pfc_electrolytic_dc_link"
    if report.spec.topology_id == _SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID:
        return "totem_pole_pfc_electrolytic_dc_link"
    if _is_ac_dc_electrolytic_dc_link_topology(report):
        return "ac_dc_electrolytic_dc_link"
    if _is_inverter_electrolytic_dc_link_topology(report):
        return "inverter_electrolytic_dc_link"
    if _is_flyback_topology(report):
        return "flyback_output_capacitor"
    if _is_psfb_topology(report):
        return "psfb_output_capacitor"
    return ""


def _output_capacitance_min_f(report: DesignReport) -> float:
    if _is_flyback_topology(report) or _is_psfb_topology(report):
        candidate = report.candidate
        return max(float(candidate.capacitance_f), 0.0) if candidate is not None else 0.0
    if not _is_electrolytic_dc_link_topology(report):
        return 0.0
    candidate = report.candidate
    if candidate is None:
        return 0.0
    return max(float(candidate.capacitance_f), 0.0)


def _output_dc_voltage_v(report: DesignReport) -> float:
    if _is_ac_dc_electrolytic_dc_link_topology(report):
        metadata = report.candidate.metadata if report.candidate is not None else {}
        for key in ("capacitor_voltage_requirement_v", "capacitor_voltage_required_v"):
            value = _positive_float(metadata.get(key) if isinstance(metadata, dict) else None, 0.0)
            if value > 0.0:
                return value
    if _is_inverter_electrolytic_dc_link_topology(report):
        candidate = report.candidate
        if candidate is not None:
            vdc_nom_v = abs(float(candidate.vin_nom))
            delta_vdc_pp_v = max(float(candidate.delta_vo), 0.0)
            return max(vdc_nom_v + 0.5 * delta_vdc_pp_v, 1e-9)
    waveform = report.waveform
    return max(abs(float(waveform.operating_vout_v)), 1e-9)


def _output_voltage_margin(report: DesignReport) -> float:
    if _is_ac_dc_electrolytic_dc_link_topology(report):
        metadata = report.candidate.metadata if report.candidate is not None else {}
        if isinstance(metadata, dict):
            for key in ("capacitor_voltage_requirement_v", "capacitor_voltage_required_v"):
                if _positive_float(metadata.get(key), 0.0) > 0.0:
                    return 1.0
    if _is_inverter_electrolytic_dc_link_topology(report):
        return 1.15
    return 1.2


def _include_epcos_screw_terminal_electrolytics(report: DesignReport) -> bool:
    raw_input = report.spec.raw_input or {}
    metadata = report.spec.metadata or {}
    for key in (
        "include_epcos_screw_terminal_electrolytics",
        "include_tdk_epcos_electrolytics",
        "enable_epcos_electrolytics",
    ):
        if _truthy_flag(raw_input.get(key)) or _truthy_flag(metadata.get(key)):
            return True
    technologies = raw_input.get("allowed_capacitor_technologies") or metadata.get("allowed_capacitor_technologies")
    return _contains_aluminum_electrolytic(technologies)


def _allowed_capacitor_technologies(report: DesignReport) -> tuple[str, ...] | None:
    if _is_electrolytic_dc_link_topology(report):
        return ("aluminum_electrolytic",)
    raw_input = report.spec.raw_input or {}
    metadata = report.spec.metadata or {}
    raw_value = raw_input.get("allowed_capacitor_technologies")
    value = raw_value if raw_value is not None else metadata.get("allowed_capacitor_technologies")
    if value is None:
        return None
    if isinstance(value, str):
        values = value.replace(";", ",").replace("|", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    normalized = tuple(str(item).strip() for item in values if str(item).strip())
    return normalized or None


def _truthy_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().casefold() in {"1", "true", "yes", "y", "on", "enable", "enabled"}


def _contains_aluminum_electrolytic(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        values = value.replace(";", ",").replace("|", ",").split(",")
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    return any(_normalize_text(item) == "aluminum_electrolytic" for item in values)


def _normalize_text(value: object) -> str:
    return str(value or "").strip().casefold().replace("-", "_").replace(" ", "_")


def _dedupe_candidates(candidates: tuple) -> tuple:
    deduped = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in seen:
            continue
        seen.add(candidate.part_number)
        deduped.append(candidate)
    return tuple(deduped)


def _remove_average(values: list[float]) -> list[float]:
    if not values:
        return []
    average = sum(values) / len(values)
    return [value - average for value in values]


def _resolve_ripple_ratio_percent(report: DesignReport) -> float:
    raw_input = report.spec.raw_input
    metadata = report.spec.metadata
    if "ripple_voltage_ratio_percent" in raw_input:
        return max(float(raw_input["ripple_voltage_ratio_percent"]), 0.0)
    if "vout_ripple_ratio" in raw_input:
        return max(100.0 * float(raw_input["vout_ripple_ratio"]), 0.0)
    if "vout_ripple_ratio" in metadata:
        return max(100.0 * float(metadata["vout_ripple_ratio"]), 0.0)
    candidate = report.candidate
    if _is_inverter_electrolytic_dc_link_topology(report) and candidate is not None:
        return max(100.0 * candidate.delta_vo / max(abs(candidate.vin_nom), 1e-9), 0.0)
    if candidate is not None and candidate.vout_target:
        return max(100.0 * candidate.delta_vo / max(abs(candidate.vout_target), 1e-9), 0.0)
    return 1.0


def _run_llc_resonant_capacitor_search(
    request,
    candidates,
    ambient_temp_c: float,
    *,
    output_root: str | Path | None = None,
):
    if request is None:
        return None
    return search_llc_resonant_capacitor_banks(
        request,
        candidates,
        output_dir=Path(output_root) / "resonant_capacitor_design"
        if output_root is not None
        else _project_root() / "outputs" / "resonant_capacitor_design",
        ambient_temp_c=ambient_temp_c,
    )


def _llc_resonant_artifact_paths(search) -> list[str]:
    if search is None:
        return []
    return [
        path
        for path in (
            search.feasible_csv_path,
            search.pareto_csv_path,
            search.chosen_csv_path,
            search.pareto_png_path,
            search.near_miss_csv_path,
        )
        if path
    ]


def _build_llc_resonant_capacitor_request(report: DesignReport) -> LlcResonantCapacitorDesignRequest | None:
    if report.spec.topology_id not in LLC_RESONANT_CAPACITOR_TOPOLOGY_IDS:
        return None
    llc_fha = _llc_fha_metadata(report)
    if not llc_fha:
        return None
    warnings: list[str] = []
    notes = [
        "Resonant capacitor voltage rating uses full-load lowest-frequency FHA stress with first-pass margin.",
        "Status: resonant capacitor candidate search pending.",
    ]
    cr_target_f = _positive_float(llc_fha.get("cr_f"), 0.0)
    lr_target_h = _positive_float(llc_fha.get("lr_h"), 0.0)
    transformer_lk_h, external_lr_actual_h, lr_total_actual_h, lr_warning = _llc_lr_actuals(report, lr_target_h)
    if lr_warning:
        warnings.append(lr_warning)
    current_rms_a, current_peak_a, current_basis, current_warning = _llc_resonant_current_basis(llc_fha)
    if current_warning:
        warnings.append(current_warning)
    voltage_rms_v, voltage_peak_v, fs_basis_hz, voltage_basis, voltage_warning = _llc_voltage_stress_basis(llc_fha, cr_target_f)
    if voltage_warning:
        warnings.append(voltage_warning)
    voltage_margin_factor = 1.2
    is_design_required = cr_target_f > 0.0
    if not is_design_required:
        warnings.append("Invalid or missing Cr target; resonant capacitor design is not available.")
    return LlcResonantCapacitorDesignRequest(
        cr_target_f=cr_target_f,
        cr_target_nF=cr_target_f * 1e9,
        lr_target_h=lr_target_h,
        lr_total_actual_h=lr_total_actual_h,
        transformer_lk_h=transformer_lk_h,
        external_lr_actual_h=external_lr_actual_h,
        current_rms_a=current_rms_a,
        current_peak_a=current_peak_a,
        current_basis=current_basis,
        voltage_rms_v=voltage_rms_v,
        voltage_peak_v=voltage_peak_v,
        voltage_basis=voltage_basis,
        voltage_rating_basis="peak resonant capacitor voltage stress",
        voltage_margin_factor=voltage_margin_factor,
        required_voltage_rating_v=voltage_margin_factor * voltage_peak_v,
        fs_basis_hz=fs_basis_hz,
        fs_min_hz=_positive_float(llc_fha.get("fs_min_hz"), 0.0),
        fs_max_hz=_positive_float(llc_fha.get("fs_max_hz"), 0.0),
        frequency_basis=f"full-load lowest-frequency FHA corner at {fs_basis_hz:.6g} Hz" if fs_basis_hz > 0.0 else "",
        is_design_required=is_design_required,
        warning=" ".join(_dedupe(warnings)),
        notes=notes,
    )


def _llc_lr_actuals(report: DesignReport, lr_target_h: float) -> tuple[float, float, float, str]:
    search_result = (
        report.magnetic.llc_external_resonant_inductor_search_result
        if report.magnetic is not None
        else None
    )
    recommended = search_result.recommended_candidate if search_result is not None else None
    if recommended is not None and recommended.total_lr_actual_h > 0.0:
        return (
            float(recommended.transformer_lk_h),
            float(recommended.actual_l_h),
            float(recommended.total_lr_actual_h),
            "",
        )
    target = (
        report.magnetic.llc_external_resonant_inductor_target
        if report.magnetic is not None
        else None
    )
    transformer_lk_h = float(target.transformer_lk_h) if target is not None else 0.0
    return (
        transformer_lk_h,
        max(lr_target_h - transformer_lk_h, 0.0) if transformer_lk_h > 0.0 else 0.0,
        lr_target_h,
        "External Lr actual is unavailable; resonant capacitor request uses FHA Lr target.",
    )


def _llc_resonant_current_basis(llc_fha: dict[str, object]) -> tuple[float, float, str, str]:
    corner_estimates = [
        estimate
        for estimate in llc_fha.get("current_estimates_by_corner", [])
        if isinstance(estimate, dict)
        and isinstance(estimate.get("ir_rms_a"), (int, float))
        and isinstance(estimate.get("ir_peak_a"), (int, float))
    ]
    if corner_estimates:
        selected = max(corner_estimates, key=lambda row: (float(row["ir_rms_a"]), float(row["ir_peak_a"])))
        corner_name = str(selected.get("corner_name", "-"))
        return (
            float(selected["ir_rms_a"]),
            float(selected["ir_peak_a"]),
            f"worst_case_fha_corner: {corner_name}",
            "",
        )
    nominal = llc_fha.get("current_estimates_nominal_full_load", {})
    if isinstance(nominal, dict) and isinstance(nominal.get("ir_rms_a"), (int, float)) and isinstance(nominal.get("ir_peak_a"), (int, float)):
        return (
            float(nominal["ir_rms_a"]),
            float(nominal["ir_peak_a"]),
            "nominal_full_load_fha_current",
            "Using nominal full-load FHA resonant current because corner current metadata is unavailable.",
        )
    fallback_current_a = _positive_float(llc_fha.get("pout_max_w"), 0.0) / max(_positive_float(llc_fha.get("vout_nom_v"), 1.0), 1e-12)
    return (
        fallback_current_a,
        sqrt(2.0) * fallback_current_a,
        "fallback_output_current_used_as_last_resort",
        "Using output current as last-resort Cr current basis because FHA resonant tank current metadata is unavailable.",
    )


def _llc_voltage_stress_basis(llc_fha: dict[str, object], cr_target_f: float) -> tuple[float, float, float, str, str]:
    corner = _select_full_load_lowest_frequency_corner(llc_fha)
    if corner is None:
        fs_basis_hz = _positive_float(llc_fha.get("fs_min_hz"), _positive_float(llc_fha.get("fr_hz"), 0.0))
        corner_name = "unavailable"
        current_peak_a = 0.0
    else:
        fs_basis_hz = _positive_float(corner.get("fs_hz"), _positive_float(llc_fha.get("fs_min_hz"), 0.0))
        corner_name = str(corner.get("corner_name", corner.get("label", "-")))
        current_peak_a = _positive_float(corner.get("ir_peak_a"), 0.0)
    voltage_basis = f"full_load_lowest_frequency_fha_corner: {corner_name}"
    peak_direct = _positive_float(corner.get("vcr_peak_v") if corner is not None else None, 0.0)
    rms_direct = _positive_float(corner.get("vcr_rms_v") if corner is not None else None, 0.0)
    if peak_direct > 0.0:
        return rms_direct if rms_direct > 0.0 else peak_direct / sqrt(2.0), peak_direct, fs_basis_hz, voltage_basis, ""
    if current_peak_a > 0.0 and fs_basis_hz > 0.0 and cr_target_f > 0.0:
        peak_v = current_peak_a / (2.0 * pi * fs_basis_hz * cr_target_f)
        return (
            peak_v / sqrt(2.0),
            peak_v,
            fs_basis_hz,
            voltage_basis,
            "Cr voltage stress is estimated from sinusoidal FHA current and Cr; detailed time-domain capacitor voltage is not implemented.",
        )
    return 0.0, 0.0, fs_basis_hz, voltage_basis, "Cr voltage stress could not be resolved from FHA metadata."


def _select_full_load_lowest_frequency_corner(llc_fha: dict[str, object]) -> dict[str, object] | None:
    corners = [
        corner
        for corner in llc_fha.get("current_estimates_by_corner", [])
        if isinstance(corner, dict)
        and isinstance(corner.get("fs_hz"), (int, float))
        and _is_full_load_corner(corner, llc_fha)
    ]
    if not corners:
        corners = [
            corner
            for corner in llc_fha.get("coverage_results", [])
            if isinstance(corner, dict)
            and isinstance(corner.get("fs_hz"), (int, float))
            and _is_full_load_corner(corner, llc_fha)
        ]
    return min(corners, key=lambda row: float(row["fs_hz"])) if corners else None


def _is_full_load_corner(corner: dict[str, object], llc_fha: dict[str, object]) -> bool:
    pout_max_w = _positive_float(llc_fha.get("pout_max_w"), 0.0)
    if pout_max_w <= 0.0:
        return "Pout_max" in str(corner.get("corner_name", corner.get("label", "")))
    return abs(_positive_float(corner.get("pout_w"), 0.0) - pout_max_w) <= max(1e-9, 1e-6 * pout_max_w)


def _llc_fha_metadata(report: DesignReport) -> dict[str, object]:
    candidate = report.candidate
    if candidate is None or not isinstance(getattr(candidate, "metadata", None), dict):
        return {}
    llc_fha = candidate.metadata.get("llc_fha", {})
    return llc_fha if isinstance(llc_fha, dict) else {}


def _positive_float(value: object, fallback: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return fallback
    return result if result > 0.0 else fallback


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _capacitor_output_dir(report: DesignReport, output_root: str | Path | None) -> Path:
    if output_root is not None:
        return Path(output_root) / "capacitor_design"
    run_root = get_run_output_root(report)
    if run_root is not None:
        return run_root / "capacitor_design"
    return _project_root() / "outputs" / "capacitor_design"
