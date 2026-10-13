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
