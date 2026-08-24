"""Build the Step 4 registry, capability, and routing evidence."""

from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw")
PLAN_ROOT = ROOT / "Plan" / "active"
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.parsers.design_request import normalize_design_request_file
from pe_claw_gui.topologies.base.capabilities import TOPOLOGY_CAPABILITIES
from pe_claw_gui.topologies.base.registry import build_default_registry


MIGRATED_TOPOLOGIES = (
    ("01_buck_diode", "buck_diode_rectified_unidirectional"),
    ("02_buck_synchronous", "buck_synchronous_rectified_unidirectional"),
    ("03_boost_diode", "boost_diode_rectified_unidirectional"),
    ("04_boost_synchronous", "boost_synchronous_rectified_unidirectional"),
    ("05_buck_boost_diode", "buck_boost_diode_rectified_unidirectional"),
    ("06_flyback_ccm", "flyback_diode_rectified_isolated"),
    ("07_psfb_diode", "phase_shifted_full_bridge_diode_rectifier_isolated"),
    ("08_llc_full_bridge_diode", "llc_resonant_converter_diode_rectifier"),
    ("09_llc_half_bridge_diode", "llc_resonant_converter_diode_rectifier"),
    ("10_single_phase_capacitor_rectifier", "single_phase_diode_bridge_rectifier_capacitor_filter"),
    ("11_single_phase_dc_inductor_rectifier", "single_phase_diode_bridge_rectifier_dc_inductor_filter"),
    ("12_three_phase_capacitor_rectifier", "three_phase_diode_bridge_rectifier_capacitor_filter"),
    ("13_diode_bridge_boost_pfc", "single_phase_boost_pfc_diode_bridge"),
    ("14_totem_pole_pfc", "single_phase_totem_pole_bridgeless_pfc"),
    ("15_single_phase_full_bridge_inverter", "single_phase_full_bridge_inverter"),
    ("16_three_phase_two_level_vsi", "three_phase_two_level_voltage_source_inverter"),
    ("17_three_phase_three_level_npc", "three_phase_three_level_npc_inverter"),
)
LLC_VARIANTS = {
    "08_llc_full_bridge_diode": ("full_bridge", "full_bridge_rectifier"),
    "09_llc_half_bridge_diode": ("half_bridge", "full_wave_center_tapped_rectifier"),
}


