"""Step-9 NPC system validation and final run closure."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from ..engines.hardware_overview import build_and_generate_hardware_overview
from ..models.design_report import DesignReport
from ..models.design_run_context import get_run_output_dir, update_design_run
from .options import PipelineOptions
from ..topologies.base import TopologyPlugin
from .run_efficiency_sweep_pipeline import run_efficiency_sweep
from .run_full_pipeline import run_full_pipeline

NPC_TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
VALIDATION_LOADS = (0.05, 0.25, 0.50, 0.75, 1.00, 1.10)
VALIDATION_BUS_POINTS = ("minimum", "nominal", "maximum")
VALIDATION_PF_POINTS = (-1.0, -0.8, 0.8, 1.0)


@dataclass(frozen=True)
class SystemValidationCheck:
    check_id: str
    status: str
    observed: Any
    limit: Any
    source: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items()}


@dataclass(frozen=True)
class NPCSystemValidationResult:
    status: str
    matrix_count: int
    matrix: tuple[dict[str, Any], ...] = ()
    checks: tuple[SystemValidationCheck, ...] = ()
    artifact_paths: list[str] = field(default_factory=list)
    unverified_risks: tuple[str, ...] = ()
    conclusions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "matrix_count": self.matrix_count,
            "matrix": [dict(row) for row in self.matrix],
            "checks": [check.to_dict() for check in self.checks],
            "artifact_paths": list(self.artifact_paths),
            "unverified_risks": list(self.unverified_risks),
            "conclusions": list(self.conclusions),
        }


def run_npc_system_validation(report: DesignReport) -> DesignReport:
    """Build the Step-9 validation result for an already-completed NPC run."""
    if report.spec.topology_id != NPC_TOPOLOGY_ID:
        raise ValueError("NPC Step-9 validation requires the three-phase three-level NPC topology.")
    result = build_npc_system_validation(report)
    output_dir = get_run_output_dir(report, "validation")
    if output_dir is not None:
        result = export_npc_system_validation(result, output_dir)
        result = _add_run_artifact_integrity_check(result, report)
        result = export_npc_system_validation(result, output_dir)
    updated = replace(report, system_validation=result)
    validation_status = "failed" if result.status == "fail" else "succeeded"
    validation_reason = (
        "NPC system validation contains one or more failed hard checks."
        if result.status == "fail"
        else None
    )
    updated = update_design_run(updated, {"validation": validation_status}, reason=validation_reason)
    return updated


def run_npc_step9_pipeline(
    plugin: TopologyPlugin,
    raw_input: dict[str, str],
    *,
    output_root: str | Path | None = None,
) -> DesignReport:
    """Run the complete NPC design, efficiency, overview, and validation chain."""
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=raw_input,
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=True),
        output_root=output_root,
    )
    report = update_design_run(
        report,
        {
            "design": "succeeded",
            "semiconductor_design": "succeeded" if report.device is not None else "not_started",
            "capacitor_design": "succeeded" if report.capacitor is not None else "not_started",
            "inductor_design": "succeeded" if report.magnetic is not None else "not_started",
            "loss": "succeeded" if report.loss is not None else "not_started",
            "thermal": "succeeded" if report.thermal is not None else "not_started",
        },
    )
    efficiency = run_efficiency_sweep(
        report,
        plugin=plugin,
        load_points=VALIDATION_LOADS,
    )
    report = replace(report, efficiency_sweep=efficiency)
    report = update_design_run(report, {"efficiency_sweep": "succeeded" if efficiency.is_complete() else "blocked"}, reason=efficiency.blocked_reason)
    overview = build_and_generate_hardware_overview(report)
    report = update_design_run(report, {"hardware_overview": "succeeded" if overview.status == "available" else "blocked"}, reason=overview.blocked_reason)
    report = run_npc_system_validation(report)
    return report


def build_npc_system_validation(report: DesignReport) -> NPCSystemValidationResult:
    """Evaluate the deterministic Step-9 matrix and cross-stage contracts."""
    candidate = report.candidate
    if candidate is None:
        raise ValueError("NPC system validation requires a synthesized candidate.")
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    basis = metadata.get("design_basis") if isinstance(metadata.get("design_basis"), dict) else {}
    vdc = _number(metadata.get("vdc_nom_v"), 700.0)
    vdc_min = _number(metadata.get("vdc_min_v"), vdc)
    vdc_max = _number(metadata.get("vdc_max_v"), vdc)
    vac_ll = _number(metadata.get("vac_ll_rms_v"), 400.0)
    pout = _number(candidate.pout_target, 0.0)
    pf_min = _number(_nested(basis, "power_factor", "min"), 0.8)
    pf_max = _number(_nested(basis, "power_factor", "max"), 1.0)
    load_max = _number(_nested(basis, "operating_range", "overload_ratio_max"), 1.10)
    modulation_limit = _number(_nested(basis, "switching", "modulation_index_limit"), 1.0)
    bus_values = {"minimum": vdc_min, "nominal": vdc, "maximum": vdc_max}
    matrix: list[dict[str, Any]] = []
    for bus_id in VALIDATION_BUS_POINTS:
        for load in VALIDATION_LOADS:
            for pf in VALIDATION_PF_POINTS:
                active_power_w = pout * load
                phase_rms = active_power_w / max(math.sqrt(3.0) * vac_ll * abs(pf), 1e-9)
                phase_peak = math.sqrt(2.0) * phase_rms
                ripple_pp = abs(candidate.delta_il) * load * (bus_values[bus_id] / max(vdc, 1e-9))
                b_peak = _selected_b_peak(report) * load * (bus_values[bus_id] / max(vdc, 1e-9))
                ccm = ripple_pp < 2.0 * phase_peak if phase_peak > 0.0 else True
                modulation = 2.0 * math.sqrt(2.0 / 3.0) * vac_ll / max(bus_values[bus_id], 1e-9)
                current_limit = _number(metadata.get("d_axis_current_limit_a"), math.inf)
                matrix.append(
                    {
                        "bus_point": bus_id,
                        "vdc_v": bus_values[bus_id],
                        "load_pu": load,
                        "power_factor": pf,
                        "active_power_w": active_power_w,
                        "phase_rms_a": phase_rms,
                        "phase_peak_a": phase_peak,
                        "ripple_pp_a": ripple_pp,
                        "b_peak_t": b_peak,
                        "modulation_index": modulation,
                        "ccm_valid": ccm,
                        "current_limit_pass": phase_peak <= current_limit,
                    }
                )

    checks = [
        _check("matrix_complete", len(matrix) == 72, len(matrix), 72, "step9.validation_matrix"),
        _check("declared_load_range", max(row["load_pu"] for row in matrix) <= load_max, max(row["load_pu"] for row in matrix), load_max, "request.design_basis.operating_range"),
        _check("modulation_all_bus_points", max(row["modulation_index"] for row in matrix) <= modulation_limit, max(row["modulation_index"] for row in matrix), modulation_limit, "npc.modulation.first_pass"),
        _check("declared_pf_range", min(abs(row["power_factor"]) for row in matrix) >= pf_min and max(abs(row["power_factor"]) for row in matrix) <= pf_max, (min(abs(row["power_factor"]) for row in matrix), max(abs(row["power_factor"]) for row in matrix)), (pf_min, pf_max), "request.design_basis.power_factor"),
        _check("ccm_all_matrix_points", all(row["ccm_valid"] for row in matrix), all(row["ccm_valid"] for row in matrix), True, "npc.current_ripple.first_pass"),
        _check("current_limit_all_matrix_points", all(row["current_limit_pass"] for row in matrix), all(row["current_limit_pass"] for row in matrix), True, "npc.controller.current_limit"),
        _voltage_check(report),
        _thermal_check(report),
        _capacitor_check(report),
        _filter_check(report),
        _efficiency_check(report),
        _switch_state_check(report),
        _deadtime_check(report),
        SystemValidationCheck("short_circuit_protection", "unverified", None, "hardware_protection_test", "request.design_basis", "Short-circuit test and hardware protection timing are not modeled."),
        SystemValidationCheck("double_pulse_overvoltage", "unverified", None, "measured_parasitic_overvoltage", "request.design_basis.voltage_stress", "Double-pulse and busbar parasitic validation remain pending."),
        SystemValidationCheck("emi_estimate", "unverified", None, "conducted_and_radiated_limits", "step9.scope", "No conducted/radiated EMI model is available in the current runtime."),
    ]
    hard_fail = any(item.status == "fail" for item in checks)
    unverified = tuple(item.notes for item in checks if item.status == "unverified")
    conditional = any(item.status == "conditional" for item in checks)
    status = "fail" if hard_fail else "conditional_pass" if (conditional or unverified) else "pass"
    final_conclusion = (
        "Final status is fail because at least one analytical hard constraint is not met."
        if hard_fail
        else "Final status is conditional because hardware-dependent protection, overvoltage, and EMI evidence is unavailable."
        if unverified
        else "All requested checks have analytical evidence."
    )
    conclusions = (
        f"System validation covers {len(matrix)} bus/load/PF operating points.",
        "All analytical hard checks pass." if not hard_fail else "At least one analytical hard check failed.",
        final_conclusion,
    )
    return NPCSystemValidationResult(status, len(matrix), tuple(matrix), tuple(checks), unverified_risks=unverified, conclusions=conclusions)


def export_npc_system_validation(result: NPCSystemValidationResult, output_dir: Path) -> NPCSystemValidationResult:
    """Persist JSON, matrix CSV, and a hash manifest for the validation stage."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "npc_system_validation.json"
    csv_path = output_dir / "npc_validation_matrix.csv"
    exported = replace(result, artifact_paths=[str(json_path), str(csv_path)])
    json_path.write_text(json.dumps(exported.to_dict(), indent=2, ensure_ascii=True), encoding="ascii")
    fields = list(result.matrix[0]) if result.matrix else []
    with csv_path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result.matrix)
    return exported


