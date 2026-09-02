"""Simplified magnetic thermal-stage runtime orchestration."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import replace
from pathlib import Path

from ..engines.thermal.thermal_estimator import (
    estimate_design_thermal_entry,
    export_thermal_summary,
    resolve_ambient_temperature_c,
)
from ..models.design_report import DesignReport
from ..models.design_run_context import get_run_output_dir
from ..models.thermal_result import ThermalComparisonEntry, ThermalEstimate, ThermalResult
from ..models.thermal_result import NpcThermalRoleResult, NpcThermalScenarioResult
from ..engines.devices.loss_aggregation import role_physical_device_count
from ..engines.devices.stress_adapter import build_current_operating_switch_stress_case
from ..engines.devices.loss_evaluator import evaluate_switch_loss
from ..engines.devices.thermal_interface import resolve_thermal_interface_stack
from ..libraries.semiconductors.registry import build_default_semiconductor_registry
from ..models.operating_point import OperatingPoint
from ..topologies.base.registry import build_default_registry
from .options import MAGNETIC_STAGE_DISABLED_NOTE, MAGNETIC_THERMAL_DISABLED_NOTE, PipelineOptions, resolve_pipeline_options
from ..engines.magnetics.core_loss_audit import core_loss_is_comparable
from ..models.llc_run_context import is_llc_topology


def _optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def run_thermal_pipeline(report: DesignReport, pipeline_options: PipelineOptions | None = None) -> DesignReport:
    """Attach a first-pass magnetic thermal estimate and close LLC lifecycle state."""

    result = _run_thermal_pipeline(report, pipeline_options=pipeline_options)
    return _finalize_llc_thermal_stage(result)


def _run_thermal_pipeline(report: DesignReport, pipeline_options: PipelineOptions | None = None) -> DesignReport:
    """Attach a first-pass magnetic thermal estimate to a design report."""
    options = resolve_pipeline_options(pipeline_options)
    if report.spec.topology_id == "three_phase_three_level_npc_inverter":
        return _run_npc_thermal_pipeline(report, options)
    if not options.enable_magnetic_design:
        thermal_result = ThermalResult(
            ambient_temp_c=resolve_ambient_temperature_c(report),
            summary=MAGNETIC_THERMAL_DISABLED_NOTE,
            notes=[MAGNETIC_STAGE_DISABLED_NOTE],
        )
        return replace(report, thermal=thermal_result)

    if report.magnetic is not None and report.magnetic.result_type == "separated_llc_transformer":
        contract = report.magnetic.llc_magnetic_contract
        if report.llc_run_context is not None and contract is None:
            thermal_result = ThermalResult(
                ambient_temp_c=resolve_ambient_temperature_c(report),
                summary="LLC thermal screening is blocked because the magnetic combination contract is incomplete.",
                notes=["No unified LLC magnetic combination contract is available."],
                status="unavailable",
            )
            return replace(report, thermal=thermal_result)
        transformer_result = report.magnetic.transformer_pareto_result
        transformer = getattr(transformer_result, "recommended_candidate", None)
        external_result = report.magnetic.llc_external_resonant_inductor_search_result
        external = getattr(external_result, "recommended_candidate", None)
        transformer_id = (
            contract.transformer_design_id
            if contract is not None
            else report.magnetic.recommended_transformer_design_id
            or getattr(transformer, "candidate_id", None)
        )
        external_id = (
            contract.external_lr_design_id
            if contract is not None
            else report.magnetic.recommended_external_lr_design_id
            or getattr(external, "design_id", None)
        )
        combined_id = (
            contract.combined_magnetic_design_id
            if contract is not None
            else report.magnetic.recommended_combined_magnetic_design_id
        )
        components: dict[str, dict[str, object]] = {}
        if transformer is not None:
            components["transformer"] = {
                "status": "available",
                "design_id": transformer_id,
                "assembly_type": "transformer",
                "loss_basis": "LLC current operating-point first-pass magnetic screening",
                "ambient_c": resolve_ambient_temperature_c(report),
                "core_loss_w": _optional_float(getattr(transformer, "core_loss_w", None)),
                "copper_loss_w": _optional_float(getattr(transformer, "copper_loss_w", None)),
                "total_loss_w": _optional_float(getattr(transformer, "total_loss_w", None)),
                "hotspot_c": _optional_float(getattr(transformer, "hotspot_c", None)),
                "source": "LLC transformer magnetic screening first-pass hotspot estimate",
            }
        else:
            components["transformer"] = {
                "status": "not_evaluated",
                "design_id": transformer_id,
                "assembly_type": "transformer",
                "loss_basis": "LLC current operating-point first-pass magnetic screening",
                "ambient_c": resolve_ambient_temperature_c(report),
                "core_loss_w": None,
                "copper_loss_w": None,
                "total_loss_w": None,
                "hotspot_c": None,
                "source": "LLC transformer magnetic screening",
            }
        if external is not None:
            components["external_lr"] = {
                "status": "available",
                "design_id": external_id,
                "assembly_type": "external_lr",
                "loss_basis": "LLC current operating-point first-pass magnetic screening",
                "ambient_c": resolve_ambient_temperature_c(report),
                "core_loss_w": _optional_float(getattr(external, "core_loss_w", None)),
                "copper_loss_w": _optional_float(getattr(external, "copper_loss_w", None)),
                "total_loss_w": _optional_float(getattr(external, "total_loss_w", None)),
                "hotspot_c": _optional_float(getattr(external, "hotspot_c", None)),
                "source": "External Lr magnetic screening first-pass hotspot estimate",
            }
        else:
            external_status = "not_required"
            target = report.magnetic.llc_external_resonant_inductor_target
            if target is None:
                external_status = "not_evaluated"
            elif target.is_design_required:
                external_status = "no_feasible_candidate"
            components["external_lr"] = {
                "status": external_status,
                "design_id": external_id,
                "assembly_type": "external_lr",
                "loss_basis": "LLC current operating-point first-pass magnetic screening",
                "ambient_c": resolve_ambient_temperature_c(report),
                "core_loss_w": None,
                "copper_loss_w": None,
                "total_loss_w": None,
                "hotspot_c": None,
                "source": "External Lr magnetic screening",
            }
        valid_component_count = sum(
            item.get("hotspot_c") is not None for item in components.values()
        )
        thermal_entries = _llc_thermal_entries(report, transformer, external, components)
        artifact_paths = export_thermal_summary(
            thermal_entries,
            output_dir=_llc_thermal_output_dir(report),
        )
        thermal_result = ThermalResult(
            ambient_temp_c=resolve_ambient_temperature_c(report),
            recommended_design_id=combined_id or transformer_id,
            summary="LLC transformer and external resonant-inductor thermal screening uses magnetic first-pass hotspot estimates.",
            notes=[
                "The separated LLC transformer screening includes a first-pass hotspot estimate.",
                "The fixed-inductor stack-count thermal comparison is not applied to separated LLC components.",
                "Transformer and external Lr hotspots are reported separately; no combined thermal network is inferred.",
                *([f"Thermal summary artifact saved to {artifact_paths[0]}."] if artifact_paths else []),
            ],
            llc_component_thermal=components,
            llc_component_estimates={entry.assembly_type: entry for entry in thermal_entries if entry.assembly_type},
            chosen_design_estimates=thermal_entries,
            artifact_paths=artifact_paths,
            status="valid" if valid_component_count else "unavailable",
            valid_loss_entry_count=valid_component_count,
            unavailable_loss_entry_count=len(components) - valid_component_count,
        )
        return replace(report, thermal=thermal_result)

    if report.magnetic is not None and report.magnetic.result_type == "ac_dc_sendust_reactor":
        selection = report.magnetic.ac_dc_reactor_result
        selected = selection.selected_candidate if selection is not None else None
        thermal_result = ThermalResult(
            ambient_temp_c=resolve_ambient_temperature_c(report),
            recommended_design_id=selected.candidate_id if selected is not None else None,
            summary="AC-DC Sendust reactor thermal model is pending; loss and geometry proxy data are reported in Magnetics.",
            notes=[
                "AC-DC Sendust reactor selection produced design-point copper/core loss, but a calibrated low-frequency toroid thermal model is not implemented yet.",
                "Do not interpret this stage as a final choke temperature rise estimate.",
            ],
        )
        return replace(report, thermal=thermal_result)

    if report.magnetic is None or not report.magnetic.chosen_designs:
        thermal_result = ThermalResult(
            ambient_temp_c=resolve_ambient_temperature_c(report),
            notes=["Thermal evaluation did not run because no selected magnetic designs are available."],
        )
        return replace(report, thermal=thermal_result)

    ambient_temp_c = resolve_ambient_temperature_c(report)
    evaluation_by_id = {
        evaluation.design_id: evaluation
        for evaluation in (report.magnetic.evaluations if report.magnetic is not None else [])
    }

    chosen_design_estimates = [
        estimate_design_thermal_entry(
            design=design,
            ambient_temp_c=ambient_temp_c,
            evaluation=evaluation_by_id.get(design.candidate_id),
        )
        for design in report.magnetic.chosen_designs
    ]
    all_entries = [*chosen_design_estimates]
    valid_loss_entry_count = sum(entry.estimate is not None for entry in all_entries)
    unavailable_loss_entry_count = len(all_entries) - valid_loss_entry_count

    best_by_stack_count: dict[int, ThermalComparisonEntry] = {}
    for stack_count, design in report.magnetic.best_by_stack_count.items():
        best_by_stack_count[stack_count] = estimate_design_thermal_entry(
            design=design,
            ambient_temp_c=ambient_temp_c,
            evaluation=evaluation_by_id.get(design.candidate_id),
        )

    recommended_design_id = _resolve_recommended_design_id(report)
    recommended_entry = _find_entry(chosen_design_estimates, recommended_design_id)
    if recommended_entry is None and recommended_design_id is not None:
        recommended_entry = next(
            (entry for entry in best_by_stack_count.values() if entry.design_id == recommended_design_id),
            None,
        )
    if recommended_entry is None and chosen_design_estimates:
        recommended_entry = chosen_design_estimates[len(chosen_design_estimates) // 2]
        recommended_design_id = recommended_entry.design_id

    unique_entries = _dedupe_entries([*chosen_design_estimates, *best_by_stack_count.values()])
    artifact_paths = export_thermal_summary(unique_entries, output_dir=_llc_thermal_output_dir(report))

    notes = [
        f"Ambient temperature resolved to {ambient_temp_c:.1f} C from GUI/spec input, with 25.0 C as the blank-field fallback.",
        "Thermal stage reuses the existing magnetic design outputs and operating-point loss reevaluation without rerunning magnetic search.",
        "This first pass uses MKF-inspired empirical resistance formulas rather than a detailed thermal network or CFD model.",
    ]
    if artifact_paths:
        notes.append(f"Thermal summary artifact saved to {artifact_paths[0]}.")

    recommended_hotspot_c = (
        recommended_entry.estimate.hotspot_proxy_temp_c
        if recommended_entry is not None and recommended_entry.estimate is not None
        else None
    )
    if recommended_entry is not None and recommended_hotspot_c is not None:
        summary = (
            f"Simplified magnetic thermal estimate completed for {len(unique_entries)} designs. "
            f"Recommended design {recommended_entry.design_id} has a hotspot proxy of {recommended_hotspot_c:.2f} C."
        )
    else:
        summary = "Simplified magnetic thermal estimate completed, but no fully resolved hotspot proxy was available."

    thermal_result = ThermalResult(
        summary=summary,
        ambient_temp_c=ambient_temp_c,
        recommended_design_id=recommended_design_id,
        recommended_estimate=recommended_entry.estimate if recommended_entry is not None else None,
        chosen_design_estimates=chosen_design_estimates,
        best_by_stack_count=best_by_stack_count,
        artifact_paths=artifact_paths,
        notes=notes,
        status="valid" if valid_loss_entry_count else "unavailable",
        valid_loss_entry_count=valid_loss_entry_count,
        unavailable_loss_entry_count=unavailable_loss_entry_count,
    )
    return replace(report, thermal=thermal_result)


_NPC_THERMAL_SCENARIOS = (
    ("rated", "Rated operating point", 1.0, "design", "ambient"),
    ("max_bus", "Maximum DC-link voltage", 1.0, "design", "ambient"),
    ("minimum_pf", "Minimum power factor", 1.0, "minimum", "ambient"),
    ("overload", "Maximum overload", "overload", "design", "ambient"),
    ("maximum_ambient", "Maximum ambient temperature", 1.0, "design", "maximum"),
)
_NPC_HEATSINK_MODEL = "forced_air_shared_extrusion_proxy_v1"
_NPC_SELECTED_SINK_RTH_K_PER_W = 0.12
_NPC_AIRFLOW_M3_H = 120.0
_NPC_AIRFLOW_DERATING = 0.80
_NPC_THERMAL_COUPLING = 1.15
_NPC_CONTACT_PRESSURE_MPA = 0.35


def _run_npc_thermal_pipeline(report: DesignReport, options: PipelineOptions) -> DesignReport:
    """Run a role-aware, shared-sink NPC semiconductor thermal screen."""
    if not options.enable_magnetic_design:
        # The option controls the legacy magnetic stage; semiconductor thermal
        # design is still required for NPC because it has no magnetic prerequisite.
        pass
    if report.device is None or report.candidate is None or report.stress is None:
        result = ThermalResult(
            summary="NPC semiconductor thermal design is unavailable because device or stress results are missing.",
            ambient_temp_c=resolve_ambient_temperature_c(report),
            status="unavailable",
            notes=["Run topology, device selection, and operating-point loss stages before NPC thermal design."],
        )
        return replace(report, thermal=result)

    basis = _npc_design_basis(report)
    registry = build_default_semiconductor_registry()
    topology_plugin = build_default_registry().get_plugin(report.spec.topology_id)
    devices = _npc_devices_by_role(report, registry)
    scenarios = tuple(
        _npc_thermal_scenario(report, basis, devices, scenario, topology_plugin)
        for scenario in _NPC_THERMAL_SCENARIOS
    )
    valid = [scenario for scenario in scenarios if scenario.worst_junction_temp_c is not None]
    worst = max(valid, key=lambda item: item.worst_junction_temp_c) if valid else None
    output_dir = get_run_output_dir(report, "semiconductor_design")
    artifact_paths = _export_npc_thermal_artifacts(scenarios, output_dir)
    assumptions = {
        "heatsink_model": _NPC_HEATSINK_MODEL,
        "selected_sink_rth_k_per_w": _NPC_SELECTED_SINK_RTH_K_PER_W,
        "design_airflow_m3_h": _NPC_AIRFLOW_M3_H,
        "airflow_derating_factor": _NPC_AIRFLOW_DERATING,
        "thermal_coupling_factor": _NPC_THERMAL_COUPLING,
        "interface_material_stack": "0.03 mm thermal grease + 0.10 mm electrically insulating pad + 0.03 mm thermal grease",
        "installation_pressure_mpa": _NPC_CONTACT_PRESSURE_MPA,
        "interface_pressure_basis": "engineering assumption; verify with assembly work instruction and TIM supplier data",
        "airflow_basis": "effective forced-air design flow after fan/system derating; verify by anemometer or CFD",
        "loss_basis": "fifth-step DeviceLossResult refreshed for each NPC thermal scenario",
    }
    notes = [
        "NPC thermal design uses the corrected per-device loss model and physical role counts; the former fixed 11.17 W basis is retired.",
        "Shared heatsink temperature includes a 1.15 thermal-coupling factor for neighboring devices.",
        "Interface material and installation pressure are engineering assumptions pending assembly validation.",
        "Airflow is a derated effective design value, not a fan nameplate or measured flow claim.",
        *([f"Worst case: {worst.label}, {worst.worst_role} Tj={worst.worst_junction_temp_c:.2f} C."] if worst else []),
        *([f"NPC thermal artifacts saved to {artifact_paths[0]}."] if artifact_paths else []),
    ]
    result = ThermalResult(
        summary=(
            f"NPC semiconductor thermal design evaluated {len(scenarios)} worst-case scenarios; "
            f"worst junction temperature is {worst.worst_junction_temp_c:.2f} C."
            if worst else "NPC semiconductor thermal design could not resolve a valid scenario."
        ),
        ambient_temp_c=float(basis["ambient_c"]),
        artifact_paths=artifact_paths,
        notes=notes,
        status="valid" if scenarios else "unavailable",
        valid_loss_entry_count=len(valid),
        unavailable_loss_entry_count=len(scenarios) - len(valid),
        npc_scenarios=scenarios,
        npc_worst_case=worst,
        npc_assumptions=assumptions,
    )
    return replace(report, thermal=result)


def _npc_design_basis(report: DesignReport) -> dict[str, float]:
    metadata = report.candidate.metadata if report.candidate is not None else {}
    basis = metadata.get("design_basis") if isinstance(metadata, dict) else {}
    dc = basis.get("dc_link_voltage_v", {}) if isinstance(basis, dict) else {}
    pf = basis.get("power_factor", {}) if isinstance(basis, dict) else {}
    op = basis.get("operating_range", {}) if isinstance(basis, dict) else {}
    thermal = basis.get("thermal", {}) if isinstance(basis, dict) else {}
    return {
        "vdc_nom": float(dc.get("nominal", metadata.get("vdc_nom_v", 700.0))),
        "vdc_max": float(dc.get("max", metadata.get("vdc_max_v", 750.0))),
        "pf": float(pf.get("design", metadata.get("power_factor", 1.0))),
        "pf_min": float(pf.get("min", metadata.get("power_factor_min", 0.8))),
        "overload": float(op.get("overload_ratio_max", metadata.get("overload_ratio_max", 1.1))),
        "ambient_c": float(thermal.get("ambient_temperature_c", 25.0)),
        "target_tj_c": float(thermal.get("target_junction_temperature_c", 100.0)),
    }


def _npc_devices_by_role(report: DesignReport, registry) -> dict[str, object]:
    selected = getattr(report.device, "selected_devices", {}) or {}
    devices: dict[str, object] = {}
    for role in ("npc_outer_switch", "npc_inner_switch", "npc_clamp_diode"):
        part = selected.get(role)
        if part:
            try:
                devices[role] = registry.get_device(part)
            except KeyError:
                pass
    return devices


def _npc_thermal_scenario(report, basis, devices, definition, topology_plugin) -> NpcThermalScenarioResult:
    scenario_id, label, load_value, pf_mode, ambient_mode = definition
    load_ratio = basis["overload"] if load_value == "overload" else float(load_value)
    pf = basis["pf_min"] if pf_mode == "minimum" else basis["pf"]
    vdc = basis["vdc_max"] if scenario_id == "max_bus" else basis["vdc_nom"]
    ambient_c = max(basis["ambient_c"], float(report.spec.metadata.get("ambient_temp_c", basis["ambient_c"])))
    if ambient_mode == "maximum":
        ambient_c = max(ambient_c, float(report.spec.metadata.get("ambient_temp_max_c", ambient_c + 10.0)))
    operating_point = OperatingPoint(vin_v=vdc, load_ratio=load_ratio, power_factor=pf)
    scenario_report = replace(report, operating_point=operating_point)
    current_case = build_current_operating_switch_stress_case(
        replace(scenario_report, waveform=None),
        plugin=topology_plugin,
    )
    losses = _npc_scenario_losses(scenario_report, current_case, devices, report.device)
    role_results = []
    total_loss = 0.0
    for role, loss in losses.items():
        device = devices[role]
        count = role_physical_device_count(report.device, role)
        interface = resolve_thermal_interface_stack(device, loss["stress"])
        total_loss += count * loss["result"].p_total_W
        role_results.append((role, device, count, loss["result"], interface))
    total_sink_power = total_loss * _NPC_THERMAL_COUPLING
    allowed_sink_values = [
        (
            basis["target_tj_c"] - ambient_c
            - loss.p_total_W * (device.static.rth_jc_K_per_W + interface.total_rth_k_per_w)
        ) / total_sink_power
        for _, device, _, loss, interface in role_results
        if total_sink_power > 0
    ]
    allowed_sink_rth = min(allowed_sink_values) if allowed_sink_values else None
    selected_rth = _NPC_SELECTED_SINK_RTH_K_PER_W
    final_roles = []
    for role, device, count, loss, interface in role_results:
        sink_rise = total_sink_power * selected_rth
        interface_temp = ambient_c + sink_rise
        case_temp = interface_temp + loss.p_total_W * interface.total_rth_k_per_w
        tj = case_temp + loss.p_total_W * device.static.rth_jc_K_per_W
        margin = min(float(device.static.tj_max_C) - tj, basis["target_tj_c"] - tj)
        final_roles.append(NpcThermalRoleResult(
            role=role, part_number=device.part_number, physical_device_count=count,
            per_device_loss_w=loss.p_total_W, total_loss_w=count * loss.p_total_W,
            rth_jc_k_per_w=device.static.rth_jc_K_per_W, rth_cs_k_per_w=interface.total_rth_k_per_w,
            junction_temp_c=tj, case_temp_c=case_temp, interface_temperature_c=interface_temp,
            target_junction_temp_c=basis["target_tj_c"], tj_max_c=device.static.tj_max_C,
            junction_margin_c=margin, thermal_passed=margin >= 0.0,
            interface_model_name=interface.model_name, interface_layer_summary=interface.layer_summary,
            notes=tuple(interface.notes + interface.warnings),
        ))
    worst_role_result = max(final_roles, key=lambda item: item.junction_temp_c, default=None)
    required_sink = allowed_sink_rth if allowed_sink_rth is not None else None
    required_airflow = _required_airflow_m3_h(total_loss, max(basis["target_tj_c"] - ambient_c, 1.0))
    passed = bool(final_roles) and all(item.thermal_passed for item in final_roles)
    return NpcThermalScenarioResult(
        scenario_id=scenario_id, label=label, load_ratio=load_ratio, power_factor=pf, vdc_v=vdc,
        ambient_temp_c=ambient_c, total_semiconductor_loss_w=total_loss,
        required_sink_rth_k_per_w=required_sink, selected_sink_rth_k_per_w=selected_rth,
        heatsink_model=_NPC_HEATSINK_MODEL, heatsink_volume_cm3=_sink_volume_cm3(selected_rth),
        required_airflow_m3_h=required_airflow, design_airflow_m3_h=_NPC_AIRFLOW_M3_H,
        airflow_derating=_NPC_AIRFLOW_DERATING, thermal_coupling_factor=_NPC_THERMAL_COUPLING,
        worst_role=worst_role_result.role if worst_role_result else None,
        worst_junction_temp_c=worst_role_result.junction_temp_c if worst_role_result else None,
        minimum_junction_margin_c=min((item.junction_margin_c for item in final_roles), default=None),
        passed=passed, roles=tuple(final_roles),
        notes=("Scenario losses were refreshed from the fixed selected hardware.",),
    )


def _npc_scenario_losses(report, current_case, devices, device_result):
    if current_case is None:
        return {}
    from .run_device_pipeline import scale_switch_stress_for_parallel

    result = {}
    for stress in current_case.stresses:
        device = devices.get(stress.role)
        if device is None:
            continue
        role_result = next(
            (item for scheme in getattr(device_result, "scheme_results", ())
             if scheme.scheme_id == (getattr(device_result, "active_scheme_id", None) or getattr(device_result, "recommended_scheme_id", None))
             for item in scheme.role_results if item.role == stress.role),
            None,
        )
        parallel_count = max(int(getattr(role_result, "parallel_count", 1) or 1), 1)
        scenario_v_block = 0.5 * float(report.candidate.metadata.get("npc_neutral_point_stress_factor", 1.02)) * float(report.operating_point.vin_v)
        scenario_v_block += float(report.candidate.metadata.get("npc_switching_overvoltage_v", 0.0))
        scaled_stress = scale_switch_stress_for_parallel(
            replace(stress, v_block_V=scenario_v_block), parallel_count
        )
        result[stress.role] = {"stress": scaled_stress, "result": evaluate_switch_loss(device, scaled_stress)}
    return result


def _required_airflow_m3_h(power_w: float, delta_t_c: float) -> float:
    # Air-side estimate: Q = m_dot * cp * delta-T with density 1.2 kg/m3.
    return max(power_w, 0.0) / (1.2 * 1005.0 * max(delta_t_c, 1.0)) * 3600.0


def _sink_volume_cm3(rth_k_per_w: float) -> float:
    return 1.0 / (0.0025 * 10.0 * max(rth_k_per_w, 1e-9))


def _export_npc_thermal_artifacts(scenarios, output_dir) -> list[str]:
    if output_dir is None:
        return []
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "npc_thermal_design.json"
    csv_path = directory / "npc_thermal_scenarios.csv"
    payload = {
        "schema_version": "npc_thermal_design_v1",
        "scenarios": [
            {"scenario_id": item.scenario_id, "label": item.label, "load_ratio": item.load_ratio,
             "power_factor": item.power_factor, "vdc_v": item.vdc_v, "ambient_temp_c": item.ambient_temp_c,
             "total_semiconductor_loss_w": item.total_semiconductor_loss_w,
             "required_sink_rth_k_per_w": item.required_sink_rth_k_per_w,
             "selected_sink_rth_k_per_w": item.selected_sink_rth_k_per_w,
             "heatsink_model": item.heatsink_model, "heatsink_volume_cm3": item.heatsink_volume_cm3,
             "required_airflow_m3_h": item.required_airflow_m3_h, "design_airflow_m3_h": item.design_airflow_m3_h,
             "airflow_derating": item.airflow_derating, "thermal_coupling_factor": item.thermal_coupling_factor,
             "worst_role": item.worst_role, "worst_junction_temp_c": item.worst_junction_temp_c,
             "minimum_junction_margin_c": item.minimum_junction_margin_c, "passed": item.passed,
             "roles": [role.__dict__ for role in item.roles], "notes": list(item.notes)}
            for item in scenarios
        ],
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("scenario_id", "load_ratio", "power_factor", "vdc_v", "ambient_temp_c", "total_semiconductor_loss_w", "worst_role", "worst_junction_temp_c", "minimum_junction_margin_c", "required_sink_rth_k_per_w", "selected_sink_rth_k_per_w", "required_airflow_m3_h", "design_airflow_m3_h", "passed"))
        writer.writeheader()
        for item in scenarios:
            writer.writerow({key: getattr(item, key) for key in writer.fieldnames})
    return [str(json_path), str(csv_path)]


def _finalize_llc_thermal_stage(report: DesignReport) -> DesignReport:
    """Close the LLC thermal stage from the thermal result actually produced."""

    context = report.llc_run_context
    if context is None or not is_llc_topology(report.spec.topology_id):
        return report
    thermal = report.thermal
    if thermal is not None and thermal.status == "valid" and thermal.recommended_design_id:
        updated_context = context.transition("thermal", "succeeded")
    else:
        updated_context = context.transition(
            "thermal",
            "blocked",
            reason="LLC thermal result is incomplete; no current-run thermal recommendation is available.",
        )
    return replace(report, llc_run_context=updated_context)


def _llc_thermal_entries(report, transformer, external, components):
    """Adapt LLC component hotspot estimates to the shared thermal CSV contract."""

    entries = []
    for role, candidate in (("transformer", transformer), ("external_lr", external)):
        if candidate is None:
            continue
        component = components.get(role, {})
        ambient_c = _optional_float(component.get("ambient_c")) or resolve_ambient_temperature_c(report)
        hotspot_c = _optional_float(component.get("hotspot_c"))
        core_loss_w = _optional_float(component.get("core_loss_w"))
        copper_loss_w = _optional_float(component.get("copper_loss_w"))
        total_loss_w = _optional_float(component.get("total_loss_w"))
        entries.append(
            ThermalComparisonEntry(
                design_id=str(component.get("design_id") or getattr(candidate, "candidate_id", getattr(candidate, "design_id", role))),
                assembly_type=role,
                loss_basis="LLC current operating-point first-pass magnetic screening",
                estimate=ThermalEstimate(
                    ambient_temp_c=ambient_c,
                    core_loss_w=core_loss_w,
                    copper_loss_w=copper_loss_w,
                    total_loss_w=total_loss_w,
                    hotspot_proxy_temp_c=hotspot_c,
                ),
                notes=[str(component.get("source") or "LLC magnetic component thermal estimate")],
            )
        )
    return entries


def _llc_thermal_output_dir(report: DesignReport):
    """Keep thermal artifacts inside the current run when one exists."""

    return get_run_output_dir(report, "inductor_design")


def _resolve_recommended_design_id(report: DesignReport) -> str | None:
    if report.loss is not None and report.loss.recommended_design_id:
        return report.loss.recommended_design_id
    if report.magnetic is not None and report.magnetic.selected_design_id:
        return report.magnetic.selected_design_id
    return None


def _find_entry(entries: list[ThermalComparisonEntry], design_id: str | None) -> ThermalComparisonEntry | None:
    if design_id is None:
        return None
    return next((entry for entry in entries if entry.design_id == design_id), None)


def _dedupe_entries(entries: list[ThermalComparisonEntry]) -> list[ThermalComparisonEntry]:
    deduped: list[ThermalComparisonEntry] = []
    seen: set[str] = set()
    for entry in entries:
        if entry.design_id in seen:
            continue
        deduped.append(entry)
        seen.add(entry.design_id)
    return deduped
