"""Fixed-hardware efficiency sweep orchestration."""

from __future__ import annotations

import hashlib
import json
import math
import csv
from dataclasses import asdict, replace
from pathlib import Path
from collections.abc import Sequence

from matplotlib.figure import Figure

from ..engines.devices.bridge_rectifier_selector import estimate_bridge_rectifier_loss
from ..engines.devices.inverter_segmented_loss import build_inverter_line_cycle_segments
from ..libraries.magnetics.sendust_steinmetz import (
    estimate_sendust_core_loss_mw_per_cm3,
    get_sendust_steinmetz_material,
)
from ..models.design_report import DesignReport
from ..models.design_run_context import get_run_context, get_run_output_dir
from ..models.efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult
from ..models.llc_run_context import is_llc_topology
from ..models.operating_point import OperatingPoint
from ..models.waveform import WaveformSet
from ..topologies.base import TopologyPlugin
from .options import PipelineOptions
from .run_bridge_rectifier_pipeline import (
    SUPPORTED_BRIDGE_RECTIFIER_TOPOLOGIES,
    build_bridge_rectifier_selection_request,
)
from .run_capacitor_pipeline import run_capacitor_operating_point_refresh
from .run_device_pipeline import run_device_operating_point_refresh
from ..engines.devices.loss_aggregation import active_scheme, semiconductor_losses_total_w
from .run_loss_pipeline import run_loss_pipeline
from .run_thermal_pipeline import run_thermal_pipeline

DEFAULT_LOAD_POINTS: tuple[float, ...] = tuple(round(index / 20.0, 2) for index in range(1, 21))
DEFAULT_INVERTER_PF_POINTS: tuple[float, ...] = tuple(round(index / 10.0, 1) for index in range(-10, 11) if index != 0)
SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID = "single_phase_totem_pole_bridgeless_pfc"
def run_efficiency_sweep(
    report: DesignReport,
    plugin: TopologyPlugin | None = None,
    load_points: Sequence[float] | None = None,
    output_dir: str | Path | None = None,
) -> EfficiencySweepResult:
    """Evaluate efficiency over load using the existing selected hardware."""

    load_grid = _normalize_load_grid(load_points)
    warnings: list[str] = []
    signature = _build_signature(report, load_grid)
    run_context = get_run_context(report)
    llc_validation = _validate_llc_efficiency_dependencies(report)
    if llc_validation is not None:
        output_root = _resolve_efficiency_output_dir(report, output_dir)
        result = EfficiencySweepResult(
            load_grid=load_grid,
            warnings=(llc_validation,),
            signature=signature,
            status="blocked",
            run_id=getattr(run_context, "run_id", None),
            topology_id=report.spec.topology_id,
            input_sha256=getattr(run_context, "input_sha256", None),
            source_ids=_llc_source_ids(report),
            fixed_parameters=_llc_fixed_parameters(report),
            blocked_reason=llc_validation,
        )
        return _write_blocked_llc_result(result, output_root)
    if _can_reuse_sweep_result(
        report.efficiency_sweep,
        signature,
        _resolve_efficiency_output_dir(report, output_dir),
    ):
        return report.efficiency_sweep

    blocking_warning = _blocking_warning(report, plugin)
    if blocking_warning is not None:
        return EfficiencySweepResult(load_grid=load_grid, warnings=(blocking_warning,), signature=signature)

    if report.capacitor is None:
        warnings.append("Capacitor design has not been run; capacitor loss is omitted.")
    if _is_single_phase_pfc_topology(report):
        if report.magnetic is None or not _has_selected_magnetic_design(report):
            warnings.append("PFC magnetic design has not been run; boost-inductor loss is omitted.")
    elif _is_ac_dc_bridge_topology(report):
        if _is_ac_dc_reactor_topology(report) and _selected_ac_dc_reactor_candidate(report) is None:
            warnings.append("AC-DC reactor magnetic design has not been run; magnetic loss is omitted.")
    elif not is_llc_topology(report.spec.topology_id) and (
        report.magnetic is None or not report.magnetic.chosen_designs
    ):
        warnings.append("Magnetic design has not been run; magnetic loss is omitted.")

    points: list[EfficiencySweepPoint] = []
    for load_pu in load_grid:
        point, point_warnings = _evaluate_sweep_load_point(report, plugin, load_pu)
        points.append(point)
        warnings.extend(point_warnings)

    result = _build_result(points, load_grid, warnings, signature, report)
    if is_llc_topology(report.spec.topology_id) and not _all_points_complete(points):
        reason = "LLC efficiency sweep blocked: one or more load points did not produce complete efficiency results."
        result = replace(
            result,
            status="blocked",
            blocked_reason=reason,
            warnings=tuple(_dedupe([*result.warnings, reason])),
            run_id=getattr(run_context, "run_id", None),
            topology_id=report.spec.topology_id,
            input_sha256=getattr(run_context, "input_sha256", None),
            source_ids=_llc_source_ids(report),
            fixed_parameters=_llc_fixed_parameters(report),
        )
        return _write_blocked_llc_result(result, _resolve_efficiency_output_dir(report, output_dir))
    artifacts = _write_artifacts(result, _resolve_efficiency_output_dir(report, output_dir))
    pf_sweep_points: tuple[dict[str, object], ...] = ()
    pf_sweep_artifacts: dict[str, str] = {}
    if _is_single_phase_inverter_topology(report):
        pf_sweep_points, pf_sweep_artifacts, pf_warnings = _build_inverter_pf_sweep(report, plugin, _resolve_efficiency_output_dir(report, output_dir))
        warnings.extend(pf_warnings)
        result = _build_result(points, load_grid, warnings, signature, report)
    elif _is_three_phase_two_level_inverter_topology(report) or _is_three_phase_npc_inverter_topology(report):
        pf_sweep_points, pf_sweep_artifacts, pf_warnings = _build_inverter_pf_sweep(
            report,
            plugin,
            _resolve_efficiency_output_dir(report, output_dir),
            zvs_mode="not_applicable_npc" if _is_three_phase_npc_inverter_topology(report) else "not_applicable",
        )
        warnings.extend(pf_warnings)
        result = _build_result(points, load_grid, warnings, signature, report)
    return replace(
        result,
        artifact_paths=artifacts,
        pf_sweep_points=pf_sweep_points,
        pf_sweep_artifact_paths=pf_sweep_artifacts,
        run_id=getattr(run_context, "run_id", None),
        topology_id=report.spec.topology_id,
        input_sha256=getattr(run_context, "input_sha256", None),
        source_ids=_llc_source_ids(report),
        fixed_parameters=_llc_fixed_parameters(report),
    )