def _add_run_artifact_integrity_check(
    result: NPCSystemValidationResult,
    report: DesignReport,
) -> NPCSystemValidationResult:
    """Check that the current run has complete, contained stage artifacts."""

    root = get_run_output_dir(report, "validation")
    if root is None:
        check = SystemValidationCheck(
            "run_artifact_integrity",
            "fail",
            "run output root unavailable",
            "all required groups present in one run root",
            "run.manifest.artifact_groups",
        )
    else:
        run_root = root.parent.resolve()
        groups = (
            "design_request",
            "semiconductor_design",
            "capacitor_design",
            "inductor_design",
            "efficiency_sweep",
            "hardware_overview",
            "validation",
        )
        counts = {}
        contained = True
        for group in groups:
            files = [path for path in (run_root / group).rglob("*") if path.is_file()]
            counts[group] = len(files)
            contained = contained and all(_is_within(path, run_root) for path in files)
        exported_present = all(Path(path).is_file() and _is_within(Path(path), run_root) for path in result.artifact_paths)
        passed = contained and exported_present and all(counts[group] > 0 for group in groups)
        check = SystemValidationCheck(
            "run_artifact_integrity",
            "pass" if passed else "fail",
            {"file_counts": counts, "all_paths_contained": contained, "validation_artifacts_present": exported_present},
            "all required groups present in one run root",
            "run.manifest.artifact_groups",
            "Manifest consistency is checked from the current run root; artifacts from other runs are not accepted.",
        )
    checks = (*result.checks, check)
    hard_fail = any(item.status == "fail" for item in checks)
    unverified = tuple(item.notes for item in checks if item.status == "unverified")
    conditional = any(item.status == "conditional" for item in checks)
    status = "fail" if hard_fail else "conditional_pass" if (conditional or unverified) else "pass"
    conclusions = (
        f"System validation covers {result.matrix_count} bus/load/PF operating points.",
        "All analytical hard checks pass." if not hard_fail else "At least one analytical hard check failed.",
        "Final status is fail because at least one analytical hard constraint is not met."
        if hard_fail
        else "Final status is conditional because hardware-dependent protection, overvoltage, and EMI evidence is unavailable."
        if unverified
        else "All requested checks have analytical evidence.",
    )
    return replace(result, status=status, checks=checks, unverified_risks=unverified, conclusions=conclusions)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _check(check_id: str, passed: bool, observed: Any, limit: Any, source: str, notes: str = "") -> SystemValidationCheck:
    return SystemValidationCheck(check_id, "pass" if passed else "fail", observed, limit, source, notes)


