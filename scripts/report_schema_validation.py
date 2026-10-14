"""Validate PE-Claw structured report snapshots against the step-10 contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import math


REQUIRED = ("schema_version", "report_kind", "topology", "request", "candidate", "operating_point", "waveform", "stress", "magnetic", "capacitor", "thermal", "hardware", "ripple", "status", "audit")
QUANTITY = ("value", "unit", "source")
STATUSES = {"pass", "fail", "not_evaluated", "boundary", "unknown"}


def validate_report(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing:{key}")
    if payload.get("schema_version") != "pe_claw_structured_design_report_v1":
        errors.append("schema_version")
    if payload.get("report_kind") != "design_report":
        errors.append("report_kind")
    topology = payload.get("topology", {})
    if not isinstance(topology, dict) or not isinstance(topology.get("id"), str) or not topology["id"]:
        errors.append("topology.id")
    for path in (
        ("request", "output_voltage"),
        ("request", "output_power"),
        ("candidate", "inductance"),
        ("candidate", "capacitance"),
        ("ripple", "output_ripple_target"),
        ("ripple", "output_ripple_estimated"),
        ("ripple", "output_ripple_predicted"),
        ("ripple", "output_ripple_simulated"),
    ):
        value = payload.get(path[0], {}).get(path[1]) if isinstance(payload.get(path[0]), dict) else None
        if not isinstance(value, dict) or any(key not in value for key in QUANTITY):
            errors.append(".".join(path))
        elif not isinstance(value["unit"], str) or not isinstance(value["source"], str):
            errors.append("quantity:" + ".".join(path))
    status = payload.get("status", {})
    for key in ("zvs_status", "pf_status", "thermal_status"):
        if status.get(key) not in STATUSES:
            errors.append(f"status.{key}")
    for key in ("request", "candidate", "operating_point", "waveform", "stress", "magnetic", "capacitor", "thermal", "ripple", "audit"):
        if not isinstance(payload.get(key), dict):
            errors.append(f"section:{key}")
    if "engineering_result" in payload:
        engineering = payload["engineering_result"]
        if not isinstance(engineering, dict):
            errors.append("section:engineering_result")
        else:
            if payload.get("topology",{}).get("id") != "three_phase_three_level_t_type_inverter":
                errors.append("engineering_result.topology")
            if engineering.get("schema_version") != 1 or engineering.get("loss_scope_id") != "t_type_conduction_magnetics_capacitors_v1":
                errors.append("engineering_result.scope")
            basis = engineering.get("design_basis", {})
            policy = basis.get("selection_policy", "legacy_envelope") if isinstance(basis, dict) else None
            if not isinstance(policy, str) or policy not in {"legacy_envelope", "nominal_design_point"}:
                errors.append("engineering_result.selection_policy")
            if policy == "nominal_design_point":
                try:
                    raw = payload["request"]["raw_input"]
                    expected = (float(raw["vdc_nom"]), 1.0, float(raw["power_factor"]))
                    cases = basis["cases"]
                    if (len(cases) != 1 or tuple(cases[0]) != expected
                            or not all(math.isfinite(v) and v > 0 for v in expected)
                            or expected[2] > 1):
                        errors.append("engineering_result.design_point")
                except (KeyError, TypeError, ValueError, OverflowError):
                    errors.append("engineering_result.design_point")
            if not isinstance(engineering.get("excluded_components"),(list,tuple)) or "switching_on" not in engineering.get("excluded_components",()):
                errors.append("engineering_result.excluded_components")
            roles = {"t_type_main_switch","t_type_midpoint_switch"}
            devices = engineering.get("selected_devices",())
            if not isinstance(devices,(list,tuple)):
                errors.append("engineering_result.device")
                devices = ()
            selected_roles={d.get("role") for d in devices if isinstance(d,dict)}
            stage_status = engineering.get("stage_status",{})
            if engineering.get("magnetics") is not None:
                errors.extend(_validate_t_type_magnetics(engineering["magnetics"], basis))
            if engineering.get("capacitors") is not None:
                errors.extend(_validate_t_type_capacitors(engineering["capacitors"], basis, payload.get("capacitor", {}), payload.get("operating_point", {})))
            if not isinstance(stage_status,dict):
                errors.append("engineering_result.stage_status")
                stage_status = {}
            if stage_status.get("device") == "succeeded" and selected_roles != roles:
                errors.append("engineering_result.required_roles")
            for device in devices:
                if (not isinstance(device,dict) or device.get("role") not in roles or not device.get("part_number")
                        or device.get("parallel_count") not in (1,2,3) or not isinstance(device.get("position_ids"),(list,tuple))
                        or any(not isinstance(p,str) for p in device["position_ids"]) or len(set(device["position_ids"])) != 6):
                    errors.append("engineering_result.device")
            references = engineering.get("role_selection_reference",{})
            if not isinstance(references,dict):
                errors.append("engineering_result.reference")
                references = {}
            for reference in references.values():
                if policy == "nominal_design_point" and isinstance(reference, dict):
                    case = reference.get("case")
                    cases = basis.get("cases")
                    if (not isinstance(case, (list, tuple)) or not isinstance(cases, (list, tuple))
                            or len(cases) != 1 or not isinstance(cases[0], (list, tuple))
                            or tuple(case) != tuple(cases[0])):
                        errors.append("engineering_result.reference_case")
                if not isinstance(reference,dict) or any(not isinstance(reference.get(key),(int,float)) or not math.isfinite(reference[key])
                        for key in ("per_device_channel_w","per_device_diode_w","reference_tj_c")):
                    errors.append("engineering_result.reference")
                elif reference["per_device_channel_w"]<0 or reference["per_device_diode_w"]<0:
                    errors.append("engineering_result.negative_loss")
            if stage_status.get("device") == "succeeded":
                if len(devices) != 2 or set(references) != roles:
                    errors.append("engineering_result.required_roles")
                expected_packages = {}
                for device in devices:
                    if not isinstance(device,dict) or device.get("role") not in roles:
                        continue
                    role = device["role"]
                    positions = {f"{p}_{r}" for p in "abc" for r in (("QP","QN") if role == "t_type_main_switch" else ("QA","QO"))}
                    actual_positions = device.get("position_ids",())
                    if not isinstance(actual_positions,(list,tuple)) or any(not isinstance(p,str) for p in actual_positions) or set(actual_positions) != positions:
                        errors.append("engineering_result.position_ids")
                    n = device.get("parallel_count")
                    if n not in (1,2,3):
                        continue
                    for position in positions:
                        for index in range(n):
                            expected_packages[f"{position}_{index+1}"] = (device.get("part_number"),[position])
                    ref = references.get(role,{})
                    if not isinstance(ref,dict) or ref.get("part_number") != device.get("part_number") or ref.get("parallel_count") != n or ref.get("position_id") not in positions:
                        errors.append("engineering_result.reference_identity")
                packages = engineering.get("packages",())
                if not isinstance(packages,(list,tuple)):
                    packages = ()
                ids = [p.get("package_instance_id") for p in packages if isinstance(p,dict) and isinstance(p.get("package_instance_id"),str)]
                if len(ids) != len(packages) or len(set(ids)) != len(ids) or set(ids) != set(expected_packages):
                    errors.append("engineering_result.packages")
                for package in packages:
                    if not isinstance(package,dict):
                        continue
                    expected = expected_packages.get(package.get("package_instance_id"))
                    members = package.get("member_position_ids",())
                    sections = package.get("section_bindings",())
                    if expected is None or not isinstance(members,(list,tuple)) or not isinstance(sections,(list,tuple)) or (package.get("part_number"),list(members)) != expected or tuple(sections) != ("discrete_IGBT_FRD",):
                        errors.append("engineering_result.package_binding")
    return errors


def _validate_t_type_magnetics(magnetic, design_basis):
    """Validate the optional step-two physical-instance subtotal contract."""
    prefix = "engineering_result.magnetics"
    if not isinstance(magnetic, dict):
        return [prefix]
    errors = []
    finite = lambda value: isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
    totals = ("total_copper_loss_w", "total_core_loss_w", "total_loss_w", "total_volume_m3")
    status = magnetic.get("status")
    if status not in {"available", "unavailable"}:
        errors.append(prefix + ".status")
    if not isinstance(design_basis, dict) or any(magnetic.get(k) != design_basis.get(k) for k in ("candidate_fingerprint", "run_id")):
        errors.append(prefix + ".source_identity")
    target = magnetic.get("target_inductance_h")
    if not finite(target) or target <= 0 or not isinstance(design_basis, dict) or target != design_basis.get("design_inductance_h"):
        errors.append(prefix + ".target_inductance")
    if status != "available":
        if any(magnetic.get(k) is not None for k in totals):
            errors.append(prefix + ".unavailable_totals")
        return errors
    selected_l = magnetic.get("selected_inductance_h")
    if not finite(selected_l) or selected_l <= 0 or not magnetic.get("selected_library_design_id"):
        errors.append(prefix + ".selection")
    phases = magnetic.get("phase_instances", ())
    if not isinstance(phases, (list, tuple)) or len(phases) != 3 or {p.get("instance_id") for p in phases if isinstance(p, dict)} != {"phase_a", "phase_b", "phase_c"}:
        return errors + [prefix + ".required_phases"]
    sums = {key: 0. for key in totals}
    operating_basis = magnetic.get("operating_basis", {})
    for phase in phases:
        design, evaluation, request = phase.get("design", {}), phase.get("evaluation", {}), phase.get("operating_request", {})
        if not all(isinstance(x, dict) for x in (design, evaluation, request, operating_basis)):
            errors.append(prefix + ".phase_data")
            continue
        expected_id = f"{magnetic.get('selected_library_design_id')}::{phase.get('instance_id')}"
        if design.get("candidate_id") != expected_id or evaluation.get("design_id") != expected_id or design.get("inductance_h") != selected_l:
            errors.append(prefix + ".phase_identity")
        required = (evaluation.get("copper_loss_w"), evaluation.get("core_loss_w"), evaluation.get("total_loss_w"), design.get("total_volume_m3"))
        if not all(finite(v) for v in required):
            errors.append(prefix + ".finite_components")
            continue
        if required[3] <= 0:
            errors.append(prefix + ".physical_volume")
        if not math.isclose(required[0] + required[1], required[2], rel_tol=1e-9, abs_tol=1e-9):
            errors.append(prefix + ".phase_total")
        metadata = request.get("metadata", {})
        if (not isinstance(metadata, dict) or request.get("operating_vin_v") != operating_basis.get("vdc_v")
                or request.get("operating_vout_v") != operating_basis.get("vac_ll_rms_v")
                or request.get("load_ratio") != operating_basis.get("load_ratio")
                or metadata.get("operating_power_factor") != operating_basis.get("power_factor")
                or metadata.get("actual_inductance_h") != selected_l):
            errors.append(prefix + ".operating_basis")
        if any(evaluation.get(k) != request.get(k) for k in ("operating_vin_v", "fs_hz", "i_rms_a", "i_peak_a")):
            errors.append(prefix + ".evaluation_basis")
        reference = phase.get("reference_request")
        if reference is not None:
            cases = design_basis.get("cases", ())
            nominal_case = cases[0] if isinstance(cases, (list, tuple)) and cases else None
            reference_metadata = reference.get("metadata", {}) if isinstance(reference, dict) else None
            if (not isinstance(reference, dict) or not isinstance(nominal_case, (list, tuple)) or len(nominal_case) != 3
                    or not isinstance(reference_metadata, dict)
                    or reference.get("operating_vin_v") != nominal_case[0]
                    or reference.get("load_ratio") != 1
                    or reference_metadata.get("operating_power_factor") != nominal_case[2]):
                errors.append(prefix + ".reference_basis")
        for key, value in zip(totals, required):
            sums[key] += value
    for key, value in sums.items():
        if not finite(magnetic.get(key)) or not math.isclose(magnetic[key], value, rel_tol=1e-9, abs_tol=1e-12):
            errors.append(prefix + "." + key)
    return errors


def _validate_t_type_capacitors(snapshot, basis, public, operating):
    errors = []
    prefix = "engineering_result.capacitors"
    if not isinstance(snapshot, dict):
        return [prefix]
    try:
        if snapshot["candidate_fingerprint"] != basis["candidate_fingerprint"] or snapshot["run_id"] != basis["run_id"]:
            errors.append(prefix + ".source")
        if snapshot["ripple_model"] != "fixed_bus_ripple_estimate":
            errors.append(prefix + ".scope")
        totals = ("equivalent_link_capacitance_f", "total_loss_w", "total_volume_cm3")
        if snapshot["status"] != "available":
            if snapshot["status"] != "unavailable" or any(snapshot[k] is not None for k in (*totals, "current_upper", "current_lower")) or public.get("available"):
                errors.append(prefix + ".unavailable")
            return errors
        if not public.get("available"):
            errors.append(prefix + ".public_availability")
        expected_basis = {"vdc_v": basis["cases"][0][0], "load_ratio": 1., "power_factor": basis["cases"][0][2],
            "vac_ll_rms_v": basis["vac_ll_rms_v"], "f_line_hz": basis["f_line_hz"],
            "fsw_hz": basis["fsw_hz"], "inductance_h": basis["design_inductance_h"], "power_factor_phase": basis["phase"]}
        for key, field in (("vdc_v", "input_voltage"), ("load_ratio", "load_ratio"), ("power_factor", "power_factor")):
            value = operating.get(field, {}).get("value")
            if operating.get("available") and value is not None:
                expected_basis[key] = value
        if any(snapshot["operating_basis"].get(k) != v for k, v in expected_basis.items()):
            errors.append(prefix + ".operating_basis")
        entries = []
        for side in ("upper", "lower"):
            entry, selected = snapshot[f"current_{side}"], snapshot[f"selected_{side}"]
            c = entry["candidate"]
            ns, np = entry["series_count"], entry["parallel_count"]
            if (not entry["feasible"] or not c["source"] or ns not in range(1, 5) or np not in range(1, 6)
                    or any(entry[k] != selected[k] for k in ("candidate", "series_count", "parallel_count"))):
                errors.append(prefix + f".{side}.hardware")
            expected = {"equivalent_capacitance_f": c["capacitance_f"] * np / ns,
                "equivalent_rs_ohm": c["rs_ohm"] * ns / np,
                "p_total_w": entry["p_joule_w"] + entry["p_dielectric_w"],
                "p_total_per_cap_w": entry["p_total_w"] / (ns * np),
                "p_joule_w": entry["capacitor_current_rms_total_a"] ** 2 * entry["equivalent_rs_ohm"],
                "capacitor_current_rms_per_cap_a": entry["capacitor_current_rms_total_a"] / np,
                "ripple_capacitive_pp_v": entry["q_swing_c"] / entry["equivalent_capacitance_f"],
                "ripple_esr_pp_v": entry["capacitor_current_pp_total_a"] * entry["equivalent_rs_ohm"],
                "ripple_total_pp_v": entry["ripple_capacitive_pp_v"] + entry["ripple_esr_pp_v"]}
            for key, value in expected.items():
                if not math.isfinite(entry[key]) or entry[key] < 0 or not math.isclose(entry[key], value, rel_tol=1e-10, abs_tol=1e-12):
                    errors.append(prefix + f".{side}.{key}")
            evidence = snapshot["port_metrics"]["banks"][side]
            limit = max(1e-10, 1e-8 * evidence["absolute_charge_c"])
            if (not math.isfinite(evidence["raw_charge_drift_c"]) or abs(evidence["raw_charge_drift_c"]) > limit
                    or not math.isclose(evidence["charge_drift_limit_c"], limit, rel_tol=1e-12, abs_tol=1e-15)):
                errors.append(prefix + f".{side}.raw_charge")
            for key, field in (("capacitance", "equivalent_capacitance_f"), ("ripple_total", "ripple_total_pp_v"),
                               ("current_rms", "capacitor_current_rms_total_a"), ("hotspot_temperature", "hotspot_temp_c")):
                if public[side]["metrics"][key]["value"] != entry[field]:
                    errors.append(prefix + f".{side}.public_readback")
                unit = {"capacitance": "F", "ripple_total": "V", "current_rms": "A", "hotspot_temperature": "degC"}[key]
                if public[side]["metrics"][key]["unit"] != unit or public[side]["metrics"][key]["source"] != f"engineering_result.capacitors.current_{side}":
                    errors.append(prefix + f".{side}.public_units_source")
            entries.append(entry)
        cu, cl = [e["equivalent_capacitance_f"] for e in entries]
        expected_totals = (cu * cl / (cu + cl), sum(e["p_total_w"] for e in entries), sum(e["total_volume_cm3"] for e in entries))
        for key, expected in zip(totals, expected_totals):
            if not math.isfinite(snapshot[key]) or not math.isclose(snapshot[key], expected, rel_tol=1e-12, abs_tol=1e-12):
                errors.append(prefix + "." + key)
        if public["metadata"]["basis"] != snapshot["operating_basis"]:
            errors.append(prefix + ".public_basis")
        for key, value in (("loss", snapshot["total_loss_w"]), ("volume", snapshot["total_volume_cm3"]),
                           ("equivalent_link_capacitance", snapshot["equivalent_link_capacitance_f"])):
            if public["bank_subtotal"][key]["value"] != value:
                errors.append(prefix + ".public_total")
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        errors.append(prefix + ".incomplete")
    return errors


def validate_snapshot_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="ascii"))
    records = payload.get("records", [])
    results = []
    for record in records:
        errors = validate_report(record.get("structured_report", {}))
        results.append({"matrix_id": record.get("matrix_id"), "case_id": record.get("case_id"), "errors": errors, "valid": not errors})
    return {"contract_version": "pe_claw_structured_output_validation_v1", "record_count": len(results), "valid_count": sum(item["valid"] for item in results), "invalid_count": sum(not item["valid"] for item in results), "records": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_snapshot_file(args.snapshot)
    text = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="ascii")
    print(json.dumps({key: result[key] for key in ("record_count", "valid_count", "invalid_count")}, ensure_ascii=True))
    return 0 if result["invalid_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