def _validate_llc_efficiency_dependencies(report: DesignReport) -> str | None:
    """Reject LLC efficiency sweeps that are not tied to complete current-run hardware."""

    if not is_llc_topology(report.spec.topology_id):
        return None
    context = report.llc_run_context
    if context is None:
        return "LLC efficiency sweep blocked: current run context is unavailable."
    if report.candidate is None:
        return "LLC efficiency sweep blocked: current electrical design is unavailable."
    for stage in ("design", "magnetics", "capacitors"):
        if context.stage_status.get(stage) != "succeeded":
            return f"LLC efficiency sweep blocked: stage {stage} is not succeeded."
    device = report.device
    if device is None or not device.recommended_scheme_id or not device.selected_devices:
        return "LLC efficiency sweep blocked: current semiconductor recommendation is incomplete."
    if context.device_design_id != device.recommended_scheme_id:
        return "LLC efficiency sweep blocked: semiconductor recommendation ID does not match the current run."
    magnetic = report.magnetic
    contract = getattr(magnetic, "llc_magnetic_contract", None) if magnetic is not None else None
    if contract is None:
        return "LLC efficiency sweep blocked: current magnetic combination contract is unavailable."
    if contract.run_id != context.run_id or contract.topology_id != report.spec.topology_id:
        return "LLC efficiency sweep blocked: magnetic contract does not match the current run."
    if context.transformer_design_id != contract.transformer_design_id:
        return "LLC efficiency sweep blocked: transformer ID does not match the current run contract."
    if context.external_lr_design_id != contract.external_lr_design_id:
        return "LLC efficiency sweep blocked: external Lr ID does not match the current run contract."
    transformer_search = getattr(magnetic, "llc_transformer_result", None)
    transformer_candidates = []
    if transformer_search is not None:
        transformer_candidates = list(getattr(transformer_search, "feasible_candidates", []) or [])
        if not transformer_candidates:
            transformer_candidates = list(getattr(transformer_search, "candidates", []) or [])
    if not any(getattr(candidate, "candidate_id", None) == contract.transformer_design_id for candidate in transformer_candidates):
        return "LLC efficiency sweep blocked: current transformer candidate is not in the run result set."
    external_search = getattr(magnetic, "llc_external_resonant_inductor_search_result", None)
    external_candidates = getattr(external_search, "candidates", []) if external_search is not None else []
    if contract.external_lr_design_id is not None and not any(
        getattr(candidate, "design_id", None) == contract.external_lr_design_id for candidate in external_candidates
    ):
        return "LLC efficiency sweep blocked: current external Lr candidate is not in the run result set."
    capacitor = report.capacitor
    cr_search = getattr(capacitor, "llc_resonant_capacitor_search_result", None) if capacitor is not None else None
    cr_candidate = getattr(cr_search, "recommended_candidate", None) if cr_search is not None else None
    if cr_candidate is None:
        return "LLC efficiency sweep blocked: current LLC Cr recommendation is unavailable."
    if context.cr_design_id != cr_candidate.design_id:
        return "LLC efficiency sweep blocked: LLC Cr recommendation ID does not match the current run."
    return None


def _all_points_complete(points: Sequence[EfficiencySweepPoint]) -> bool:
    return bool(points) and all(point.efficiency is not None and point.total_loss_w is not None for point in points)


def _llc_source_ids(report: DesignReport) -> dict[str, str | None]:
    context = report.llc_run_context
    contract = getattr(report.magnetic, "llc_magnetic_contract", None) if report.magnetic is not None else None
    return {
        "transformer_design_id": getattr(contract, "transformer_design_id", None),
        "external_lr_design_id": getattr(contract, "external_lr_design_id", None),
        "combined_magnetic_design_id": getattr(contract, "combined_magnetic_design_id", None),
        "cr_design_id": getattr(context, "cr_design_id", None),
        "device_design_id": getattr(context, "device_design_id", None),
    }


def _llc_fixed_parameters(report: DesignReport) -> dict[str, object]:
    contract = getattr(report.magnetic, "llc_magnetic_contract", None) if report.magnetic is not None else None
    cr_search = getattr(report.capacitor, "llc_resonant_capacitor_search_result", None) if report.capacitor is not None else None
    cr = getattr(cr_search, "recommended_candidate", None) if cr_search is not None else None
    return {
        "fs_hz": getattr(contract, "fs_hz", None) or getattr(report.candidate, "fs_hz", None),
        "lm_target_h": getattr(contract, "lm_target_h", None),
        "lm_actual_h": getattr(contract, "lm_actual_h", None),
        "total_lr_target_h": getattr(contract, "total_lr_target_h", None),
        "total_lr_actual_h": getattr(contract, "total_lr_actual_h", None),
        "cr_target_f": getattr(cr, "cr_target_f", None),
        "cr_actual_f": getattr(cr, "bank_capacitance_f", None),
        "cr_error_percent": getattr(cr, "capacitance_error_percent", None),
    }


def _resolve_efficiency_output_dir(report: DesignReport, output_dir: str | Path | None) -> Path:
    if output_dir is not None:
        return Path(output_dir)
    run_dir = get_run_output_dir(report, "efficiency_sweep")
    if run_dir is not None:
        return run_dir
    return _project_root() / "outputs" / "efficiency_sweep"


def _write_blocked_llc_result(result: EfficiencySweepResult, output_dir: Path) -> EfficiencySweepResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("efficiency_curve.png", "loss_breakdown_stacked.png", "semiconductor_loss_vs_pf.png", "efficiency_vs_pf.png", "zvs_segments_vs_pf.png"):
        path = output_dir / name
        if path.exists():
            path.unlink()
    path = output_dir / "efficiency_sweep_result.json"
    path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True, default=str), encoding="utf-8")
    return replace(result, artifact_paths={"diagnostic_json": str(path)})


def _evaluate_sweep_load_point(
    report: DesignReport,
    plugin: TopologyPlugin,
    load_pu: float,
) -> tuple[EfficiencySweepPoint, list[str]]:
    """Isolate one failed operating point so the remaining sweep can finish."""

    try:
        if _is_single_phase_boost_pfc_topology(report):
            return _evaluate_single_phase_boost_pfc_load_point(report, plugin, load_pu)
        if _is_single_phase_totem_pole_pfc_topology(report):
            return _evaluate_single_phase_totem_pole_pfc_load_point(report, plugin, load_pu)
        if _is_ac_dc_bridge_topology(report):
            return _evaluate_ac_dc_load_point(report, plugin, load_pu)
        return _evaluate_load_point(report, plugin, load_pu)
    except Exception as exc:
        warning = (
            f"Efficiency sweep failed at {load_pu:.1f} p.u.: "
            f"{type(exc).__name__}: {exc}"
        )
        return (
            EfficiencySweepPoint(
                load_pu=load_pu,
                output_power_w=0.0,
                total_loss_w=None,
                efficiency=None,
                semiconductor_loss_w=None,
                magnetic_loss_w=None,
                capacitor_loss_w=None,
                other_loss_w=None,
                warnings=(warning,),
            ),
            [warning],
        )


def _evaluate_load_point(
    base_report: DesignReport,
    plugin: TopologyPlugin,
    load_pu: float,
) -> tuple[EfficiencySweepPoint, list[str]]:
    point_warnings: list[str] = []
    operating_point = _sweep_operating_point(base_report, load_pu)
    if operating_point.power_factor is not None and abs(float(operating_point.power_factor)) < 0.05:
        warning = "Efficiency point omitted because |PF| < 0.05 is outside the meaningful loss/efficiency calculation boundary."
        return (
            EfficiencySweepPoint(
                load_pu=load_pu,
                output_power_w=0.0,
                total_loss_w=None,
                efficiency=None,
                semiconductor_loss_w=None,
                magnetic_loss_w=None,
                capacitor_loss_w=None,
                other_loss_w=None,
                warnings=(warning,),
            ),
            [warning],
        )
    waveform_set = plugin.generate_waveforms(base_report.candidate, operating_point=operating_point)
    if waveform_set is None:
        warning = f"Waveform generation returned no data at {load_pu:.1f} p.u.; point omitted."
        return (
            EfficiencySweepPoint(
                load_pu=load_pu,
                output_power_w=0.0,
                total_loss_w=None,
                efficiency=None,
                semiconductor_loss_w=None,
                magnetic_loss_w=None,
                capacitor_loss_w=None,
                other_loss_w=None,
                warnings=(warning,),
            ),
            [warning],
        )
    low_slope_warning = _tcm_low_slope_warning(waveform_set, load_pu=load_pu)
    if low_slope_warning:
        point_warnings.append(low_slope_warning)

    stress_result = plugin.extract_stress(base_report.candidate, waveform_set=waveform_set)
    topology_result = plugin.evaluate(base_report.candidate, waveform_set=waveform_set, stress_result=stress_result)
    refreshed = replace(
        base_report,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
    )
    refreshed = run_device_operating_point_refresh(refreshed, plugin=plugin)
    if refreshed.magnetic is not None and refreshed.magnetic.chosen_designs:
        magnetic_options = PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=refreshed.capacitor is not None)
        refreshed = run_loss_pipeline(
            refreshed,
            preserve_selected_design_id=True,
            refresh_plot_artifact=False,
            pipeline_options=magnetic_options,
        )
        refreshed = run_thermal_pipeline(refreshed, pipeline_options=magnetic_options)
    refreshed = run_capacitor_operating_point_refresh(refreshed)

    semiconductor_loss_w = _semiconductor_loss_w(refreshed)
    magnetic_loss_w = _magnetic_loss_w(refreshed)
    capacitor_loss_w = _capacitor_loss_w(refreshed)
    other_loss_w = _auxiliary_loss_w(refreshed)
    available_losses = [semiconductor_loss_w, magnetic_loss_w, capacitor_loss_w, other_loss_w]
    total_loss_w = sum(loss for loss in available_losses if loss is not None)
    if not any(loss is not None for loss in available_losses):
        total_loss_w = None
        point_warnings.append(f"No loss components were available at {load_pu:.1f} p.u.")

    output_power_w, power_warning = _output_power_w(refreshed, load_pu)
    if power_warning:
        point_warnings.append(power_warning)
    efficiency = None
    if total_loss_w is not None and output_power_w > 0.0:
        efficiency = output_power_w / (output_power_w + total_loss_w)

    return (
        EfficiencySweepPoint(
            load_pu=load_pu,
            output_power_w=output_power_w,
            total_loss_w=total_loss_w,
            efficiency=efficiency,
            semiconductor_loss_w=semiconductor_loss_w,
            magnetic_loss_w=magnetic_loss_w,
            capacitor_loss_w=capacitor_loss_w,
            other_loss_w=other_loss_w,
            loss_breakdown_w=_loss_breakdown(
                semiconductor=semiconductor_loss_w,
                magnetic=magnetic_loss_w,
                capacitor=capacitor_loss_w,
                other=other_loss_w,
            ),
            warnings=tuple(point_warnings),
        ),
        point_warnings,
    )