def _voltage_check(report: DesignReport) -> SystemValidationCheck:
    stress_checks = getattr(report.stress, "role_voltage_checks", {}) if report.stress is not None else {}
    selected_checks = getattr(report.device, "voltage_checks", {}) if report.device is not None else {}
    stress_pass = bool(stress_checks) and all(
        getattr(item, "worst_case_blocking_voltage_v", 0.0)
        < getattr(item, "required_device_rating_v", 0.0)
        for item in stress_checks.values()
    )
    selected_pass = bool(selected_checks) and all(
        item.get("passed") is True for item in selected_checks.values() if isinstance(item, dict)
    )
    observed = {
        "worst_case_blocking_voltage_v": {
            key: getattr(value, "worst_case_blocking_voltage_v", None)
            for key, value in stress_checks.items()
        },
        "selected_device_rating_v": {
            key: value.get("selected_device_rating_v")
            for key, value in selected_checks.items()
            if isinstance(value, dict)
        },
        "selected_device_passed": {
            key: value.get("passed")
            for key, value in selected_checks.items()
            if isinstance(value, dict)
        },
    }
    return _check(
        "npc_voltage_rating",
        stress_pass and selected_pass,
        observed,
        "each selected NPC role device passes the required rating",
        "npc.stress.voltage_checks + npc.device.voltage_checks",
        "Uses maximum bus, neutral-point factor, switching overvoltage assumption, static margin, and selected-device rating readback.",
    )