def _registry_ast(path: Path) -> dict[str, dict[str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: dict[str, dict[str, str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "register" or not node.args:
            continue
        definition = node.args[0]
        if not isinstance(definition, ast.Call):
            continue
        values: dict[str, str] = {}
        for keyword in definition.keywords:
            if keyword.arg in {"topology_id", "display_name", "module_path", "legacy_key"}:
                value = ast.literal_eval(keyword.value)
                values[keyword.arg] = str(value)
        if "topology_id" in values:
            result[values["topology_id"]] = values
    return result


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    registry = build_default_registry()
    definitions = {item.topology_id: item for item in registry.list_definitions()}
    source_registry = _registry_ast(SOURCE_ROOT / "src/pe_claw_gui/topologies/base/registry.py")
    target_registry = _registry_ast(ROOT / "src/pe_claw_gui/topologies/base/registry.py")

    registry_rows: list[dict[str, Any]] = []
    for request_dir, topology_id in MIGRATED_TOPOLOGIES:
        definition = definitions[topology_id]
        source = source_registry[topology_id]
        target = target_registry[topology_id]
        registry_rows.append({
            "request_directory": request_dir,
            "topology_id": topology_id,
            "source_topology_id": source.get("topology_id"),
            "target_topology_id": target.get("topology_id"),
            "source_display_name": source.get("display_name"),
            "target_display_name": target.get("display_name"),
            "source_module_path": source.get("module_path"),
            "target_module_path": target.get("module_path"),
            "source_legacy_key": source.get("legacy_key"),
            "target_legacy_key": target.get("legacy_key"),
            "category_id": definition.category_id,
            "implemented": definition.implemented,
            "shared_plugin_variant": request_dir in LLC_VARIANTS,
            "variant_primary_bridge_type": LLC_VARIANTS.get(request_dir, ("", ""))[0],
            "variant_secondary_rectifier_type": LLC_VARIANTS.get(request_dir, ("", ""))[1],
            "registry_metadata_match": source == target,
        })
    _write_csv(
        PLAN_ROOT / "topology_registry_mapping.csv",
        registry_rows,
        list(registry_rows[0]),
    )

    capability_rows = []
    for capability in TOPOLOGY_CAPABILITIES:
        definition = definitions[capability.topology_id]
        capability_rows.append({
            "topology_id": capability.topology_id,
            "capability_id": capability.capability_id,
            "display_name": capability.display_name,
            "category_id": capability.category_id,
            "registered": True,
            "implemented": definition.implemented,
            "support_status": capability.support_status,
            "required_fields": ";".join(capability.required_fields),
            "default_fields": ";".join(capability.default_fields),
            "plugin_hooks": ";".join(capability.hooks),
            "boundary_notes": " | ".join(capability.boundary_notes),
        })
    _write_csv(
        PLAN_ROOT / "topology_capability_mapping.csv",
        capability_rows,
        list(capability_rows[0]),
    )

    route_records: list[dict[str, Any]] = []
    route_mismatches: list[dict[str, Any]] = []
    for request_dir, expected_topology_id in MIGRATED_TOPOLOGIES:
        request_files = sorted((SOURCE_ROOT / "design_requests" / request_dir).glob("*/design_request.md"))
        for request_file in request_files:
            normalized = normalize_design_request_file(request_file)
            hint = str(normalized.get("topology_hint") or "")
            try:
                resolved = registry.resolve_topology_id(hint)
                route_status = "matched" if resolved == expected_topology_id else "wrong_topology"
            except ValueError as exc:
                resolved = None
                route_status = "unsupported_topology"
                route_mismatches.append({"request": str(request_file), "error": str(exc)})
            constraints = normalized.get("constraints") or {}
            expected_bridge, expected_rectifier = LLC_VARIANTS.get(request_dir, (None, None))
            variant_status = "not_applicable"
            if expected_bridge is not None:
                variant_status = (
                    "matched"
                    if constraints.get("primary_bridge_type") == expected_bridge
                    and constraints.get("secondary_rectifier_type") == expected_rectifier
                    else "variant_mismatch"
                )
            record = {
                "request_directory": request_dir,
                "request_file": str(request_file),
                "topology_hint": hint,
                "expected_topology_id": expected_topology_id,
                "resolved_topology_id": resolved,
                "route_status": route_status,
                "variant_status": variant_status,
                "primary_bridge_type": constraints.get("primary_bridge_type"),
                "secondary_rectifier_type": constraints.get("secondary_rectifier_type"),
            }
            route_records.append(record)
            if route_status != "matched" or variant_status == "variant_mismatch":
                route_mismatches.append(record)

    report = {
        "step": 4,
        "contract": "topology_registry_and_plugin_routing_v1",
        "source_root": str(SOURCE_ROOT),
        "target_root": str(ROOT),
        "migrated_request_directories": len(MIGRATED_TOPOLOGIES),
        "migrated_unique_topology_ids": len({topology_id for _, topology_id in MIGRATED_TOPOLOGIES}),
        "target_registered_topology_count": len(definitions),
        "target_registered_topology_ids_unique": len(definitions) == len(registry.list_definitions()),
        "registry_metadata_match_count": sum(1 for row in registry_rows if row["registry_metadata_match"]),
        "registry_metadata_mismatch_count": sum(1 for row in registry_rows if not row["registry_metadata_match"]),
        "request_count": len(route_records),
        "route_match_count": sum(1 for row in route_records if row["route_status"] == "matched"),
        "route_mismatch_count": len(route_mismatches),
        "llc_variant_match_count": sum(1 for row in route_records if row["variant_status"] == "matched"),
        "llc_variant_case_count": sum(1 for row in route_records if row["variant_status"] != "not_applicable"),
        "route_mismatches": route_mismatches,
        "records": route_records,
        "validation_pass": (
            len(MIGRATED_TOPOLOGIES) == 17
            and len({topology_id for _, topology_id in MIGRATED_TOPOLOGIES}) == 16
            and len(definitions) == 19
            and all(row["registry_metadata_match"] for row in registry_rows)
            and not route_mismatches
        ),
    }
    (PLAN_ROOT / "topology_routing_consistency.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key not in {"records", "route_mismatches"}}, indent=2))
    return 0 if report["validation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