def _blocking_warning(report: DesignReport, plugin: TopologyPlugin | None) -> str | None:
    if report is None or report.candidate is None:
        return "Run Design before running Efficiency Sweep."
    if plugin is None:
        return "Efficiency sweep requires the active topology plugin."
    return efficiency_sweep_blocking_warning(report)


def efficiency_sweep_blocking_warning(report: DesignReport | None) -> str | None:
    """Return the shared hardware prerequisite warning for an efficiency sweep."""

    if report is None or report.candidate is None:
        return "Run Design before running Efficiency Sweep."
    if _is_single_phase_boost_pfc_topology(report):
        return _boost_pfc_fixed_hardware_warning(report)
    if _is_single_phase_totem_pole_pfc_topology(report):
        return _totem_pole_pfc_fixed_hardware_warning(report)
    if _is_ac_dc_bridge_topology(report):
        bridge = report.bridge_rectifier
        if bridge is None or bridge.selected_candidate is None:
            return "Efficiency sweep requires selected AC-DC bridge rectifier hardware from Run Design."
        if _is_ac_dc_reactor_topology(report) and _selected_ac_dc_reactor_candidate(report) is None:
            return "Efficiency sweep requires selected AC-DC reactor hardware from Run Magnetics."
        return None
    device = report.device
    if device is None or (not device.selected_devices and not device.design_point_losses and not device.scheme_results):
        return "Efficiency sweep requires selected semiconductor hardware from Run Design."
    return None


def _boost_pfc_fixed_hardware_warning(report: DesignReport) -> str | None:
    bridge = report.bridge_rectifier
    if bridge is None or bridge.selected_candidate is None:
        return "Boost PFC efficiency sweep requires selected input bridge-rectifier hardware from Run Design."
    device = report.device
    if device is None or not {"main_switch", "rectifier_diode"}.issubset(set(device.selected_devices)):
        return "Boost PFC efficiency sweep requires selected boost switch and independent boost diode hardware."
    capacitor = report.capacitor
    if capacitor is None or capacitor.output_selection is None or capacitor.output_selection.recommended is None:
        return "Boost PFC efficiency sweep requires selected DC-link capacitor hardware from Run Capacitor."
    if report.magnetic is None or not _has_selected_magnetic_design(report):
        return "Boost PFC efficiency sweep requires selected boost-inductor hardware from Run Magnetics."
    return None


def _totem_pole_pfc_fixed_hardware_warning(report: DesignReport) -> str | None:
    device = report.device
    if device is None or not {"totem_pole_hf_switch", "totem_pole_lf_switch"}.issubset(set(device.selected_devices)):
        return "Totem-Pole PFC efficiency sweep requires selected HF and LF switch hardware."
    capacitor = report.capacitor
    if capacitor is None or capacitor.output_selection is None or capacitor.output_selection.recommended is None:
        return "Totem-Pole PFC efficiency sweep requires selected DC-link capacitor hardware from Run Capacitor."
    if report.magnetic is None or not _has_selected_magnetic_design(report):
        return "Totem-Pole PFC efficiency sweep requires selected boost-inductor hardware from Run Magnetics."
    return None


def _evaluate_single_phase_boost_pfc_load_point(
    base_report: DesignReport,
    plugin: TopologyPlugin,
    load_pu: float,
) -> tuple[EfficiencySweepPoint, list[str]]:
    point_warnings: list[str] = []
    operating_point = _sweep_operating_point(base_report, load_pu)
    waveform_set = plugin.generate_waveforms(base_report.candidate, operating_point=operating_point)
    if waveform_set is None:
        warning = f"Boost PFC waveform generation returned no data at {load_pu:.1f} p.u.; point omitted."
        return (
            EfficiencySweepPoint(
                load_pu=load_pu,
                output_power_w=0.0,
                total_loss_w=None,
                efficiency=None,
                semiconductor_loss_w=None,
                magnetic_loss_w=None,
                capacitor_loss_w=None,
                other_loss_w=None,
                warnings=(warning,),
            ),
            [warning],
        )

    stress_result = plugin.extract_stress(base_report.candidate, waveform_set=waveform_set)
    topology_result = plugin.evaluate(base_report.candidate, waveform_set=waveform_set, stress_result=stress_result)
    refreshed = replace(
        base_report,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
    )
    refreshed = run_device_operating_point_refresh(refreshed, plugin=plugin)
    magnetic_options = PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=refreshed.capacitor is not None)
    refreshed = run_loss_pipeline(
        refreshed,
        preserve_selected_design_id=True,
        refresh_plot_artifact=False,
        pipeline_options=magnetic_options,
    )
    refreshed = run_thermal_pipeline(refreshed, pipeline_options=magnetic_options)
    refreshed = run_capacitor_operating_point_refresh(refreshed)

    semiconductor_loss_w = _semiconductor_loss_w(refreshed)
    if semiconductor_loss_w is None:
        point_warnings.append(f"Selected boost switch/diode loss was unavailable at {load_pu:.1f} p.u.")
    bridge_loss_w = _ac_dc_bridge_loss_w(refreshed, load_pu)
    if bridge_loss_w is None:
        point_warnings.append(f"Selected input bridge loss was unavailable at {load_pu:.1f} p.u.")
    magnetic_loss_w = _magnetic_loss_w(refreshed)
    if magnetic_loss_w is None:
        point_warnings.append(f"Selected boost-inductor loss was unavailable at {load_pu:.1f} p.u.")
    capacitor_loss_w = _capacitor_loss_w(refreshed)
    if capacitor_loss_w is None:
        point_warnings.append(f"Selected DC-link capacitor loss was unavailable at {load_pu:.1f} p.u.")

    available_losses = [semiconductor_loss_w, bridge_loss_w, magnetic_loss_w, capacitor_loss_w]
    total_loss_w = sum(loss for loss in available_losses if loss is not None)
    if not any(loss is not None for loss in available_losses):
        total_loss_w = None
        point_warnings.append(f"No Boost PFC loss components were available at {load_pu:.1f} p.u.")

    output_power_w, power_warning = _output_power_w(refreshed, load_pu)
    if power_warning:
        point_warnings.append(power_warning)
    efficiency = None
    if total_loss_w is not None and output_power_w > 0.0:
        efficiency = output_power_w / (output_power_w + total_loss_w)

    return (
        EfficiencySweepPoint(
            load_pu=load_pu,
            output_power_w=output_power_w,
            total_loss_w=total_loss_w,
            efficiency=efficiency,
            semiconductor_loss_w=semiconductor_loss_w,
            magnetic_loss_w=magnetic_loss_w,
            capacitor_loss_w=capacitor_loss_w,
            other_loss_w=None,
            bridge_rectifier_loss_w=bridge_loss_w,
            loss_breakdown_w=_loss_breakdown(
                semiconductor=semiconductor_loss_w,
                bridge_rectifier=bridge_loss_w,
                magnetic=magnetic_loss_w,
                capacitor=capacitor_loss_w,
            ),
            warnings=tuple(point_warnings),
        ),
        point_warnings,
    )