def _thermal_check(report: DesignReport) -> SystemValidationCheck:
    thermal = report.thermal
    status = getattr(thermal, "status", "not_evaluated") if thermal is not None else "not_evaluated"
    return SystemValidationCheck("thermal_worst_case", "pass" if status == "valid" else "conditional" if status in {"available", "conditional_pass"} else "fail", status, "worst junction and magnetic hotspot limits", "npc.thermal_design", "Reuses the Step-6 scenario result; magnetic hotspot remains an analytical estimate.")


def _capacitor_check(report: DesignReport) -> SystemValidationCheck:
    design = getattr(report.capacitor, "npc_design", None) if report.capacitor is not None else None
    ratio = getattr(design, "worst_midpoint_deviation_ratio", None)
    limit = _number(_nested(report.spec.metadata, "design_basis", "targets", "neutral_point_voltage_deviation_ratio"), 0.02)
    return _check("split_link_midpoint_balance", ratio is not None and ratio <= limit, ratio, limit, "npc.capacitor.midpoint_proxy", "This is the Step-7 midpoint proxy, not closed-loop neutral-point control." )


def _filter_check(report: DesignReport) -> SystemValidationCheck:
    audit = getattr(report.magnetic, "npc_output_filter_audit", None)
    status = getattr(audit, "status", "not_evaluated") if audit is not None else "not_evaluated"
    return SystemValidationCheck("output_filter", "pass" if status == "pass" else "conditional" if status == "conditional_pass" else "fail", status, "resonance, damping, control interaction, ripple", "npc.output_filter.step8", "Reuses Step-8 output-filter audit and its explicit assumptions." )


def _efficiency_check(report: DesignReport) -> SystemValidationCheck:
    sweep = report.efficiency_sweep
    complete = sweep is not None and sweep.is_complete()
    return _check("efficiency_reproducible", complete, len(sweep.points) if sweep else 0, len(VALIDATION_LOADS), "efficiency_sweep.current_run", "Every validation load point must have total loss and efficiency." )


def _switch_state_check(report: DesignReport) -> SystemValidationCheck:
    metadata = report.waveform.metadata if report.waveform is not None and isinstance(report.waveform.metadata, dict) else {}
    gates = metadata.get("three_phase_npc_pd_spwm_waveforms")
    passed = bool(gates) and bool(metadata.get("three_phase_npc_device_currents"))
    return _check("npc_switch_state_paths", passed, bool(gates), True, "npc.waveform.pd_spwm", "Confirms generated three-level states and all six clamp-current branches are present." )


def _deadtime_check(report: DesignReport) -> SystemValidationCheck:
    value = _nested(report.spec.metadata, "design_basis", "losses", "dead_time_ns")
    return _check("dead_time_input", _number(value, -1.0) >= 0.0, value, ">= 0 ns", "request.design_basis.losses.dead_time_ns", "Dead-time is an input and loss term; commutation timing is not a switching transient simulation." )


def _selected_b_peak(report: DesignReport) -> float:
    magnetic = report.magnetic
    if magnetic is None:
        return 0.0
    design = next((item for item in magnetic.chosen_designs if item.candidate_id == magnetic.selected_design_id), None)
    design = design or (magnetic.chosen_designs[0] if magnetic.chosen_designs else None)
    return float(getattr(design, "b_peak_design_t", 0.0) or 0.0)


def _nested(value: Any, *keys: str) -> Any:
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _number(value: Any, fallback: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return fallback
    return value if math.isfinite(value) else fallback