def _evaluate_single_phase_totem_pole_pfc_load_point(
    base_report: DesignReport,
    plugin: TopologyPlugin,
    load_pu: float,
) -> tuple[EfficiencySweepPoint, list[str]]:
    point, point_warnings = _evaluate_load_point(base_report, plugin, load_pu)
    if point.semiconductor_loss_w is None:
        point_warnings.append(f"Selected Totem-Pole HF/LF switch loss was unavailable at {load_pu:.1f} p.u.")
    if point.magnetic_loss_w is None:
        point_warnings.append(f"Selected Totem-Pole boost-inductor loss was unavailable at {load_pu:.1f} p.u.")
    if point.capacitor_loss_w is None:
        point_warnings.append(f"Selected Totem-Pole DC-link capacitor loss was unavailable at {load_pu:.1f} p.u.")
    if point_warnings:
        point = replace(point, warnings=tuple(point_warnings))
    return point, point_warnings


def _evaluate_ac_dc_load_point(
    base_report: DesignReport,
    plugin: TopologyPlugin,
    load_pu: float,
) -> tuple[EfficiencySweepPoint, list[str]]:
    point_warnings: list[str] = []
    operating_point = _sweep_operating_point(base_report, load_pu)
    waveform_set = plugin.generate_waveforms(base_report.candidate, operating_point=operating_point)
    if waveform_set is None:
        warning = f"AC-DC waveform generation returned no data at {load_pu:.1f} p.u.; point omitted."
        return (
            EfficiencySweepPoint(
                load_pu=load_pu,
                output_power_w=0.0,
                total_loss_w=None,
                efficiency=None,
                semiconductor_loss_w=None,
                magnetic_loss_w=None,
                capacitor_loss_w=None,
                other_loss_w=None,
                warnings=(warning,),
            ),
            [warning],
        )

    waveform_set = _prepare_ac_dc_sweep_waveform(base_report, waveform_set, load_pu)
    stress_result = plugin.extract_stress(base_report.candidate, waveform_set=waveform_set)
    topology_result = plugin.evaluate(base_report.candidate, waveform_set=waveform_set, stress_result=stress_result)
    refreshed = replace(
        base_report,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
    )
    bridge_loss_w = _ac_dc_bridge_loss_w(refreshed, load_pu)
    if bridge_loss_w is None:
        point_warnings.append(f"Selected bridge loss was unavailable at {load_pu:.1f} p.u.")
    magnetic_loss_w = _ac_dc_reactor_loss_w(refreshed)
    if _is_ac_dc_reactor_topology(base_report) and magnetic_loss_w is None:
        point_warnings.append(f"Selected AC-DC reactor loss was unavailable at {load_pu:.1f} p.u.")
    refreshed = run_capacitor_operating_point_refresh(refreshed)
    capacitor_loss_w = _capacitor_loss_w(refreshed)
    if base_report.capacitor is not None and capacitor_loss_w is None:
        point_warnings.append(f"Selected DC-link capacitor loss was unavailable at {load_pu:.1f} p.u.")

    available_losses = [bridge_loss_w, magnetic_loss_w, capacitor_loss_w]
    total_loss_w = sum(loss for loss in available_losses if loss is not None)
    if not any(loss is not None for loss in available_losses):
        total_loss_w = None
        point_warnings.append(f"No AC-DC loss components were available at {load_pu:.1f} p.u.")

    output_power_w, power_warning = _output_power_w(refreshed, load_pu)
    if power_warning:
        point_warnings.append(power_warning)
    efficiency = None
    if total_loss_w is not None and output_power_w > 0.0:
        efficiency = output_power_w / (output_power_w + total_loss_w)

    return (
        EfficiencySweepPoint(
            load_pu=load_pu,
            output_power_w=output_power_w,
            total_loss_w=total_loss_w,
            efficiency=efficiency,
            semiconductor_loss_w=None,
            magnetic_loss_w=magnetic_loss_w,
            capacitor_loss_w=capacitor_loss_w,
            other_loss_w=None,
            bridge_rectifier_loss_w=bridge_loss_w,
            loss_breakdown_w=_loss_breakdown(
                bridge_rectifier=bridge_loss_w,
                magnetic=magnetic_loss_w,
                capacitor=capacitor_loss_w,
            ),
            warnings=tuple(point_warnings),
        ),
        point_warnings,
    )


def _normalize_load_grid(load_points: Sequence[float] | None) -> tuple[float, ...]:
    values = load_points if load_points is not None else DEFAULT_LOAD_POINTS
    normalized = tuple(round(float(value), 6) for value in values)
    if not normalized:
        raise ValueError("Efficiency sweep load grid must contain at least one point.")
    return normalized


def _operating_vin_v(report: DesignReport) -> float:
    if report.operating_point is not None:
        return float(report.operating_point.vin_v)
    if report.candidate is not None:
        return float(report.candidate.vin_nom)
    return float(report.spec.vin_min)


def _sweep_operating_point(report: DesignReport, load_pu: float) -> OperatingPoint:
    power_factor = None
    if report.operating_point is not None and report.operating_point.power_factor is not None:
        power_factor = report.operating_point.power_factor
    return OperatingPoint(vin_v=_operating_vin_v(report), load_ratio=load_pu, power_factor=power_factor)


def _output_power_w(report: DesignReport, load_pu: float) -> tuple[float, str | None]:
    if report.waveform is not None:
        try:
            active_power_w = abs(float(report.waveform.metadata.get("operating_active_power_w")))
            if active_power_w > 0.0:
                return active_power_w, None
        except (TypeError, ValueError):
            pass
    if report.waveform is not None and report.candidate is not None:
        try:
            power_w = abs(float(report.waveform.operating_vout_v) * float(report.candidate.iout) * float(report.waveform.load_ratio))
            if power_w > 0.0:
                return power_w, None
        except (AttributeError, TypeError, ValueError):
            pass
    design_power_w = _design_power_w(report)
    if design_power_w is None:
        return 0.0, f"Output power unavailable at {load_pu:.1f} p.u.; efficiency omitted."
    return max(float(design_power_w) * load_pu, 0.0), (
        f"Used load_pu * design output power fallback at {load_pu:.1f} p.u."
    )


def _prepare_ac_dc_sweep_waveform(
    report: DesignReport,
    waveform_set: WaveformSet,
    load_pu: float,
) -> WaveformSet:
    if _is_three_phase_ac_dc_bridge_topology(report):
        return _scale_three_phase_ac_dc_waveform(report, waveform_set, load_pu)
    return replace(waveform_set, load_ratio=load_pu)


def _scale_three_phase_ac_dc_waveform(
    report: DesignReport,
    waveform_set: WaveformSet,
    load_pu: float,
) -> WaveformSet:
    """Scale the current-only ideal six-pulse preview for fixed-hardware load sweep."""

    if report.candidate is None:
        return waveform_set
    design_idc_a = _positive_float(report.candidate.metadata.get("idc_a"), report.candidate.iout)
    operating_power_w = max(float(report.candidate.pout_target) * max(load_pu, 0.0), 0.0)
    vout_v = max(float(waveform_set.operating_vout_v or report.candidate.vout_target), 1.0e-12)
    operating_idc_a = operating_power_w / vout_v
    scale = operating_idc_a / max(design_idc_a, 1.0e-12)

    def scale_values(values: Sequence[float]) -> list[float]:
        return [float(value) * scale for value in values]

    metadata = dict(waveform_set.metadata)
    metrics = dict(metadata.get("ac_dc_three_phase_rectifier_metrics") or {})
    if metrics:
        metrics.update(
            {
                "idc_a": operating_idc_a,
                "pout_operating_w": operating_power_w,
                "load_ratio": load_pu,
                "dc_link_capacitor_current_rms_a": _rms(scale_values(waveform_set.capacitor_current_a)),
                "line_current_rms_a": _rms(scale_values(waveform_set.input_source_current_a)),
                "per_diode_avg_current_a": operating_idc_a / 3.0,
                "per_diode_rms_current_a": operating_idc_a / math.sqrt(3.0),
                "per_diode_peak_current_a": operating_idc_a,
                "current_model": "scaled six-step continuous-DC-current approximation for efficiency sweep",
            }
        )
        metadata["ac_dc_three_phase_rectifier_metrics"] = metrics
    metadata["load_ratio"] = load_pu
    return replace(
        waveform_set,
        inductor_current_a=scale_values(waveform_set.inductor_current_a),
        capacitor_current_a=scale_values(waveform_set.capacitor_current_a),
        diode_current_a=scale_values(waveform_set.diode_current_a),
        input_source_current_a=scale_values(waveform_set.input_source_current_a),
        load_ratio=load_pu,
        metadata=metadata,
    )


def _ac_dc_bridge_loss_w(report: DesignReport, load_pu: float) -> float | None:
    bridge = report.bridge_rectifier
    if bridge is None or bridge.selected_candidate is None:
        return None
    request = bridge.request
    request = _adjust_ac_dc_bridge_request_for_load(report, request, load_pu)
    return estimate_bridge_rectifier_loss(bridge.selected_candidate, request).total_loss_w


def _adjust_ac_dc_bridge_request_for_load(report, request, load_pu: float):
    if _is_three_phase_ac_dc_bridge_topology(report):
        output_power_w, _ = _output_power_w(report, load_pu)
        dc_output_current_a = output_power_w / max(request.dc_bus_voltage_v, 1.0e-12)
        return replace(
            request,
            output_power_w=output_power_w,
            dc_output_current_a=dc_output_current_a,
            bridge_current_avg_a=dc_output_current_a,
            bridge_current_rms_a=dc_output_current_a,
            bridge_current_waveform_a=tuple(report.waveform.diode_current_a if report.waveform is not None else ()),
        )
    return request


def _ac_dc_reactor_loss_w(report: DesignReport) -> float | None:
    selected = _selected_ac_dc_reactor_candidate(report)
    if selected is None or report.waveform is None:
        return None
    metrics = _ac_dc_reactor_metrics(report.waveform)
    if not metrics:
        return None
    i_rms_a = _positive_float(metrics.get("il_rms_a"), _rms(report.waveform.inductor_current_a))
    delta_i_pp_a = _positive_float(metrics.get("il_ripple_pp_a"), _waveform_pp(report.waveform.inductor_current_a))
    if i_rms_a <= 0.0:
        return None

    parallel = max(int(selected.parallel_core_count or 1), 1)
    per_core_i_rms_a = i_rms_a / parallel
    rdc_25c_ohm = selected.rdc_25c_ohm
    if rdc_25c_ohm is None or rdc_25c_ohm <= 0.0:
        design_i_rms_a = _positive_float(
            getattr(report.magnetic.ac_dc_reactor_result.request, "i_rms_a", None)
            if report.magnetic is not None and report.magnetic.ac_dc_reactor_result is not None
            else None,
            i_rms_a,
        )
        return (selected.total_loss_w or 0.0) * (i_rms_a / max(design_i_rms_a, 1.0e-12)) ** 2.0

    temperature_factor = _positive_float(selected.metadata.get("copper_temperature_factor"), 1.25)
    copper_loss_w = parallel * per_core_i_rms_a * per_core_i_rms_a * rdc_25c_ohm * temperature_factor

    per_core_delta_i_pp_a = delta_i_pp_a / parallel
    ae_m2 = max(selected.ae_cm2 * 1.0e-4, 1.0e-18)
    turns = max(int(selected.turns or selected.per_core_turns or 1), 1)
    per_core_effective_l_h = selected.per_core_effective_inductance_h or selected.effective_inductance_h * parallel
    delta_b_t = per_core_effective_l_h * per_core_delta_i_pp_a / max(turns * ae_m2, 1.0e-18)
    material = get_sendust_steinmetz_material(selected.material_id)
    ripple_frequency_hz = _positive_float(
        metrics.get("ripple_frequency_hz"),
        report.candidate.fs_hz if report.candidate is not None else 100.0,
    )
    core_loss_density_mw_per_cm3 = estimate_sendust_core_loss_mw_per_cm3(
        material,
        frequency_hz=ripple_frequency_hz,
        delta_b_t=delta_b_t,
    )
    core_loss_w = parallel * core_loss_density_mw_per_cm3 * selected.ve_cm3 / 1000.0
    return copper_loss_w + core_loss_w


def _design_power_w(report: DesignReport) -> float | None:
    if report.candidate is not None:
        return getattr(report.candidate, "pout_target", None)
    return report.spec.pout


def _semiconductor_loss_w(report: DesignReport) -> float | None:
    device = report.device
    if device is None:
        return None
    if device.current_operating_losses:
        return semiconductor_losses_total_w(device, device.current_operating_losses)
    scheme = active_scheme(device)
    if scheme is not None:
        return scheme.total_scheme_loss_w
    if device.design_point_losses:
        return semiconductor_losses_total_w(device, device.design_point_losses)
    return None


def _auxiliary_loss_w(report: DesignReport) -> float | None:
    """Return explicitly entered non-semiconductor auxiliary losses."""

    if not _is_three_phase_npc_inverter_topology(report):
        return 0.0
    metadata = report.spec.metadata if isinstance(report.spec.metadata, dict) else {}
    try:
        value = float(metadata.get("npc_auxiliary_loss_w", 0.0))
    except (TypeError, ValueError):
        return 0.0
    return max(value, 0.0)


def _magnetic_loss_w(report: DesignReport) -> float | None:
    if report.loss is None:
        return None
    return report.loss.total_loss_w


def _capacitor_loss_w(report: DesignReport) -> float | None:
    if report.capacitor is None:
        return None
    total = 0.0
    found = False
    for side_result in (report.capacitor.current_operating_input, report.capacitor.current_operating_output):
        if side_result is not None and side_result.recommended is not None:
            total += side_result.recommended.p_total_w
            found = True
    return total if found else None


def _loss_breakdown(**components: float | None) -> dict[str, float | None]:
    """Return named loss components while omitting unavailable values."""

    return {name: value for name, value in components.items() if value is not None}


def _build_result(
    points: list[EfficiencySweepPoint],
    load_grid: tuple[float, ...],
    warnings: list[str],
    signature: str,
    report: DesignReport,
) -> EfficiencySweepResult:
    complete_points = [point for point in points if point.efficiency is not None]
    peak = max(complete_points, key=lambda point: point.efficiency or 0.0) if complete_points else None
    return EfficiencySweepResult(
        points=tuple(points),
        load_grid=load_grid,
        peak_efficiency=peak.efficiency if peak is not None else None,
        peak_efficiency_load_pu=peak.load_pu if peak is not None else None,
        full_load_efficiency=_efficiency_at(points, 1.0),
        light_load_efficiency=_efficiency_at(points, 0.1),
        sweep_basis=_sweep_basis(report, load_grid, points),
        warnings=tuple(_dedupe(warnings)),
        signature=signature,
    )


def _sweep_basis(report: DesignReport, load_grid: tuple[float, ...], points: list[EfficiencySweepPoint]) -> dict[str, object]:
    full_load = _point_at(points, 1.0)
    included_losses = []
    if full_load is None:
        full_load = points[-1] if points else None
    if full_load is not None:
        loss_labels = _loss_labels(report)
        if full_load.semiconductor_loss_w is not None:
            included_losses.append(loss_labels["semiconductor"])
        if full_load.bridge_rectifier_loss_w is not None:
            included_losses.append(loss_labels["bridge_rectifier"])
        if full_load.magnetic_loss_w is not None:
            included_losses.append(loss_labels["magnetic"])
        if full_load.capacitor_loss_w is not None:
            included_losses.append(loss_labels["capacitor"])
        if full_load.other_loss_w is not None and full_load.other_loss_w > 0.0:
            included_losses.append(loss_labels["other"])
    return {
        "load_grid": tuple(load_grid),
        "operating_power_factor": _operating_power_factor_for_report(report),
        "fixed_hardware": _fixed_hardware_label(report),
        "included_losses": tuple(included_losses),
        "loss_breakdown": dict(full_load.loss_breakdown_w) if full_load is not None else {},
        "loss_labels": _loss_labels(report),
        "pf_sweep_mode": (
            "three_phase_npc_first_pass"
            if _is_three_phase_npc_inverter_topology(report)
            else "three_phase_first_pass"
            if _is_three_phase_two_level_inverter_topology(report)
            else "single_phase_first_pass"
            if _is_single_phase_inverter_topology(report)
            else "not_applicable"
        ),
        "pf_sweep_current_basis": (
            "phase current RMS from line-line voltage"
            if _is_three_phase_two_level_inverter_topology(report) or _is_three_phase_npc_inverter_topology(report)
            else "single-phase output current RMS"
            if _is_single_phase_inverter_topology(report)
            else "not_applicable"
        ),
    }


def _point_at(points: Sequence[EfficiencySweepPoint], load_pu: float) -> EfficiencySweepPoint | None:
    for point in points:
        if abs(point.load_pu - load_pu) < 1.0e-9:
            return point
    return None


def _operating_power_factor_for_report(report: DesignReport) -> float | None:
    if report.operating_point is not None and report.operating_point.power_factor is not None:
        return float(report.operating_point.power_factor)
    if report.candidate is not None:
        try:
            return float(report.candidate.metadata.get("power_factor"))
        except (TypeError, ValueError):
            return None
    return None


def _fixed_hardware_label(report: DesignReport) -> str:
    if _is_single_phase_inverter_topology(report):
        return "selected inverter switches, output inductor, and DC-link capacitor bank"
    if _is_three_phase_two_level_inverter_topology(report):
        return "selected six-switch inverter bridge, 3x per-phase output inductors, and DC-link capacitor bank"
    if _is_three_phase_npc_inverter_topology(report):
        return "selected NPC outer/inner switches, clamp diodes, 3x per-phase output inductors, and upper/lower split-link capacitor banks"
    if _is_single_phase_boost_pfc_topology(report):
        return "selected input bridge rectifier, boost switch/diode, boost inductor, and DC-link capacitor bank"
    if _is_single_phase_totem_pole_pfc_topology(report):
        return "selected Totem-Pole HF/LF switches, boost inductor, and DC-link capacitor bank"
    if _is_ac_dc_bridge_topology(report):
        return "selected bridge rectifier and available passive hardware"
    return "selected semiconductor, magnetic, and capacitor hardware"


def _loss_labels(report: DesignReport) -> dict[str, str]:
    labels = {
        "semiconductor": "semiconductor",
        "bridge_rectifier": "bridge rectifier",
        "magnetic": "magnetic",
        "capacitor": "capacitor",
        "other": "other",
    }
    if _is_single_phase_boost_pfc_topology(report):
        labels.update(
            semiconductor="boost switch / diode",
            bridge_rectifier="input bridge rectifier",
            magnetic="boost inductor",
            capacitor="DC-link capacitor",
        )
    elif _is_single_phase_totem_pole_pfc_topology(report):
        labels.update(
            semiconductor="Totem-Pole HF / LF switches",
            magnetic="boost inductor",
            capacitor="DC-link capacitor",
        )
    elif _is_ac_dc_bridge_topology(report):
        labels.update(
            magnetic="AC-DC reactor" if _is_ac_dc_reactor_topology(report) else "magnetic",
            capacitor="DC-link capacitor",
        )
    elif _is_single_phase_inverter_topology(report):
        labels.update(magnetic="output inductor", capacitor="DC-link capacitor")
    return labels


def _efficiency_at(points: list[EfficiencySweepPoint], load_pu: float) -> float | None:
    for point in points:
        if abs(point.load_pu - load_pu) < 1.0e-9:
            return point.efficiency
    return None


def _write_artifacts(result: EfficiencySweepResult, output_dir: str | Path | None) -> dict[str, str]:
    directory = Path(output_dir) if output_dir is not None else _project_root() / "outputs" / "efficiency_sweep"
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "efficiency_sweep.csv"
    efficiency_path = directory / "efficiency_curve.png"
    loss_path = directory / "loss_breakdown_stacked.png"
    _write_sweep_csv(result, csv_path)
    _write_efficiency_curve(result, efficiency_path)
    _write_loss_breakdown(result, loss_path)
    return {
        "csv": str(csv_path),
        "efficiency_curve": str(efficiency_path),
        "loss_breakdown_stacked": str(loss_path),
    }


def _write_sweep_csv(result: EfficiencySweepResult, path: Path) -> None:
    """Persist the load-point efficiency data as a stable audit artifact."""

    fieldnames = (
        "load_pu",
        "output_power_w",
        "total_loss_w",
        "efficiency",
        "semiconductor_loss_w",
        "magnetic_loss_w",
        "capacitor_loss_w",
        "other_loss_w",
        "bridge_rectifier_loss_w",
        "loss_breakdown_w",
        "warnings",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for point in result.points:
            writer.writerow(
                {
                    "load_pu": point.load_pu,
                    "output_power_w": point.output_power_w,
                    "total_loss_w": point.total_loss_w,
                    "efficiency": point.efficiency,
                    "semiconductor_loss_w": point.semiconductor_loss_w,
                    "magnetic_loss_w": point.magnetic_loss_w,
                    "capacitor_loss_w": point.capacitor_loss_w,
                    "other_loss_w": point.other_loss_w,
                    "bridge_rectifier_loss_w": point.bridge_rectifier_loss_w,
                    "loss_breakdown_w": json.dumps(point.loss_breakdown_w, sort_keys=True),
                    "warnings": " | ".join(point.warnings),
                }
            )


def _build_inverter_pf_sweep(
    report: DesignReport,
    plugin: TopologyPlugin,
    output_dir: str | Path | None,
    *,
    zvs_mode: str = "diagnostic",
) -> tuple[tuple[dict[str, object], ...], dict[str, str], list[str]]:
    if report.device is None or report.candidate is None:
        return (), {}, ["PF sweep requires selected inverter switch hardware."]
    fixed_load = _pf_sweep_load_pu(report)
    points: list[dict[str, object]] = []
    warnings: list[str] = []
    for pf in DEFAULT_INVERTER_PF_POINTS:
        operating_point = OperatingPoint(vin_v=_operating_vin_v(report), load_ratio=fixed_load, power_factor=pf)
        pf_report = replace(report, operating_point=operating_point)
        point, point_warnings = _evaluate_load_point(pf_report, plugin, fixed_load)
        warnings.extend(point_warnings)
        if zvs_mode == "diagnostic":
            try:
                segments = build_inverter_line_cycle_segments(report, operating_point=operating_point)
                zvs_count = sum(1 for segment in segments if segment.zvs_turn_on)
                low_slope_segment_count = sum(1 for segment in segments if segment.low_slope_fsw_violation)
            except (TypeError, ValueError):
                segments = ()
                zvs_count = None
                low_slope_segment_count = None
        else:
            segments = ()
            zvs_count = None
            low_slope_segment_count = None
        i_rms_a, i_peak_a = _inverter_current_metrics(report, fixed_load, pf)
        min_segment_fsw_hz = min((segment.fsw_hz for segment in segments), default=None)
        min_natural_segment_fsw_hz = min((segment.natural_fsw_hz for segment in segments), default=None)
        points.append(
            {
                "power_factor": pf,
                "fixed_load_pu": fixed_load,
                "output_power_sign": -1 if pf < 0.0 else 1,
                "semiconductor_loss_w": point.semiconductor_loss_w,
                "zvs_segment_count": zvs_count,
                "efficiency": point.efficiency,
                "current_rms_a": i_rms_a,
                "current_peak_a": i_peak_a,
                "segment_count": len(segments) if segments else None,
                "min_segment_fsw_hz": min_segment_fsw_hz,
                "min_natural_segment_fsw_hz": min_natural_segment_fsw_hz,
                "low_slope_segment_count": low_slope_segment_count,
                "low_slope_segment_fraction": (
                    low_slope_segment_count / len(segments)
                    if low_slope_segment_count is not None and segments
                    else None
                ),
            }
        )
    artifacts = _write_pf_sweep_artifacts(points, output_dir, zvs_mode=zvs_mode) if points else {}
    return tuple(points), artifacts, _dedupe(warnings)


def _pf_sweep_load_pu(report: DesignReport) -> float:
    if report.operating_point is not None:
        try:
            return max(float(report.operating_point.load_ratio), 0.0)
        except (TypeError, ValueError):
            pass
    return 1.0


def _inverter_current_metrics(report: DesignReport, load_pu: float, power_factor: float) -> tuple[float | None, float | None]:
    if report.candidate is None:
        return None, None
    try:
        pout_w = float(report.candidate.metadata.get("pout_w") or report.candidate.pout_target)
        pf_abs = max(abs(float(power_factor)), 1.0e-6)
        if _is_three_phase_two_level_inverter_topology(report) or _is_three_phase_npc_inverter_topology(report):
            vac_ll_rms_v = float(report.candidate.metadata.get("vac_ll_rms_v") or report.candidate.vout_target)
            denominator = math.sqrt(3.0) * vac_ll_rms_v * pf_abs
        else:
            vac_rms_v = float(report.candidate.metadata.get("vac_rms_v") or report.candidate.vout_target)
            denominator = vac_rms_v * pf_abs
        i_rms_a = max(load_pu, 0.0) * pout_w / max(denominator, 1.0e-12)
    except (TypeError, ValueError):
        return None, None
    return i_rms_a, math.sqrt(2.0) * i_rms_a


def _write_pf_sweep_artifacts(
    points: Sequence[dict[str, object]],
    output_dir: str | Path | None,
    *,
    zvs_mode: str = "diagnostic",
) -> dict[str, str]:
    directory = Path(output_dir) if output_dir is not None else _project_root() / "outputs" / "efficiency_sweep"
    directory.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "semiconductor_loss_vs_pf": directory / "semiconductor_loss_vs_pf.png",
        "efficiency_vs_pf": directory / "efficiency_vs_pf.png",
    }
    stale_zvs_path = directory / "zvs_segments_vs_pf.png"
    if zvs_mode == "diagnostic":
        artifacts["zvs_segments_vs_pf"] = stale_zvs_path
    elif stale_zvs_path.exists():
        stale_zvs_path.unlink()
    _write_pf_line_plot(
        points,
        artifacts["semiconductor_loss_vs_pf"],
        y_key="semiconductor_loss_w",
        y_label="Semiconductor loss [W]",
        color="#4c78a8",
    )
    if zvs_mode == "diagnostic":
        _write_pf_line_plot(
            points,
            artifacts["zvs_segments_vs_pf"],
            y_key="zvs_segment_count",
            y_label="ZVS segments / line cycle",
            color="#f58518",
        )
    _write_pf_line_plot(
        points,
        artifacts["efficiency_vs_pf"],
        y_key="efficiency",
        y_label="Efficiency [%]",
        color="#54a24b",
        scale=100.0,
    )
    return {key: str(path) for key, path in artifacts.items()}


def _write_placeholder_plot(path: Path, *, title: str, message: str) -> None:
    figure = Figure(figsize=(5.8, 3.2), dpi=120)
    axis = figure.add_subplot(111)
    axis.set_title(title)
    axis.text(0.5, 0.5, message, ha="center", va="center", wrap=True, fontsize=11)
    axis.set_axis_off()
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()


def _tcm_low_slope_warning(waveform_set: WaveformSet, *, load_pu: float) -> str | None:
    metadata = waveform_set.metadata
    if not metadata.get("tcm_low_slope_region_detected"):
        return None
    try:
        min_fsw_hz = float(metadata.get("tcm_low_slope_min_fsw_hz"))
        limit_hz = float(metadata.get("tcm_low_slope_fsw_min_limit_hz"))
        fraction = float(metadata.get("tcm_low_slope_violation_fraction"))
    except (TypeError, ValueError):
        return (
            f"TCM low-slope guard active at {load_pu:.3g} p.u.; reconstructed fsw falls below the requested minimum. "
            "Mixed-mode fallback clamps fsw to the requested minimum."
        )
    return (
        f"TCM low-slope guard active at {load_pu:.3g} p.u.: min reconstructed fsw {min_fsw_hz:.6g} Hz "
        f"is below requested {limit_hz:.6g} Hz over {100.0 * fraction:.3g}% of reconstructed cycles; "
        "mixed-mode fallback clamps fsw to the requested minimum."
    )


def _write_pf_line_plot(
    points: Sequence[dict[str, object]],
    path: Path,
    *,
    y_key: str,
    y_label: str,
    color: str,
    scale: float = 1.0,
) -> None:
    figure = Figure(figsize=(5.8, 3.2), dpi=120)
    axis = figure.add_subplot(111)
    filtered = [
        (float(point["power_factor"]), float(point[y_key]) * scale)
        for point in points
        if point.get(y_key) is not None
    ]
    x_values = [item[0] for item in filtered]
    y_values = [item[1] for item in filtered]
    axis.plot(x_values, y_values, marker="o", color=color)
    axis.set_xlabel("Power factor")
    axis.set_ylabel(y_label)
    axis.grid(True, alpha=0.3)
    axis.set_xlim(-1.05, 1.05)
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()


def _write_efficiency_curve(result: EfficiencySweepResult, path: Path) -> None:
    figure = Figure(figsize=(5.8, 3.2), dpi=120)
    axis = figure.add_subplot(111)
    x_values = [point.load_pu for point in result.points if point.efficiency is not None]
    y_values = [100.0 * (point.efficiency or 0.0) for point in result.points if point.efficiency is not None]
    axis.plot(x_values, y_values, marker="o", color="#1f77b4")
    axis.set_xlabel("Load [p.u.]")
    axis.set_ylabel("Efficiency [%]")
    axis.grid(True, alpha=0.3)
    if x_values:
        axis.set_xlim(min(x_values) - 0.03, max(x_values) + 0.03)
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()


def _write_loss_breakdown(result: EfficiencySweepResult, path: Path) -> None:
    figure = Figure(figsize=(5.8, 3.2), dpi=120)
    axis = figure.add_subplot(111)
    valid_points = [point for point in result.points if point.total_loss_w is not None]
    x_values = [point.load_pu for point in valid_points]
    loss_labels = result.sweep_basis.get("loss_labels") or {}
    component_specs = (
        (str(loss_labels.get("semiconductor") or "Semiconductor"), "semiconductor_loss_w", "#4c78a8"),
        (str(loss_labels.get("bridge_rectifier") or "Bridge rectifier"), "bridge_rectifier_loss_w", "#e45756"),
        (str(loss_labels.get("magnetic") or "Magnetic"), "magnetic_loss_w", "#f58518"),
        (str(loss_labels.get("capacitor") or "Capacitor"), "capacitor_loss_w", "#54a24b"),
        (str(loss_labels.get("other") or "Other"), "other_loss_w", "#b279a2"),
    )
    components = tuple(
        (label, [getattr(point, attr) or 0.0 for point in valid_points], color)
        for label, attr, color in component_specs
        if any(getattr(point, attr) is not None for point in valid_points)
    )
    bottoms = [0.0 for _ in valid_points]
    width = 0.065
    for label, values, color in components:
        axis.bar(x_values, values, width=width, bottom=bottoms, label=label, color=color)
        bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
    axis.set_xlabel("Load [p.u.]")
    axis.set_ylabel("Loss [W]")
    axis.grid(True, axis="y", alpha=0.3)
    if components:
        axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()


def _build_signature(report: DesignReport, load_grid: tuple[float, ...]) -> str:
    device = report.device
    capacitor = report.capacitor
    magnetic = report.magnetic
    bridge = report.bridge_rectifier
    payload = {
        "efficiency_sweep_model_version": 3,
        "topology_id": report.spec.topology_id,
        "raw_input": report.spec.raw_input,
        "candidate": _candidate_signature(report.candidate),
        "semiconductor_scheme": getattr(device, "active_scheme_id", None) or getattr(device, "recommended_scheme_id", None),
        "selected_devices": getattr(device, "selected_devices", {}),
        "selected_bridge_rectifier": _bridge_rectifier_signature(bridge),
        "capacitor_parts": _capacitor_signature(capacitor),
        "magnetic_design_id": _magnetic_design_signature(magnetic),
        "load_grid": load_grid,
        "operating_vin": report.operating_point.vin_v if report.operating_point is not None else None,
        "operating_power_factor": report.operating_point.power_factor if report.operating_point is not None else None,
    }
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _candidate_signature(candidate) -> dict[str, object]:
    if candidate is None:
        return {}
    values = asdict(candidate) if hasattr(candidate, "__dataclass_fields__") else vars(candidate)
    return {
        "topology_id": values.get("topology_id"),
        "vin_nom": values.get("vin_nom"),
        "vout_target": values.get("vout_target"),
        "pout_target": values.get("pout_target"),
        "fs_hz": values.get("fs_hz"),
        "inductance_h": values.get("inductance_h"),
        "capacitance_f": values.get("capacitance_f"),
        "duty_nom": values.get("duty_nom"),
        "iout": values.get("iout"),
        "metadata": values.get("metadata", {}),
    }


def _bridge_rectifier_signature(bridge) -> dict[str, object] | None:
    if bridge is None or bridge.selected_candidate is None:
        return None
    candidate = bridge.selected_candidate
    values = asdict(candidate) if hasattr(candidate, "__dataclass_fields__") else vars(candidate)
    return {
        "candidate_id": values.get("candidate_id"),
        "part_number": values.get("part_number"),
        "manufacturer": values.get("manufacturer"),
        "v_rrm_v": values.get("v_rrm_v"),
        "io_avg_rectified_a": values.get("io_avg_rectified_a"),
        "vf_max_v": values.get("vf_max_v"),
        "vf_test_current_a": values.get("vf_test_current_a"),
        "rth_jc_k_per_w": values.get("rth_jc_k_per_w"),
        "rth_ja_k_per_w": values.get("rth_ja_k_per_w"),
        "topology_kind": values.get("topology_kind"),
    }


def _can_reuse_sweep_result(result: EfficiencySweepResult | None, signature: str, output_dir) -> bool:
    if result is None or result.signature != signature:
        return False
    paths = result.artifact_paths
    if not paths or any(not Path(path).exists() for path in paths.values()):
        return False
    expected_dir = (
        Path(output_dir).resolve()
        if output_dir is not None
        else (_project_root() / "outputs" / "efficiency_sweep").resolve()
    )
    return all(Path(path).resolve().parent == expected_dir for path in paths.values())


def _capacitor_signature(capacitor) -> dict[str, str | None]:
    if capacitor is None:
        return {}
    return {
        "input": _capacitor_part(capacitor.input_selection),
        "output": _capacitor_part(capacitor.output_selection),
    }


def _capacitor_part(side_result) -> str | None:
    if side_result is None or side_result.recommended is None:
        return None
    recommended = side_result.recommended
    return ":".join(
        (
            recommended.candidate.part_number,
            str(recommended.series_count),
            str(recommended.parallel_count),
        )
    )


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _magnetic_design_signature(magnetic) -> str | None:
    if magnetic is None:
        return None
    if getattr(magnetic, "result_type", "") == "ac_dc_sendust_reactor":
        result = magnetic.ac_dc_reactor_result
        selected = result.selected_candidate if result is not None else None
        return selected.candidate_id if selected is not None else None
    return getattr(magnetic, "selected_design_id", None)


def _selected_ac_dc_reactor_candidate(report: DesignReport):
    magnetic = report.magnetic
    if magnetic is None or magnetic.result_type != "ac_dc_sendust_reactor":
        return None
    result = magnetic.ac_dc_reactor_result
    if result is None:
        return None
    return result.selected_candidate


def _has_selected_magnetic_design(report: DesignReport) -> bool:
    magnetic = report.magnetic
    if magnetic is None:
        return False
    if magnetic.selected_design_id or magnetic.chosen_designs:
        return True
    result = magnetic.ac_dc_reactor_result
    return result is not None and result.selected_candidate is not None


def _ac_dc_reactor_metrics(waveform_set: WaveformSet) -> dict[str, object]:
    metrics = waveform_set.metadata.get("ac_dc_dc_inductor_metrics")
    return metrics if isinstance(metrics, dict) else {}


def _is_ac_dc_bridge_topology(report: DesignReport) -> bool:
    return report.spec.topology_id in SUPPORTED_BRIDGE_RECTIFIER_TOPOLOGIES


def _is_single_phase_boost_pfc_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == SINGLE_PHASE_BOOST_PFC_TOPOLOGY_ID


def _is_single_phase_totem_pole_pfc_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == SINGLE_PHASE_TOTEM_POLE_PFC_TOPOLOGY_ID


def _is_single_phase_pfc_topology(report: DesignReport) -> bool:
    return _is_single_phase_boost_pfc_topology(report) or _is_single_phase_totem_pole_pfc_topology(report)


def _is_ac_dc_reactor_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == "single_phase_diode_bridge_rectifier_dc_inductor_filter"


def _is_three_phase_ac_dc_bridge_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == "three_phase_diode_bridge_rectifier_capacitor_filter"


def _is_single_phase_inverter_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == "single_phase_full_bridge_inverter"


def _is_three_phase_two_level_inverter_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == "three_phase_two_level_voltage_source_inverter"


def _is_three_phase_npc_inverter_topology(report: DesignReport) -> bool:
    return report.spec.topology_id == "three_phase_three_level_npc_inverter"


def _positive_float(value: object, default: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(numeric) or numeric <= 0.0:
        return float(default)
    return numeric


def _rms(values: Sequence[float]) -> float:
    values = [float(value) for value in values]
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))


def _waveform_pp(values: Sequence[float]) -> float:
    values = [float(value) for value in values]
    if not values:
        return 0.0
    return max(values) - min(values)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]
